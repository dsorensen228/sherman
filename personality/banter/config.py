"""Bounded, non-secret configuration for Sherman's stationary chatter process."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Config:
    enabled: bool = False
    api_url: str = ""
    source_device_id: str = "robot-example"
    response_device_id: str = ""
    credentials_file: str = "/etc/sherman/jarvis-credentials.json"
    alsa_device: str = "plughw:0,0"
    volume: float = 0.50
    mean_interval_s: float = 3600.0
    minimum_interval_s: float = 900.0
    face_health_file: str = "/run/sherman-face.health.json"
    wake_request_file: str = "/run/sherman-wake.json"
    history_file: str = "/userdata/sherman/banter-history.json"
    health_file: str = "/run/sherman-banter.health.json"


def read_json(path: str | Path, limit: int = 8192):
    with open(path, "rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("JSON size limit exceeded")
    return json.loads(raw)


def load_config(path: str | Path) -> Config:
    raw = read_json(path)
    if not isinstance(raw, dict) or type(raw.get("schema_version")) is not int:
        raise ValueError("config requires integer schema_version")
    if raw.pop("schema_version") != 1 or set(raw) - set(Config.__dataclass_fields__):
        raise ValueError("unsupported config field or version")
    cfg = Config(**raw)
    if type(cfg.enabled) is not bool:
        raise ValueError("enabled must be boolean")
    for name in Config.__dataclass_fields__:
        if name in {"enabled", "volume", "mean_interval_s", "minimum_interval_s"}:
            continue
        value = getattr(cfg, name)
        if (
            not isinstance(value, str)
            or len(value) > 512
            or any(ord(c) < 32 for c in value)
        ):
            raise ValueError(f"invalid {name}")
    for name in ("volume", "mean_interval_s", "minimum_interval_s"):
        value = getattr(cfg, name)
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
    if not 0 < cfg.volume <= 0.50:
        raise ValueError("volume must be in (0, 0.50]")
    if not 300 <= cfg.minimum_interval_s < cfg.mean_interval_s <= 86400:
        raise ValueError("require 300 <= minimum_interval_s < mean_interval_s <= 86400")
    if not re.fullmatch(r"[a-zA-Z0-9_:,.-]{1,100}", cfg.alsa_device):
        raise ValueError("invalid ALSA device")
    for name in (
        "credentials_file",
        "face_health_file",
        "wake_request_file",
        "history_file",
        "health_file",
    ):
        if not Path(getattr(cfg, name)).is_absolute():
            raise ValueError(f"{name} must be absolute")
    if cfg.enabled:
        url = urlsplit(cfg.api_url)
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username
            or url.password
        ):
            raise ValueError("api_url must be an HTTP(S) origin without credentials")
        if url.path not in {"", "/"} or url.query or url.fragment:
            raise ValueError("api_url must be an origin")
        for value in (cfg.source_device_id, cfg.response_device_id):
            if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", value):
                raise ValueError(
                    "enabled banter requires source and response device IDs"
                )
    return cfg
