# Implementation

- `config.py`: strict bounded configuration, private credential-file reference.
- `client.py`: stdlib HTTP, no redirects or ambiguous request retries, bounded
  authentication/response reads, version/device/shape/content validation. Manual
  polling passes a three-second timeout through authentication and forwards only
  validated trigger IDs on deliberately requested script creation.
- `audio.py`: deterministic procedural PCM and interruptible `aplay`; hardware
  access is isolated behind `AlsaSpeaker.play` and faked in simulation tests.
- `runtime.py`: injected clocks/randomness, idle admission, scheduling and script
  execution. `ManualTriggers` polls the configured pair every five seconds, retains
  idempotent outcome acknowledgments after failed polls, backs off failures with
  jitter capped at 60 seconds, and resets the autonomous timer on each consumed
  request. Automatic admission rejects circadian quiet; manual admission permits
  nighttime drowsiness, while explicit quiet, pause, tasks, low energy, unknown,
  stale and unhealthy face state deny both paths. The chosen admission predicate
  is rechecked throughout execution and by the audio adapter.
- `run_banter.py`: independent process, file lock, signals, diagnostics and bounded
  health record. No display-loop work or safety/motion authority is added.

Protocol content was landed first in `proto/`, with a matching Jarvis fixture.
Jarvis owns generation/expiry/reply consumption; Sherman never sends the API a
replacement spoken reply. An uncertain result abandons the remainder, without
retry or local fallback. The same owner scopes source, script and response device.

Owned packet: P1-JAR-002; runtime pin is the documented Buildroot Python 3.11.6.
No dependency installation, root environment or model runtime is needed.

Manual demo extension: P1-JAR-003 and ADR 0007. The API consumes one queued trigger
only for a ready poll. A manual request stays in the synchronous execution loop
under the existing process lock; there is no incoming robot server, second audio
worker or parallel autonomous interaction. P1-JAR-004 / ADR 0008 narrows the manual
gate to allow scheduled nighttime quiet without enabling spontaneous speech.
