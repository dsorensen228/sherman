"""Bounded local wake leases affect presentation, never native quiet policy."""

from __future__ import annotations

import json
import math
from pathlib import Path
import re

from runtime.personality_adapter import PersonalityIntent


class ManualWakeReader:
    def __init__(self, path: Path, started_s: float):
        self.path = path
        self.started_s = started_s
        self._next_read_s = started_s
        self._request_id = ""
        self._expires_s = 0.0

    def update(self, now_s: float, intent: PersonalityIntent, *, degraded: bool) -> str:
        if now_s >= self._next_read_s:
            self._next_read_s = now_s + 0.1
            self._request_id = ""
            try:
                with self.path.open("rb") as stream:
                    raw = stream.read(1025)
                if len(raw) > 1024:
                    raise ValueError("oversized wake request")
                request = json.loads(raw)
                if not isinstance(request, dict) or set(request) != {
                    "schema_version",
                    "request_id",
                    "issued_at_monotonic_s",
                    "expires_at_monotonic_s",
                }:
                    raise ValueError("invalid wake shape")
                issued = request["issued_at_monotonic_s"]
                expires = request["expires_at_monotonic_s"]
                request_id = request["request_id"]
                if (
                    type(request["schema_version"]) is not int
                    or request["schema_version"] != 1
                    or not isinstance(request_id, str)
                    or re.fullmatch(r"[a-f0-9]{32}", request_id) is None
                    or type(issued) not in (int, float)
                    or type(expires) not in (int, float)
                    or not math.isfinite(issued)
                    or not math.isfinite(expires)
                    or not self.started_s <= issued <= now_s < expires
                    or not 0 < expires - issued <= 300
                ):
                    raise ValueError("invalid wake lease")
                self._request_id = request_id
                self._expires_s = expires
            except (OSError, ValueError, TypeError, OverflowError):
                pass
        # The existing manual exception is circadian-only. Explicit quiet,
        # pause, tasks, fallback, startup and unknown reasons still win.
        allowed_reasons = (1 << 1) | (1 << 7)
        if (
            degraded
            or now_s >= self._expires_s
            or intent.reason_flags & ~allowed_reasons
            or intent.micro_behavior
            not in {"settled", "orienting", "observing", "drowsy"}
            or (
                intent.micro_behavior == "drowsy" and not intent.reason_flags & (1 << 1)
            )
        ):
            return ""
        return self._request_id
