# Firmware and Platform

## Scope

This directory owns target board support and the companion real-time controller firmware. It does not own high-level behavior, mapping, perception policy, Jarvis semantics, or cosmetic eye content.

Planned subareas when code begins:

- `linux/`: target image integration, device tree/config fragments, service definitions, hardware adapters, provisioning hooks.
- `controller/`: real-time motor/safety firmware, bootloader/update policy, board support, hardware abstraction.
- `shared/`: protocol constants generated from `proto/`, units, hardware-profile IDs; no duplicated hand-authored schemas.
- `tools/`: target-specific flashing, self-test, factory/receiving diagnostics.

## Contracts

Firmware exposes timestamped, bounded device interfaces and health. Only the controller may directly drive motors. Linux hardware adapters publish sensor frames and consume admitted motion, display, and configuration contracts. Every adapter has a simulator/fake equivalent outside this directory.

## Quality bars

Boot/reset defaults are safe, target builds are reproducible, vendor changes are isolated and documented, hardware revisions are explicit, loops and queues are bounded, logs cannot stall critical work, and recovery does not require undocumented manual steps.

See `IMPLEMENTATION.md` and `TESTING.md` before assigning firmware packets.

