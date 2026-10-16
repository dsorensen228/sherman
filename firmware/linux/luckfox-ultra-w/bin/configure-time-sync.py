#!/usr/bin/env python3
"""Give stock ntpd sole ownership of UTC on the stock Luckfox image."""

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


def disable_camera_ntp(text):
    """Preserve unrelated camera settings and reject unexpected config shapes."""
    section = re.search(r"(?ms)^\[network\.ntp\]\s*\n(.*?)(?=^\[|\Z)", text)
    if section is None:
        raise ValueError("missing network.ntp section")
    body, count = re.subn(r"(?m)^(enable\s*=\s*)[01](\s*)$", r"\g<1>0\2", section[1])
    if count != 1:
        raise ValueError("expected one network.ntp enable setting")
    return text[: section.start(1)] + body + text[section.end(1) :]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--utc-epoch",
        type=int,
        required=True,
        help="current trusted host UTC epoch seconds",
    )
    args = parser.parse_args()
    if args.utc_epoch < 1_767_225_600:  # 2026-01-01; reject an unset host clock
        parser.error("host UTC clock is not plausible")
    # RkLunch.sh copies a sensor-specific OEM template over /userdata at boot.
    paths = sorted(set(Path("/oem/usr/share").glob("rkipc*.ini")))
    paths.append(Path("/userdata/rkipc.ini"))
    changes = [(p, disable_camera_ntp(p.read_text())) for p in paths]
    changed = any(p.read_text() != text for p, text in changes)
    camera_command = None
    if changed:
        pids = subprocess.run(
            ["pidof", "rkipc"], capture_output=True, text=True
        ).stdout.split()
        if len(pids) > 1:
            raise RuntimeError("multiple camera processes; refusing ambiguous restart")
        if pids:
            camera_command = (
                Path("/proc/{}/cmdline".format(pids[0]))
                .read_bytes()
                .rstrip(b"\0")
                .decode()
                .split("\0")
            )
            if [Path(camera_command[0]).name] + camera_command[1:] not in (
                ["rkipc"],
                ["rkipc", "-a", "/oem/usr/share/iqfiles"],
            ):
                raise RuntimeError("unexpected camera command; refusing restart")
            camera_command[0] = str(Path("/proc/{}/exe".format(pids[0])).resolve())
            subprocess.run(["kill", "-TERM", pids[0]], check=True)
            deadline = time.monotonic() + 15
            while Path("/proc/{}".format(pids[0])).exists():
                if time.monotonic() >= deadline:
                    raise RuntimeError("camera did not stop within 15 seconds")
                time.sleep(0.1)
    try:
        for path, text in changes:
            if path.read_text() == text:
                continue
            backup = path.with_name(path.name + ".before-sherman-time-sync")
            if not backup.exists():
                shutil.copy2(path, backup)
            staged = path.with_name(path.name + ".sherman-installing")
            shutil.copy2(path, staged)
            staged.write_text(text)
            staged.replace(path)
            print("disabled camera NTP:", path, flush=True)
    finally:
        if camera_command:
            subprocess.Popen(
                camera_command,
                env=dict(os.environ, LD_LIBRARY_PATH="/oem/usr/lib:/oem/lib:/usr/lib"),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
    subprocess.run(["/etc/init.d/S49ntp", "stop"], check=False)
    subprocess.run(["date", "-u", "-s", "@{}".format(args.utc_epoch)], check=True)
    subprocess.run(["hwclock", "-w", "-u"], check=True)
    subprocess.run(["/etc/init.d/S49ntp", "start"], check=True)
    print("UTC/RTC seeded; stock ntpd owns ongoing synchronization", flush=True)


if __name__ == "__main__":
    main()
