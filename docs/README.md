# Documentation Map

## Product intent

- `../GOALS.md` — mission, design principles, measurable outcomes and non-goals.
- `product/experience-spec.md` — intended daily experience and behavioral acceptance.
- `product/industrial-design-brief.md` — physical/visual intent and concept-art boundaries.
- `product/jarvis-relationship.md` — authority and interaction contract.

## Plan and architecture

- `overall-plan.md` — delivery model, workstreams, gates, procurement and risks.
- `roadmap/` — detailed Phase 0–5 plans.
- `architecture/` — runtime architecture, contracts and persistence/replay.
- `decisions/` — accepted/proposed ADRs.

## Hardware and assurance

- `hardware/` — complete phased shopping list, 1.9-inch landscape display selection, BOM qualification, mechanical envelope, power/thermal, pins/buses and vendor sources.
- `safety/hazard-analysis.md` — preliminary hazards, controls and release blockers.
- `testing/` — layered verification strategy and acceptance traceability.

## Swarm and operations

- `agents/` — roles, packet backlog, merge order and integration playbook.
- `operations/` — build/release, observability/support and data/device operations.
- Every code/artifact area has its own `README.md`, `IMPLEMENTATION.md` and `TESTING.md`.

## Document authority

In conflicts: safety requirements and accepted ADRs win; then canonical schemas/contracts; then active phase plan; then subsystem plan. Resolve real conflicts through an ADR or documented plan change rather than silently picking one.

All measured claims identify hardware/build/config/calibration and evidence. Proposed targets are labeled; concept art is never engineering evidence.
