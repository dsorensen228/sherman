# Core Runtime

## Scope

`core/` owns the on-device lifecycle, typed event routing, health/readiness aggregation, action lifecycle, scheduling, capability/resource ownership, safety admission, configuration view, time/random abstractions, and composition root. It does not implement sensors, navigation algorithms, perception, personality scoring, rendering, wire transport, or storage backend details.

Core is the narrow waist: every subsystem can be constructed with fakes and driven by deterministic time. Hardware and network failures become typed health/events, not exceptions that silently terminate the runtime.

## Key invariants

- Only `ACTIVE` plus valid authority permits motion proposals to reach the gateway.
- Every action is identifiable, expiring/cancelable, and terminal exactly once.
- Priority/preemption is centralized and inspectable.
- Queues and work budgets are bounded.
- Wall time never controls safety deadlines.
- Configuration cannot exceed compiled/hardware safety bounds.
- Shutdown/restart leaves actuators safe and state consistent.

