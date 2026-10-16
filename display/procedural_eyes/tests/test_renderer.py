from __future__ import annotations

import hashlib
import math
import unittest

from sherman_procedural_eyes import (
    AnimationInputs,
    Expression,
    ProceduralEyesRenderer,
    ProceduralFace,
    SHERMAN_PURPLE_RGB,
    SHERMAN_PURPLE_RGB565,
    compose_pose,
    default_parameters,
    expression_preset,
    interpolate,
    mask_to_rgb565,
)


def lit_pixels(mask) -> int:  # type: ignore[no-untyped-def]
    return sum(value.bit_count() for value in mask.tobytes())


def center_x(mask) -> float:  # type: ignore[no-untyped-def]
    bbox = mask.getbbox()
    if bbox is None:
        raise AssertionError("expected a visible face")
    return (bbox[0] + bbox[2] - 1) / 2


class ProceduralEyesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.renderer = ProceduralEyesRenderer()

    def test_upstream_parameter_contract(self) -> None:
        params = default_parameters()
        self.assertEqual(43, len(params))
        face = ProceduralFace(params)
        self.assertEqual(params, face.params)
        self.assertEqual(5, face.eyes[0].offset)
        self.assertEqual(24, face.eyes[1].offset)
        # Byte-for-byte match against pycozmo commit 1b6dcd9 at its native
        # 128x64 resolution. This guards the port before Sherman-specific poses.
        upstream_mask = ProceduralFace(width=128, height=64).render_mask().tobytes()
        self.assertEqual(
            "b15e577c7bc4e662c5213f5b2102b1e493e344b6cc1b27f827b10edd86808711",
            hashlib.sha256(upstream_mask).hexdigest(),
        )
        with self.assertRaises(ValueError):
            ProceduralFace(params[:-1])

    def test_canonical_frame_is_purple_rgb565(self) -> None:
        self.assertEqual((178, 102, 255), SHERMAN_PURPLE_RGB)
        self.assertEqual(0xB33F, SHERMAN_PURPLE_RGB565)
        pose = expression_preset(Expression.CALM)
        mask = self.renderer.render_mask(pose)
        self.assertEqual((320, 170), mask.size)
        self.assertGreater(lit_pixels(mask), 8_000)

        image = self.renderer.render_image(pose)
        self.assertEqual(
            {(0, 0, 0), SHERMAN_PURPLE_RGB},
            {color for _, color in image.getcolors(maxcolors=3)},
        )
        packed = self.renderer.render_rgb565(pose)
        self.assertEqual(320 * 170 * 2, len(packed))
        self.assertIn(SHERMAN_PURPLE_RGB565.to_bytes(2, "big"), packed)
        self.assertEqual(
            packed[0:2],
            self.renderer.background_rgb565.to_bytes(2, "big"),
        )

    def test_expressions_are_distinct_and_deterministic(self) -> None:
        hashes: set[str] = set()
        for expression in Expression:
            first = self.renderer.render_mask(expression_preset(expression)).tobytes()
            second = self.renderer.render_mask(expression_preset(expression)).tobytes()
            self.assertEqual(first, second)
            hashes.add(hashlib.sha256(first).hexdigest())
        self.assertEqual(len(Expression), len(hashes))

    def test_gaze_blink_squash_and_expression_geometry(self) -> None:
        left = self.renderer.render_mask(AnimationInputs(gaze_x=-1.0))
        right = self.renderer.render_mask(AnimationInputs(gaze_x=1.0))
        self.assertGreater(center_x(right) - center_x(left), 25.0)

        open_mask = self.renderer.render_mask(AnimationInputs())
        closed_mask = self.renderer.render_mask(AnimationInputs(blink=1.0))
        self.assertGreater(lit_pixels(closed_mask), 100)
        self.assertLess(lit_pixels(closed_mask), lit_pixels(open_mask) // 8)

        tired = self.renderer.render_mask(expression_preset(Expression.TIRED))
        surprised = self.renderer.render_mask(expression_preset(Expression.SURPRISED))
        self.assertLess(lit_pixels(tired), lit_pixels(open_mask))
        self.assertGreater(lit_pixels(surprised), lit_pixels(open_mask))

    def test_interpolation_preserves_resolution_and_endpoints(self) -> None:
        source = expression_preset(Expression.CURIOUS)
        target = expression_preset(Expression.PLEASED)
        frames = list(interpolate(source, target, 5))
        self.assertEqual(source.params, frames[0].params)
        self.assertEqual(target.params, frames[-1].params)
        self.assertTrue(all(frame.width == 320 and frame.height == 170 for frame in frames))
        for index, value in enumerate(frames[2].params):
            self.assertAlmostEqual((source.params[index] + target.params[index]) / 2, value)

    def test_external_inputs_are_bounded(self) -> None:
        pose = compose_pose(
            AnimationInputs(
                gaze_x=math.inf,
                gaze_y=-math.inf,
                blink=math.nan,
                attention=99.0,
                arousal=-99.0,
            )
        )
        self.assertIsNotNone(self.renderer.render_mask(pose).getbbox())

    def test_non_byte_aligned_rgb565_has_no_row_padding(self) -> None:
        renderer = ProceduralEyesRenderer(17, 9)
        mask = renderer.render_mask(AnimationInputs())
        packed = mask_to_rgb565(mask)
        self.assertEqual(17 * 9 * 2, len(packed))

    def test_dimension_and_byteorder_validation(self) -> None:
        with self.assertRaises(ValueError):
            ProceduralEyesRenderer(0, 170)
        with self.assertRaises(ValueError):
            self.renderer.render_rgb565(AnimationInputs(), "middle")
        with self.assertRaises(ValueError):
            self.renderer.render_mask(ProceduralFace(width=128, height=64))


if __name__ == "__main__":
    unittest.main()
