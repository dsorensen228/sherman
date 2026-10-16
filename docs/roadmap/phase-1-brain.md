# Phase 1 — Brain, Real Eyes, and Jarvis Link

## Outcome

The exact Luckfox Pico Ultra W boots a reproducible image, supervises the Sherman runtime, renders expressive eyes on a qualified compact display, persists bounded state, and maintains a versioned resilient Jarvis connection. Sherman is stationary.

## Primary risks

Target toolchain/OS reproducibility, constrained CPU/RAM, small-display Linux support, device-tree pin conflicts, deployment/recovery, boot behavior, storage integrity, Wi-Fi reliability, and protocol reconnect semantics.

## Entry conditions

- G0 accepted and Phase 0 schemas/fixtures tagged.
- Exact board and two identical Waveshare 1.9-inch modules available; a mechanically different fallback is purchased only after a recorded failure.
- Current vendor recovery and device-tree documentation archived/linked.
- No battery required; use measured, current-capable bench/USB power.

## Work packages

### 1. Receiving and board baseline

Record model, memory, storage, Wi-Fi module, PCB revision, dimensions, mass, mounting holes, antenna, connector heights, photos, and boot/recovery behavior. Validate USB and Ethernet paths, note vendor USB-A/USB-C switching, inventory current device-tree pin use, and create a hardware profile ID.

### 2. OS and reproducible build

Evaluate the vendor-supported Buildroot path first. A temporary Ubuntu image may accelerate exploration but must not become the production baseline accidentally. Pin SDK/toolchain sources and patches, document a clean Linux build host/container, produce a hashable system image and `shermand` artifact, and capture licenses/source obligations.

### 3. Platform service

Implement lifecycle, configuration layers/hash, hardware-profile validation, structured bounded logs, metrics, watchdog/supervisor integration, orderly restart/shutdown, build info, health/readiness, time/timezone handling, and a local diagnostic CLI that cannot bypass authority.

### 4. Landscape display qualification

Qualify the Waveshare 1.9-inch SKU 23822 on the exact Ultra W: prove electrical logic, RGB-pin release/SPI pinmux, reset/backlight boot state, user-space `spidev` path, RGB565/landscape rotation, full and partial update rate, tearing, semantic-to-visible latency, CPU, memory, power, brightness, viewing angle, image retention/lifetime concerns, cable, and `51.2 × 27.3 mm` enclosure envelope. Use the same renderer contract through host and target backends. Accept/supersede ADR 0003 from recorded evidence; invoke the 1.47-inch/Adafruit fallback ladder only after a defined primary failure.

### 5. Jarvis transport

Implement authenticated-identity/pairing abstraction, version negotiation, bounded WebSocket or selected transport, schema validation, deadlines, idempotency, correlation, progress, heartbeat, exponential backoff, event cursor/reconciliation, priority spool, and diagnostic metrics. Test against emulator before real Jarvis integration.

### 6. Persistence

Spike the planning-default SQLite approach against target storage and power/process interruption. Measure binary/working-set, write amplification, latency, and recovery. Implement repository abstraction, schema migrations, atomic last-good state, retention limits, and export/erase foundations.

### 7. Target integration

Port the Phase 0 behavior/expression slice with fake world inputs. The real display shows semantic eyes; Jarvis requests simulated observation/routine actions; target health and state survive restarts according to policy.

## Resource budgets to establish

Measure, then freeze provisional Phase 2 budgets for boot time, idle and peak RSS, CPU during 30/60 fps eyes, log/storage growth, Wi-Fi reconnect cost, display power, board idle/active power, and sustained internal temperature. Keep headroom for camera, ToF, and perception; Phase 1 may not consume all available memory for visual polish.

## Failure tests

- power/process kill during boot, config read, state migration, active write, and log rotation;
- invalid hardware profile, missing display, display bus failure, renderer crash;
- Wi-Fi absent/flapping, DNS failure, wrong time, authentication rejection, server restart;
- stale/duplicate/oversized/malformed/unknown-version Jarvis messages;
- spool full and event cursor gap;
- full storage, read-only storage, corrupted last write;
- thermal/resource load while eyes and reconnect attempts run;
- supervisor restart loop protection and last-good rollback.

## Coherent demo

Cold-flash or provision a documented board, boot without developer intervention, show self-test/ready eyes, accept a Jarvis-emulator request, animate/action-progress, disconnect network while local routine continues, reconnect and reconcile without replaying commands, restart runtime, and recover persistent state. Export a bounded support bundle.

## Gate G1 acceptance

- Clean build/provision/recovery performed by someone other than the author using docs.
- The Waveshare 1.9-inch path meets the accepted latency/legibility/resource goals and fits the provisional face envelope, or ADR 0003 is explicitly superseded with equivalent evidence.
- Eight-hour target soak has no unbounded memory/log/storage growth or unrecovered service failure.
- Jarvis contract and reconnect/fuzz suites pass; network is optional for local operation.
- Storage interruption/migration suite preserves last-good data.
- Resource/thermal/power budgets leave reviewed headroom for Phase 2.
- Exact OS, board, display, build, hardware profile, and ADRs are recorded.

## Stop conditions

If no compact display provides acceptable target performance, pause and select a different face technology or relax the envelope. If the target cannot hold Phase 0 behavior + display + transport with adequate Phase 2 headroom, reduce architecture/asset footprint before buying perception hardware.
