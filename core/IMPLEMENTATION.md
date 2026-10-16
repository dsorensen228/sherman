# Core Implementation Plan

## Modules

### Foundations

Strong unit types or naming for time/distance/angle/voltage; monotonic and wall-clock interfaces; seeded random source; IDs; result/error taxonomy; cancellation/deadline token; build/config/hardware identity; immutable snapshot types.

### Lifecycle and health

Implement the documented system lifecycle with guarded transitions, reason/event, entry/exit actions, readiness dependencies, capability mask, degraded state, latching policy, and test-only state inspection. Components publish health with freshness; aggregator decides readiness through explicit policy.

### Event routing

Prefer typed in-process events and immutable payloads. Define bounded queues, priority classes, backpressure/drop/coalesce policy, subscriber time budget, and metrics. Critical health/safety events cannot be silently dropped; high-rate telemetry may be coalesced or dropped with counters.

### Action manager

Create action from behavior/Jarvis intent, validate preconditions/resources/deadline, assign ID, admit/reject/defer, execute through subsystem interface, handle progress, cancellation, preemption and exactly-one terminal outcome. Persist only compact action/outcome state; never resume physical motion after restart.

### Safety arbiter

Consume lifecycle, human stop, controller status, sensor freshness, localization confidence, zone/speed limits, battery/thermal, and proposed motion. Produce permitted/limited/rejected envelope and reason. Make the logic pure where possible for exhaustive/property tests. It provides defense in depth; controller remains final immediate stop authority.

### Scheduler and composition

Schedule periodic and event work through injected clock/executor. Detect overrun, queue pressure, missed deadline and starvation. Compose modules in one process initially; lifecycle start/stop order is explicit and reversible.

### Configuration

Load/validate layered configuration, compute effective hash, clamp user/session values inside safe hardware/compiled bounds, detect restart-required keys, and publish change events. Invalid config fails readiness rather than substituting dangerous defaults.

## Milestones

- C0: foundations, fake clock/random, lifecycle/action state machines.
- C1: typed event bus, health/readiness, metrics hooks.
- C2: action manager and fake subsystem integration.
- C3: pure safety admission with exhaustive fixtures.
- C4: target composition, shutdown/restart/resource controls.
- C5: performance and fault hardening for integrated v1.

## Agent boundaries

One integration owner controls composition/build files. Lifecycle, event bus, action, safety, and configuration can be separate packets after interfaces land. Do not let subsystem agents add global singleton state or call hardware/transport directly from core.

