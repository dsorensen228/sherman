"""Wait for the face to wake before a deliberate exchange, then release it."""

from pathlib import Path
import time

from .config import read_json
from .runtime import write_json


class ManualWake:
    def __init__(self, config, ready, awake, *, clock=time.monotonic, pause=time.sleep):
        self.config = config
        self.ready = ready
        self.awake = awake
        self.clock = clock
        self.pause = pause
        self.request_id = ""

    def begin(self, request_id):
        self.request_id = request_id
        issued = self.clock()
        write_json(
            self.config.wake_request_file,
            {
                "schema_version": 1,
                "request_id": request_id,
                "issued_at_monotonic_s": issued,
                "expires_at_monotonic_s": issued + 300,
            },
        )
        while self.clock() - issued < 6.0:
            if not self.ready():
                return False
            if self.is_awake():
                return True
            self.pause(0.05)
        return False

    def is_awake(self):
        try:
            return (
                self.awake()
                and read_json(self.config.face_health_file, 4096).get("wake_request_id")
                == self.request_id
            )
        except (OSError, ValueError, AttributeError):
            return False

    def end(self):
        Path(self.config.wake_request_file).unlink(missing_ok=True)
        self.request_id = ""
