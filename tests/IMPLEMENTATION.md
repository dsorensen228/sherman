# Shared Test Infrastructure Plan

## Test harness

Unified runner discovers scenario/protocol metadata, selects profile, injects clock/seed/faults, collects structured results, verifies assertions and writes manifest with build/config/hardware/calibration IDs. Commands are stable and documented for agents/CI/operators.

## Fakes and fixtures

Contract-faithful fake platform/controller/display/sensors/store/transport/Jarvis; builders for valid/invalid messages; synthetic desk/object/sensor data; golden schema bytes; approved calibration/replay bundles; fault-point store and network. Fakes must model failure/freshness/limits, not just happy returns.

## Physical protocols

Versioned step-by-step protocols with equipment, environment, preflight, stop condition, instrumentation, sample matrix, pass criteria, artifact requirements and cleanup. Cliff, stop timing, motor characterization, power/runtime/charge, thermal, calibration and endurance get separate protocols.

## Traceability

Machine-readable mapping requirement/safety/performance/experience IDs → test IDs → profile/hardware → last result/artifact. Markdown acceptance matrix is generated or checked against it when implementation begins.

## Result format

JUnit or selected machine summary plus Sherman manifest, metrics time series, event trace, logs, media references and `RESULTS.md`. Preserve failed artifacts and mark deviations. Sensitive data has classification/retention.

## Milestones

- T0 host runner/fakes/golden/contracts.
- T1 deterministic scenarios/replay.
- T2 target smoke/resource and calibration fixtures.
- T3 HIL/physical protocols/traceability.
- T4 endurance/release reporting.

