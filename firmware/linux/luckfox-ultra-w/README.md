# Luckfox Pico Ultra W Platform Baseline

This package records the first known-good Sherman bring-up in which the exact
Luckfox Pico Ultra W simultaneously exposes the Waveshare ST7789V2 display bus,
runs the SC3336 CSI camera pipeline, and remains reachable over Wi-Fi and USB.
It belongs to `P1-PLAT-001`; display performance qualification remains
`P1-DSP-001/002`, and camera contracts/calibration remain Phase 2 work.

The baseline was observed on 2026-08-19 with:

- Buildroot `2023.02.6`, Linux `5.10.160`, ARMv7;
- Luckfox SDK commit `824b817f889c2cbff1d48fcdb18ab494a68f69d1`;
- Waveshare 1.9-inch LCD SKU 23822, ST7789V2, `320 × 170`, RGB565;
- Luckfox SC3336 3MP Camera B;
- SPI0 M0 at the validated deployed `40 MHz`, CS enabled, MISO omitted;
- vendor `rkipc` CSI/ISP/encoder/RTSP pipeline.

`hardware-profile.json` is the machine-readable record. `luckfox.cfg` is an
exact copy of the verified persistent configuration, including the inert
`SPI0_M0_MODE=1` line emitted by a vendor-script fallback bug. The operative
MISO setting is `SPI0_M0_MISO_ENABLE=0`.

## Pin map

All display wiring is on header P1. Physical pin numbers, SoC names, and Linux
GPIO offsets must not be interchanged.

| LCD signal | P1 pin | Luckfox signal | Linux access |
| --- | ---: | --- | --- |
| `VCC` | 1 | `3.3V` | power only |
| `DC` | 13 | `GPIO1_D0` | `/dev/gpiochip1`, offset `24` |
| `RST` | 15 | `GPIO1_D1` | `/dev/gpiochip1`, offset `25` |
| `DIN/MOSI` | 19 | `GPIO1_C2 / SPI0_M0_MOSI` | `/dev/spidev0.0` |
| `CLK` | 23 | `GPIO1_C1 / SPI0_M0_CLK` | `/dev/spidev0.0` |
| `CS` | 24 | `GPIO1_C0 / SPI0_M0_CS0` | `/dev/spidev0.0` |
| `GND` | 25 | `GND` | power return |
| `BL` | 26 | `GPIO1_D2 / PWM0_M1` | `/dev/gpiochip1`, offset `26` initially |

The legacy sysfs GPIO numbers for DC, RST, and BL are `56`, `57`, and `58`, but
new code should use gpiochip line offsets. Their electrical boot states have
not yet been qualified. The display service must explicitly hold BL off until
reset, initialization, and a safe first frame complete.

The camera is not multiplexed onto these header pins. The verified image uses
I2C4 M2 on GPIO3_C7/GPIO3_D0 for sensor control and dedicated CSI lanes for
pixels. Disabling the parallel RGB block therefore releases the display pins
without disabling SC3336.

## Why no SDK build was required

The stock Ultra W DTS enables the parallel RGB block and disables SPI0. The
vendor `luckfox-config` utility provides both mechanisms needed for bring-up:

1. RGB disable is written into the FIT/device tree in the eMMC boot partition.
2. SPI0 is persisted in `/etc/luckfox.cfg` and replayed as a configfs overlay by
   `/etc/init.d/S99luckfoxconfigload` on every boot.

The source locations in the pinned SDK are:

- `sysdrv/source/kernel/arch/arm/boot/dts/rv1106g-luckfox-pico-ultra.dts` —
  top-level `&spi0` default;
- `sysdrv/source/kernel/arch/arm/boot/dts/rv1106-luckfox-pico-ultra-ipc.dtsi`
  — RGB `lcd_pins`, SPI0 M0 pins, SC3336, and I2C4 M2;
- `project/cfg/BoardConfig_IPC/overlay/overlay-luckfox-config/usr/bin/luckfox-config`;
- `project/cfg/BoardConfig_IPC/overlay/overlay-luckfox-config/etc/init.d/S99luckfoxconfigload`.

This live-overlay route is suitable for qualification. Production image work
must convert it into a reviewed source patch and reproducible `boot.img` per
`firmware/IMPLEMENTATION.md`; manually patched deployed DTBs are not the final
build architecture.

## Reproduce the configuration

Before changing the boot partition, capture it and the config on build-host. Run
these commands from the Mac, where the `robot-usb` and `build-host` SSH aliases are
configured. They stream data outward and do not require target free space:

```sh
ssh robot-usb 'dd if=/dev/block/by-name/boot bs=1M status=none' \
  | ssh build-host 'umask 077; mkdir -p /home/example/backups/robot-host/YYYY-MM-DD; \
      dd of=/home/example/backups/robot-host/YYYY-MM-DD/boot-before-spi.img \
      bs=1M status=none'
ssh robot-usb 'cat /etc/luckfox.cfg' \
  | ssh build-host 'umask 077; \
      dd of=/home/example/backups/robot-host/YYYY-MM-DD/luckfox.cfg.before-spi \
      status=none'
ssh build-host 'sha256sum /home/example/backups/robot-host/YYYY-MM-DD/*'
```

Then use an allocated TTY because the vendor utility uses `dialog`:

```sh
ssh -tt robot-usb luckfox-config
```

Select `Advanced Options` → `RGB` → `disable`, exit cleanly, and reboot. After
the target returns, run `luckfox-config` again and select `Advanced Options` →
`SPI` → `SPI0_M0` → `enable`, then:

- speed: `40000000` (`16000000` remains the conservative fallback);
- CS0: `enable`;
- MISO: `disable`.

Reboot once more and run the health check below. Do not enable SPI while the
currently booted RGB driver still owns the pins.

## Read-only health evidence

Deploy `bin/health-check.sh` anywhere executable on the target, or pipe it over
SSH without installing it:

```sh
ssh robot-host 'sh -s -- --format ndjson' \
  < firmware/linux/luckfox-ultra-w/bin/health-check.sh \
  > luckfox-health.ndjson
```

The script checks exact target identity, persistent config, live device-tree
status, spidev/GPIO/media nodes, overlay replay, `rkipc`, RTSP port 554, bounded
camera-stream kernel evidence, temperature, and total memory. It is strictly
read-only and emits no unbounded logs or camera data. Exit `0` means all
required checks passed; exit `1` means a required condition failed; exit `2`
means invocation/dependency error. Missing old kernel-ring evidence is a
warning because the ring can rotate.

The collector expects the recorded and currently deployed `40 MHz` cap. It can
be overridden without editing the script when validating the conservative
`16 MHz` fallback:

```sh
SHERMAN_EXPECTED_SPI_HZ=16000000 health-check.sh --format ndjson
```

## Camera and RTSP verification

The on-target health collector proves that the SC3336/CSI nodes are enabled,
media devices exist, `rkipc` is alive, and port 554 is listening. Real decoded
frames must be verified from another machine so the test exercises the sensor,
encoder, network, RTSP, demux, and decoder path rather than merely inspecting a
process or stream header:

```sh
firmware/linux/luckfox-ultra-w/bin/probe-rtsp.sh robot-host
firmware/linux/luckfox-ultra-w/bin/probe-rtsp.sh \
  rtsp://192.0.2.10/live/1
```

The main and substream paths are `/live/0` and `/live/1`. `probe-rtsp.sh` uses
RTSP-over-TCP and FFmpeg to decode three frames into the null muxer. An external
wall-clock watchdog bounds connection, I/O, demux and decode across FFmpeg
versions; compact JSON reports the requested and decoded counts without printing
the endpoint, and no frame pixels are retained. A successful probe plus a
passing health report is the minimum camera coexistence evidence. Raw camera
captures must not be added to this package.

The camera on the bring-up bench was dangling with its translucent lens cap
installed. Successful decoding therefore proves only CSI/ISP/encoder/network
transport; the pixels are not evidence of focus, orientation, color, exposure,
or scene-understanding quality.

## Personality-driven face service

After cross-building `libsherman_procedural_eyes_c.so` and
`libsherman_personality_c.so` with the pinned ARM toolchain on build-host, deploy
the tested runtime and boot service from the repo root:

```sh
firmware/linux/luckfox-ultra-w/bin/deploy-face.sh \
  robot-host /path/to/libsherman_procedural_eyes_c.so \
  /path/to/libsherman_personality_c.so
ssh robot-host /etc/init.d/S99sherman-face status
```

The service starts after the SPI overlay is loaded, then runs the bounded
30-fps face loop at the measured 40 MHz clock. Production boot mode is native
autonomous personality/idle behavior; the vocabulary-cycle demo is never
selected by init. Native personality runs at 10 Hz, and both loops drop stale
work rather than accumulate a queue. The service uses the explicitly configured
POSIX timezone `EST5EDT,M3.2.0/2`, which target libc applies without a zoneinfo
database. Provisioning can change this field without changing personality.

The native personality ABI and output values are validated before use. If the
personality library or a step fails, the default field profile keeps safe calm
eyes alive and reports `personality_degraded`; qualification can set
`personality_required` to fail the service instead. The checksummed, 4096-byte
bounded restart state lives on the persistent ext4 partition at
`/userdata/sherman/personality.state`, is atomically replaced at most every five
minutes, and is also saved on orderly shutdown. No physical action resumes from
that presentation state.

`stop` sends `SIGTERM`, allowing the state save and backend blank/backlight
cleanup paths to run. `/opt/sherman.previous` is retained as the one-deployment
software rollback; the deployment transaction also restores the prior init
script and face config on failure. The preserved boot/config backup remains the
pinmux rollback. Boot readiness allows up to ten seconds but detects an early
process exit immediately. A deployment is accepted only after bounded health
reports native personality mode without degradation. Startup failure evidence
is kept in `/run/sherman-face.startup-diagnostic`; deployment copies it to
`/run/sherman-face.deploy-failure` before restoring and restarting the prior
service.

## Backup and rollback

The preserved pre-change files on build-host are:

```text
/home/example/backups/robot-host/2026-08-19/boot-before-spi.img
/home/example/backups/robot-host/2026-08-19/luckfox.cfg.before-spi
```

The boot image is exactly `33,554,432` bytes with SHA-256
`6516d188102760d459dff2dd8a664f4a44b0d9bf5ff97f64dbf60643cdfeee8b`.
The config SHA-256 is
`8b0a329ac46d3e9540410edf2a6387cb8a8054573502626834a8bda5993bd612`.

While the target is bootable, stream the known-good files back through the Mac
SSH aliases and reboot:

```sh
ssh build-host 'cat /home/example/backups/robot-host/2026-08-19/boot-before-spi.img' \
  | ssh robot-usb 'dd of=/dev/block/by-name/boot bs=1M conv=fsync'
ssh build-host 'cat /home/example/backups/robot-host/2026-08-19/luckfox.cfg.before-spi' \
  | ssh robot-usb 'dd of=/etc/luckfox.cfg conv=fsync'
ssh robot-usb 'sync; reboot'
```

If the target does not boot, use the boot button/download-mode procedure from
build-host and restore the vendor image:

```sh
cd /home/example/src/luckfox-pico
sudo ./rkflash.sh boot \
  /home/example/firmware/luckfox-ultra-w-250607/Luckfox_Pico_Ultra_W_EMMC_250607/boot.img
```

The SDK script invokes `upgrade_tool di -b` and resets the target. Restore the
saved `/etc/luckfox.cfg` after SSH returns. A full `update.img` flash is a last
resort because it also replaces rootfs and user data.

## Known limitations and next evidence

- `16 MHz` remains the conservative fallback and needs `54.4 ms` of ideal wire
  time for one `108,800`-byte full frame. The deployed 40 MHz configuration ran
  the confirmed animation and camera concurrently without SPI/kernel errors.
  At 40 MHz, full frames averaged `31.81 ms`;
  the bounded `85,536`-byte face region typically transfers in about `23.9 ms`
  and sustains 30-fps animation after startup while the camera and RTSP run.
- The user confirmed the production-quality animation showed no visible issue.
  A future harness revision still needs formal cable-margin/signal-integrity
  capture; `16 MHz` remains the immediate fallback if that wiring changes.
- DC/RST/BL boot levels and BL-off-until-ready behavior remain unqualified.
- The recorded PCB revision, physical measurements, current, and mass remain
  open receiving fields.
- RTSP proves the vendor camera path, not Sherman's future bounded camera
  contract, timestamp semantics, privacy controls, or calibration.
- The live configuration is a bring-up baseline, not the required reproducible
  production device-tree patch.

## Local tests

```sh
sh -n bin/health-check.sh bin/probe-rtsp.sh init/S99sherman-face \
  tests/health-check_test.sh tests/probe-rtsp_test.sh \
  tests/face-service_test.sh tests/fixtures/start-stop-daemon
tests/health-check_test.sh
tests/probe-rtsp_test.sh
tests/face-service_test.sh
python3 -m unittest discover -s tests -p '*_test.py'
```

Rollback for this repository package is simply deletion of
`firmware/linux/luckfox-ultra-w/`; it has no automatic deployment behavior.

## Speaker and generated dialogue

The independent `S99sherman-banter` service uses the native ALSA codec and the attached
1 W, 8 ohm speaker. `bin/deploy-banter.sh` installs it to `/opt/sherman-banter`, leaving
face deployments independent. `/etc/sherman/banter.json` owns the Jarvis API address,
response-device ID, audio output and randomized interval. See the
[banter guide](../../../personality/banter/README.md) from the repository root at
`personality/banter/README.md` for provisioning, operation, tests and rollback.
