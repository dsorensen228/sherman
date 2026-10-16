# Tooling Implementation Plan

## Command design

One documented entry surface (script/task runner/CLI) with subcommands, `--help`, dry-run where meaningful, explicit target/profile, machine-readable output and stable exit codes. Print build/config/hardware/calibration identity for target-affecting actions.

## Planned tools

- bootstrap/pinned dependency and build environment check;
- system/controller build, image manifest, flash/provision/recover;
- hardware receiving record and pin-ledger validation;
- controller link monitor/fault injector that remains unable to bypass firmware bounds;
- display animation/latency pattern;
- camera/ToF/IMU/wheel calibration capture/solve/validate;
- replay record/inspect/anonymize and scenario runner;
- metrics/log/support bundle collection/redaction;
- power/runtime/thermal data import/plot/report;
- CAD/export/BOM/assembly release checks;
- documentation link and requirements traceability audit;
- release candidate manifest/checksum/rollback helper.

## Safety/privacy

Physical actions require explicit profile/preflight/confirmation in operator tools and preserve controller authority; automation for tests uses a separate controlled fixture mode. Camera capture shows mode, destination, duration/size, classification and erase. Secrets are referenced through platform stores/environment, never printed or embedded.

## Portability

Host tools target documented macOS/Linux where practical; vendor SDK builds may require pinned Linux/container/VM. Detect unsupported host early. Do not silently download changing binaries; pin/checksum dependencies and record licenses.

## Observability

Structured output includes tool version, inputs, start/end, target identity, result and artifact paths. Long operations are resumable or leave diagnosable partial state. Destructive erase/flash targets are exact and verified.

