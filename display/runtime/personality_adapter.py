"""Hardware-independent bridge from native personality to face semantics.

The native library owns character policy, needs, mood, idle micro-behavior and
its deterministic random stream. This module only validates that versioned C
contract, translates its output into renderer semantics, and persists the
opaque fixed-size native snapshot.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass, replace
from enum import IntEnum
import math
import os
from pathlib import Path
import struct
from typing import Callable, Protocol
import zlib


PERSONALITY_API_VERSION = 0x00010000
PERSONALITY_SNAPSHOT_VERSION = 1
MAX_STATE_BYTES = 4096
_STATE_MAGIC = b"SHRMPER1"
_STATE_ENVELOPE_VERSION = 1
_STATE_HEADER = struct.Struct(">8sHII")
_NATIVE_STATE_MAGIC = b"SHRNAT01"
_NATIVE_STATE_VERSION = 2
_NATIVE_STATE_V1_HEADER = struct.Struct(">8sHHH")
_NATIVE_STATE_HEADER = struct.Struct(">8sHHHH")

_EXPRESSIONS = (
    "calm",
    "curious",
    "focused",
    "pleased",
    "uncertain",
    "frustrated",
    "tired",
)
_MICRO_BEHAVIORS = (
    "settled",
    "orienting",
    "observing",
    "engaged",
    "reflecting",
    "drowsy",
)


class PersonalityRuntimeError(RuntimeError):
    """The native personality contract could not be used safely."""


class PersonalityEvent(IntEnum):
    DISCOVERY = 0
    TASK_STARTED = 1
    TASK_SUCCEEDED = 2
    TASK_FAILED = 3
    BLOCKED = 4
    SOCIAL_CONTACT = 5
    SOCIAL_MISSED = 6
    PICKED_UP = 7
    RESTED = 8
    ENERGY_DEPLETED = 9
    URGENT_REQUEST = 10
    CALMED = 11
    INTERACTION_STARTED = 12
    INTERACTION_ENDED = 13


class _Config(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("api_version", ctypes.c_uint32),
        ("seed", ctypes.c_uint64),
        ("curiosity", ctypes.c_float),
        ("sociability", ctypes.c_float),
        ("calmness", ctypes.c_float),
        ("expressiveness", ctypes.c_float),
        ("day_activity", ctypes.c_float),
    ]


class _Input(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("monotonic_time_ns", ctypes.c_uint64),
        ("local_second_of_day", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32),
        ("activity_load", ctypes.c_float),
        ("task_engagement", ctypes.c_float),
        ("social_engagement", ctypes.c_float),
        ("novelty", ctypes.c_float),
        ("external_urgency", ctypes.c_float),
        ("attention_target_x", ctypes.c_float),
        ("attention_target_y", ctypes.c_float),
        ("attention_salience", ctypes.c_float),
    ]


class _Output(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("api_version", ctypes.c_uint32),
        ("monotonic_time_ns", ctypes.c_uint64),
        ("sequence", ctypes.c_uint64),
        ("expression", ctypes.c_int32),
        ("micro_behavior", ctypes.c_int32),
        ("reason_flags", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32),
        ("valence", ctypes.c_float),
        ("arousal", ctypes.c_float),
        ("confidence", ctypes.c_float),
        ("attention", ctypes.c_float),
        ("gaze_x", ctypes.c_float),
        ("gaze_y", ctypes.c_float),
        ("eyelid_open", ctypes.c_float),
        ("blink_rate_hz", ctypes.c_float),
    ]


class _Snapshot(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("snapshot_version", ctypes.c_uint32),
        ("rng_state", ctypes.c_uint64),
        ("sequence", ctypes.c_uint64),
        ("total_awake_s", ctypes.c_float),
        ("since_interaction_s", ctypes.c_float),
        ("since_engagement_s", ctypes.c_float),
        ("idle_delay_remaining_s", ctypes.c_float),
        ("energy", ctypes.c_float),
        ("curiosity", ctypes.c_float),
        ("social_engagement", ctypes.c_float),
        ("confidence", ctypes.c_float),
        ("frustration", ctypes.c_float),
        ("urgency", ctypes.c_float),
        ("valence", ctypes.c_float),
        ("arousal", ctypes.c_float),
        ("mood", ctypes.c_int32),
        ("reserved", ctypes.c_uint32),
    ]


class _PolicySnapshot(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("snapshot_version", ctypes.c_uint32),
        ("last_selected_candidate_id", ctypes.c_uint64),
        ("last_selected_kind", ctypes.c_int32),
        ("seen_kind_mask", ctypes.c_uint32),
        ("seconds_since_kind_selected", ctypes.c_float * 10),
    ]


class _RoutineProgress(ctypes.Structure):
    _fields_ = [
        ("routine_id", ctypes.c_uint64),
        ("last_completed_day_id", ctypes.c_int64),
        ("active_occurrence_day_id", ctypes.c_int64),
        ("cooldown_remaining_s", ctypes.c_float),
        ("next_checkpoint_index", ctypes.c_uint32),
        ("has_completed", ctypes.c_uint32),
        ("has_active_occurrence", ctypes.c_uint32),
    ]


class _RoutineSnapshot(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("snapshot_version", ctypes.c_uint32),
        ("routine_count", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32),
        ("routines", _RoutineProgress * 8),
    ]


@dataclass(frozen=True)
class PersonalityInput:
    """Validated environmental semantics supplied by core/sensor adapters."""

    monotonic_time_ns: int
    local_second_of_day: int = 0
    circadian_valid: bool = False
    resting: bool = False
    quiet: bool = False
    user_present: bool = False
    task_active: bool = False
    paused: bool = False
    activity_load: float = 0.0
    task_engagement: float = 0.0
    social_engagement: float = 0.0
    novelty: float = 0.0
    external_urgency: float = 0.0
    attention_target_x: float | None = None
    attention_target_y: float | None = None
    attention_salience: float = 0.0


@dataclass(frozen=True)
class PersonalityIntent:
    """Semantic face intent; it carries no raw pixels or actuator authority."""

    monotonic_time_ns: int
    sequence: int
    expression: str
    micro_behavior: str
    reason_flags: int
    valence: float
    arousal: float
    confidence: float
    attention: float
    gaze_x: float | None
    gaze_y: float | None
    eyelid_open: float
    blink_rate_hz: float

    @property
    def sleeping(self) -> bool:
        return bool(self.reason_flags & ((1 << 1) | (1 << 2)))


class PersonalitySource(Protocol):
    backend_name: str

    def step(self, inputs: PersonalityInput) -> PersonalityIntent: ...

    def apply_event(self, event: int, strength: float = 1.0) -> bool: ...

    def snapshot(self) -> bytes: ...

    def restore(self, payload: bytes) -> bool: ...

    def close(self) -> None: ...


def safe_fallback_intent(
    monotonic_time_ns: int, sequence: int = 0
) -> PersonalityIntent:
    return PersonalityIntent(
        monotonic_time_ns=max(0, int(monotonic_time_ns)),
        sequence=max(0, int(sequence)),
        expression="calm",
        micro_behavior="settled",
        reason_flags=1 << 10,
        valence=0.0,
        arousal=0.18,
        confidence=0.5,
        attention=0.24,
        gaze_x=None,
        gaze_y=None,
        eyelid_open=1.0,
        blink_rate_hz=0.22,
    )


class FallbackPersonalitySource:
    """Safe degraded presentation used when native personality is unavailable."""

    backend_name = "safe-calm-fallback"

    def __init__(self) -> None:
        self._sequence = 0

    def step(self, inputs: PersonalityInput) -> PersonalityIntent:
        self._sequence += 1
        intent = safe_fallback_intent(inputs.monotonic_time_ns, self._sequence)
        # Mirror the native quiet interval for library failure/restart. This
        # fallback is presentation only and can never admit speech or motion.
        circadian_quiet = (
            inputs.circadian_valid is True
            and type(inputs.local_second_of_day) is int
            and 0 <= inputs.local_second_of_day < 86400
        ) and (2 * 3600 <= inputs.local_second_of_day < 8 * 3600)
        if inputs.quiet is True or circadian_quiet:
            return replace(
                intent,
                expression="tired",
                micro_behavior="drowsy",
                reason_flags=intent.reason_flags
                | (int(circadian_quiet) << 1)
                | (int(inputs.quiet is True) << 2),
                gaze_x=0.0,
                gaze_y=0.0,
                attention=0.0,
                arousal=0.0,
                eyelid_open=0.0,
                blink_rate_hz=0.0,
            )
        return intent

    def snapshot(self) -> bytes:
        return b""

    def apply_event(self, event: int, strength: float = 1.0) -> bool:
        if (
            isinstance(event, bool)
            or not isinstance(event, int)
            or not 0 <= event <= 13
        ):
            raise ValueError("event must be a known personality event integer")
        if not math.isfinite(strength) or not 0.0 < strength <= 1.0:
            raise ValueError("event strength must be finite and in (0, 1]")
        return False

    def restore(self, payload: bytes) -> bool:
        return not payload

    def close(self) -> None:
        return None


def _default_library_candidates() -> tuple[Path, ...]:
    install_root = Path(__file__).resolve().parents[2]
    name = "libsherman_personality_c.so"
    return (
        install_root / "lib" / name,
        Path("/opt/sherman/lib") / name,
    )


class NativePersonalitySource:
    """Strict ctypes consumer of the versioned native personality C ABI."""

    backend_name = "native-personality-c-v1"

    def __init__(
        self,
        library_path: str | os.PathLike[str] | None = None,
        *,
        seed: int = 0x534845524D414E,
        library_loader: Callable[[str], object] = ctypes.CDLL,
    ) -> None:
        requested = Path(library_path) if library_path else None
        environment = os.environ.get("SHERMAN_PERSONALITY_LIBRARY")
        if requested is not None:
            candidates = (requested,)
        elif environment:
            candidates = (Path(environment),)
        else:
            candidates = _default_library_candidates()
        selected = next((path for path in candidates if path.is_file()), None)
        if selected is None:
            joined = ", ".join(str(path) for path in candidates)
            raise FileNotFoundError(f"personality library not found: {joined}")

        self.library_path = selected
        if isinstance(seed, bool) or not 0 <= int(seed) <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("personality seed must be in uint64 range")
        self._library = library_loader(str(selected))
        self._configure_api()
        self._validate_api()

        config = _Config(struct_size=ctypes.sizeof(_Config))
        status = self._library.sherman_personality_default_config(ctypes.byref(config))
        if status != 0:
            raise PersonalityRuntimeError(
                f"personality default config failed with status {status}"
            )
        config.seed = int(seed) & 0xFFFFFFFFFFFFFFFF
        self._seed = int(config.seed)
        self._handle = self._library.sherman_personality_create(ctypes.byref(config))
        if not self._handle:
            raise PersonalityRuntimeError("personality runtime creation failed")

    def _configure_api(self) -> None:
        library = self._library
        for name in (
            "sherman_personality_api_version",
            "sherman_personality_config_size",
            "sherman_personality_input_size",
            "sherman_personality_output_size",
            "sherman_personality_snapshot_size",
            "sherman_personality_policy_snapshot_size",
            "sherman_personality_routine_snapshot_size",
        ):
            function = getattr(library, name)
            function.argtypes = []
            function.restype = ctypes.c_uint32
        library.sherman_personality_default_config.argtypes = [ctypes.POINTER(_Config)]
        library.sherman_personality_default_config.restype = ctypes.c_int32
        library.sherman_personality_create.argtypes = [ctypes.POINTER(_Config)]
        library.sherman_personality_create.restype = ctypes.c_void_p
        library.sherman_personality_destroy.argtypes = [ctypes.c_void_p]
        library.sherman_personality_destroy.restype = None
        library.sherman_personality_reset.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
        library.sherman_personality_reset.restype = ctypes.c_int32
        library.sherman_personality_apply_event.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int32,
            ctypes.c_float,
        ]
        library.sherman_personality_apply_event.restype = ctypes.c_int32
        library.sherman_personality_step.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_Input),
            ctypes.POINTER(_Output),
        ]
        library.sherman_personality_step.restype = ctypes.c_int32
        library.sherman_personality_snapshot_state.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_Snapshot),
        ]
        library.sherman_personality_snapshot_state.restype = ctypes.c_int32
        library.sherman_personality_restore.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_Snapshot),
        ]
        library.sherman_personality_restore.restype = ctypes.c_int32
        library.sherman_personality_snapshot_policy.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_PolicySnapshot),
        ]
        library.sherman_personality_snapshot_policy.restype = ctypes.c_int32
        library.sherman_personality_restore_policy.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_PolicySnapshot),
        ]
        library.sherman_personality_restore_policy.restype = ctypes.c_int32
        library.sherman_personality_snapshot_routines.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_RoutineSnapshot),
        ]
        library.sherman_personality_snapshot_routines.restype = ctypes.c_int32
        library.sherman_personality_restore_routines.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_RoutineSnapshot),
        ]
        library.sherman_personality_restore_routines.restype = ctypes.c_int32

    def _validate_api(self) -> None:
        library = self._library
        version = int(library.sherman_personality_api_version())
        if version != PERSONALITY_API_VERSION:
            raise PersonalityRuntimeError(
                f"personality API mismatch: expected 0x{PERSONALITY_API_VERSION:08x}, "
                f"got 0x{version:08x}"
            )
        expected_sizes = (
            ("config", ctypes.sizeof(_Config), library.sherman_personality_config_size),
            ("input", ctypes.sizeof(_Input), library.sherman_personality_input_size),
            ("output", ctypes.sizeof(_Output), library.sherman_personality_output_size),
            (
                "snapshot",
                ctypes.sizeof(_Snapshot),
                library.sherman_personality_snapshot_size,
            ),
            (
                "policy snapshot",
                ctypes.sizeof(_PolicySnapshot),
                library.sherman_personality_policy_snapshot_size,
            ),
            (
                "routine snapshot",
                ctypes.sizeof(_RoutineSnapshot),
                library.sherman_personality_routine_snapshot_size,
            ),
        )
        for label, expected, query in expected_sizes:
            actual = int(query())
            if actual != expected:
                raise PersonalityRuntimeError(
                    f"personality {label} ABI size mismatch: expected {expected}, got {actual}"
                )

    @staticmethod
    def _checked_unit(value: float, label: str) -> float:
        value = float(value)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"{label} must be finite and in [0, 1]")
        return value

    @classmethod
    def _to_native_input(cls, inputs: PersonalityInput) -> _Input:
        if not 0 <= inputs.monotonic_time_ns <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("monotonic_time_ns is outside uint64 range")
        if not 0 <= inputs.local_second_of_day < 86_400:
            raise ValueError("local_second_of_day must be in [0, 86400)")
        attention_valid = inputs.attention_target_x is not None
        if attention_valid != (inputs.attention_target_y is not None):
            raise ValueError(
                "attention target coordinates must both be present or absent"
            )
        for value, label in (
            (inputs.circadian_valid, "circadian_valid"),
            (inputs.resting, "resting"),
            (inputs.quiet, "quiet"),
            (inputs.user_present, "user_present"),
            (inputs.task_active, "task_active"),
            (inputs.paused, "paused"),
        ):
            if not isinstance(value, bool):
                raise ValueError(f"{label} must be a boolean")
        attention_x = (
            0.0
            if inputs.attention_target_x is None
            else float(inputs.attention_target_x)
        )
        attention_y = (
            0.0
            if inputs.attention_target_y is None
            else float(inputs.attention_target_y)
        )
        if not math.isfinite(attention_x) or not -1.0 <= attention_x <= 1.0:
            raise ValueError("attention_target_x must be finite and in [-1, 1]")
        if not math.isfinite(attention_y) or not -1.0 <= attention_y <= 1.0:
            raise ValueError("attention_target_y must be finite and in [-1, 1]")

        flags = 0
        for enabled, bit in (
            (inputs.resting, 0),
            (inputs.quiet, 1),
            (inputs.user_present, 2),
            (inputs.task_active, 3),
            (inputs.paused, 4),
            (attention_valid, 5),
            (inputs.circadian_valid, 6),
        ):
            if enabled:
                flags |= 1 << bit

        return _Input(
            struct_size=ctypes.sizeof(_Input),
            flags=flags,
            monotonic_time_ns=inputs.monotonic_time_ns,
            local_second_of_day=inputs.local_second_of_day,
            reserved=0,
            activity_load=cls._checked_unit(inputs.activity_load, "activity_load"),
            task_engagement=cls._checked_unit(
                inputs.task_engagement, "task_engagement"
            ),
            social_engagement=cls._checked_unit(
                inputs.social_engagement, "social_engagement"
            ),
            novelty=cls._checked_unit(inputs.novelty, "novelty"),
            external_urgency=cls._checked_unit(
                inputs.external_urgency, "external_urgency"
            ),
            attention_target_x=attention_x,
            attention_target_y=attention_y,
            attention_salience=cls._checked_unit(
                inputs.attention_salience, "attention_salience"
            ),
        )

    @staticmethod
    def _intent(output: _Output) -> PersonalityIntent:
        if output.api_version != PERSONALITY_API_VERSION:
            raise PersonalityRuntimeError("personality returned an incompatible output")
        if not 0 <= output.expression < len(_EXPRESSIONS):
            raise PersonalityRuntimeError("personality returned an unknown expression")
        if not 0 <= output.micro_behavior < len(_MICRO_BEHAVIORS):
            raise PersonalityRuntimeError(
                "personality returned an unknown micro-behavior"
            )
        values = (
            output.valence,
            output.arousal,
            output.confidence,
            output.attention,
            output.gaze_x,
            output.gaze_y,
            output.eyelid_open,
            output.blink_rate_hz,
        )
        if not all(math.isfinite(value) for value in values):
            raise PersonalityRuntimeError("personality returned non-finite semantics")
        if not -1.0 <= output.valence <= 1.0:
            raise PersonalityRuntimeError("personality valence is outside [-1, 1]")
        for value, label in (
            (output.arousal, "arousal"),
            (output.confidence, "confidence"),
            (output.attention, "attention"),
            (output.eyelid_open, "eyelid_open"),
        ):
            if not 0.0 <= value <= 1.0:
                raise PersonalityRuntimeError(f"personality {label} is outside [0, 1]")
        if not -1.0 <= output.gaze_x <= 1.0 or not -1.0 <= output.gaze_y <= 1.0:
            raise PersonalityRuntimeError("personality gaze is outside [-1, 1]")
        if not 0.0 <= output.blink_rate_hz <= 2.0:
            raise PersonalityRuntimeError("personality blink rate is outside [0, 2]")
        return PersonalityIntent(
            monotonic_time_ns=int(output.monotonic_time_ns),
            sequence=int(output.sequence),
            expression=_EXPRESSIONS[output.expression],
            micro_behavior=_MICRO_BEHAVIORS[output.micro_behavior],
            reason_flags=int(output.reason_flags),
            valence=float(output.valence),
            arousal=float(output.arousal),
            confidence=float(output.confidence),
            attention=float(output.attention),
            gaze_x=float(output.gaze_x),
            gaze_y=float(output.gaze_y),
            eyelid_open=float(output.eyelid_open),
            blink_rate_hz=float(output.blink_rate_hz),
        )

    def step(self, inputs: PersonalityInput) -> PersonalityIntent:
        if not getattr(self, "_handle", None):
            raise PersonalityRuntimeError("personality runtime is closed")
        native_input = self._to_native_input(inputs)
        output = _Output(struct_size=ctypes.sizeof(_Output))
        status = self._library.sherman_personality_step(
            self._handle, ctypes.byref(native_input), ctypes.byref(output)
        )
        if status != 0:
            raise PersonalityRuntimeError(
                f"personality step failed with status {status}"
            )
        return self._intent(output)

    def apply_event(self, event: int, strength: float = 1.0) -> bool:
        if not getattr(self, "_handle", None):
            raise PersonalityRuntimeError("personality runtime is closed")
        if (
            isinstance(event, bool)
            or not isinstance(event, int)
            or not 0 <= event <= 13
        ):
            raise ValueError("event must be a known personality event integer")
        if not math.isfinite(strength) or not 0.0 < strength <= 1.0:
            raise ValueError("event strength must be finite and in (0, 1]")
        status = int(
            self._library.sherman_personality_apply_event(
                self._handle, int(event), float(strength)
            )
        )
        if status == 1:
            return False
        if status != 0:
            raise PersonalityRuntimeError(
                f"personality event failed with status {status}"
            )
        return True

    def snapshot(self) -> bytes:
        if not getattr(self, "_handle", None):
            raise PersonalityRuntimeError("personality runtime is closed")
        snapshot = _Snapshot(struct_size=ctypes.sizeof(_Snapshot))
        status = self._library.sherman_personality_snapshot_state(
            self._handle, ctypes.byref(snapshot)
        )
        if status != 0:
            raise PersonalityRuntimeError(
                f"personality snapshot failed with status {status}"
            )
        policy = _PolicySnapshot(struct_size=ctypes.sizeof(_PolicySnapshot))
        status = self._library.sherman_personality_snapshot_policy(
            self._handle, ctypes.byref(policy)
        )
        if status != 0:
            raise PersonalityRuntimeError(
                f"personality policy snapshot failed with status {status}"
            )
        state_bytes = ctypes.string_at(ctypes.byref(snapshot), ctypes.sizeof(snapshot))
        policy_bytes = ctypes.string_at(ctypes.byref(policy), ctypes.sizeof(policy))
        routines = _RoutineSnapshot(struct_size=ctypes.sizeof(_RoutineSnapshot))
        status = self._library.sherman_personality_snapshot_routines(
            self._handle, ctypes.byref(routines)
        )
        if status != 0:
            raise PersonalityRuntimeError(
                f"personality routine snapshot failed with status {status}"
            )
        routine_bytes = ctypes.string_at(
            ctypes.byref(routines), ctypes.sizeof(routines)
        )
        return (
            _NATIVE_STATE_HEADER.pack(
                _NATIVE_STATE_MAGIC,
                _NATIVE_STATE_VERSION,
                len(state_bytes),
                len(policy_bytes),
                len(routine_bytes),
            )
            + state_bytes
            + policy_bytes
            + routine_bytes
        )

    def restore(self, payload: bytes) -> bool:
        state_size = ctypes.sizeof(_Snapshot)
        policy_size = ctypes.sizeof(_PolicySnapshot)
        routine_size = ctypes.sizeof(_RoutineSnapshot)
        policy_payload: bytes | None = None
        routine_payload: bytes | None = None
        if len(payload) == state_size:
            # Compatibility with the first bring-up snapshot, before policy
            # repetition state existed.
            state_payload = payload
        elif len(payload) >= _NATIVE_STATE_V1_HEADER.size:
            magic, version = struct.unpack_from(">8sH", payload)
            if magic != _NATIVE_STATE_MAGIC:
                return False
            if version == _NATIVE_STATE_VERSION:
                if len(payload) < _NATIVE_STATE_HEADER.size:
                    return False
                (
                    _magic,
                    _version,
                    encoded_state_size,
                    encoded_policy_size,
                    encoded_routine_size,
                ) = _NATIVE_STATE_HEADER.unpack_from(payload)
                if (
                    encoded_state_size != state_size
                    or encoded_policy_size != policy_size
                    or encoded_routine_size != routine_size
                    or len(payload)
                    != _NATIVE_STATE_HEADER.size
                    + state_size
                    + policy_size
                    + routine_size
                ):
                    return False
                offset = _NATIVE_STATE_HEADER.size
                state_payload = payload[offset : offset + state_size]
                policy_start = offset + state_size
                routine_start = policy_start + policy_size
                policy_payload = payload[policy_start:routine_start]
                routine_payload = payload[routine_start:]
            elif version == 1:
                (
                    _magic,
                    _version,
                    encoded_state_size,
                    encoded_policy_size,
                ) = _NATIVE_STATE_V1_HEADER.unpack_from(payload)
                if (
                    encoded_state_size != state_size
                    or encoded_policy_size != policy_size
                    or len(payload)
                    != _NATIVE_STATE_V1_HEADER.size + state_size + policy_size
                ):
                    return False
                offset = _NATIVE_STATE_V1_HEADER.size
                state_payload = payload[offset : offset + state_size]
                policy_payload = payload[offset + state_size :]
            else:
                return False
        else:
            return False

        snapshot = _Snapshot.from_buffer_copy(state_payload)
        state_status = int(
            self._library.sherman_personality_restore(
                self._handle, ctypes.byref(snapshot)
            )
        )
        policy_status = 0
        if state_status == 0 and policy_payload is not None:
            policy = _PolicySnapshot.from_buffer_copy(policy_payload)
            policy_status = int(
                self._library.sherman_personality_restore_policy(
                    self._handle, ctypes.byref(policy)
                )
            )
        routine_status = 0
        if state_status == 0 and policy_status == 0 and routine_payload is not None:
            routines = _RoutineSnapshot.from_buffer_copy(routine_payload)
            routine_status = int(
                self._library.sherman_personality_restore_routines(
                    self._handle, ctypes.byref(routines)
                )
            )
        if state_status == 0 and policy_status == 0 and routine_status == 0:
            return True
        self._library.sherman_personality_reset(self._handle, self._seed)
        return False

    def close(self) -> None:
        handle = getattr(self, "_handle", None)
        if handle:
            self._library.sherman_personality_destroy(handle)
            self._handle = None

    def __enter__(self) -> "NativePersonalitySource":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()


class PersonalityStateStore:
    """Atomic, checksummed, size-bounded storage for the native snapshot."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)

    def load(self) -> bytes | None:
        try:
            with self.path.open("rb") as stream:
                encoded = stream.read(MAX_STATE_BYTES + 1)
        except FileNotFoundError:
            return None
        if len(encoded) < _STATE_HEADER.size or len(encoded) > MAX_STATE_BYTES:
            raise ValueError("personality state has an invalid size")
        magic, version, payload_size, checksum = _STATE_HEADER.unpack_from(encoded)
        payload = encoded[_STATE_HEADER.size :]
        if magic != _STATE_MAGIC or version != _STATE_ENVELOPE_VERSION:
            raise ValueError("personality state envelope is incompatible")
        if payload_size != len(payload):
            raise ValueError("personality state payload size is inconsistent")
        if zlib.crc32(payload) & 0xFFFFFFFF != checksum:
            raise ValueError("personality state checksum does not match")
        return payload

    def save(self, payload: bytes) -> None:
        if not payload:
            return
        encoded = (
            _STATE_HEADER.pack(
                _STATE_MAGIC,
                _STATE_ENVELOPE_VERSION,
                len(payload),
                zlib.crc32(payload) & 0xFFFFFFFF,
            )
            + payload
        )
        if len(encoded) > MAX_STATE_BYTES:
            raise ValueError("personality state exceeds its 4096-byte bound")
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            try:
                directory = os.open(self.path.parent, os.O_RDONLY)
            except OSError:
                return
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
