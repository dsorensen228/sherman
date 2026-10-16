# Build, Provisioning, Update, and Release Plan

## Build identity

Every artifact records source revision, dirty status, toolchain/dependency versions, schema, OS/vendor SDK base, configuration defaults, build time/reproducibility metadata and checksum. System image, `shermand`, controller firmware, display assets and generated schemas are independently identifiable but combined in a release manifest.

## Build environments

Use a pinned documented Linux environment/container for vendor target image/toolchain; host C++/Python tests on supported macOS/Linux; no unpinned download during release. Cache is convenience, not authority. Clean build is exercised regularly.

## Provisioning

Verify exact target hardware and power; flash system/controller through documented recoverable paths; provision unique identity/network/Jarvis credentials without logging; select hardware profile; install calibration; set timezone; run self-test; leave motors disarmed; emit provisioning record.

## Updates

Updates require compatible hardware/schema/storage/calibration, sufficient power/storage and disarmed state. Verify integrity/authenticity where practical, stage without destroying last-good, migrate transactionally, reboot/self-test and mark good only after bounded observation. Interrupted/failed update rolls back or enters documented recovery, never motor-enabled limbo.

## Release gates

Release candidate includes manifest/checksums, BOM/hardware/calibration/CAD IDs, reproducible build/provision/recover, acceptance evidence, resource/endurance report, known limitations/residual risks, operations/data guides and rollback. Independent operator reproduces a defined subset.

## Versioning

Use explicit major/minor/patch for user-facing software, separately version schemas/hardware/calibration. A version label alone never implies hardware compatibility; release manifest/profile does.

