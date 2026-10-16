"""Bounded userspace backend for Sherman's Waveshare ST7789V2 display.

The renderer hands this module a complete big-endian RGB565 frame. Hardware
imports are lazy and factories are injectable so the protocol can be tested on
a development host without GPIO or SPI devices.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable, Protocol


class _Spi(Protocol):
    mode: int
    max_speed_hz: int
    bits_per_word: int

    def writebytes(self, values: list[int]) -> None: ...

    def writebytes2(self, values: Any) -> None: ...

    def close(self) -> None: ...


class _Pin(Protocol):
    def write(self, value: bool) -> None: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class St7789Config:
    """Exact Phase-1 display profile for the Luckfox Pico Ultra W."""

    width: int = 320
    height: int = 170
    x_offset: int = 0
    y_offset: int = 35
    spi_bus: int = 0
    spi_device: int = 0
    spi_speed_hz: int = 16_000_000
    gpio_chip: str = "/dev/gpiochip1"
    dc_line: int = 24
    reset_line: int = 25
    backlight_line: int = 26
    madctl: int = 0x60

    @property
    def frame_bytes(self) -> int:
        return self.width * self.height * 2

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("display dimensions must be positive")
        if self.spi_speed_hz <= 0 or self.spi_speed_hz > 50_000_000:
            raise ValueError("SPI speed must be in the range 1..50 MHz")
        if min(self.dc_line, self.reset_line, self.backlight_line) < 0:
            raise ValueError("GPIO line offsets must be non-negative")


@dataclass
class DisplayStats:
    frames_presented: int = 0
    bytes_transferred: int = 0
    transfer_errors: int = 0
    last_transfer_ms: float = 0.0
    maximum_transfer_ms: float = 0.0


@dataclass(frozen=True)
class DisplayRegion:
    """A bounded framebuffer rectangle in landscape pixel coordinates."""

    x: int
    y: int
    width: int
    height: int

    @property
    def byte_size(self) -> int:
        return self.width * self.height * 2

    def validate(self, frame_width: int, frame_height: int) -> None:
        if self.x < 0 or self.y < 0 or self.width <= 0 or self.height <= 0:
            raise ValueError(
                "display region must have a non-negative origin and positive size"
            )
        if (
            self.x + self.width > frame_width
            or self.y + self.height > frame_height
        ):
            raise ValueError("display region extends beyond the framebuffer")


def _open_spi(bus: int, device: int) -> _Spi:
    import spidev  # type: ignore[import-not-found]

    spi = spidev.SpiDev()
    spi.open(bus, device)
    return spi


def _open_pin(chip: str, line: int) -> _Pin:
    from periphery import GPIO  # type: ignore[import-not-found]

    return GPIO(chip, line, "out")


class St7789Display:
    """Synchronous, queue-free ST7789V2 RGB565 frame sink.

    Backlight stays off through reset and initialization, and is enabled only
    after the first complete frame reaches the panel. Calls never retain a
    caller's frame, so stale frames cannot accumulate inside the backend.
    """

    def __init__(
        self,
        config: St7789Config = St7789Config(),
        *,
        spi_factory: Callable[[int, int], _Spi] = _open_spi,
        pin_factory: Callable[[str, int], _Pin] = _open_pin,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        config.validate()
        self.config = config
        self.stats = DisplayStats()
        self._spi_factory = spi_factory
        self._pin_factory = pin_factory
        self._sleep = sleep
        self._clock = clock
        self._spi: _Spi | None = None
        self._dc: _Pin | None = None
        self._reset: _Pin | None = None
        self._backlight: _Pin | None = None
        self._initialized = False
        self._visible = False
        self._region_buffer = bytearray()

    @property
    def ready(self) -> bool:
        return self._initialized

    def open(self) -> None:
        if self._spi is not None:
            return
        try:
            self._spi = self._spi_factory(
                self.config.spi_bus, self.config.spi_device
            )
            self._spi.mode = 0
            self._spi.max_speed_hz = self.config.spi_speed_hz
            self._spi.bits_per_word = 8
            self._dc = self._pin_factory(
                self.config.gpio_chip, self.config.dc_line
            )
            self._reset = self._pin_factory(
                self.config.gpio_chip, self.config.reset_line
            )
            self._backlight = self._pin_factory(
                self.config.gpio_chip, self.config.backlight_line
            )
            self._backlight.write(False)
            self._initialize_panel()
        except Exception:
            self.close()
            raise

    def _require_open(self) -> tuple[_Spi, _Pin, _Pin, _Pin]:
        if not all((self._spi, self._dc, self._reset, self._backlight)):
            raise RuntimeError("display backend is not open")
        return self._spi, self._dc, self._reset, self._backlight

    def _command(self, command: int, data: bytes = b"") -> None:
        spi, dc, _, _ = self._require_open()
        dc.write(False)
        spi.writebytes([command])
        if data:
            dc.write(True)
            spi.writebytes2(data)

    def _initialize_panel(self) -> None:
        _, _, reset, backlight = self._require_open()
        backlight.write(False)
        reset.write(False)
        self._sleep(0.020)
        reset.write(True)
        self._sleep(0.150)

        self._command(0x01)  # software reset
        self._sleep(0.150)
        self._command(0x11)  # sleep out
        self._sleep(0.120)
        self._command(0x3A, b"\x55")  # RGB565
        self._command(0x36, bytes((self.config.madctl,)))
        self._command(0xB2, bytes((0x0C, 0x0C, 0x00, 0x33, 0x33)))
        self._command(0xB7, b"\x35")
        self._command(0xBB, b"\x35")
        self._command(0xC0, b"\x2C")
        self._command(0xC2, b"\x01")
        self._command(0xC3, b"\x13")
        self._command(0xC4, b"\x20")
        self._command(0xC6, b"\x0F")
        self._command(0xD0, bytes((0xA4, 0xA1)))
        self._command(0xD6, b"\xA1")
        self._command(
            0xE0,
            bytes((0xD0, 0x00, 0x06, 0x09, 0x0B, 0x2A, 0x3C,
                   0x55, 0x4B, 0x08, 0x16, 0x14, 0x19, 0x20)),
        )
        self._command(
            0xE1,
            bytes((0xD0, 0x00, 0x06, 0x09, 0x0B, 0x29, 0x36,
                   0x54, 0x4B, 0x0D, 0x16, 0x14, 0x21, 0x20)),
        )
        self._command(0x21)  # display inversion on for this IPS panel
        self._command(0x29)  # display on
        self._sleep(0.050)
        self._initialized = True

    def _set_window(self, region: DisplayRegion) -> None:
        cfg = self.config
        region.validate(cfg.width, cfg.height)
        x_start = cfg.x_offset + region.x
        y_start = cfg.y_offset + region.y
        x_end = x_start + region.width - 1
        y_end = y_start + region.height - 1
        self._command(
            0x2A,
            bytes((x_start >> 8, x_start & 0xFF,
                   x_end >> 8, x_end & 0xFF)),
        )
        self._command(
            0x2B,
            bytes((y_start >> 8, y_start & 0xFF,
                   y_end >> 8, y_end & 0xFF)),
        )

    def _present_packed(self, pixels: memoryview, region: DisplayRegion) -> float:
        spi, dc, _, backlight = self._require_open()
        try:
            self._set_window(region)
            dc.write(False)
            spi.writebytes([0x2C])
            dc.write(True)
            started = self._clock()
            spi.writebytes2(pixels)
            elapsed_ms = (self._clock() - started) * 1000.0
            if not self._visible:
                backlight.write(True)
                self._visible = True
            self.stats.frames_presented += 1
            self.stats.bytes_transferred += len(pixels)
            self.stats.last_transfer_ms = elapsed_ms
            self.stats.maximum_transfer_ms = max(
                self.stats.maximum_transfer_ms, elapsed_ms
            )
            return elapsed_ms
        except Exception:
            self.stats.transfer_errors += 1
            raise

    def show_rgb565(self, frame: bytes | bytearray | memoryview) -> float:
        """Present one full big-endian RGB565 frame and return transfer ms."""

        if not self._initialized:
            raise RuntimeError("display backend is not initialized")
        view = memoryview(frame).cast("B")
        if len(view) != self.config.frame_bytes:
            raise ValueError(
                f"expected {self.config.frame_bytes} RGB565 bytes, got {len(view)}"
            )
        return self._present_packed(
            view, DisplayRegion(0, 0, self.config.width, self.config.height)
        )

    def show_rgb565_region(
        self,
        frame: bytes | bytearray | memoryview,
        region: DisplayRegion,
    ) -> float:
        """Present a rectangle from a complete RGB565 framebuffer.

        The first presentation is promoted to a full frame so the backlight is
        never enabled over uninitialized panel memory. Later calls repack one
        bounded rectangle into a reused buffer and transfer only that region.
        """

        if not self._initialized:
            raise RuntimeError("display backend is not initialized")
        view = memoryview(frame).cast("B")
        if len(view) != self.config.frame_bytes:
            raise ValueError(
                f"expected {self.config.frame_bytes} RGB565 bytes, got {len(view)}"
            )
        region.validate(self.config.width, self.config.height)
        if not self._visible:
            return self.show_rgb565(view)

        if len(self._region_buffer) != region.byte_size:
            self._region_buffer = bytearray(region.byte_size)
        packed = memoryview(self._region_buffer)
        source_stride = self.config.width * 2
        row_bytes = region.width * 2
        source_x = region.x * 2
        for row in range(region.height):
            source = (region.y + row) * source_stride + source_x
            target = row * row_bytes
            packed[target:target + row_bytes] = view[source:source + row_bytes]
        return self._present_packed(packed, region)

    def close(self) -> None:
        if self._backlight is not None:
            try:
                self._backlight.write(False)
            except Exception:
                pass
        if self._spi is not None and self._initialized:
            try:
                self._command(0x28)  # display off
            except Exception:
                pass
        for resource in (self._backlight, self._reset, self._dc, self._spi):
            if resource is not None:
                try:
                    resource.close()
                except Exception:
                    pass
        self._spi = None
        self._dc = None
        self._reset = None
        self._backlight = None
        self._initialized = False
        self._visible = False

    def __enter__(self) -> "St7789Display":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
