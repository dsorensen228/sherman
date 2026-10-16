# Face Display Selection

## Decision summary

Use the **Waveshare 1.9inch LCD Module, SKU 23822** as Sherman's Phase 1 face-display candidate. Mount it in landscape orientation so the module is `51.2 mm wide × 27.3 mm high`; the active area is `42.72 mm wide × 22.70 mm high`. It is a `170 × 320` IPS panel using the ST7789V2 controller over 4-wire SPI.

This replaces the earlier square-display concept. It is not yet a frozen production part: it must pass electrical, Linux, optical, performance, and enclosure qualification. Order two identical modules so one can remain on a bench rig while the other is integrated into the face cassette.

Primary sources:

- [Waveshare product page](https://www.waveshare.com/1.9inch-lcd-module.htm)
- [Waveshare wiki and examples](https://www.waveshare.com/wiki/1.9inch_LCD_Module)
- [Luckfox Pico Ultra device-tree guide](https://wiki.luckfox.com/Luckfox-Pico-Ultra/Device-Tree/)
- [Luckfox Pico Ultra SPI guide](https://wiki.luckfox.com/Luckfox-Pico-Ultra/SPI-Communication/)

## Why this shape fits Sherman

Sherman's face must show two eyes side-by-side, short gaze shifts, eyelid shapes, and authoritative status cues. A landscape active area provides the right semantic canvas without making the display define the entire enclosure.

| Property | Waveshare 1.9-inch | Sherman consequence |
| --- | ---: | --- |
| Module outline | `51.2 × 27.3 mm` | Leaves roughly 7–14 mm total horizontal margin in a 58–65 mm face before tolerance details |
| Active area | `42.72 × 22.70 mm` | Two eyes can occupy about 16–18 mm each with center gap and edge breathing room |
| Resolution | `320 × 170` landscape | `1.88:1` aspect ratio suits a binocular face and procedural antialiased eyes |
| Interface | 4-wire SPI | Avoids the 4-inch RGB panel and its large mechanical/electrical footprint |
| Controller | ST7789V2 | Common command set with vendor example code; still requires a Luckfox-specific backend |
| Supply | 3.3 V or 5 V module input | Bench first at documented levels; verify IO translation and current |
| Included harness | MX1.25 8-pin cable | Useful for bring-up; replace or restrain it in the mobile harness after mating-cycle review |

The display should sit behind a separate visible-light face window. Camera and 940 nm ToF apertures remain separately baffled; do not put an unqualified smoked plastic sheet over all three optical paths.

## Compared candidates

| Candidate | Module / active area | Strength | Reason not primary |
| --- | --- | --- | --- |
| **Waveshare 1.9-inch SKU 23822** | `51.2 × 27.3` / `42.72 × 22.70 mm` | Best balance of landscape proportion, legibility, enclosure margin, price, and simple SPI | Primary candidate; target driver work remains |
| Waveshare 1.47-inch LCD Module | `38.5 × 22.0` / `32.35 × 17.39 mm` | More internal margin and lower transfer cost | Eyes are small at seated viewing distance; retain only as an envelope fallback |
| Adafruit 1.9-inch TFT, product 5394 | `57.2 × 36.6 × 5.2 mm`; screen about `46 × 25 mm` | Strong documentation, level shifting, EYESPI, microSD | Carrier consumes nearly all of a 60 mm face and adds unused board area; bench fallback only |
| Luckfox official 4-inch RGB panels | roughly 84 mm class outline | Direct vendor display path and high bandwidth | Mechanically incompatible with the target product |
| 1.3–1.54-inch square panels | roughly square | Compact, common ST7789 family | Wrong face proportion; wastes vertical pixels and constrains two-eye spacing |
| Small monochrome OLED | landscape options exist | Black level and simple graphics | Lower expression/color flexibility plus burn-in/lifetime qualification |

Do not buy the Adafruit fallback unless the Waveshare module fails a defined gate. Buying a second primary unit is more useful than splitting effort across two mechanically different carriers before a failure exists.

## Target electrical path

### Initial backend

Use the Luckfox `spidev` path first:

1. Disable the default RGB display reservation with the supported configuration flow.
2. Enable one complete SPI pin group in the exact board device tree; do not mix pins from alternate SPI groups.
3. Enable `spidev@0`, keep any competing `fbtft@0` node disabled, and expose `/dev/spidev0.0`.
4. Drive `CS`, `DC`, `RST`, and `BL` with documented GPIO/PWM outputs whose boot state leaves backlight off and display reset asserted or benign.
5. Port only the ST7789V2 initialization and window-write behavior needed by Sherman's backend; preserve the vendor sample as a reference, not as production architecture.
6. Render to RGB565 and write full or dirty rectangles from a bounded worker that always drops stale frames rather than queuing them.

Luckfox documents a device-tree SPI example with a 50 MHz maximum. This is permission to test up to the qualified electrical limit, not proof that the panel, harness, userspace loop, or chosen pin group is reliable at 50 MHz.

### Transfer budget

A complete RGB565 frame is:

`320 × 170 × 2 = 108,800 bytes`

Ignoring protocol and software overhead, full-frame transfer ceilings are about:

| SPI clock | Ideal full frames/s |
| ---: | ---: |
| 16 MHz | 18.4 |
| 24 MHz | 27.6 |
| 32 MHz | 36.8 |
| 40 MHz | 46.0 |
| 50 MHz | 57.4 |

The product does not need a desktop UI at 60 fps. Initial acceptance is stable `≥30 visible fps` for the standard eye workload, with semantic-event-to-visible latency `≤50 ms` as required by `GOALS.md`, no persistent tearing, and reviewed CPU/RSS/power. Dirty rectangles may improve typical performance, but a full-screen fault overlay must remain prompt. This implies a qualified SPI clock above the ideal 24 MHz full-frame ceiling or reliable dirty-region updates.

### Later backend options

After the userspace path is measured, evaluate a framebuffer/DRM/MIPI-DBI-style backend only if it materially improves CPU, latency, boot, or integration. Do not assume a current upstream Linux driver exists in the Luckfox vendor `5.10` kernel image. Any kernel port must be maintained as a pinned patch with recovery coverage.

## Wiring ledger fields

The exact pins remain intentionally unassigned until the delivered Ultra W revision and selected camera/device tree are inspected. The hardware profile must freeze:

| Display signal | Direction | Reset/boot requirement | Qualification |
| --- | --- | --- | --- |
| `VCC` | power | off or valid rail only | current, ripple, level-translator behavior |
| `GND` | power return | common reference | motor-noise correlation |
| `DIN/MOSI` | Luckfox → display | benign level | eye pattern at increasing SPI rates |
| `CLK` | Luckfox → display | no uncontrolled toggling | edge integrity and transfer errors |
| `CS` | Luckfox → display | inactive | wrong-device/noise immunity |
| `DC` | Luckfox → display | defined | command/data correctness |
| `RST` | Luckfox → display | asserted or defined | 100 cold boots and runtime reset |
| `BL` | Luckfox → display | off until renderer ready | PWM range, flicker, shutdown and current |

## Qualification sequence

1. Photograph, weigh, and caliper both received modules; record markings and cable pin order.
2. Verify power and logic levels from the exact schematic/module documentation before connection.
3. Run the vendor color bars from a known host or MCU to eliminate panel faults.
4. Bring up Luckfox SPI at a conservative clock; capture reset, command, and first-frame timing.
5. Sweep SPI rate, cable routing, brightness, and CPU load while counting corruptions/timeouts.
6. Run Sherman's canonical eyes, gaze sweep, blink, full-screen fault, privacy, low-battery, and shutdown frames.
7. Measure visible latency with GPIO marker plus high-speed video or photodiode where practical.
8. Stress display concurrently with camera, front ToF, Wi-Fi, storage writes, and later motor transients.
9. Validate the face window, viewing cone, daylight/night brightness, reflections, light leakage, and reassembly alignment.
10. Run an 8-hour soak for G1 and a 24-hour animation/endurance run before hardware freeze.

## Pass, fallback, and stop rules

Pass only when the exact board/display/harness/device-tree/backend combination meets the Phase 1 resource and visible-performance budgets. If throughput is marginal, try measured dirty-region writes and a maintained kernel backend before changing display hardware. If the Waveshare carrier is mechanically too wide, test the 1.47-inch landscape variant with the same expression-recognition protocol. If no compact landscape display meets the visible, resource, and reliability gates, enlarge the face or change face technology explicitly; do not silently return to the 4-inch kit.
