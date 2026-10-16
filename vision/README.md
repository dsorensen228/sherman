# Vision and Perception

## Scope

`vision/` owns camera and front-range ingestion above firmware adapters, calibration application, time synchronization, bounded frame pipelines, feature/object observations, tracking, stationary/mobile scene-change evidence, recorded replay, and model/runtime wrappers.

It does not own raw camera drivers/device tree, global pose estimation, persistent world-belief policy, behavior decisions, motor safety, or unrestricted image streaming.

## Principles

Start with inspectable geometry/features and a vendor-supported camera. Every observation carries time, coordinate frame, confidence/uncertainty, provenance, calibration and model version, and quality flags. Raw imagery is transient by default. Optional inference is rate/resource limited and can be shed without losing sensor health or safety.

