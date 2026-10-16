# Core Testing Plan

## State-machine coverage

Enumerate valid transitions and assert every invalid transition is rejected with no partial side effect. Cover startup failure, readiness loss, degrade/recover, safe-stop latch/reset, shutdown from every state, action success/fail/cancel/preempt/timeout, duplicate completion, late callbacks, and restart policy.

## Determinism and scheduling

Fake-clock tests advance exact deadlines without sleeps. Property tests generate event ordering, cancellation and faults; normalized action/lifecycle traces must be identical for a seed. Test overrun, long subscriber, full queues, priority inversion attempts, time jump/timezone change, and random-source recording.

## Safety admission

Build a truth-table/property corpus across lifecycle, controller arm/fault, command freshness, cliff/sensor health, localization confidence, battery/thermal, user stop, zone and requested speeds. Invariants: any critical false precondition yields zero permission; limits never increase requested or hardware maxima; NaN/infinite/missing values fail closed.

## Event bus and resource bounds

Stress producers beyond configured rates. Verify drop/coalesce/backpressure policy, critical-event delivery, counter accuracy, no deadlock/reentrancy corruption, bounded memory, subscriber removal, and clean shutdown. Run sanitizers/race detectors on host.

## Configuration

Fuzz types/ranges/unknown keys/duplicate layers/corrupt files; verify safe clamping, restart flags, deterministic effective hash, hardware-profile mismatch, and inability to raise immutable limits.

## Integration fixtures

Use fake platform, storage, controller, display, perception, navigation, behavior, and transport to test startup order, partial readiness, component crash/restart notification, action cancellation propagation, safe shutdown, and support snapshot.

## Performance

Publish host and target latency distributions for event dispatch, safety admission, action transition, lifecycle health aggregation, queue depth and CPU/RSS under representative rates. Regressions over reviewed thresholds block integration.

