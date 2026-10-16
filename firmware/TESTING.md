# Firmware Testing Plan

## Host and static tests

- Compile platform-independent controller logic for host with strict warnings, sanitizers, and coverage.
- Transition/property tests for boot, negotiation, disarmed/armed/moving/braking/fault states.
- Protocol golden/fuzz corpus: sync loss, truncation, CRC, length, unknown version/type, duplicate/out-of-order/wrapped sequence, stale TTL, NaN/overflow.
- Pin-ledger/device-tree/firmware constant consistency checks.
- Stack, static allocation, task period, and queue capacity review.

## Controller HIL

Instrument motor enable and outputs first with controller timestamps, LEDs/test points, an inexpensive logic analyzer, multimeter and phone slow-motion video. Borrow oscilloscope access only if a specific transient or signal-integrity failure remains unresolved. Test reset, bootloader, firmware start, arm, valid motion, TTL expiry, heartbeat loss, corrupted/flooded UART, controller watchdog, Linux reset, controlled undervoltage, USB/power transitions, and sensor faults. Acceptance requires motor-disabled default and measured stop under the qualified bound.

Use simulated encoders/sensors to sweep rates, wrap, bounce, stale, noise, impossible deltas, cliff threshold hysteresis, and bus lock. Confirm a failed I2C operation cannot block the safety task.

## Motor bench

Current-limited supply, wheels unloaded first. Verify polarity, command sign, encoder sign, closed-loop response, saturation, acceleration, stop/coast/brake, stall pulse/current limit, thermal fault, driver sleep/fault, and simultaneous channels. Record load, voltage, motor/wheel/hardware IDs.

## Linux image tests

- Clean deterministic build and checksum comparison/manifest.
- Flash/recovery by independent operator.
- Boot/readiness/restart loops, full/read-only/corrupt storage, wrong hardware profile.
- Device discovery and missing/faulted peripheral.
- Resource/thermal soak with camera/display/network/controller activity.
- Log rotation/bounds and secret scan.
- Interrupted update/config deployment and last-good recovery.

## Physical progression

No free movement until protocol/controller HIL, motor bench, and wheels-up tests pass. Then follow Phase 3 restrained/contained progression. Any uncontrolled output or unexplained reset is a release blocker.

## Evidence

Store waveforms, UART traces, test reports, build map/resource usage, timing histograms, thermal/current plots, image hashes, exact toolchain, and hardware IDs under the owning packet artifacts.
