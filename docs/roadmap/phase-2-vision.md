# Phase 2 — Stationary Vision and Scene Model

## Outcome

Stationary Sherman captures synchronized camera and multizone range data, produces calibrated observations/tracks/change hypotheses with confidence and provenance, persists a bounded local scene model, and reports useful summaries to Jarvis without retaining raw imagery by default.

## Entry conditions

- G1 accepted with resource headroom and stable target build.
- Vendor-supported camera and candidate VL53L5CX breakout received/recorded.
- Privacy default and debug-capture consent behavior reviewed.
- Calibration fixtures and representative desk target set defined.

## Work packages

### Camera pipeline

Begin with a vendor-supported MIPI CSI sensor/module and known image pipeline. Expose timestamped frames through a bounded buffer pool with explicit pixel format, dimensions, exposure/gain, dropped-frame counters, and privacy state. Measure sensor/ISP/encode/copy latency and memory at representative resolutions/rates; do not start at maximum.

### ToF pipeline

Bring up exact breakout, verify voltage/level shifting, reset/interrupt, I2C rates, 4×4/8×8 modes, ranging frequency, target status, ambient/spad/quality fields, self-heating, and recovery from bus/device faults. Represent every zone with calibrated direction/FOV, range, uncertainty/status, and timestamp.

### Calibration and synchronization

Build repeatable camera intrinsics, lens distortion, camera↔ToF extrinsics, faceplate/window, and range offset/crosstalk procedures. Record profile ID, hardware IDs, fixture/version, ambient conditions, residuals, and validity bounds. Establish Linux clock behavior, acquisition latency, and synchronization tolerance; a fused observation carries time uncertainty.

### Perception baseline

Start with cheap, inspectable features: motion/scene difference, edges/regions, selected object categories only when a representative model fits the budget, and ToF geometry. Rate-limit optional NPU inference and shed it before sensor health/eyes. Every output has model/version, confidence, source frame IDs, coordinate frame, and quality flags.

### Tracking and change

Associate observations over time into local tracks with existence probability, geometry, semantic hypotheses, last-seen time, and merge/split lineage. Compare against the stored stationary scene using confidence-aware hypotheses: new, removed, moved, uncertain, or lighting/view change. Require repeated/supporting evidence before destructive updates.

### Stationary scene model

Use a local coordinate frame fixed to the test mount. Store nearby range/occupancy samples, landmarks/features, object beliefs, and change hypotheses through the repository interface. Support snapshot/restart/replay, age/decay, and explicit clear/export.

### Privacy and diagnostics

Raw camera frames remain in bounded transient buffers. Debug recording is visible, authenticated/locally authorized, time/size limited, and stored separately with retention metadata. Test logs and support bundles use synthetic/cropped/redacted data when possible.

## Fixture matrix

Include matte/glossy black/white/color objects; thin cable/pencil; transparent/translucent object; textured/blank background; monitor/keyboard/mug/notebook; near/far/partially occluded targets; daylight/office/dim and display-on leakage; no-change and controlled moved/added/removed cases. Mark which materials are unsupported rather than manufacturing confidence.

## Performance characterization

For each selected pipeline mode record sensor rate, end-to-end latency, drops, CPU/RAM/NPU usage, temperature, power, queue depth, and display/network interference. Choose an operating point that preserves safety headroom for Phase 3. Store raw/processed sample pairs only as a governed qualification dataset.

## Tests

- Driver unit/integration and replay equivalence.
- Calibration repeatability after disassembly/reassembly and temperature change.
- Synchronization under load and clock adjustment.
- Invalid quality/status, I2C fault/stuck bus, camera dropout/corrupt frame, missing calibration.
- Labeled fixture precision/recall or error distributions with explicit unknown class.
- Track identity, merge/split, occlusion, disappearance, and time decay scenarios.
- Change false-positive control under lighting/exposure/view changes.
- Storage interruption, migration, bounded growth, clear/export.
- Network/storage audit proves raw frames are absent unless capture mode is enabled.
- Eight-hour stationary perception soak with reconnect/display active.

## Coherent demo

From a calibrated stationary mount, Sherman displays attentive eyes, observes a known desk arrangement, reports a compact scene summary, sees a mug moved and creates a change hypothesis, confirms it on reobservation, informs Jarvis with confidence/age, survives a sensor unplug/restart, and replays the recorded synthetic/approved session deterministically.

## Gate G2 acceptance

- Camera/ToF modes and calibration procedure are reproducible.
- Controlled fixture metrics meet agreed baselines; unsupported cases are documented.
- Observations/tracks carry complete time/frame/confidence/provenance.
- Resource and thermal profile leaves Phase 3 motion/safety headroom.
- Restart/power-loss preserves last-good scene/calibration.
- Raw imagery is transient by default and privacy controls pass audit.
- A replay bundle reproduces semantic outputs within documented tolerances.

## Deferrals

No mobile localization, global map, autonomous object search, final NPU model, or docking. Keep the stationary mount coordinate frame separate from future robot/world frames.

