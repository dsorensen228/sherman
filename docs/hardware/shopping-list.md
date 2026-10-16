# Complete DIY Prototype Shopping List

Checked **2026-09-01**. Prices are approximate USD list prices before tax and shipping unless an order record says otherwise. This is a complete development/prototype procurement plan, not a frozen production BOM.

## How to use this list

Purchase by gate, not all at once:

- **ORDERED:** purchased by the owner; wait for receiving inspection before treating it as available or qualified.
- **NOW:** enables the Luckfox + real-eyes bring-up and retires the display risk.
- **G1:** purchase after the Phase 1 brain/display gate or when Phase 2 work begins.
- **G2 / P3A:** purchase after stationary perception is stable, for wheels-up and restrained mobility.
- **P3B HOLD:** exact candidates are named, but do not purchase until the measured power and M0 layout gates pass.
- **IF ABSENT:** workshop capability; buy only if an equivalent is not already available.
- **OPTIONAL:** fallback/spare that is not required for the first coherent build.

Quantities include deliberate spares for fragile, safety-critical, or parallel bench/chassis work. Every received item gets a hardware ID, photo, measured dimensions/mass, revision/markings, and receiving-test record.

`shopping-list.csv` mirrors the exact module/electromechanical table for sorting and price arithmetic. The Markdown document remains authoritative for supplies, tools, fixtures, gates, and safety notes.

## Exact modules and electromechanical parts

| Gate | Subsystem | Exact part | SKU / item | Qty | Unit | Extended | Why / constraint |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| ORDERED 2026-08-07 | Compute | [Luckfox Pico Ultra W](https://www.luckfox.com/EN-Luckfox-Pico-Ultra?ci=510), 256 MB / 1 TOPS wireless variant, no 4-inch LCD or PoE kit | Ultra W option | 1 | $50.99 | $50.99 | Permanent Linux/vision board; record delivered variant and revision |
| ORDERED 2026-08-07 | Face | [Waveshare 1.9inch LCD Module](https://www.waveshare.com/1.9inch-lcd-module.htm), 170×320 IPS ST7789V2 | SKU 23822 | 2 | $11.99 | $23.98 | Primary landscape display plus identical bench spare; included MX1.25 cable |
| ORDERED 2026-08-07 | Camera | [Luckfox SC3336 3MP Camera (B)](https://www.luckfox.com/EN-SC3336-3MP-Camera-B), with FFC | SKU 25553 | 1 | $8.99 | $8.99 | Exact vendor-supported Ultra camera; 84° H / 44° V FOV, manual focus |
| ORDERED 2026-08-14 | Front ranging | [Pololu VL53L5CX carrier](https://www.pololu.com/product/3417) | #3417 | 1 | $19.95 | $19.95 | 8×8 multizone front obstacle/range candidate; must pass optical-window and target matrix |
| ORDERED 2026-08-14 | Safety controller | [Raspberry Pi Pico 2](https://www.raspberrypi.com/products/raspberry-pi-pico-2/), non-wireless, no headers | Pico 2 | 1 | $5.00 | $5.00 | Low-profile robot controller; RP2350, watchdog, PWM, UART/I2C/SPI |
| ORDERED 2026-08-14 | Safety controller | [Raspberry Pi Pico 2 with headers](https://www.raspberrypi.com/products/raspberry-pi-pico-2/), non-wireless | Pico 2 with headers | 1 | $6.00 | $6.00 | Breadboard/HIL peer with pre-soldered headers |
| RECEIVED / WIRED 2026-08-30 | Cliff sensing | [Pololu VL53L4CD carrier](https://www.pololu.com/product/3692) | #3692 | 3 | $13.95 | $41.85 | Two units wired through the passive hub plus one spare; XSHUT/address startup and full surface matrix remain mandatory |
| RECEIVED / WIRED 2026-08-30 | IMU | [Pololu LSM6DSO carrier](https://www.pololu.com/product/2798) | #2798 | 1 | $19.95 | $19.95 | Wired through the passive hub; 6-axis IMU with regulator/level shifting; mount orientation is controlled |
| ORDERED 2026-08-14 | Motors | [Pololu 298:1 Micro Metal Gearmotor MP 6V with 12 CPR encoder, back connector](https://www.pololu.com/product/5146) | #5146 | 3 | $29.95 | $89.85 | Matched pair plus spare; gentle 1S-speed candidate; 0.67 A theoretical stall each |
| ORDERED 2026-08-14 | Motor harness | [Pololu 6-pin encoder cable, 12 cm, female to unterminated](https://www.pololu.com/product/4762) | #4762 | 3 | $2.10 | $6.30 | One per motor; cut only after routing is frozen |
| ORDERED 2026-08-14 | Wheels | [Pololu black wheel pair, 32×7 mm](https://www.pololu.com/product/1087) | #1087 | 2 pairs | $4.45 | $8.90 | One pair plus spare; 3 mm D-shaft, silicone tires |
| ORDERED 2026-08-14 | Motor mounts | [Pololu black micro metal gearmotor bracket pair](https://www.pololu.com/product/989) | #989 | 2 pairs | $2.95 | $5.90 | One installed pair plus spare; compatible with 32 mm wheels |
| ORDERED 2026-08-14 | Motor driver | [Pololu DRV8833 dual carrier](https://www.pololu.com/product/2130) | #2130 | 2 | $10.95 | $21.90 | One installed plus one bench spare; 2.7–10.8 V, 1.2 A/channel continuous |
| ORDERED 2026-08-14 | 5 V rail | [Pololu U3V70F5 5 V step-up regulator](https://www.pololu.com/product/2891) | #2891 | 2 | $22.95 | $45.90 | Candidate plus spare; large transient margin, true shutdown; measure efficiency/heat/ripple |
| ORDERED 2026-08-14 | Power gating | [Pololu Mini Pushbutton Power Switch LV](https://www.pololu.com/product/2808) | #2808 | 2 | $4.95 | $9.90 | One system switch and one automatic motor-rail gate; neither is an emergency disconnect |
| ORDERED 2026-08-14 | Battery | [Adafruit protected 3.7 V 1200 mAh LiPo](https://www.adafruit.com/product/258) | Product 258 | 2 | $9.95 | $19.90 | Envelope/runtime candidate plus spare; 34×62×5 mm, 23 g, JST-PH lead rated 2 A |
| RECEIVED 2026-08-30 + ORDERED 2026-09-01 | Power-path charger | [Adafruit Universal USB/DC/Solar LiPo charger](https://www.adafruit.com/product/4755) | Product 4755 / BQ24074 | 1 received + 2 incoming | $14.95 ea. | $44.85 | Exterior USB-C and load sharing for responsive compute; retain one qualified spare and reserve the additional incoming board for bench/fault work |
| RECEIVED / INSTALLED 2026-08-30 | I2C distribution | [GODIYMODULES I2Chub I2Cadapter](https://www.amazon.com/dp/B0DGQBFSKL) | B0DGQBFSKL | 1 | $11.99 | $11.99 | Passive 10-port distribution for the wired IMU and cliff sensors; not an address multiplexer |
| FAST FOLLOW — DOCK | Dock supply | Regulated 5 V DC supply, ≥3 A, UL/ETL-listed | exact SKU pending cable/connector layout | 1 | $15–30 | $15–30 | Dock-switched feed to the same charger input; defaults off until pilot proof |
| FAST FOLLOW — DOCK | Dock contacts | Keyed recessed spring contacts and hard-gold-plated robot pads | exact family after fit test | ≥4 contacts + spare | $15–35 | $15–35 | Ground, switched 5 V, current-limited pilot/identity, and open-drain release request; never expose battery terminals |
| ORDERED 2026-08-14 | Fuel gauge | [Adafruit MAX17048 battery monitor](https://www.adafruit.com/product/5580) | Product 5580 | 1 | $5.95 | $5.95 | I2C state-of-charge candidate; validate under motor pulses |

**Exact-module subtotal: approximately $454.00.** The subtotal includes the
received and incoming #4755 boards but excludes the separately ordered
charge-interlock PCB/passive kit, tax, shipping, tools, cable stock, and chassis
materials.

### Explicitly do not buy

- Do not buy a Luckfox 4-inch LCD kit; it defeats the enclosure and face proportions.
- Do not buy the Adafruit 1.9-inch TFT carrier unless the Waveshare path fails; its `57.2 × 36.6 mm` PCB is a useful open-bench fallback but a poor face cassette.
- The #4410 already ordered is retained only for standalone cell bench work; it must not be installed in Sherman. The received #4755 is the V1 cable-charge candidate. Dock supply and contact hardware are the fast follow after its physical and electrical qualification.
- Do not substitute random marketplace LiPo cells, camera modules, motor encoders, or ToF boards. Connector polarity, protection, optical design, and board layouts vary.

## Cables, connectors, passives, and bench electronics

These are complete category requirements. Exact production connectors and passive values are frozen only with the schematic and harness; quantities below cover two bench rigs and several harness revisions.

| Gate | Item / specification | Qty | Budget | Use and acceptance notes |
| --- | --- | ---: | ---: | --- |
| NOW | USB-C to USB-A data cable, known-good, 1 m or shorter | 2 | $15–25 | Flash/recovery plus spare; label data-capable |
| NOW | CAT5e/CAT6 Ethernet patch cable, 1–2 m | 1 | $5–10 | Rescue/debug; not carried in robot |
| NOW | Regulated 5 V USB supply rated at least 3 A | 1 | $10–20 | Stationary target bring-up; current rating is not evidence of board consumption |
| NOW | Solderless breadboards, full-size and mini | 1 each | $12–20 | Display/controller adapter work only; no mobile motor current through weak contacts |
| NOW | Dupont jumper kit, male/male, male/female, female/female | 1 kit each | $15–25 | Temporary low-current signals; replace in mobile build |
| NOW | 0.1-inch breakaway male and female header strips | 2×40 each | $6–12 | Populate only where needed; keep mobile stack height low |
| NOW | Fine hook-up wire, 26–28 AWG stranded, at least 6 colors | 1 assortment | $15–25 | Logic and sensors; document color map |
| G2 / P3A | Silicone power wire, 22 AWG red/black | 2 m each | $10–18 | Battery, regulator, driver, motors; verify voltage drop and flex |
| G2 / P3A | JST-PH 2-pin extension/pigtail pairs with verified Adafruit polarity | 4 pairs | $8–15 | Battery/charger/gauge bench interconnect; continuity-check every lead |
| G2 / P3A | JST-XH or equivalent keyed 2–6 pin connector assortment rated ≥3 A on power contacts | 1 kit | $15–30 | Serviceable prototype harness; freeze exact family after crimp/fit review |
| G2 / P3A | Matching ratcheting crimp tool for chosen connector family | 1 | $25–60 | Pull-test sample crimps before mobile use |
| G2 / P3A | Heat-shrink assortment, 1.5–6 mm | 1 kit | $8–15 | Insulation/strain relief; no heat on LiPo pouch |
| G2 / P3A | Polyimide tape, quality electrical tape, adhesive cable anchors, small zip ties | 1 each | $15–25 | Harness retention and temporary insulation |
| G2 / P3A | Perfboard/protoboard with plated holes | 1–3 | $4–15 | HIL and M1 adapters only; not used for the mobile charge interlock |
| ORDERED 2026-09-01 | [`charging-interlock-rev-a`](../../electronics/pcb/charging-interlock-rev-a/README.md) bare PCB from OSH Park | 3 bare boards | $7.10 standard-service quote; paid service/total on receipt | Populate and qualify two; retain the third bare as a fabrication spare |
| ORDERED 2026-09-01 | TI `SN74HC08N` PDIP-14, Mouser `595-SN74HC08N` | 2 | $1.58 | U1, one per populated interlock PCB |
| ORDERED 2026-09-01 | TE `1-2199298-3` 14-pin DIP socket, Mouser `571-1-2199298-3` | 2 | $0.56 | One U1 socket per populated PCB; install the IC only after pre-power checks |
| ORDERED 2026-09-01 | onsemi `2N3904BU`, Mouser `512-2N3904BU` | 5 | $1.40 | Q1 ×2 plus handling and fault-injection spares; exact E-B-C pinout is controlled |
| ORDERED 2026-09-01 | KEMET `C315C104K5R5TA` 100 nF X7R, Mouser `80-C315C104K5R5TA` | 10 | $2.83 | C1 ×2 plus bypass spares |
| ORDERED 2026-09-01 | Yageo `MFR-25FRF52-4K7` 4.7 kΩ 1%, Mouser `603-MFR-25FRF52-4K7` | 10 | $0.42 | R7 ×2 plus spares; R7 is on the PCB, so do not add a second SLEEP pull-down at the driver |
| ORDERED 2026-09-01 | Yageo `MFR-25FRF52-10K` 10 kΩ 1%, Mouser `603-MFR-25FRF5210K` | 10 | $0.42 | R1/R4/R5/R6 ×2 plus two interlock spares |
| ORDERED 2026-09-01 | Yageo `MFR-25FRF52-47K` 47 kΩ 1%, Mouser `603-MFR-25FRF52-47K` | 10 | $0.42 | R2 ×2 plus spares |
| ORDERED 2026-09-01 | Yageo `MFR-25FBF52-100K` 100 kΩ 1%, Mouser `603-MFR-25FBF52-100K` | 10 | $0.42 | R3 ×2 plus spares |
| ORDERED 2026-09-01 | Samtec `TSW-140-07-L-S` 2.54 mm male breakaway header, Mouser `200-TSW14007LS` | 1 × 40 positions | $2.99 | Cut 22 positions for J1/J2/J3 on two boards; 18 positions remain |
| G2 / P3A | 10 µF X7R ceramic capacitors, voltage rating ≥10 V | 10 | $5–10 | Local rail support |
| G2 / P3A | 100 µF low-ESR electrolytic capacitors, ≥10 V, 105°C | 10 | $5–10 | Driver/rail experiments; compare resets, errors and coarse voltage behavior with/without |
| G2 / P3A | Additional 1 kΩ and 10 kΩ 1% resistor stock | 25 each or existing stock | $3–8 | General prototypes plus four external 10 kΩ DRV8833 `AIN1/AIN2/BIN1/BIN2` pull-downs; these are separate from the two-board interlock population kit |
| G2 / P3A | Small Schottky diodes and unidirectional TVS candidates for 1S/5 V rails | 5 each | $8–20 | Select exact part from measured transients; not populated by habit |
| G2 / P3A | Resettable PTC/fuse candidates around 2–3 A plus holders/test leads | 5 | $8–15 | Freeze from worst-case current and trip testing |
| G2 / P3A | Momentary normally-open panel button for Pololu #2808 | 2 | $5–12 | User power control; the on-board switch remains accessible during bench work |
| G2 / P3A | Assorted test-point loops and 0.1-inch shunts | 1 kit | $8–15 | Rails, enable, UART, encoders, cliff XSHUT and faults |

Expected electronics/harness budget: **$185–360**, depending mostly on whether wire, crimping, and prototyping stock are already available.

## Mechanical and optical materials

| Gate | Item / specification | Qty | Budget | Notes |
| --- | --- | ---: | ---: | --- |
| NOW | Digital caliper, 0.01 mm display / verified against gauge | 1 if absent | $20–40 | Measure every received component; do not CAD from listings alone |
| G2 / P3A | PLA or PLA+ filament for M0/M1 fit iterations | 1 kg | $18–30 | Cheap iteration material; not final thermal evidence |
| G2 / P3A | PETG or tougher qualified filament for M2/M3 | 1 kg | $20–35 | Print coupons and heat/impact-test first |
| G2 / P3A | M2 screw assortment, 4–20 mm, washers, nyloc nuts | 1 kit | $15–25 | Stainless or black-oxide as appropriate; count fasteners |
| G2 / P3A | M2 heat-set inserts plus matching installation tip | 50 | $12–25 | Repeated service points; pull-test in chosen material |
| G2 / P3A | M2 nylon/metal standoff assortment | 1 kit | $10–20 | Board/tray spacing and electrical clearance |
| G2 / P3A | 0.5–2 mm closed-cell foam and thin silicone isolation sheet | 1 sheet each | $10–20 | Controlled anti-rattle/insulation; do not blanket hot components |
| G2 / P3A | 3M UHMW-PE tape or small PTFE glide stock | 1 roll/sheet | $8–15 | Low-profile third-contact skid; qualify yaw, wear, debris, and desk marking |
| G2 / P3A | Matte black flocking/paint or printed baffle stock | 1 | $8–20 | Separate display/camera/ToF optical paths; verify shedding/outgassing |
| G2 / P3A | Clear and smoke acrylic/polycarbonate coupons, 0.5–1.5 mm | 6 coupons | $15–30 | Display window experiments only; separately test 940 nm transmission/crosstalk |
| G2 / P3A | Thin removable black face gasket material | 1 sheet | $5–10 | Light sealing and display alignment |
| G2 / P3A | Removable threadlocker suitable for small fasteners | 1 | $6–10 | Keep away from plastics unless compatibility is known |
| G2 / P3A | Nonconductive safety tether and soft containment barrier | 1 each | $15–30 | Restrained and first free-motion tests |
| G2 / P3A | Sacrificial foam/plywood tabletop test deck larger than stopping envelope | 1 | $20–50 | Never run first cliff trials over an occupied/valuable surface |

Expected mechanical/optical material budget: **$187–360** if none is already owned. CAD must preserve `10–15%` unclaimed M1/M2 internal volume.

## DIY measurement and fabrication capability

This is a DIY project, not an electronics lab build-out. Use ordinary tools first and buy nothing expensive merely because it appears in a test plan. Borrow specialty instrumentation only when a specific unresolved failure justifies it.

| Capability | DIY expectation | Why / fallback |
| --- | --- | --- |
| Known-good 5 V USB supply | Use the ordinary ≥3 A supply already listed | Stationary Luckfox/display/camera bring-up |
| Digital multimeter | Basic reputable meter with fused current input; buy only if absent | Polarity, continuity, shorts, resistance and coarse current checks |
| Inline USB power meter | Inexpensive USB-C-capable unit; optional but useful | Coarse board/display/camera power comparison; not safety evidence for motor peaks |
| Logic analyzer | Optional $10–20-class 8-channel analyzer | Useful for SPI/I2C/UART debugging; software logs and loopback tests come first |
| Phone slow-motion video | Use an existing phone | Visible display latency, wheel speed markers and physical event timing |
| Oscilloscope | **Do not buy for Sherman** | Borrow or use a makerspace only if a concrete brownout, motor-noise or signal-integrity fault cannot be resolved otherwise |
| Current-limited bench supply | **Do not buy initially** | Use known USB power for Phase 1; borrow one or use a small fused/current-limited DIY test fixture only when motor bring-up begins |
| Soldering station | temperature controlled with fine and medium tips | modules, harness adapters, rework |
| Hot-air/rework capability | Not expected | Avoid board-level rework; replace a failed inexpensive module or borrow equipment |
| Wire stripper/crimper | correct dies for 22–28 AWG and connector terminals | repeatable harnesses |
| ESD mat and wrist strap | grounded common point | camera, display, SoC, sensor handling |
| Thermal measurement | fine thermocouples/data logger preferred; IR camera optional | compute, converter, driver, motors, battery-adjacent region |
| Scale | 0.1 g resolution, ≥500 g | mass/CoM budgets and receiving records |
| Printer or fabrication service | dimensionally repeatable FDM; 0.4 and optional 0.25 mm nozzle | chassis ladder and optical baffles |
| Battery-safe charging area | nonflammable surface/container, smoke detection, supervised operation | LiPo qualification; never charge unattended |

## Replacement-first fault policy

For inexpensive boards, sensors, displays, motor drivers and regulators:

1. Inspect the connector, cable orientation, polarity, visible damage and obvious shorts.
2. Confirm the documented supply and configuration, then run the smallest vendor/known-good example.
3. Swap the cable, then the spare module where available.
4. If the failure follows the module, label and quarantine it and order a replacement. Do not attempt component-level repair.
5. If a replacement fails identically, stop replacing parts and inspect the shared wiring, power, pinmux, software or mechanical interface.

Keep only the logs/photos needed to avoid repeating the same mistake. A replaced motor, driver, cliff sensor or controller repeats its receiving test and the affected safety checks before use.

## Calibration and test fixtures

- Printed display bezel/alignment card with active-area datum and 0.5 mm grid.
- Matte white, 18% gray, matte black, glossy black, clear acrylic/glass, wood, patterned laminate, and metal obstacle targets.
- Light sources covering dim room, office, window daylight, and strong oblique illumination; record lux and geometry.
- Camera checkerboard/ChArUco board on dimensionally stable backing.
- ToF target board at repeatable distances/angles and a removable face-window coupon holder.
- Motor clamp, wheel tachometer or high-frame-rate video marker, 0.1–1 Ω characterized current shunts, and guarded stall-pulse jig.
- Cliff fixture with adjustable sensor height/angle, exchangeable surface coupons, a real edge, catch net/foam, tether, and overhead video.
- M2 go/no-go coupons, insert pull-test coupons, wheel-alignment gauge, and chassis datum jig.
- Fire-safe battery inspection/storage container appropriate to local practice; do not use it to justify unattended charging.

Budget **$50–150** if fabricated mostly in-house.

## Phase order bundles

### Bundle A — ordered: real eyes and target baseline

The Luckfox Ultra W, two Waveshare 1.9-inch displays, and SC3336 camera were ordered on 2026-08-07. Exact-module subtotal at the recorded list prices is **$83.96**. Use ordinary known-good data/power cables already on hand where possible. On arrival, these parts are enough to perform the complete Phase 1 target/display baseline and an early camera/pinmux check; no additional hardware order is needed first.

### Bundle B — ordered: stationary perception

The VL53L5CX carrier was ordered on 2026-08-14. Construct calibration targets before qualification. Exact-module subtotal is **$19.95**.

### Bundle C — ordered: wheels-up and restrained motion

One headerless Pico 2 and one Pico 2 with pre-soldered headers, three cliff carriers, one IMU, three motors/cables, two wheel and bracket pairs, and two motor drivers were ordered on 2026-08-14. Exact-part subtotal is **$205.65**. Characterize on bench power before connecting a cell.

### Bundle D — ordered; qualification gates remain

The boost regulators, pushbutton power switches, battery candidates, #4410 charger, and gauge were ordered on 2026-08-14. The #4410 is superseded for Sherman by the #4755 power-path charger. The load/thermal and real M0 volume gates still control installation and use. The named battery's 2 A harness is a constraint, not a target; combined system peaks must stay below the qualified continuous/transient envelope or a different protected cell/connector architecture is required.

### Bundle E — ordered: compact automatic charge interlock

The OSH Park and Mouser orders were placed on 2026-09-01. The fabrication
order is for three bare revision-A PCBs. The population order contains enough
dedicated parts for two complete boards, including two IC sockets and deliberate
passive/transistor/header overage. Populate one installed assembly and one fully
bench-qualified spare; retain the third PCB bare. The Mouser order also includes
two additional Adafruit #4755 charger boards. Reconcile quantities, service
level, and final paid totals against the shipping confirmations when the
packages arrive; order numbers, addresses, and payment data are intentionally
not stored in this repository.

The 10 kΩ order reserves eight resistors for `R1/R4/R5/R6` on the two PCBs and
leaves two interlock spares. It does **not** supply all four external DRV8833
input pull-downs; take those from existing 10 kΩ stock or the separate general
stock line above. The PCB's `R7` is already the required 4.7 kΩ SLEEP-output
pull-down—do not install another at the driver.

## Battery and charging rule for prototype V1

V1 charging has one user action: plug a powered USB-C cable into Sherman's
exterior #4755 port. No shutdown, switch, disarm command, shell opening, or
battery handling is allowed. The #4755 `OUT` rail keeps the qualified compute and
logic workload responsive while its battery terminal charges the installed cell.
Motors use a separate fused-cell branch through the second #2808. A 3.3 V
SN74HC08N/2N3904 interlock uses both raw #4755 `VBUS` and active-low open-drain
`PGOOD` evidence to force that gate off and DRV8833 `nSLEEP` low in hardware.

The #4755 is a candidate, not a reason to weaken that behavior. If its documented
1.5 A `OUT` limit or live-load charge behavior cannot support Sherman's responsive
compute load, replace the charger/power-path hardware. Do not move motors onto
`OUT`, require system shutdown, or add a charging procedure. Charge termination
must be qualified with the real docked workload attached.

The fast-follow rear-entry dock Sherman backs into feeds the same charger input through at least four contacts:
first-mate/last-break ground, dock-switched 5 V, current-limited pilot/identity,
and open-drain release request. Dock 5 V defaults off until contact proof. When
Sherman has enough charge it requests release, verifies charger input absent,
requires fresh motion authority, and drives forward off without human assistance.

The Adafruit 1200 mAh cell is only a dimension/runtime candidate. Release it to mobile testing only after:

1. full target + display + camera + ToF active current is measured;
2. motor free-run, acceleration, reversal, and bounded stall-pulse current is measured;
3. the total rail model includes boost efficiency and startup/inrush;
4. connector/wire/protection limits are not exceeded;
5. runtime and reserve meet the accepted duty cycle;
6. the `34 × 62 × 5 mm` pouch plus swelling/lead bend/retention fits M0;
7. brownout, boot-loop, thermal, and physical-removal tests pass.

## Receiving checklist

For every exact item:

1. Match invoice, manufacturer, SKU, silkscreen, revision, option, and quantity.
2. Photograph both sides with a scale and assign a hardware ID.
3. Measure outline, height, connector/body keep-outs, cable exit, mounting holes, and mass.
4. Inspect for shipping or ESD damage and verify connector polarity with continuity before mating.
5. Archive manufacturer page/datasheet and the checked date.
6. Power alone with a current limit; record idle/active/peak current and heat.
7. Run the subsystem receiving test before handing the part to another workstream.
8. Record failures and quarantine suspect parts; do not silently swap a spare into safety evidence.

For the charge-interlock delivery specifically, count three bare PCBs and match
all nine Mouser lines to
[`order-manifest.md`](../../electronics/pcb/charging-interlock-rev-a/order-manifest.md).
Inspect the PCB outline, four M2 holes, plated/non-plated drills, front legend,
and all annular rings before population. Do not mark an assembly received or
qualified merely because the carrier reports delivery.

## Cost envelope

- Exact modules/electromechanical candidates and named spares: **about $454**, excluding the interlock PCB/passive order and fast-follow dock.
- The compact interlock PCB and population kit are **ordered**; final paid totals are reconciled from receipts rather than inferred from the prepared-cart quote.
- Remaining purchases are workshop stock, protection parts selected after measurement, mechanical materials, and the fast-follow dock—not another interlock implementation.
- Electronics/harness stock if starting empty: **about $183–355**.
- Mechanical/optical materials if starting empty: **about $187–360**.
- Calibration/test fixtures: **about $50–150**.
- Those shop-stock ranges are checklists, not expected purchases. Reuse household/makerspace tools and buy consumables only when the active phase needs them.
- No oscilloscope, laboratory bench supply, hot-air station, thermal camera, or other major instrument is part of Sherman's purchase plan.

The practical DIY cost is therefore the exact gated modules plus whatever small amount of wire, fasteners, filament and basic tools is genuinely missing. Do not turn the checklist into a cart.
