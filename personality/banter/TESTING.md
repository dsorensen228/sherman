# Testing

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

Jarvis's `apps/api/tests/test_banter.py` additionally verifies auth, same-owner
speaker selection, strict generated JSON, inherited level-3 personality, model
cooldown, expiry, duplicate/out-of-order/concurrent requests, ambiguous playback,
and full HTTP-to-WebSocket acknowledgment. `devices/voice/tests/test_scripted_speech.py`
verifies drain, idle admission, interruption, audio failure and malformed PCM.

Bench evidence under `artifacts/phase-1/P1-JAR-002/` records live generation,
ALSA return status, office playback acknowledgment, face coexistence and deployment
IDs. Machine-reported playback proves the software path, not a subjective listening
review or electrical power qualification. Long soak and voice-character review are
follow-up evidence; no robot motion is involved.
