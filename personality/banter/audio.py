"""Procedural droid phonation and an interruptible ALSA adapter. No audio catalog."""

from __future__ import annotations

import hashlib
import math
import random
import subprocess
import sys
import tempfile
import time
import wave
from array import array

SAMPLE_RATE = 16000
EMOTIONS = frozenset({"curious", "pleased", "skeptical", "indignant", "conspiratorial"})


def synthesize(meaning: str, emotion: str, seed: str, volume: float = 0.18) -> bytes:
    if (
        not isinstance(meaning, str)
        or not 1 <= len(meaning) <= 180
        or emotion not in EMOTIONS
        or not 0 < volume <= 0.35
    ):
        raise ValueError("invalid beep utterance")
    digest = hashlib.sha256(f"{seed}:{emotion}:{meaning}".encode()).digest()
    rng = random.Random(int.from_bytes(digest[:8], "little"))
    syllables = min(14, max(5, len(meaning.split()) + 2))
    samples = array("h")
    for index in range(syllables):
        duration = rng.uniform(0.09, 0.21)
        start_hz = rng.uniform(650, 2100)
        end_hz = start_hz * rng.uniform(0.65, 1.45)
        if emotion == "indignant":
            duration *= 0.8
            start_hz *= 1.15
        elif emotion == "conspiratorial":
            start_hz *= 0.65
            end_hz *= 0.65
        if index == syllables - 1:
            duration *= 1.5
            end_hz = start_hz * (1.45 if emotion == "curious" else 0.65)
        count = round(duration * SAMPLE_RATE)
        phase = 0.0
        for sample in range(count):
            t = sample / SAMPLE_RATE
            progress = sample / max(1, count - 1)
            frequency = start_hz + (end_hz - start_hz) * progress
            frequency += 35 * math.sin(2 * math.pi * 24 * t)
            phase += 2 * math.pi * frequency / SAMPLE_RATE
            envelope = min(1.0, t / 0.008, (duration - t) / 0.015)
            tone = (math.sin(phase) + 0.18 * math.sin(phase * 2)) / 1.18
            samples.append(round(32767 * volume * max(0, envelope) * tone))
        gap = rng.uniform(0.035, 0.11) + (0.12 if index % 4 == 3 else 0)
        samples.extend([0] * round(gap * SAMPLE_RATE))
    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


class AlsaSpeaker:
    def __init__(self, device: str, volume: float):
        self.device = device
        self.volume = volume

    def play(self, exchange: dict, seed: str, allowed) -> None:
        pcm = synthesize(exchange["sherman"], exchange["emotion"], seed, self.volume)
        if not allowed():
            raise RuntimeError("idle admission lost")
        with tempfile.NamedTemporaryFile(prefix="sherman-", suffix=".wav") as stream:
            with wave.open(stream.name, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(SAMPLE_RATE)
                wav.writeframes(pcm)
            process = subprocess.Popen(
                ["aplay", "-q", "-D", self.device, stream.name],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            deadline = time.monotonic() + 8.0
            try:
                while process.poll() is None:
                    if not allowed() or time.monotonic() >= deadline:
                        raise RuntimeError("beep playback cancelled or timed out")
                    time.sleep(0.05)
                if process.returncode:
                    raise RuntimeError("ALSA playback failed")
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=1)
