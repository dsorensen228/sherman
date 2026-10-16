# Controller wire contract v1 (draft)

Canonical vocabulary/layout: `../schema/controller-v1.json`; generated C++:
`firmware/controller/include/sherman/wire_generated.hpp`; Python codec reads the
same schema. This first controller version has no prior supported version. Existing
banter schemas are independent. Schema changes require a new compatible negotiation
or major version; unknown versions/types or extra fields fail closed in this fixed
safety protocol rather than being interpreted as motion.

## Frame

UART0 115200, 8N1, 3.3 V. Every multi-byte field is little-endian.

| Offset | Size | Meaning |
| --- | --- | --- |
| 0 | 2 | sync A5 5A |
| 2 | 1 | version = 1 |
| 3 | 1 | message ID |
| 4 | 2 | payload byte count, 0..64 |
| 6 | 4 | sequence (commands strictly increasing, no wrap) |
| 10 | 8 | controller boot-session random nonce |
| 18 | N | payload, fixed exact size from schema |
| 18+N | 2 | CRC16/CCITT-FALSE, poly 0x1021, init FFFF, no reflection/xor, covers offset 2 through payload |

Max frame is 84 bytes; inter-byte timeout is 20 ms. A corrupt frame is discarded;
subsequent sync or a gap permits recovery. Any parser/UART error latches a fault.
This UART is a trusted physical link, not a cryptographically authenticated network.

## Authority

Read STATUS first for nonce and current Pico uptime. HELLO echoes profile
1462820865 and that nonce with sequence >=1. Each command consumes its sequence,
including rejected commands; duplicate/out-of-order/wrapped values latch a fault.
HELLO always disarms and clears heartbeat authority; it does not clear a fault or
reset the last sequence. Reboot creates a new nonce and disarmed state.

HEARTBEAT, ARM and TWIST carry an **absolute uint32 Pico-clock deadline_ms**.
Remaining time must be 1..100 ms using modulo subtraction; do not send Linux wall
clock or grant TTL at receipt. Synchronize from fresh status and account for link
latency; a lost/stale status means no motion. An ARM is single-use, requires a
fresh heartbeat and healthy qualified sensors, and itself expires if no TWIST
arrives. Every TWIST must also arrive before the previous command expires.
HEARTBEAT cannot revive expired authority. No raw duty/PWM command exists.

TWIST holds linear mm/s, angular mrad/s, acceleration mm/s² and an action ID for
correlation. Absolute immutable simulation maxima: each wheel 40 mm/s, angular
500 mrad/s, acceleration 100 mm/s², duty 25%. Both wheel targets must be >=0:
front-only W1 coverage does not authorize reverse or in-place pivot. These values
are illustrative until measured and are **not a physical operating envelope**.
CONFIGURE_LIMITS accepts positive values up to these maxima only while disarmed.

STOP has empty payload and is honored even with stale sequence/wrong session;
it never grants authority, clears current drive and heartbeat, and is idempotent.
CLEAR_FAULT works only while disarmed, with a qualified healthy profile, then
requires a fresh heartbeat/arm. No host command can qualify a physical profile.
SELF_TEST only computes sensor/precondition health; it never toggles an actuator.
STATUS communicates acceptance via last_sequence, rejected counter, faults and
armed state; no positive ACK is required for a local stop. Fault first-occurrence
uptime persists until explicit successful clear. Fault bits come from the schema.

## Telemetry

STATUS/SENSORS/ODOMETRY rotate nominally every 20 ms (each about 16.7 Hz), with a
common boot nonce and independent device TX sequence. Uptime and sample ages use
the Pico clock; link loss is detected on the host independently. Unknown TX types
are not motion authority. Outbound full-buffer frames are dropped, never queued
without bound. USB text reports drops and maximum observed loop time.

SENSORS validity bits 0/1/2/3 mean fresh left cliff/right cliff/IMU/power respectively;
input bits 0/1 mean CHARGE_ABSENT/driver nFAULT high. Stale/failed values remain for
diagnosis but MUST NOT be used as valid observations. Freshness is <50 ms for
cliffs/IMU and <500 ms for power. Voltage is mV, SOC hundredths of percent,
acceleration mg, gyro milli-degrees/s. Gyro saturation invalidates IMU in this draft.
CLIFF flags and samples are uncalibrated for physical safety until P3-CLF-001.

ODOMETRY ticks are modulo uint32 raw quadrature counts (interpret differences as
signed), left/right speeds are signed mm/s, integration interval is ms and invalid
transition count saturates at 65535. The unqualified target's scale and polarity
are illustrative; use raw counts for bench characterization. No global pose,
current sensing, charge-current measurement or calibrated wheel odometry is claimed.
