#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import statistics
import sys
import time
import zlib

MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT))

from sherman_procedural_eyes import AnimationInputs, ProceduralEyesRenderer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark mask and RGB565 rendering")
    parser.add_argument("--frames", type=int, default=120)
    args = parser.parse_args()
    if args.frames <= 0:
        parser.error("--frames must be positive")

    renderer = ProceduralEyesRenderer()
    samples_ms: list[float] = []
    checksum = 0
    for frame_index in range(args.frames + 5):
        inputs = AnimationInputs(
            gaze_x=((frame_index % 31) - 15) / 15,
            gaze_y=((frame_index % 17) - 8) / 8,
            blink=1.0 if frame_index % 47 in (0, 1, 2) else 0.0,
        )
        started = time.perf_counter()
        frame = renderer.render_rgb565(inputs)
        elapsed_ms = (time.perf_counter() - started) * 1_000
        checksum = zlib.crc32(frame, checksum)
        if frame_index >= 5:
            samples_ms.append(elapsed_ms)

    ordered = sorted(samples_ms)
    p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
    print(f"frames={args.frames}")
    print(f"mean_ms={statistics.fmean(samples_ms):.3f}")
    print(f"p95_ms={p95:.3f}")
    print(f"max_ms={max(samples_ms):.3f}")
    print(f"mean_fps={1_000 / statistics.fmean(samples_ms):.1f}")
    print(f"checksum={checksum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
