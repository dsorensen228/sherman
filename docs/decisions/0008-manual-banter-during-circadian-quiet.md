# 0008 — Manual banter during circadian quiet

## Status
Accepted, 2026-09-18. The owner explicitly requested that the standby button work
at night while spontaneous nighttime interactions remain suppressed.

## Context
The manual button reused automatic speech admission. Live voice-example status
was `not_idle` although both services were healthy: Sherman reported `drowsy`
with reason flag 2, meaning circadian quiet. This disabled a deliberate request
for the entire nighttime period.

## Decision
Keep automatic admission unchanged. For authenticated manual triggers only,
permit the circadian-quiet reason and its drowsy presentation. Poll readiness,
initial execution, post-generation checks and audio cancellation use the same
manual predicate. Drowsiness without the circadian reason remains denied.

Explicit quiet, pause, task/attention engagement, low energy, startup, fallback,
unknown reasons and stale or degraded health still deny speech. The existing
Jarvis speaker-idle and single-use trigger checks remain authoritative. A manual
exchange samples a fresh automatic interval as before.

## Alternatives
Disabling circadian behavior globally would also enable unsolicited night speech.
Changing only the poll would enable the button but reject execution. Both fail
the requested behavior.

## Consequences
The exception applies only to the stationary banter adapter; face state and the
nighttime schedule are unchanged. No wire fields, hardware configuration, audio
volume, motor authority or safety thresholds change. No incoming server or new
background worker is introduced.

## Verification
Reproduce nighttime health in deterministic tests; verify manual polling and
sequential playback, automatic suppression, and retained denial/interruption for
other reasons. Deploy the exact committed runtime, check its hashes, and request
one live exchange through voice-example while face health remains circadian quiet.
Require local completion plus Jarvis playback acknowledgment and renewed readiness.

## Rollback
Restore `/opt/sherman-banter.previous` and restart the existing banter init service.
The button then becomes unavailable during nighttime hours again.

## Links
- `0007-manual-banter-trigger.md`
- `../../personality/banter/README.md`
- `../agents/work-packets.md`, P1-JAR-004
- `../../artifacts/phase-1/P1-JAR-004/RESULTS.md`
