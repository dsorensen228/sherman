# Phase 5 — Character, Daily Operation, and v1 Release

## Outcome

Sherman operates as a reliable tiny coworker: predictable but not mechanical, expressive but not misleading, useful to Jarvis, respectful of quiet/privacy boundaries, supportable by the owner, and stable through supervised multi-day use.

## Entry conditions

- G4 accepted; remaining safety/environment assumptions are explicit.
- Hardware and calibration profile targeted for v1 is stable.
- Product owner has used the integrated robot enough to identify nuisance and delight patterns.
- Operations owner and v1 gate reviewer named.

## Character system

Freeze a small personality parameter pack: curiosity, persistence, sociability, caution, patience, energy expression, and recovery style. Parameters adjust bounded policy weights/timings; they never bypass admission/safety. Preserve continuity across days without producing manipulative emotional claims or pretending to possess feelings/needs beyond the product metaphor.

## Daily routines

Implement wake/self-test, morning desk sweep, routine landmarks, periodic low-duty refresh, Jarvis-request windows, quiet hours, charge/rest, end-of-day summary, pause/vacation mode, missed-routine catch-up, and daylight-saving/timezone changes. User pause wins immediately and persists clearly.

## Expression polish

Finalize the semantic grammar and a compact animation library for attention, curiosity, tracking, thinking, satisfaction, uncertainty, frustration, tired/low battery, blocked, pickup, charging, privacy, update, degraded, fault, and help. Authoritative overlays have reserved priority and visual language. Tune brightness/night behavior, blink/gaze naturalness, repetition, transitions, and gaze alignment with physical sensor/task direction.

## Jarvis relationship

Use versioned task requests, progress, cancellation, uncertainty, summaries, and help. Sherman should report facts and confidence concisely; Jarvis can add dialogue/personality. Define comic beats as optional presentation over true state—never fabricate a located object, completed patrol, battery condition, or safety status.

## Operations

- repeatable provisioning and hardware-profile selection;
- calibration wizard and validity check;
- authenticated pairing/re-pairing and credential rotation;
- software/config update with verification, disarmed execution, rollback, and last-good;
- backup/export/erase of world and personality state;
- bounded support bundle with redaction/privacy review;
- self-test, fault codes, replaceable-part/assembly guide;
- recovery from failed boot, full storage, corrupted state, lost network, dead battery, and replaced sensor/module;
- documented safe operating environment, charge/storage, cleaning, and inspection.

## Experience validation

Use a mixed method:

- semantic expression recognition without logs;
- task success and honest-uncertainty review;
- interruption/pause/quiet-hour responsiveness;
- behavior variety/repetition statistics;
- nuisance observations: noise, screen brightness, motion frequency, false alerts;
- delight observations recorded separately from requirement pass/fail;
- privacy-state understanding and data audit;
- accessibility considerations: brightness, motion sensitivity, visual-only alerts and alternate status in Jarvis/logs.

## Endurance ladder

1. 8-hour workday with scripted routine and injected network outage.
2. 24-hour supervised run including quiet hours, charge/rest, storage rotation, time transition.
3. Multi-day supervised office use with daily inspections and controlled object changes.
4. Restart/update/rollback during the endurance campaign.

Track memory/CPU/thermal/power/storage, battery cycles, resets, reconnects, dropped data, action timeouts, recovery attempts, localization resets, false change alerts, cliff stops, motor stalls, log volume, and human interventions. Every intervention is data, not hidden from reliability metrics.

## v1 release packet

- released source/config/schema/build and dependency manifests;
- frozen BOM/hardware and calibration profiles;
- CAD release, drawings, print settings, assembly/inspection procedure;
- provisioning, pairing, calibration, operation, update/rollback, backup/erase guides;
- requirements/acceptance traceability and raw artifact index;
- hazard analysis/safety case with qualified environment and residual risks;
- performance/resource/power/thermal/runtime/endurance report;
- known limitations, unsupported surfaces/objects/lighting, and recovery steps;
- privacy/data-retention description;
- demonstration scenario and support bundle procedure.

## Gate G5 acceptance

- All non-deferred acceptance-matrix rows pass against the frozen v1 profile.
- 24-hour and multi-day suites have no unresolved safety-critical failure or unbounded resource growth.
- Pause, stop, quiet hours, privacy, update/rollback, backup/erase, and recovery are independently reproduced from docs.
- Expressions are legible, including reserved safety/privacy/degraded states.
- Jarvis interactions are useful and uncertainty is honest.
- The owner accepts nuisance/delight tradeoffs and explicit environmental limits.
- A fresh provision/assembly or documented rebuild can reproduce the released system.

## Post-v1 backlog, not silent scope

Possible audio, improved docking, new object models, smaller/custom electronics, alternate shells, multi-desk profiles, remote diagnostics, or commercial productization each require a new phase/ADR and renewed privacy/safety analysis.

