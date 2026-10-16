# Shared Test Infrastructure

## Scope

`tests/` holds cross-subsystem fixtures, fakes, canonical scenarios, schema/replay data, hardware-in-loop scripts/config, physical-test protocols and acceptance harness. Unit tests close to code may live in subsystem directories; shared evidence and system assertions live here.

Planned layout: `fixtures/`, `golden/`, `scenarios/`, `replay/`, `hil/`, `physical/`, `acceptance/`, `support/`. Real private captures are not committed by default.

