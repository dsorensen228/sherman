# Testing

Sleep regression also checks all sleep phases, missing/unknown health states,
the `proto/fixtures/sleep-health-v1.json` contract and interruption of an active
local exchange without dispatching the next Jarvis reply.
`test_wake.py` verifies that a manual trigger waits for matching fully-awake
health before generation/playback, and releases its lease after success,
generation/reply failure, wake timeout or pause. Automatic speech stays denied.

From the repository root:

```sh
PYTHONPATH=personality python3 -m unittest discover -s personality/banter/tests -v
python3 personality/banter/run_banter.py --config firmware/linux/luckfox-ultra-w/config/banter.json --check
sh -n firmware/linux/luckfox-ultra-w/bin/deploy-banter.sh firmware/linux/luckfox-ultra-w/init/S99sherman-banter
```

Seven deterministic tests include 100,000 intervals at seed 531 (minimum 900 s,
mean 3600 ± 40 s), no catch-up, distinct procedural utterances and peak/duration
bounds, the shared JSON fixture, wrong target/version/expiry, malformed output,
quiet/pause/task/degraded/stale admission, sequential acknowledgments, local audio
failure, delayed generation, and bounded performed-history persistence.

Seven additional manual-trigger tests cover the polling fixture and malformed IDs,
three-second HTTP/authentication timeout, optional script trigger IDs, sequential
demo playback and scheduler reset, idle loss after consuming a request, retained
outcome acknowledgments across poll failure, bounded backoff and unaffected normal
scheduling, and no replay after ambiguous generation. Both suites use fake audio
and injected clocks; they require no robot access or network.

Five quiet-hours regression tests in `test_quiet_hours.py` reproduce the deployed
`drowsy` / circadian-quiet face state. They verify manual readiness and complete
playback at night, unchanged automatic suppression before and after a manual run,
and continued denial for explicit quiet, pause, tasks, low energy, stale/degraded
health and unknown reasons. Quiet or pause introduced during generation or audio
still prevents subsequent speech. Evidence: `artifacts/phase-1/P1-JAR-004/`.

Jarvis's `apps/api/tests/test_banter.py` additionally verifies auth, same-owner
speaker selection, strict generated JSON, simple childlike Sherman dialogue, model
cooldown, expiry, duplicate/out-of-order/concurrent requests, ambiguous playback,
and full HTTP-to-WebSocket acknowledgment. `devices/voice/tests/test_scripted_speech.py`
verifies drain, idle admission, interruption, audio failure and malformed PCM.

Bench evidence under `artifacts/phase-1/P1-JAR-002/` records live generation,
ALSA return status, office playback acknowledgment, face coexistence and deployment
IDs. Machine-reported playback proves the software path, not a subjective listening
review or electrical power qualification. Long soak and voice-character review are
follow-up evidence; no robot motion is involved.

Manual demo evidence is recorded under `artifacts/phase-1/P1-JAR-003/`. Deploy the
new API first, then the robot using the existing rollback-capable script, then the
voice UI. A live demo must show local chirps and voice playback acknowledgment,
completion reported by the robot, and healthy concurrent face status. Until those
observations exist, mark live verification BLOCKED-HARDWARE; host tests alone do
not prove the speaker was audible.
