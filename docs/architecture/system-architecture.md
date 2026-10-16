# System Architecture

## Architectural objective

Separate fast safety, device I/O, perception, persistent belief, behavior policy, expression, and remote orchestration so each can be simulated, tested, degraded, and replaced independently.

## Two-computer reference design

### Luckfox Pico Ultra W: deliberative computer

The Linux board owns camera ingestion, front range processing, perception, map and world model, behavior selection, display rendering, persistence, observability, and Jarvis communication. It may propose motion but cannot force motors to run.

### Companion controller: real-time safety computer

A small MCU-class module is the reference design for Phase 3. It owns motor PWM/direction, encoder capture, cliff sensors, command expiry, local current/voltage inputs where available, watchdog, and the physical motor-enable path. Exact module selection is gated; the architecture is intentionally independent of the SKU.

The controller accepts bounded velocity commands with a short time-to-live. If heartbeats stop, a command expires, a cliff threshold is violated, the watchdog trips, or its state becomes invalid, it disables drive without Linux cooperation. This is defense in depth, not a claim of commercial functional-safety certification.

## Linux runtime components

The initial deployment may use one supervised `shermand` process with internal modules to conserve memory and simplify atomic state. Modules can split into processes only when isolation evidence outweighs overhead.

| Module | Input | Output | Failure behavior |
| --- | --- | --- | --- |
| Platform | OS, device tree, config, monotonic clock | device handles, health, lifecycle | refuse readiness; no motion |
| Sensor hub | camera, ToF, MCU telemetry, IMU | timestamped sensor frames | mark source stale; degrade policy |
| Perception | synchronized frames | observations and tracks | shed optional models; retain range/safety |
| Localization | odometry, IMU, range/visual cues | pose + covariance/confidence | slow, stop, or relocalize |
| World model | observations, pose, prior map | occupancy, objects, change events | preserve last valid snapshot; flag uncertainty |
| Behavior engine | needs, world state, routines, commands | intent and action plan | fall back to safe idle/expressive state |
| Safety arbiter | proposed actions, health, zones, MCU state | permitted motion envelope | fail closed |
| Motion gateway | permitted command | expiring MCU command | send stop on invalid or stale input |
| Eye renderer | mood, gaze, authoritative status | display frames | show reserved fault expression or blank safely |
| Jarvis client | outbound events, inbound requests | validated command/events | reconnect with backoff; local operation continues |
| Store | state deltas, snapshots, config | transactional local persistence | read-only/degraded mode; never corrupt last-good |
| Telemetry | metrics, structured events | bounded logs and traces | drop low-priority data first |

## Priority domains

From highest to lowest:

1. Electrical and controller fail-safe.
2. Cliff/contact/thermal/battery safety.
3. Explicit human stop and physical pickup detection.
4. Recovery and localization protection.
5. Jarvis-directed task.
6. Local routine and curiosity.
7. Expressive flourish.

A lower domain may never override a higher domain. The safety arbiter receives proposals, not imperative motor commands.

## Runtime state machines

### System lifecycle

`BOOTING → SELF_TEST → READY_STATIONARY → ACTIVE → DEGRADED → SAFE_STOP → SHUTTING_DOWN`

- Only `ACTIVE` permits nonzero motion.
- `READY_STATIONARY` permits perception, eyes, network, and calibration.
- `DEGRADED` has an explicit capability mask and speed limit.
- `SAFE_STOP` is latched for selected faults until a validated recovery action.

### Motion authority

`DISARMED → ARM_REQUESTED → ARMED → MOVING → BRAKING → DISARMED`, with transitions to `FAULT_LATCHED` from every state. Arming requires controller readiness, sensor freshness, acceptable battery/thermal state, a valid motion zone, and no human stop.

### Behavioral action

`PROPOSED → ADMITTED → EXECUTING → SUCCEEDED | FAILED | CANCELED | PREEMPTED`. Every action has an ID, deadline, resource claim, cancel path, and completion evidence.

## Data flow

1. Adapters timestamp raw data near acquisition using monotonic time.
2. Synchronization associates camera, range, odometry, and IMU with known tolerance.
3. Perception emits immutable observations with source metadata.
4. Localization estimates pose and confidence.
5. World model fuses observations using pose uncertainty and updates map/object beliefs.
6. Behavior selects an intent from needs, routines, Jarvis requests, and world uncertainty.
7. Planner proposes actions; safety admits, modifies, or rejects them.
8. Controller executes only fresh, bounded motion commands and returns telemetry.
9. Expression mirrors intent and authoritative status without controlling either.
10. Store writes versioned deltas and periodic atomic snapshots.

## Time and determinism

- Use monotonic time for deadlines, freshness, control, and replay ordering.
- Use wall-clock time only for human schedules and external timestamps; record timezone.
- Never compare raw timestamps from unsynchronized clock domains. Estimate controller/Linux offset and uncertainty.
- Policy randomness is seeded and recorded. A replay with the same inputs, seed, build, and config must produce the same decisions within documented numeric tolerances.

## Configuration

Configuration is layered: compiled safe bounds → hardware profile → environment profile → user preferences → session overrides. A later layer cannot exceed compiled or hardware safety bounds. Every effective configuration has a hash included in evidence and telemetry.

## Resource strategy

The target is constrained. Use bounded allocators/queues on streaming paths; avoid retaining decoded image history; prefer zero-copy or buffer pools; make inference optional and rate-limited; persist features/tracks rather than raw video; and load only assets needed by the selected eye theme. Resource pressure causes graceful feature shedding before it threatens safety or display responsiveness.

## Security and privacy

- Mutual identity for Jarvis/Sherman should be provisionable without hard-coded secrets.
- Pairing is a local, explicit action.
- Reject unknown message types, invalid units, stale commands, oversized payloads, and privilege escalation.
- Do not stream or retain camera frames by default. Derive and store minimal observations.
- A visible privacy mode disables capture/streaming and records the transition.
- Logs redact tokens, network credentials, raw private content, and unnecessary identifiers.

## Architectural fitness tests

- All hardware interfaces have host/simulation implementations.
- No module other than motion gateway can produce controller motion frames.
- No remote message can bypass behavior admission and safety.
- Replaying a golden scenario yields stable action and expression sequences.
- Killing Jarvis transport does not stop local safety or corrupt state.
- Killing deliberative runtime causes the controller to stop motors within the qualified bound.
- Invalid configuration cannot raise physical limits.
- Storage upgrade tests preserve last-good snapshots and support rollback.

