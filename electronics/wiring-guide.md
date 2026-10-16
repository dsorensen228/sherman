# Sherman Prototype Wiring and Bring-Up Guide

**Packet:** `P3-WIR-001` (Phase 3 enabling packet)
**Revision:** `W1`, updated 2026-09-01
**Status:** W1 architecture draft implementing accepted
[ADR 0004](../docs/decisions/0004-zero-touch-charging-and-autonomous-dock.md).
Stages A and B are released. Stage C is
conditional on the UART4 M0 device-tree and pinmux proof below. Stage D is
electrically specified with the documented XSHUT startup caveat. Stages E, F,
and G remain gated. The automatic charge-interlock PCBs and two-board population
kit are ordered but not received or bench-qualified. This is not yet a released
full harness.

This is the canonical wiring packet for the exact modules in the Sherman
shopping list. It preserves the already working LCD and CSI camera wiring and
assigns every remaining carried signal without reusing a pin or mixing a 5 V
signal with 3.3 V logic. The machine-readable companion is
[`prototype-netlist.csv`](prototype-netlist.csv).

Throughout this repository, **the Pico** means the Raspberry Pi Pico 2 and **the
Luckfox** means the Luckfox Pico Ultra W. Never shorten the Luckfox board's full
name to “the Pico.” The word **pin** means the physical, numbered board pin.
`GPn` means a Pico GPIO. A Luckfox name such as `GPIO1_B2` is a Rockchip SoC
signal, not a physical pin number.

## 1. Exact hardware covered

| Function | Exact installed/candidate item | Quantity used |
| --- | --- | ---: |
| Linux compute | Luckfox Pico Ultra W, 256 MB wireless | 1 |
| Face | Waveshare 1.9inch LCD Module, SKU 23822, ST7789V2 | 1 |
| Camera | Luckfox SC3336 3MP Camera (B), SKU 25553 | 1 |
| Front range | Pololu VL53L5CX carrier #3417 | 1 |
| Safety controller | Raspberry Pi Pico 2, non-wireless | 1 |
| Cliff range | Pololu VL53L4CD carrier #3692 | 2 |
| IMU | Pololu LSM6DSO carrier #2798 | 1 |
| Motor driver | Pololu DRV8833 carrier #2130 | 1 |
| Drivetrain | Pololu #5146 motors, #4762 cables, #1087 wheels, #989 brackets | 2 each |
| 5 V rail | Pololu U3V70F5 #2891 | 1 |
| System and motor power gates | Pololu Mini Pushbutton Power Switch LV #2808 | 2: `#2808-S` system, `#2808-M` automatic motor gate |
| Cell | Adafruit protected 3.7 V 1200 mAh LiPo #258 | 1 |
| Power-path charger | Adafruit BQ24074 Universal USB/DC/Solar #4755 | 1 received + 2 incoming; V1 exterior cable, qualified spare, bench unit |
| Fuel gauge | Adafruit MAX17048 #5580 | 1 |
| Charge interlock logic | [`charging-interlock-rev-a`](pcb/charging-interlock-rev-a/README.md), TI SN74HC08N + onsemi 2N3904BU | 3 bare ordered; populate 1 installed + 1 tested spare |
| Pico-side I2C distribution | GODIYMODULES I2Chub B0DGQBFSKL | 1 passive hub |

Spares stay off the robot and are used for bounded module-swap diagnosis.

## 2. Stop rules

1. Disconnect build-host USB, Pico USB, the LiPo, and motor power before changing
   any wire. The LCD, CSI FFC, and sensor boards are not hot-plug interfaces.
2. Leave both wheels off the shafts until the restrained motor-direction step.
3. Do not put motor current through a solderless breadboard or Dupont jumper.
   Use 22 AWG power wire and a keyed, rated connector for the motor branch.
4. Do not connect the LiPo to the robot until its connector polarity has been
   checked at both ends with a meter. Adafruit warns that other JST-PH harnesses
   can have reversed polarity.
5. Never connect external `5V_SYS` to the Luckfox while its power USB is
   attached. Do not attach Pico USB while externally powering Pico `VSYS`
   during this bring-up. These rules avoid an unqualified back-power path.
6. The #4755 is the current charger candidate. Its `BATT/LIPO` connector
   attaches to the protected cell through the battery fuse and its separate
   `LOAD/OUT` output supplies only the compute/logic branch through a second
   system fuse. A separate fused-battery branch supplies the motors through the
   automatic `#2808-M` gate. The #4410 is not installed in the
   robot. Before connecting the #258 cell, cut the #4755 factory 1.0 A charge
   jumper and close only its 0.5 A jumper; Adafruit limits this exact cell to a
   500 mA charge rate. Do not select 1.0 A or 1.5 A.
7. Applying valid charger input must automatically force `#2808-M` off and
   DRV8833 `nSLEEP` low in hardware. Firmware also disarms, but no user action or
   healthy firmware is required to inhibit motion. If either inhibit does not
   assert on charger insertion, stop; the one-action charging gate has failed.
8. Neither #2808 is an emergency disconnect. `#2808-M` is an automatic motor
   power gate whose `CTRL` input is held low by default and may turn on only
   through the hardware charge interlock after a fresh Pico arm request. Pololu
   also warns that interrupting current can create damaging spikes; the gates
   are not substitutes for qualified transient suppression.
9. Stop immediately for a reversed rail, unexpected continuity to ground,
   smoke/odor, cell swelling, a hot wire/connector, repeated resets, an
   uncontrolled motor pulse, or a driver/regulator too hot to touch.

## 3. Electrical architecture

The principal voltage and interlock nets are:

| Net | Nominal range | Source | Consumers |
| --- | --- | --- | --- |
| `VBAT_RAW` | 3.0-4.23 V | protected Adafruit #258 connector | battery-fuse input only; no positive branch before this fuse |
| `VBAT_FUSED` | 3.0-4.23 V | selected battery-fuse output | #4755 `BATT/LIPO`, #5580 battery-voltage sense, and `#2808-M` motor-gate input |
| `LOAD_RAW` | about 3.0-4.4 V | #4755 `LOAD/OUT` power-path output | system-fuse input only |
| `LOAD_FUSED` | about 3.0-4.4 V | selected system-fuse output | `#2808-S` input |
| `SYS_SW` | about 3.0-4.4 V | `#2808-S` switched output | U3V70F5 input only |
| `MOTOR_VIN` | 0 V with charge input or without a fresh arm; 3.0-4.23 V qualified undocked | `#2808-M` output | DRV8833 `VIN` only |
| `5V_SYS` | 5 V | U3V70F5 output | Luckfox 5 V input and Pico 2 `VSYS`; **not used during USB bench bring-up** |
| `3V3_PICO` | 3.3 V | Pico 2 pin 36 | Pico-side I2C sensors and both encoders only |
| `CHARGE_IN_5V` | nominal 5 V | exterior USB-C or dock-switched power | #4755 input and immediate hardware input-presence detector |
| `CHARGE_ABSENT` | 3.3 V logic | 10 kOhm pull-up, pulled low by #4755 `PGOOD` or VBUS-sense Q1 | both interlock AND gates and Pico GP6 |

The Luckfox front ToF uses the Luckfox header's 3.3 V rail, named
`3V3_LUCKFOX`. Do not join `3V3_LUCKFOX` to `3V3_PICO`. All grounds join at the
power-distribution/driver area; the two 3.3 V regulator outputs do not.

For initial firmware bring-up, keep the architecture split:

- build-host USB powers the Luckfox, display, and camera. It powers the front ToF
  only after the Luckfox 3.3 V rail passes the Section 7 entry gate.
- Pico USB powers the Pico, cliffs, IMU, fuel-gauge logic, and encoders.
- DRV8833 `VIN` and both motors remain disconnected until Section 11.
- Join Luckfox P1 pin 9 and Pico pin 3 through the UART ground wire before
  joining TX/RX. P1 pin 6 is reserved for one separately rated final-power
  return termination. There is no UART level shifter because both interfaces
  are 3.3 V.

## 4. Canonical Luckfox allocation

The Ultra W has two separate 26-pin GPIO header strips, P1 and P2. All numbered
Luckfox pins below are on **P1**; P2 is reserved and is not used in revision W1.
Do not choose the strip or infer pin 1 from USB/Ethernet orientation. Find the
board's P1 and pin-1 markings, reconcile them with Luckfox's official Ultra W
pin-distribution drawing, and put an orientation label on the harness before
adding a wire. The existing verified LCD wires are an additional cross-check,
not a substitute for the markings. Its six control/data pins must not be
repurposed.

| P1 pin | SoC function | Sherman net | Direction at Luckfox | Notes |
| ---: | --- | --- | --- | --- |
| 1 | 3.3 V | `LCD_3V3` | power | Existing verified wire |
| 2, 4 | 5 V | `5V_SYS` | power input | Final power only; two equal 22 AWG leads; never with USB power |
| 3 | `GPIO1_A0 / I2C2_SCL_M0` | `FRONT_SCL` | bidirectional/open drain | New; clock stretching allowed |
| 5 | `GPIO1_A1 / I2C2_SDA_M0` | `FRONT_SDA` | bidirectional/open drain | New |
| 6 | GND | `GND_POWER` | power | One separately rated final 5 V return termination; not the UART ground |
| 7 | `GPIO1_B0 / UART4_RX_M0` | `HOST_RX` | input | New; receives Pico `GP0/TX`; gated on UART4 M0 proof |
| 8 | `GPIO1_B2 / UART2_TX_M1` | reserved | no connection | Active FIQ/debug console; never use as controller link |
| 9 | GND | `GND_UART` | power | New common reference to Pico pin 3 |
| 10 | `GPIO1_B3 / UART2_RX_M1` | reserved | no connection | Active FIQ/debug console; never use as controller link |
| 11 | `GPIO1_B1 / UART4_TX_M0` | `HOST_TX` | output | New; crosses to Pico `GP1/RX`; gated on UART4 M0 proof |
| 12 | `GPIO1_C6` | `FRONT_INT_N` | input | New; sensor output is open drain |
| 13 | `GPIO1_D0` | `LCD_DC` | output | Existing verified wire; gpiochip1 offset 24 |
| 14 | GND | `FRONT_GND` | power | New front-ToF return |
| 15 | `GPIO1_D1` | `LCD_RST_N` | output | Existing verified wire; gpiochip1 offset 25 |
| 16 | `GPIO2_A7` | `FRONT_I2C_RST` | output | New; active high, sensor carrier pulls low; current live profile verified unclaimed |
| 17 | 3.3 V | `FRONT_3V3` | power | New; feeds #3417 `VIN` |
| 18 | `GPIO2_A6` | `FRONT_LPN_N` | open-drain-style output | New; drive low or release/input; current live profile verified unclaimed |
| 19 | `GPIO1_C2 / SPI0_M0_MOSI` | `LCD_MOSI` | output | Existing verified wire |
| 20 | GND | `GND_POWER` | power | One of two final 5 V return leads |
| 21 | `GPIO1_C3 / SPI0_M0_MISO` | reserved | no connection | Keep reserved inside the active display SPI group |
| 23 | `GPIO1_C1 / SPI0_M0_CLK` | `LCD_CLK` | output | Existing verified wire |
| 24 | `GPIO1_C0 / SPI0_M0_CS0` | `LCD_CS_N` | output | Existing verified wire |
| 25 | GND | `LCD_GND` | power | Existing verified wire |
| 26 | `GPIO1_D2` | `LCD_BL` | output | Existing verified wire; gpiochip1 offset 26 |

The SC3336 remains only on its keyed CSI connector/FFC. Its sensor-control bus is
the already verified `I2C4_M2` on `GPIO3_C7/GPIO3_D0`; those signals are not on
this W1 harness.

### Conflict result

- SPI0 M0 is complete on P1 pins 19/23/24; MISO on pin 21 stays disabled.
- I2C2 M0 is complete on P1 pins 3/5 and does not overlap SPI0 M0 or CSI I2C4 M2.
- UART2 M1 on P1 pins 8/10 is the active FIQ/debug console and stays physically
  unconnected. It must never carry the framed controller link.
- UART4 M0 is complete on P1 pins 7/11. The deployed tree currently disables
  UART4, so those pins cannot be wired until the enablement and live proof below
  pass.
- LCD GPIOs 13/15/26 and front-ToF GPIOs 12/16/18 are unique in the current
  live profile. Live pinctrl inspection verified `GPIO2_A6` and `GPIO2_A7` are
  both MUX/GPIO unclaimed and I2C3 is active on M2, not M0.
- Parallel RGB remains disabled. Re-enabling it invalidates this ledger.
- P1 pin 21 and all unused P1/P2 pins stay reserved rather than becoming
  undocumented convenience GPIOs.

Enable only UART4 M0 in the board device tree; never add its M1 pin group:

```dts
&uart4 {
    pinctrl-names = "default";
    pinctrl-0 = <&uart4m0_xfer>;
    status = "okay";
};
```

The persistent deployed configuration must express the same choice with
`UART4_M0_STATUS=1`. Front-ToF release additionally requires
`I2C2_M0_STATUS=1` and `I2C2_M0_SPEED=100000`. Preserve the already verified
LCD bus as `SPI0_M0_SPEED=40000000`; a stale 16 MHz configuration is not the
deployed baseline. Treat these as image-build inputs, then verify the resulting
live tree rather than trusting the text file alone.

Before installing the three-wire link, verify the running image exposes
`/dev/ttyS4`, the live pinmux owns only P1 pins 7/11 for UART4, and no other
consumer owns either pin. Verify two-way traffic, independent reboots, and zero
boot chatter on `/dev/ttyS4` before treating it as the controller link. Any
image or overlay change reopens this gate.

## 5. Canonical Pico 2 allocation

Use the Pico 2 **with headers** for open-bench bring-up. Transfer the identical
pin map to the headerless carried Pico only after the HIL controller firmware is
proven. Physical numbering is with USB at the top, matching Raspberry Pi's
official Pico 2 pinout.

| Pico pin | GPIO/function | Sherman net | Direction at Pico | Connected module |
| ---: | --- | --- | --- | --- |
| 1 | `GP0 / UART0_TX` | `HOST_RX` | output | Luckfox P1 pin 7 / UART4 M0 RX |
| 2 | `GP1 / UART0_RX` | `HOST_TX` | input | Luckfox P1 pin 11 / UART4 M0 TX |
| 3 | GND | `GND_UART` | power | Luckfox P1 pin 9 |
| 4 | `GP2` | `CTRL_READY` | output | Reserved test point; no Luckfox wire in W1 |
| 5 | `GP3` | `MOTOR_RAIL_REQUEST` | output/default low | charge-interlock AND gate; never direct to `#2808-M` |
| 6 | `GP4 / I2C0_SDA` | `SAFE_SDA` | bidirectional | both cliffs, IMU, MAX17048 |
| 7 | `GP5 / I2C0_SCL` | `SAFE_SCL` | bidirectional/open drain | both cliffs, IMU, MAX17048; clock stretching allowed |
| 8 | GND | `GND_LOGIC` | power | sensor ground star |
| 9 | `GP6` | `CHARGE_ABSENT` | input | hardware charger-present state; low means motor inhibit |
| 11 | `GP8 / PWM4_A` | `MOTOR_L_IN1` | output | DRV8833 `AIN1` |
| 12 | `GP9 / PWM4_B` | `MOTOR_L_IN2` | output | DRV8833 `AIN2` |
| 13 | GND | `GND_DRIVER_LOGIC` | power | DRV8833 GND |
| 14 | `GP10 / PWM5_A` | `MOTOR_R_IN1` | output | DRV8833 `BIN1` |
| 15 | `GP11 / PWM5_B` | `MOTOR_R_IN2` | output | DRV8833 `BIN2` |
| 16 | `GP12` | `MOTOR_SLEEP_REQUEST` | output/default low | charge-interlock AND gate; gate output drives DRV8833 `nSLEEP/SLP` |
| 17 | `GP13` | `MOTOR_FAULT_N` | input/pull-up | DRV8833 `nFAULT/FLT`; defer cross-domain 10 kOhm pull-up until Section 11 |
| 18 | GND | `GND_ENCODER` | power | both encoder green wires |
| 19 | `GP14` | `ENC_L_A` | input | left #4762 yellow wire |
| 20 | `GP15` | `ENC_L_B` | input | left #4762 white wire |
| 21 | `GP16` | `ENC_R_A` | input | right #4762 yellow wire |
| 22 | `GP17` | `ENC_R_B` | input | right #4762 white wire |
| 23 | GND | `GND_SENSOR` | power | additional sensor return if needed |
| 24 | `GP18` | `CLIFF_L_XSHUT_N` | open-drain-style output | left #3692 `XSHUT` |
| 25 | `GP19` | `CLIFF_R_XSHUT_N` | open-drain-style output | right #3692 `XSHUT` |
| 26 | `GP20` | `CLIFF_L_INT_N` | input | left #3692 `GPIO1` |
| 27 | `GP21` | `CLIFF_R_INT_N` | input | right #3692 `GPIO1` |
| 28 | GND | `GND_SENSOR` | power | sensor return |
| 29 | `GP22` | `IMU_INT1` | input | #2798 `INT1` |
| 30 | `RUN` | `CTRL_RUN_N` | reset input | reserved test point; do not connect to Luckfox directly |
| 31 | `GP26` | `IMU_INT2` | input | #2798 `INT2/DEN` |
| 36 | `3V3(OUT)` | `3V3_PICO` | power | encoders and all Pico-side sensor `VIN` pins |
| 38 | GND | `GND_POWER` | power | power-tree return |
| 39 | `VSYS` | `5V_SYS` | power input | connect only in battery-power stage; not while Pico USB is attached |

GP7, GP27, and GP28 remain unassigned spares. Do not consume them
without updating both this table and the netlist.

## 6. Pico-side I2C bus

Wire all four modules in parallel to `SAFE_SDA`, `SAFE_SCL`, `3V3_PICO`, and
ground. Powering each carrier's `VIN` from 3.3 V makes its level-shifted bus
3.3 V. Do not power a carrier's `VIN` from 5 V; that would pull its bus high to
5 V. On the delivered Adafruit #5580, use the physical pad silk-screened `SDA`
for the I2C data connection.

| Module | I2C address at reset | Extra wires | W1 operating address |
| --- | --- | --- | --- |
| Left Pololu #3692 VL53L4CD | `0x29` | `XSHUT` to GP18; `GPIO1` to GP20 | `0x2A` |
| Right Pololu #3692 VL53L4CD | `0x29` | `XSHUT` to GP19; `GPIO1` to GP21 | `0x2B` |
| Pololu #2798 LSM6DSO | `0x6B` (carrier pulls SA0 high) | `INT1` GP22; `INT2` GP26 | `0x6B`, verify by scan |
| Adafruit #5580 MAX17048 | `0x36` | battery JST only | `0x36` |

The carriers pull `XSHUT` high, while Pico pins are inputs during reset. W1
therefore expects a brief startup window in which both sensors are awake at
`0x29`; wiring alone cannot truthfully guarantee "boot with XSHUT low." Firmware
must make GP18/19 low its earliest GPIO initialization and perform no I2C
transaction before that completes. It must then treat both signals as low or
high impedance: drive low to shut down, release the left sensor alone and
change it to `0x2A`, then release the right and change it to `0x2B`. Never drive
either line high. Motors remain asleep throughout address assignment and on any
failure. A future design may add qualified external XSHUT pull-downs if the
shared-address startup window is unacceptable.

Each carrier already contributes pull-ups. Before powering the assembled bus,
measure resistance from SDA to 3.3 V and SCL to 3.3 V and record it; parallel
pull-ups that are too strong must be corrected on the harness/module options,
not hidden with a slower firmware timeout.

## 7. Front VL53L5CX to Luckfox

The #3417 draws 100 mA typically while ranging and can peak at 150 mA. Luckfox
identifies P1 pin 17 as 3.3 V but does not publish usable current headroom for
that header rail. Therefore **do not install the `FRONT_3V3` wire yet**. First
record that the loaded Luckfox rail has at least 150 mA of additional capacity,
including the existing LCD load, without leaving its voltage tolerance,
resetting, or heating abnormally. If that cannot be established, a separately
qualified 3.3 V supply/level architecture is required and this ledger must be
revised. Do not power #3417 from 5 V while connecting its I2C pins directly to
Luckfox: the carrier pulls SDA/SCL up to `VIN` and would expose 5 V logic.

The current deployed image has also passed a live allocation check:
`GPIO2_A6` and `GPIO2_A7` were MUX/GPIO unclaimed, and I2C3 was active on M2.
Repeat that check after any device-tree/image change and verify `GPIO1_C6` is
also unclaimed before installing the optional control wires. P1 pin 21 remains
reserved as SPI0 M0 MISO even though the LCD does not currently need MISO.

After both entry gates pass, connect the Pololu #3417 exactly as follows, with
all power removed:

| #3417 pin | Luckfox P1 pin/net |
| --- | --- |
| `VIN` | P1 pin 17 / `FRONT_3V3` |
| `GND` | P1 pin 14 / `FRONT_GND` |
| `SCL` | P1 pin 3 / `FRONT_SCL` |
| `SDA` | P1 pin 5 / `FRONT_SDA` |
| `LPn` | P1 pin 18 / `FRONT_LPN_N` |
| `INT` | P1 pin 12 / `FRONT_INT_N` |
| `I2C_RST` | P1 pin 16 / `FRONT_I2C_RST` |
| `VDD` | no connection |

Remove the clear shipping liner over the sensor only when mounting and optical
testing begin. The front sensor's default address is `0x29`, but it is on the
Luckfox I2C2 bus and therefore does not conflict with the Pico-side cliff
sensors. Start I2C2 at 100 kHz; raise it only after errors and coexistence have
been measured. The `LPn` signal is also low-or-release, not push-pull high.
As a lower-risk initial configuration, leave `LPn`, `INT`, and `I2C_RST`
unconnected and poll the sole `0x29` device: the #3417 carrier pulls `LPn` high
and `I2C_RST` low, and `INT` is optional.

## 8. IMU orientation

Mount #2798 rigidly to the lower safety/motion tray, away from the motor cans
and with its silkscreen axes photographed. Record the transform into Sherman's
robot frame (`+X` forward through the face, `+Y` left, `+Z` up) before using IMU
data. Wiring alone does not establish the transform. Leave `CS`, `SDO/SA0`,
`SDx`, `SCx`, and `SDO_Aux` unconnected in W1; the carrier defaults to I2C.

## 9. Motor and encoder harness

The Pololu #4762 wire colors are part of the exact #5146 connector definition:

| #5146 connector pin | #4762 color | Function | Sherman connection |
| ---: | --- | --- | --- |
| 1 | green | encoder GND | `GND_ENCODER` |
| 2 | white | encoder B | `ENC_L_B` or `ENC_R_B` |
| 3 | yellow | encoder A | `ENC_L_A` or `ENC_R_A` |
| 4 | blue | encoder Vcc, 2.7-18 V allowed | `3V3_PICO` |
| 5 | black | motor M2 | left `AOUT2`; right `BOUT2` |
| 6 | red | motor M1 identification | left `AOUT1`; right `BOUT1` |

Keep the red/black mapping identical for the first wheels-off test. Mirrored
physical motor installation can make the wheels turn in opposite robot-frame
directions with identical electrical polarity. Record the observed direction
and use an explicit per-side inversion setting; do not silently swap colors in
one harness.

Use each unmodified #4762 12 cm pigtail's 28 AWG red/black conductors for the
short final run to its motor. Use 22 AWG only for any upstream extension from
the driver to a keyed transition into that pigtail; never claim that the
purchased pigtail itself is 22 AWG. Route each red/black pair together and keep
encoder and I2C wires away from motor outputs and the U3V70F5 switching area.
Provide strain relief at the small JST-SH motor connector. Qualify connector
and wire voltage drop and temperature during start, reverse, and bounded
stall-current pulses; motor current never uses a breadboard or Dupont lead.

## 10. Automatic charge interlock and DRV8833 logic bring-up

Keep both #2808 power inputs, DRV8833 `VIN`, all four motor outputs, the battery,
and both motors disconnected while building this logic.

![Sherman W1 automatic charging interlock wiring diagram](diagrams/charging-interlock.svg)

Three bare
[`charging-interlock-rev-a`](pcb/charging-interlock-rev-a/README.md) PCBs and
parts for two populated assemblies were ordered on 2026-09-01. Do not recreate
the U1/Q1 circuit point-to-point. Populate one `SHERMAN` candidate and one
`SPARE`; keep the third PCB bare.

Populate each board by printed reference designator:

| Reference | Exact value/part on each board |
| --- | --- |
| `R1`, `R4`, `R5`, `R6` | 10 kOhm 1% axial |
| `R2` | 47 kOhm 1% axial |
| `R3` | 100 kOhm 1% axial |
| `R7` | 4.7 kOhm 1% axial; `SLEEP_EN` output pull-down |
| `C1` | KEMET `C315C104K5R5TA`, 100 nF X7R |
| `Q1` | onsemi `2N3904BU`; board outline and device flat face aligned, `E-B-C` pins `1-2-3` |
| `U1-SOCKET` | TE `1-2199298-3`, notch aligned to the U1 outline |
| `U1` after pre-power checks | TI `SN74HC08N`, notch aligned to socket and outline |
| `J1`, `J2`, `J3` | 5, 3, and 3 positions cut from Samtec `TSW-140-07-L-S` |

Inspect the bare board first. Verify no short among `3V3`, `VBUS`, and GND,
then install `R1`–`R7`, C1, the socket, Q1, and the headers with U1 absent.
Recheck values and soldering. Apply current-limited 3.3 V only to
`J1.1/J1.2`; verify the empty socket has 3.3 V at pin 14 and GND at pin 7.
Remove power before inserting U1. Keep the battery, motor rail, driver `VIN`,
motor outputs, and motors disconnected through the truth-table test.

The PCB already routes the internal safety circuit:

1. R1 pulls `CHARGE_ABSENT` to `3V3_PICO`; #4755 `PGOOD` and Q1 can each pull
   it low. R2 feeds Q1 from raw #4755 `VBUS`, and R3 holds Q1 off when VBUS is
   absent. Raw VBUS therefore inhibits immediately while `PGOOD` provides
   redundant valid-input evidence.
2. R4 holds the GP3 request low; U1 gates it with `CHARGE_ABSENT`; R5 holds the
   `RAIL_EN` output low. Do not add a second CTRL pull-down at #2808-M.
3. R6 holds the GP12 request low; U1 gates it with `CHARGE_ABSENT`; R7 holds the
   `SLEEP_EN` output low. Do not add another 4.7 kOhm pull-down at the DRV8833.
4. U1 pins 9, 10, 12, and 13 are grounded; unused outputs 8 and 11 are isolated.
   C1 bypasses U1 directly between 3.3 V and GND.

With component-side text readable, count from each square pin-1 pad:

| PCB pin | Harness endpoint |
| --- | --- |
| `J1.1 3V3` | Pico physical pin 36 / `3V3(OUT)` |
| `J1.2 GND` | Pico physical pin 23 / GND |
| `J1.3 GP3` | Pico physical pin 5 / `GP3` |
| `J1.4 GP12` | Pico physical pin 16 / `GP12` |
| `J1.5 CA` | Pico physical pin 9 / `GP6`, input-only observer |
| `J2.1 VBUS` | Adafruit #4755 `VBUS` |
| `J2.2 PGOOD` | Adafruit #4755 `PGOOD` |
| `J2.3 GND` | Adafruit #4755 GND |
| `J3.1 RAIL` | Pololu #2808-M `CTRL` |
| `J3.2 SLEEP` | DRV8833 `SLP/nSLEEP` |
| `J3.3 GND` | driver/power-gate GND |

Continuity-check endpoints rather than relying on ribbon colors. Firmware never
drives `J1.5 CA`. Separately connect Pico GND to DRV8833 GND, GP8/9 to
`AIN1/AIN2`, and GP10/11 to `BIN1/BIN2`; add four external 10 kOhm pull-downs
at those driver inputs. Those four resistors are not positions on the interlock
PCB. Leave `nFAULT/FLT` and GP13 disconnected until Section 11.

The required truth table applies independently to both used AND gates:

| Charge input | Pico request | Motor-gate/SLP result |
| --- | --- | --- |
| present or uncertain (`CHARGE_ABSENT=0`) | either state | low/off |
| absent (`CHARGE_ABSENT=1`) | low, reset, or broken wire | low/off |
| absent (`CHARGE_ABSENT=1`) | explicit high request | high/on candidate |

Power the Pico only. Verify `J3.1 RAIL` and `J3.2 SLEEP` remain low through
reset, flashing, watchdog reset, and interlock power removal. Then command each
request high with charge input absent and verify only its matching output rises.
Apply 5 V to the #4755 input while both requests remain high: both J3 outputs
must go low without firmware participation. Remove the input and verify the
outputs do not become high unless the corresponding fresh Pico request is still
valid.

Do not cut the DRV8833 carrier's current-sense links or add sense resistors in
W1. That would be module rework and requires a separately reviewed design.

## 11. Restrained automatic motor-power bring-up

This stage needs a current-limited 2.7-4.242 V source or selected inline limiter.
Do not substitute an arbitrary wire or rely on LiPo protection.

1. With power removed, connect the limited source positive to `#2808-M VIN` and
   its return to the driver/Pico ground star. Connect `#2808-M VOUT` to DRV8833
   `VIN`; `VMM` remains a measurement output, never another supply input.
2. Connect interlock `J3.1 RAIL` to `#2808-M CTRL` and `J3.3 GND` to the
   driver/power-gate ground. PCB R5 is the output pull-down; do not add a second
   one. The #2808-M on-board pushbutton is not a user control and must not
   override a low `CTRL`; prove this before motors are attached. Any override
   behavior rejects #2808-M for this role.
3. Keep FLT disconnected and power domains separately. With Pico/interlock
   unpowered, `MOTOR_VIN` and VMM must stay approximately 0 V. With Pico powered
   but requests low, they must also remain 0 V. With the motor source present,
   Pico `3V3` and `VSYS` must not be back-powered.
4. Remove power, install FLT to GP13 with a 10 kOhm pull-up to `3V3_PICO`, and
   repeat the independent-domain tests. Isolate or level-shift FLT if any test
   fails.
5. Firmware boots with GP3, GP8-12 low and requires fresh, expiring authority.
   After admission it may assert GP3, verify `MOTOR_VIN`, then assert GP12. After
   SLP measures at least 2.5 V it waits at least 1 ms before any PWM edge.
6. With both requests high and no motors attached, insert powered USB-C into
   #4755. DRV8833 SLP must fall low within the accepted stop bound and #2808-M
   must remove motor power automatically. No button, command, or user step is
   allowed. Remove USB-C; firmware remains disarmed until a fresh arm decision.
7. Run the reset/power-order matrix at 2.7 V and 4.242 V: Pico unpowered, RUN
   reset, BOOTSEL/flash, watchdog, motor-first, logic-first, simultaneous power,
   controlled brownout, charge-input insertion/removal/bounce, `PGOOD` stuck
   low, VBUS detector open/short, and each request wire open/short. Before a
   valid arm, SLP stays at or below 0.5 V, `MOTOR_VIN` stays absent, GP8-11 stay
   low, and no H-bridge pulse or back-power occurs.
8. Remove power, connect one motor without its wheel, restore power, and use a
   bounded low-duty pulse. Insert charge input during the pulse and verify stop.
   Repeat for the other motor, then both motors, including reverse and turn.
9. Verify UART loss, Luckfox reboot, Pico reset, charger insertion, and dock-
   power bounce all return both inhibit paths to disabled.
10. Install wheels only on a restrained/tethered chassis above a sacrificial
    surface.

The #5146 theoretical stall current is 0.67 A per motor at 6 V; stalls can
damage the motor or gearbox. W1 does not authorize an unbounded stall test.

## 12. Zero-touch battery and charging power tree (gated)

The intended physical sequence is:

```text
Exterior USB-C 5 V ------------------------------+
                                                  +-> #4755 charge input
Dock-switched 5 V -> proved four-contact dock ---+

Adafruit #258 cell -> verified-polarity connector
  -> battery fuse, physically close to cell-positive -> VBAT_FUSED
       +-> #4755 BATT/LIPO
       +-> #5580 BAT+ sense (second gauge JST unused)
       `-> #2808-M VIN
              -> #2808-M VOUT = MOTOR_VIN -> DRV8833 VIN

#4755 LOAD/OUT -> system fuse -> #2808-S VIN
  -> #2808-S VOUT = SYS_SW -> #2891 VIN -> 5V_SYS
       +-> Luckfox P1 pins 2 and 4; returns on P1 pins 6 and 20
       `-> Pico VSYS

#4755 VBUS + PGOOD -> charge detector -> CHARGE_ABSENT
CHARGE_ABSENT + Pico GP3  -> hardware AND -> #2808-M CTRL
CHARGE_ABSENT + Pico GP12 -> hardware AND -> DRV8833 SLP
```

Cell negative, #4755 GND, #5580 BAT-, both #2808 grounds, #2891 GND,
interlock GND, DRV8833 GND, Pico pin 38, and Luckfox P1 pins 6/20 share the
qualified power ground. The #5580 only senses `VBAT_FUSED`; no system or motor
current passes through its small JST pass-through.

### V1 cable behavior

The only normal user action is plugging powered USB-C into Sherman's exterior
charge port. VBUS immediately pulls `CHARGE_ABSENT` low, hardware removes the
motor rail and drives SLP low, firmware observes the state and enters
`CHARGING`, #4755 powers the compute branch, and the installed cell charges.
Sherman remains powered and responsive if it was already on. No shutdown,
switch, disarm command, shell opening, battery handling, or separate motor
control is part of this workflow.

Unplugging charge power removes the hardware inhibit, but does not itself command
motion: fresh Pico motion authority is still required. An internal battery
service connector may be used during maintenance only; it is not a charging
control.

### Fast-follow dock behavior

The dock is a rear-entry target Sherman backs into. Its interface has at least
four contacts: ground first-mate/last-break, dock-switched 5 V, current-limited
pilot/identity, and open-drain release request. Dock 5 V defaults off. Stable
pilot proof permits the dock controller to energize 5 V, after which the same
VBUS hardware path stops and inhibits motion.

When the battery policy reaches its departure threshold, Sherman asserts release
request. The dock removes 5 V and reports/permits verification; Sherman verifies
VBUS and `PGOOD` are absent, waits through the qualified debounce interval,
obtains fresh motion authority, and drives forward off on battery power. If 5 V remains,
hardware keeps both motor inhibits active and Sherman reports a dock fault.

### Charger and current constraints

The #4755 1.5 A `LOAD/OUT` limit now covers compute/logic only, not motors. It
must still pass Luckfox boot, display, camera, front ToF, Pico, sensors, and the
accepted responsive charging workload with margin. If it does not, #4755 is
rejected and replaced by a higher-capacity power-path charger; no user step,
system-off requirement, or nonresponsive charging mode is an acceptable fix.

The #4755 ships at 1.0 A charge current. Before mating #258, verify that the
1.0 A jumper is cut and only 0.5 A is closed. Leave the default input-current
limit unchanged unless reviewed. As compute approaches the input-current limit,
charge current falls and battery supplement can occur; verify termination under
the accepted live workload rather than relying on LEDs alone.

On `#2808-S`, the normal momentary button connects A to B. Leave ON/OFF/CTRL
unconnected. On `#2808-M`, A/B are not user controls and CTRL is continuously
owned by the interlock. On #2891, leave ENABLE open so its pull-up enables the
regulator. Verify the module marking before relying on 5 V output.

Do **not** connect the cell or `5V_SYS` until all of the following are recorded:

- battery polarity/protection and bidirectional battery-fuse behavior;
- selected battery and compute-system fuses, ratings, drops, and trip behavior;
- automatic interlock truth table and default-off results for every power order;
- independent proof that either motor-rail cutoff or SLP inhibit prevents motion
  with charger input present;
- charge-input insertion during forward/reverse/turn stops within the accepted
  bound with no pulse on removal;
- local bulk/transient suppression on motor and boost branches from recorded
  startup, braking, charge-insertion, and switch-off waveforms;
- compute-only #4755 `LOAD/OUT` current below 1.5 A with margin during boot and
  the accepted responsive charging workload;
- motor start/reverse/stall-pulse and total cell current below the qualified
  battery, lead, connector, fuse, and #2808-M envelope;
- `5V_SYS` at 4.8-5.2 V and qualified Luckfox P1 current sharing/temperature;
- exterior USB-C insertion/removal/back-power and strain tests;
- dock pilot, release, default-off power, sequencing, bounce, bridge, short,
  reset, and autonomous departure tests;
- charge termination without DPPM/battery supplement under the accepted live
  workload; and charger, boost, gate, contact, and battery temperatures within
  limits.

Manufacturer suppression guidance supplies starting points, not a finished
design. Select capacitors, Schottky, TVS, and wiring from recorded transients.
If either the #4755 compute envelope or #258 cell/lead envelope fails, replace
the affected charger, cell, connector, or power architecture. Never recover by
adding a user charging step or installing a larger fuse.

## 13. Step-by-step full assembly order

Mark each line and preserve the readings/photos in `artifacts/phase-3/P3-WIR-001/`.

### Stage A — receiving and unpowered checks

1. Assign hardware IDs and photograph both sides of every exact module with its
   SKU/revision and a scale visible.
2. Count three charge-interlock PCBs and reconcile the nine Mouser population
   lines against the order manifest. Record the Luckfox PCB revision, Pico 2
   revision, charger revision/jumper, both #2808 revisions, SN74HC08N and Q1
   markings, battery label/protection markings, I2Chub labels, and bottom
   marking on U3V70F5.
3. Inspect every connector, FFC latch, solder joint, cell pouch, bare-PCB edge,
   annular ring, drill, solder-mask opening, and front legend. Quarantine damaged
   parts or boards.
4. With no battery or USB attached, continuity-check every ground in the
   proposed harness. Confirm no 3.3 V, 5 V, or battery positive net is shorted
   to ground and confirm `3V3_PICO` is not joined to `3V3_LUCKFOX`.
5. Verify every JST-PH red/positive and black/negative position end-to-end; do
   not trust purchased pigtail colors alone.
6. With only known-good USB power applied and no loose probes near adjacent
   pins, confirm the marked P1 strip has 5 V on physical pins 2/4, ground on
   pins 6/9/20, and 3.3 V on pin 17. Power down before continuing.

### Stage B — retain the known-good face/camera baseline

1. Do not alter the existing LCD wiring or CSI FFC.
2. Boot from build-host USB and run the existing Luckfox health check.
3. Confirm animated eyes, camera media nodes/RTSP decode, SPI at the deployed
   40 MHz setting, Wi-Fi, and normal temperature. Save the report.

### Stage C — controller link only

1. On an unwired board, enable exactly the UART4 M0 device-tree group shown in
   Section 4. Verify `/dev/ttyS4`, live pinmux ownership of only P1 pins 7/11,
   and that pins 8/10 remain the untouched FIQ/debug console.
2. Confirm UART4 emits zero boot chatter through independent cold/warm reboots.
   Any byte before the framed service opens fails the link gate.
3. With both boards off, wire P1 pin 9 to Pico ground, P1 pin 11/TX to Pico
   GP1/RX, and Pico GP0/TX to P1 pin 7/RX. Do not wire P1 pins 8/10.
4. Power both from their separate USB cables.
5. Verify neither TX nor RX exceeds 3.3 V and run bidirectional framed traffic
   with CRC/sequence counters for ten minutes.
6. Reboot each side independently and confirm the other side detects link loss;
   motor commands must expire rather than replay.

### Stage D — Pico-side sensors

1. Continuity-map the passive I2Chub, connect its 3.3 V/GND/SDA/SCL trunk to the
   Pico, and prove it does not join another voltage domain. Connect only #2798
   through one hub position. Scan and record its address; then add INT1/INT2.
2. Power off. Add the left #3692, including XSHUT/GPIO1. On boot expect the
   carrier pull-up to make it briefly visible at `0x29`; firmware must drive
   XSHUT low before any bus access, then release it, assign `0x2A`, and take
   stationary readings.
3. Power off. Add the right #3692. On boot expect both carriers briefly active
   at the shared `0x29`; firmware must first drive both low without a bus
   transaction, then assign left `0x2A` and right `0x2B`, and verify independent
   cover/uncover behavior.
4. Power off. Connect #5580 logic and its I2C wires, but leave the cell
   disconnected. It is expected not to answer without a battery.
5. Run a bus reset, cable-disconnect, stuck-device timeout, and Pico watchdog
   test. Every failure must remain bounded and motor-disarmed.

### Stage E — front sensor

1. Establish and record the Section 7 rail entry gate for the #3417's 100 mA
   typical/150 mA peak load. Do not use the Luckfox 3.3 V pin until it passes.
2. Repeat the live GPIO/pinmux gate for P1 pins 12/16/18 and prove I2C3 remains
   on M2; any conflicting owner closes this stage. Keeping all three optional
   control wires open and polling is the lower-risk initial setup.
3. Power off Luckfox and connect #3417 per Section 7.
4. Verify resistance-to-ground and no short on 3.3 V before USB power.
5. Boot with `LPn` released and `I2C_RST` low. Confirm only `0x29` appears on the
   newly enabled I2C2 bus.
6. Validate reset, interrupt, 4x4 then 8x8 readings with the sensor stationary.
7. Stress front ranging while the eyes animate and both RTSP paths decode.

### Stage F — driver and encoders

1. Complete the Section 10 interlock assembly and truth table with no driver
   motor power.
2. Connect encoder green/blue/yellow/white wires while leaving red/black motor
   wires insulated and separate. Rotate each shaft by hand and verify A/B counts.
3. Stage F remains closed until the full Section 11 reset/power/charge-insertion
   matrix, `MOTOR_VIN`/VMM/SLP/GP8-11 evidence, no-backpower checks, and selected
   local bulk/transient control all pass at 2.7 V and 4.242 V.
4. Execute the remaining Section 11 steps under restraint. Record electrical
   polarity, physical forward direction, encoder sign, fault behavior, current,
   voltage transients, and temperature.

### Stage G — power qualification and mobile harness

1. Complete every Section 12 gate on a protected bench.
2. Before connecting the #258, meter-check its polarity and verify the #4755
   factory 1.0 A charge jumper is open and only the 0.5 A jumper is closed.
3. Install both selected fuses: the battery fuse before the #4755/gauge/motor-
   gate split and the compute-system fuse immediately after #4755 `LOAD/OUT`.
4. Move logic signals from breadboard/Dupont jumpers to keyed harnesses. Keep
   motor current off breadboards and use pull-tested crimps.
5. Install the battery where it is service-removable, insulated,
   strain-relieved, and
   not heated by compute, regulator, driver, or motors. Preserve pouch swelling
   clearance; no tape or tie may compress the pouch.
6. Verify all power states: off, logic-only, automatic motor gate off/on,
   controlled shutdown, maintenance cell removal, USB service, one-action cable
   charging with compute off, and one-action charging with the qualified live
   workload. No normal charging test uses an extra switch or command.
7. Repeat camera, display, UART, I2C, encoder, reset, fault, and motor-stop tests
   after final routing. Inspect for motor-noise-correlated errors.

## 14. Harness and routing rules

- `PWR-BAT`: 22 AWG red/black, keyed two-pin connectors; the battery fuse is
  serviceable internally. Label both ends `VBAT`; it is not a user charge control.
- `PWR-LOAD`: 22 AWG red/black from #4755 `LOAD/OUT` through the separate system
  fuse to `#2808-S`. Label it `LOAD`, not `VBAT`; it can reach 4.4 V while docked.
- `PWR-MOTOR`: a separate 22 AWG branch from `VBAT_FUSED` through `#2808-M` to
  DRV8833. It never passes through #4755 `LOAD/OUT`.
- `PWR-DOCK`: at least four asymmetric contacts for ground, dock-switched 5 V,
  current-limited pilot/identity, and open-drain release request. Do not expose
  battery or `LOAD/OUT` on the dock.
- `PWR-5V`: 22 AWG red/black from U3V70F5 to a retained distribution point.
- `MOTOR-L/R`: short twisted red/black pairs; no shared connector with sensors.
- `UART`: ground plus crossed TX/RX; keep away from motor outputs.
- `SAFE-I2C`: the passive I2Chub provides a short star. SDA/SCL and ground run
  together; keep all branches short and qualify aggregate pull-ups/capacitance.
- `FRONT-I2C`: separate Luckfox harness and separate 3.3 V domain.
- Put visible test points on dock 5 V/pilot/release, `CHARGE_ABSENT`,
  `VBAT_RAW`, `VBAT_FUSED`, `LOAD_RAW`,
  `LOAD_FUSED`, `SYS_SW`, `MOTOR_VIN`, `5V_SYS`, `3V3_PICO`, both
  grounds, UART TX/RX, `MOTOR_SLEEP_N`, `MOTOR_FAULT_N`, four PWM inputs, four
  encoders, two XSHUT lines, and both I2C buses.
- Provide strain relief and service slack, but no loop can reach a wheel, motor
  shaft, sharp chassis edge, camera FFC, or optical aperture.

## 15. Required physical observations before W1 freeze

These cannot be inferred from catalog pages and remain intentionally open:

- delivered Luckfox PCB revision and at least 150 mA of measured P1 3.3 V rail
  headroom beyond the LCD/board load for #3417;
- actual P1 pin-1 orientation marked in the assembly photo;
- exact Pico 2 revision and final carried/headerless orientation;
- confirmation that the delivered LSM6DSO carrier answers at its documented
  default `0x6B` address;
- aggregate SDA/SCL pull-up resistance and reliable bus rate after routing;
- left/right cliff sensor physical assignment, height, angle, FOV, and robot
  frame transforms;
- IMU robot-frame transform;
- motor left/right assignment, physical forward polarity, encoder sign, and
  cable routing;
- delivered #4755 with its 1.0 A jumper cut and only 0.5 A closed; exterior
  USB-C fit/strain relief; and compute-only `LOAD/OUT` envelope below 1.5 A;
- chosen battery fuse/PTC and compute-system fuse/PTC exact parts;
- exact interlock assembly, #2808-M CTRL behavior, VBUS/PGOOD timing, and
  independent motor-rail/SLP stop evidence;
- chosen four-contact dock, pilot/identity and release circuits, default-off
  dock power controller, sequencing, and autonomous departure behavior;
- all rail idle/start/reverse currents, voltage sag, ripple symptoms, and
  module/battery-adjacent temperatures;
- measured Luckfox P1 5 V injection current sharing, voltage drop, and
  connector/wire temperature at worst qualified load;
- whether compute remains inside #4755's 1.5 A `LOAD/OUT` limit and total
  battery/motor current remains inside the Adafruit #258 lead's 2 A limit;
- battery placement, swelling clearance, and removal path.

Until those fields are recorded, W1 is an exact bench net assignment—not a
released mobile battery harness.

## 16. Primary manufacturer references

- [Luckfox Pico Ultra W official schematic PDF](https://github.com/LuckfoxTECH/Luckfox-Pico-docs/blob/main/Hardware/Schematic/Luckfox-Pico-Ultra-W.pdf)
- [Luckfox Ultra/Ultra W GPIO pin distribution](https://wiki.luckfox.com/Luckfox-Pico-Ultra/GPIO/)
- [Luckfox Ultra device-tree bus configuration](https://wiki.luckfox.com/Luckfox-Pico-Ultra/Device-Tree/)
- [Luckfox Ultra UART guide](https://wiki.luckfox.com/Luckfox-Pico-Ultra/UART/)
- [Luckfox SDK RV1106 pinctrl definitions](https://github.com/LuckfoxTECH/luckfox-pico/blob/main/sysdrv/source/kernel/arch/arm/boot/dts/rv1106-pinctrl.dtsi)
- [Luckfox SDK Ultra IPC device tree](https://github.com/LuckfoxTECH/luckfox-pico/blob/main/sysdrv/source/kernel/arch/arm/boot/dts/rv1106-luckfox-pico-ultra-ipc.dtsi)
- [Raspberry Pi Pico 2 datasheet](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf)
- [Raspberry Pi Pico/Pico 2 official pinout](https://datasheets.raspberrypi.com/pico/Pico-2-Pinout.pdf)
- [Waveshare 1.9inch LCD module](https://www.waveshare.com/wiki/1.9inch_LCD_Module)
- [Luckfox SC3336 Camera (B)](https://wiki.luckfox.com/SC3336-3MP-Camera/)
- [Pololu VL53L5CX carrier #3417](https://www.pololu.com/product/3417)
- [Pololu VL53L4CD carrier #3692](https://www.pololu.com/product/3692)
- [Pololu LSM6DSO carrier #2798](https://www.pololu.com/product/2798)
- [Pololu DRV8833 carrier #2130](https://www.pololu.com/product/2130)
- [TI DRV8833 datasheet](https://www.ti.com/lit/ds/symlink/drv8833.pdf)
- [Pololu #5146 motor/encoder pinout](https://www.pololu.com/product/5146)
- [Pololu #4762 six-pin motor cable](https://www.pololu.com/product/4762)
- [Pololu U3V70F5 #2891](https://www.pololu.com/product/2891)
- [Pololu Mini Pushbutton Power Switch LV #2808](https://www.pololu.com/product/2808)
- [Adafruit protected 1200 mAh cell #258](https://www.adafruit.com/product/258)
- [Adafruit BQ24074 Universal USB/DC/Solar charger #4755](https://www.adafruit.com/product/4755)
- [Adafruit #4755 pinouts and configuration](https://learn.adafruit.com/adafruit-bq24074-universal-usb-dc-solar-charger-breakout/pinouts)
- [TI BQ24074 datasheet](https://www.ti.com/lit/ds/symlink/bq24074.pdf)
- [TI SN74HC08 quad AND gate](https://www.ti.com/product/SN74HC08)
- [Adafruit MAX17048 #5580 guide](https://learn.adafruit.com/adafruit-max17048-lipoly-liion-fuel-gauge-and-battery-monitor)
