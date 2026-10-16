# Navigation Testing Plan

## Mathematical tests

Frame composition/inverse, timestamp lookup, angle wrap, differential-drive forward/inverse kinematics, integration under straight/turn/zero, covariance propagation sanity, footprint/inflation, grid/world conversion, collision checking and cost monotonicity. Use analytic and randomized property cases.

## Simulation scenarios

Exact routes in empty/obstacle maps; narrow/blocked/unknown/stale; near edge; localization uncertainty increase; wheel slip; IMU bias; landmark outliers; kidnapped robot; moving obstacle; route invalidation; goal cancellation; repeated oscillation/stuck and recovery limits. Assert no proposal beyond speed/zone/confidence rules.

## Replay and HIL

Feed controller telemetry with jitter/drop/reset/wrap and sensor/landmark replays. Verify pose/mode/uncertainty, deterministic decision trace, bounded runtime and no NaN divergence. HIL controller consumes proposed commands through actual protocol while simulated world returns telemetry/faults.

## Physical characterization

Marked/surveyed course: straight distance, 90/180/360 turns, square/loop, arcs, stop/restart at checkpoints, surfaces and battery states. Measure endpoint/drift, path error, wheel-speed saturation, current and slip. Tune only with configuration tied to hardware profile.

## Safety/recovery

Planner output remains subordinate to safety rejection/limiting. Test stale map/pose, cliff event during trajectory, controller fault, pickup, obstacle insertion, lost localization, repeated no-progress, Jarvis cancel and process restart. A restart never resumes motion automatically.

## Acceptance

Publish localization error/confidence calibration, map path success, clearance, replan/oscillation, recovery success/attempts/time, CPU/RAM/latency and physical intervention rate. Safety matrix must remain passing after every navigation change.

