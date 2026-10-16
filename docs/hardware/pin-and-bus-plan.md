# Pin, Bus, and Electrical Interface Plan

## Rule

Do not assign pins from memory or a generic RV1106 pinout. Create the hardware profile from the exact Luckfox board revision, schematic, connector diagram, device tree, and measured logic levels. The vendor device tree is authoritative for mux conflicts in the selected OS image.

## Provisional bus allocation

| Function | Preferred owner/link | Notes |
| --- | --- | --- |
| CSI camera | Luckfox MIPI CSI | use vendor-supported sensor first |
| Face display | Luckfox SPI + GPIO/PWM CS/DC/reset/backlight | Waveshare 1.9-inch ST7789V2 primary; initial `/dev/spidev0.0` path |
| Front multizone ToF | Luckfox I2C | interrupt/reset pins desirable; driver load profiled |
| Companion controller | Luckfox UART with framing/CRC | separate reset/ready/optional hardware disable line |
| Motors/encoders | Companion controller | never direct from high-level behavior |
| Cliff sensors | Companion controller I2C/GPIO | XSHUT/address sequencing for identical devices |
| IMU | Companion controller preferred | timestamps near motor/encoder domain; alternative requires clock analysis |
| Power/fuel telemetry | Controller I2C/ADC preferred | validate levels and isolation |
| Debug | dedicated UART/USB/Ethernet as available | must remain accessible while chassis open |

## Required pin ledger

The machine-readable ledger eventually records: board header pin, SoC GPIO, voltage domain, reset state, pull, mux/function, owner, direction, active level, maximum rate, safety impact, device-tree node, harness connector/pin, and test point.

## Conflict resolution process

1. Enumerate exact pins used by boot, eMMC, Wi-Fi, camera, Ethernet, audio, the default RGB display reservation, and vendor overlays.
2. Disable the RGB display function with the supported configuration flow, then boot with only the SPI display; verify mux and electrical level.
3. Add one peripheral at a time and run a stress test while monitoring errors.
4. Generate the hardware profile and device-tree/config diff from source.
5. Reserve safety signals and recovery/debug access before convenience features.
6. Freeze the ledger with the harness drawing and continuity test.

For the target display, choose one complete SPI pin group from the exact Ultra W model device tree. Luckfox documents that alternate groups cannot be combined and shows `spidev@0` with a 50 MHz maximum while `fbtft@0` is disabled. Start at a conservative clock and increase only with captured integrity/performance evidence. CS, DC, reset, and backlight must have defined boot states; backlight remains off until a safe frame is ready.

## I2C rules

Calculate pull-up resistance/capacitance for the actual harness, logic voltage, and requested rate. Avoid long star wiring. Handle identical sensor addresses through separate enable/reset lines or a qualified mux. Recover a stuck bus explicitly and count recoveries. No sensor driver may block the safety controller loop indefinitely.

## UART rules

Use bounded binary frames with sync, length, version/type, sequence, payload, and CRC. Test false sync, truncation, corruption, flooding, reset mid-frame, and baud mismatch. Electrical idle/reset states must keep motors disabled.

## EMI/noise practices

Keep motor current loops short, twist motor leads where practical, separate sensor/camera routing from motor/boost switching nodes, add local bypass/bulk capacitance based on driver/vendor guidance, and provide test points for rails, UART, enable, PWM, encoder, and cliff signals.

## Verification

- Automated pin-ledger consistency against firmware constants and device-tree settings.
- Continuity and no-short inspection before power.
- Logic-analyzer captures for bus rates, resets, and fault cases.
- Camera/ToF/display stress while motors accelerate and reverse.
- Hot-plug only where explicitly supported; otherwise verify connector keying and warning.
- Controller reset/boot waveform proves motor-enable remains inactive.
