"""Independent Rev B acceptance and real-fault regression tests.

Run with electronics/pcb/charging-interlock-rev-b/.venv/bin/python -m unittest
 electronics.tests.test_charging_interlock_rev_b
"""

import copy
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOARD = ROOT / "electronics/pcb/charging-interlock-rev-b"
spec = importlib.util.spec_from_file_location("verify_interlock", BOARD / "verify.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class RevBVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.pads, _, cls.mounts = v.read_board(
            BOARD / "charging-interlock-rev-b.kicad_pcb"
        )

    def test_actual_board_matches_manufacturer_pin_geometry_and_w1_circuit(self):
        self.assertEqual(v.pin_orientation_errors(self.pads), [])
        self.assertEqual(v.circuit_errors(self.pads), [])

    def test_exact_part_envelopes_and_lead_access(self):
        errors, gaps, _ = v.mechanical_errors(self.pads, self.mounts)
        self.assertEqual(errors, [])
        self.assertGreaterEqual(gaps[0][0], 0.5)

    def test_rev_a_is_rejected_for_both_observed_defects(self):
        _, pads, _, mounts = v.read_board(
            ROOT
            / "electronics/pcb/charging-interlock-rev-a/charging-interlock-rev-a.kicad_pcb"
        )
        self.assertTrue(v.pin_orientation_errors(pads))
        errors, _, _ = v.mechanical_errors(pads, mounts)
        self.assertTrue(any("U1 obstructs Q1.1" in e for e in errors))

    def test_mirroring_current_ic_is_rejected(self):
        pads = copy.deepcopy(self.pads)
        yy = [p["y"] for (r, _), p in pads.items() if r == "U1"]
        for (r, _), p in pads.items():
            if r == "U1":
                p["y"] = min(yy) + max(yy) - p["y"]
        self.assertEqual(len(v.pin_orientation_errors(pads)), 14)

    def test_transistor_moved_beneath_socket_is_rejected(self):
        pads = copy.deepcopy(self.pads)
        for (r, _), p in pads.items():
            if r == "Q1":
                p["x"] -= 8
        errors, _, _ = v.mechanical_errors(pads, self.mounts)
        self.assertTrue(any("U1 obstructs Q1." in e for e in errors))

    def test_exported_copper_drills_masks_outline_and_mount_clearance(self):
        errors, stats = v.gerber_errors(BOARD / "fabrication", self.pads, self.mounts)
        self.assertEqual(errors, [])
        self.assertEqual(stats["component_pads"], 44)
        self.assertEqual(
            stats["electrical_nets"], 11
        )  # 9 routed nets + 2 isolated outputs

    def test_short_added_to_exported_gerber_is_rejected(self):
        from gerbonara import GerberFile
        from gerbonara.apertures import CircleAperture
        from gerbonara.graphic_objects import Line
        from gerbonara.utils import MM

        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "fabrication"
            shutil.copytree(BOARD / "fabrication", folder)
            f = next(folder.glob("*.gtl"))
            g = GerberFile.open(f)
            a, b = self.pads["C1", "1"], self.pads["C1", "2"]
            g.objects.append(
                Line(
                    a["x"],
                    -a["y"],
                    b["x"],
                    -b["y"],
                    aperture=CircleAperture(0.4064, unit=MM),
                    unit=MM,
                )
            )
            g.save(f)
            errors, _ = v.gerber_errors(folder, self.pads, self.mounts)
            self.assertTrue(any("shorted" in e for e in errors))

    def test_open_added_to_exported_gerbers_is_rejected(self):
        from gerbonara import GerberFile
        from gerbonara.graphic_objects import Line

        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "fabrication"
            shutil.copytree(BOARD / "fabrication", folder)
            removed = 0
            for f in [*folder.glob("*.gtl"), *folder.glob("*.gbl")]:
                g = GerberFile.open(f)
                keep = []
                for o in g.objects:
                    if (
                        isinstance(o, Line)
                        and isinstance(o.attrs, dict)
                        and o.attrs.get(".N") == ("GP3",)
                    ):
                        removed += 1
                    else:
                        keep.append(o)
                g.objects = keep
                g.save(f)
            self.assertGreater(removed, 0)
            errors, _ = v.gerber_errors(folder, self.pads, self.mounts)
            self.assertTrue(any("open net GP3" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
