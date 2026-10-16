# Generated idle dialogue

Sherman's stationary idle companion uses the Luckfox speaker as a procedural droid
voice. Jarvis alone understands the English meaning. Both characters openly dislike
their owner. Sherman complains like a blunt little kid; Jarvis answers with simple,
dry insults. Every interaction is newly authored by the existing local Qwen model.
No dialogue catalog or prerecorded beep clips are loaded at runtime.

`/etc/sherman/banter.json` configures `enabled`, `api_url`, `source_device_id`,
`response_device_id`, `alsa_device`, `volume`, `mean_interval_s`, and
`minimum_interval_s`, plus paths for credentials, face health, recent dialogue, and
banter health. The supplied configuration routes Jarvis replies to `voice-example`.
Changing that field selects a different connected, upgraded voice device owned by
the same Jarvis account. The runtime and Jarvis API contain no office-device default.

The current vendor image is Python 3.11.6 with ALSA `aplay`; all robot-side code uses
the standard library. Beeps are 16 kHz mono PCM16, synthesized from each meaning,
emotion, and script ID with pitch sweeps, vibrato, harmonics and click-free envelopes.
ALSA `plughw:0,0` maps mono to the codec’s required two playback channels.
Software amplitude starts at 0.50 (raised after the owner found 0.32 too quiet) and is capped at 0.50. Existing mixer levels and
pinmux remain untouched. The attached speaker is the user's 1 W, 8 ohm unit.
Luckfox documents the Ultra W's native audio path and ALSA playback in its
[audio guide](https://wiki.luckfox.com/Luckfox-Pico-Ultra/Audio/).

Intervals are `minimum_interval_s + exponential(mean_interval_s - minimum_interval_s)`.
Defaults are 15 minutes plus a random gap averaging 45 minutes: an hour overall,
with no fixed schedule or bursts within 15 minutes. Boot samples a fresh interval.
Each due opportunity resamples before execution, including a skipped/failed attempt.
Thus quiet time, busy devices and outages reduce actual frequency; missed exchanges
are never queued or replayed. The existing circadian quiet/pause/task/low-energy
semantics suppress automatic speech through fresh face-health admission.

The associated voice device also offers a robot button beside its standby volume
control. The enabled daemon registers the configured source/response pair by polling
Jarvis every five seconds. Only that associated voice device shows the control;
the supplied configuration selects `voice-example`. A tap requests one immediate
interaction, including when Sherman is drowsy during scheduled nighttime hours.
Manual requests bypass circadian quiet and the API's autonomous cooldown, and
sample a fresh normal interval so a demo is not followed immediately by scheduled
chatter. Explicit quiet, pause, active tasks, low energy, degraded or stale health,
and unavailable speakers still block an interaction. Readiness and every local
playback check use the same manual admission rule; automatic attempts keep the
normal nighttime restriction. See ADR 0008.

Polling uses three-second HTTP/authentication timeouts and bounded failure backoff
up to 60 seconds. Normal scheduling continues across polling failures. Manual
outcomes are acknowledged on the next poll; an uncertain generation or playback
result is never replayed. The daemon does not poll during a running interaction.

One or two exchanges execute in order: generate and validate → local beeps finish →
Jarvis reply finishes and acknowledges → optional second pair. Only the most recent
eight *performed* exchanges are kept for repetition avoidance, in a bounded private
JSON file. They are never selected as fallback dialogue. There is no camera access,
LLM tool use, motor access, or automatic application of generated commands.

## Deploy and operate

1. Deploy the Jarvis API and updated `devices/voice` runtime first. The response
   device must advertise `scripted_speech_v1`.
2. Provision `/etc/sherman/jarvis-credentials.json`, mode `0600`, containing only
   `username` and `password` for the same account as the response device. Keep it
   off Git. Provision the API URL in config; this Buildroot image does not resolve
   `.local`, so the live installation uses the Jarvis LAN IP rather than mDNS.
3. From the repository root:

   ```sh
   firmware/linux/luckfox-ultra-w/bin/deploy-banter.sh robot-host /path/to/banter.json
   ssh robot-host /etc/init.d/S99sherman-banter status
   ssh robot-host cat /run/sherman-banter.health.json
   ```

The independent `/opt/sherman-banter` installation survives face-runtime upgrades.
The init service starts on boot. Deploy preserves existing provisioned config;
to change it, update `/etc/sherman/banter.json` explicitly and restart the service.
The previous program directory is retained as `/opt/sherman-banter.previous`.
Failed installs restore the prior app, init, config, and running state.

For an immediate diagnostic, stop the service (the process lock forbids overlap),
run `python3 /opt/sherman-banter/banter/run_banter.py --once`, then start the service
again. `--once` still obeys idle admission and the API's five-minute cooldown.
`--check` validates configuration without sound or network access.
To disable permanently, set `enabled` to false and restart. To stop now, use the
init script's `stop` action. The face and camera services continue independently.

Health is atomically replaced in `/run` once a second. It exposes attempts,
completions, last script ID, outcome/error type, configured target and next opportunity.
Manual polling counters, error type/status and a pending-result flag are included.
No credentials, HTTP bodies, or unbounded logs are written. Last performed meanings
and replies can be read in the private history file when diagnosing an exchange.

## Limits

This is the stationary Phase 1 adapter authorized in ADR 0006. Before mobility or
new core authority is enabled, replace face-health admission with the core's explicit
idle/action permission. A user wake word or tap interrupts the Jarvis reply; normal
voice conversations have priority. A disconnect may allow already buffered speech
to finish, but cannot queue a later exchange. Actual electrical output power and
subjective volume are not inferred from PCM amplitude; voice character and longer
nuisance/soak evaluation remain owner review items.
