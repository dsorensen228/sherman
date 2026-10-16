# Overall Delivery Plan

## Purpose

This plan turns Sherman from an experience concept into a sequence of evidence-gated systems. It is intentionally organized so multiple agents can work in parallel without inventing competing interfaces or integrating untested hardware all at once.

## Delivery model

Sherman is built through six phases. Each phase produces a coherent, demoable system and closes a specific class of risk. A calendar date does not complete a phase; its exit evidence does.

| Phase | Coherent demo | Primary risk retired |
| --- | --- | --- |
| 0 — Personality | Deterministic desktop simulator with eyes, moods, routines, and Jarvis-like commands | Product behavior and software boundaries |
| 1 — Brain | Luckfox board drives the real eye display and maintains a resilient Jarvis link | Board, build, display, deployment, resource budget |
| 2 — Vision | Stationary Sherman creates observations, range data, tracks, and a local scene model | Camera/ToF integration and perception feasibility |
| 3 — Mobility | Restrained, then free-running chassis moves safely and avoids desk edges | Power, drivetrain, hard-real-time safety, packaging |
| 4 — World Model | Sherman patrols, revisits uncertainty, notices controlled changes, and docks or asks for help | Localization, persistence, curiosity, recovery |
| 5 — Character | Long-running daily routines make Sherman legible, useful, and endearing | Experience coherence, endurance, privacy, operability |

The detailed plans are in `docs/roadmap/phase-*.md`.

## Workstreams

### Product and behavior

Own the behavior vocabulary, mood model, eye language, routines, social contract with Jarvis, and human override semantics. This work begins in Phase 0 and supplies fixtures to every later phase.

### Platform and runtime

Own cross-compilation, boot, service supervision, configuration, logging, updates, resource budgets, and abstractions that allow identical high-level logic to run on host, simulator, and target.

### Safety and motion

Own the safety state machine, expiring motion command path, companion controller qualification, motor/encoder control, cliff sensing, watchdog, bump/contact policy, restrained testing, and recovery.

### Perception and world model

Own synchronized camera/range ingestion, calibration, observations, tracks, mapping, localization confidence, scene-change detection, storage, map decay, and replay.

### Industrial design and electronics

Own component measurements, volume and mass budgets, power tree, thermal paths, cable routing, service access, optical windows, wheel geometry, tolerance stack, prototype chassis, and assembly instructions.

### Integration and verification

Own contract tests, golden replays, scenario suites, hardware-in-loop rigs, acceptance evidence, endurance runs, release candidates, and phase-gate reviews.

## Dependency policy

1. Product vocabulary and safety states precede implementation.
2. Schemas precede producers and consumers.
3. Simulated adapters precede physical adapters.
4. Bench characterization precedes enclosure CAD freeze.
5. Restrained motion precedes free motion.
6. Deterministic replay precedes autonomy tuning.
7. Fault injection precedes endurance testing.
8. Endurance and privacy review precede habitual daily use.

## DIY build and repair policy

Sherman is assembled from replaceable development boards and breakout modules. Troubleshooting is intentionally bounded: inspect wiring/polarity/configuration, run the smallest known-good test, then swap the suspected module. If the fault follows an inexpensive module, quarantine and replace it rather than attempting component-level repair or purchasing lab equipment. Diagnose more deeply only when a replacement exhibits the same failure, because that points to a shared system problem. Replacements repeat receiving and affected safety/integration checks.

## Global technical baseline

- Target compute: Luckfox Pico Ultra W, exact SKU and revision recorded at receiving.
- Permanent development board: Ethernet, USB-C recovery, headers, and other board protrusions must remain serviceable.
- Target OS: start with vendor-supported Buildroot for reproducibility; permit an Ubuntu-based bring-up image only for exploration. Freeze one production baseline during Phase 1.
- On-device implementation: C++17 for resource-constrained services and hardware adapters; Python 3.11+ for host tools, scenario generation, analytics, and optional simulator orchestration. Any alternate language requires target toolchain and memory evidence.
- Build: CMake + Ninja for C/C++; a pinned Python environment for tooling; reproducible container or documented Linux build host.
- Contracts: versioned schemas in `proto/`; binary payloads for streaming paths and human-readable diagnostic representations.
- Testing: host unit tests, schema contract tests, deterministic simulation, recorded sensor replay, hardware-in-loop, and physical acceptance trials.

These are planning defaults, not permission to install dependencies without a work packet.

## Cross-cutting quality budgets

Each phase must publish measurements for:

- steady and peak resident memory by service;
- CPU load and worst observed scheduling latency;
- boot-to-ready time;
- message rates, queue depth, drop counts, and reconnect behavior;
- thermal steady state in the current enclosure;
- idle, active, and peak electrical power;
- log volume and storage growth;
- sensor-to-decision and decision-to-expression latency;
- fault detection and safe-stop latency.

Budget values start as hypotheses and become limits after Phase 1 and Phase 3 characterization.

## Phase gate review

Every gate uses the same review packet:

1. Scope completed and scope deferred.
2. Requirements-to-test traceability matrix.
3. Reproducible build identifier and configuration.
4. Automated test summary with raw artifacts.
5. Resource and performance measurements.
6. Safety/fault-injection results relevant to the phase.
7. Photographs or videos for physical claims.
8. Open risks ranked by severity and probability.
9. ADRs accepted during the phase.
10. Go, conditional-go, or no-go decision with named owners.

## Procurement strategy

Do not buy the whole v1 list on day one. The complete quantities, current prices, supplies, instruments, and receiving checks are in `docs/hardware/shopping-list.md` and `shopping-list.csv`. Procurement follows risk:

- Phase 1: board, debug/recovery cables, two identical Waveshare 1.9-inch landscape displays, supported camera, basic power instrumentation.
- Phase 2: supported CSI camera, front multizone ToF breakout, calibration fixtures.
- Phase 3 bench: #5146 encoder motors, #2130 driver, Pico 2 controllers, #3692 cliff sensors, #2798 IMU, #1087 wheels, and a low-cost fused/current-limited test setup using owned or borrowed tools.
- Phase 3 power/chassis: boost, battery, charger, gauge and enclosure stock only after measured component/load envelopes and power/thermal characterization.
- Charging/docking components: the one-action exterior USB-C path and automatic motor interlock are Phase 3 V1 requirements; the rear-entry four-contact dock, default-off dock controller, and autonomous release/forward-departure path are the mandatory fast follow in Phase 4.

Exact orderable candidates and substitutions live in `docs/hardware/bom.md`; the procurement quantities live in `docs/hardware/shopping-list.md`.

## Major program risks

| Risk | Early signal | Mitigation/gate |
| --- | --- | --- |
| Target envelope is too small | Connector/wheel/battery collision in layout | Parametric volume study; comfortable chassis first |
| Small display lacks usable Linux path | Poor refresh or missing driver | Phase 1 display bake-off; preserve backend abstraction |
| Linux cannot guarantee cliff-stop latency | Jitter or service stalls | Companion real-time controller owns motor enable and cliff reflex |
| Camera/NPU stack consumes memory | OOM, drops, thermal rise | Representative pipeline profiling before model selection |
| ToF fails on dark/glossy/angled surfaces | False-clear edge readings | Qualified surface matrix and heterogeneous sensing/geometry |
| Mapping is brittle at tiny scale | Drift and poor landmarks | Encoders + IMU + range/camera fusion; confidence-aware behavior |
| Battery runtime misses target | High motor/compute/display load | Measured duty cycles, power states, larger comfortable chassis |
| Personality hides failures | Cute animation masks unsafe state | Safety expressions are reserved and driven by authoritative state |
| Swarm integration stalls | Schema churn and overlapping edits | Work packets, owned paths, contract-first merge order |

## Definition of v1

Sherman v1 is achieved when one documented hardware configuration can be provisioned reproducibly, patrol a qualified desk for two hours, avoid edges under the acceptance protocol, preserve and refresh a useful local map, notice scripted object changes, interact with Jarvis through versioned contracts, communicate intent through eyes and motion, recover from defined faults, and produce an auditable session record without retaining unnecessary private imagery.
