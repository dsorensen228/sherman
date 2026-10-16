# Agent Operating Contract

This file is authoritative for every coding agent working in this repository.

## Mission discipline

Optimize for a safe, testable, characterful robot—not for maximum algorithmic novelty. A change is complete only when its required evidence exists. If a plan and the implementation disagree, either update the plan through a recorded decision or stop and escalate the conflict.

## Before starting

1. Read the root `README.md`, `GOALS.md`, and the active phase plan.
2. Read the `README.md`, `IMPLEMENTATION.md`, and `TESTING.md` in every directory you will modify.
3. Read `docs/architecture/contracts.md` before changing an interface or message.
4. Read `docs/decisions/README.md`; create an ADR for a costly, cross-cutting, safety-relevant, or hard-to-reverse decision.
5. Claim a work packet in `docs/agents/work-packets.md`. Do not broaden its scope silently.

## Work packet format

Every assignment must state:

- packet ID and parent phase;
- objective and non-goals;
- owned paths;
- allowed dependencies and interfaces;
- prerequisite packet IDs;
- implementation tasks;
- required tests and evidence;
- completion and rollback criteria;
- unresolved decisions requiring human review.

## Ownership and concurrency

- One agent owns a file at a time. Shared schemas, build files, and root documentation require an integration owner.
- Prefer new files behind existing interfaces over concurrent edits to shared files.
- Schema changes start in `proto/`, include compatibility fixtures, and land before consumers.
- Agents must not change mechanical dimensions, voltage domains, GPIO assignments, safety thresholds, or public message semantics without an ADR and downstream-owner review.
- Generated files are never hand-edited. Record the generator and source.

## Engineering rules

- In project prose, “the Pico” means the Raspberry Pi Pico 2 and “the Luckfox”
  means the Luckfox Pico Ultra W. Never shorten the Luckfox board to “the Pico.”
- Use deterministic clocks, seeds, and sensor replay wherever possible.
- Keep hardware access behind interfaces with a simulation implementation.
- No behavior may bypass the safety arbiter to command motors.
- Loss of localization, transport, a sensor, or Jarvis must degrade locally and safely.
- Network access is optional for safe local operation.
- Use explicit units in names and schemas (`distance_mm`, `age_ms`, `voltage_v`).
- Attach timestamps and provenance to observations and derived world-state.
- Bound queues, retries, memory, log volume, and actuator commands.
- Treat all external inputs—including Jarvis messages—as untrusted and validate them.

## DIY hardware fault policy

- Sherman is a module-level DIY build, not a board-repair or laboratory-instrumentation project.
- For a suspect purchased module, perform one bounded pass covering visible damage, connector seating, polarity, continuity, supply/configuration, and a minimal known-good test.
- Swap in the known-good spare or replacement next. If the fault follows the module, quarantine and replace it; do not spend agent time reverse-engineering or reworking an inexpensive PCB.
- Deeper diagnosis is justified only when the same fault survives a module swap, indicating a shared wiring, power, software, protocol, or mechanical problem; or when safety evidence would otherwise be invalid.
- Do not propose buying specialty instruments to save a low-cost replaceable part. Borrow access only for a specific unresolved system-level failure.
- A replaced safety-relevant module must repeat its receiving and affected integration tests; replacement is cheaper than repair, not a waiver of verification.

## Definition of done

A packet is done only when:

- code or artifact satisfies its acceptance criteria;
- specified unit, contract, integration, and regression tests pass;
- static analysis and formatting pass;
- relevant simulation scenario passes with a recorded seed;
- hardware-dependent work includes bench evidence or is explicitly marked `BLOCKED-HARDWARE`;
- metrics/logs make success and failure diagnosable;
- documentation and traceability are updated;
- no new safety-critical TODO is hidden in code;
- the handoff names residual risks and exact follow-up packets.

## Evidence format

Put packet evidence under `artifacts/<phase>/<packet-id>/` when implementation begins. Include a short `RESULTS.md`, machine-readable test output, relevant logs, plots, photos, and build identifiers. Do not commit secrets, raw private camera captures, or large unbounded logs.

## Review priorities

Review in this order: human/desk safety, hardware risk, data-contract compatibility, deterministic correctness, resource use, failure recovery, maintainability, then style.
