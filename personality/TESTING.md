# Personality Testing Plan

## Invariants/property tests

Needs remain finite/bounded; no tick-rate dependence beyond tolerance; lower-priority candidate cannot preempt admitted critical action; expired/canceled tasks stop influencing selection; cooldown/duty prevents loops; quiet/pause suppresses disallowed actions; low energy/fault moves toward rest/help not curiosity; output facts originate from supplied world/action state.

## Golden scenario traces

Version canonical morning, moved mug, lost headphones request/cancel, block/frustration/recovery, pickup, low battery, Jarvis outage, contradictory observation, no-news day, quiet hours, repeated failure and restart. Assert allowed action/expression sequences and explanation tags rather than overfitting exact millisecond timing.

## Statistical/long-horizon

Run hundreds of seeds and accelerated weeks. Measure action distribution, repetition intervals, idle/motion duty, cancellation, unresolved actions, energy trend, routine completion, change follow-up, help frequency and entropy/variety. Flag pathological cycles, starvation and extreme tails.

## Counterfactual tests

Change one input—energy, risk, information value, Jarvis priority, route cost, recent failure—and verify selection changes in the expected direction. This detects sign/weight errors and supports explainability.

## Human evaluation

Blinded traces/clips ask viewers to infer intent/mood and rate predictability, charm, annoyance and trust. Separate subjective results from safety/functional requirements. Ensure authoritative fault/privacy states remain clear independent of personality pack.

## Persistence/migration

Restart at every action/routine stage. Physical actions do not resume; mood/needs/routine checkpoint follows specified policy. Migrate prior pack/state versions, reject incompatible/corrupt values safely and support reset to defaults.

## Executable coverage

`runtime/tests/runtime_test.cpp` implements deterministic same/different-seed
replays, natural idle-state coverage, semantic attention/task/outcome response,
quiet/circadian/pause behavior, invalid-input non-mutation, restart policy and a
seven-day accelerated run. Policy tests exercise routine, Jarvis, world-change,
risk, failure, repetition, low-energy, commitment, hysteresis, duplicate IDs,
deadline boundaries and the bounded candidate limit. Routine coverage includes
ordered checkpoints, windows crossing midnight, quiet/pause, skip/catch-up,
failure cooldown, repeated/backward/forward civil time, persistence and corrupt
state. `runtime_c_test.c` compiles as C11 and verifies ABI sizes, safe fallback,
all snapshots, policy/routine selection and event validation. Both suites are
run under strict warnings and ASan/UBSan.
