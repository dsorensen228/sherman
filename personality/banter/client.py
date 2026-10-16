"""Bounded authenticated Jarvis HTTP; failed script/reply calls are never retried."""

from __future__ import annotations

import json
import os
import re
import time
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .audio import EMOTIONS
from .config import read_json


def validate_exchange(raw):
    if not isinstance(raw, dict) or set(raw) != {"sherman", "emotion", "jarvis"}:
        raise ValueError("invalid exchange shape")
    for name, maximum in (("sherman", 180), ("jarvis", 240)):
        text = raw[name]
        if (
            not isinstance(text, str)
            or not text.strip()
            or len(text) > maximum
            or any(ord(c) < 32 for c in text)
        ):
            raise ValueError("invalid dialogue text")
    if raw["emotion"] not in EMOTIONS or len(raw["jarvis"].split()) > 30:
        raise ValueError("invalid exchange delivery")
    return dict(raw)


def validate_script(raw, source: str, target: str):
    if not isinstance(raw, dict) or type(raw.get("schema_version")) is not int:
        raise ValueError("missing script version")
    if raw["schema_version"] != 1:
        raise ValueError("unsupported script version")
    if raw.get("source_device_id") != source or raw.get("response_device_id") != target:
        raise ValueError("script device mismatch")
    script_id = raw.get("script_id")
    if not isinstance(script_id, str) or not re.fullmatch(r"[a-f0-9]{32}", script_id):
        raise ValueError("invalid script ID")
    ttl = raw.get("expires_in_seconds")
    if type(ttl) is not int or not 1 <= ttl <= 180:
        raise ValueError("invalid script expiry")
    exchanges = raw.get("exchanges")
    if not isinstance(exchanges, list) or not 1 <= len(exchanges) <= 2:
        raise ValueError("invalid exchange count")
    initiator = raw.get("initiator", "sherman")
    if initiator not in ("sherman", "jarvis"):
        raise ValueError("invalid initiator")
    return {
        **raw,
        "initiator": initiator,
        "exchanges": [validate_exchange(item) for item in exchanges],
    }


def validate_trigger(raw):
    if not isinstance(raw, dict) or "trigger_id" not in raw:
        raise ValueError("missing trigger ID")
    trigger_id = raw["trigger_id"]
    if trigger_id is not None and (
        not isinstance(trigger_id, str) or not re.fullmatch(r"[a-f0-9]{32}", trigger_id)
    ):
        raise ValueError("invalid trigger ID")
    return trigger_id


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward credentials to another origin or silently replay a POST.
        return None


class JarvisClient:
    def __init__(self, config):
        self.config = config
        self.opener = build_opener(NoRedirect())
        self.token = ""
        self.token_until = 0.0

    def _post(self, path: str, body, *, authenticated=True, timeout=60):
        headers = {"Content-Type": "application/json"}
        if authenticated:
            self._authenticate(timeout=timeout)
            headers["Authorization"] = "Bearer " + self.token
        data = json.dumps(body, separators=(",", ":")).encode()
        request = Request(
            self.config.api_url.rstrip("/") + path, data=data, headers=headers
        )
        with self.opener.open(request, timeout=timeout) as response:
            encoded = response.read(16385)
        if len(encoded) > 16384:
            raise ValueError("Jarvis response too large")
        return json.loads(encoded)

    def _authenticate(self, *, timeout=60):
        if self.token and time.monotonic() < self.token_until:
            return
        if os.stat(self.config.credentials_file).st_mode & 0o077:
            raise ValueError("credentials file must be private (chmod 600)")
        credentials = read_json(self.config.credentials_file, 4096)
        if (
            not isinstance(credentials, dict)
            or set(credentials) != {"username", "password"}
            or any(not isinstance(v, str) or not v for v in credentials.values())
        ):
            raise ValueError("invalid credential file")
        result = self._post(
            "/v1/auth/token", credentials, authenticated=False, timeout=timeout
        )
        token = result.get("access_token")
        if not isinstance(token, str) or not 1 <= len(token) <= 8192:
            raise ValueError("invalid access token")
        self.token = token
        self.token_until = time.monotonic() + max(
            0, min(3600, int(result["expires_in"]) - 60)
        )

    def poll(self, *, ready: bool, result=None):
        body = {
            "source_device_id": self.config.source_device_id,
            "response_device_id": self.config.response_device_id,
            "ready": ready,
        }
        if result is not None:
            body["result"] = result
        try:
            return validate_trigger(self._post("/v1/banter/poll", body, timeout=3))
        except Exception:
            self.token_until = 0
            raise

    def create(self, recent, trigger_id=None):
        self._authenticate()
        body = {
            "source_device_id": self.config.source_device_id,
            "response_device_id": self.config.response_device_id,
            "recent_exchanges": recent,
        }
        if trigger_id is not None:
            body["trigger_id"] = validate_trigger({"trigger_id": trigger_id})
        try:
            raw = self._post(
                "/v1/banter/scripts",
                body,
            )
            return validate_script(
                raw, self.config.source_device_id, self.config.response_device_id
            )
        except Exception:
            self.token_until = 0
            raise

    def reply(self, script_id: str, index: int):
        result = self._post(f"/v1/banter/scripts/{script_id}/replies/{index}", {})
        if (
            result.get("status") != "played"
            or result.get("script_id") != script_id
            or result.get("exchange_index") != index
        ):
            raise RuntimeError("Jarvis playback was not acknowledged")
