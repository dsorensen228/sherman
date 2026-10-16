import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

from banter.config import Config
from banter.runtime import (
    Interaction,
    ManualTriggers,
    Scheduler,
    face_is_idle,
    write_json,
)

TRIGGER_ID = "d" * 32
NIGHT = {
    "state": "running",
    "mode": "personality",
    "personality_degraded": False,
    "micro_behavior": "drowsy",
    "reason_flags": 1 << 1,
    "sleep_state": "awake",  # Acknowledged temporary manual wake.
}
SCRIPT = {
    "script_id": "e" * 32,
    "expires_in_seconds": 180,
    "exchanges": [
        {"robot-example": "I'm bored.", "emotion": "curious", "jarvis": "Yes, me too."}
    ],
}


class QuietHoursTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "face.json"
        write_json(self.path, NIGHT)

    def automatic_allowed(self):
        return face_is_idle(str(self.path))

    def manual_allowed(self):
        return face_is_idle(str(self.path), allow_circadian_quiet=True)

    def interaction(self):
        cfg = replace(Config(), history_file=self.folder.name + "/history.json")
        client, speaker = Mock(), Mock()
        client.create.return_value = SCRIPT
        client.poll.return_value = TRIGGER_ID
        runtime = Interaction(
            cfg,
            client,
            speaker,
            self.automatic_allowed,
            pause=lambda _: None,
            manual_allowed=self.manual_allowed,
        )
        return runtime, client, speaker, Scheduler(cfg)

    def test_circadian_quiet_allows_only_manual_requests(self):
        for behavior in ("settled", "orienting", "observing", "drowsy"):
            for flags in (2, 2 | 128):
                with self.subTest(behavior=behavior, flags=flags):
                    write_json(
                        self.path,
                        dict(NIGHT, micro_behavior=behavior, reason_flags=flags),
                    )
                    self.assertTrue(self.manual_allowed())
                    self.assertFalse(self.automatic_allowed())
        for flags in (0, 128):
            write_json(self.path, dict(NIGHT, reason_flags=flags))
            self.assertFalse(self.manual_allowed(), "unexplained drowsiness")
            write_json(
                self.path, dict(NIGHT, micro_behavior="settled", reason_flags=flags)
            )
            self.assertTrue(self.manual_allowed())
            self.assertTrue(self.automatic_allowed())

    def test_manual_still_denies_explicit_quiet_pause_tasks_and_bad_health(self):
        for flags in (1, 4, 8, 16, 32, 64, 256, 512, 1024, 2048):
            for reasons in (flags, flags | 2, flags | 2 | 128):
                with self.subTest(reasons=reasons):
                    write_json(self.path, dict(NIGHT, reason_flags=reasons))
                    self.assertFalse(self.manual_allowed())
        for changes in (
            {"reason_flags": True},
            {"reason_flags": "2"},
            {"reason_flags": -1},
            {"reason_flags": None},
            {"personality_degraded": True},
            {"personality_degraded": None},
            {"mode": "diagnostic"},
            {"state": "stopped"},
            {"micro_behavior": "engaged"},
            {"micro_behavior": "reflecting"},
            {"micro_behavior": "unknown"},
        ):
            with self.subTest(changes=changes):
                write_json(self.path, dict(NIGHT, **changes))
                self.assertFalse(self.manual_allowed())
        write_json(self.path, NIGHT)
        for age in (-1, 16):
            self.assertFalse(
                face_is_idle(
                    str(self.path),
                    lambda: self.path.stat().st_mtime + age,
                    allow_circadian_quiet=True,
                )
            )
        self.path.write_text("invalid json")
        self.assertFalse(self.manual_allowed())
        self.path.unlink()
        self.assertFalse(self.manual_allowed())

    def test_nighttime_poll_and_playback_use_manual_admission(self):
        runtime, client, speaker, scheduler = self.interaction()
        self.assertFalse(runtime.run_once())
        client.create.assert_not_called()
        speaker.play.assert_not_called()

        # The audio adapter continuously calls the same permission predicate.
        speaker.play.side_effect = lambda line, seed, allowed: self.assertTrue(
            allowed()
        )
        manual = ManualTriggers(client, runtime, scheduler)
        scheduler.next_at = 0
        self.assertTrue(manual.tick())
        client.poll.assert_called_once_with(ready=True, result=None)
        client.create.assert_called_once_with([], trigger_id=TRIGGER_ID)
        speaker.play.assert_called_once()
        client.reply.assert_called_once_with(SCRIPT["script_id"], 0)
        self.assertEqual(manual.result["status"], "completed")
        self.assertFalse(scheduler.due())
        self.assertEqual(runtime.completed, 1)

        # Manual admission must not leak into later scheduled attempts.
        self.assertFalse(runtime.run_once())
        self.assertEqual(client.create.call_count, 1)

    def test_explicit_quiet_during_manual_generation_prevents_audio(self):
        runtime, client, speaker, _ = self.interaction()

        def generate(*args, **kwargs):
            write_json(self.path, dict(NIGHT, reason_flags=2 | 4))
            return SCRIPT

        client.create.side_effect = generate
        self.assertFalse(runtime.run_once(trigger_id=TRIGGER_ID))
        speaker.play.assert_not_called()
        client.reply.assert_not_called()

    def test_pause_during_manual_beeps_cancels_remaining_reply(self):
        runtime, client, speaker, _ = self.interaction()

        def play(line, seed, allowed):
            self.assertTrue(allowed())
            write_json(self.path, dict(NIGHT, reason_flags=2 | 8))
            self.assertFalse(allowed())

        speaker.play.side_effect = play
        self.assertFalse(runtime.run_once(trigger_id=TRIGGER_ID))
        client.reply.assert_not_called()
        self.assertEqual(runtime.completed, 0)


if __name__ == "__main__":
    unittest.main()
