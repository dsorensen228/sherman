# Vision Implementation Plan

## Pipeline stages

1. **Acquire:** receive immutable camera/ToF buffer handles plus acquisition metadata; no hidden copies.
2. **Validate:** dimensions/format, timestamps, calibration IDs, sensor status, exposure/range quality, sequence/drop counters.
3. **Synchronize:** associate streams within configurable tolerance and preserve unmatched data when useful; attach time uncertainty.
4. **Preprocess:** lens correction/resize/color conversion/range filtering using bounded buffer pool.
5. **Extract:** geometric/visual features, motion/scene difference, range surfaces, optional object inference.
6. **Project/fuse:** transform to calibrated sensor/base frame and combine supporting evidence without overstating certainty.
7. **Track:** association, state/existence update, occlusion, merge/split and last-seen metadata.
8. **Emit:** immutable observations/tracks plus performance/quality metrics; never mutate world state directly.

## Calibration package

Define camera intrinsics/distortion, sensor resolution/crop, camera↔ToF/base extrinsics, range offset/crosstalk and cover-window profile, calibration temperature/time/hardware IDs/residuals. Provide capture, solve, validate, compare, activate, and invalidate tools. Runtime refuses fusion on incompatible profile; degraded single-sensor output is labeled.

## Baseline algorithms

Phase 2 first: robust difference/region proposals, range grid interpretation, simple descriptors/features, and a small selected object set only if target measurements pass. Use confidence calibration from fixture results. Tracking may start with gated nearest-neighbor/Kalman-like state for geometry, but interface must support multiple hypotheses/unknown without class certainty.

Phase 4 adds motion compensation through supplied poses, world-coordinate observation candidates, viewpoint/occlusion reasoning, landmark descriptors, and change evidence. Vision reports evidence; world model decides persistence/change.

## Model lifecycle

Every model has source/license, input contract, preprocessing, quantization, target runtime/NPU version, checksum, performance/accuracy fixture results, memory/thermal/power, fallback, and compatibility. No opaque download at runtime. Invalid/slow model disables itself or reduces rate through resource policy.

## Buffer/resource design

Fixed-capacity pools and queues; latest-frame or explicit drop policy; no unbounded history; separate fast quality/ToF path from optional slow inference; measure every stage. Backpressure cannot stall sensor health or display/core. Diagnostic capture copies intentionally into a governed capped store.

## Milestones

- V0: schemas, replay reader, synthetic fixtures.
- V1: camera and ToF acquisition/quality separately.
- V2: calibration/synchronization and fused observation baseline.
- V3: tracking/change evidence and stationary scene demo.
- V4: target inference/model candidate, if justified.
- V5: mobile motion compensation/landmarks and release tuning.

