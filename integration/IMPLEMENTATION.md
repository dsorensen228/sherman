# Integration Implementation Plan

## Composition manifest

For each profile define module implementations/fakes, rates/budgets, hardware/calibration/config IDs, feature flags, authority/safety bounds, external endpoints, artifact location and supported scenario set. Composition must fail visibly on incompatible identity rather than silently select defaults.

## Bring-up pipeline

1. Verify exact hardware and preflight/physical stop.
2. Flash/deploy pinned artifacts and effective config hash.
3. Validate platform/controller readiness with actuators disarmed.
4. Test schemas/health/log/time/storage/network independently.
5. Add display, sensor, perception, world, behavior in dependency order.
6. Add motion only at the appropriate physical progression level.
7. Run negative/fault scenarios before human-facing demo.
8. Capture resource baseline and support bundle.

## HIL

Build transport bridges that connect production Linux/runtime to simulated controller/sensors or production controller to simulated world. Fault injection is scriptable and timestamped. HIL definitions must not weaken production validation/authority checks.

## Release candidate

Create immutable manifest of source commit, toolchain/dependencies, system/controller images, schema, configuration, hardware profile, calibration, assets, CAD/BOM, acceptance protocols and evidence index. Sign/checksum where tooling permits. Document rollback to prior candidate.

## Phase gate assembly

Generate traceability snapshot, automated results, resource/performance plots, physical artifacts, known deviations/risks, ADR list and operator reproduction steps. A demo script references actual scenario/test IDs.

## Ownership

One integration owner per phase controls root composition/profile files. Subsystem agents contribute via reviewed interface and their own tests, then pair with integration owner for profile update.

