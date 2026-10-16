# Simulation Testing Plan

## Simulator correctness

Test event ordering, cancellation, periodic drift, accelerated wall/monotonic behavior, named random stream independence, seed replay, trace checksum, bounded event queue and shutdown. Use analytic kinematics/ray/geometry/energy cases and conservation/symmetry properties where applicable.

## Determinism

Run each canonical scenario repeatedly across clean processes; normalized traces/checksums match for a build/config/seed. Parallel test scheduling must not change scenario results. If floating differences are allowed, define semantic/tolerance normalization.

## Fault model tests

For each injected fault verify onset/duration/recovery and emitted sensor/link semantics: drop, stale, delay, noise, saturation, corrupt, reset, clock skew, storage full, network flap, power sag, pickup, slip and object change. Test overlapping faults and restoration ordering.

## System invariant suite

No motion when disarmed/faulted/expired; stop within modeled bound; safety priority preempts; bounded recovery; no expired command replay; quiet/privacy modes; honest lost localization; map beliefs decay; storage/log/queue bounds; accelerated days do not accumulate runaway tasks.

## Model validation

Compare physical course/stop/sensor/power captures against simulation with declared metrics and confidence bands. A model may support regression even if not predictive; label its validated domain. Phase gates use physical evidence for safety.

## Scenario quality

Schema/lint manifests, require unique IDs/owners/requirement links, detect unused events/assertions and forbidden real-time sleep/network. Nightly matrix records seed and retains first failure trace plus minimized case when available.

