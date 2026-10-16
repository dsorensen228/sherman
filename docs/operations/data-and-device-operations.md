# Data and Device Operations

## Owner operations

- View health, versions, active hardware/calibration/config and qualified environment.
- Pause/resume autonomy, enter privacy/quiet/vacation, stop/disarm.
- Run safe self-test and calibration validity check.
- Export a map/world summary, routines/preferences and support bundle.
- Clear world/history while retaining hardware calibration; factory reset including credentials as separate exact action.
- Pair/re-pair/revoke Jarvis and rotate credentials.
- Update/rollback/recover and inspect battery/service condition.

## Data retention defaults

Raw camera/audio: transient only. Derived observations/world beliefs: retained with age/confidence and user clear/export. Action/fault summaries: bounded history. Detailed logs/metrics: short rolling retention. Diagnostic captures: explicit, visible, capped and expiring. Exact durations/sizes become configuration after target storage/endurance evidence.

## Backup/restore

Backup manifest identifies schema, build compatibility, hardware/calibration and included data classes; encrypt if it leaves the device. Restore validates and stages transactionally. Never restore physical motion/action-in-progress or incompatible calibration as active. Provide dry-run compatibility summary.

## Replace/repair

Changing board, camera, ToF, IMU, motors/wheels/encoders, controller, battery/power or mechanical sensor mount invalidates specified profiles/calibrations/tests. Replacement workflow identifies affected requalification, not just “it boots.”

## Decommission

Disarm/remove power safely, export if desired, revoke Jarvis identity, erase credentials/world/diagnostics, verify erase at supported level and handle LiPo/electronics responsibly. Document limitations of flash/eMMC secure erasure rather than overclaim.

## Tests

Permission/confirmation and exact target; pause/privacy persistence; export/import current/prior/corrupt/incompatible; selective clear vs factory reset; credential revocation; capture expiry/erase; interrupted operations; no motor enable; audit of residual sensitive data.

