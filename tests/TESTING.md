# Test Infrastructure Self-Tests

## Harness

Prove discovery/filtering, fake clock/seed, timeout/cancel, parallel isolation, artifact paths, expected-fail/skip policy, result aggregation and nonzero exit. Deliberately fail assertions/setup/cleanup to ensure failure cannot be reported pass.

## Fakes

Run contract suites against fake and production adapters where possible. Verify fault modes, freshness, queue bounds, reset/state and timing. Detect fixtures that omit newly required fields or use incompatible schema/calibration.

## Determinism and artifact integrity

Repeat scenario across processes/order/parallel execution; same normalized result. Check checksums, manifest completeness, collision-free output, partial-run recovery and redaction/secret/private-frame scans.

## Physical protocol dry runs

Independent operator reviews and dry-runs with safe/dummy hardware. Validate sample-count calculations, randomization/order, data capture, abort, recovery and ambiguity. A protocol cannot be accepted only by its author.

## Traceability consistency

Fail when an active requirement has no test/owner, a gate test has no approved protocol, an artifact is missing/mismatched, or acceptance docs drift from machine mapping.

