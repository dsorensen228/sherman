"""Stationary idle admission, randomized cadence, and sequential script execution."""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path

from .client import validate_exchange
from .config import read_json


def write_json(path, value):
    encoded = json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode()
    if len(encoded) > 16384:
        raise ValueError("state record too large")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + f".{os.getpid()}.tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def face_is_idle(path: str, wall_clock=time.time) -> bool:
    try:
        age = wall_clock() - os.stat(path).st_mtime
        status = read_json(path, 4096)
        return (
            0 <= age <= 15
            and status.get("state") == "running"
            and status.get("mode") == "personality"
            and status.get("personality_degraded") is False
            and status.get("micro_behavior") in {"settled", "orienting", "observing"}
            and type(status.get("reason_flags")) is int
            and status["reason_flags"] in {0, 1 << 7}
        )
    except (OSError, ValueError, AttributeError):
        return False


class Scheduler:
    def __init__(self, config, clock=time.monotonic, rng=None):
        self.config = config
        self.clock = clock
        # OS entropy in production; deterministic streams are injected in tests.
        self.rng = rng if rng is not None else random.Random()
        self.next_at = 0.0
        self.reschedule()

    def reschedule(self):
        gap = self.config.minimum_interval_s + self.rng.expovariate(
            1.0 / (self.config.mean_interval_s - self.config.minimum_interval_s)
        )
        self.next_at = self.clock() + gap

    def due(self):
        if self.clock() < self.next_at:
            return False
        self.reschedule()
        return True


class Interaction:
    def __init__(
        self, config, client, speaker, allowed, clock=time.monotonic, pause=time.sleep
    ):
        self.config = config
        self.client = client
        self.speaker = speaker
        self.allowed = allowed
        self.clock = clock
        self.pause = pause
        self.recent = []
        self.last_status = "waiting"
        self.last_error_type = ""
        self.last_error_stage = ""
        self.last_http_status = 0
        self.report = lambda: None
        self.completed = 0
        self.attempts = 0
        self.last_script_id = ""
        try:
            history = read_json(config.history_file, 16384)
            if not isinstance(history, list) or len(history) > 8:
                raise ValueError("invalid history")
            self.recent = [validate_exchange(item) for item in history]
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError):
            self.last_error_type = "HistoryInvalid"

    def run_once(self):
        if not self.allowed():
            self.last_status = "skipped_not_idle"
            return False
        self.attempts += 1
        self.last_error_type = ""
        self.last_error_stage = ""
        self.last_http_status = 0
        started = self.clock()
        try:
            self.last_status = "generating"
            self.report()
            script = self.client.create(self.recent)
            self.last_script_id = script["script_id"]
            deadline = started + script["expires_in_seconds"]

            def permitted():
                return self.allowed() and self.clock() < deadline

            for index, exchange in enumerate(script["exchanges"]):
                if not permitted():
                    raise RuntimeError("idle admission or script expired")
                self.last_status = "sherman_speaking"
                self.report()
                self.speaker.play(exchange, f"{script['script_id']}:{index}", permitted)
                self.pause(0.35)
                if not permitted():
                    raise RuntimeError("idle admission or script expired")
                self.last_status = "jarvis_speaking"
                self.report()
                self.client.reply(script["script_id"], index)
                # Remember only content already performed, including a partial script.
                self.recent = (self.recent + [exchange])[-8:]
                write_json(self.config.history_file, self.recent)
                self.pause(0.45)
            self.completed += 1
            self.last_status = "completed"
            return True
        except Exception as error:
            # No fallback dialogue and no retry of an ambiguous playback result.
            self.last_error_stage = self.last_status
            self.last_http_status = getattr(error, "code", 0)
            self.last_status = "skipped_or_interrupted"
            self.last_error_type = type(error).__name__
            return False

    def health(self, scheduler):
        return {
            "schema_version": 1,
            "state": "running",
            "enabled": self.config.enabled,
            "status": self.last_status,
            "attempts": self.attempts,
            "completed": self.completed,
            "last_script_id": self.last_script_id,
            "last_error_type": self.last_error_type,
            "last_error_stage": self.last_error_stage,
            "last_http_status": self.last_http_status,
            "response_device_id": self.config.response_device_id,
            "next_in_seconds": round(max(0, scheduler.next_at - self.clock())),
        }
