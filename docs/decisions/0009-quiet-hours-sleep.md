# 0009: Quiet hours are behavioral sleep

## Status

Accepted, 2026-09-26, implementing the owner's request. Integration review covers
personality, display and stationary banter; physical motor validation remains
BLOCKED-HARDWARE under P3-SAF-001.

## Context

Quiet hours already stop banter but only lower the eyelids. External attention
can override drowsiness, and a candidate marked quiet-compatible can request a
patrol. There is no implemented motor driver or safety arbiter in this repository.

## Decision

Use the owner-requested local interval [02:00, 08:00), including explicit quiet input.
Quiet overrides character attention, tasks and pause, with closed centered eyes.
Display owns monotonic, interruptible three-second falling-asleep and 2.4-second
waking transitions, plus a six-second subtle breathing animation while asleep.
Transitions start from the currently displayed pose, including after reversals.
The native ABI and persisted layouts remain unchanged: existing quiet reason
bits request sleep and `Drowsy` remains its renderer-neutral micro-behavior.

Quiet policy admits only zero-motion Wait/Rest candidates, regardless of origin,
urgency, quiet-compatible flags or current-action commitment. The C wrapper
propagates the controller's quiet reasons into selection even if a caller omits
the policy quiet flag. Direct C++ policy consumers must supply that flag.
This is proposal filtering, not actuator authority: the future core must cancel
active motion and inhibit all motor output during quiet hours independently of
face health, before connecting motors. Existing stop/fault authority always wins.

Face health adds a descriptive sleep state. Banter requires `awake`, and health
is published on each transition so an ongoing local beep is interrupted through
its existing permission callback. Older health without sleep state fails closed.
Missing native personality retains local sleep in the degraded presentation.
Neither OS suspend nor a network dependency is introduced.

Per the owner's clarification, a deliberate nighttime request wakes the eyes,
waits for the full wake animation, performs the Jarvis exchange, then immediately
starts the falling-asleep animation. Preserve ADR 0008's manual exception through
a bounded presentation-only wake lease and matching face-health acknowledgment.
The lease expires after at most 300 seconds and is removed on success/failure;
it cannot clear quiet motion policy or override explicit quiet, pause or faults.
Face ignores requests predating its process start, so restarts never replay wake.

## Alternatives

A TIRED expression alone does not look asleep. Letting attention wake Sherman
violates the requested quiet-hours behavior. A display-owned motor output path
would bypass the future safety arbiter and is rejected.

## Consequences

Deploy face and banter together. Installations with older face health remain
silent until upgraded. Restart recomputes quiet state from local time; it never
resumes an old sleep timer or physical action. Wall-clock changes select the
desired state; monotonic time drives visual transitions.

The owner corrected the schedule to 02:00–08:00 on 2026-09-26. The Luckfox's
vendor camera NTP adds 28,800 seconds directly to UTC every minute; provisioning
disables that clock writer in live and boot-template camera configs. Stock ntpd
owns UTC, the RTC stores UTC, and face presentation applies the configured
America/New_York-equivalent POSIX timezone. No timezone offset enters UTC.

## Verification

Fake-clock boundary, restart, attention, policy and ABI tests; frame continuity,
sleep-cycle determinism, region bounds and banter admission tests; rendered preview.
Physical motor inhibition must be qualified in P3-SAF-001 before mobility.

## Rollback

Restore the previous face and banter installations together. No state migration.

## Links

- `docs/agents/work-packets.md`: P1-DSP-003
- `proto/quiet-hours-sleep.md`: additive health and existing ABI semantics
- `docs/decisions/0002-expiring-motion-authority.md`
