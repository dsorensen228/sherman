# Phase 0 — Personality and Deterministic Simulator

## Outcome

A desktop application runs Sherman’s lifecycle, needs, moods, routines, Jarvis interactions, action arbitration, and animated eyes in a deterministic simulated world. It can record and replay a session and explain why an action was chosen. No hardware is required.

## Why this phase exists

Sherman’s distinguishing value is behavior, not locomotion. Phase 0 makes the product legible before hardware constraints make iteration slow. It also creates the fake clocks, schemas, event traces, world abstractions, and test scenarios that every later hardware adapter must satisfy.

## Entry conditions

- `GOALS.md`, system architecture, and v0 terminology reviewed.
- Product owner accepts the design principles and v1 non-goals.
- Program integrator, contract owner, and Phase 0 integration owner named.

## Deliverables

1. Host build with one-command test and simulator launch.
2. Versioned v0 event/action/expression/Jarvis schemas with C++ and Python golden fixtures.
3. Deterministic simulation kernel with fake monotonic/wall clocks, seeded random source, bounded event queue, scenario manifests, and trace writer.
4. Runtime lifecycle and action state machines.
5. Needs/mood model, behavior scoring/arbitration, routines, interruption/cancellation, and explanation tags.
6. Semantic eye-expression grammar, animation timeline, and desktop renderer.
7. Jarvis emulator supporting commands, questions, disconnect/reconnect, delays, duplicates, and invalid messages.
8. Scenario library and G0 evidence report.

## Behavioral model

### Internal state

Start with a small bounded vector: energy, curiosity, social engagement, confidence, frustration, and urgency. Values are normalized, updated on explicit ticks/events, clamped, and serializable. Mood is a derived, slowly changing presentation state; it must not secretly carry control state.

### Candidate actions

Examples: observe, look toward target, patrol waypoint, revisit uncertainty, inspect change, report, wait, rest, ask for help, react to pickup/blockage, and acknowledge Jarvis. Phase 0 uses simulated equivalents and records the action’s objective, costs, utility components, preconditions, resource claims, and deadline.

### Selection

Use an inspectable utility-based baseline before considering planning/learning. Score useful progress, novelty/information gain, routine pressure, social request priority, energy/time/motion cost, risk, repetition penalty, and recent failure. Apply hard admission constraints separately. Record the top candidates and score components so tuning is evidence-driven.

### Routines

Model time-of-day triggers, quiet hours, one-shot/recurring routines, missed-window policy, pause/resume, and cooldown. The accelerated clock must reproduce a day in minutes without changing ordering semantics.

### Expression

Define semantic channels: eye shape, pupil/iris position, blink, gaze, eyelid openness, squash/stretch, brightness, and reserved overlays. Map intent/mood/confidence/status to parameters, then animate through named clips with duration, easing, interruptibility, and priority. Avoid a one-off animation per behavior.

## Simulation scenarios

Minimum canonical scenarios:

- normal morning wake, initial scan, routine checkpoints, and summary;
- moved coffee mug creates uncertainty and an inspection;
- Jarvis asks for lost headphones, then cancels;
- Jarvis disconnects during a local task and later reconciles;
- repeated blocked path increases frustration but never bypasses safety;
- low energy interrupts curiosity and selects rest;
- pickup event cancels motion, changes expression, and requires placement recovery;
- contradictory observations create a change hypothesis;
- malformed/stale/duplicate Jarvis commands are rejected;
- 24-hour accelerated schedule respects quiet hours and duty limits.

Each scenario declares initial state, seed, timed inputs, expected invariants, allowed action sets, expression semantics, resource ceilings, and golden trace normalization.

## Implementation order and parallel agents

1. Contract agent lands schemas/fixtures.
2. Simulation agent builds clock/event/scenario/trace foundations.
3. Core agent builds lifecycle/action state machines against fakes.
4. Personality and display agents work in parallel against contracts.
5. Jarvis emulator agent creates failure and request fixtures.
6. Integration agent assembles the vertical slice.
7. Validation agent runs determinism, semantic expression, and accelerated-day suites.

Use packets `P0-*` in `docs/agents/work-packets.md`. No agent may invent a new global state field without schema/ownership review.

## Tests

- Unit/transition coverage for lifecycle, actions, needs, mood derivation, routines, animation timelines, and score components.
- Property tests: state remains bounded; canceled/expired actions do not complete; higher safety priority always preempts; queue/log growth remains bounded.
- Determinism: repeated run with same build/config/seed yields equivalent normalized trace; different seeds vary only allowed policy choices.
- Contract/fuzz tests for all messages.
- Golden expression frames plus semantic assertions at key timeline points.
- Blinded human review: viewers label at least the agreed core states above chance and identify fault/low-battery/privacy states reliably.
- Accelerated multi-day run: no runaway repetition, unbounded memory/storage, missed quiet hours, or action stuck past deadline.
- Restart tests: persisted behavioral/routine state resumes according to explicit policy, not mid-motion.

## Gate G0 acceptance

- All canonical scenarios pass from a clean build.
- Trace replay reproduces action and expression semantics.
- Every action is explainable from logged score/admission inputs.
- Jarvis is optional; outage and bad input do not break local behavior.
- Product owner approves a small expression vocabulary and three representative routines.
- Resource growth is bounded for an accelerated week.
- Architecture review confirms simulated adapters can be replaced by target adapters without changing behavior contracts.

## Explicit deferrals

No real vision, accurate physics, motor control, final map algorithm, NPU model, docking, audio, or production authentication. Simulator affordances must be labeled so they are not mistaken for physical capability.

