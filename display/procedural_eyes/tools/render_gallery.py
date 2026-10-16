#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT))

from PIL import Image, ImageDraw  # noqa: E402

from sherman_procedural_eyes import (  # noqa: E402
    AnimationInputs,
    Expression,
    ProceduralEyesRenderer,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Sherman's expression gallery")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    renderer = ProceduralEyesRenderer()
    expressions = list(Expression)
    columns = 2
    label_height = 28
    rows = (len(expressions) + columns - 1) // columns
    gallery = Image.new(
        "RGB",
        (renderer.width * columns, (renderer.height + label_height) * rows),
        (28, 22, 36),
    )
    draw = ImageDraw.Draw(gallery)
    for index, expression in enumerate(expressions):
        column = index % columns
        row = index // columns
        x = column * renderer.width
        y = row * (renderer.height + label_height)
        frame = renderer.render_image(AnimationInputs(expression=expression))
        gallery.paste(frame, (x, y))
        draw.text((x + 8, y + renderer.height + 6), expression.value, fill=(220, 210, 230))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    gallery.save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
