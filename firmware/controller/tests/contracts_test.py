import csv
import importlib.util
import json
import os
import pty
import re
import subprocess
import sys
import tty
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "link", ROOT / "firmware/controller/tools/link.py"
)
link = importlib.util.module_from_spec(spec)
spec.loader.exec_module(link)
CODEC = sys.argv.pop(1)


class Contracts(unittest.TestCase):
    def test_cross_language_golden(self):
        fixtures = json.loads((ROOT / "proto/fixtures/controller-v1.json").read_text())
        for f in fixtures:
            data = link.encode(f["name"], f["sequence"], f["session"], **f["payload"])
            self.assertEqual(data.hex(), f["hex"])
            result = subprocess.run(
                [CODEC],
                input=data.hex() + "\n",
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual(result.stdout.strip(), data.hex())
            decoded = link.decode(bytes.fromhex(result.stdout.strip()))
            self.assertEqual(decoded["payload"], f["payload"])

    def test_controller_telemetry_fields(self):
        result = subprocess.run(
            [CODEC, "--telemetry"], text=True, capture_output=True, check=True
        )
        status, sensors, odometry = [
            link.decode(bytes.fromhex(line)) for line in result.stdout.splitlines()
        ]
        self.assertEqual(status["session"], 123)
        self.assertEqual(status["payload"]["qualified"], 0)
        self.assertEqual(status["payload"]["watchdog_reset"], 1)
        self.assertEqual(status["payload"]["rx_errors"], 7)
        self.assertEqual(sensors["payload"]["cliff_right_mm"], 21)
        self.assertEqual(sensors["payload"]["imu_age_ms"], 8)
        self.assertEqual(sensors["payload"]["battery_mv"], 3800)
        self.assertEqual(sensors["payload"]["gx_mdeg_s"], -120)
        self.assertEqual(sensors["payload"]["az_mg"], 1000)
        self.assertEqual(sensors["payload"]["valid_mask"], 15)
        self.assertEqual(sensors["payload"]["input_mask"], 3)
        self.assertEqual(odometry["payload"]["left_ticks"], 0xFFFFFFFF)
        self.assertEqual(odometry["payload"]["right_ticks"], 1234)

    def test_malformed_and_recovery(self):
        packet = link.encode("STOP", 0, 0)
        for data in (
            packet[:-1],
            packet + b"x",
            b"x" + packet[1:],
            packet[:-1] + bytes([packet[-1] ^ 1]),
        ):
            with self.assertRaises(ValueError):
                link.decode(data)
        stream = link.Stream()
        self.assertEqual(stream.feed(b"noise" + packet[:5], 0), [])
        self.assertEqual(len(stream.feed(packet, 0.021)), 1)
        self.assertEqual(stream.errors, 1)
        for value in range(256):
            stream.feed(bytes([value]) * 100, 1)
            self.assertLessEqual(len(stream.buffer), 84)
        self.assertEqual(len(stream.feed(packet, 2)), 1)

    def test_monitor_cli_failure_paths(self):
        tool = str(ROOT / "firmware/controller/tools/link.py")
        for args in (
            [],
            ["--device", "/definitely-not-a-sherman-device"],
            ["--device", "/dev/null", "--seconds", "0"],
            ["--device", "/dev/null", "--seconds", "nan"],
        ):
            result = subprocess.run(
                [sys.executable, tool, *args],
                input="",
                text=True,
                capture_output=True,
                timeout=3,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(result.stderr)

    def test_monitor_uart_and_timeout(self):
        master, slave = pty.openpty()
        try:
            tty.setraw(slave)
            device = os.ttyname(slave)
            os.write(master, link.encode("STOP", 0, 0))
            command = [
                sys.executable,
                str(ROOT / "firmware/controller/tools/link.py"),
                "--device",
                device,
                "--seconds",
                "0.03",
            ]
            result = subprocess.run(
                command,
                input="",
                text=True,
                capture_output=True,
                timeout=3,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout.splitlines()[0])["type"], "STOP")
            # The consumed fixture leaves a silent UART with a finite failure deadline.
            result = subprocess.run(
                command,
                input="",
                text=True,
                capture_output=True,
                timeout=3,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no valid controller telemetry", result.stderr)
        finally:
            os.close(master)
            os.close(slave)

    def test_pins_match_canonical_netlist(self):
        header = (ROOT / "firmware/controller/include/sherman/pins.hpp").read_text()
        pins = {k: int(v) for k, v in re.findall(r"(\w+)\s*=\s*(\d+)", header)}
        checked = set()
        with (ROOT / "electronics/prototype-netlist.csv").open() as f:
            for row in csv.DictReader(f):
                if row["net"] not in pins:
                    continue
                endpoints = row["source_endpoint"] + " " + row["destination_endpoint"]
                match = re.search(r"Pico2_pin_\d+_GP(\d+)", endpoints)
                if match:
                    self.assertEqual(pins[row["net"]], int(match[1]), row["net"])
                    checked.add(row["net"])
        self.assertEqual(set(pins) - checked, {"CTRL_READY"})
        self.assertEqual(len(set(pins.values())), len(pins))

    def test_generated_source_current(self):
        target = ROOT / "firmware/controller/include/sherman/wire_generated.hpp"
        before = target.read_bytes()
        subprocess.run(
            [sys.executable, str(ROOT / "proto/tools/generate_controller.py")],
            check=True,
        )
        self.assertEqual(target.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
