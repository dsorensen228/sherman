# Hardware Sources and Verified Assumptions

Checked 2026-08-07. Prefer these primary vendor sources over reseller summaries. Re-check before procurement because revisions and availability change.

## Luckfox Pico Ultra W

- [Official product/wiki page](https://wiki.luckfox.com/Luckfox-Pico-Ultra/): RV1106 family, Cortex-A7 at 1.2 GHz, integrated ISP/NPU, memory/Wi-Fi variants, MIPI CSI, RGB666, USB, GPIO, Ethernet, and eMMC summary.
- [Device-tree guide](https://wiki.luckfox.com/Luckfox-Pico-Ultra/Device-Tree/): model-specific DTS selection and vendor SDK location.
- [USB guide](https://wiki.luckfox.com/Luckfox-Pico-Ultra/USB/): USB-A/USB-C switching behavior; they are not simultaneously usable for data in the described configuration.
- [eMMC flashing guide](https://wiki.luckfox.com/Luckfox-Pico-RV1106/Getting-Started/eMMC-Models/): recovery/boot-button workflow for Ultra models.
- [RGB screen guide](https://wiki.luckfox.com/Luckfox-Pico-Ultra/RGB-Screen/): documented 480×480 and 720×720 RGB displays.
- [Official 4-inch display listing](https://www.luckfox.com/LF40-720720-ARK): roughly 84 mm outline, confirming the directly supported panel is too large for the Sherman target.
- [GPIO guide](https://wiki.luckfox.com/Luckfox-Pico-Ultra/GPIO/): default RGB reservations and configuration workflow.
- [SPI guide](https://wiki.luckfox.com/Luckfox-Pico-Ultra/SPI-Communication/): target SPI userspace bring-up.
- [SC3336 3MP Camera (B)](https://www.luckfox.com/EN-SC3336-3MP-Camera-B): SKU 25553, included FFC, 2304×1296, manual focus and lens/FOV details.

Claims not yet closed: exact Ultra W PCB outline/mounting/keep-outs; exact delivered memory/NPU variant; available PWM/timer/interrupt pins under the chosen camera/display device tree; sustained thermal behavior; and the Waveshare target backend's measured performance.

## Face display

- [Waveshare 1.9inch LCD Module](https://www.waveshare.com/1.9inch-lcd-module.htm): SKU 23822; `170×320`, IPS, ST7789V2, 4-wire SPI, `51.2×27.3 mm` module, `42.72×22.70 mm` active area, 3.3/5 V and included cable.
- [Waveshare wiki/examples](https://www.waveshare.com/wiki/1.9inch_LCD_Module): controller examples and reference initialization path.
- [Adafruit 1.9-inch ST7789 display](https://www.adafruit.com/product/5394): documented bench fallback; `57.2×36.6×5.2 mm` carrier is too large for the preferred face.

Claims not yet closed: exact delivered panel revision/markings, maximum reliable SPI clock on Sherman harness, reset/backlight boot behavior, visible frame rate/latency, power, viewing/optical window, and long-run retention/reliability.

## Ranging

- [ST VL53L5CX datasheet](https://www.st.com/resource/en/datasheet/vl53l5cx.pdf): multizone 4×4/8×8 ranging, wide field of illumination, I2C control, supply/interface conditions, performance limits, optical/mechanical handling.
- [Pololu VL53L5CX carrier #3417](https://www.pololu.com/product/3417): exact front-range breakout dimensions, levels, current and orderable status.
- [ST VL53L4CD product page](https://www.st.com/en/imaging-and-photonics-solutions/vl53l4cd.html): short-range sensor, 1 mm linear range, up to 100 Hz, 18° FOV; robotics cliff detection use case.
- [Pololu VL53L4CD carrier #3692](https://www.pololu.com/product/3692): exact cliff candidate with regulator/level shifting and orderable module data.

Claims not yet closed: chosen breakout behavior and logic levels; cover-window crosstalk; real desk targets; Linux driver memory/CPU/rate; suitability as a front obstacle/map sensor.

The VL53L4CD cliff candidate still requires a two-sensor address/XSHUT plan, controller port of the official API, final height/angle/FOV, dark/glossy/transparent/ambient-light surface evidence, contamination testing, and 500-approach acceptance. Its short-range specification improves geometry but does not itself prove edge safety.

## Motor driver

- [Texas Instruments DRV8833 datasheet](https://www.ti.com/lit/ds/symlink/drv8833.pdf): dual DC-motor bridge, voltage/current/thermal characteristics, sleep/fault behavior, bulk capacitance and layout guidance.

Claims not yet closed: exact breakout layout/components; compatibility with selected motor stall current, motor voltage, logic level, braking, thermal envelope, and power architecture.

## Motion, controller, and power candidates

- [Pololu 298:1 MP encoder gearmotor #5146](https://www.pololu.com/product/5146): exact ratio, 12 CPR input-shaft encoder, no-load/stall data and connector pinout.
- [Pololu 32×7 mm wheel pair #1087](https://www.pololu.com/product/1087), [bracket pair #989](https://www.pololu.com/product/989), and [encoder cable #4762](https://www.pololu.com/product/4762): exact drivetrain accessories.
- [Raspberry Pi Pico 2 product brief](https://datasheets.raspberrypi.com/pico/pico-2-product-brief.pdf): dimensions, RP2350 resources, watchdog, interfaces and supported supply.
- [Pololu LSM6DSO carrier #2798](https://www.pololu.com/product/2798): exact IMU breakout.
- [Pololu U3V70F5 #2891](https://www.pololu.com/product/2891): exact 5 V boost candidate, efficiency/current/thermal constraints and true shutdown.
- [Pololu Mini Pushbutton Power Switch LV #2808](https://www.pololu.com/product/2808): 1S-compatible soft power switch used for both system switching and the automatic motor-rail gate; vendor warns it is not an emergency disconnect.
- [TI SN74HC08](https://www.ti.com/product/SN74HC08/part-details/SN74HC08N): 2–6 V quad two-input AND gate in a hand-solderable PDIP-14 package for the automatic dual-inhibit interlock.
- [Adafruit protected 1200 mAh LiPo #258](https://www.adafruit.com/product/258), [BQ24074 power-path charger #4755](https://www.adafruit.com/product/4755), [#4755 pinouts](https://learn.adafruit.com/adafruit-bq24074-universal-usb-dc-solar-charger-breakout/pinouts), and [MAX17048 gauge #5580](https://www.adafruit.com/product/5580): power-gated prototype candidates. The #4755 is the received V1 exterior cable/load-sharing candidate for compute only; its raw `VBUS` and active-low open-drain `PGOOD` feed the automatic charge interlock. #4410 is not installed in Sherman.

Claims not yet closed: actual responsive-compute current against the #4755's
1.5 A output limit; motor speed/torque/noise at 1S voltage; #2808 motor-gate
current/thermal and override behavior; interlock fault coverage; boost
efficiency/ripple/heat; battery connector/protection transient capability;
runtime/reserve; live-load charge temperature/termination; enclosure fit and
swelling allowance. A failed #4755 load test triggers power-path replacement, not
a manual charging step.

## Source hygiene

When adding a BOM item, link the manufacturer datasheet and exact module documentation. Archive the part/revision identifier and critical parameters in the receiving record. Forums and examples may guide experiments but cannot close an electrical, thermal, optical, or safety requirement.
