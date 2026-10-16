# Data, Persistence, and Replay Plan

## Data classes

1. **Configuration:** versioned, human-reviewable inputs and compiled bounds.
2. **Operational state:** current lifecycle, actions, health, and controller state; mostly ephemeral.
3. **World state:** map tiles/cells, landmarks, objects, tracks, confidence, and decay metadata.
4. **Behavior state:** needs, routine checkpoints, preferences, and bounded relationship history.
5. **Evidence:** test output, build/config IDs, metrics, and carefully selected diagnostics.
6. **Sensitive sensor data:** camera/audio frames; transient by default and governed explicitly.

## Storage model

Use a transactional embedded store appropriate to the final OS image, with a versioned repository interface and an in-memory implementation for tests. SQLite in WAL mode is the planning default if target measurements pass; otherwise use an append-only journal plus atomic snapshots.

Logical tables/collections:

- `schema_migrations`
- `sessions`
- `map_snapshots` and `map_deltas`
- `landmarks`
- `object_beliefs`
- `change_hypotheses`
- `behavior_state`
- `routines`
- `actions` and compact outcomes
- `calibration_profiles`
- `hardware_profiles`
- `fault_history`
- `event_spool`

Every record that represents a belief contains created, observed, and updated time; confidence; source/provenance; and schema/model version.

## Write policy

- Stream state changes into a bounded journal.
- Commit safety/fault and calibration data promptly.
- Coalesce high-rate world changes and checkpoint periodically.
- Write a new snapshot completely, verify checksum, then atomically publish it.
- Retain at least one last-known-good snapshot and migration backup.
- On low battery or shutdown, stop optional writes first and finish a bounded critical checkpoint.

## Map decay

Decay represents uncertainty, not deletion. Occupancy, landmark, and object beliefs decay at different rates based on time, location, observation conditions, and mobility. Reobservation increases confidence; contradictions create a change hypothesis before destructive replacement. Static desk boundaries decay slowly; small movable objects decay quickly.

## Privacy and retention

- Raw camera buffers live only long enough for processing unless a debug capture is explicitly enabled.
- Diagnostic captures have a visible state, time limit, size cap, and redaction/export workflow.
- Store derived features or thumbnails only when required and classified.
- Provide user operations to inspect and clear world/history state without breaking calibration.
- Never include credentials, raw frames, or private content in crash logs.

## Replay format

A replay bundle contains manifest, build and config hashes, schema versions, seed, clock mapping, sensor/event streams, expected landmarks/actions/expressions, and checksums. Sensor payloads are chunked and compressed independently for random access. The format supports anonymized synthetic data so most regression fixtures contain no real workspace imagery.

## Migration and recovery tests

- Create/upgrade/downgrade boundary tests from every supported schema.
- Kill power/process at every write-stage fault point; last-good state must open.
- Fill storage and verify priority eviction and safe degraded operation.
- Corrupt journal records, snapshots, indexes, and checksums; recovery must be bounded and diagnosable.
- Replay across supported builds and quantify expected behavioral differences.
- Verify erase/export operations and confirm sensitive data is absent after erase.

