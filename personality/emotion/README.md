# Emotion and Mood Model

`personality/emotion` is a compact C++17 model for Sherman's presentation
state. It owns bounded needs, explicit event impulses, slow relaxation, mood
derivation and the semantic values consumed by an eye-expression mapper. It
does not command pixels, motors, lifecycle state or authoritative overlays.

## API

Create an `EmotionModel`, feed explicit outcomes with `apply()`, and call
`advance(elapsed_s, stimulus)` from an injected monotonic clock. Read
`expression()` to obtain:

- one of `calm`, `curious`, `focused`, `pleased`, `uncertain`, `frustrated` or
  `tired`;
- valence in `[-1, 1]`;
- arousal, confidence and attention in `[0, 1]`.

All state transitions are deterministic. Continuous updates use exponential
relaxation so need values do not depend on tick rate. Inputs are checked for
non-finite values and finite normalized inputs are clamped. Repeated events
have a short cooldown to prevent an unbounded event burst from instantly
driving presentation. Mood dwell time is not backdated across a need threshold
observed during a coarse update, so equivalent coarse and fine tick schedules
do not transition early.

`snapshot()` returns the small versioned state that is meaningful across a
restart. `restore()` rejects incompatible or corrupt state and resets to
defaults. Transient affect, attention, transition progress and cooldowns never
survive restart. A storage owner remains responsible for encoding, checksums
and atomic persistence.

The display layer should map `ExpressionIntent` into its own renderer poses.
Core remains responsible for compositing fault, low-battery, privacy and update
overlays at a higher priority.

## Build and test

```sh
cmake -S personality/emotion -B build/emotion -G Ninja
cmake --build build/emotion
ctest --test-dir build/emotion --output-on-failure
```
