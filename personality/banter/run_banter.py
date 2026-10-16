#!/usr/bin/env python3
"""Boot companion to Sherman's stationary face/personality service."""

from __future__ import annotations

import argparse
import fcntl
import json
import signal
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from banter.audio import AlsaSpeaker  # noqa: E402
from banter.client import JarvisClient  # noqa: E402
from banter.config import load_config  # noqa: E402
from banter.runtime import (  # noqa: E402
    Interaction,
    ManualTriggers,
    Scheduler,
    face_is_idle,
    write_json,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="/etc/sherman/banter.json")
    parser.add_argument(
        "--once", action="store_true", help="one immediate admitted live exchange"
    )
    parser.add_argument(
        "--check", action="store_true", help="validate config without playing audio"
    )
    args = parser.parse_args()
    config = load_config(args.config)
    if args.check:
        print(json.dumps({"valid": True, "enabled": config.enabled}))
        return 0
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    Path(config.health_file).parent.mkdir(parents=True, exist_ok=True)
    # Also protects diagnostics from accidentally overlapping the boot service.
    with open(config.health_file + ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        scheduler = Scheduler(config)
        client = JarvisClient(config)
        interaction = Interaction(
            config,
            client,
            AlsaSpeaker(config.alsa_device, config.volume),
            allowed=lambda: config.enabled
            and not stop.is_set()
            and face_is_idle(config.face_health_file),
            pause=stop.wait,
            manual_allowed=lambda: config.enabled
            and not stop.is_set()
            and face_is_idle(config.face_health_file, allow_circadian_quiet=True),
        )
        manual = ManualTriggers(client, interaction, scheduler)

        def health():
            return {**interaction.health(scheduler), **manual.health()}

        interaction.report = lambda: write_json(config.health_file, health())
        write_json(config.health_file, health())
        if args.once:
            success = interaction.run_once()
            write_json(
                config.health_file,
                {**health(), "state": "stopped"},
            )
            print(json.dumps({**health(), "state": "stopped"}))
            return 0 if success else 1
        while not stop.wait(1.0):
            if config.enabled:
                manual.tick()
                if scheduler.due():
                    interaction.run_once()
            write_json(config.health_file, health())
        write_json(config.health_file, {**health(), "state": "stopped"})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        # Neither credential contents nor HTTP bodies belong in boot diagnostics.
        print(
            json.dumps(
                {"event": "banter_start_failed", "error_type": type(error).__name__}
            )
        )
        raise SystemExit(1)
