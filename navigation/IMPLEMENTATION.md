# Navigation Implementation Plan

## Coordinate frames

Implement explicit timestamped transforms among `world/map`, `odom`, `base`, camera, front ToF, IMU and cliff frames. Use the repository coordinate convention. Pose always includes uncertainty/confidence and mode. Transform lookup fails if stale/incompatible rather than extrapolating silently.

## Odometry and calibration

Consume controller encoder/IMU telemetry. Calibrate wheel radius/track width/direction/counts over repeated straight/turn courses and surfaces. Integrate with midpoint/exact differential-drive model as appropriate and propagate uncertainty from tick quantization, slip and timing. Detect impossible deltas/clock gaps.

## Localization

Start with encoder+gyro prediction; add selected visual/range landmark/map corrections. Use an inspectable filter/graph approach fitting target resources. Track innovation/outlier rejection, covariance/confidence, and modes `LOCALIZED`, `UNCERTAIN`, `RELOCALIZING`, `LOST`. Manual relocation and wheel slip must be detectable or cause conservative loss state.

## Map/traversability interface

Consume world model occupancy/boundary/no-go/age/confidence. Inflate by measured footprint and uncertainty margin. Unknown and stale edge-adjacent areas are high cost or forbidden. Keep planner map resolution/memory bounded; support local rolling view and simplified topology if full fine grid is too expensive.

## Planning

Global candidate route plus local differential-drive trajectories. Costs: collision/edge clearance, unknown/stale, pose uncertainty, reverse/turn, path length/time/energy/noise, repeated disruption, recovery history. Validate route continuously and attach an allowed speed envelope based on confidence/clearance.

## Progress and recovery

Measure commanded versus odometric progress, distance-to-goal trend, oscillation, replans, slip/current/fault cues. Recovery ladder is stateful, attempt-limited and logged: stop/reobserve; small qualified retreat/turn; alternate route; relocalize; cancel/return/help. No random exploratory motion near uncertain boundary.

## Docking

V1 requirement. Separate coarse route, homing cue, contact approach, alignment, charge detection and abort. Controller remains armed only for bounded approach and disarms before contact/charge. Dock absence, failed contact proof, or loss of dock power must leave motors disabled and must not strand Sherman in an unsafe state.

## Milestones

- N0: frames, kinematics, simulator model and tests.
- N1: controller telemetry/odometry calibration.
- N2: map interface, footprint, static planning simulation.
- N3: localization fusion and confidence modes/replay.
- N4: physical low-speed path following and replan.
- N5: recovery/curiosity integration.
- N6: v1 docking and endurance tuning.
