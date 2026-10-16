# Firmware Implementation Plan

## Linux platform baseline

1. Record exact Luckfox board revision and clone/pin the vendor SDK/toolchain sources.
2. Reproduce stock image build and flashing before customization.
3. Create a minimal Sherman board configuration with only required subsystems enabled.
4. Manage device-tree changes as reviewed source patches tied to the pin ledger; never patch deployed DTBs manually.
5. Package `shermand`, configuration, assets, service/supervisor unit, log policy, and build metadata.
6. Implement A/B or last-good rollback only after a target-appropriate design spike; until then preserve a known recovery image and explicit flash process.
7. Generate an SBOM/license/source manifest and image checksum.

### Linux adapters

Implement adapters behind interfaces for monotonic clock, hardware identity, camera, I2C ToF, SPI display, controller UART, storage, network, temperature/power telemetry, and controlled shutdown. Adapters must expose readiness, stale/error counters, timeouts, and recovery without leaking vendor types into core modules.

### Provisioning

Provision unique device ID, hardware profile, calibration references, Wi-Fi/network settings, Jarvis identity material, timezone, and release channel. Secrets are never embedded in images or logs. Provisioning is repeatable and can validate/repair without erasing world state unless explicitly requested.

## Companion controller

### Scheduler and tasks

Use a static/bounded design: high-priority safety tick; encoder capture/velocity estimate; motor control update; cliff/IMU/power acquisition; protocol RX validation; telemetry TX; diagnostics at lowest priority. Establish rates from characterization and publish measured worst-case execution/jitter.

### Boot state

Hardware outputs and driver enable remain inactive through reset, bootloader, firmware init, protocol negotiation, and config validation. A valid arm sequence is required after every reset. Controller maxima are compiled/read-only or protected from ordinary Linux configuration.

### Motion path

Validate sequence, TTL, units, finite numeric ranges, speed/acceleration limits, lifecycle, and current fault state. Interpolate or ramp targets within limits, close wheel-speed loops, prevent integral windup, and expire output independently. `STOP` is idempotent and a missing acknowledgment cannot delay local stop.

### Sensors and faults

Timestamp encoder and cliff data near acquisition. Detect stale, saturated, implausible, or inconsistent inputs. Maintain current and latched faults with first-fault context. Recovery paths are explicit: automatic only for proven transient conditions; otherwise disarm and require acknowledgment/self-test.

### Update and diagnostics

Firmware update occurs only disarmed on qualified power, verifies image/target/version, and preserves a recoverable last-good path when supported. Diagnostic commands cannot enable motors or exceed limits. Export version, reset reason, watchdog count, and self-test results.

## Implementation milestones

- F0: host-compiled protocol/state-machine library with fake HAL.
- F1: controller module blinks/telemeters with motor enable physically disconnected.
- F2: boot-safe enable waveform and watchdog/expiry validated.
- F3: one motor, then two, encoders and speed loop on current-limited bench.
- F4: cliff/IMU/power sensors and fault state.
- F5: Linux link/HIL and restrained chassis.
- F6: released hardware profile, update/recovery, manufacturing/receiving diagnostics.

## Documentation/evidence

Each platform change records vendor base revision, patch purpose, rebuild instructions, image/firmware hashes, supported hardware profile, resource changes, and rollback. Controller tuning records physical motor/wheel/load and must not be copied across profiles blindly.

