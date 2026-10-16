# Candidate Bill of Materials and Qualification Plan

## Status vocabulary

- **Committed:** architectural constraint accepted by the owner.
- **Candidate:** plausible but not yet measured.
- **Bench-qualified:** passes isolated functional and electrical tests.
- **Integration-qualified:** passes in the current chassis/system.
- **Frozen:** exact orderable item and allowed substitutes are released.

## Compute and development

| Item | Qty | Status | Required evidence |
| --- | ---: | --- | --- |
| Luckfox Pico Ultra W, 256 MB / 1 TOPS wireless option | 1 | Ordered 2026-08-07; receiving pending | Exact delivered revision; board dimensions/mass; recovery; Wi-Fi; camera; I2C/SPI/UART; sustained load; thermal/power |
| Debug/flash USB cable | 2 | Candidate | reliable flashing; known data capability; strain relief |
| Ethernet patch cable | 1 | Candidate | rescue/debug workflow; not carried in robot |
| Known-good 5 V ≥3 A USB supply + inexpensive inline USB meter | 1 each if not owned | DIY baseline | coarse current comparison and reliable stationary power; borrow lab equipment only for a specific unresolved fault |

Vendor documentation indicates an RV1106-based 1.2 GHz Cortex-A7 platform with integrated ISP/NPU, MIPI CSI, GPIO/I2C/SPI/UART, eMMC, Ethernet, and Wi-Fi/Bluetooth on W variants. Record the delivered board rather than assuming every reseller listing matches.

## Face and expression

The primary Phase 1 candidate is the **Waveshare 1.9inch LCD Module, SKU 23822**: `320 × 170` landscape, IPS, ST7789V2, 4-wire SPI, `51.2 × 27.3 mm` module and `42.72 × 22.70 mm` active area. Order two identical modules. See `display-selection.md` and ADR 0003.

Luckfox’s directly documented RGB panels are 4 inches and mechanically incompatible with the target envelope. The compact display must therefore prove the whole Luckfox Linux path; controller family familiarity on other platforms is not qualification.

| Candidate | Status | Qualification |
| --- | --- | --- |
| Waveshare 1.9-inch SKU 23822, quantity 2 | Ordered 2026-08-07; receiving pending | cold boot, `spidev`/possible kernel backend, ≥30 visible fps eye workload, ≤50 ms semantic-to-visible latency, tearing, CPU/RSS, power, cable, optical/window, enclosure |
| Waveshare 1.47-inch landscape | Mechanical fallback only | same expression legibility and target backend suite; use only if 51.2 mm carrier fails fit |
| Adafruit 1.9-inch product 5394 | Open-bench fallback only | carrier is too large for preferred face; buy only if primary path fails |
| Small OLED | Technology fallback | burn-in risk, brightness, lifetime, refresh artifacts, power, reduced expression grammar |
| Luckfox 4-inch RGB | Rejected for v1 | exceeds target envelope |

Display qualification score: integration risk 30%, envelope 20%, legibility 15%, latency 15%, power 10%, supply 5%, cost 5%. Do not split initial effort across mechanically different modules without a recorded primary-candidate failure.

## Vision and ranging

| Item | Qty | Status | Qualification |
| --- | ---: | --- | --- |
| Luckfox SC3336 3MP Camera, expected Camera (B) SKU 25553 | 1 | Ordered 2026-08-07; exact item receiving confirmation pending | manual focus, frame formats, ISP, latency, memory, low light, exact FFC/orientation |
| Pololu VL53L5CX carrier #3417 | 1 | Selected candidate | 4×4/8×8 modes, I2C throughput, FOV/cover window, dark/glossy targets, power, heat, Linux driver/API |
| Pololu VL53L4CD carriers #3692 | 2 + 1 spare | Selected cliff candidate | 1 mm close-range behavior, ≤100 Hz, surface matrix, height/angle, ambient IR, edge speed, identical-address XSHUT sequence |
| Pololu LSM6DSO carrier #2798 | 1 | Selected candidate | gyro bias/stability, timestamping, vibration, bus rate, interrupt support |
| Integrated 12 CPR motor encoders | 2 + motor spare | Selected candidate | roughly 3575 counts/output revolution by ratio calculation; missed counts, noise, controller capture |

The VL53L5CX is an 8×8 multizone ToF sensor with a documented wide field of illumination and I2C control. Using a breakout avoids optical-LGA assembly during prototype phases but its regulator, level shifting, and physical size must be included.

## Motion and safety control

| Item | Qty | Status | Qualification |
| --- | ---: | --- | --- |
| Pololu 298:1 MP 6V encoder gearmotor #5146 | 2 + 1 spare | Selected candidate | 1S speed/torque, stall/current curve, minimum controllable speed, backlash, noise, encoder quality, temperature, mass |
| Pololu 32×7 mm black wheel pair #1087 | 1 pair + 1 spare pair | Selected candidate | traction, concentricity, fit, contamination, desk marking |
| Low-friction skid or micro caster | 1 | Candidate | yaw consistency, height tolerance, cable/edge snagging |
| Pololu DRV8833 carrier #2130 | 1 + 1 spare | Selected candidate | motor-voltage/current compatibility, optional current limit, thermal rise, braking mode, fault behavior, logic level |
| Raspberry Pi Pico 2, non-wireless | 1 + 1 spare/HIL peer | Selected candidate | watchdog, PWM, encoder inputs, I2C sensors, UART link, boot safety, physical fit |
| Pololu Mini Pushbutton Power Switch LV #2808, automatic motor-rail gate role | 1 + 1 system-switch unit | Selected candidate | 1S current/thermal margin, `CTRL` truth table, boot/reset default-off, charge-present forced-off behavior, button unable to override an asserted inhibit |
| [`charging-interlock-rev-a`](../../electronics/pcb/charging-interlock-rev-a/README.md), populated with SN74HC08N + 2N3904BU | 3 bare ordered; populate 1 installed + 1 complete tested spare | Ordered 2026-09-01; receiving and qualification pending | 38.10 mm × 24.13 mm; raw-input and `PGOOD` sensing, dual independent inhibit outputs, open/short/reset/input-bounce fault matrix, truth-table capture |

The DRV8833 can drive two DC motors and provides sleep, overcurrent, and thermal protection, but module implementations vary. Qualify the exact board, bulk capacitance, layout, and motor stall current.

## Power

| Item | Qty | Status | Qualification |
| --- | ---: | --- | --- |
| Adafruit protected 1S 1200 mAh LiPo #258 | 1 + 1 spare | Power/M0-gated candidate | capacity at load, 2 A cable constraint, protection thresholds, swelling allowance, lead/connector, temperature |
| Pololu U3V70F5 5 V boost #2891 | 1 + 1 spare | Power-gated candidate | efficiency map, transient response, ripple affecting camera/ToF, thermal, undervoltage behavior |
| Adafruit BQ24074 Universal USB/DC/Solar charger #4755 | 1 received + 2 ordered | V1 compute power-path candidate; incoming units await receiving inspection | Exterior USB-C, separate `LOAD` output/load sharing, ≤1.5 A responsive-compute load, selected charge current, thermal/termination and unplug/replug behavior |
| GODIYMODULES I2Chub I2Cadapter Board (B0DGQBFSKL) | 1 | Received and installed for IMU/cliff harness | Exact delivered dimensions, connector population, 3.3 V compatibility, aggregate pull-up resistance, and shared-bus integrity; this is a passive hub, not an address multiplexer |
| Adafruit MAX17048 #5580 | 1 | Candidate | usable state-of-charge accuracy under pulsed motor load |
| Fuse/PTC and reverse-polarity protection | as designed | Candidate | separate compute/motor branch fault tests and voltage drop |

The #4755 is already received, but remains a candidate until responsive-compute
load sharing is qualified. Its `OUT` rail does not feed the motors: the fused cell
also feeds a separate automatic motor gate. If the compute workload exceeds the
#4755 limit, replace the charger/power-path hardware; do not add a user charging
step or require shutdown. The named 1200 mAh cell is an explicit test candidate,
not a production freeze, and its `34 × 62 × 5 mm` body plus service/swelling
allowance may force the comfortable chassis envelope.

## Mechanical

- Printed chassis iterations: cheap material for fit; tougher heat-resistant material only after geometry stabilizes.
- Heat-set inserts or captured nuts where repeated service is required.
- M2/M1.6 hardware assortment, isolators, foam, cable retention, black optical baffles/windows.
- A transparent test shell or open rig for early sensor and thermal visibility.
- Fast-follow rear-entry dock Sherman backs into: at least four keyed contacts for first-mate/last-break ground,
  dock-switched 5 V, current-limited pilot/identity, and open-drain release request;
  hard-gold-plated robot pads, a listed 5 V ≥3 A supply, and alignment fixture.
  Freeze the exact contact family only after repeated mate/unmate, bridge, short,
  release, and autonomous-departure tests.

## Purchasing gates

1. **Phase 1 order:** compute board if not owned, two identical Waveshare 1.9-inch displays, supported camera, measurement tools.
2. **Phase 2 order:** ToF breakout, calibration targets/fixture, optional second camera lens/FOV candidate.
3. **Phase 3A order:** motor/encoder pairs, driver, controller modules, IMU, cliff candidates, bench power parts.
4. **Phase 3B order:** automatic interlock PCB and two-board population kit ordered 2026-09-01; any replacement battery/charger/boost still follows the measured load model, and wheels still require motor-shaft/layout confirmation.
5. **Freeze:** exact BOM after chassis integration, endurance, and fault tests; list allowed substitutions and their requalification subset.

The orderable list, current quantities/prices, ordinary electronics, mechanical supplies, instruments, and receiving checklist live in `shopping-list.md` and `shopping-list.csv`.
