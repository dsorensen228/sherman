#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT))

from sherman_procedural_eyes import (  # noqa: E402
    Expression,
    ProceduralEyesRenderer,
    expression_preset,
)


def pillow_lit_pixels(renderer: ProceduralEyesRenderer, expression: Expression) -> set[int]:
    mask = renderer.render_mask(expression_preset(expression))
    packed = mask.tobytes()
    bytes_per_row = renderer.width // 8
    return {
        y * renderer.width + x
        for y in range(renderer.height)
        for x in range(renderer.width)
        if packed[y * bytes_per_row + x // 8] & (0x80 >> (x % 8))
    }


def cpp_lit_pixels(raw: bytes) -> set[int]:
    return {
        index
        for index in range(len(raw) // 2)
        if raw[index * 2] != 0 or raw[index * 2 + 1] != 0
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare fast C++ masks with the exact Pillow reference"
    )
    parser.add_argument("render_frame", type=Path)
    parser.add_argument("--minimum-iou", type=float, default=0.87)
    args = parser.parse_args()

    renderer = ProceduralEyesRenderer()
    passed = True
    with tempfile.TemporaryDirectory(prefix="sherman-eye-fidelity-") as directory:
        root = Path(directory)
        for expression in Expression:
            output = root / f"{expression.value}.rgb565"
            subprocess.run(
                [
                    str(args.render_frame),
                    "--expression",
                    expression.value,
                    "--output",
                    str(output),
                ],
                check=True,
            )
            cpp = cpp_lit_pixels(output.read_bytes())
            pillow = pillow_lit_pixels(renderer, expression)
            intersection = len(cpp & pillow)
            union = len(cpp | pillow)
            iou = intersection / union
            print(
                f"{expression.value:10s} iou={iou:.4f} "
                f"cpp_pixels={len(cpp)} pillow_pixels={len(pillow)}"
            )
            passed = passed and iou >= args.minimum_iou
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
