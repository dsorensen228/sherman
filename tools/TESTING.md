# Tooling Testing Plan

## CLI tests

Help/usage, required args, invalid combinations, exit codes, structured output schema, dry-run, paths with spaces, missing dependency/device, interrupted operation and cleanup. Golden manifests/reports have tolerant timestamps but exact semantic content.

## Safety tests

Wrong/ambiguous target, incompatible hardware/profile/image, low/unknown power, controller armed, missing confirmation, erase scope, capture privacy and secret redaction. Tools fail before side effects and never raise hardware safety maxima.

## Integration

Run against fakes and sacrificial test target for flash/provision/recover, calibration, capture/replay, fault injection, support bundle and release. Verify artifacts link to exact identities and can be consumed by test harness.

## Reproducibility/security

Clean host bootstrap/build, dependency checksums, offline behavior after cache, malicious/corrupt input files, archive path traversal/oversize, log injection and secret scanning. Fuzz parsers shared with device messages/replays.

## Documentation audits

Automated link/file checks, directory README/IMPLEMENTATION/TESTING presence, work-packet IDs, acceptance/traceability consistency and generated-output freshness. The audit itself has fixtures that intentionally violate each rule.

