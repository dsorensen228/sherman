# ADR 0009: Pico 2 W1 diagnostic firmware and bounded controller protocol

## Status
Proposed for hardware qualification; accepted as an isolated software first draft.

## Context
W1 defines the Pico 2 pins and sensors, but no measured drivetrain calibration,
cliff envelope, or controller bench evidence exists. A draft must be useful on a
USB-powered board without silently granting physical motion authority.

## Decision
Use Pico SDK C++17 and a host-testable allocation-free core. Keep existing W1
pins. The target always uses an unqualified profile: physical ARM is denied and
both motor requests and all PWM outputs stay low. No runtime command or build
option unlocks this. A later reviewed profile requires bench evidence and code
changes. The same controller runs with explicit synthetic calibration in tests.
Use generated v1 constants from proto/schema/controller-v1.json, little-endian
bounded CRC16 frames, boot session nonce, increasing sequence numbers, and
controller-clock deadlines. STOP is accepted regardless of session/sequence.
Unknown or invalid traffic fails closed. UART is the authority transport; USB
is read-only diagnostics/recovery. No USB shell or direct PWM command is exposed.
Read both VL53L4CDs, LSM6DSO, MAX17048, encoders and interlock inputs, timestamp
fresh data, and report invalid/stale values honestly. Failed sensor startup stays
failed until reset; no uncontrolled repeated recovery while armed.

## Alternatives
MicroPython would simplify interactive flashing but adds scheduling/GC variability.
Direct Linux PWM violates ADR 0002. Guessing physical calibration would conceal
unclosed qualification gates. A no-sensor blink stub would not be a useful draft.

## Consequences
This is F0/F1 software, not a motion release. Numeric control/safety bounds in the
simulation profile are illustrative and never authorize hardware movement. The
Linux motion arbiter remains P3-SAF-001. There is no prior controller wire version
to migrate. The new codec is additive to the existing banter protocols.

## Verification
Host state/negative/property tests and seeded parser fuzz; cross-language golden
fixtures; W1 netlist checks; strict-warning and sanitizer builds; RP2350 UF2 build.
Physical reset, watchdog, power ordering, sensor unplug, and stop measurements
remain P3-CTL-001/P3-HIL-001, with motor characterization in P3-MOT-001.

## Rollback
Do not wire motor power for F1. Restore a known UF2 using ROM BOOTSEL. Preserve
W1 hardware interlock and external pull-downs; firmware does not replace them.

## Links
- ../hardware/pin-and-bus-plan.md
- ../../electronics/wiring-guide.md
- ../../firmware/controller/README.md
- ../../proto/docs/controller-v1.md
