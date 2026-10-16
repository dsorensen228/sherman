# Display Implementation Plan

## Expression grammar

Inputs: base mood, arousal, valence, confidence, gaze target/direction, attention strength, blink policy, action cue, and authoritative overlay. Outputs are parameter curves for eye centers/scale/aspect, pupil/iris position if used, eyelid openness/tilt, brow-like silhouette only if stylistically approved, brightness/color, and optional minimal icons.

Define named semantic clips: wake/self-test, idle breathing, blink, orient, track, curious inspect, think, pleased, uncertain, frustrated, tired/low battery, blocked, pickup, charging, privacy, updating, degraded, fault/help. Each has duration, entry/exit, priority, interruptibility, repeat/cooldown, and reduced-motion form.

## Timeline and arbitration

Separate long-lived expression state from short clips. Resolve priorities: fault/critical battery/privacy/update → lifecycle/degraded → action/attention → mood/idle. On preemption, transition to a safe canonical pose; do not strand parameters. Injected monotonic clock and deterministic blink/gaze random stream make replay exact.

## Renderer

Use resolution-independent vector/procedural shapes into an internal framebuffer; choose pixel format and scaling per backend. The selected target candidate is `320 × 170` landscape on the Waveshare 1.9-inch ST7789V2 module. Avoid heavy asset memory. Support orientation/rotation, safe face region, antialiasing tuned to target, dirty regions only if measured beneficial, and frame timing metrics. Render loop has bounded rate and drops old semantic updates rather than accumulating frames.

## Backends

- Host window/headless image sequence for Phase 0.
- Target primary: bounded RGB565 userspace SPI backend using `/dev/spidev0.0`, explicit ST7789V2 initialization/window writes, and GPIO/PWM for CS/DC/RST/backlight.
- Optional target optimization: maintained framebuffer/DRM/MIPI-DBI-style kernel path only after userspace measurement justifies it.
- Null/semantic capture backend for tests.

Backend reports readiness, dimensions/format, visible-frame completion when measurable, drops/transfer errors and power/brightness capability. Missing display degrades safely without blocking core.

## Display qualification

Implement a standard test animation: full-white/black, edges/text diagnostic (not product UI), gaze sweep, blink, rapid fault overlay, gradients/color, partial/full changes. Measure electrical/boot/driver, latency, FPS/tearing, CPU/RAM, power/thermal, brightness/viewing, cable/connector and lifetime. Initial candidate gates are `≥30` stable visible fps for the standard eye workload and `≤50 ms` semantic-event-to-visible latency. See `docs/hardware/display-selection.md` for transfer budgets and fallbacks.

## Accessibility and operations

Brightness/night/quiet policy, reduced motion, alternate status via Jarvis/logs, display self-test, stuck-frame detection where possible, and safe blank/dim on shutdown. Privacy indicator is clear and cannot be disabled by theme.

## Milestones

- D0 semantic schema/timeline and headless snapshots.
- D1 desktop renderer/animation lab.
- D2 Waveshare 1.9-inch Luckfox backend/qualification and ADR 0003 disposition.
- D3 authoritative overlay and action/gaze integration.
- D4 final grammar, brightness/reduced motion and endurance.
