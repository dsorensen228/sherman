#!/usr/bin/env python3
"""Run Sherman's expressive eyes on the Luckfox ST7789V2 display."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import signal
import sys
import time
from typing import Any

DISPLAY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DISPLAY_ROOT))
sys.path.insert(0, str(DISPLAY_ROOT / "procedural_eyes"))

from backends.st7789 import DisplayRegion, St7789Config, St7789Display  # noqa: E402
from runtime.config import FaceRuntimeConfig, load_face_runtime_config  # noqa: E402
from runtime.animation import EyeAnimator  # noqa: E402
from runtime.manual_wake import ManualWakeReader  # noqa: E402
from runtime.fast_renderer import FastProceduralEyesRenderer  # noqa: E402
from runtime.personality_adapter import (  # noqa: E402
    FallbackPersonalitySource,
    NativePersonalitySource,
    PersonalityStateStore,
)
from runtime.personality_loop import AutonomousPersonalityController  # noqa: E402
from sherman_procedural_eyes import (  # noqa: E402
    Expression,
    ProceduralEyesRenderer,
    expression_names,
)


DEMO_SEQUENCE = (
    Expression.CALM,
    Expression.CURIOUS,
    Expression.PLEASED,
    Expression.FOCUSED,
    Expression.UNCERTAIN,
    Expression.SURPRISED,
    Expression.TIRED,
    Expression.CALM,
)

# Exhaustive corners of the bounded expression/gaze/blink/attention/arousal
# input space occupy x=34..285 and y=9..160. Keep a further 3-6 pixel margin.
FACE_UPDATE_REGION = DisplayRegion(x=28, y=4, width=264, height=162)
MAX_HEALTH_BYTES = 4096
DEFAULT_CONFIG_PATH = Path("/etc/sherman/face-runtime.json")


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    encoded = (
        json.dumps(payload, separators=(",", ":"), ensure_ascii=True) + "\n"
    ).encode("utf-8")
    if len(encoded) > MAX_HEALTH_BYTES:
        raise ValueError("face health record exceeds its 4096-byte bound")

    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _load_defaults(argv: list[str]) -> tuple[FaceRuntimeConfig, Path | None]:
    preparser = argparse.ArgumentParser(add_help=False)
    preparser.add_argument("--config", type=Path)
    preliminary, _ = preparser.parse_known_args(argv)
    configured = preliminary.config
    if configured is not None:
        return load_face_runtime_config(configured), configured
    environment_path = os.environ.get("SHERMAN_FACE_CONFIG")
    candidate = Path(environment_path) if environment_path else DEFAULT_CONFIG_PATH
    if candidate.is_file():
        return load_face_runtime_config(candidate), candidate
    return FaceRuntimeConfig(), None


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        defaults, loaded_config = _load_defaults(arguments)
    except (OSError, ValueError) as error:
        raise SystemExit(f"invalid face runtime config: {error}") from error

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=loaded_config)
    parser.add_argument(
        "--mode",
        choices=("personality", "manual", "demo"),
        default=defaults.mode,
        help="production personality or an explicit diagnostic mode",
    )
    parser.add_argument(
        "--expression", choices=list(expression_names()), default=defaults.expression
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="diagnostic compatibility alias for --mode demo",
    )
    parser.add_argument("--fps", type=float, default=defaults.fps)
    parser.add_argument("--spi-hz", type=int, default=defaults.spi_hz)
    parser.add_argument(
        "--renderer",
        choices=("auto", "fast", "reference"),
        default=defaults.renderer,
    )
    parser.add_argument(
        "--renderer-library",
        type=Path,
        default=(
            Path(defaults.renderer_library) if defaults.renderer_library else None
        ),
    )
    parser.add_argument(
        "--personality-library",
        type=Path,
        default=(
            Path(defaults.personality_library) if defaults.personality_library else None
        ),
    )
    parser.add_argument(
        "--personality-required",
        action="store_true",
        default=defaults.personality_required,
        help="exit instead of showing safe calm eyes if personality fails",
    )
    parser.add_argument(
        "--personality-tick-hz", type=float, default=defaults.personality_tick_hz
    )
    parser.add_argument(
        "--personality-state-file",
        type=Path,
        default=Path(defaults.personality_state_file),
    )
    parser.add_argument(
        "--persistence-interval",
        type=float,
        default=defaults.persistence_interval_s,
    )
    parser.add_argument("--timezone", default=defaults.timezone)
    parser.add_argument(
        "--wake-request-file", type=Path, default=Path(defaults.wake_request_file)
    )
    parser.add_argument(
        "--circadian-enabled",
        action="store_true",
        default=defaults.circadian_enabled,
    )
    parser.add_argument(
        "--full-frame",
        action="store_true",
        default=defaults.full_frame,
        help="disable bounded face-region updates",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="seconds; zero runs until stopped",
    )
    parser.add_argument("--seed", type=int, default=defaults.seed)
    parser.add_argument(
        "--health-file",
        type=Path,
        help="atomically replace this bounded JSON health record",
    )
    args = parser.parse_args(arguments)
    if args.demo:
        args.mode = "demo"
    if not 1.0 <= args.fps <= 60.0:
        parser.error("--fps must be in the range 1..60")
    if args.duration < 0.0:
        parser.error("--duration cannot be negative")
    if not 1.0 <= args.personality_tick_hz <= 30.0:
        parser.error("--personality-tick-hz must be in the range 1..30")
    if not 10.0 <= args.persistence_interval <= 3600.0:
        parser.error("--persistence-interval must be in the range 10..3600")
    if args.circadian_enabled and not args.timezone:
        parser.error("--circadian-enabled requires an explicit --timezone")
    if args.timezone and (
        len(args.timezone) > 96
        or any(character in args.timezone for character in "\x00\r\n")
    ):
        parser.error("--timezone must be a bounded single-line POSIX TZ string")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.timezone:
        os.environ["TZ"] = args.timezone
        tzset = getattr(time, "tzset", None)
        if tzset is not None:
            tzset()

    stopping = False
    health_failure_reported = False

    def publish_health(payload: dict[str, Any]) -> None:
        nonlocal health_failure_reported
        if args.health_file is None:
            return
        try:
            _atomic_write_json(args.health_file, payload)
        except (OSError, ValueError) as error:
            if not health_failure_reported:
                print(
                    json.dumps(
                        {
                            "event": "face_health_write_failed",
                            "error": str(error)[:512],
                        },
                        separators=(",", ":"),
                    ),
                    file=sys.stderr,
                    flush=True,
                )
                health_failure_reported = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    renderer_backend = "pillow-reference"
    if args.renderer == "reference":
        renderer = ProceduralEyesRenderer()
    else:
        try:
            renderer = FastProceduralEyesRenderer(args.renderer_library)
            renderer_backend = renderer.backend_name
        except (AttributeError, OSError, RuntimeError) as error:
            if args.renderer == "fast":
                raise
            print(
                json.dumps(
                    {
                        "event": "face_renderer_fallback",
                        "requested": "auto",
                        "selected": renderer_backend,
                        "reason": str(error),
                    },
                    separators=(",", ":"),
                ),
                file=sys.stderr,
                flush=True,
            )
            renderer = ProceduralEyesRenderer()
    started_s = time.monotonic()
    animator = EyeAnimator(seed=args.seed, started_s=started_s)
    manual_wake = ManualWakeReader(args.wake_request_file, started_s)
    wake_request_id = ""
    animator.set_expression(args.expression, started_s, transition_s=0.0)
    personality: AutonomousPersonalityController | None = None
    if args.mode == "personality":
        personality_initial_error = ""
        try:
            personality_source = NativePersonalitySource(
                args.personality_library, seed=args.seed
            )
        except (AttributeError, OSError, RuntimeError, ValueError) as error:
            if args.personality_required:
                close_renderer = getattr(renderer, "close", None)
                if close_renderer is not None:
                    close_renderer()
                raise
            personality_initial_error = str(error)[:512]
            personality_source = FallbackPersonalitySource()
        personality = AutonomousPersonalityController(
            personality_source,
            started_s=started_s,
            tick_hz=args.personality_tick_hz,
            state_store=PersonalityStateStore(args.personality_state_file),
            persistence_interval_s=args.persistence_interval,
            circadian_enabled=args.circadian_enabled,
            source_required=args.personality_required,
            initial_error=personality_initial_error,
        )
    else:
        animator.set_semantic_intent(
            args.expression,
            started_s,
            attention=0.72,
            arousal=0.52,
        )
    period_s = 1.0 / args.fps
    next_frame_s = started_s
    next_report_s = started_s + 5.0
    next_demo_s = started_s + 3.5
    demo_index = 0
    dropped = 0
    rendered = 0
    render_total_ms = 0.0

    display = St7789Display(St7789Config(spi_speed_hz=args.spi_hz))
    runtime_error: Exception | None = None

    def runtime_health(state: str) -> dict[str, Any]:
        health: dict[str, Any] = {
            "event": "face_runtime_health",
            "state": state,
            "mode": args.mode,
            "renderer": renderer_backend,
            "expression": animator.expression.value,
            "sleep_state": animator.sleep_state,
            "wake_request_id": wake_request_id,
            "frames": rendered,
            "dropped": dropped,
            "transfer_errors": display.stats.transfer_errors,
        }
        if personality is not None:
            health.update(personality.health())
        return health

    try:
        display.open()
        publish_health(runtime_health("running"))
        while not stopping:
            now_s = time.monotonic()
            if args.duration and now_s - started_s >= args.duration:
                break
            previous_sleep_state = animator.sleep_state
            previous_wake_request_id = wake_request_id
            if personality is not None:
                intent = personality.update(now_s)
                wake_request_id = manual_wake.update(
                    now_s, intent, degraded=personality.degraded
                )
                sleeping = intent.sleeping and not wake_request_id
                if intent.sleeping and wake_request_id:
                    # Only the face wakes. Native quiet remains asserted for
                    # motor policy and automatic speech admission.
                    intent = replace(
                        intent,
                        expression="calm",
                        attention=0.5,
                        arousal=0.35,
                        gaze_x=0.0,
                        gaze_y=0.0,
                        eyelid_open=1.0,
                        blink_rate_hz=0.16,
                    )
                animator.set_semantic_intent(
                    intent.expression,
                    now_s,
                    attention=intent.attention,
                    arousal=intent.arousal,
                    gaze_x=intent.gaze_x,
                    gaze_y=intent.gaze_y,
                    eyelid_open=intent.eyelid_open,
                    blink_rate_hz=intent.blink_rate_hz,
                    sleeping=bool(sleeping),
                )
            elif args.mode == "demo" and now_s >= next_demo_s:
                demo_index = (demo_index + 1) % len(DEMO_SEQUENCE)
                animator.set_expression(DEMO_SEQUENCE[demo_index], now_s)
                next_demo_s = now_s + 3.5

            render_started_s = time.monotonic()
            frame = renderer.render_rgb565(animator.sample(now_s))
            render_ms = (time.monotonic() - render_started_s) * 1000.0
            if args.full_frame:
                display.show_rgb565(frame)
            else:
                display.show_rgb565_region(frame, FACE_UPDATE_REGION)
            rendered += 1
            render_total_ms += render_ms
            if (
                animator.sleep_state != previous_sleep_state
                or wake_request_id != previous_wake_request_id
            ):
                # Quiet admission must reach the speech process immediately,
                # rather than waiting for the five-second periodic report.
                publish_health(runtime_health("running"))

            next_frame_s += period_s
            after_frame_s = time.monotonic()
            if after_frame_s > next_frame_s:
                # A slight overrun starts the next current-state frame
                # immediately. Only count whole elapsed frame periods as
                # dropped; rounding every overrun up would turn a 34 ms frame
                # at 30 fps into an artificial 15 fps cadence.
                missed = int((after_frame_s - next_frame_s) / period_s)
                dropped += missed
                next_frame_s += missed * period_s
            else:
                time.sleep(next_frame_s - after_frame_s)

            if after_frame_s >= next_report_s:
                health = runtime_health("running")
                health.update(
                    {
                        "mean_render_ms": round(render_total_ms / rendered, 2),
                        "last_transfer_ms": round(display.stats.last_transfer_ms, 2),
                        "max_transfer_ms": round(display.stats.maximum_transfer_ms, 2),
                        "region_bytes": (
                            display.config.frame_bytes
                            if args.full_frame
                            else FACE_UPDATE_REGION.byte_size
                        ),
                    }
                )
                print(
                    json.dumps(health, separators=(",", ":")),
                    flush=True,
                )
                publish_health(health)
                next_report_s = after_frame_s + 5.0
    except Exception as error:
        runtime_error = error
        health = runtime_health("error")
        health.update({"error_type": type(error).__name__, "error": str(error)[:256]})
        publish_health(health)
    finally:
        display.close()
        if personality is not None:
            personality.close()
        close_renderer = getattr(renderer, "close", None)
        if close_renderer is not None:
            close_renderer()
    if runtime_error is not None:
        print(
            json.dumps(
                {
                    "event": "face_runtime_stopped_on_error",
                    "error_type": type(runtime_error).__name__,
                    "error": str(runtime_error)[:256],
                },
                separators=(",", ":"),
            ),
            file=sys.stderr,
            flush=True,
        )
        return 1
    publish_health(runtime_health("stopped"))
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as error:
        print(
            json.dumps(
                {
                    "event": "face_runtime_start_failed",
                    "error_type": type(error).__name__,
                    "error": str(error)[:512],
                },
                separators=(",", ":"),
            ),
            file=sys.stderr,
            flush=True,
        )
        exit_code = 1
    raise SystemExit(exit_code)
