#!/usr/bin/env python3
"""Structural checks for the W1 Sherman prototype netlist."""

from __future__ import annotations

import csv
import re
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NETLIST = ROOT / "electronics" / "prototype-netlist.csv"
GUIDE = ROOT / "electronics" / "wiring-guide.md"
ELI5_GUIDE = ROOT / "electronics" / "wiring-guide-eli5.md"
INTERLOCK_DIAGRAM = ROOT / "electronics" / "diagrams" / "charging-interlock.svg"
FIELDS = {
    "net",
    "domain",
    "source_endpoint",
    "destination_endpoint",
    "direction",
    "wire",
    "stage",
    "status",
    "notes",
}
REQUIRED_NETS = {
    "HOST_TX",
    "HOST_RX",
    "FRONT_SCL",
    "FRONT_SDA",
    "FRONT_LPN_N",
    "FRONT_INT_N",
    "FRONT_I2C_RST",
    "SAFE_SCL",
    "SAFE_SDA",
    "CLIFF_L_XSHUT_N",
    "CLIFF_R_XSHUT_N",
    "MOTOR_SLEEP_N",
    "MOTOR_RAIL_REQUEST",
    "MOTOR_SLEEP_REQUEST",
    "MOTOR_GATE_CTRL",
    "MOTOR_FAULT_N",
    "CHARGE_IN_5V",
    "CHARGE_ABSENT",
    "CHARGE_VBUS_SENSE",
    "VBAT_RAW",
    "VBAT_FUSED",
    "LOAD_RAW",
    "LOAD_FUSED",
    "SYS_SW",
    "MOTOR_VIN",
    "DOCK_5V_RAW",
    "DOCK_5V",
    "DOCK_PILOT",
    "DOCK_RELEASE_N",
    "5V_SYS",
}
POWER_PINS = {
    "Luckfox_P1_pin_1",
    "Luckfox_P1_pin_2",
    "Luckfox_P1_pin_4",
    "Luckfox_P1_pin_6",
    "Luckfox_P1_pin_9",
    "Luckfox_P1_pin_14",
    "Luckfox_P1_pin_17",
    "Luckfox_P1_pin_20",
    "Luckfox_P1_pin_25",
    "Pico2_pin_3_GND",
    "Pico2_pin_8_GND",
    "Pico2_pin_13_GND",
    "Pico2_pin_18_GND",
    "Pico2_pin_23_GND",
    "Pico2_pin_28_GND",
    "Pico2_pin_36_3V3_OUT",
    "Pico2_pin_38_GND",
    "Pico2_pin_39_VSYS",
}


def rows() -> list[dict[str, str]]:
    with NETLIST.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if set(reader.fieldnames or ()) != FIELDS:
            raise AssertionError(f"unexpected columns: {reader.fieldnames}")
        return list(reader)


class PrototypeNetlistTest(unittest.TestCase):
    def test_shape_and_enumerations(self) -> None:
        ledger = rows()
        self.assertEqual(len(ledger), 104)
        for line, row in enumerate(ledger, start=2):
            self.assertTrue(all(value.strip() for key, value in row.items() if key != "notes"), line)
            self.assertIn(row["stage"], set("ABCDEFG"), line)
            self.assertIn(row["status"], {"verified", "proposed", "gated"}, line)

    def test_required_nets_exist(self) -> None:
        self.assertLessEqual(REQUIRED_NETS, {row["net"] for row in rows()})

    def test_signal_pin_has_one_owner(self) -> None:
        owners: defaultdict[str, set[str]] = defaultdict(set)
        signal_pin = re.compile(r"^(Luckfox_P1_pin_\d+|Pico2_pin_\d+)(?:_|$)")
        for row in rows():
            for endpoint in (row["source_endpoint"], row["destination_endpoint"]):
                match = signal_pin.match(endpoint)
                if match and match.group(1) not in POWER_PINS:
                    owners[match.group(1)].add(row["net"])
        conflicts = {pin: nets for pin, nets in owners.items() if len(nets) != 1}
        self.assertEqual(conflicts, {})

    def test_no_5v_logic_and_no_joined_3v3_domains(self) -> None:
        for line, row in enumerate(rows(), start=2):
            if row["domain"] == "5V":
                self.assertEqual(row["direction"], "power", line)
            endpoints = row["source_endpoint"] + " " + row["destination_endpoint"]
            self.assertFalse(
                "3V3_PICO" in endpoints and "3V3_LUCKFOX" in endpoints,
                line,
            )
        domains = defaultdict(set)
        for row in rows():
            domains[row["net"]].add(row["domain"])
        self.assertEqual(domains["3V3_PICO"], {"3.3V_PICO"})
        self.assertEqual(domains["FRONT_3V3"], {"3.3V_LUCKFOX"})

    def test_exact_luckfox_ultra_w_p1_mapping(self) -> None:
        by_net = defaultdict(list)
        for row in rows():
            by_net[row["net"]].append(row)

        expected = {
            "GND_UART": ("Luckfox_P1_pin_9_GND", "Pico2_pin_3_GND"),
            "HOST_TX": (
                "Luckfox_P1_pin_11_GPIO1_B1_UART4_M0_TX",
                "Pico2_pin_2_GP1_UART0_RX",
            ),
            "HOST_RX": (
                "Pico2_pin_1_GP0_UART0_TX",
                "Luckfox_P1_pin_7_GPIO1_B0_UART4_M0_RX",
            ),
            "FRONT_SCL": (
                "Luckfox_P1_pin_3_GPIO1_A0_I2C2_SCL_M0",
                "Pololu_3417_SCL",
            ),
            "FRONT_SDA": (
                "Luckfox_P1_pin_5_GPIO1_A1_I2C2_SDA_M0",
                "Pololu_3417_SDA",
            ),
            "FRONT_LPN_N": (
                "Luckfox_P1_pin_18_GPIO2_A6",
                "Pololu_3417_LPn",
            ),
            "FRONT_INT_N": (
                "Pololu_3417_INT",
                "Luckfox_P1_pin_12_GPIO1_C6",
            ),
            "FRONT_I2C_RST": (
                "Luckfox_P1_pin_16_GPIO2_A7",
                "Pololu_3417_I2C_RST",
            ),
        }
        for net, endpoints in expected.items():
            self.assertEqual(len(by_net[net]), 1, net)
            row = by_net[net][0]
            self.assertEqual((row["source_endpoint"], row["destination_endpoint"]), endpoints)

    def test_uart2_debug_console_is_never_in_netlist(self) -> None:
        serialized = NETLIST.read_text(encoding="utf-8")
        self.assertNotIn("UART2", serialized)
        self.assertNotRegex(serialized, r"Luckfox_P1_pin_(8|10)(?:_|,)")
        guide = GUIDE.read_text(encoding="utf-8")
        self.assertIn("UART2 M1 on P1 pins 8/10 is the active FIQ/debug console", guide)
        self.assertIn("pinctrl-0 = <&uart4m0_xfer>;", guide)

    def test_motor_sleep_has_required_fail_safe_pulldown(self) -> None:
        sleep = [row for row in rows() if row["net"] == "MOTOR_SLEEP_N"]
        self.assertEqual(len(sleep), 2)
        direct = next(row for row in sleep if row["source_endpoint"] == "Interlock_PCB_J3_2_SLEEP")
        pulldown = next(row for row in sleep if row["direction"] == "internal_pcb")
        self.assertEqual(direct["destination_endpoint"], "Pololu_2130_nSLEEP_SLP")
        request = next(row for row in rows() if row["net"] == "MOTOR_SLEEP_REQUEST")
        self.assertEqual(request["source_endpoint"], "Pico2_pin_16_GP12")
        self.assertEqual(request["destination_endpoint"], "Interlock_PCB_J1_4_GP12")
        self.assertEqual(pulldown["source_endpoint"], "Interlock_PCB_R7_4.7k")
        self.assertEqual(pulldown["destination_endpoint"], "Interlock_PCB_J3_3_GND")
        self.assertEqual({row["status"] for row in sleep}, {"gated"})

    def test_charge_interlock_has_two_hardware_inhibits(self) -> None:
        ledger = rows()
        charge_absent = [row for row in ledger if row["net"] == "CHARGE_ABSENT"]
        self.assertEqual(len(charge_absent), 3)
        self.assertTrue(
            any(row["source_endpoint"] == "Adafruit_4755_PGOOD" for row in charge_absent)
        )
        self.assertTrue(
            any(
                row["source_endpoint"] == "Interlock_PCB_Q1_2N3904BU_collector"
                for row in charge_absent
            )
        )
        vbus = next(row for row in ledger if row["net"] == "CHARGE_VBUS_SENSE")
        self.assertEqual(vbus["source_endpoint"], "Adafruit_4755_VBUS")
        self.assertEqual(vbus["destination_endpoint"], "Interlock_PCB_J2_1_VBUS")
        motor_gate = next(
            row
            for row in ledger
            if row["net"] == "MOTOR_GATE_CTRL" and row["direction"] != "internal_pcb"
        )
        self.assertEqual(motor_gate["source_endpoint"], "Interlock_PCB_J3_1_RAIL")
        self.assertEqual(motor_gate["destination_endpoint"], "Pololu_2808_M_CTRL")
        sleep = next(
            row
            for row in ledger
            if row["net"] == "MOTOR_SLEEP_N" and row["direction"] != "internal_pcb"
        )
        self.assertEqual(sleep["source_endpoint"], "Interlock_PCB_J3_2_SLEEP")
        grounds = [row for row in ledger if row["net"] == "INTERLOCK_GND"]
        self.assertEqual(len(grounds), 4)
        ground_endpoints = {
            endpoint
            for row in grounds
            for endpoint in (row["source_endpoint"], row["destination_endpoint"])
        }
        self.assertLessEqual(
            {
                "Interlock_PCB_J1_2_GND",
                "Interlock_PCB_J2_3_GND",
                "Interlock_PCB_J3_3_GND",
            },
            ground_endpoints,
        )

    def test_i2c_clock_is_bidirectional_open_drain(self) -> None:
        scl_rows = [row for row in rows() if row["net"] in {"SAFE_SCL", "FRONT_SCL"}]
        self.assertTrue(scl_rows)
        for row in scl_rows:
            self.assertEqual(row["direction"], "bidirectional")
            self.assertRegex(row["notes"].lower(), r"open_drain|open drain")

    def test_no_positive_battery_branch_bypasses_fuse(self) -> None:
        ledger = rows()
        raw = [row for row in ledger if row["net"] == "VBAT_RAW"]
        self.assertEqual(len(raw), 1)
        self.assertEqual(raw[0]["source_endpoint"], "Adafruit_258_JST_positive")
        self.assertEqual(raw[0]["destination_endpoint"], "Selected_battery_fuse_input")
        gauge = next(
            row for row in ledger if row["destination_endpoint"] == "Adafruit_5580_BAT_JST_positive"
        )
        charger = next(
            row
            for row in ledger
            if row["destination_endpoint"] == "Adafruit_4755_BATT_LIPO_positive"
        )
        load = next(
            row for row in ledger if row["source_endpoint"] == "Adafruit_4755_LOAD_OUT_positive"
        )
        system_switch = next(
            row for row in ledger if row["destination_endpoint"] == "Pololu_2808_S_VIN"
        )
        motor_gate = next(
            row for row in ledger if row["destination_endpoint"] == "Pololu_2808_M_VIN"
        )
        self.assertEqual(gauge["net"], "VBAT_FUSED")
        self.assertEqual(charger["net"], "VBAT_FUSED")
        self.assertEqual(load["net"], "LOAD_RAW")
        self.assertEqual(load["destination_endpoint"], "Selected_system_fuse_input")
        self.assertEqual(system_switch["net"], "LOAD_FUSED")
        self.assertEqual(motor_gate["net"], "VBAT_FUSED")

    def test_exact_cell_charge_setting_is_500ma(self) -> None:
        settings = [row for row in rows() if row["net"] == "CHARGE_ISET"]
        self.assertEqual(len(settings), 2)
        one_amp = next(row for row in settings if "1A_jumper" in row["source_endpoint"])
        half_amp = next(row for row in settings if "0.5A_jumper" in row["source_endpoint"])
        self.assertEqual(one_amp["destination_endpoint"], "Open_cut_trace")
        self.assertEqual(half_amp["destination_endpoint"], "Closed_solder_bridge")
        self.assertEqual({row["status"] for row in settings}, {"gated"})

    def test_bench_guide_preserves_names_and_critical_connections(self) -> None:
        guide = ELI5_GUIDE.read_text(encoding="utf-8")
        engineering_guide = GUIDE.read_text(encoding="utf-8")
        netlist = NETLIST.read_text(encoding="utf-8")
        self.assertIn("**the Pico** means the Raspberry Pi Pico 2", guide)
        self.assertIn("**the Luckfox** means the Luckfox Pico Ultra W", guide)
        self.assertIn("P1 pin 9", guide)
        self.assertIn("P1 pin 11", guide)
        self.assertIn("P1 pin 7", guide)
        self.assertIn("Pico physical pin 36", guide)
        self.assertIn("factory `1.0A`", guide)
        self.assertRegex(guide, r"bridge only the\s+`0\.5A` jumper")
        self.assertIn("#4410", guide)
        self.assertIn("Do not use P1 pins 8 or 10", guide)
        self.assertNotIn("SDI", guide)
        self.assertNotIn("SDI", engineering_guide)
        self.assertNotIn("SDI", netlist)
        self.assertIn("Adafruit_5580_SDA", netlist)
        self.assertTrue(INTERLOCK_DIAGRAM.is_file())
        self.assertIn("diagrams/charging-interlock.svg", guide)
        self.assertIn("diagrams/charging-interlock.svg", engineering_guide)


if __name__ == "__main__":
    unittest.main()
