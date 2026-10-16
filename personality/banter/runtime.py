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


def face_is_idle(
    path: str,
    wall_clock=time.time,
    *,
    allow_circadian_quiet: bool = False,
    allow_sleep: bool = False,
) -> bool:
    try:
        age = wall_clock() - os.stat(path).st_mtime
        status = read_json(path, 4096)
        reasons = status.get("reason_flags")
        if type(reasons) is not int:
            return False
        allowed_reasons = 1 << 7  # Spontaneous idle motion of the eyes.
        behaviors = {"settled", "orienting", "observing"}
        if allow_circadian_quiet:
            # A deliberate request can speak at night. Explicit quiet, pause,
            # tasks, low energy, faults and unknown reasons still fail closed.
            allowed_reasons |= 1 << 1
            if reasons & (1 << 1):
                behaviors.add("drowsy")
        return (
            0 <= age <= 15
            and status.get("state") == "running"
            and status.get("mode") == "personality"
            and status.get("personality_degraded") is False
            and (
                status.get("sleep_state") == "awake"
                or (
                    allow_sleep
                    and allow_circadian_quiet
                    and reasons & (1 << 1)
                    and status.get("sleep_state")
                    in {"falling_asleep", "sleeping", "waking_up"}
                )
            )
            and status.get("micro_behavior") in behaviors
            and reasons & ~allowed_reasons == 0
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


class ManualTriggers:
    """Poll one bounded request at a time using deliberate-request admission."""

    def __init__(self, client, interaction, scheduler, clock=time.monotonic, rng=None):
        self.client = client
        self.interaction = interaction
        self.scheduler = scheduler
        self.clock = clock
        self.rng = rng if rng is not None else random.Random()
        self.next_at = 0.0
        self.result = None
        self.failures = 0
        self.attempts = 0
        self.last_error_type = ""
        self.last_http_status = 0
        self.last_trigger_id = ""

    def tick(self):
        if self.clock() < self.next_at:
            return False
        self.attempts += 1
        try:
            trigger_id = self.client.poll(
                ready=self.interaction.manual_ready(), result=self.result
            )
        except Exception as error:
            self.failures = min(self.failures + 1, 5)
            delay = min(60.0, 5 * 2 ** (self.failures - 1))
            self.next_at = self.clock() + min(60.0, delay * self.rng.uniform(0.8, 1.2))
            self.last_error_type = type(error).__name__
            self.last_http_status = getattr(error, "code", 0)
            return False
        self.failures = 0
        self.last_error_type = ""
        self.last_http_status = 0
        self.next_at = self.clock() + 5.0
        self.result = None
        if trigger_id is None:
            return False
        self.last_trigger_id = trigger_id
        # Manual requests consume the same daemon loop; they cannot overlap an
        # autonomous interaction, and a fresh interval prevents immediate chatter.
        self.scheduler.reschedule()
        success = self.interaction.run_once(trigger_id=trigger_id)
        self.result = {
            "trigger_id": trigger_id,
            "status": "completed" if success else "failed",
        }
        return True

    def health(self):
        return {
            "manual_poll_attempts": self.attempts,
            "manual_poll_failures": self.failures,
            "manual_poll_error_type": self.last_error_type,
            "manual_poll_http_status": self.last_http_status,
            "manual_last_trigger_id": self.last_trigger_id,
            "manual_result_pending": self.result is not None,
        }


class Interaction:
    def __init__(
        self,
        config,
        client,
        speaker,
        allowed,
        clock=time.monotonic,
        pause=time.sleep,
        *,
        manual_allowed=None,
        manual_ready=None,
        wake=None,
    ):
        self.config = config
        self.client = client
        self.speaker = speaker
        self.allowed = allowed
        self.manual_allowed = allowed if manual_allowed is None else manual_allowed
        self.manual_ready = (
            self.manual_allowed if manual_ready is None else manual_ready
        )
        self.wake = wake
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

    def run_once(self, trigger_id=None):
        allowed = self.allowed if trigger_id is None else self.manual_allowed
        ready = self.allowed if trigger_id is None else self.manual_ready
        if not ready():
            self.last_status = "skipped_not_idle"
            return False
        self.attempts += 1
        self.last_error_type = ""
        self.last_error_stage = ""
        self.last_http_status = 0
        started = self.clock()
        try:
            if trigger_id is not None and self.wake is not None:
                self.last_status = "waking_up"
                self.report()
                if not self.wake.begin(trigger_id):
                    raise RuntimeError("face did not acknowledge wake")
            self.last_status = "generating"
            self.report()
            script = (
                self.client.create(self.recent)
                if trigger_id is None
                else self.client.create(self.recent, trigger_id=trigger_id)
            )
            self.last_script_id = script["script_id"]
            deadline = started + script["expires_in_seconds"]

            def permitted():
                return (
                    allowed()
                    and self.clock() < deadline
                    and (
                        trigger_id is None or self.wake is None or self.wake.is_awake()
                    )
                )

            for index, exchange in enumerate(script["exchanges"]):
                if not permitted():
                    raise RuntimeError("idle admission or script expired")
                if script.get("initiator") == "jarvis":
                    self.last_status = "jarvis_speaking"
                    self.report()
                    self.client.reply(script["script_id"], index)
                    self.pause(0.35)
                    if not permitted():
                        raise RuntimeError("idle admission or script expired")
                    self.last_status = "sherman_speaking"
                    self.report()
                    self.speaker.play(
                        exchange, f"{script['script_id']}:{index}", permitted
                    )
                else:
                    self.last_status = "sherman_speaking"
                    self.report()
                    self.speaker.play(
                        exchange, f"{script['script_id']}:{index}", permitted
                    )
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

        finally:
            if trigger_id is not None and self.wake is not None:
                try:
                    self.wake.end()
                except OSError:
                    # The bounded lease still expires if /run becomes unwritable.
                    self.last_error_type = "WakeReleaseFailed"

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
