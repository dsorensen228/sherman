"""Time-owned animation around the clock-free procedural eye engine."""

from __future__ import annotations

import math
import random

from sherman_procedural_eyes import (
    AnimationInputs,
    Expression,
    ProceduralFace,
    compose_pose,
)


def _smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


class EyeAnimator:
    """Deterministic natural gaze, blink, and expression transitions.

    The caller supplies monotonic seconds. Randomness is seed-owned, bounded,
    and used only for harmless idle timing/targets.
    """

    def __init__(self, *, seed: int = 0x53484552, started_s: float = 0.0) -> None:
        self._random = random.Random(seed)
        self._expression = Expression.CALM
        self._previous_expression = Expression.CALM
        self._transition_started_s = started_s
        self._transition_duration_s = 0.28
        self._gaze_x = 0.0
        self._gaze_y = 0.0
        self._gaze_from_x = 0.0
        self._gaze_from_y = 0.0
        self._gaze_target_x = 0.0
        self._gaze_target_y = 0.0
        self._gaze_started_s = started_s
        self._gaze_duration_s = 0.35
        self._next_gaze_s = started_s + self._random.uniform(0.8, 1.8)
        self._blink_started_s: float | None = None
        self._blink_rate_hz = 0.28
        self._next_blink_s = started_s + self._next_blink_delay_s()
        self._external_gaze: tuple[float, float] | None = None
        self._attention = 0.5
        self._arousal = 0.5
        self._eyelid_open = 1.0
        self._sleep_requested = False
        self.sleep_state = "awake"
        self._sleep_started_s = started_s
        self._sleep_duration_s = 0.0
        self._sleep_from: ProceduralFace | None = None

    @property
    def expression(self) -> Expression:
        return self._expression

    def set_expression(
        self, expression: Expression | str, now_s: float, transition_s: float = 0.28
    ) -> None:
        if not math.isfinite(now_s) or not math.isfinite(transition_s):
            raise ValueError("expression timing must be finite")
        expression = Expression(expression)
        if expression is self._expression:
            return
        self._previous_expression = self._expression
        self._expression = expression
        self._transition_started_s = now_s
        self._transition_duration_s = max(0.0, min(2.0, transition_s))

    def set_semantic_intent(
        self,
        expression: Expression | str,
        now_s: float,
        *,
        attention: float,
        arousal: float,
        gaze_x: float | None = None,
        gaze_y: float | None = None,
        eyelid_open: float = 1.0,
        blink_rate_hz: float = 0.28,
        sleeping: bool = False,
    ) -> None:
        """Apply renderer-facing semantics without taking ownership of policy.

        Native personality may supply a gaze target and resting eyelid/blink
        policy. A ``None`` gaze delegates harmless idle gaze timing to this
        animator, which is also the degraded/manual-mode behavior.
        """

        values = (now_s, attention, arousal, eyelid_open, blink_rate_hz)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("semantic intent values must be finite")
        if (gaze_x is None) != (gaze_y is None):
            raise ValueError("gaze_x and gaze_y must both be supplied or omitted")
        if gaze_x is not None and (
            not math.isfinite(gaze_x) or not math.isfinite(gaze_y)
        ):
            raise ValueError("semantic gaze must be finite")

        if type(sleeping) is not bool:
            raise ValueError("sleeping must be boolean")
        # Capture before replacing semantics: entry and reversals must start
        # from the visible pose, not the new (already closed/open) eyelids.
        if sleeping != self._sleep_requested:
            self._sleep_from = self.sample(now_s)
            self._sleep_requested = sleeping
            self.sleep_state = "falling_asleep" if sleeping else "waking_up"
            self._sleep_started_s = now_s
            self._sleep_duration_s = 3.0 if sleeping else 2.4
            self._blink_started_s = None
            self._next_blink_s = now_s + self._sleep_duration_s + 1.0
            self._next_gaze_s = now_s + self._sleep_duration_s + 1.0

        self.set_expression(expression, now_s)
        self._attention = max(0.0, min(1.0, attention))
        self._arousal = max(0.0, min(1.0, arousal))
        self._eyelid_open = max(0.0, min(1.0, eyelid_open))
        self._blink_rate_hz = max(0.0, min(2.0, blink_rate_hz))
        self._external_gaze = (
            None
            if gaze_x is None
            else (
                max(-1.0, min(1.0, gaze_x)),
                max(-1.0, min(1.0, gaze_y)),
            )
        )

    def _next_blink_delay_s(self) -> float:
        if self._blink_rate_hz <= 0.0:
            return 60.0
        return max(0.6, min(12.0, self._random.expovariate(self._blink_rate_hz)))

    def _update_gaze(self, now_s: float) -> tuple[float, float]:
        if now_s >= self._next_gaze_s:
            self._gaze_from_x = self._gaze_x
            self._gaze_from_y = self._gaze_y
            # Favor the center; occasional edge looks make curiosity legible.
            self._gaze_target_x = self._random.triangular(-0.9, 0.9, 0.0)
            self._gaze_target_y = self._random.triangular(-0.55, 0.45, -0.05)
            self._gaze_started_s = now_s
            self._gaze_duration_s = self._random.uniform(0.22, 0.52)
            self._next_gaze_s = now_s + self._random.uniform(1.1, 3.2)

        progress = _smoothstep(
            (now_s - self._gaze_started_s) / max(self._gaze_duration_s, 0.001)
        )
        self._gaze_x = (
            self._gaze_from_x + (self._gaze_target_x - self._gaze_from_x) * progress
        )
        self._gaze_y = (
            self._gaze_from_y + (self._gaze_target_y - self._gaze_from_y) * progress
        )
        return self._gaze_x, self._gaze_y

    def _blink(self, now_s: float) -> float:
        if self._blink_rate_hz <= 0.0:
            self._blink_started_s = None
            return 0.0
        if self._blink_started_s is None and now_s >= self._next_blink_s:
            self._blink_started_s = now_s

        if self._blink_started_s is None:
            return 0.0
        elapsed_s = now_s - self._blink_started_s
        duration_s = 0.165
        if elapsed_s >= duration_s:
            self._blink_started_s = None
            self._next_blink_s = now_s + self._next_blink_delay_s()
            return 0.0
        phase = elapsed_s / duration_s
        if phase < 0.42:
            return _smoothstep(phase / 0.42)
        return 1.0 - _smoothstep((phase - 0.42) / 0.58)

    def sample(self, now_s: float) -> ProceduralFace:
        if not math.isfinite(now_s):
            raise ValueError("animation time must be finite")
        if self._sleep_requested:
            target = compose_pose(
                AnimationInputs(
                    expression=Expression.CALM, blink=1.0, attention=0.0, arousal=0.0
                )
            )
            # Closed lids breathe gently without wandering gaze or random blinks.
            breath = math.sin(2.0 * math.pi * (now_s - self._sleep_started_s) / 6.0)
            target.center_y += 8.0 + 1.2 * breath
            for eye in target.eyes:
                eye.scale_x *= 0.94 + 0.025 * breath
        else:
            target = self._sample_awake(now_s)
        if self._sleep_from is not None:
            amount = _smoothstep(
                (now_s - self._sleep_started_s) / self._sleep_duration_s
            )
            if amount < 1.0:
                return ProceduralFace(
                    [
                        a + (b - a) * amount
                        for a, b in zip(self._sleep_from.params, target.params)
                    ],
                    target.width,
                    target.height,
                )
            self._sleep_from = None
        self.sleep_state = "sleeping" if self._sleep_requested else "awake"
        return target

    def _sample_awake(self, now_s: float) -> ProceduralFace:
        if self._external_gaze is None:
            gaze_x, gaze_y = self._update_gaze(now_s)
        else:
            gaze_x, gaze_y = self._external_gaze
        blink = max(self._blink(now_s), 1.0 - self._eyelid_open)
        dynamic = dict(
            gaze_x=gaze_x,
            gaze_y=gaze_y,
            blink=blink,
            attention=self._attention,
            arousal=self._arousal,
        )
        target = compose_pose(AnimationInputs(expression=self._expression, **dynamic))
        if self._transition_duration_s <= 0.0:
            return target
        amount = _smoothstep(
            (now_s - self._transition_started_s) / self._transition_duration_s
        )
        if amount >= 1.0:
            self._previous_expression = self._expression
            return target
        source = compose_pose(
            AnimationInputs(expression=self._previous_expression, **dynamic)
        )
        params = [
            left + (right - left) * amount
            for left, right in zip(source.params, target.params)
        ]
        return ProceduralFace(params, target.width, target.height)
