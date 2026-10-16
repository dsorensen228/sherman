"""Strict, bounded configuration for the production face service."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any


CONFIG_SCHEMA_VERSION = 1
MAX_CONFIG_BYTES = 8192


@dataclass(frozen=True)
class FaceRuntimeConfig:
    mode: str = "personality"
    expression: str = "calm"
    fps: float = 30.0
    spi_hz: int = 40_000_000
    renderer: str = "fast"
    renderer_library: str | None = None
    personality_library: str | None = None
    personality_required: bool = False
    personality_tick_hz: float = 10.0
    personality_state_file: str = "/var/lib/sherman/personality.state"
    wake_request_file: str = "/run/sherman-wake.json"
    persistence_interval_s: float = 300.0
    circadian_enabled: bool = False
    timezone: str | None = None
    full_frame: bool = False
    seed: int = 0x534845524D414E


_FIELDS = frozenset(FaceRuntimeConfig.__dataclass_fields__)


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _validate(raw: dict[str, Any]) -> FaceRuntimeConfig:
    unknown = set(raw) - _FIELDS - {"schema_version"}
    if unknown:
        raise ValueError(f"unknown face runtime config field: {sorted(unknown)[0]}")
    if raw.get("schema_version", CONFIG_SCHEMA_VERSION) != CONFIG_SCHEMA_VERSION:
        raise ValueError("unsupported face runtime config schema_version")

    defaults = FaceRuntimeConfig()
    merged = {name: raw.get(name, getattr(defaults, name)) for name in _FIELDS}
    if merged["mode"] not in ("personality", "manual", "demo"):
        raise ValueError("mode must be personality, manual, or demo")
    if merged["renderer"] not in ("auto", "fast", "reference"):
        raise ValueError("renderer must be auto, fast, or reference")
    if merged["expression"] not in (
        "calm",
        "curious",
        "focused",
        "pleased",
        "uncertain",
        "frustrated",
        "tired",
        "surprised",
    ):
        raise ValueError("expression is not recognized")
    for name in (
        "personality_required",
        "circadian_enabled",
        "full_frame",
    ):
        if not isinstance(merged[name], bool):
            raise ValueError(f"{name} must be a boolean")
    for name in (
        "renderer_library",
        "personality_library",
        "timezone",
    ):
        if merged[name] is not None and not isinstance(merged[name], str):
            raise ValueError(f"{name} must be a string or null")
    timezone = merged["timezone"]
    if timezone is not None and (
        not timezone
        or len(timezone) > 96
        or "\x00" in timezone
        or "\n" in timezone
        or "\r" in timezone
    ):
        raise ValueError("timezone must be a bounded single-line POSIX TZ string")
    if merged["circadian_enabled"] and timezone is None:
        raise ValueError("circadian_enabled requires an explicit timezone")
    if (
        not isinstance(merged["personality_state_file"], str)
        or not merged["personality_state_file"]
    ):
        raise ValueError("personality_state_file must be a non-empty string")
    wake_path = merged["wake_request_file"]
    if (
        not isinstance(wake_path, str)
        or len(wake_path) > 512
        or not Path(wake_path).is_absolute()
        or any(ord(c) < 32 for c in wake_path)
    ):
        raise ValueError("wake_request_file must be a bounded absolute path")

    merged["fps"] = _number(merged["fps"], "fps")
    merged["personality_tick_hz"] = _number(
        merged["personality_tick_hz"], "personality_tick_hz"
    )
    merged["persistence_interval_s"] = _number(
        merged["persistence_interval_s"], "persistence_interval_s"
    )
    if not 1.0 <= merged["fps"] <= 60.0:
        raise ValueError("fps must be in [1, 60]")
    if not 1.0 <= merged["personality_tick_hz"] <= 30.0:
        raise ValueError("personality_tick_hz must be in [1, 30]")
    if not 10.0 <= merged["persistence_interval_s"] <= 3600.0:
        raise ValueError("persistence_interval_s must be in [10, 3600]")

    for name in ("spi_hz", "seed"):
        if isinstance(merged[name], bool) or not isinstance(merged[name], int):
            raise ValueError(f"{name} must be an integer")
    if not 1_000_000 <= merged["spi_hz"] <= 50_000_000:
        raise ValueError("spi_hz must be in [1000000, 50000000]")
    if not 0 <= merged["seed"] <= 0xFFFFFFFFFFFFFFFF:
        raise ValueError("seed must be in uint64 range")
    return FaceRuntimeConfig(**merged)


def load_face_runtime_config(path: str | Path) -> FaceRuntimeConfig:
    config_path = Path(path)
    with config_path.open("rb") as stream:
        encoded = stream.read(MAX_CONFIG_BYTES + 1)
    if not encoded or len(encoded) > MAX_CONFIG_BYTES:
        raise ValueError("face runtime config must be 1..8192 bytes")
    try:
        raw = json.loads(encoded.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid face runtime JSON: {error}") from error
    if not isinstance(raw, dict):
        raise ValueError("face runtime config must be a JSON object")
    return _validate(raw)
