# Electronics Implementation Plan

## Documentation artifacts

Maintain block/power diagrams, machine-readable BOM, exact module links/revisions, pin/bus ledger, harness/connector table, wiring schematic, test-point map, rail/current budget, power-state matrix, receiving record and approved substitutions.

## Bring-up sequence

1. Verify board/module markings, physical damage, dimensions/mass and documentation.
2. Establish logic levels, rail limits, polarity/keying and idle/reset states on paper.
3. Continuity/resistance check unpowered harness/assembly.
4. Power each module alone from a known-good supply; use the supply's protection, an inexpensive inline limiter/fuse, or borrowed current-limited supply where actuator fault energy warrants it. Log coarse idle/active current and heat with available DIY tools.
5. Validate logic bus with analyzer before actuators.
6. Add motor driver with motors disconnected; confirm enable/output default.
7. Single motor then dual motor under characterization fixture.
8. Combine display/camera/ToF and motor transients; inspect rail ripple/errors.
9. Add candidate battery/boost/charger only after the system load model exists.

## DIY fault triage

Use a bounded module-level workflow: visual/connector/polarity/continuity check, documented supply/configuration, minimal vendor example, cable swap, then spare-module swap. If the fault follows a low-cost module, quarantine and replace it. Do not perform component-level board repair. Continue deeper only if the same fault survives replacement and therefore implicates a shared interface, power rail, harness, software configuration, or mechanical condition.

## Power system

Specify 1S protected LiPo and conversion only from measured load. The current candidates are Adafruit #258/#4755/#5580 and Pololu #2891/#2808; their presence in the shopping list is not a freeze. Split compute and motor power after the battery fuse: #4755 `LOAD/OUT` supplies compute only, while a separate automatic high-side gate supplies the driver. Charger-input presence must force that gate off and DRV8833 `nSLEEP` low in hardware without firmware or user action. Include cell connector/strain/swelling, fuse/PTC/protection, retained interlock logic, four-contact dock pilot/release, local bulk/bypass, regulator efficiency/transient/ripple/thermal and dock-input back-power prevention. V1 charging is one-action cable insertion with compute responsive; the follow-up dock must charge and release Sherman for autonomous departure. Reserve energy for stop/checkpoint and prevent low-voltage boot loops.

## Motion/sensor integration

Controller/driver reset and pull states keep motors off. Encoder inputs tolerate/noise-filter without missing legitimate edges. Identical I2C cliff sensors get separate reset/address management or qualified mux. IMU orientation and interrupt/timestamp ownership match mechanical frame. Motor leads/loops stay separated from sensitive camera/ToF/display wiring.

## Harness

Keyed/polarized connectors where possible, explicit pin 1, voltage/color labeling, strain relief, abrasion/edge protection, slack for assembly but none near wheels, bend-radius and mating-cycle considerations. Provide accessible test points for each rail, ground, enable, UART, PWM/outputs, encoders and sensor buses.

## Thermal/noise

Measure converter/charger/driver/motor/battery-adjacent temperatures and conducted noise. Select PWM and acceleration based on motor/control/acoustic evidence. Fix root current-loop/decoupling/routing problems before hiding them with software retries.

## Freeze process

Bench-qualified → integrated M2 → enclosure/thermal/runtime/charge qualified → frozen exact BOM/harness. A substitution lists affected electrical, driver, mechanical, calibration, power/thermal and safety retests.
