# Quiet-hours sleep semantics (ADR 0009)

The existing personality C ABI version and structure layouts are unchanged.
Circadian quiet (reason bit 1) or explicit quiet (bit 2) requests behavioral sleep.
The Drowsy micro-behavior carries closed-eyelid, zero-blink, centered-gaze intent;
display interpolates entry/exit instead of applying closure instantaneously.

The bounded face-health JSON gains `sleep_state`, one of `awake`,
`falling_asleep`, `sleeping`, `waking_up`. It describes presentation and is never
motor authorization. Banter requires the exact `awake` value in addition to its
existing freshness, personality and reason checks; missing/unknown values deny
speech. Prior readers ignore this additive field and still reject quiet reason
bits, but do not suppress speech throughout waking: upgrade both consumers.

A manual trigger may be admitted while falling asleep/sleeping/waking, subject
to the existing circadian-only exception (ADR 0008). The banter daemon writes
`manual-wake-request-v1.json` atomically to the shared configurable
`wake_request_file` (default `/run/sherman-wake.json`). Face reports the accepted
`wake_request_id` alongside sleep state. Banter waits at most six seconds for
the matching ID and `awake` before generation/playback, retaining the lease
through the entire exchange. It removes the request in a finally block on
success/failure/cancellation. Missing, malformed, expired or pre-restart leases
return the face to sleep if quiet remains. Lease lifetime is at most 300 seconds
with no automatic renewal; all scheduled, explicit-quiet, pause, degraded and
task admission rules remain enforced. A wake lease only affects presentation:
native circadian quiet and motor-proposal inhibition stay asserted throughout.

Quiet behavior-policy admission now permits only Wait/Rest with zero motion
cost and the existing quiet-compatible flag. Current commitment, high urgency
and Jarvis origin cannot bypass this admission. The C handle combines caller
quiet with its latest controller quiet output. Consumers step personality before
selection; direct C++ policy callers propagate quiet explicitly. Selection is
not safety admission; core must cancel active motion and hold motors inhibited.
