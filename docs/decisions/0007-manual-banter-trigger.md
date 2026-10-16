# 0007 — Manual banter trigger

## Status
Accepted for the stationary Phase 1 prototype, 2026-09-14. User requested an
immediate demo button on the associated voice device; Codex owns both API and robot.

Amended by ADR 0008 on 2026-09-18: deliberate button requests may bypass scheduled
circadian quiet. Explicit quiet and all other admission checks remain enforced.

## Context
Random hourly banter is inconvenient to demonstrate. The configured Sherman source
and Jarvis response pair already determines where real chirps and speech belong.

## Decision
The enabled robot polls authenticated `/v1/banter/poll` every five seconds with its
configured pair, current idle readiness and optional prior manual outcome. Jarvis
exposes the associated voice-device control and queues at most one short-lived
request. Only a ready poll consumes its 32-character lowercase hexadecimal ID.
Sherman passes that ID to normal script creation once, allowing Jarvis to bypass
the autonomous cooldown for a deliberate demo. Every local idle, script deadline,
sequential playback and process lock check still applies. A consumed manual request
resamples the autonomous timer, including a locally denied or failed request.

Outcome acknowledgments are idempotent and retained across polling failures.
Ambiguous script creation or playback is never retried. Poll and authentication
have three-second HTTP timeouts. Failure retries use exponential jittered backoff
capped at 60 seconds; the daemon continues its autonomous scheduler. The synchronous
daemon does not poll or start another interaction during a running exchange.

## Alternatives
An incoming robot HTTP server adds credentials and listening-socket maintenance.
Remote shell execution couples the UI to provisioning. Lowering the autonomous
interval changes normal behavior without providing a deliberate demo control.

## Consequences
One additive API polling exchange, optional script-creation `trigger_id`, and bounded
health counters; no robot configuration, GPIO, motor, audio amplitude or safety
authority changes. An unavailable or non-idle robot cannot be forced to speak.
Requests expire on the API after 15 seconds queued or 180 seconds in progress;
stale associations are unavailable after 15 seconds and retained for 300 seconds.

## Verification
Golden poll fixture, malformed ID/body validation, bounded timeout/backoff, repeated
outcome acknowledgment, failed/idle-denied scripts without replay, scheduler reset,
existing seed 531 regression, and coordinated live voice/ALSA acknowledgment.

## Rollback
Restore `/opt/sherman-banter.previous` or disable the banter init service. The
separate face runtime is unchanged; the old robot ignores the additive API paths.

## Links
- `proto/schema/banter-poll-request-v1.json`
- `proto/schema/banter-poll-response-v1.json`
- Jarvis `contracts/devices/banter-v1.md`
- `docs/agents/work-packets.md`, packet P1-JAR-003
