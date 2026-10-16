# Phase 3 — Safe Mobility, Power, and Chassis

## Outcome

Sherman moves on a qualified desktop within a measured speed/acceleration envelope, reports odometry/health, stops independently on command expiry or critical fault, avoids qualified edges, and runs from a qualified battery/power system in a serviceable prototype chassis.

## Safety posture

This is the highest-risk phase. Progression is bench → hardware-in-loop → wheels-up → restrained → contained sacrificial surface → free movement on a qualified desk. No agent skips a stage because the happy path worked once.

## Entry conditions

- G2 accepted; perception can be disabled without breaking platform health.
- Preliminary hazard analysis and physical test controls reviewed.
- Motors, encoders, driver, controller, IMU, cliff candidates, wheels, and instrumentation received/recorded.
- Measured component envelope exists before battery/chassis freeze.

## Work packages

### Controller qualification and protocol

Select a small MCU-class module using boot-safe outputs, watchdog, timers/PWM, encoder capture, I2C/GPIO, UART, toolchain/testability, resource margin, and fit. Implement versioned framed CRC protocol, sequence/TTL, handshake, immutable maxima, arm/disarm/fault latch, telemetry, bootloader/update safety, and golden/fuzz tests on both ends.

### Motor/driver characterization

Start with the Pololu #5146 298:1 MP 6 V encoder motors, #4762 cables, #1087 32 mm wheels, and #2130 DRV8833 carrier. Measure winding resistance if appropriate, no-load and representative-load current/speed across the 1S voltage range, stall pulse/current under controlled conditions, minimum stable duty/speed, encoder resolution/missed counts, backlash, noise, heating, direction/polarity, coast/brake modes, driver thermal/fault behavior, and wheel traction. Introduce a second ratio only if the candidate misses a written speed/control/noise/torque gate; select for quiet low-speed control and safe energy, not top speed.

### Real-time loops

Controller tasks: sensor acquisition, encoder timestamping, wheel-speed estimation/control, command interpolation/limits, cliff filtering/reflex, watchdog/expiry, fault state, and telemetry. Measure worst loop jitter under maximum traffic/faults. Bound integral windup and command acceleration. Reset always starts disarmed.

### Cliff safety

Characterize two Pololu VL53L4CD #3692 candidates over the defined surface set, height, angle, ambient light, contamination, vibration, address/XSHUT faults, and battery/rail conditions. Its 1 mm short-range capability and up-to-100 Hz rate enable low chassis geometry, but do not constitute safety evidence. Design sensor geometry from stopping distance:

`margin = edge_detect_distance - (speed × total_latency + braking_distance + slip/tolerance allowance)`

Qualify forward, arcing, and any permitted reverse trajectories. If reverse coverage is insufficient, restrict reverse speed/distance/geometry explicitly.

### Linux motion and safety

Localization/planner proposes twist; Linux safety arbiter applies lifecycle, freshness, health, zones, confidence, speed, and human/Jarvis stop; motion gateway converts only admitted proposals into expiring controller commands. All paths log action/command IDs and rejection/limiting reason.

### Power architecture

Characterize real rail loads, motor transients, the Pololu U3V70F5 boost candidate, charger-input/back-power behavior, brownout, reserve, protected cell candidates, and thermal. V1 charging is one-action USB-C insertion with the installed cell and responsive compute. A hardware interlock automatically removes the separate motor branch and forces driver sleep; no manual disconnect, switch, shutdown, or disarm step is allowed. Freeze cell, conversion, automatic gate/interlock, four-contact dock interface, connectors, fuse/protection, charge policy, and critical shutdown only after active-motion insertion and fault tests.

### Mechanical ladder

Build M0 measured layout, M1 open tray, M2 restrained chassis, then M3 serviceable enclosure. Maintain wheel/CoM/cliff/optical/antenna/thermal geometry, cable retention, battery service access, exterior charge and USB/recovery access, local stop access, and the internal automatic motor interlock. Cosmetic shell follows evidence.

## HIL and fault campaign

Inject stale/duplicate/out-of-order/corrupt frames; heartbeat loss; Linux process/OS reset; controller reset; UART flood/unplug; cliff stuck high/low/noisy/stale; encoder dropout/reversal; IMU fault; motor stall/driver fault; battery sag/brownout; sensor bus lock; storage/network/perception load; and configuration mismatch. Measure motor-terminal output, wheel motion, controller state, and Linux diagnosis.

## Physical acceptance progression

1. Continuity, polarity, logic level, current limit, boot enable waveform.
2. Single motor unloaded; then both; wheels elevated.
3. Command expiry, stop, controller reset, Linux kill.
4. Restrained surface motion: direction, wheel speed, odometry, arcs, stop distance.
5. Synthetic cliff signal and physical sensor fixture.
6. Contained sacrificial surface at minimum speed with observer/tether.
7. Expand speed/angle/surface/light matrix only after prior bound passes.
8. Execute final qualified 500-approach protocol with zero departures.

Any departure, uncontrolled pulse, or unexplained near miss resets the relevant qualification; preserve telemetry/video and perform a causal review.

## Coherent demo

Power from the qualified prototype system, self-test/disarmed start, explicit arm, low-speed route around simple obstacles, visible expression of intent, safe cliff stops from multiple approaches, injected Jarvis loss with local continuation, injected Linux kill with controller stop, pickup/disarm/replacement, and runtime/reserve report.

## Gate G3 acceptance

- Exact controller/motor/driver/wheel/cliff/IMU/power hardware profile frozen for next phase.
- No uncontrolled motor output in boot/reset/brownout/USB/link fault matrix.
- Critical stop timing and stopping-distance claim meet accepted bounds.
- SAF-CLIFF-001 passes the approved 500-trial qualified matrix with zero table departures.
- Low-speed control/odometry meet course tolerances and diagnose saturation/slip.
- Mixed patrol battery test meets target or records approved envelope/runtime tradeoff.
- Thermal steady state and charge behavior stay within component/margin limits.
- M3 chassis is serviceable, restrained harness is retained, and calibration survives assembly cycles.

## Stop conditions

Do not proceed to autonomy if edge safety depends on Linux scheduling, any rail transition produces motion, exact battery/charger behavior is unclear, or chassis geometry invalidates sensor qualification.
