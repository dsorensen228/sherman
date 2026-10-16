# Integration Playbook

## Integration branch readiness

A component enters integration only with passing local tests, compatible schema version, fake/replay fixture, resource notes, documented configuration, and a named rollback. Hardware adapters also require receiving record and bench results.

## Integration sequence

1. Pin build, schema, configuration, hardware, and calibration IDs.
2. Run baseline before merging the candidate.
3. Integrate one producer/consumer boundary at a time using recorded data.
4. Verify health/readiness and negative paths before the happy-path demo.
5. Run representative scenario and resource comparison.
6. Inject dependency loss, stale input, invalid payload, restart, and queue pressure.
7. For motion, progress simulated → HIL → wheels-up → restrained → contained free motion.
8. Store result under the phase/packet artifact directory and update traceability.

## Interface failure checklist

- clock domain and timestamp units;
- coordinate frame and handedness;
- enum/unknown/default behavior;
- freshness and expiry;
- queue bounds/backpressure;
- retry/idempotency/replay;
- lifecycle/readiness race;
- reset and partial state;
- numeric saturation/NaN;
- configuration/calibration mismatch;
- authority and capability checks.

## Build-breaking conflict policy

Restore the last known green integration baseline before layering additional changes. Do not “fix forward” across multiple unknown failures. Bisect by packet and preserve the failing artifacts. Contract owner decides semantic conflicts; safety owner decides motion/safety conflicts; program integrator decides sequencing.

## Phase demo rule

A demo is a reproducible scenario, not a hand-steered success. Its manifest names setup, inputs, build/config/hardware/calibration IDs, expected assertions, stop conditions, and artifact outputs. The human-facing demo may be charming; the underlying evidence remains machine-checkable.

