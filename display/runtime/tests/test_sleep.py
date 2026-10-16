from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from runtime.animation import EyeAnimator
from runtime.manual_wake import ManualWakeReader
from runtime.personality_adapter import FallbackPersonalitySource, PersonalityInput
from runtime.personality_loop import AutonomousPersonalityController
from runtime.run_face import FACE_UPDATE_REGION, main
from sherman_procedural_eyes import ProceduralEyesRenderer


def intent(animator, now_s, sleeping):
    animator.set_semantic_intent(
        "tired" if sleeping else "calm",
        now_s,
        attention=0.0 if sleeping else 0.5,
        arousal=0.0 if sleeping else 0.5,
        gaze_x=0.0,
        gaze_y=0.0,
        eyelid_open=0.0 if sleeping else 1.0,
        blink_rate_hz=0.0,
        sleeping=sleeping,
    )


class SleepTest(unittest.TestCase):
    def test_wake_lease_is_bounded_restart_safe_and_cannot_clear_quiet_policy(self):
        fixture = json.loads(
            (
                Path(__file__).resolve().parents[3]
                / "proto/fixtures/manual-wake-request-v1.json"
            ).read_text()
        )
        native_intent = replace(
            FallbackPersonalitySource().step(
                PersonalityInput(0, 10800, circadian_valid=True)
            ),
            reason_flags=2,
        )
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "wake.json"
            path.write_text(json.dumps(fixture))
            reader = ManualWakeReader(path, 99.0)
            self.assertEqual(
                reader.update(100, native_intent, degraded=False), fixture["request_id"]
            )
            self.assertTrue(native_intent.sleeping)
            self.assertEqual(reader.update(400, native_intent, degraded=False), "")
            self.assertEqual(
                ManualWakeReader(path, 101).update(101, native_intent, degraded=False),
                "",
            )
            for changes in (
                {"reason_flags": 6},
                {"reason_flags": 10},
                {"reason_flags": 66},
            ):
                self.assertEqual(
                    ManualWakeReader(path, 99).update(
                        100, replace(native_intent, **changes), degraded=False
                    ),
                    "",
                )
            self.assertEqual(
                ManualWakeReader(path, 99).update(100, native_intent, degraded=True), ""
            )
            for changes in (
                {"schema_version": True},
                {"request_id": "bad"},
                {"issued_at_monotonic_s": 101},
                {"expires_at_monotonic_s": 401},
                {"issued_at_monotonic_s": float("nan")},
                {"expires_at_monotonic_s": float("inf")},
                {"extra": True},
            ):
                path.write_text(json.dumps(dict(fixture, **changes)))
                self.assertEqual(
                    ManualWakeReader(path, 99).update(
                        100, native_intent, degraded=False
                    ),
                    "",
                )
            path.write_text("x" * 1025)
            self.assertEqual(
                ManualWakeReader(path, 99).update(100, native_intent, degraded=False),
                "",
            )
            path.unlink()
            self.assertEqual(
                ManualWakeReader(path, 99).update(100, native_intent, degraded=False),
                "",
            )

    def test_slow_closure_breathing_and_wake_are_continuous(self):
        animator = EyeAnimator(seed=531)
        intent(animator, 0.0, False)
        awake = animator.sample(0.0)
        intent(animator, 0.0, True)
        self.assertEqual(animator.sample(0.0).params, awake.params)
        heights = []
        for step in range(91):
            now = step / 30
            intent(animator, now, True)  # repeated ticks must not restart the clip
            heights.append(animator.sample(now).eyes[0].scale_y)
        self.assertTrue(all(a >= b for a, b in zip(heights, heights[1:])))
        self.assertEqual(animator.sleep_state, "sleeping")
        sleeping = animator.sample(4.5)
        self.assertLess(sleeping.eyes[0].scale_y, 0.04)
        self.assertNotEqual(sleeping.params, animator.sample(6.0).params)
        self.assertAlmostEqual(
            sleeping.eyes[0].scale_y, animator.sample(6.0).eyes[0].scale_y
        )
        before_wake = animator.sample(7.0)
        intent(animator, 7.0, False)
        self.assertEqual(animator.sample(7.0).params, before_wake.params)
        self.assertEqual(animator.sleep_state, "waking_up")
        self.assertLess(animator.sample(8.2).eyes[0].scale_y, awake.eyes[0].scale_y)
        animator.sample(9.4)
        self.assertEqual(animator.sleep_state, "awake")

    def test_reversal_and_large_clock_jumps_do_not_snap_or_replay(self):
        animator = EyeAnimator(seed=531)
        intent(animator, 0.0, True)
        for now, sleeping in ((1.0, False), (1.5, True), (2.0, False)):
            before = animator.sample(now)
            intent(animator, now, sleeping)
            self.assertEqual(before.params, animator.sample(now).params)
        animator.sample(86400.0)
        self.assertEqual(animator.sleep_state, "awake")
        intent(animator, 86400.0, True)
        animator.sample(172800.0)
        self.assertEqual(animator.sleep_state, "sleeping")

    def test_sleep_cycle_is_seeded_visible_and_inside_display_region(self):
        left, right = EyeAnimator(seed=531), EyeAnimator(seed=531)
        renderer = ProceduralEyesRenderer()
        region = FACE_UPDATE_REGION
        for tick in range(91):
            now = tick / 5
            for animator in (left, right):
                intent(animator, now, now < 12)
            pose = left.sample(now)
            self.assertEqual(pose.params, right.sample(now).params)
            bounds = renderer.render_mask(pose).getbbox()
            self.assertIsNotNone(bounds)
            x0, y0, x1, y1 = bounds
            self.assertGreaterEqual(x0, region.x)
            self.assertGreaterEqual(y0, region.y)
            self.assertLessEqual(x1, region.x + region.width)
            self.assertLessEqual(y1, region.y + region.height)

    def test_fallback_preserves_schedule_explicit_quiet_and_failure_entry(self):
        source = FallbackPersonalitySource()
        for second, sleeping in (
            (0, False),
            (7199, False),
            (7200, True),
            (10800, True),
            (28799, True),
            (28800, False),
            (71100, False),  # 19:45 must be awake
            (86399, False),
        ):
            output = source.step(PersonalityInput(0, second, circadian_valid=True))
            self.assertEqual(output.sleeping, sleeping)
        self.assertFalse(source.step(PersonalityInput(0)).sleeping)
        self.assertTrue(source.step(PersonalityInput(0, quiet=True)).sleeping)
        broken = mock.Mock()
        broken.step.side_effect = RuntimeError("native failure")
        controller = AutonomousPersonalityController(
            broken,
            started_s=0.0,
            circadian_enabled=False,
            input_provider=lambda ns, *_: PersonalityInput(ns, quiet=True),
        )
        self.assertTrue(controller.update(0.0).sleeping)
        self.assertTrue(controller.degraded)
        controller.close()

    def test_runtime_publishes_each_transition_before_periodic_report(self):
        now = [0.0]
        records = []
        fallback = FallbackPersonalitySource()
        source = mock.Mock(backend_name="test-native")
        source.restore.return_value = True
        source.snapshot.return_value = b""
        source.step.side_effect = lambda inputs: replace(
            fallback.step(
                replace(
                    inputs,
                    circadian_valid=True,
                    local_second_of_day=10800 if 1 <= now[0] < 16 else 28800,
                )
            ),
            reason_flags=2 if 1 <= now[0] < 16 else 0,
        )
        display = mock.Mock()
        display.stats = SimpleNamespace(
            transfer_errors=0,
            last_transfer_ms=1.0,
            maximum_transfer_ms=1.0,
        )
        renderer = mock.Mock(backend_name="test-renderer")
        renderer.render_rgb565.return_value = b""

        def pause(seconds):
            now[0] += seconds
            if 5 <= now[0] < 11 and not wake_file.exists():
                wake_file.write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "request_id": "d" * 32,
                            "issued_at_monotonic_s": now[0],
                            "expires_at_monotonic_s": now[0] + 300,
                        }
                    )
                )
            elif now[0] >= 11:
                wake_file.unlink(missing_ok=True)

        def publish(_path, payload):
            records.append((now[0], dict(payload)))

        with (
            tempfile.TemporaryDirectory() as folder,
            mock.patch("runtime.run_face.NativePersonalitySource", return_value=source),
            mock.patch("runtime.run_face.St7789Display", return_value=display),
            mock.patch(
                "runtime.run_face.FastProceduralEyesRenderer", return_value=renderer
            ),
            mock.patch("runtime.run_face.time.monotonic", side_effect=lambda: now[0]),
            mock.patch("runtime.run_face.time.sleep", side_effect=pause),
            mock.patch("runtime.run_face._atomic_write_json", side_effect=publish),
        ):
            wake_file = Path(folder) / "wake.json"
            self.assertEqual(
                main(
                    [
                        "--duration",
                        "20",
                        "--wake-request-file",
                        str(wake_file),
                        "--health-file",
                        str(Path(folder) / "health"),
                        "--personality-state-file",
                        str(Path(folder) / "state"),
                    ]
                ),
                0,
            )
        changes = []
        for when, record in records:
            if not changes or changes[-1][1] != record["sleep_state"]:
                changes.append((when, record["sleep_state"]))
            self.assertLess(len(json.dumps(record)), 4096)
        self.assertEqual(
            [state for _, state in changes],
            [
                "awake",
                "falling_asleep",
                "sleeping",
                "waking_up",
                "awake",
                "falling_asleep",
                "sleeping",
                "waking_up",
                "awake",
            ],
        )
        self.assertLess(changes[1][0], 1.2)
        self.assertLess(changes[3][0], 5.2)
        self.assertLess(changes[5][0], 11.2)
        self.assertLess(changes[7][0], 16.2)
        manually_awake = next(
            record
            for when, record in records
            if 7 < when < 11 and record["sleep_state"] == "awake"
        )
        self.assertEqual(manually_awake["reason_flags"], 2)
        self.assertEqual(manually_awake["wake_request_id"], "d" * 32)


if __name__ == "__main__":
    unittest.main()
