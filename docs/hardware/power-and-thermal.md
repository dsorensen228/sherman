# Power, Battery, Charging, and Thermal Plan

## Safety premise

Battery integration is hardware work, not a software-only task. Use protected cells from reputable suppliers, current-limited bench power during bring-up, insulated connectors, strain relief, fusing/protection, and a nonflammable test area. Never charge an unattended prototype or a damaged/swollen cell.

## Provisional power tree

`1S protected LiPo → battery fuse → branches:`

- #4755 power-path `LOAD/OUT` → regulated/boosted 5 V compute rail for Luckfox, Pico, and selected peripherals;
- separate automatic high-side motor gate → motor rail, with charge-present hardware inhibit, noise isolation, and local bulk capacitance;
- regulated sensor/controller rails as required;
- an exterior USB-C/dock input that keeps the robot powered and charges its installed cell while hardware automatically disables motion.

Common ground strategy, rail sequencing, inrush, motor noise, and USB back-power paths must be documented before connecting battery, charger, and USB simultaneously.

Named qualification candidates are the Adafruit protected 1200 mAh cell #258, Pololu U3V70F5 5 V boost #2891, two Pololu Mini Pushbutton Power Switch LV #2808 modules, Adafruit BQ24074 Universal USB/DC/Solar charger #4755, TI SN74HC08N interlock logic, and Adafruit MAX17048 gauge #5580. The #4410 is not part of the mobile architecture. None may be released to mobile use until the load and M0 gates in `shopping-list.md` pass.

## Measurement campaign

For every hardware configuration measure voltage/current at ≥ idle, boot, Wi-Fi connect, display animation, camera stream, ToF active, representative inference, motor free-run, turning, acceleration, recovery, and controlled stall pulse. Record average, peak, duration, ripple, ambient, and rail location.

Build a duty-cycle model:

`runtime_h = usable_battery_Wh × conversion_efficiency / average_system_W`

Use measured usable capacity and efficiency curves, not label capacity. Reserve energy for a safe stop, final report, and return-home attempt. Publish nominal, pessimistic, and degraded-battery estimates.

## Brownout behavior

- Controller must enter motors-off on undervoltage/reset.
- Luckfox reboot cannot leave drive enabled.
- Storage writes must tolerate abrupt loss.
- Low-battery thresholds include motor-load sag and hysteresis.
- Repeated boot loops are prevented below a qualified voltage.
- USB insertion/removal cannot create a motor pulse or unsafe rail reversal.

## Charging

V1 charging is a product invariant: plugging powered USB-C into Sherman is the only user action. The cell stays installed; compute remains powered and responsive; raw VBUS/`PGOOD` hardware forces both the automatic motor-power gate off and DRV8833 `nSLEEP` low; firmware observes and records the transition but cannot override the inhibit. The #4410 must not be installed. Configure #4755 for the cell's accepted charge current only after thermal and termination tests.

Motors use a separate fused-battery branch, so #4755's 1.5 A `LOAD/OUT` budget applies only to compute and logic. If the accepted responsive compute workload exceeds it, replace #4755 with a higher-capacity power-path part; shutdown or an extra charging step is not an alternative. The fast-follow rear-entry dock uses ground, switched 5 V, pilot/identity, and release-request contacts. Sherman backs in; dock power defaults off until pilot proof; Sherman requests 5 V removal, verifies charger input absent, then drives forward off. Measure battery, charger, regulator, automatic gate, contact, and enclosure temperature.

## Power states

- `ACTIVE`: full sensing and permitted motion.
- `OBSERVING`: stationary perception; reduced motor rail.
- `QUIET`: lower perception rate, dim eyes, network alive.
- `SLEEP`: controller safety alive, Linux suspended/off only if recovery is reliable.
- `CHARGING`: cable VBUS or proved dock power present; both hardware motor inhibits active; controller disarmed; responsive qualified compute/sensing workload; faults retain motor inhibit and report visibly.
- `CRITICAL`: immediate stop, minimal checkpoint, clear expression, shutdown.

Transitions are explicit, logged, and exercised under fault injection.

## Thermal qualification

Instrument compute hot spot, enclosure air, boost/charger, motor driver, motors, and battery-adjacent region. Run worst representative combined load until thermal steady state or defined timeout. Test while charging separately and under the allowed combined charging workload.

Acceptance limits come from exact component specifications plus conservative enclosure margins. Firmware reduces optional inference/display brightness before safety-critical control is threatened, but no thermal policy may rely on a sensor that has not been calibrated and plausibility-checked.

## Tests

- Coarse boot/current logging with an inline USB meter; borrow current-limited supply or scope access only if a concrete inrush/brownout fault needs higher-resolution diagnosis.
- Motor transient and camera/ToF corruption correlation.
- Converter efficiency/ripple map across battery voltage and load.
- USB + battery + charger state matrix including unplug/replug; all unsupported simultaneous states must be blocked or fail safely.
- One-action charge insertion during every motion direction and reset state; no user preparation, motor pulse, or command replay.
- Dock pilot/default-off power/release request/verified 5 V removal/autonomous departure matrix.
- Undervoltage ramp and sudden disconnect.
- Controller and Linux independent reset during motion command.
- Fuel/voltage estimate under pulsed load.
- Runtime trial from full to reserve under scripted mixed duty.
- Charge cycle with thermal logging and post-charge termination observation.
- Storage integrity after power cuts at controlled write phases.
