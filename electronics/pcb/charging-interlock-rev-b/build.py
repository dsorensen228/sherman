#!/usr/bin/env python3
"""Regenerate, verify, and package the board. Run using this directory's venv."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NAME = "charging-interlock-rev-b"
EVIDENCE = ROOT / "artifacts/phase-3/P3-PWR-003"


def run(args, output=None):
    result = subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if output:
        output.write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(result.stdout)
    print(result.stdout, end="")
    return result.stdout


def main():
    ap = argparse.ArgumentParser()
    app = Path.home() / "Applications/KiCad.app/Contents"
    ap.add_argument(
        "--kicad-cli",
        default=os.environ.get(
            "KICAD_CLI", shutil.which("kicad-cli") or str(app / "MacOS/kicad-cli")
        ),
    )
    ap.add_argument(
        "--kicad-python",
        default=os.environ.get(
            "KICAD_PYTHON",
            str(app / "Frameworks/Python.framework/Versions/3.9/bin/python3"),
        ),
    )
    args = ap.parse_args()
    cli = args.kicad_cli
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    # Any failure invalidates the previous order package.
    archive = HERE / f"{NAME}-gerbers.zip"
    archive.unlink(missing_ok=True)
    run([args.kicad_python, HERE / "generate.py"], EVIDENCE / "generation.txt")
    pcb = HERE / f"{NAME}.kicad_pcb"
    run(
        [
            cli,
            "pcb",
            "drc",
            "--all-track-errors",
            "--format",
            "json",
            "--exit-code-violations",
            "--output",
            EVIDENCE / "kicad-drc.json",
            pcb,
        ]
    )
    drc = json.loads((EVIDENCE / "kicad-drc.json").read_text())
    assert not drc["violations"] and not drc["unconnected_items"], drc
    fab = HERE / "fabrication"
    if fab.exists():
        shutil.rmtree(fab)
    fab.mkdir()
    run(
        [
            cli,
            "pcb",
            "export",
            "gerbers",
            "--layers",
            "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,Edge.Cuts",
            "--output",
            str(fab) + "/",
            pcb,
        ]
    )
    run(
        [
            cli,
            "pcb",
            "export",
            "drill",
            "--excellon-separate-th",
            "--output",
            str(fab) + "/",
            pcb,
        ]
    )
    run([sys.executable, HERE / "verify.py"], HERE / "validation.json")
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "electronics.tests.test_charging_interlock_rev_b",
            "-v",
        ],
        EVIDENCE / "regression-tests.txt",
    )
    # Archive exactly eight verified fabrication files, no source or incidental jobs.
    files = sorted(
        f
        for f in fab.iterdir()
        if f.suffix in {".gtl", ".gbl", ".gts", ".gbs", ".gto", ".gm1", ".drl"}
    )
    assert len(files) == 8, [f.name for f in files]
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            info = zipfile.ZipInfo(f.name, date_time=(2026, 9, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, f.read_bytes())
    # Hash both the actual upload and each fabrication input, without changing KiCad data.
    hashed = [pcb, archive, *files]
    (HERE / "SHA256SUMS").write_text(
        "".join(
            hashlib.sha256(f.read_bytes()).hexdigest()
            + "  "
            + str(f.relative_to(HERE))
            + "\n"
            for f in hashed
        )
    )
    shutil.copyfile(HERE / "validation.json", EVIDENCE / "validation.json")
    print(
        "PASS: order package created after DRC, independent verification, and fault regressions."
    )


if __name__ == "__main__":
    main()
