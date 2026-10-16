# Integration Testing Plan

## Smoke matrix

For every profile: clean start, self-test/readiness, expected capabilities, schema/config/hardware/calibration identity, bounded logs, health snapshot, graceful stop/restart and support bundle. Target profiles include boot/power and missing peripheral.

## Boundary tests

Producer/consumer version mismatch, stale timestamp, wrong frame/calibration, queue pressure, component not ready/restart, storage/network outage, display/sensor fault, Jarvis cancel/reconnect, controller sequence/expiry and safety rejection. Verify correct degraded capability and human-visible state.

## Vertical scenarios

One canonical scenario per phase plus regression of previous phase: personality morning; target eyes/Jarvis; stationary moved object; mobile edge/obstacle; persistent patrol/change/recovery; daily endurance. Each has seed/setup/assertions/artifacts.

## Resource/endurance

Compare profile CPU/RSS/latency/thermal/power/log/storage against baseline and budget. Run soak with faults/restarts rather than only steady happy path. Attribute regressions to owning packet before release.

## Release reproduction

Independent operator uses release manifest to provision/recover and run demo/acceptance subset. Verify checksums and rollback. Missing manual knowledge is a failure of the release candidate.

