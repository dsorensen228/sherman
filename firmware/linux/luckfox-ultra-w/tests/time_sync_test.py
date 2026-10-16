import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "time_sync", Path(__file__).resolve().parents[1] / "bin/configure-time-sync.py"
)
time_sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(time_sync)


class TimeSyncTest(unittest.TestCase):
    def test_only_camera_ntp_changes_and_second_run_is_identical(self):
        original = "[video]\nenable = 1\n[network.ntp]\nenable = 1\nrefresh_time_s = 60\nntp_server = example\n[audio]\nenable = 1\n"
        expected = original.replace(
            "[network.ntp]\nenable = 1", "[network.ntp]\nenable = 0"
        )
        self.assertEqual(time_sync.disable_camera_ntp(original), expected)
        self.assertEqual(time_sync.disable_camera_ntp(expected), expected)

    def test_last_section_and_unexpected_configuration(self):
        self.assertEqual(
            time_sync.disable_camera_ntp("[network.ntp]\nenable=1\n"),
            "[network.ntp]\nenable=0\n",
        )
        for text in (
            "[video]\nenable=1\n",
            "[network.ntp]\nenable=yes\n",
            "[network.ntp]\nenable=1\nenable=0\n",
        ):
            with self.assertRaises(ValueError):
                time_sync.disable_camera_ntp(text)
