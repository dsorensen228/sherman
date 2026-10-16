# Transport Testing Plan

## Deterministic state tests

Fake clock/network drives DNS failure, connection refusal, TLS/auth failure, negotiation mismatch, server close, idle timeout, offline/online, backoff ceiling, and shutdown. Same seed gives same jitter trace. Confirm no busy reconnect loop or unbounded task/thread growth.

## Contract/security tests

Malformed/oversized/fragmented messages, unknown versions/types/enums, invalid ranges, stale/future timestamps, duplicate/idempotency collision, unauthorized capability, credential rotation/revocation, wrong server identity, log redaction, and parser fuzz.

## Reconciliation tests

Disconnect before acceptance, after acceptance, during progress, before terminal result, and after event spooling. Restart Sherman and Jarvis independently. Confirm exactly-one semantic action, no expired replay, correct cursor gap signal, and honest unknown outcome when proof is absent.

## Load/resource tests

Ingress rate/connection abuse; outbound burst; long offline period; spool byte/count/age full; priority eviction/coalescing; slow receiver/backpressure; network flapping during display/perception load. Measure CPU/RSS/storage/log growth and latency of critical events.

## End-to-end

Run emulator and real Jarvis compatibility against current/prior schema. Include pause/stop, observe/locate, cancel, progress, result, health, help, privacy mode, and invalid remote motion attempt. Prove transport absence does not affect local safe operation.

