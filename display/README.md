# Display and Eye Expression

## Scope

`display/` owns the semantic expression model, eye layout, gaze/blink/eyelid animation timelines, compositing of authoritative status overlays, renderer, host and target display backends, assets/themes, brightness/power policy hooks, screenshots and visual diagnostics.

It does not own mood/behavior selection, safety decisions, display device-tree/platform code, or arbitrary remote pixel streaming. Personality requests semantics; core supplies authoritative lifecycle/fault/privacy overlays; display resolves visual priority deterministically.

## Product principle

Eyes should reveal attention, intent, uncertainty and state at a glance. Character comes from timing/gaze/proportion, not a large library of unrelated cartoons. Safety and privacy states must never be hidden by cute animation.

The Phase 1 hardware target is the Waveshare 1.9-inch `320 × 170` landscape ST7789V2 module. Its selection, fallback ladder, bus budget, and evidence gates are in `docs/hardware/display-selection.md` and ADR 0003.
