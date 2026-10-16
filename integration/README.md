# Integration and Release Candidates

## Scope

`integration/` owns cross-subsystem composition profiles, bring-up checklists, system scenarios, hardware-in-loop definitions, target deployment manifests, release-candidate configuration and phase-gate evidence assembly.

It is not a dumping ground for code that lacks an owner. Fix behavior in the owning subsystem; integration contains adapters/configuration/tests only when the responsibility is genuinely cross-cutting.

## Profiles

Planned: host-sim, target-stationary, HIL-controller, restrained-M2, mobile-M3, v1-candidate. Every profile pins schemas, build, hardware, calibration, configuration and expected capabilities.

