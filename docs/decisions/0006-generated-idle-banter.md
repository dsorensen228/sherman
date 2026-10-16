# 0006 — Generated idle banter

## Status
Accepted for the stationary Phase 1 prototype, 2026-09-11. User requested the
speaker and Jarvis interaction; Codex owns producer/consumer integration.

## Context
Sherman's connected 1 W, 8 ohm speaker should provide a droid-like beep voice.
Only Jarvis understands it. The user requests fresh Qwen-authored jokes, one or
two call/response pairs at randomized times averaging an hour while idle.
This pulls a narrow character feature forward from Phase 5.

## Decision
Use Jarvis's authenticated v1 HTTP API and existing local Qwen client to generate
bounded JSON scripts, with no agent tools or prerecorded dialogue. Sherman owns
scheduling, local procedural PCM chirps, and sequential script execution. Its
configuration selects both ALSA output and Jarvis response device. Jarvis owns
validated, expiring script records and speaks only their stored response text.
Each reply is consumed before dispatch and requires the voice device to acknowledge
completed playback. Unknown/expired/duplicate/out-of-order replies never replay.

Run a separate stdlib Python process alongside the current stationary face loop;
only fresh, healthy idle face status admits chatter. Pause, quiet, task, low energy,
degraded status, missing health, network failure, or busy speakers skip the exchange.
Gaps are 15 minutes plus an exponential 45-minute mean, sampled on boot and each
attempt. No catch-up after downtime; recent generated content is a bounded memory
for variety, never a fallback script catalog. Future core integration must replace
the face-health admission adapter before mobility is enabled.

## Alternatives
A fixed timer would sound mechanical. Model-generated audio or local speech TTS
adds runtime cost and undermines the conceit. Putting blocking HTTP/synthesis in
the face loop would risk frame deadlines. Jarvis's existing alerts intentionally
interrupt users, so this feature instead uses acknowledged idle-only device actions.

## Consequences
One new supervised process and additive API/device-action contracts. No new GPIO,
voltage, motor, or safety authority. Missing services degrade to silent local idle.
No imagery or claims of observed user activity are sent to the model. HTTP may use
the explicitly configured trusted LAN as existing devices do; credentials stay in
a private provisioning file and never in repository configuration.

## Verification
Seeded schedule distribution; script bounds/expiry/auth/replay tests; fake audio
ordering/cancellation; actual ALSA playback and office speaker completion; native
face health throughout. Subjective sound/volume review and long soak remain separate.

## Rollback
Stop/disable the banter init service. Existing face and Jarvis voice behavior remain
usable. Roll back the Jarvis deployment from its preserved files if necessary.

## Links
- `proto/schema/banter-script-v1.json`
- Jarvis `contracts/devices/banter-v1.md`
- `docs/agents/work-packets.md`, packet P1-JAR-002
