# Implementation and draft boundaries

The source split is `protocol.cpp` (framing), `controller.cpp` (pure authority and
control), `sensors.cpp` (portable bounded drivers), and `main.cpp` (Pico SDK HAL).
There is one execution thread. Encoder ISR counters are atomically snapshotted with
interrupts briefly masked. No heap allocation is used by controller/driver code.

The loop checks safety before and after acquisition, services at most 64 RX bytes,
polls sensors nominally every 10 ms, queues one of three telemetry frames every
20 ms, and feeds the 1 s watchdog only after returning from a complete iteration.
Initialization uses a 3 s watchdog window for the bounded sensor boot polls.
The USB summary never waits for a consumer. I2C reads/writes have 2/4 ms bounds;
startup poll loops have 100 iterations maximum. No sensor data-ready wait occurs
in the runtime loop. CRC/header/timeout/UART errors latch a protocol fault.
Telemetry has one bounded 84-byte slot; full slots count drops instead of blocking.

Cliff initialization drives both XSHUT lines low before I2C, releases and addresses
one sensor at a time, verifies its model ID, performs bounded VHV calibration,
sets 20 ms continuous ranging, and rejects invalid result status/zero SPAD count.
Failed initializers shut that sensor down. LSM6DSO uses BDU/autoincrement and fresh
accel+gyro data at 104 Hz. Gyro telemetry is signed milli-degrees/s, with saturation
outside +/-32.767 degrees/s explicitly marking the sample invalid in this draft.
MAX17048 reads voltage and state of charge at 10 Hz; it does not reset fuel state.
No software battery percentage estimate is substituted when the gauge is missing.
Sensor timestamps are acquisition-completion times in the Pico clock domain.

The controller's example calibration is for deterministic simulation only. The
physical target always constructs the unqualified controller and continuously
forces six motor pins low. All W1 voltage domains, pins and hardware interlocks
remain unchanged. No runtime mechanism exists to qualify that profile. Before a
motion firmware release, add the measured profile and a reviewed driver sequencer
that verifies the rail before releasing sleep, handles direction dead time, and
meets measured stop timing. Do not reinterpret this software test as that evidence.

Safety checks run even on receipt of a fresh command: an expired command cannot
be revived by arriving at the same scheduler iteration as its replacement. STOP
clears heartbeat authority; clearing faults requires healthy qualified sensors and
fresh heartbeat/arm afterward. Unknown or malformed command types fail closed.
No partial state is stored across reset; new random boot nonce invalidates old
traffic. Protocol sequence wrap requires reboot/re-negotiation, never rollover.
