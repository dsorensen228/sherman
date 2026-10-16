# Personality and Behavior Policy

## Scope

`personality/` owns bounded needs/mood state, behavior candidate generation/scoring, routines, curiosity/revisit priorities, social/Jarvis interaction style, expression intents, cooldown/repetition controls and explainability.

It does not own lifecycle/safety admission, motor commands, perception truth, world storage, transport, or authoritative fault/privacy state. Personality may propose and present; it cannot fabricate facts or overrule constraints.

## Character statement

Sherman is curious, earnest, persistent, slightly fussy about his desk, pleased by useful discoveries, mildly indignant when picked up or blocked, and quietly fond of Jarvis. He is not reckless, needy, manipulative, omniscient, or falsely confident.

## Implemented foundation

- `emotion/` owns bounded durable needs and slowly changing presentation mood.
- `runtime/` owns the deterministic autonomous idle controller, stable C ABI,
  and inspectable bounded candidate policy for routines, Jarvis, world changes,
  recovery and local curiosity.

See `runtime/README.md` for integration contracts and explicit safety/storage
boundaries.

`banter/` adds generated idle exchanges with Jarvis for the stationary prototype,
including procedural beep speech, randomized timing and a configurable reply speaker.
See `banter/README.md` and ADR 0006.
