# Acceptance Matrix

This is the high-level traceability spine. Detailed phase documents define exact fixtures and tolerances; those values must be copied here when frozen.

| ID | Requirement/claim | Primary evidence | Phase |
| --- | --- | --- | --- |
| REQ-EXP-001 | Eye and motion state are understandable without logs | blinded expression clips + semantic contract tests | 0/5 |
| REQ-PLAT-001 | Target build and provisioning are reproducible | clean build/provision on documented host; artifact hash | 1 |
| PERF-EYE-001 | Mood-to-visible-eye latency meets `GOALS.md` target | timestamped render/display capture | 1 |
| PERF-DSP-001 | Exact face path sustains accepted eye workload without stale growth or corruption | Waveshare 1.9-inch SPI/FPS/CPU/RSS/power/soak report | 1 |
| CON-JAR-001 | Jarvis requests are versioned, validated, expiring, and reconnect safely | cross-language contract/fault suite | 1 |
| PERF-RES-001 | Representative runtime stays inside measured CPU/RAM/thermal budgets | target soak with telemetry | 1/2 |
| REQ-VIS-001 | Camera and range streams are timestamped, calibrated, and replayable | calibration report + replay equivalence | 2 |
| REQ-VIS-002 | Controlled objects/changes yield bounded-confidence observations | labeled fixture matrix | 2/4 |
| SAF-MOT-001 | Nonzero motion requires current valid authority | controller protocol tests + terminal capture | 3 |
| SAF-STOP-001 | Critical fault stops within qualified bound | kill/dropout/cliff/brownout timing captures | 3 |
| SAF-CLIFF-001 | No table departure in qualified trial matrix | 500 approaches; zero departures; failure review | 3 |
| REQ-MOT-001 | Motion commands track low-speed profile within tolerance | restrained and marked-course logs | 3 |
| PERF-PWR-001 | Mixed patrol runtime reaches target with reserve | scripted battery run | 3/5 |
| REQ-CHARGE-UX-001 | Applying power to the exterior charge port is the only user action; Sherman remains responsive and automatically hardware-inhibits motion | 100-cycle insert/remove, active-motion insertion, reset/bounce/back-power/thermal matrix | 3 |
| REQ-MAP-001 | Map represents qualified boundaries/landmarks usefully | ground-truth fixture and repeat runs | 4 |
| REQ-LOC-001 | Localization uncertainty grows honestly and triggers recovery | occlusion/slip/kidnap scenarios | 4 |
| REQ-CHG-001 | Controlled object changes are detected without destructive belief replacement | before/after fixture matrix | 4 |
| REC-STUCK-001 | Qualified stuck cases recover or ask for help safely | scenario + physical fixture suite | 4 |
| REQ-DOCK-001 | Sherman backs into the dock, proves contact, charges its installed cell, requests dock-power removal, verifies release, and drives forward off without human action | alignment/pilot/release/departure/contact-fault/charge/thermal matrix | 4 |
| REC-NET-001 | Jarvis outage does not compromise safe local operation | ≥30 min disconnect run | 3/5 |
| REC-STOR-001 | Abrupt loss never destroys last-good world/calibration state | fault-point power/process suite | 2/4 |
| REQ-PRIV-001 | Raw imagery is transient by default; capture/streaming is explicit | storage/network audit and mode tests | 2/5 |
| PERF-END-001 | 24-hour supervised endurance has no unbounded resource growth | trend report with restart/fault counts | 5 |
| EXP-NUIS-001 | Quiet hours, pause, and motion duty bounds work | accelerated schedule + lived-use review | 5 |

## Gate rule

An acceptance row cannot be marked pass from an anecdote. It needs an approved protocol version and artifacts. If a requirement changes, preserve old evidence, create a new test version, and explain the traceability change.
