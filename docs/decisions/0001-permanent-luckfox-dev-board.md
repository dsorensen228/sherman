# ADR 0001: Permanently Integrate the Luckfox Development Board

**Status:** Accepted

## Context

Moving from a development board to a custom SoM carrier would reduce volume but adds PCB, power sequencing, high-speed interface, manufacturing, and recovery work the project owner does not want.

## Decision

The finished Sherman prototype line will permanently use a Luckfox Pico Ultra W development board. The chassis must support its actual connector protrusions, antenna/keep-out needs, recovery button and USB-C access, cable bend radii, mounting holes, and thermal behavior.

## Alternatives

- Core1106 SoM on custom carrier: smaller, rejected for scope.
- Different SBC: possible future branch, not a v1 optimization path.

## Consequences

The comfortable chassis may exceed the stretch envelope. Ethernet and USB-A may remain internally unused but still consume volume. Mechanical work begins from measured hardware, not published outline alone. Software preserves vendor recovery and provisioning workflows.

## Verification

Phase 1 receiving inspection and board scan; Phase 3 serviceability, cable-access, antenna, thermal, and drop/handling checks.

## Rollback

Requires a new ADR and a separate hardware profile; do not mutate v1 CAD around an unqualified replacement.

