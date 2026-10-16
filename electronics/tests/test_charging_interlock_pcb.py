#!/usr/bin/env python3
"""Structural and regeneration checks for the charge-interlock Rev A PCB."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import unittest
import zipfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOARD = ROOT / "electronics" / "pcb" / "charging-interlock-rev-a"
GENERATOR = BOARD / "generate.py"
ZIP = BOARD / "charging-interlock-rev-a-gerbers.zip"


def digest_tree() -> dict[str, str]:
    excluded = {"README.md", "generate.py"}
    return {
        str(path.relative_to(BOARD)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(BOARD.rglob("*"))
        if path.is_file() and path.name not in excluded and "__pycache__" not in path.parts
    }


class ChargingInterlockPcbTest(unittest.TestCase):
    def test_regeneration_is_deterministic(self) -> None:
        before = digest_tree()
        subprocess.run(["python3", str(GENERATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
        self.assertEqual(digest_tree(), before)

    def test_expected_geometry_and_rules(self) -> None:
        report = json.loads((BOARD / "verification.json").read_text(encoding="utf-8"))
        self.assertEqual((report["board_width_mm"], report["board_height_mm"]), (38.1, 24.13))
        self.assertEqual(report["nets"], 9)
        self.assertGreaterEqual(report["minimum_clearance_mm"], 0.30)
        self.assertGreaterEqual(report["signal_width_mm"], 0.40)
        self.assertGreaterEqual(report["supply_width_mm"], 0.60)

    def test_order_zip_has_complete_two_layer_fabrication_set(self) -> None:
        expected_suffixes = {
            "-F_Cu.gtl", "-B_Cu.gbl", "-F_Mask.gts", "-B_Mask.gbs",
            "-F_Silkscreen.gto", "-Edge_Cuts.gm1", "-PTH.drl", "-NPTH.drl",
            "-job.gbrjob",
        }
        with zipfile.ZipFile(ZIP) as archive:
            names = set(archive.namelist())
            self.assertEqual(len(names), len(expected_suffixes))
            for suffix in expected_suffixes:
                self.assertEqual(sum(name.endswith(suffix) for name in names), 1, suffix)
            for name in names:
                content = archive.read(name)
                if name.endswith((".gtl", ".gbl", ".gts", ".gbs", ".gto", ".gm1")):
                    self.assertTrue(content.rstrip().endswith(b"M02*"), name)
                if name.endswith(".drl"):
                    self.assertTrue(content.rstrip().endswith(b"M30"), name)

    def test_connector_contract_and_logic_pinout(self) -> None:
        with (BOARD / "netlist.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        pins = {(row["endpoint"], row["pin"]): row["net"] for row in rows}
        expected = {
            ("J1", "1"): "3V3", ("J1", "2"): "GND", ("J1", "3"): "GP3",
            ("J1", "4"): "GP12", ("J1", "5"): "CHARGE_ABSENT",
            ("J2", "1"): "VBUS", ("J2", "2"): "CHARGE_ABSENT", ("J2", "3"): "GND",
            ("J3", "1"): "RAIL_EN", ("J3", "2"): "SLEEP_EN", ("J3", "3"): "GND",
            ("U1", "1"): "GP3", ("U1", "2"): "CHARGE_ABSENT", ("U1", "3"): "RAIL_EN",
            ("U1", "4"): "GP12", ("U1", "5"): "CHARGE_ABSENT", ("U1", "6"): "SLEEP_EN",
            ("U1", "7"): "GND", ("U1", "9"): "GND", ("U1", "10"): "GND",
            ("U1", "12"): "GND", ("U1", "13"): "GND", ("U1", "14"): "3V3",
            ("Q1", "1"): "GND", ("Q1", "2"): "QBASE", ("Q1", "3"): "CHARGE_ABSENT",
        }
        self.assertLessEqual(expected.items(), pins.items())

    def test_per_board_bom_and_two_board_totals(self) -> None:
        with (BOARD / "bom.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        quantities = defaultdict(int)
        for row in rows:
            quantities[row["value"]] += int(row["quantity"])
        self.assertEqual(quantities["SN74HC08N"], 1)
        self.assertEqual(quantities["2N3904BU"], 1)
        self.assertEqual(quantities["100nF"], 1)
        self.assertEqual(quantities["10k"], 4)
        self.assertEqual(quantities["47k"], 1)
        self.assertEqual(quantities["100k"], 1)
        self.assertEqual(quantities["4.7k"], 1)

    def test_order_status_and_guides_use_the_fabricated_pcb_contract(self) -> None:
        readme = (BOARD / "README.md").read_text(encoding="utf-8")
        manifest = (BOARD / "order-manifest.md").read_text(encoding="utf-8")
        engineering = (ROOT / "electronics" / "wiring-guide.md").read_text(encoding="utf-8")
        eli5 = (ROOT / "electronics" / "wiring-guide-eli5.md").read_text(encoding="utf-8")

        self.assertIn("three bare boards", readme.lower())
        self.assertIn("Orders placed: 2026-09-01", manifest)
        self.assertNotIn("No purchase was submitted", manifest)
        for guide in (engineering, eli5):
            for connector_pin in ("J1.1 3V3", "J1.5 CA", "J2.1 VBUS", "J3.1 RAIL", "J3.2 SLEEP"):
                self.assertIn(connector_pin, guide)
            self.assertNotIn("retained perfboard", guide.lower())
        self.assertRegex(eli5, r"do not add another one at\s+the driver")


if __name__ == "__main__":
    unittest.main()
