# Personality Implementation Plan

## State model

Bounded normalized needs: energy, curiosity, social engagement, confidence, frustration and urgency. Update from explicit events/ticks using configuration with time constants, clamps and cooldowns. Mood is a filtered semantic projection (calm/curious/focused/pleased/uncertain/frustrated/tired), persisted compactly with version and restart policy.

## Candidate generation

Sources: routine due items, Jarvis requests, world change hypotheses, stale/uncertain areas, localization need, battery/return-home, self-test/recovery/help, and harmless idle attention. Each candidate declares goal, preconditions, expected information/task/social value, time/energy/motion/risk/repetition costs, urgency, interruptibility, deadline and required capabilities.

## Selection and arbitration

Compute inspectable utility components; apply hard constraints in core; select with small seeded variation only among near-equivalent safe candidates. Add hysteresis/commitment to avoid twitching and cancellation logic for higher priorities or invalidated context. Log top alternatives and explanation tags such as `routine_due`, `jarvis_priority`, `stale_map`, `change_confirm`, `low_energy`, `repetition_penalty`.

## Curiosity

Curiosity is question selection, not random motion. Generate questions from uncertainty/change/staleness and ask navigation/vision for estimated reachability, risk and observation value. Maintain novelty/revisit cooldown and global motion duty. Completing an inspection updates confidence; failure reduces immediate retry utility.

## Routines

Data-driven, timezone-aware schedules with window, priority, prerequisites, quiet compatibility, missed policy, cooldown, checkpoint list and summary. Morning example: wake/self-test → observe keyboard → coffee area → notebook → monitor base → report notable change or “no material change.” Do not hard-code a specific user’s schedule into engine code.

## Jarvis relationship

Map validated Jarvis tasks to candidates and produce concise progress/outcome facts with uncertainty. Humorous expression/dialogue cues are annotations over true status. Cancellation is honored; requests may be rejected/deferred with reason. Jarvis suggestions do not become personality memories unless the storage policy permits.

## Tuning/configuration

Personality packs are versioned, bounded configs with semantic regression suite. Expose a small reviewed surface (caution, curiosity, sociability, persistence, quietness) rather than raw dozens of coefficients. Changes produce trace comparison before deployment.

## Milestones

- P0 needs/mood and expression mapping.
- P1 candidate/utility/action explanations.
- P2 routine scheduler and Jarvis task mapping.
- P3 world-change/curiosity integration.
- P4 recovery/social nuance and bounded persistence.
- P5 final pack, nuisance/variety/endurance tuning.

## Current runtime

The implementation under `runtime/` provides the common policy foundation for
these milestones. It accepts caller-owned semantic candidates rather than
hard-coding world, routine or Jarvis adapters. Selection is bounded to 16
candidates and includes source/reason tags, a complete utility breakdown,
deterministic near-tie variation, repetition costs, minimum commitment and
hysteresis. Its steady-state C ABI does not allocate and is suitable for both
the current Python display supervisor and a future native `shermand`.

The autonomous idle layer uses injected monotonic/local time and seeded random
state. It generates settled/orient/observe presence when no adapter is present,
then yields to valid attention, task, interaction, outcome, pause and quiet
semantics. It never invents a sensor target or produces an actuator command.

The data-driven routine scheduler owns bounded windows, skip/catch-up policy,
quiet compatibility, cooldown and checkpoint progress. It receives explicit
civil day/local-second input but uses monotonic time for cooldowns. Completed
occurrence IDs prevent replay through repeated or backward civil-time changes.
No user schedule or physical completion is inferred by the scheduler.
