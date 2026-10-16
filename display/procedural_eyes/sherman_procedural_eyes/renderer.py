"""Sherman's purple RGB565 adapter for pycozmo's procedural-face model.

The geometry classes in this file are a focused Python/Pillow port of
``pycozmo/procedural_face.py``. The 43-value pose layout is intentionally kept
compatible while robot protocol, numpy, clocks, and random animation are left
out. See THIRD_PARTY_NOTICES.md for attribution and license.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
import math
from typing import Generator, Iterable, Sequence

from PIL import Image, ImageDraw


DEFAULT_WIDTH = 320
DEFAULT_HEIGHT = 170
UPSTREAM_DESIGN_WIDTH = 128
UPSTREAM_DESIGN_HEIGHT = 64
UPSTREAM_EYE_WIDTH = 28
UPSTREAM_EYE_HEIGHT = 40
PARAMETER_COUNT = 43

SHERMAN_PURPLE_RGB = (178, 102, 255)
SHERMAN_PURPLE_RGB565 = 0xB33F
BLACK_RGB = (0, 0, 0)
BLACK_RGB565 = 0x0000

_X_FACTOR = 0.55
_Y_FACTOR = 0.25
_NEAREST = Image.Resampling.NEAREST


def _clamp(value: float, minimum: float, maximum: float, fallback: float) -> float:
    try:
        finite = float(value)
    except (TypeError, ValueError):
        return fallback
    if not math.isfinite(finite):
        return fallback
    return max(minimum, min(maximum, finite))


def _rgb565(color: tuple[int, int, int]) -> int:
    red, green, blue = color
    return ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)


class ProceduralBase:
    def __init__(
        self,
        params: list[float],
        offset: int,
        width: int,
        height: int,
    ) -> None:
        self.params = params
        self.offset = offset
        self.width = int(width)
        self.height = int(height)
        self.eye_width = self.width * (UPSTREAM_EYE_WIDTH / UPSTREAM_DESIGN_WIDTH)
        self.eye_height = self.height * (UPSTREAM_EYE_HEIGHT / UPSTREAM_DESIGN_HEIGHT)
        self.half_eye_width = self.eye_width / 2
        self.half_eye_height = self.eye_height / 2
        self.scale_factor_lid_height = 1.2 * self.eye_width
        self.scale_factor_lid_bend = 1.2 * self.half_eye_width


class ProceduralLid(ProceduralBase):
    def __init__(
        self,
        params: list[float],
        offset: int,
        y_offset: float,
        angle_offset: float,
        width: int,
        height: int,
    ) -> None:
        super().__init__(params, offset, width, height)
        self.y_offset = float(y_offset)
        self.angle_offset = float(angle_offset)

    @property
    def y(self) -> float:
        return self.params[self.offset]

    @y.setter
    def y(self, value: float) -> None:
        self.params[self.offset] = value

    @property
    def angle(self) -> float:
        return self.params[self.offset + 1]

    @angle.setter
    def angle(self, value: float) -> None:
        self.params[self.offset + 1] = value

    @property
    def bend(self) -> float:
        return self.params[self.offset + 2]

    @bend.setter
    def bend(self, value: float) -> None:
        self.params[self.offset + 2] = value

    @staticmethod
    @lru_cache(maxsize=12)
    def _black(width: int, height: int) -> Image.Image:
        return Image.new("1", (width, height), color=0)

    def render(self, image: Image.Image) -> None:
        lid = Image.new("1", (self.width * 2, self.height * 2), color=0)
        draw = ImageDraw.Draw(lid)

        lid_height = int(self.eye_height * self.y)
        x1 = self.width - self.scale_factor_lid_height
        y1 = self.height - 1 - self.half_eye_height
        x2 = self.width + self.scale_factor_lid_height
        y2 = self.height - 1 + lid_height
        draw.rectangle(((x1, y1), (x2, y2)), fill=1)

        bend_height = int(self.eye_height * (1.0 - self.y) * self.bend)
        x3 = self.width - self.scale_factor_lid_bend
        y3 = self.height - 1 + lid_height - bend_height
        x4 = self.width + self.scale_factor_lid_bend
        y4 = self.height - 1 + lid_height + bend_height
        draw.chord(((x3, y3), (x4, y4)), 0, 180, fill=1)

        lid = lid.rotate(self.angle + self.angle_offset, resample=_NEAREST, expand=0)
        location = (
            int((image.size[0] - lid.size[0]) / 2),
            int((image.size[1] - lid.size[1]) / 2 + self.y_offset),
        )
        image.paste(self._black(self.width * 2, self.height * 2), location, lid)


class ProceduralEye(ProceduralBase):
    def __init__(
        self,
        params: list[float],
        offset: int,
        x_offset: float,
        width: int,
        height: int,
    ) -> None:
        super().__init__(params, offset, width, height)
        self.x_offset = float(x_offset)
        self.corner_radius = self.width / 20 + self.height / 10
        self.lids = (
            ProceduralLid(
                params, offset + 13, -self.half_eye_height, 0.0, width, height
            ),
            ProceduralLid(
                params,
                offset + 16,
                self.half_eye_height + 1,
                180.0,
                width,
                height,
            ),
        )

    def _value_property(index: int):  # type: ignore[no-untyped-def]
        def get(self: "ProceduralEye") -> float:
            return self.params[self.offset + index]

        def set_value(self: "ProceduralEye", value: float) -> None:
            self.params[self.offset + index] = value

        return property(get, set_value)

    center_x = _value_property(0)
    center_y = _value_property(1)
    scale_x = _value_property(2)
    scale_y = _value_property(3)
    angle = _value_property(4)
    lower_inner_radius_x = _value_property(5)
    lower_inner_radius_y = _value_property(6)
    lower_outer_radius_x = _value_property(7)
    lower_outer_radius_y = _value_property(8)
    upper_inner_radius_x = _value_property(9)
    upper_inner_radius_y = _value_property(10)
    upper_outer_radius_x = _value_property(11)
    upper_outer_radius_y = _value_property(12)

    def _draw_eye_shape(self, draw: ImageDraw.ImageDraw) -> None:
        x1 = self.width // 2 - self.half_eye_width
        y1 = self.height // 2 - self.half_eye_height
        x2 = self.width // 2 + self.half_eye_width
        y2 = self.height // 2 + self.half_eye_height

        x3 = x2 - int(
            self.corner_radius
            * max(self.upper_inner_radius_x, self.lower_inner_radius_x)
        )
        y3 = y1 + int(self.corner_radius * self.upper_inner_radius_y)
        y4 = y2 - int(self.corner_radius * self.lower_inner_radius_y)
        draw.rectangle(((x3, y3), (x2, y4)), fill=1)

        x3 = x1 + int(self.corner_radius * self.upper_outer_radius_x)
        x4 = x2 - int(self.corner_radius * self.upper_inner_radius_x)
        y4 = y1 + int(
            self.corner_radius
            * max(self.upper_outer_radius_y, self.upper_inner_radius_y)
        )
        draw.rectangle(((x3, y1), (x4, y4)), fill=1)

        y3 = y1 + int(self.corner_radius * self.upper_outer_radius_y)
        x4 = x1 + int(
            self.corner_radius
            * max(self.upper_outer_radius_x, self.lower_outer_radius_x)
        )
        y4 = y2 - int(self.corner_radius * self.lower_outer_radius_y)
        draw.rectangle(((x1, y3), (x4, y4)), fill=1)

        x3 = x1 + int(self.corner_radius * self.lower_outer_radius_x)
        y3 = y2 - int(
            self.corner_radius
            * max(self.lower_outer_radius_y, self.lower_inner_radius_y)
        )
        x4 = x2 - int(self.corner_radius * self.lower_inner_radius_x)
        draw.rectangle(((x3, y3), (x4, y2)), fill=1)

        x3 = (
            x1
            + int(
                self.corner_radius
                * max(self.upper_outer_radius_x, self.lower_outer_radius_x)
            )
            - 2
        )
        y3 = (
            y1
            + int(
                self.corner_radius
                * max(self.upper_outer_radius_y, self.upper_inner_radius_y)
            )
            - 1
        )
        x4 = (
            x2
            - int(
                self.corner_radius
                * max(self.upper_inner_radius_y, self.lower_inner_radius_y)
            )
            + 2
        )
        y4 = (
            y2
            - int(
                self.corner_radius
                * max(self.lower_outer_radius_y, self.lower_inner_radius_y)
            )
            + 1
        )
        draw.rectangle(((x3, y3), (x4, y4)), fill=1)

        draw.pieslice(
            (
                x2 - 2 * int(self.corner_radius * self.lower_inner_radius_x),
                y2 - 2 * int(self.corner_radius * self.lower_inner_radius_y),
                x2,
                y2,
            ),
            0,
            90,
            fill=1,
        )
        draw.pieslice(
            (
                x2 - 2 * int(self.corner_radius * self.upper_inner_radius_x),
                y1,
                x2,
                y1 + 2 * int(self.corner_radius * self.upper_inner_radius_y),
            ),
            270,
            360,
            fill=1,
        )
        draw.pieslice(
            (
                x1,
                y1,
                x1 + 2 * int(self.corner_radius * self.upper_outer_radius_x),
                y1 + 2 * int(self.corner_radius * self.upper_outer_radius_y),
            ),
            180,
            270,
            fill=1,
        )
        draw.pieslice(
            (
                x1,
                y2 - 2 * int(self.corner_radius * self.lower_outer_radius_y),
                x1 + 2 * int(self.corner_radius * self.lower_outer_radius_x),
                y2,
            ),
            90,
            180,
            fill=1,
        )

    def render(self, image: Image.Image) -> None:
        eye = Image.new("1", (self.width, self.height), color=0)
        self._draw_eye_shape(ImageDraw.Draw(eye))
        for lid in self.lids:
            lid.render(eye)

        eye = eye.rotate(self.angle, resample=_NEAREST, expand=1)
        scaled_size = (
            int(float(eye.size[0]) * self.scale_x),
            int(float(eye.size[1]) * self.scale_y),
        )
        if scaled_size[0] <= 0 or scaled_size[1] <= 0:
            return
        eye = eye.resize(scaled_size, resample=_NEAREST)
        location = (
            int((image.size[0] - eye.size[0]) / 2 + self.center_x * _X_FACTOR + self.x_offset),
            int((image.size[1] - eye.size[1]) / 2 + self.center_y * _Y_FACTOR),
        )
        image.paste(eye, location, eye)


def default_parameters() -> list[float]:
    eye = [
        0.0,
        0.0,
        1.0,
        1.0,
        0.0,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ]
    return [0.0, 0.0, 1.0, 1.0, 0.0, *eye, *eye]


class ProceduralFace(ProceduralBase):
    def __init__(
        self,
        params: Sequence[float] | None = None,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("face dimensions must be positive")
        values = default_parameters() if params is None else [float(value) for value in params]
        if len(values) != PARAMETER_COUNT:
            raise ValueError("procedural face requires exactly 43 floating-point values")
        super().__init__(values, 0, width, height)
        eye_offset = int(self.width / 5)
        self.eyes = (
            ProceduralEye(values, 5, -eye_offset, width, height),
            ProceduralEye(values, 24, eye_offset, width, height),
        )

    def _value_property(index: int):  # type: ignore[no-untyped-def]
        def get(self: "ProceduralFace") -> float:
            return self.params[index]

        def set_value(self: "ProceduralFace", value: float) -> None:
            self.params[index] = value

        return property(get, set_value)

    center_x = _value_property(0)
    center_y = _value_property(1)
    scale_x = _value_property(2)
    scale_y = _value_property(3)
    angle = _value_property(4)

    def copy(self) -> "ProceduralFace":
        return ProceduralFace(self.params, self.width, self.height)

    def render_mask(self) -> Image.Image:
        image = Image.new("1", (self.width, self.height), color=0)
        face = Image.new("1", (self.width, self.height), color=0)
        for eye in self.eyes:
            eye.render(face)

        face = face.rotate(self.angle, resample=_NEAREST, expand=1)
        scaled_size = (
            int(float(face.size[0]) * self.scale_x),
            int(float(face.size[1]) * self.scale_y),
        )
        if scaled_size[0] <= 0 or scaled_size[1] <= 0:
            return image
        face = face.resize(scaled_size, resample=_NEAREST)
        location = (
            int((image.size[0] - face.size[0]) / 2 + self.center_x * _X_FACTOR),
            int((image.size[1] - face.size[1]) / 2 + self.center_y * _Y_FACTOR),
        )
        image.paste(face, location)
        return image


def interpolate(
    from_face: ProceduralFace,
    to_face: ProceduralFace,
    steps: int,
) -> Generator[ProceduralFace, None, None]:
    if steps < 2:
        raise ValueError("at least two interpolation steps are required")
    if from_face.width != to_face.width or from_face.height != to_face.height:
        raise ValueError("interpolated faces must have matching dimensions")
    for step in range(steps):
        amount = step / (steps - 1)
        params = [
            source + amount * (target - source)
            for source, target in zip(from_face.params, to_face.params)
        ]
        yield ProceduralFace(params, from_face.width, from_face.height)


class Expression(str, Enum):
    CALM = "calm"
    CURIOUS = "curious"
    FOCUSED = "focused"
    PLEASED = "pleased"
    UNCERTAIN = "uncertain"
    FRUSTRATED = "frustrated"
    TIRED = "tired"
    SURPRISED = "surprised"


def _neutral(width: int, height: int) -> ProceduralFace:
    face = ProceduralFace(width=width, height=height)
    for eye in face.eyes:
        eye.scale_x = 0.8
        eye.scale_y = 0.8
    return face


def expression_preset(
    expression: Expression,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> ProceduralFace:
    """Return a pycozmo-compatible pose tuned to Sherman's expression grammar."""
    expression = Expression(expression)
    face = _neutral(width, height)
    left, right = face.eyes

    if expression is Expression.CALM:
        return face
    if expression is Expression.CURIOUS:
        left.scale_x, left.scale_y = 0.76, 0.82
        right.scale_x, right.scale_y = 0.92, 0.98
        left.lids[1].y, left.lids[1].bend = 0.12, 0.15
        right.lids[0].angle = -10.0
        right.lids[0].y = 0.12
        return face
    if expression is Expression.FOCUSED:
        left.lids[0].y, left.lids[0].angle = 0.18, -16.0
        right.lids[0].y, right.lids[0].angle = 0.18, 16.0
        left.scale_y = right.scale_y = 0.76
        return face
    if expression is Expression.PLEASED:
        for eye in face.eyes:
            eye.upper_outer_radius_x = 1.0
            eye.upper_inner_radius_x = 1.0
            eye.lids[1].y = 0.36
            eye.lids[1].bend = 0.36
        return face
    if expression is Expression.UNCERTAIN:
        left.lids[0].y, left.lids[0].angle = 0.34, -8.0
        right.lids[0].y, right.lids[0].angle = 0.10, 22.0
        left.lids[1].y = right.lids[1].y = 0.18
        return face
    if expression is Expression.FRUSTRATED:
        left.lids[0].y, left.lids[0].angle = 0.30, -28.0
        right.lids[0].y, right.lids[0].angle = 0.30, 28.0
        left.lids[1].y = right.lids[1].y = 0.12
        return face
    if expression is Expression.TIRED:
        left.lids[0].y, left.lids[0].angle = 0.38, 5.0
        right.lids[0].y, right.lids[0].angle = 0.38, -5.0
        left.lids[1].y = right.lids[1].y = 0.34
        left.center_y = right.center_y = 18.0
        return face
    if expression is Expression.SURPRISED:
        for eye in face.eyes:
            eye.scale_x = 1.0
            eye.scale_y = 1.0
            eye.lower_inner_radius_x = eye.lower_inner_radius_y = 0.9
            eye.lower_outer_radius_x = eye.lower_outer_radius_y = 0.9
            eye.upper_inner_radius_x = eye.upper_inner_radius_y = 0.9
            eye.upper_outer_radius_x = eye.upper_outer_radius_y = 0.9
        return face
    raise AssertionError("unreachable expression")


@dataclass(frozen=True)
class AnimationInputs:
    expression: Expression = Expression.CALM
    gaze_x: float = 0.0
    gaze_y: float = 0.0
    blink: float = 0.0
    attention: float = 0.5
    arousal: float = 0.5


def compose_pose(
    inputs: AnimationInputs,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> ProceduralFace:
    """Combine semantic and continuous inputs without owning time or randomness."""
    face = expression_preset(inputs.expression, width, height)
    gaze_x = _clamp(inputs.gaze_x, -1.0, 1.0, 0.0)
    gaze_y = _clamp(inputs.gaze_y, -1.0, 1.0, 0.0)
    blink = _clamp(inputs.blink, 0.0, 1.0, 0.0)
    attention = _clamp(inputs.attention, 0.0, 1.0, 0.5)
    arousal = _clamp(inputs.arousal, 0.0, 1.0, 0.5)

    scale = min(width / UPSTREAM_DESIGN_WIDTH, height / UPSTREAM_DESIGN_HEIGHT)
    face.center_x += gaze_x * (10.0 + 3.0 * attention) * scale
    face.center_y += gaze_y * (28.0 + 4.0 * attention) * scale
    for eye in face.eyes:
        eye.scale_x *= 0.94 + 0.12 * attention
        eye.scale_y *= 0.94 + 0.12 * arousal
        # pycozmo's blink uses squash/stretch. Keep a thin visible purple line
        # at full closure so a blink cannot look like a dead display.
        eye.scale_x *= 1.0 + blink * 0.20
        eye.scale_y *= max(0.035, 1.0 - blink * 0.965)
    return face


@lru_cache(maxsize=32)
def _packed_byte_lookup(
    foreground: int,
    background: int,
    byteorder: str,
) -> tuple[bytes, ...]:
    if byteorder not in ("big", "little"):
        raise ValueError("byteorder must be 'big' or 'little'")
    foreground_bytes = foreground.to_bytes(2, byteorder)
    background_bytes = background.to_bytes(2, byteorder)
    values: list[bytes] = []
    for packed in range(256):
        expanded = bytearray(16)
        for bit in range(8):
            color = foreground_bytes if packed & (0x80 >> bit) else background_bytes
            expanded[bit * 2 : bit * 2 + 2] = color
        values.append(bytes(expanded))
    return tuple(values)


def mask_to_rgb565(
    mask: Image.Image,
    eye_color: int = SHERMAN_PURPLE_RGB565,
    background_color: int = BLACK_RGB565,
    byteorder: str = "big",
) -> bytes:
    """Pack a mode-1 mask as contiguous row-major RGB565 bytes."""
    if mask.mode != "1":
        raise ValueError("RGB565 packing requires a Pillow mode-1 mask")
    if not 0 <= eye_color <= 0xFFFF or not 0 <= background_color <= 0xFFFF:
        raise ValueError("RGB565 colors must be unsigned 16-bit values")
    lookup = _packed_byte_lookup(eye_color, background_color, byteorder)
    packed = mask.tobytes()
    width, height = mask.size
    if width % 8 == 0:
        return b"".join(lookup[value] for value in packed)

    # Pillow pads each mode-1 row to a whole byte. Trim those padding bits for
    # non-panel/test sizes while retaining the fast path for 320-pixel rows.
    bytes_per_row = (width + 7) // 8
    foreground = eye_color.to_bytes(2, byteorder)
    background = background_color.to_bytes(2, byteorder)
    output = bytearray(width * height * 2)
    output_offset = 0
    for y in range(height):
        row = packed[y * bytes_per_row : (y + 1) * bytes_per_row]
        for x in range(width):
            color = foreground if row[x // 8] & (0x80 >> (x % 8)) else background
            output[output_offset : output_offset + 2] = color
            output_offset += 2
    return bytes(output)


class ProceduralEyesRenderer:
    def __init__(
        self,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        eye_rgb: tuple[int, int, int] = SHERMAN_PURPLE_RGB,
        background_rgb: tuple[int, int, int] = BLACK_RGB,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("renderer dimensions must be positive")
        self.width = int(width)
        self.height = int(height)
        self.eye_rgb = tuple(int(channel) for channel in eye_rgb)
        self.background_rgb = tuple(int(channel) for channel in background_rgb)
        if any(channel < 0 or channel > 255 for channel in (*self.eye_rgb, *self.background_rgb)):
            raise ValueError("RGB channels must be in [0, 255]")
        self.eye_rgb565 = _rgb565(self.eye_rgb)
        self.background_rgb565 = _rgb565(self.background_rgb)

    def pose(self, inputs: AnimationInputs) -> ProceduralFace:
        return compose_pose(inputs, self.width, self.height)

    def render_mask(self, pose: ProceduralFace | AnimationInputs) -> Image.Image:
        if isinstance(pose, AnimationInputs):
            pose = self.pose(pose)
        if pose.width != self.width or pose.height != self.height:
            raise ValueError("pose and renderer dimensions must match")
        return pose.render_mask()

    def render_image(self, pose: ProceduralFace | AnimationInputs) -> Image.Image:
        mask = self.render_mask(pose)
        image = Image.new("RGB", mask.size, self.background_rgb)
        image.paste(self.eye_rgb, mask=mask)
        return image

    def render_rgb565(
        self,
        pose: ProceduralFace | AnimationInputs,
        byteorder: str = "big",
    ) -> bytes:
        return mask_to_rgb565(
            self.render_mask(pose),
            self.eye_rgb565,
            self.background_rgb565,
            byteorder,
        )


def expression_names() -> Iterable[str]:
    return (expression.value for expression in Expression)
