# Contributing

Sherman begins as a plan-first hardware/software project. Before changing anything, read `AGENTS.md`, the active phase plan, and the three files in every subsystem you touch.

## Change sequence

1. Claim or write an agent-sized packet.
2. Confirm interfaces, requirements and owned paths.
3. Add or update tests/fixtures before or with implementation.
4. Implement behind existing boundaries; use fakes before hardware.
5. Run required unit/contract/simulation/integration tests.
6. Record exact evidence and residual risks.
7. Update docs/traceability/ADR when behavior or decisions change.
8. Hand off with rollback and follow-up packet IDs.

Do not merge direct motor control outside firmware/controller, permissive fallbacks for invalid safety data, unbounded queues/logs/captures, raw private imagery, embedded secrets, silent schema breaks, or hardware claims without exact part/revision and evidence.

Commit/PR conventions can be chosen when source development starts; keep packet ID visible in branch/change metadata and evidence.

