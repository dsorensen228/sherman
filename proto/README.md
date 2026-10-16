# Schemas and Compatibility

## Scope

`proto/` owns the canonical semantic and wire schemas shared by C++, Python, the controller, Jarvis, replays, and tools. It also owns generated-code configuration, golden encoded fixtures, validation rules, compatibility policy, and schema documentation.

Schemas describe data, units, provenance, authority, expiry, and unknown behavior. They do not contain business logic. Consumers must still validate at ingress and authority boundaries.

Planned packages: common envelope/units, health/lifecycle, actions, expression, observations/tracks/pose/map, Jarvis requests/events, controller link, replay manifest, configuration/hardware/calibration identities.


The first Pico 2 controller draft uses `schema/controller-v1.json` with generated
C++ constants, Python/C++ golden fixtures and the bounded UART contract documented
in [controller-v1](docs/controller-v1.md). It does not change the banter schemas.
