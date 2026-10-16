# Simulation Implementation Plan

## Kernel

Discrete-event scheduler with injected monotonic/wall clocks and seedable named random streams. Stable ordering for equal timestamps, bounded event count, cancellation, periodic tasks without drift, accelerated time and trace of every external input. No real sleeps in deterministic tests.

## World and robot

2D desk polygon/boundaries, obstacles, semantic objects, landmarks, surface regions, lighting/time metadata and optional dock. Differential-drive robot model includes footprint, wheel geometry, velocity/acceleration limits, slip/noise, collision/contact, pickup/relocation and energy model. Keep a cheap model first; add fidelity only to retire a known risk.

## Sensor/actuator models

Camera semantic/synthetic observations or replay; multizone ToF ray/field sampling; cliff range/reflectivity; encoders/IMU; battery/power/temperature approximations; display semantic capture; controller command expiry and fault. Each supports latency, jitter, rate, noise, bias, dropout, stale, saturation, corruption and reset.

## External systems

Jarvis emulator, network connectivity/backoff, time/timezone transitions, storage capacity/corruption/power-cut points, human stop/pickup/object moves, and scheduled routines. Commands use real schemas and validation.

## Scenarios/assertions

YAML/JSON or selected declarative manifest references fixture assets and expected assertions. Assertions include never/always/eventually within virtual deadline, counts/rates/bounds, ordered semantic events, map/pose tolerances, no motion while disarmed, and resource-model ceilings. Traces can shrink/focus a failing randomized case.

## Visualization

Optional live/recorded 2D world with robot footprint/FOV/rays/map/pose uncertainty/path/actions and eye state. Headless is authoritative for CI. Visualization reads trace; it must not alter scheduling.

## Measurement alignment

Store model parameter source and uncertainty. Fit wheel/motor/latency/noise/power from Phase 3 data and maintain validation scenarios comparing simulated vs physical trajectories/energy. Mark unmodeled effects prominently.

## Milestones

- S0 kernel/scenario/trace/seed.
- S1 personality world/Jarvis/eyes.
- S2 sensor replay and stationary desk.
- S3 kinematics/controller/cliff/power faults.
- S4 occupancy/localization/planning/change/recovery.
- S5 accelerated daily/endurance and model-to-hardware report.

