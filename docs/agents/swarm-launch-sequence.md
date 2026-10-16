# Swarm Launch Sequence

## Principle

Parallelize behind stable contracts and fakes; serialize shared-schema, composition and physical-authority changes. The waves below are the recommended first execution order.

## Phase 0 launch

### Wave 0 — human/integration setup

Name program integrator, contract owner and reviewers. Choose root build/test scaffolding packet ownership. Confirm language/wire-format ADR spike and v0 terminology. No agent implements private ad-hoc schemas.

### Wave 1 — contract lane (serialized)

Agent A: `P0-CON-001` defines common/event/action/expression/Jarvis schemas, validation and cross-language golden fixtures. Reviewer checks units/time/unknown/expiry/compatibility. Merge before dependent public interfaces.

### Wave 2 — foundations (parallel after Wave 1)

- Agent B: `P0-SIM-001` deterministic clock/event/scenario/trace kernel.
- Agent C: `P0-CORE-001` lifecycle/action state machines using fake clock.
- Agent D: `P0-DSP-001` semantic expression grammar/timeline with headless tests.

Owned paths do not overlap; shared build changes go through integrator. Merge fakes/fixtures before implementation consumers.

### Wave 3 — behavior and surfaces (parallel)

- Agent E: `P0-PER-001` needs/mood state.
- Agent F after E interface: `P0-PER-002` utility/arbitration/explanation.
- Agent G: `P0-DSP-002` desktop renderer/goldens.
- Agent H: `P0-JAR-001` Jarvis emulator and network failure scenarios.
- Agent I: test infrastructure/traceability harness, separate owned paths.

### Wave 4 — integration (serialized around composition)

Integration owner executes `P0-INT-001`, resolves contract-compliant wiring only, and opens defects back to owners rather than absorbing logic. Run canonical scenarios and resource baseline.

### Wave 5 — independent validation

Validation/review agent executes `P0-VAL-001`: repeat determinism, accelerated week, invalid inputs, expression legibility packet and G0 traceability. Human owner reviews product behavior before G1.

## Later-phase concurrency lanes

### Phase 1

After board baseline: build/platform, display bake-off, transport, and storage spike can run in parallel. Display candidate agents share one benchmark/protocol but not backend files. One target integration owner controls image/composition.

### Phase 2

Camera and ToF bring-up run in parallel; calibration/synchronization waits for both contracts. Perception can develop from synthetic/replay fixtures before hardware capture. Privacy audit is independent.

### Phase 3

Controller/protocol, motor characterization, cliff characterization, power characterization and M0 CAD can run in parallel only on isolated safe benches/models. Exact power/harness/chassis freeze waits for measurements. Safety owner serializes arm/authority/free-motion progression.

### Phase 4

Frames/pose contract first; simulation map/planner, localization replay, world-belief/change and behavior curiosity can then run in parallel. Physical integration follows simulator/replay acceptance.

### Phase 5

Personality pack, routines, final expressions, Jarvis scenarios and operations tooling run in parallel behind frozen semantics. Endurance and release candidate are serialized evidence activities.

## Capacity guidance

With four agents: one integration/contract lane plus three independent subsystem lanes. With more agents, add reviewers, fixtures/fault injection, documentation/evidence and candidate bake-offs before splitting shared implementation. More agents on the same files usually reduce throughput.

## Merge checks per wave

Owned-path compliance; schema compatibility; unit/contract tests; relevant deterministic scenarios; no relaxed safety/privacy/resource bounds; docs/traceability; exact handoff/artifacts; green integration baseline before next wave.

