# Jarvis Transport

## Scope

`websocket/` owns Sherman’s resilient authenticated connection to Jarvis: connection lifecycle, version/capability negotiation, schema framing, deadlines, request/result/progress correlation, deduplication, reconnect/reconciliation, priority spool, and metrics.

It does not decide whether a task is behaviorally desirable or physically safe. It submits validated requests to core and reports outcomes honestly. It cannot directly command hardware.

Despite the directory name, the exact transport remains an ADR; preserve an interface so TLS WebSocket can be replaced without changing command semantics.

