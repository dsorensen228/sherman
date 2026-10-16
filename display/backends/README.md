# ST7789V2 target backend

`st7789.py` is Sherman's bounded userspace frame sink for the Phase-1
Waveshare 1.9-inch display. It accepts exactly one complete `320 × 170`
big-endian RGB565 frame per call and never owns a frame queue. Backlight stays
off until initialization and the first frame complete successfully.

After that safe full frame, `show_rgb565_region()` can update a validated fixed
rectangle from the same complete framebuffer. It repacks into one reused,
bounded buffer; it does not retain or queue frames. The runtime's normal eye
region is deliberately larger than the sampled full expression/gaze envelope.

The default profile is the verified Luckfox Pico Ultra W wiring:

| Signal | Linux endpoint |
| --- | --- |
| SPI | `/dev/spidev0.0`, mode 0, initially 16 MHz |
| DC | `/dev/gpiochip1`, line 24 (`GPIO1_D0`) |
| reset | `/dev/gpiochip1`, line 25 (`GPIO1_D1`) |
| backlight | `/dev/gpiochip1`, line 26 (`GPIO1_D2`) |

The target image already contains Python 3.11, `spidev`, and
`python-periphery`. Host tests use injected fakes and need none of them:

```sh
python3 -m unittest discover -s display/backends/tests -v
```

The conservative clock is a first-light baseline, not the product setting.
The exact harness has now completed the 24/32/40 MHz sweep with concurrent
camera/network load. The repository default remains the conservative 16 MHz
baseline; the deployed face runtime selects the measured 40 MHz profile.
