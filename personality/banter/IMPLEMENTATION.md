# Implementation

- `config.py`: strict bounded configuration, private credential-file reference.
- `client.py`: stdlib HTTP, no redirects or ambiguous request retries, bounded
  authentication/response reads, version/device/shape/content validation.
- `audio.py`: deterministic procedural PCM and interruptible `aplay`; hardware
  access is isolated behind `AlsaSpeaker.play` and faked in simulation tests.
- `runtime.py`: injected clocks/randomness, idle admission, scheduling and script
  execution. Unknown, stale, unhealthy or non-idle face state denies speech.
- `run_banter.py`: independent process, file lock, signals, diagnostics and bounded
  health record. No display-loop work or safety/motion authority is added.

Protocol content was landed first in `proto/`, with a matching Jarvis fixture.
Jarvis owns generation/expiry/reply consumption; Sherman never sends the API a
replacement spoken reply. An uncertain result abandons the remainder, without
retry or local fallback. The same owner scopes source, script and response device.

Owned packet: P1-JAR-002; runtime pin is the documented Buildroot Python 3.11.6.
No dependency installation, root environment or model runtime is needed.
