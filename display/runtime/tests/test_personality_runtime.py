from __future__ import annotations

import ctypes
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock

from runtime.config import load_face_runtime_config
from runtime.personality_adapter import (
    PERSONALITY_API_VERSION,
    FallbackPersonalitySource,
    NativePersonalitySource,
    PersonalityInput,
    PersonalityIntent,
    PersonalityRuntimeError,
    PersonalityStateStore,
    _Config,
    _Input,
    _Output,
    _PolicySnapshot,
    _RoutineSnapshot,
    _Snapshot,
)
from runtime.personality_loop import AutonomousPersonalityController
from runtime.run_face import _parse_args, main


class _FakeFunction:
    def __init__(self, implementation):  # type: ignore[no-untyped-def]
        self.implementation = implementation
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):  # type: ignore[no-untyped-def]
        return self.implementation(*args)


class _FakeLibrary:
    def __init__(self, *, version: int = PERSONALITY_API_VERSION) -> None:
        self.destroyed = False
        self.last_input: _Input | None = None
        self.restored: _Snapshot | None = None
        self.policy_restored: _PolicySnapshot | None = None
        self.routines_restored: _RoutineSnapshot | None = None
        self.sherman_personality_api_version = _FakeFunction(lambda: version)
        self.sherman_personality_config_size = _FakeFunction(
            lambda: ctypes.sizeof(_Config)
        )
        self.sherman_personality_input_size = _FakeFunction(
            lambda: ctypes.sizeof(_Input)
        )
        self.sherman_personality_output_size = _FakeFunction(
            lambda: ctypes.sizeof(_Output)
        )
        self.sherman_personality_snapshot_size = _FakeFunction(
            lambda: ctypes.sizeof(_Snapshot)
        )
        self.sherman_personality_policy_snapshot_size = _FakeFunction(
            lambda: ctypes.sizeof(_PolicySnapshot)
        )
        self.sherman_personality_routine_snapshot_size = _FakeFunction(
            lambda: ctypes.sizeof(_RoutineSnapshot)
        )
        self.sherman_personality_default_config = _FakeFunction(self._default_config)
        self.sherman_personality_create = _FakeFunction(lambda _config: 1234)
        self.sherman_personality_destroy = _FakeFunction(self._destroy)
        self.sherman_personality_reset = _FakeFunction(lambda _handle, _seed: 0)
        self.sherman_personality_apply_event = _FakeFunction(
            lambda _handle, _event, _strength: 0
        )
        self.sherman_personality_step = _FakeFunction(self._step)
        self.sherman_personality_snapshot_state = _FakeFunction(self._snapshot)
        self.sherman_personality_restore = _FakeFunction(self._restore)
        self.sherman_personality_snapshot_policy = _FakeFunction(
            self._snapshot_policy
        )
        self.sherman_personality_restore_policy = _FakeFunction(
            self._restore_policy
        )
        self.sherman_personality_snapshot_routines = _FakeFunction(
            self._snapshot_routines
        )
        self.sherman_personality_restore_routines = _FakeFunction(
            self._restore_routines
        )

    @staticmethod
    def _default_config(pointer) -> int:  # type: ignore[no-untyped-def]
        config = pointer._obj
        if config.struct_size != ctypes.sizeof(_Config):
            return -1
        config.api_version = PERSONALITY_API_VERSION
        return 0

    def _destroy(self, _handle) -> None:  # type: ignore[no-untyped-def]
        self.destroyed = True

    def _step(self, _handle, input_pointer, output_pointer) -> int:  # type: ignore[no-untyped-def]
        self.last_input = _Input.from_buffer_copy(input_pointer._obj)
        output = output_pointer._obj
        output.struct_size = ctypes.sizeof(_Output)
        output.api_version = PERSONALITY_API_VERSION
        output.monotonic_time_ns = self.last_input.monotonic_time_ns
        output.sequence = 7
        output.expression = 1
        output.micro_behavior = 2
        output.reason_flags = 128
        output.valence = 0.1
        output.arousal = 0.4
        output.confidence = 0.7
        output.attention = 0.8
        output.gaze_x = -0.25
        output.gaze_y = 0.5
        output.eyelid_open = 0.9
        output.blink_rate_hz = 0.3
        return 0

    @staticmethod
    def _snapshot(_handle, pointer) -> int:  # type: ignore[no-untyped-def]
        snapshot = pointer._obj
        snapshot.struct_size = ctypes.sizeof(_Snapshot)
        snapshot.snapshot_version = 1
        snapshot.rng_state = 99
        return 0

    def _restore(self, _handle, pointer) -> int:  # type: ignore[no-untyped-def]
        self.restored = _Snapshot.from_buffer_copy(pointer._obj)
        return 0

    @staticmethod
    def _snapshot_policy(_handle, pointer) -> int:  # type: ignore[no-untyped-def]
        snapshot = pointer._obj
        snapshot.struct_size = ctypes.sizeof(_PolicySnapshot)
        snapshot.snapshot_version = 1
        snapshot.last_selected_candidate_id = 22
        return 0

    def _restore_policy(self, _handle, pointer) -> int:  # type: ignore[no-untyped-def]
        self.policy_restored = _PolicySnapshot.from_buffer_copy(pointer._obj)
        return 0

    @staticmethod
    def _snapshot_routines(_handle, pointer) -> int:  # type: ignore[no-untyped-def]
        snapshot = pointer._obj
        snapshot.struct_size = ctypes.sizeof(_RoutineSnapshot)
        snapshot.snapshot_version = 1
        snapshot.routine_count = 0
        return 0

    def _restore_routines(self, _handle, pointer) -> int:  # type: ignore[no-untyped-def]
        self.routines_restored = _RoutineSnapshot.from_buffer_copy(pointer._obj)
        return 0


class _FakeSource:
    backend_name = "fake-native"

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.steps = 0
        self.closed = False
        self.restored = b""

    def step(self, inputs: PersonalityInput) -> PersonalityIntent:
        self.steps += 1
        if self.fail:
            raise RuntimeError("fixture personality failure")
        return PersonalityIntent(
            monotonic_time_ns=inputs.monotonic_time_ns,
            sequence=self.steps,
            expression="curious",
            micro_behavior="observing",
            reason_flags=128,
            valence=0.2,
            arousal=0.5,
            confidence=0.7,
            attention=0.8,
            gaze_x=0.1,
            gaze_y=-0.2,
            eyelid_open=1.0,
            blink_rate_hz=0.3,
        )

    def snapshot(self) -> bytes:
        return b"native-state"

    def apply_event(self, _event: int, _strength: float = 1.0) -> bool:
        return True

    def restore(self, payload: bytes) -> bool:
        self.restored = payload
        return payload == b"native-state"

    def close(self) -> None:
        self.closed = True


class NativeAdapterTest(unittest.TestCase):
    def test_exact_abi_is_validated_and_semantics_are_mapped(self) -> None:
        with tempfile.NamedTemporaryFile() as library_file:
            fake = _FakeLibrary()
            source = NativePersonalitySource(
                library_file.name,
                seed=42,
                library_loader=lambda _path: fake,
            )
            intent = source.step(
                PersonalityInput(
                    monotonic_time_ns=123,
                    local_second_of_day=45_000,
                    circadian_valid=True,
                    attention_target_x=0.2,
                    attention_target_y=-0.4,
                    attention_salience=0.8,
                )
            )
            self.assertEqual(intent.expression, "curious")
            self.assertEqual(intent.micro_behavior, "observing")
            self.assertAlmostEqual(intent.gaze_y or 0.0, 0.5)
            assert fake.last_input is not None
            self.assertEqual(fake.last_input.flags, (1 << 5) | (1 << 6))
            payload = source.snapshot()
            self.assertGreater(
                len(payload), ctypes.sizeof(_Snapshot) + ctypes.sizeof(_PolicySnapshot)
            )
            self.assertTrue(source.restore(payload))
            self.assertIsNotNone(fake.policy_restored)
            self.assertIsNotNone(fake.routines_restored)
            source.close()
            self.assertTrue(fake.destroyed)

    def test_api_version_mismatch_fails_before_create(self) -> None:
        with tempfile.NamedTemporaryFile() as library_file:
            with self.assertRaises(PersonalityRuntimeError):
                NativePersonalitySource(
                    library_file.name,
                    library_loader=lambda _path: _FakeLibrary(version=0x00020000),
                )

    def test_untrusted_input_ranges_are_rejected(self) -> None:
        with tempfile.NamedTemporaryFile() as library_file:
            source = NativePersonalitySource(
                library_file.name, library_loader=lambda _path: _FakeLibrary()
            )
            with self.assertRaises(ValueError):
                source.step(PersonalityInput(monotonic_time_ns=1, novelty=float("nan")))
            with self.assertRaises(ValueError):
                source.step(
                    PersonalityInput(
                        monotonic_time_ns=1,
                        attention_target_x=0.0,
                        attention_target_y=None,
                    )
                )
            source.close()


class StateStoreTest(unittest.TestCase):
    def test_round_trip_and_checksum_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "personality.state"
            store = PersonalityStateStore(path)
            self.assertIsNone(store.load())
            store.save(b"native-state")
            self.assertEqual(store.load(), b"native-state")
            encoded = bytearray(path.read_bytes())
            encoded[-1] ^= 1
            path.write_bytes(encoded)
            with self.assertRaisesRegex(ValueError, "checksum"):
                store.load()

    def test_oversized_state_is_rejected_without_replacing_last_good(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "personality.state"
            store = PersonalityStateStore(path)
            store.save(b"last-good")
            with self.assertRaises(ValueError):
                store.save(b"x" * 4096)
            self.assertEqual(store.load(), b"last-good")


class ControllerTest(unittest.TestCase):
    def test_tick_scheduler_drops_stale_ticks_without_queueing(self) -> None:
        source = _FakeSource()
        controller = AutonomousPersonalityController(
            source, started_s=10.0, tick_hz=10.0
        )
        self.assertEqual(controller.update(10.0).expression, "curious")
        controller.update(10.05)
        controller.update(11.0)
        self.assertEqual(source.steps, 2)
        self.assertEqual(controller.tick_drops, 9)
        controller.close()

    def test_native_failure_degrades_once_to_safe_calm(self) -> None:
        source = _FakeSource(fail=True)
        controller = AutonomousPersonalityController(source, started_s=0.0)
        intent = controller.update(0.0)
        self.assertEqual(intent.expression, "calm")
        self.assertTrue(controller.degraded)
        self.assertTrue(source.closed)
        controller.update(1.0)
        self.assertEqual(controller.step_errors, 1)
        controller.close()

    def test_state_restores_and_is_saved_on_close(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = PersonalityStateStore(Path(directory) / "state")
            store.save(b"native-state")
            source = _FakeSource()
            controller = AutonomousPersonalityController(
                source, started_s=0.0, state_store=store
            )
            self.assertEqual(controller.restore_status, "restored")
            controller.close()
            self.assertEqual(store.load(), b"native-state")

    def test_explicit_timezone_drives_local_second(self) -> None:
        source = _FakeSource()
        captured: list[PersonalityInput] = []

        def provider(now_ns: int, local_second: int, circadian: bool) -> PersonalityInput:
            item = PersonalityInput(now_ns, local_second, circadian)
            captured.append(item)
            return item

        fixed = time.struct_time((2026, 8, 19, 13, 14, 15, 2, 231, 1))
        controller = AutonomousPersonalityController(
            source,
            started_s=0.0,
            input_provider=provider,
            localtime=lambda: fixed,
            circadian_enabled=True,
        )
        controller.update(0.0)
        self.assertEqual(captured[0].local_second_of_day, 13 * 3600 + 14 * 60 + 15)
        self.assertTrue(captured[0].circadian_valid)
        controller.close()


class ConfigTest(unittest.TestCase):
    def test_service_config_is_strict_and_defaults_to_personality(self) -> None:
        args = _parse_args(["--duration", "1"])
        self.assertEqual(args.mode, "personality")
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "face.json"
            config.write_text(
                '{"schema_version":1,"timezone":"UTC0",'
                '"circadian_enabled":true,"fps":25}',
                encoding="utf-8",
            )
            loaded = load_face_runtime_config(config)
            self.assertEqual(loaded.mode, "personality")
            self.assertEqual(loaded.timezone, "UTC0")
            self.assertEqual(loaded.fps, 25.0)

    def test_circadian_requires_explicit_timezone_and_unknowns_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "face.json"
            config.write_text('{"circadian_enabled":true}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "timezone"):
                load_face_runtime_config(config)
            config.write_text('{"unexpected":1}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unknown"):
                load_face_runtime_config(config)


class ProductionLoopTest(unittest.TestCase):
    def test_default_production_loop_consumes_personality_not_demo(self) -> None:
        source = _FakeSource()

        class Renderer:
            backend_name = "fake-fast"

            def render_rgb565(self, _pose):  # type: ignore[no-untyped-def]
                return memoryview(bytearray(320 * 170 * 2))

            def close(self) -> None:
                return None

        class Stats:
            transfer_errors = 0
            last_transfer_ms = 1.0
            maximum_transfer_ms = 1.0

        class Display:
            def __init__(self, config) -> None:  # type: ignore[no-untyped-def]
                self.config = config
                self.stats = Stats()

            def open(self) -> None:
                return None

            def show_rgb565(self, _frame) -> None:  # type: ignore[no-untyped-def]
                return None

            def show_rgb565_region(self, _frame, _region) -> None:  # type: ignore[no-untyped-def]
                return None

            def close(self) -> None:
                return None

        with tempfile.TemporaryDirectory() as directory:
            health = Path(directory) / "health.json"
            state = Path(directory) / "state"
            with (
                mock.patch(
                    "runtime.run_face.NativePersonalitySource", return_value=source
                ),
                mock.patch(
                    "runtime.run_face.FastProceduralEyesRenderer",
                    return_value=Renderer(),
                ),
                mock.patch("runtime.run_face.St7789Display", Display),
            ):
                status = main(
                    [
                        "--duration",
                        "0.12",
                        "--health-file",
                        str(health),
                        "--personality-state-file",
                        str(state),
                        "--persistence-interval",
                        "10",
                    ]
                )
            self.assertEqual(status, 0)
            self.assertGreater(source.steps, 0)
            record = health.read_text(encoding="utf-8")
            self.assertIn('"mode":"personality"', record)
            self.assertIn('"state":"stopped"', record)
            self.assertNotIn('"mode":"demo"', record)


if __name__ == "__main__":
    unittest.main()
