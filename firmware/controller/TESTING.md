# Validation

Run the README host build and CTest. Assertions remain enabled in Release builds.
The host suite uses strict compiler warnings, ASan and UBSan; an explicit option
can disable sanitizers only for an unsupported host, and must be recorded.

- `core`: boot/qualification, handshake mismatch, stop/idempotency, replay,
  expired and future deadlines, heartbeat loss, uint32 clock wrap, speed/reverse/
  pivot restrictions, PI output bounds, stalled/invalid encoders, ten injected
  sensor/interlock faults, latched recovery, loop overrun, and 1M random parser
  bytes with seed 531. This is a synthetic control scenario, not a plant model.
- `sensor`: physical-address isolation through fake bus, model mismatch,
  register conversion, no-ready staleness, invalid measurements, bus failure,
  and bounded startup timeout. It executes production drivers.
- `contracts`: Python encodes every schema message, C++ decodes and re-encodes
  golden bytes, Python decodes that output; malformed stream recovery,
  bounded buffering, generated-source parity and canonical W1 pin consistency.

Compile the Pico 2 target and inspect binary program identity, memory use and UF2
family. Run clang-format on hand-authored C++ and ruff on Python. Do not hand-edit
wire_generated.hpp: regenerate with `python3 proto/tools/generate_controller.py`.
Golden fixtures are reviewed protocol examples and must change explicitly with
schema evolution, not automatically during ordinary builds/tests.

Bench, with motor branch physically disconnected: identify the board; preserve
prior image; flash; read USB and UART status; confirm qualified=0/armed=0; observe
six motor pins low across boot, reset, invalid traffic and sensor unplug. Check
sensor measurements against real geometry and power; verify encoder hand rotation,
interlock state and controller-clock sample age. Test wrong/missing sensor, held
I2C bus, UART flood, power cycle and watchdog recovery. Record build hash, board
revision, pin levels, timing and log data in the packet evidence. These steps have
not been executed without the actual Pico and wiring.
