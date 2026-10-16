# Personality Runtime Verification

Packet scope: `P0-PER-002` policy foundation plus the stationary subset of
`P0-INT-001` and the stable-pack foundation for `P5-PER-001`.

## Implemented claims

- Seeded autonomous idle behavior is deterministic, bounded and not a canned
  clip: settled, orienting and observing states all occur in the replay suite.
- Expression intent is derived from durable needs, semantic activity/outcome
  events, uptime, circadian/quiet state and recent interaction.
- Semantic attention drives normalized gaze without any dependency on camera or
  presence hardware; missing adapters remain explicitly invalid/unset.
- Behavior scoring accepts at most 16 candidates and exposes every positive and
  negative score component, winner, runner-up and reason bits.
- The data-driven scheduler bounds routines/checkpoints at 8 x 8, supports
  wrap-midnight windows, quiet/pause, skip/catch-up, cooldown and repeat-safe
  civil-time discontinuities without embedding a user's schedule.
- Quiet, pause, low energy, availability and expiration exclusions precede
  scoring; commitment, hysteresis and repetition costs bound policy churn.
- Runtime, policy and routine snapshots reject corrupt/incompatible state and
  never resume a transient physical presentation or action.
- The C ABI uses fixed-size caller-owned records with explicit API/record
  versions and has no allocation on steady-state calls.

## Automated evidence

Host verification command families:

```text
clang++ -std=c++17 -Wall -Wextra -Wpedantic -Werror ... runtime_test.cpp
clang -std=c11 -Wall -Wextra -Wpedantic -Werror ... runtime_c_test.c
clang++ -fsanitize=address,undefined -fno-omit-frame-pointer ...
```

Results on 2026-08-19:

```text
All personality runtime tests passed
All personality C ABI tests passed
AddressSanitizer/UndefinedBehaviorSanitizer: pass
Accelerated deterministic horizon: seven days at one-minute ticks
```

The C ABI shared-library symbol check includes `api_version`, `step`, and
`select_behavior` and the routine functions.

Luckfox Pico Ultra W cross-build and on-device smoke, 2026-08-19:

```text
artifact: ELF 32-bit LSB ARM EABI5 shared object
size: 52,772 bytes
sha256: f57ec3d30af1b4ec4fc61a5e7af8c0e38030339ec299653c90b4499a74934247
All personality C ABI tests passed
smoke maximum RSS: 1,384 KiB
```

## Boundaries and residual work

- This library proposes behavior; core/safety remains the only owner of action
  admission, cancellation and motors.
- Jarvis, world-model and sensor adapters still have to supply truthful
  candidates/inputs. Routine definitions are configuration, never implicit
  evidence that a physical checkpoint completed.
- Authoritative privacy, battery, degraded, update and fault overlays remain
  outside personality and must win in the display compositor.
- Expression legibility and nuisance/delight require the planned blinded and
  lived-use reviews; automated semantic tests do not close those human gates.
