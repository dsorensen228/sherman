#!/usr/bin/env python3
"""Canonical codec and bounded read-only UART monitor. No motion CLI is exposed."""

import argparse
import binascii
import json
import os
import select
import struct
import termios
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = json.loads((ROOT / "proto/schema/controller-v1.json").read_text())
MESSAGES = SCHEMA["messages"]
BY_ID = {v["id"]: (k, v) for k, v in MESSAGES.items()}
HEADER = struct.Struct("<2sBBHIQ")


def encode(name, sequence, session, **values):
    msg = MESSAGES[name]
    if set(values) != set(msg["fields"]):
        raise ValueError("fields must exactly match the schema")
    payload = struct.pack("<" + msg["format"], *(values[k] for k in msg["fields"]))
    head = HEADER.pack(
        b"\xa5\x5a", SCHEMA["version"], msg["id"], len(payload), sequence, session
    )
    return (
        head + payload + struct.pack("<H", binascii.crc_hqx(head[2:] + payload, 0xFFFF))
    )


def decode(data):
    if len(data) < 20:
        raise ValueError("truncated frame")
    sync, version, kind, length, sequence, session = HEADER.unpack_from(data)
    if sync != b"\xa5\x5a" or version != SCHEMA["version"] or kind not in BY_ID:
        raise ValueError("unsupported frame")
    name, msg = BY_ID[kind]
    if (
        length > SCHEMA["max_payload"]
        or len(data) != 20 + length
        or length != struct.calcsize("<" + msg["format"])
    ):
        raise ValueError("bad length")
    if struct.unpack_from("<H", data, len(data) - 2)[0] != binascii.crc_hqx(
        data[2:-2], 0xFFFF
    ):
        raise ValueError("bad CRC")
    values = struct.unpack("<" + msg["format"], data[18:-2])
    return {
        "type": name,
        "sequence": sequence,
        "session": session,
        "payload": dict(zip(msg["fields"], values)),
    }


class Stream:
    def __init__(self):
        self.buffer = bytearray()
        self.last = 0.0
        self.errors = 0

    def feed(self, data, now):
        if self.buffer and now - self.last > 0.02:
            self.buffer.clear()
            self.errors += 1
        self.last = now
        frames = []
        for byte in data:
            self.buffer.append(byte)
            while self.buffer and self.buffer[:2] != b"\xa5\x5a":
                if self.buffer == b"\xa5":
                    break
                del self.buffer[0]
            if len(self.buffer) < 6:
                continue
            length = int.from_bytes(self.buffer[4:6], "little")
            if self.buffer[2] != 1 or length > 64:
                self.buffer.clear()
                self.errors += 1
            elif len(self.buffer) == 20 + length:
                try:
                    frames.append(decode(self.buffer))
                except ValueError:
                    self.errors += 1
                self.buffer.clear()
        return frames


def monitor(device, duration):
    # Explicit device only; no discovery that could touch another controller.
    fd = os.open(device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    old = None
    try:
        old = termios.tcgetattr(fd)
        attrs = termios.tcgetattr(fd)
        attrs[0] = attrs[1] = attrs[3] = 0
        attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
        attrs[4] = attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = attrs[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
        stream = Stream()
        deadline = time.monotonic() + duration
        count = 0
        while time.monotonic() < deadline:
            if select.select(
                [fd], [], [], min(0.01, max(0, deadline - time.monotonic()))
            )[0]:
                chunk = os.read(fd, 1024)
                if not chunk:
                    raise RuntimeError("UART disconnected")
                for frame in stream.feed(chunk, time.monotonic()):
                    print(json.dumps(frame), flush=True)
                    count += 1
        if not count:
            raise RuntimeError("no valid controller telemetry before deadline")
        if stream.errors:
            raise RuntimeError(f"{stream.errors} corrupt or incomplete frames")
    finally:
        try:
            if old is not None:
                termios.tcsetattr(fd, termios.TCSANOW, old)
        finally:
            os.close(fd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device",
        required=True,
        help="binary UART device, e.g. /dev/ttyS4 (not USB text console)",
    )
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    if not 0 < args.seconds <= 300:
        parser.error("--seconds must be in (0, 300]")
    try:
        monitor(args.device, args.seconds)
    except (OSError, RuntimeError) as exc:
        parser.exit(1, f"{exc}\n")
