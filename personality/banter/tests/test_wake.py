from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from banter.config import Config, read_json
from banter.runtime import (
    Interaction,
    ManualTriggers,
    Scheduler,
    face_is_idle,
    write_json,
)
from banter.wake import ManualWake


class WakeTest(unittest.TestCase):
    def test_manual_poll_waits_for_matching_awake_then_releases_on_success_or_failure(
        self,
    ):
        for failure in (None, "generation", "reply", "wake_timeout", "pause"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as folder:
                config = replace(
                    Config(),
                    history_file=folder + "/history.json",
                    face_health_file=folder + "/face.json",
                    wake_request_file=folder + "/wake.json",
                )
                now = [10.0]
                night = dict(
                    state="running",
                    mode="personality",
                    personality_degraded=False,
                    micro_behavior="drowsy",
                    reason_flags=2,
                    sleep_state="sleeping",
                    wake_request_id="",
                )
                write_json(config.face_health_file, night)

                def ready():
                    return face_is_idle(
                        config.face_health_file,
                        allow_circadian_quiet=True,
                        allow_sleep=True,
                    )

                def awake():
                    return face_is_idle(
                        config.face_health_file, allow_circadian_quiet=True
                    )

                def pause(seconds):
                    now[0] += seconds
                    request = read_json(config.wake_request_file)
                    finished = now[0] >= request["issued_at_monotonic_s"] + 2.4
                    write_json(
                        config.face_health_file,
                        dict(
                            night,
                            sleep_state="awake" if finished else "waking_up",
                            wake_request_id="wrong"
                            if failure == "wake_timeout"
                            else request["request_id"],
                            reason_flags=10 if failure == "pause" else 2,
                        ),
                    )

                wake = ManualWake(
                    config, ready, awake, clock=lambda: now[0], pause=pause
                )
                client, speaker = Mock(), Mock()
                trigger_id = "d" * 32
                client.poll.return_value = trigger_id

                def generate(*args, **kwargs):
                    self.assertGreaterEqual(now[0], 12.4)
                    self.assertTrue(wake.is_awake())
                    self.assertFalse(face_is_idle(config.face_health_file))
                    if failure == "generation":
                        raise RuntimeError("generation failed")
                    return {
                        "script_id": "e" * 32,
                        "expires_in_seconds": 180,
                        "exchanges": [
                            {"robot-example": "Hi.", "emotion": "curious", "jarvis": "Hello."}
                        ],
                    }

                client.create.side_effect = generate
                if failure == "reply":
                    client.reply.side_effect = RuntimeError("reply failed")
                speaker.play.side_effect = lambda _, __, permitted: self.assertTrue(
                    permitted()
                )
                interaction = Interaction(
                    config,
                    client,
                    speaker,
                    lambda: face_is_idle(config.face_health_file),
                    clock=lambda: now[0],
                    pause=pause,
                    manual_allowed=awake,
                    manual_ready=ready,
                    wake=wake,
                )
                scheduler = Scheduler(config, clock=lambda: now[0])
                manual = ManualTriggers(
                    client, interaction, scheduler, clock=lambda: now[0]
                )
                self.assertTrue(manual.tick())
                client.poll.assert_called_once_with(ready=True, result=None)
                self.assertEqual(
                    manual.result["status"],
                    "completed" if failure is None else "failed",
                )
                self.assertFalse(Path(config.wake_request_file).exists())
                if failure in ("wake_timeout", "pause"):
                    client.create.assert_not_called()
                    speaker.play.assert_not_called()

    def test_sleep_admission_is_only_for_manual_wake_not_playback(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "face.json"
            for state in ("falling_asleep", "sleeping", "waking_up"):
                write_json(
                    path,
                    dict(
                        state="running",
                        mode="personality",
                        personality_degraded=False,
                        micro_behavior="drowsy",
                        reason_flags=2,
                        sleep_state=state,
                    ),
                )
                self.assertTrue(
                    face_is_idle(
                        str(path), allow_circadian_quiet=True, allow_sleep=True
                    )
                )
                self.assertFalse(face_is_idle(str(path), allow_circadian_quiet=True))
                self.assertFalse(face_is_idle(str(path), allow_sleep=True))
