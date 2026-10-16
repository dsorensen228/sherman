"""Deterministic face animation and target runtime."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .animation import EyeAnimator

__all__ = ["EyeAnimator"]


def __getattr__(name: str) -> Any:
    if name == "EyeAnimator":
        from .animation import EyeAnimator

        return EyeAnimator
    raise AttributeError(name)
