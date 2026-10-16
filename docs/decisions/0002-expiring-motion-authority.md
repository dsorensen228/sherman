# ADR 0002: Use Expiring Motion Authority with Independent Stop

**Status:** Accepted at architecture level; exact controller hardware remains Proposed

## Context

Desktop edge avoidance and motor stop must not depend on an unconstrained Linux process remaining scheduled and healthy. The development board is optimized for vision rather than hard-real-time motor safety.

## Decision

All nonzero motion commands are bounded and expire quickly. A companion controller is the reference owner of motor output, encoder timing, cliff reflexes, command expiry, watchdog, and drive enable. Linux proposes velocity; the controller stops independently on expiry or critical fault.

## Alternatives

- Direct Linux GPIO/PWM: simpler but rejected unless Phase 3 measurements can demonstrate equivalent worst-case behavior under injected load and failures.
- Passive mechanical edge protection only: insufficient.
- Commercial safety controller: disproportionate for this prototype.

## Consequences

Adds a local protocol, firmware, module, wiring, and integration tests. It provides deterministic replayable motion semantics and a cleaner hardware-in-loop boundary.

## Verification

Watchdog, stale/duplicate/corrupt frame, reset, brownout, sensor-fault, and Linux-kill tests; safe-stop timing measured at motor terminals and wheel motion.

## Rollback

Any alternate architecture must pass the same failure and latency protocol and be accepted in a superseding ADR.

