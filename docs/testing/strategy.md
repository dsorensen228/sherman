# Verification and Validation Strategy

## Objective

Produce evidence that Sherman satisfies specified behavior in normal, boundary, degraded, and fault conditions. Tests are layered so cheap deterministic failures are found before physical hardware is placed at risk.

## Test layers

### L0 — Static and generated checks

Formatting, lint, compiler warnings-as-errors for project code, schema generation consistency, dependency/license/security review, device-tree/pin-ledger consistency, CAD parameter checks, and documentation link/traceability checks.

### L1 — Unit and property tests

Pure algorithms, parsers, state machines, filters, coordinate transforms, storage migrations, schedulers, policy scoring, eye interpolation, and resource bounds. Use fake clocks and seeded random sources. Property tests cover invalid/fuzzed ranges and invariants.

### L2 — Contract tests

Golden bytes/JSON diagnostics across C++/Python/controller implementations, prior minor versions, reconnect/idempotency, unknown fields/enums, corruption, oversized frames, expiry, and units.

### L3 — Component integration

Multiple modules with fake or recorded adapters: sensor synchronization → perception, world model → behavior, behavior → safety, expression → renderer, storage/restart, Jarvis disconnect/reconnect.

### L4 — Deterministic simulation

Scenario runner models robot kinematics, desk boundaries, obstacles, sensors, latency, noise, faults, time of day, and Jarvis events. Every scenario records seed and has assertions on safety, actions, map, expression, and resource use.

### L5 — Sensor replay

Recorded or synthetic camera/range/odometry/IMU streams run through production pipelines. Golden outputs use tolerances and semantic assertions rather than brittle exact floating-point snapshots.

### L6 — Bench hardware

One device/module at a time with current limiting and instrumentation. Drivers, logic levels, performance, fault behavior, noise coupling, thermal behavior, and recovery are established before enclosure installation.

### L7 — Hardware-in-loop

Production Linux runtime communicates with simulated or real controller/sensors through physical interfaces. Inject corruption, delay, reset, dropout, bus lock, stale data, and power events.

### L8 — Restrained chassis

Wheels elevated or chassis tethered/contained. Verify direction, encoder polarity, acceleration, stop, fault, cliff signals, current, and controller autonomy before contacting an open desk.

### L9 — Qualified physical environment

Sacrificial bounded desk, controlled obstacles/surfaces/light, safety observer, conservative speed. Execute acceptance matrices and record video/telemetry/build/config.

### L10 — Endurance and lived experience

Multi-hour/day runs on an already qualified environment, monitoring memory, thermal, storage, reconnects, routine quality, nuisance behavior, wear, battery, and privacy.

## Required test metadata

Every nontrivial result records test ID/version, UTC time, operator/agent, hardware IDs/revisions, build and config hashes, calibration profile, environment/surface/light, seed or replay ID, instrumentation, raw artifact links, outcome, and deviations.

## Test taxonomy

- `REQ-*`: product requirement.
- `SAF-*`: safety claim.
- `CON-*`: interface/compatibility.
- `PERF-*`: latency/resource/performance.
- `ENV-*`: environment/physical matrix.
- `REC-*`: recovery/fault injection.
- `EXP-*`: experience/usability/personality.

Code tests reference these IDs; the acceptance matrix maps each to an owner and phase gate.

## Physical-test controls

- Preflight checklist, motor disable verification, current-limited supply where applicable.
- Containment/tether progression and sacrificial test edge.
- One change variable per run when characterizing.
- Stop condition and observer named before free movement.
- Battery inspection and charge log.
- Preserve failed-run evidence; do not retest until the changed hypothesis is recorded.

## Flaky-test policy

A flaky test is a defect. Quarantine only with owner, issue, reproduction data, and expiry. Never quarantine safety, protocol compatibility, storage integrity, or phase-gate tests. Track rate across repeated seeded runs and reduce nondeterminism at the source.

## Coverage expectations

Coverage percentages are secondary to risk coverage. Require transition coverage for state machines; branch/condition coverage for safety admission; corpus/fuzz coverage for parsers; fault-point coverage for storage; scenario coverage for behavior; surface/angle/speed/light coverage for cliff safety; and configuration/hardware profile coverage for integration.

## Regression cadence

- Per change: L0–L3 and affected fast simulations.
- Nightly or integration batch: full simulation/replay matrix, sanitizer builds, schema compatibility, resource regression.
- Per target build: smoke on real board, boot/restart/storage/display/network.
- Per hardware change: affected bench/HIL/restrained suites.
- Per release candidate: full applicable L0–L10 evidence and traceability review.

