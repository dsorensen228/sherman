# Interface and Contract Plan

## Contract rules

Schemas live in `proto/` and are the single source of truth. Every field has units, range, optionality, default behavior, and compatibility semantics. Wire messages include schema version, message ID, source, monotonic timestamp or source clock metadata, correlation ID when applicable, and payload size limits.

Breaking changes require a new major schema version and a migration window. Additive fields are ignored safely by older readers. Enum readers must handle unknown values. Consumers must never interpret a missing field as a physically dangerous default.

## Core envelopes

### Event envelope

Fields: `schema_version`, `event_id`, `source_id`, `session_id`, `monotonic_time_ns`, optional `wall_time`, `kind`, `priority`, `correlation_id`, `payload`, `provenance`, `config_hash`.

### Command envelope

Adds: `command_id`, `issued_at`, `expires_at`, `preconditions`, `requested_capability`, `idempotency_key`, `reply_policy`. Expired commands are rejected. Motion and privacy-sensitive commands require explicit capability authorization.

### Health envelope

Fields: component, lifecycle state, readiness, degraded capabilities, last-good timestamps, fault codes, counters, resource readings, build ID. Health is descriptive; only the safety arbiter maps it to authority.

## Motion-controller protocol

Transport is a framed, checksummed UART or similarly bounded local link selected in Phase 3. The protocol has sequence numbers and explicit endian/version fields.

### Linux to controller

- `HELLO/NEGOTIATE`: compatible protocol and hardware profile.
- `HEARTBEAT`: current lifecycle, sequence, deadline.
- `ARM`: single-use request with current safety preconditions.
- `TWIST_COMMAND`: linear and angular target, acceleration bounds, sequence, TTL, behavior/action ID.
- `STOP`: priority and reason; controller must make this idempotent.
- `CONFIGURE_LIMITS`: only within immutable controller maxima and only while disarmed.
- `SELF_TEST_REQUEST` and calibration requests allowed only in explicit modes.

### Controller to Linux

- `STATUS`: armed state, watchdog, active command sequence, fault latch.
- `ODOMETRY`: encoder ticks, wheel velocities, integration interval, saturation flags.
- `IMU_SAMPLE` if the IMU is controller-owned.
- `CLIFF_SAMPLE`: raw/filtered values, threshold state, sensor health.
- `POWER_SAMPLE`: voltage/current/charge estimate and brownout flags when available.
- `FAULT`: latched code, first occurrence timestamp, contributing readings.
- `SELF_TEST_RESULT`.

### Invariants

- Controller output becomes zero on missing or invalid command, stale heartbeat, checksum error storm, reset, or critical sensor fault.
- Commands never persist across controller or Linux reset.
- Sequence rollback and duplicate frames cannot replay motion.
- Calibration mode cannot coexist with armed drive.
- Stop has no dependency on a positive acknowledgment.

## Jarvis API

Jarvis is an orchestrator and collaborator, not the safety controller.

### Jarvis to Sherman requests

- `observe_region`: request a fresh observation within privacy and reachability bounds.
- `locate_object`: search for a class or known object belief; response may be uncertain.
- `inspect_change`: revisit a change hypothesis.
- `patrol`: request a bounded route, duration, or priority area.
- `set_routine`, `pause_autonomy`, `resume_autonomy`, `return_home`.
- `say_expression`: request semantic expression, not raw pixels or arbitrary motor motion.
- `query_state`: health, capabilities, map summary, battery, active action.

Every request returns accepted/rejected/deferred with reason, action ID if accepted, and progress events. Jarvis receives honest uncertainty and cannot force unsafe movement.

### Sherman to Jarvis events

- lifecycle/health, availability, battery, dock state;
- action progress and outcomes;
- object/change observations with confidence and age;
- help requests and recovery context;
- privacy-state changes;
- notable routine summaries;
- bounded diagnostic attachments only when explicitly requested and permitted.

### Reconnect semantics

Use exponential backoff with jitter and a ceiling. Resume subscriptions from an event cursor when supported. Never replay expired commands. Reconcile action state by query; do not assume a disconnected command succeeded or failed. Outbound events use a bounded spool and priority-based eviction.

## Internal contracts

### Observation

Includes class/feature type, coordinate frame, geometry, covariance or confidence, source sensor/frame ID, acquisition time, processing model/version, quality flags, and privacy class.

### Track

Includes stable local ID, observation history summary, state estimate, existence probability, semantic hypotheses, last-seen pose/time, and merge/split lineage.

### Pose

Includes frame names, translation/orientation, covariance, source set, timestamp, and localization mode. A pose without uncertainty is invalid.

### Behavior intent

Includes objective, utility components, urgency, resource claims, risk class, deadline, interruptibility, explanation tags, and originating need/routine/request.

### Expression intent

Semantic inputs such as mood, arousal, gaze target, attention, confidence, and authoritative overlay (`low_battery`, `fault`, `privacy`, `updating`). Personality never supplies raw safety overlays.

## Contract test matrix

- Round-trip every message in C++ and Python.
- Parse golden bytes from current and previous minor versions.
- Fuzz lengths, enum values, nesting, NaNs/infinities, timestamps, and duplicate IDs.
- Confirm stale/expired commands fail closed.
- Confirm unknown additive fields do not break old readers.
- Confirm major-version mismatch prevents arming/motion.
- Confirm field range validation at ingress and again at authority boundaries.
- Test reconnect, deduplication, cursor gaps, queue overflow, and event eviction.

