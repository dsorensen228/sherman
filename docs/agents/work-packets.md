# Initial Work Packet Backlog

Packets are sized for one focused agent change. IDs encode phase and area. Dependencies in brackets must be complete first. Physical packets also require the relevant safety review.

## P1-JAR-004: Manual banter during scheduled quiet hours

Parent phase: 1; stationary speaker interaction.
Owner / integration reviewer: Codex, implemented and bench verified 2026-09-18.
Objective: Keep spontaneous nighttime banter suppressed while allowing the paired
voice-device button to request a fresh exchange during circadian quiet hours.
Non-goals: changing quiet hours, explicit quiet/pause, hardware, volume, motion,
API message shapes, or the autonomous schedule.
Prerequisites: P1-JAR-002 and P1-JAR-003; current deployed volume commit 18307b6.
Owned paths: `personality/banter/`, ADR 0008 and decision index, this packet,
and `artifacts/phase-1/P1-JAR-004/`.
Allowed dependencies/interfaces: existing face health, authenticated manual trigger
IDs, stdlib, ALSA, and Jarvis speech acknowledgments.
Implementation: separate manual admission from automatic admission, consistently
apply it to readiness and execution, and document the narrow circadian exception.
Required tests/evidence: nighttime manual polling/playback, automatic suppression,
explicit quiet/pause/low-energy/degraded/stale/unknown-state denial, interruption
during playback, existing deterministic seed 531 regressions, deployed source
hashes, and completed live voice-example interaction with healthy face runtime.
Acceptance: manual requests work during nighttime drowsiness, normal autonomous
admission remains unchanged, and all other admission and single-use checks remain.
Rollback: restore `/opt/sherman-banter.previous` with the existing init service.
Unresolved human decisions: none; user explicitly requested this behavior.
Evidence: `artifacts/phase-1/P1-JAR-004/RESULTS.md`; 19 tests and static checks
passed, deployed source hashes match, actual voice-example standby button completed
one exchange during circadian quiet, then re-enabled. Automatic admission remained
false and concurrent face health remained healthy. No residual task blockers.

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

## P1-JAR-003: Manual standby interaction trigger

Parent phase: 1; additive stationary demo control under ADR 0007.
Owner / integration reviewer: Codex Sherman agent / Codex Jarvis integration owner,
implemented and deployed 2026-09-14; live button playback verification pending.
Objective: Let the associated voice device request an immediate fresh Sherman/Jarvis
interaction through authenticated, bounded robot polling.
Non-goals: incoming robot server, motion, general transport, scheduler replacement.
Prerequisites: P1-JAR-002; coordinated Jarvis API and voice UI implementation.
Owned paths: `personality/banter/`, new poll schemas/fixtures in `proto/`,
`docs/decisions/0007-manual-banter-trigger.md`, this packet and
`artifacts/phase-1/P1-JAR-003/`.
Allowed dependencies/interfaces: stdlib HTTP and existing configured source/response
pair; authenticated `/v1/banter/poll` and optional script `trigger_id`; no secrets.
Implementation: schema/fixture, short bounded polling/backoff, single-use trigger
handoff, outcome acknowledgment, preserved idle gates, deterministic tests and docs.
Required tests/evidence: wrong/malformed IDs, short HTTP/auth timeout, no retry of
playback, failed polling recovery and scheduler independence, result retransmission,
manual idle denial, no overlapping autonomous work, existing seed 531 regression.
Acceptance: associated standby button causes one admitted exchange; polling failures
remain bounded and normal scheduling survives; live evidence or BLOCKED-HARDWARE.
Rollback: deploy `/opt/sherman-banter.previous` or disable banter; face unaffected.
Unresolved human decisions: none; stationary face admission limitations unchanged.
Evidence: `artifacts/phase-1/P1-JAR-003/RESULTS.md`; 14 deterministic tests, lint,
formatting, config and shell checks passed. Live polling succeeds for voice-example
and the concurrent face runtime remains healthy.

## P3-CTL-DRAFT: Pico 2 first firmware draft

Parent phase: 3 (F0/F1 draft; does not close G3).
Owner / integration reviewer: Codex, task b8d91453-38d4-4fd8-9746-42d57a4fbe1c.
Objective: buildable Pico 2 W1 diagnostic firmware, portable motion/safety core,
versioned UART contract, sensor acquisition, host tests, and access/recovery guide.
Non-goals: qualifying physical motion, changing wiring, Linux motion arbiter,
autonomous dock release (no assigned W1 GPIO), or deploying unrelated services.
Owned paths: firmware/controller/, proto controller schema/tools/fixtures/docs,
ADR 0009, firmware/protocol indexes, this packet, packet evidence.
Allowed dependencies: pinned Pico SDK, W1 netlist, sensor vendor documentation;
no high-level behavior can drive outputs. Prerequisites: ADR 0002/0005 and W1
design; physical P3-CTL-001/MOT/CLF/PWR gates remain open.
Tasks: freeze draft wire definition; portable parser/arbiter/control; W1 HAL,
sensors/watchdog/telemetry; build/diagnostic tools; access instructions.
Tests: host sanitizers, golden interoperability, malformed/replayed/stale input,
clock wrap, sensor/link/charge failure, deterministic control, netlist consistency,
Pico 2 cross-build. Bench if an identified device is available.
Acceptance: complete software draft and recoverable UF2; no physical motor
permission until hardware profile and calibration are qualified. Hardware-dependent
acceptance is BLOCKED-HARDWARE when no Pico is accessible.
Rollback: restore prior UF2 using BOOTSEL with motor branch disconnected; no
existing target or calibration is overwritten by this packet.
Unresolved decisions: measured polarity, gains, wheelbase, cliff/tilt/power bounds,
rail timing and stop margin belong to named physical qualification packets.
Evidence: `artifacts/phase-3/P3-CTL-DRAFT/RESULTS.md`. Software checks and Pico 2
cross-build complete; physical deployment/bench state is BLOCKED-HARDWARE.
No Pico/Debug Probe enumerated locally; `robot-host` SSH alias does not resolve.

## DOC-README-001: Public repository overview

Parent phase: cross-phase documentation; current Phase 1 bring-up.
Owner / reviewer: Codex README agent / repository integration owner, 2026-10-16.
Objective: Replace the planning-only root overview with a factual guide to the
implemented software, hardware design files, current limits, and local checks.
Non-goals: runtime changes, hardware qualification, changes to project targets,
release/deployment changes, or claims that roadmap gates have closed.
Prerequisites: existing subsystem implementations and committed verification docs.
Owned paths: `README.md` and this packet in `docs/agents/work-packets.md`.
Allowed dependencies/interfaces: existing repository files and public Jarvis link;
no new dependencies, protocols, secrets, or private network details.
Implementation tasks: inspect source/build/tests and phase plans; distinguish
implemented stationary features from planned autonomy; link representative code;
provide host-only build/test instructions and hardware-operation pointers.
Required tests/evidence: check all relative README links, run documented host
commands where available, and inspect the final diff for unsupported claims.
Acceptance criteria: a new reader can identify what exists, how it fits together,
how to exercise it without hardware, and what remains unqualified.
Completion: README updated against latest main `7290888`. Both documented native
builds passed (3 personality/emotion CTests and 2 renderer CTests); all documented
Python suites passed (8 renderer, 19 face integration, 7 backend, 20 dialogue).
The gallery command generated an image. All 33 relative README links resolve;
`git diff --check` passes. Checks used an isolated Python 3.11 environment and
build directories under `/tmp`; no hardware or deployed behavior changed.
Rollback: restore the previous root README and remove this packet.
Unresolved decisions requiring human review: none.
