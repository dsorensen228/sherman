from __future__ import annotations

import unittest

from display.backends.st7789 import DisplayRegion, St7789Config, St7789Display


class FakeSpi:
    def __init__(self) -> None:
        self.mode = -1
        self.max_speed_hz = 0
        self.bits_per_word = 0
        self.writes: list[bytes] = []
        self.closed = False

    def writebytes(self, values: list[int]) -> None:
        self.writes.append(bytes(values))

    def writebytes2(self, values: object) -> None:
        self.writes.append(bytes(values))  # type: ignore[arg-type]

    def close(self) -> None:
        self.closed = True


class FakePin:
    def __init__(self, line: int) -> None:
        self.line = line
        self.values: list[bool] = []
        self.closed = False

    def write(self, value: bool) -> None:
        self.values.append(value)

    def close(self) -> None:
        self.closed = True


class BackendTest(unittest.TestCase):
    def setUp(self) -> None:
        self.spi = FakeSpi()
        self.pins: dict[int, FakePin] = {}
        self.now = 10.0
        self.backend = St7789Display(
            St7789Config(width=4, height=2, x_offset=0, y_offset=35),
            spi_factory=lambda _bus, _device: self.spi,
            pin_factory=self._pin_factory,
            sleep=lambda _seconds: None,
            clock=self._clock,
        )

    def _pin_factory(self, _chip: str, line: int) -> FakePin:
        pin = FakePin(line)
        self.pins[line] = pin
        return pin

    def _clock(self) -> float:
        result = self.now
        self.now += 0.004
        return result

    def test_initialization_configures_bus_and_keeps_backlight_off(self) -> None:
        self.backend.open()
        self.assertTrue(self.backend.ready)
        self.assertEqual(self.spi.mode, 0)
        self.assertEqual(self.spi.max_speed_hz, 16_000_000)
        self.assertEqual(self.spi.bits_per_word, 8)
        self.assertEqual(self.pins[26].values, [False, False])
        self.assertEqual(self.pins[25].values, [False, True])
        self.assertIn(b"\x11", self.spi.writes)
        self.assertIn(b"\x29", self.spi.writes)

    def test_first_frame_sets_landscape_window_then_enables_backlight(self) -> None:
        self.backend.open()
        elapsed = self.backend.show_rgb565(bytes(range(16)))
        self.assertAlmostEqual(elapsed, 4.0)
        self.assertEqual(self.spi.writes[-6:], [
            b"\x2A", b"\x00\x00\x00\x03",
            b"\x2B", b"\x00\x23\x00\x24",
            b"\x2C", bytes(range(16)),
        ])
        self.assertTrue(self.pins[26].values[-1])
        self.assertEqual(self.backend.stats.frames_presented, 1)
        self.assertEqual(self.backend.stats.bytes_transferred, 16)

    def test_bad_frame_is_rejected_before_bus_write(self) -> None:
        self.backend.open()
        write_count = len(self.spi.writes)
        with self.assertRaisesRegex(ValueError, "expected 16"):
            self.backend.show_rgb565(b"too short")
        self.assertEqual(len(self.spi.writes), write_count)
        self.assertEqual(self.backend.stats.frames_presented, 0)

    def test_region_repackages_rows_and_sets_bounded_window(self) -> None:
        self.backend.open()
        frame = bytes(range(16))
        self.backend.show_rgb565(frame)
        self.spi.writes.clear()
        self.backend.show_rgb565_region(frame, DisplayRegion(1, 0, 2, 2))
        self.assertEqual(self.spi.writes, [
            b"\x2A", b"\x00\x01\x00\x02",
            b"\x2B", b"\x00\x23\x00\x24",
            b"\x2C", bytes((2, 3, 4, 5, 10, 11, 12, 13)),
        ])
        self.assertEqual(self.backend.stats.frames_presented, 2)
        self.assertEqual(self.backend.stats.bytes_transferred, 24)

    def test_first_region_is_promoted_to_safe_full_frame(self) -> None:
        self.backend.open()
        self.backend.show_rgb565_region(
            bytes(range(16)), DisplayRegion(1, 0, 2, 2)
        )
        self.assertEqual(self.spi.writes[-1], bytes(range(16)))
        self.assertEqual(self.backend.stats.bytes_transferred, 16)

    def test_out_of_bounds_region_is_rejected_before_bus_write(self) -> None:
        self.backend.open()
        write_count = len(self.spi.writes)
        with self.assertRaisesRegex(ValueError, "beyond"):
            self.backend.show_rgb565_region(
                bytes(range(16)), DisplayRegion(3, 0, 2, 2)
            )
        self.assertEqual(len(self.spi.writes), write_count)

    def test_close_blanks_and_closes_every_resource(self) -> None:
        self.backend.open()
        self.backend.show_rgb565(bytes(16))
        self.backend.close()
        self.assertFalse(self.backend.ready)
        self.assertFalse(self.pins[26].values[-1])
        self.assertTrue(self.spi.closed)
        self.assertTrue(all(pin.closed for pin in self.pins.values()))


if __name__ == "__main__":
    unittest.main()
