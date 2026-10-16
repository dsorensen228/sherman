# Swarm Execution Guide

## Goal

Allow many coding agents to advance Sherman without creating incompatible subsystems, unsafe shortcuts, or an integration owner who must reverse-engineer their work.

## Roles

- **Program integrator:** owns phase plan, dependency graph, root build, shared CI, and gate packet.
- **Contract owner:** owns `proto/`, generated compatibility fixtures, and interface review.
- **Safety owner:** owns safety claims, controller boundary, physical-test progression, and veto on motion authority changes.
- **Subsystem owner:** owns one directory’s implementation/test plan and work packets.
- **Test/evidence owner:** owns scenario/replay/HIL infrastructure and acceptance traceability.
- **Hardware integrator:** owns receiving records, pin/bus/power/mechanical configuration and bench safety.
- **Reviewer:** does not author the packet under review; verifies evidence and boundary compliance.

One person or agent can hold multiple roles in small phases, but author and final reviewer should differ for safety-critical work.

## Parallelization pattern

Parallel work is safe after a contract and fixtures exist. Example Phase 0 branches:

- behavior state machine and needs;
- eye renderer and expression grammar;
- simulator world/time/event runner;
- schema definitions and Jarvis emulator;
- deterministic replay/evidence tooling.

The contract owner lands schemas and golden fixtures first. Each branch implements against fakes, then the integrator combines them through a named integration packet.

## Merge order

1. ADR/requirement updates.
2. Schema/interface plus compatibility tests.
3. Fakes/simulators and shared fixtures.
4. Producer/consumer implementations independently.
5. Integration tests.
6. Hardware adapter behind the already-tested interface.
7. Performance/safety evidence and phase docs.

## Agent prompt checklist

Give each agent:

- exact packet text and prerequisite commit/build IDs;
- owned and forbidden paths;
- relevant docs and interface versions;
- target environment and allowed dependencies;
- acceptance tests and commands;
- artifact output location;
- stop/escalation conditions;
- expected handoff format.

Avoid “implement Phase 3” prompts. A packet should normally fit one reviewable change and have one primary objective.

## Escalate instead of guessing

Stop and file a decision/risk when exact pin voltage, part revision, motor limits, battery behavior, privacy policy, coordinate frame, message semantics, safety timeout, mechanical datum, or calibration ownership is missing or contradictory.

## Handoff template

1. Packet ID/objective and final status.
2. Files changed and interfaces consumed/produced.
3. Tests executed with exact command/result and artifact path.
4. Resource/performance changes.
5. Deviations from plan and ADR links.
6. Residual risks, hardware blockers, and follow-up packet IDs.
7. Rollback method.

