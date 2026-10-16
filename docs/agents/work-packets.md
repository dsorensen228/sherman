# Initial Work Packet Backlog

Packets are sized for one focused agent change. IDs encode phase and area. Dependencies in brackets must be complete first. Physical packets also require the relevant safety review.

## Phase 0 — Personality simulator

- **P0-CON-001:** define v0 event, action, expression, health, and Jarvis schemas plus golden fixtures.
- **P0-SIM-001:** deterministic clock, seed, event queue, scenario manifest, and trace writer. `[P0-CON-001]`
- **P0-CORE-001:** lifecycle and action-state machines with transition/property tests. `[P0-CON-001]`
- **P0-PER-001:** need/mood model with bounded update rules and replay fixtures. `[P0-CORE-001]`
- **P0-PER-002:** utility-based behavior selection, arbitration, cancellation, explanations. `[P0-PER-001]`
- **P0-DSP-001:** semantic expression grammar and renderer-independent animation timeline. `[P0-CON-001]`
- **P0-DSP-002:** desktop display backend and golden image/semantic tests. `[P0-DSP-001]`
- **P0-JAR-001:** Jarvis emulator with request/outage/reconnect scenarios. `[P0-CON-001, P0-SIM-001]`
- **P0-INT-001:** integrate routines, behavior, eyes, Jarvis emulator, trace/replay. `[all P0 above]`
- **P0-VAL-001:** blinded expression review, 24-hour accelerated simulation, determinism/resource report.

## Phase 1 — Brain and real eyes

- **P1-PLAT-001:** exact board receiving record, recovery, boot and chosen OS baseline.
- **P1-BLD-001:** pinned host/target build and reproducible `shermand` artifact. `[P1-PLAT-001]`
- **P1-PLAT-002:** supervisor, config layering, health, bounded structured logs. `[P1-BLD-001]`
- **P1-DSP-001:** receive and electrically qualify two identical Waveshare 1.9-inch SKU 23822 modules on a conservative SPI clock; publish photos, dimensions, device-tree diff, captures and test frames.
- **P1-DSP-002:** implement and profile the bounded RGB565 `/dev/spidev0.0` ST7789V2 backend behind the Phase 0 contract; dispose ADR 0003 from latency/FPS/resource/soak evidence. `[P1-DSP-001]`
- **P1-NET-001:** versioned WebSocket/Jarvis client with pairing/auth abstraction and fault tests.
- **P1-STO-001:** embedded store spike, power-fault/migration evaluation, down-select ADR.
- **P1-INT-001:** target demo integrating eyes, behavior trace, Jarvis link, store and supervisor.
- **P1-VAL-001:** latency, CPU/RAM, thermal, boot/recovery, reconnect and soak evidence.

## Phase 2 — Stationary perception

- **P2-CAM-001:** supported CSI camera driver/pipeline, timestamped frame contract and replay capture.
- **P2-TOF-001:** VL53L5CX breakout bring-up, rates/modes, health and raw replay capture.
- **P2-CAL-001:** camera intrinsics and camera↔ToF extrinsic calibration tooling/fixtures.
- **P2-SYNC-001:** cross-stream clock model and synchronization quality metrics.
- **P2-VIS-001:** bounded perception baseline; observations with confidence/provenance.
- **P2-TRK-001:** local multi-observation tracks and controlled change hypotheses.
- **P2-WLD-001:** stationary local scene representation and transactional persistence.
- **P2-PRV-001:** privacy modes, transient buffer audit, diagnostic capture controls.
- **P2-INT/VAL-001:** stationary desk demo and labeled fixture/resource/recovery report.

## Phase 3 — Mobility

- **P3-CTL-001:** controller selection spike and boot-safe GPIO/PWM/watchdog test.
- **P3-CON-001:** motion protocol implementation on Linux + controller with fuzz/golden tests.
- **P3-MOT-001:** characterize the Pololu #5146/#4762/#1087/#2130 drivetrain at bench, 1S-range voltage and controlled fault conditions; invoke a second ratio only if acceptance fails.
- **P3-CLF-001:** characterize two Pololu VL53L4CD #3692 cliff sensors across surfaces, height, angle, light, contamination and XSHUT/address fault cases.
- **P3-IMU-001:** IMU qualification and timestamp/calibration path.
- **P3-PWR-001:** qualify the split compute/motor power tree, automatic dual-inhibit charge interlock, converter/charger/battery down-select, one-action cable charging, and safety review.
- **P3-PWR-002 (completed 2026-09-01 by Codex):** designed and fabrication-checked the compact, dedicated revision-A PCB for the P3-PWR-001 automatic dual-inhibit charge interlock; the reproducible Gerbers, drills, BOM, assembly drawing, vendor preview, and verification evidence are published. `[P3-PWR-001 design inputs; physical bench qualification remains in P3-PWR-001]`
- **P3-PWR-003 (design/order preparation complete 2026-09-14 by Codex; BLOCKED-HARDWARE for qualification):** replaced rejected Rev A with the same-size Rev B; native KiCad DRC, independent manufacturer/Gerber checks and 26 electronics tests pass. Three corrected After Dark bare boards at OSH Park, $7.10 total, awaiting payment. Evidence: `artifacts/phase-3/P3-PWR-003/RESULTS.md`. `[P3-PWR-002 design inputs; P3-PWR-001 bench qualification remains required]`
- **P3-WIR-001:** build and verify revision W1 from the canonical guide/netlist, including the passive I2C hub and zero-touch charge transitions. `[P3-PWR-001]`
- **P3-CAD-001/002:** measured volume model, M1 tray, then restrained M2 chassis.
- **P3-CTL-002:** wheel-speed loops, odometry, command TTL, fault latch, telemetry.
- **P3-SAF-001:** Linux safety arbiter and controller admission invariants.
- **P3-HIL-001:** link/sensor/reset/brownout fault injection rig.
- **P3-INT-001:** restrained chassis bring-up; exact polarity/direction/stop checklist.
- **P3-VAL-001:** free-motion qualified matrix, including 500 cliff approaches and runtime.

## Phase 4 — Persistent world model

- **P4-NAV-001:** frame graph, pose estimate and covariance contract.
- **P4-NAV-002:** occupancy representation, inflation, local planner and controller simulation.
- **P4-LOC-001:** encoder/IMU/range/visual fusion and relocalization confidence.
- **P4-WLD-001:** object permanence, change hypotheses, decay and revisit priority.
- **P4-BEH-001:** curiosity/information-gain behavior with motion/risk/duty costs.
- **P4-REC-001:** stuck detection and bounded recovery ladder.
- **P4-DCK-001:** fast-follow rear-entry dock geometry, autonomous backing alignment, four-contact pilot/power/release handshake, charge integration, forward drive-off, and fault/thermal evidence. `[P3-PWR-001]`
- **P4-INT/VAL-001:** repeated patrol/map/change/restart/recovery evidence.

## Phase 5 — Character and daily operation

- **P5-PER-001:** stable personality parameter pack and regression scenario suite.
- **P5-RTN-001:** timezone-aware routine scheduler, quiet hours, pause and catch-up semantics.
- **P5-JAR-001:** production Jarvis interaction scenarios, summaries, help and uncertainty language.
- **P5-DSP-001:** final eye grammar, authoritative overlays and blinded legibility review.
- **P5-OPS-001:** provisioning/update/rollback/backup/erase/support bundle.
- **P5-END-001:** 24-hour then multi-day supervised endurance, privacy and nuisance review.
- **P5-REL-001:** v1 gate packet, frozen hardware profile, assembly and operating guide.

## Packet template

```markdown
# <ID>: <title>
Parent phase:
Owner / reviewer:
Objective:
Non-goals:
Prerequisites:
Owned paths:
Forbidden/shared paths:
Inputs and contracts:
Implementation tasks:
Required tests:
Required artifacts:
Acceptance criteria:
Stop/escalation conditions:
Rollback:
Handoff:
```

## P1-JAR-002: Generated idle speaker exchanges

Parent phase: 1; narrow character work pulled forward under ADR 0006.
Owner / integration reviewer: Codex, 2026-09-11 (implemented and bench verified).
Objective: Fresh one/two-pair Qwen scripts, local beep voice, configurable Jarvis
speaker, random hourly mean while healthy stationary idle.
Non-goals: locomotion, camera observations, general Jarvis transport, prerecorded jokes.
Prerequisites: deployed P1 personality/face runtime and ALSA device (observed online).
Owned paths: `personality/banter/`, new firmware banter config/init/deploy/test files,
`proto/schema/banter-script-v1.json`, `proto/fixtures/banter-script-v1.json`, related
personality/platform/protocol docs and `artifacts/phase-1/P1-JAR-002/`.
Shared integration: Jarvis API, voice device actions, generated OpenAPI and contracts.
Forbidden paths: unrelated CAD/navigation/electronics and Luckfox SDK changes.
Allowed dependencies: Python stdlib, ALSA aplay, existing authenticated Jarvis/Qwen
and voice connection hub; no motors, model runtime, or private imagery.
Implementation: schema first, bounded generation/replies, procedural audio/scheduler,
idle admission, config/boot deployment, deterministic and live verification.
Required tests/evidence: JSON bounds, auth/device ownership, expiry/replay/order,
seeded cadence and failure skips, actual playback acknowledgement and face coexistence.
Acceptance: fresh scripts execute in order through configured speakers and failures
remain silent without replay; diagnostics and deployment rollback documented.
Rollback: disable banter; restore backed-up Jarvis/voice files if needed.
Human review: owner confirmed the voice sounded good, requested more volume, and
approved the full exchange after amplitude was raised from 0.18 to 0.32.
Residual follow-up: P1-VAL-001 / P5-END-001 longer nuisance/resource soak; future
core admission replaces face-health gating before mobility.
Evidence: `artifacts/phase-1/P1-JAR-002/RESULTS.md`.
