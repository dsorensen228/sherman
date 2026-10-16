import json
import math
import pathlib
import re
import unittest


PACKAGE = pathlib.Path(__file__).resolve().parents[1]


class HardwareProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads((PACKAGE / "hardware-profile.json").read_text())
        cls.face_config = json.loads(
            (PACKAGE / "config" / "face-runtime.json").read_text()
        )
        cls.config = {}
        for line in (PACKAGE / "luckfox.cfg").read_text().splitlines():
            key, value = line.split("=", 1)
            if key in cls.config:
                raise AssertionError(f"duplicate config key: {key}")
            cls.config[key] = value

    def test_config_matches_recorded_display_bus(self) -> None:
        self.assertEqual(self.config["RGB_ENABLE"], "0")
        self.assertEqual(self.config["SPI0_M0_STATUS"], "1")
        self.assertEqual(self.config["SPI0_M0_CS_ENABLE"], "1")
        self.assertEqual(self.config["SPI0_M0_MISO_ENABLE"], "0")
        self.assertEqual(
            int(self.config["SPI0_M0_SPEED"]),
            self.profile["display"]["known_good_max_hz"],
        )
        self.assertEqual(self.config["UART4_M0_STATUS"], "1")
        self.assertEqual(self.config["I2C2_M0_STATUS"], "1")
        self.assertEqual(self.config["I2C2_M0_SPEED"], "100000")

    def test_rgb565_frame_budget_is_internally_consistent(self) -> None:
        display = self.profile["display"]
        width = display["geometry_px"]["width"]
        height = display["geometry_px"]["height"]
        expected_bytes = width * height * 2
        expected_fps = display["known_good_max_hz"] / (expected_bytes * 8)
        self.assertEqual(display["full_frame_bytes"], expected_bytes)
        self.assertTrue(
            math.isclose(
                display["theoretical_full_frame_fps_at_known_good_max"],
                expected_fps,
                abs_tol=0.01,
            )
        )

    def test_gpio_control_lines_have_consistent_offsets(self) -> None:
        pins = {pin["signal"]: pin for pin in self.profile["display"]["pins"]}
        expected = {
            "DC": (13, "GPIO1_D0", 24),
            "RST": (15, "GPIO1_D1", 25),
            "BL": (26, "GPIO1_D2", 26),
        }
        for signal, (physical_pin, soc_pin, offset) in expected.items():
            with self.subTest(signal=signal):
                pin = pins[signal]
                self.assertEqual(pin["physical_pin"], physical_pin)
                self.assertEqual(pin["soc_pin"], soc_pin)
                self.assertEqual(pin["line_offset"], offset)
                self.assertEqual(pin["legacy_global_gpio"], 32 + offset)

    def test_backup_hashes_are_sha256(self) -> None:
        known_good = self.profile["known_good"]
        for name in (
            "pre_change_boot_sha256",
            "pre_change_cfg_sha256",
            "post_change_boot_sha256",
            "post_change_cfg_sha256",
        ):
            with self.subTest(name=name):
                self.assertRegex(known_good[name], re.compile(r"^[0-9a-f]{64}$"))

    def test_boot_face_is_autonomous_and_persists_on_userdata(self) -> None:
        config = self.face_config
        self.assertEqual(config["schema_version"], 1)
        self.assertEqual(config["mode"], "personality")
        self.assertEqual(config["personality_tick_hz"], 10)
        self.assertEqual(
            config["personality_state_file"],
            "/userdata/sherman/personality.state",
        )
        self.assertTrue(config["circadian_enabled"])
        self.assertEqual(config["timezone"], "EST5EDT,M3.2.0/2,M11.1.0/2")
        self.assertEqual(config["seed"], 0x534845524D414E)
        init_script = (PACKAGE / "init" / "S99sherman-face").read_text()
        self.assertIn('--config "$CONFIG"', init_script)
        self.assertIn('[ -r "$PERSONALITY_LIBRARY" ]', init_script)
        self.assertIn('"personality_degraded":false', init_script)
        self.assertIn("STARTUP_POLLS", init_script)
        self.assertNotIn("--demo", init_script)

    def test_deploy_preserves_startup_diagnostic_before_rollback(self) -> None:
        deploy_script = (PACKAGE / "bin" / "deploy-face.sh").read_text()
        preserve_call = 'preserve_deploy_failure "$failure_reason"'
        rollback_call = "if ! rollback; then"
        self.assertIn("/run/sherman-face.deploy-failure", deploy_script)
        self.assertLess(
            deploy_script.index(preserve_call),
            deploy_script.index(rollback_call),
        )


if __name__ == "__main__":
    unittest.main()
