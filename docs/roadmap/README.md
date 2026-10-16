# Phase Roadmap

Each phase is a vertical slice with an entry gate, explicit work packages, negative/fault tests, a coherent demo, and an evidence-based exit review. Phases may prototype future work, but the next phase cannot depend on an unclosed current-phase gate.

| Phase | Plan | Hardware state | Exit demonstration |
| --- | --- | --- | --- |
| 0 | `phase-0-personality.md` | none | deterministic desktop Sherman and Jarvis emulator |
| 1 | `phase-1-brain.md` | board + display | real eyes, target runtime, resilient Jarvis link |
| 2 | `phase-2-vision.md` | stationary sensors | calibrated observations and local scene model |
| 3 | `phase-3-mobility.md` | restrained then mobile chassis | safe, characterized desk motion |
| 4 | `phase-4-world-model.md` | mobile platform | persistent map, change detection, curiosity/recovery |
| 5 | `phase-5-character.md` | integrated v1 candidate | reliable daily routine and v1 release packet |

## Gate labels

- **G0 Concept:** behavior and interfaces are coherent enough for hardware.
- **G1 Platform:** target board, display, build, deployment, and transport are reliable.
- **G2 Perception:** stationary sensing is calibrated, replayable, bounded, and private by default.
- **G3 Motion:** power, real-time stop, drivetrain, cliff avoidance, and chassis are qualified.
- **G4 Autonomy:** mapping, localization, change, curiosity, and recovery meet controlled trials.
- **G5 v1:** endurance, daily experience, operations, privacy, and documentation are release-ready.

Every gate may be `GO`, `CONDITIONAL GO` with named conditions, or `NO GO`. A conditional go may authorize independent later work but cannot waive a safety dependency.

