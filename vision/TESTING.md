# Vision Testing Plan

## Unit/property

Pixel/range conversions, coordinate transforms, distortion, interpolation, timestamps, association gates, confidence/decay, track lifecycle, buffer ownership and drop policy. Fuzz formats/sizes/stride/status, invalid calibration, NaN/inf/extreme range and sequence discontinuity.

## Calibration

Repeat capture/solve across operators, reassembly, temperatures and lighting. Measure reprojection/range/extrinsic residuals and downstream alignment. Deliberately load wrong sensor/resolution/hardware profile and require rejection. Test faceplate optical effects, display light leakage and window contamination.

## Fixture dataset

Version synthetic plus approved real captures for near/far, matte/glossy/dark/light/transparent/thin objects, partial occlusion, motion, blank/repetitive background, multiple lighting/exposure and no-change controls. Separate train/tune from held-out qualification if learned models are used.

## Metrics

Per category/condition: detection/observation precision-recall, position/range error, confidence calibration, track identity/fragmentation, change precision/recall/delay, drop/latency, CPU/RAM/NPU, thermal/power. Publish unsupported conditions.

## Fault/replay

Camera/ToF dropout, delay, rate change, corrupted frame, stuck sequence, I2C recovery, stale calibration, time skew, exposure jump, queue pressure, model crash/timeout and resource shedding. Recorded replay must reproduce semantic results within tolerances.

## Privacy

Network/storage/log scans during normal operation prove no raw frames. Enable diagnostic capture and verify visible state, authorization, time/size cap, retention, manifest and erase. Ensure crash/support bundles redact/exclude frames.

## Target endurance

Eight-hour stationary and representative mobile runs with eyes/network/storage active. Track leaks, fragmentation, drops, thermal throttling, restart recovery and calibration consistency.

