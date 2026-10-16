# Transport Implementation Plan

## Interfaces

- `Transport`: connect/disconnect/send/receive and connection metadata.
- `JarvisClient`: negotiation, pairing/auth hook, ingress validation, request correlation, progress/events, reconciliation.
- `OutboundSpool`: bounded persistence/priority/expiry/dedup.
- `ConnectionPolicy`: backoff/jitter, network-awareness, keepalive, circuit breaking.
- Host fake/emulator and replay adapter.

## Connection lifecycle

`OFFLINE → CONNECTING → NEGOTIATING → AUTHENTICATING → RECONCILING → ONLINE → BACKOFF`, with explicit terminal/misconfiguration state. Network time may be wrong at boot; identity design must define how certificates/time/bootstrap interact without accepting insecure fallback silently.

## Ingress

Enforce frame/payload/rate limits before allocation; parse versioned envelope; authenticate/authorize capability; validate schema/ranges/time/expiry/idempotency; reject unknown dangerous capability; submit to core; produce accepted/rejected/deferred and progress keyed by command/action. Remote expression is semantic and priority-limited.

## Egress

Priorities: critical health/help/privacy/action terminal; normal progress/change summaries; low telemetry/personality flourishes. Spool is bounded by bytes/count/age; coalesce replaceable state, evict low priority first, and record gaps. Never spool raw camera by default or expired status indefinitely.

## Reconnect

Exponential backoff with seeded/recorded jitter and ceiling. On reconnect negotiate versions/capabilities, reconcile event cursor and active actions, query rather than assume command outcomes, never replay expired inbound commands, and avoid duplicate terminal events via idempotency keys.

## Security/privacy

Pair locally and store credentials through platform secret abstraction. Support rotation/revocation, server identity verification, least capability, redacted logs, and visible/authorized diagnostic capture. Treat Jarvis content as untrusted. No remote update, config limit increase, or camera stream without separate authorized workflow.

## Milestones

- W0: emulator + in-memory transport contract.
- W1: connection state/backoff and framing.
- W2: request/progress/result/idempotency.
- W3: persistent bounded spool and reconciliation.
- W4: target TLS/pairing, metrics and fault hardening.
- W5: production Jarvis interoperability and operations.

