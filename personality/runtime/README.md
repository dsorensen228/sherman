# Autonomous Personality Runtime

`personality/runtime` is Sherman's target-ready personality policy. It is not a
scripted expression demo. With only an injected monotonic clock and optional
local civil time, it continuously produces a quiet, seeded sequence of settled
attention, orientation, observation and return-to-center. Validated semantic
inputs let later camera, presence, task, world-model and Jarvis adapters attract
attention without coupling this code to hardware or fabricating observations.

The runtime composes the bounded `EmotionModel` with two independent layers:

- `PersonalityController` turns needs, outcomes, attention, activity, uptime,
  circadian time, quiet/pause state and recent interaction into renderer-neutral
  expression, gaze, eyelid and blink intent.
- `BehaviorPolicy` scores at most 16 caller-supplied safe candidates for local
  idle, routines, Jarvis requests, world changes and recovery. It returns a
  selected semantic action proposal and complete score components; it never
  commands hardware or bypasses core/safety admission.
- `RoutineScheduler` turns at most eight data-defined local-time windows, each
  with up to eight semantic checkpoints, into ordinary policy candidates.

## Idle behavior

The default pack is curious but calm. During an ordinary workday Sherman rests
at center, periodically orients to a non-repeating side, observes briefly, and
settles again. The seed controls timing and direction, making replay exact while
avoiding a fixed animation loop. A valid attention target wins promptly. Active
tasks focus at center, interactions engage and then reflect, and real outcomes
feed the emotion model. Explicit pause suppresses flourishes. Explicit quiet or
the default local quiet interval (`02:00` inclusive through `08:00` exclusive)
requests sleep: centered, fully closed eyes with no random blinking. Quiet wins
over attention, tasks, interactions and pause. Display owns smooth entry/exit
and sleeping animation. Wall time is ignored unless the caller marks it valid.

No sensor is assumed. Clear `ATTENTION_VALID` when no adapter has a current
target. User presence, novelty, task engagement and other semantic fields must
come from an owning subsystem and are rejected when non-finite or out of range.

## Behavior policy

Candidates declare stable identity, kind, deadline, origin, compatibility flags,
five positive values and six costs. The policy:

1. rejects malformed batches, duplicate IDs, stale deadlines and more than 16
   candidates;
2. excludes candidates unavailable under pause, quiet or low-energy context;
3. calculates inspectable task, curiosity, social, routine and urgency value;
4. subtracts time, energy, motion, risk, repetition and recent-failure cost;
5. adds a tiny deterministic, five-second-epoch tie variation;
6. applies minimum commitment and hysteresis to prevent twitching; and
7. returns the winner, runner-up, score breakdown and reason bits.

The core remains responsible for authoritative lifecycle, capability and safety
admission. Candidate `AVAILABLE` means the core has already said that proposal
may be considered; it is not an authorization to move. An empty or fully
excluded set returns explicit `WAIT` fallback semantics.

During quiet hours only zero-motion Wait/Rest proposals are eligible, even when
an active, urgent or Jarvis-origin candidate claims quiet compatibility. The C
handle propagates its latest controller quiet reasons into policy selection;
step personality before selection. Direct C++ policy callers supply `kPolicyQuiet`.
Before motors are connected, P3-SAF-001 must additionally cancel in-flight motion
and inhibit actuator output throughout quiet hours in core/controller admission.
Policy selection and display health cannot stop or authorize a physical motor.
See ADR 0009 and `proto/quiet-hours-sleep.md`.

## Routines

No schedule is compiled into Sherman. A caller installs up to eight routine
definitions with stable IDs, local start time, window, skip/catch-up policy,
quiet and low-energy compatibility, cooldown, values, and an ordered list of up
to eight semantic behavior kinds. The scheduler emits the current checkpoint as
an ordinary routine-origin policy candidate with deterministic identity,
deadline and rising due pressure. The action owner reports success or failure;
success advances the checkpoint and failure waits 30 seconds before retrying.

Civil time is supplied as an explicit day ID plus local second, with a validity
flag. Monotonic time exclusively owns cooldowns. Completed occurrence IDs block
duplicates if a daylight-saving repeated hour or manual backward correction is
observed; a forward jump only creates catch-up work when the definition permits
it. Windows may cross midnight. Pause emits no work, and quiet suppresses any
definition not explicitly compatible.

Jarvis and world-model adapters use the same bounded candidate contract. This
lets real routines/actions arrive without a personality-policy redesign.

## Stable C ABI

`runtime_c.h` exposes API version `0x00010000` and builds
`libsherman_personality_c.so`. The opaque handle owns controller, policy and scheduler.
Creation is the only routine heap allocation; step, event, selection, output and
snapshot calls use caller-owned fixed-size structs and fixed stack storage.

The primary functions are:

- `sherman_personality_step` and `sherman_personality_get_output`;
- `sherman_personality_apply_event`;
- `sherman_personality_select_behavior`;
- `sherman_personality_snapshot_state` / `restore`;
- `sherman_personality_snapshot_policy` / `restore_policy`;
- `sherman_personality_set_routines`, `collect_routine_candidates`, result and
  routine snapshot/restore functions; and
- `sherman_personality_safe_output` for an explicit calm, centered fallback.

Every C struct carries a size, version where applicable, and reserved fields.
Call the exported size functions before binding through `ctypes`. Input failures
do not mutate native state; `step` also fills the caller's output with safe
fallback intent so a presentation loop never needs to display unvalidated data.

## Persistence and restart

Personality, policy and routine snapshots are separate fixed-layout records so
storage can checksum, version and atomically commit them. Durable needs, mood,
random sequence continuity, interaction ages, repetition, checkpoints and
routine retry/completion cooldowns survive. Active interaction, current physical
action, gaze position, emotion-event cooldowns and partially completed
micro-behaviors do not: restart begins centered and settled. Corrupt or
incompatible native state is rejected and reset to bounded defaults.

## Build and test

```sh
cmake -S personality/runtime -B build/personality-runtime -G Ninja
cmake --build build/personality-runtime
ctest --test-dir build/personality-runtime --output-on-failure
```

The tests cover deterministic idle variety, semantic attention, real outcome
responses, task focus, quiet/circadian/pause behavior, restart policy, an
accelerated week, routine/Jarvis/world-change scoring, counterfactual costs,
low-energy exclusion, repetition, commitment, routine checkpoints, midnight and
civil-time discontinuities, corruption and C ABI use. The
same suite is compiled with strict warnings and Address/Undefined sanitizers.
