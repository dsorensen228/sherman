# Coding-Agent Prompt Template

Copy this template into an agent assignment and replace every bracket. Attach only the relevant docs/fixtures; do not ask an agent to infer a whole phase.

```text
You are implementing Sherman work packet [PACKET-ID]: [TITLE].

Objective
[One concrete outcome.]

Context to read first
- /absolute/path/to/sherman/AGENTS.md
- /absolute/path/to/sherman/GOALS.md
- /absolute/path/to/sherman/docs/roadmap/[active-phase].md
- /absolute/path/to/sherman/[owned-subsystem]/README.md
- /absolute/path/to/sherman/[owned-subsystem]/IMPLEMENTATION.md
- /absolute/path/to/sherman/[owned-subsystem]/TESTING.md
- [contracts/ADRs/fixtures]

Prerequisites
- [packet/build/schema/profile IDs and expected state]

Scope and owned paths
- You may edit: [exact paths]
- You may add: [exact subtree]
- Do not edit: [shared/forbidden paths]
- Non-goals: [explicit]

Contracts and constraints
- Consume/produce: [schema/interface versions]
- Units/frames/clocks: [exact]
- Resource/safety/privacy bounds: [exact]
- Allowed dependencies: [exact or none]

Implementation tasks
1. [task]
2. [task]
3. [task]

Required tests and evidence
- [unit/property/contract/simulation/replay/HIL/physical]
- Exact acceptance: [measurable]
- Put results under: artifacts/[phase]/[packet-id]/

Stop and escalate if
- [missing decision/hardware/voltage/schema/safety issue]

Handoff
Return packet status, files changed, interfaces, exact test commands/results, resource impact, deviations/ADRs, residual risks/follow-ups, artifact paths and rollback.
```

## Review-agent variant

Give the reviewer the packet, diff, evidence and requirements. Ask for findings ordered by safety, compatibility, correctness, resources, recovery and maintainability. The reviewer should not expand product scope or rewrite style without a defect. Safety-critical packets require review independent of the author.

