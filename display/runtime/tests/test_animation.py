from __future__ import annotations

import itertools
import math
import unittest

from runtime.run_face import FACE_UPDATE_REGION
from runtime.animation import EyeAnimator
from sherman_procedural_eyes import (
    AnimationInputs,
    Expression,
    ProceduralEyesRenderer,
)


class EyeAnimatorTest(unittest.TestCase):
    def test_seeded_sequences_are_reproducible(self) -> None:
        left = EyeAnimator(seed=42)
        right = EyeAnimator(seed=42)
        for step in range(200):
            now_s = step * 0.05
            self.assertEqual(left.sample(now_s).params, right.sample(now_s).params)

    def test_expression_transition_reaches_target(self) -> None:
        animator = EyeAnimator(seed=1)
        calm = animator.sample(0.0)
        animator.set_expression(Expression.PLEASED, 1.0, transition_s=0.3)
        middle = animator.sample(1.15)
        final = animator.sample(1.30)
        self.assertNotEqual(calm.params, middle.params)
        self.assertNotEqual(middle.params, final.params)
        self.assertEqual(animator.expression, Expression.PLEASED)

    def test_invalid_time_and_expression_are_rejected(self) -> None:
        animator = EyeAnimator()
        with self.assertRaises(ValueError):
            animator.sample(math.nan)
        with self.assertRaises(ValueError):
            animator.set_expression("menacing", 0.0)
        with self.assertRaises(ValueError):
            animator.set_expression(Expression.CALM, math.inf)

    def test_every_sample_stays_finite(self) -> None:
        animator = EyeAnimator(seed=9)
        for step in range(1_000):
            pose = animator.sample(step / 30.0)
            self.assertTrue(all(math.isfinite(value) for value in pose.params))

    def test_semantic_intent_controls_gaze_energy_and_resting_eyelids(self) -> None:
        animator = EyeAnimator(seed=4)
        animator.set_semantic_intent(
            Expression.CURIOUS,
            1.0,
            attention=0.9,
            arousal=0.8,
            gaze_x=1.0,
            gaze_y=-0.5,
            eyelid_open=0.55,
            blink_rate_hz=0.4,
        )
        semantic_pose = animator.sample(1.3)
        baseline = EyeAnimator(seed=4).sample(1.3)
        self.assertNotEqual(semantic_pose.params, baseline.params)
        self.assertEqual(animator.expression, Expression.CURIOUS)

    def test_invalid_or_partial_semantic_intent_is_rejected(self) -> None:
        animator = EyeAnimator()
        with self.assertRaises(ValueError):
            animator.set_semantic_intent(
                "calm", 0.0, attention=math.nan, arousal=0.5
            )
        with self.assertRaises(ValueError):
            animator.set_semantic_intent(
                "calm",
                0.0,
                attention=0.5,
                arousal=0.5,
                gaze_x=0.0,
            )

    def test_reference_renderer_stays_inside_fast_update_region(self) -> None:
        renderer = ProceduralEyesRenderer()
        region = FACE_UPDATE_REGION
        for expression in Expression:
            for gaze_x, gaze_y in itertools.product((-1.0, 1.0), repeat=2):
                for attention, arousal in itertools.product((0.0, 1.0), repeat=2):
                    with self.subTest(
                        expression=expression,
                        gaze_x=gaze_x,
                        gaze_y=gaze_y,
                        attention=attention,
                        arousal=arousal,
                    ):
                        mask = renderer.render_mask(
                            AnimationInputs(
                                expression=expression,
                                gaze_x=gaze_x,
                                gaze_y=gaze_y,
                                attention=attention,
                                arousal=arousal,
                            )
                        )
                        bounds = mask.getbbox()
                        self.assertIsNotNone(bounds)
                        assert bounds is not None
                        left, top, right, bottom = bounds
                        self.assertGreaterEqual(left, region.x)
                        self.assertGreaterEqual(top, region.y)
                        self.assertLessEqual(right, region.x + region.width)
                        self.assertLessEqual(bottom, region.y + region.height)


if __name__ == "__main__":
    unittest.main()
