# Sherman Pico 2 firmware — first draft

This is the **Raspberry Pi Pico 2 (RP2350), non-wireless**, W1 controller,
not the Luckfox. It builds a real UF2 with UART telemetry, read-only USB diagnostics,
sensor acquisition, encoder capture, watchdog, and a portable tested motion arbiter.

**Status: F0 software draft / F1 bench image; BLOCKED-HARDWARE.** No Pico was attached
to the factory Mac during development. Nothing has been flashed or bench-qualified.
This image deliberately keeps GP3, GP12 and GP8–11 low. ARM always fails because
there is no qualified physical calibration. This is a code-level lock, not a setting
that a host message can bypass. It is useful for board/sensor/wiring bring-up and
protocol development; it is not firmware for letting Sherman drive on a desk.

## Included

- W1 pin map checked against `electronics/prototype-netlist.csv`.
- Bounded binary UART0, 115200 8N1, CRC16, boot nonce, monotonic sequence and
  controller-clock deadlines; generated C++ constants and Python codec.
- HELLO, HEARTBEAT, ARM, TWIST, STOP, disarmed limit configuration, fault clearing,
  non-actuating self-test; status, sensor, and wheel telemetry.
- Boot-safe outputs; dual hardware charge-interlock observation; expiry and latched
  cliff, stale/missing sensor, power, tilt, driver, protocol, encoder and loop faults.
- Synthetic-profile differential wheel-speed PI control, acceleration limit,
  saturation/anti-windup, stall detection and front-only trajectory restrictions.
- GPIO quadrature capture, unsigned tick wrap, invalid-transition reporting.
- Two VL53L4CDs with separate open-drain XSHUT sequencing and addresses 0x2A/0x2B;
  LSM6DSO at 0x6B; MAX17048 at 0x36. Data validity and age are explicit.
- Bounded I2C transactions, RX work, TX buffering, diagnostics, and watchdog.
- Host sanitizer/fault tests, seed-531 parser stress, cross-language golden frames,
  sensor bus simulation, reproducible SDK bootstrap, build and recovery instructions.

## Build

From the Sherman repository root, install CMake, Ninja, Python 3 and the **complete
Arm GNU embedded toolchain with newlib and C++ headers**. The Homebrew
`arm-none-eabi-gcc` formula alone lacks those libraries. Use Arm's complete
`arm-none-eabi` distribution (tested: Arm GNU 14.3.Rel1, GCC 14.3.1).
`picotool` 2.3.1 is used to produce the RP2350 UF2. SDK 2.2.0 is pinned by commit.

```sh
firmware/controller/tools/bootstrap.sh
cmake -S firmware/controller -B build/controller-host -G Ninja
cmake --build build/controller-host
ctest --test-dir build/controller-host --output-on-failure

# Point this at the directory containing the complete arm-none-eabi-gcc toolchain:
export PICO_TOOLCHAIN_PATH=/path/to/arm-gnu-toolchain/bin
cmake -S firmware/controller -B build/pico2 -G Ninja -DSHERMAN_PICO=ON
cmake --build build/pico2
```

Output: `build/pico2/sherman_pico2.uf2`, `.elf`, `.bin`, and link map. Never use a
Pico/RP2040 or Pico 2 W image for this W1 profile. CMake rejects other board names.
The USB summary and binary metadata identify the source commit and dirty status.
No network downloads occur in the firmware.

## Giving the factory access to the Pico

**Simplest first connection:** attach the Pico 2 to this Mac mini with a **USB data
cable**. The Pico uses micro-USB. For this first bench stage, unplug its external
VSYS supply and leave the motor power branch disconnected, as W1 requires. Hold
BOOTSEL while plugging USB in. It appears as a drive named **RP2350**. The factory
already has filesystem/USB access on this Mac, so there is no account, password,
Wi-Fi credential, or SSH server to configure on the Pico itself.

Once the board is physically connected, a factory task can identify it, build the
image, copy the UF2, and read its USB serial diagnostics. The copy causes a reboot
and the RP2350 drive disappears; a serial device such as `/dev/cu.usbmodem…`
should then appear. Check the actual name rather than assuming a fixed suffix.

```sh
# Only after confirming this is the intended, isolated Pico 2:
cat /Volumes/RP2350/INFO_UF2.TXT
cp build/pico2/sherman_pico2.uf2 /Volumes/RP2350/
# Read-only USB text diagnostics (exit screen with Ctrl-A then K):
screen /dev/cu.usbmodemACTUAL_DEVICE 115200
```

For **repeatable unattended flashing and debugging**, keep a Raspberry Pi Debug
Probe connected to the Mac by USB and connect its SWDIO, SWCLK and GND to the
Pico 2's labeled SWD pads/header. Power the Pico by its qualified supply; the probe
is a debug interface, not a substitute for the power harness. This lets the factory
halt, inspect, reset and flash using RP2350-aware OpenOCD without someone holding
BOOTSEL. Verify probe pin labels before wiring. Never attach both W1 external VSYS
and Pico USB power until the power-OR/backfeed qualification is complete.

Alternatively attach it to an **already authorized SSH host** and expose that host's
USB/SWD devices to the factory through SSH. Record the host, exact serial/probe ID
and power arrangement in the device inventory. A USB-only Pico is not accessible
just because the separate Luckfox is reachable over the network.

Official references:
- [Raspberry Pi Pico-series recovery/BOOTSEL](https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html)
- [Debug Probe and SWD wiring](https://www.raspberrypi.com/documentation/microcontrollers/debug-probe.html)
- [Pico SDK](https://github.com/raspberrypi/pico-sdk/tree/2.2.0)

## Communications and smoke test

USB is a **read-only text console**, approximately one line per second, including
build ID, uptime, faults, qualified/armed flags, UART errors, maximum loop duration
and telemetry drops. No USB command can arm or drive motors. The SDK USB boot
interface supports recovery where compatible tooling is installed; ROM BOOTSEL
is the dependable fallback, including for broken application firmware.

Binary telemetry is on GP0/TX and GP1/RX, not the USB console. Follow W1 Section 4
before using Luckfox UART4: its deployed device tree currently disables that UART.
Do not change the live Luckfox or wire its debug-console pins to this draft.
A separate 3.3 V USB-UART adapter on the Mac can observe GP0 plus common GND during
bench work. Never use a 5 V/RS-232 interface. On the qualified host UART:

```sh
python3 firmware/controller/tools/link.py --device /dev/ttyS4 --seconds 10
```

This monitor only reads; it exits unsuccessfully on timeout/corruption. The codec
API exists for a future safety-gateway implementation and host tests, not a raw
motion command CLI. See [wire contract](../../proto/docs/controller-v1.md).

Missing sensors do not hang startup or invent readings. Their validity flags stay
false. Reconnect/reinitialize failed hardware by resetting this disarmed image.
CTRL_READY means the firmware loop is alive, not that motors are permitted.

## Remaining physical work

P3-CTL-001: boot/reset/watchdog/USB/I2C timing on the actual Pico. P3-PWR-001:
interlock, motor rail sequencing and power/no-backfeed measurements. P3-MOT-001:
polarity, wheelbase, encoder scale, PI gains and current/speed/stop qualification.
P3-CLF-001 and P3-IMU-001: surface thresholds, geometry, alignment and tilt/health
bounds. P3-SAF-001: Linux safety arbiter. P3-HIL-001: injected failures and worst-case
stop waveform. Only then implement/enable the qualified motor-output adapter;
there is intentionally no physical PWM drive path in this diagnostic image.

Reverse, pivot, docking release, calibration writes, secure update/A-B rollback and
free-roaming autonomy are not claimed. Existing W1 has no assigned dock-release
GPIO. Calibration is not silently guessed or persisted over USB flashing. Preserve
any previous firmware image before overwriting a board; return to it with BOOTSEL
if the new image fails diagnostics, keeping motor power disconnected.
