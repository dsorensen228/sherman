# Schema Testing Plan

## Cross-language golden tests

For every message, produce a semantic fixture and canonical bytes where format permits. C++ writes/Python reads, Python writes/C++ reads, and controller host library round-trips its messages. Compare semantic values, unknown fields/enums, optional presence, and boundary values.

## Compatibility

Maintain writer-current→reader-prior and writer-prior→reader-current tests for supported minor versions. Assert additive fields are ignored/preserved as designed; missing new fields choose safe behavior; major mismatch refuses incompatible capability such as motion.

## Validation/fuzz

Fuzz arbitrary/truncated/oversized payloads, nesting depth, lengths, invalid UTF-8 if relevant, unknown enum, duplicate IDs, stale/negative durations, extreme timestamps, NaN/infinity, unit/range and cross-field contradictions. Parsing and validation must have bounded time/memory and never crash.

## Generated artifacts

CI regenerates and fails on dirty diff, verifies generator versions, scans hand edits, compiles every target language/profile, and checks generated documentation/field numbers. Prevent field-number reuse and unreviewed required semantics.

## Protocol scenarios

Explicit tests for expiry, idempotency/deduplication, command/result correlation, reconnect cursor, sequence wrap/rollback, controller CRC/framing, privacy classification, config/hardware/calibration mismatch, and replay manifest checksums.

