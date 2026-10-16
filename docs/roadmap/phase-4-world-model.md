# Phase 4 — Localization, World Model, Curiosity, and Recovery

## Outcome

Sherman patrols a qualified desk, maintains an uncertainty-aware persistent map and object beliefs, notices controlled changes, chooses useful revisits, recovers from bounded failures, and asks Jarvis/human for help when confidence or reachability is insufficient.

## Entry conditions

- G3 accepted with frozen mobile hardware profile and safety envelope.
- Robot/camera/ToF/IMU/encoder frames and calibrations are versioned.
- Deterministic kinematic/sensor simulation and mobile replay available.
- Test desk has surveyed boundaries, landmarks, obstacles, and controlled-change fixtures.

## Coordinate and belief foundations

Define frame graph (`world`, `map`, `odom`, `base`, sensor frames), timestamped transforms, covariance/confidence, and reset/relocalization semantics. `odom` is locally smooth and drifts; `map` can correct; no consumer assumes pose certainty. All observations retain the pose distribution used for fusion.

## Work packages

### Odometry and localization

Calibrate effective wheel radii/track width over surfaces and battery loads. Fuse encoder/IMU prediction with range/visual landmark corrections using an inspectable baseline suited to resources. Track innovation, covariance/confidence, slip and kidnapped/moved detection. Provide modes: localized, uncertain, relocalizing, and lost.

### Occupancy and traversability

Represent desk boundary/occupied/free/unknown with resolution justified by robot footprint and sensor error. Include inflation/footprint, observation age, source/confidence, and forbidden/no-go zones. Edge safety remains controller/local; the map adds conservative planning, never replaces cliff reflexes.

### Planning and control

Start with a global/topological or grid route and bounded local trajectory selection compatible with differential drive. Cost collision/edge margin, uncertainty, turn/reverse, path length, energy, noise, repeated disturbance, and recovery risk. Continuously validate freshness and abort/replan on changed world/health.

### Persistent object world

Transform stationary Phase 2 tracks into world beliefs with existence probability, location uncertainty, class hypotheses, last-seen conditions, and lineage. Separate observation from belief. Conflicts create change hypotheses; confirm before declaring moved/removed. Decay rates differ for static boundary, landmarks, and portable objects.

### Curiosity and information gain

Build candidate questions from stale map cells, unresolved changes, lost object beliefs, localization needs, and routine checkpoints. Estimate information value, task/social value, motion/energy/time/risk cost, novelty and repetition. The behavior engine selects a bounded inspection objective and can explain the choice.

### Recovery ladder

Detect no-progress, excessive slip, oscillation, repeated replans, localization loss, blocked route, sensor degradation, and power risk. Recovery is bounded: stop → reassess → small safe retreat/turn if qualified → alternate plan → relocalize → return home → ask for help/disarm. Cap attempts and never random-walk near uncertain edges.

### Docking decision

Docking is the fast follow to V1 cable charging and is mandatory. Define rear-entry geometry so Sherman backs in, homing sensors/markers, four-contact pilot/power/release handshake, alignment retries, abort behavior, automatic hardware motion inhibit, charge policy, dock-power removal, verified release, and autonomous forward drive-off. Manual placement is acceptable only during commissioning; no released workflow may require battery handling, a motor switch, shutdown, or human departure assistance.

## Scenario matrix

- repeated loop returns to landmarks with quantified drift/correction;
- feature-poor and visually repetitive regions;
- wheel slip/temporary lift and manual relocation (“kidnap”);
- new/moved/removed object with occlusion and false-change lighting control;
- route blocked after planning;
- stale region selected for revisit, then confidence increases;
- sensor/model degradation causes slower or refused motion;
- storage restart preserves compatible map and rejects mismatched calibration/hardware;
- object-search request returns found/not-found/uncertain honestly;
- stuck fixtures recover or request help within bounded attempts;
- Jarvis disconnect during task and later state reconciliation.

Run every logical scenario first in deterministic simulation, then replay/HIL, then a selected physical subset.

## Metrics

Pose/heading error at surveyed checkpoints; loop consistency; map boundary/obstacle precision; collision/edge clearance; replans/oscillation; change detection precision/recall/delay; object belief calibration; uncertainty consistency; inspection information gain; path/time/energy cost; recovery success/time/attempts; storage size/write rate; CPU/RAM/thermal/power.

## Coherent demo

Start from persisted state, localize, patrol routine landmarks, show a moved notebook, detect/confirm/report it, choose a stale area to revisit, encounter a new obstacle and replan, suffer a controlled slip/localization confidence drop and recover, lose Jarvis and continue safely, then return home or request placement/charge with an honest summary.

## Gate G4 acceptance

- Surveyed repeated-patrol metrics meet approved map/localization usefulness thresholds.
- Uncertainty is calibrated enough that loss/degradation triggers conservative behavior.
- Controlled change and object-search scenarios meet agreed precision/recall/delay.
- Recovery suite succeeds or asks for help without unbounded attempts/unsafe motion.
- Persistent state survives restart and detects incompatible hardware/calibration/config.
- Curiosity selects useful, bounded revisits and passes repetition/duty/energy constraints.
- Edge/collision safety remains passing after autonomous planner integration.
- Docking passes alignment, default-off contact power, charging, release request,
  verified power removal, autonomous departure, thermal, and fault evidence.
