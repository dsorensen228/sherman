# Observability and Support Plan

## Goals

Diagnose lifecycle, safety, action, perception, navigation, resource, power and connectivity without retaining excessive private data or disturbing real-time behavior.

## Signals

- Structured events: state transitions, faults, action admissions/outcomes, reconnect, recovery, config/update.
- Metrics: CPU/RSS, temperatures/power/battery, queues/drops, sensor rates/age/errors, display latency/drops, controller loop/link/stop, localization confidence, planning/recovery, storage/log/spool.
- Traces: bounded correlation from Jarvis request/behavior intent through action, perception/navigation and expression/controller command IDs.

## Policies

Levels/priorities are bounded; rate-limit/coalesce repeated events; critical first-fault context retained; low-priority telemetry drops before resource pressure. Logs include build/config/hardware/calibration/session but no credentials/raw frames/private content. Monotonic timestamps drive ordering, wall time aids humans.

## Support bundle

Explicit command produces manifest, recent bounded structured logs/metrics, health/fault/action summary, versions/config diff with secrets removed, storage integrity and calibration/profile identifiers. Camera/replay attachments require a separate visible authorized choice. Bundle is inspectable before sharing and has retention/erase.

## Alerts and user state

Eyes show authoritative status; Jarvis provides textual detail. Repeated crash, critical thermal/battery, controller fault, lost localization/help, storage corruption/full, update rollback and privacy capture are distinguishable. Avoid alarming on transient recovered conditions; preserve counts/context.

## Tests

Fault-to-signal completeness, rate/flood bounds, log rotation/full storage, clock issues, restart continuity, secret/private-data scan, support-bundle reproducibility/redaction, and observability overhead under worst representative target load.

