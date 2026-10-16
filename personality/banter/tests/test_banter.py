import json
import random
import tempfile
import unittest
from array import array
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

from banter.audio import SAMPLE_RATE, synthesize
from banter.client import validate_exchange, validate_script
from banter.config import Config, load_config
from banter.runtime import Interaction, Scheduler, face_is_idle, write_json

ROOT = Path(__file__).resolve().parents[3]
CONTENT = json.loads((ROOT / "proto/fixtures/banter-script-v1.json").read_text())
SCRIPT = dict(
    CONTENT,
    script_id="a" * 32,
    source_device_id="robot-example",
    response_device_id="my-speaker",
    expires_in_seconds=180,
)


class BanterTests(unittest.TestCase):
    def test_seeded_schedule_has_hour_mean_minimum_and_no_catchup(self):
        now = [0.0]
        cfg = Config()
        scheduler = Scheduler(cfg, clock=lambda: now[0], rng=random.Random(531))
        gaps = []
        for _ in range(100000):
            gaps.append(scheduler.next_at - now[0])
            now[0] = scheduler.next_at
            self.assertTrue(scheduler.due())
            self.assertFalse(scheduler.due())
        self.assertGreaterEqual(min(gaps), 900)
        self.assertAlmostEqual(sum(gaps) / len(gaps), 3600, delta=40)
        self.assertGreater(len(set(round(gap) for gap in gaps)), 1000)
        now[0] += 86400 * 7
        self.assertTrue(scheduler.due())
        self.assertFalse(scheduler.due())
        self.assertGreaterEqual(scheduler.next_at - now[0], 900)

    def test_procedural_audio_is_bounded_and_meaning_emotion_sensitive(self):
        a = synthesize("Test meaning.", "curious", "seed")
        self.assertEqual(a, synthesize("Test meaning.", "curious", "seed"))
        self.assertNotEqual(a, synthesize("Other meaning.", "curious", "seed"))
        self.assertNotEqual(a, synthesize("Test meaning.", "indignant", "seed"))
        for emotion in (
            "curious",
            "pleased",
            "skeptical",
            "indignant",
            "conspiratorial",
        ):
            pcm = synthesize("A " * 90, emotion, "x", 0.50)
            self.assertLess(len(pcm), SAMPLE_RATE * 2 * 7)
            values = array("h", pcm)
            self.assertLessEqual(max(abs(v) for v in values), round(32767 * 0.50))
            self.assertEqual(values[0], 0)
            self.assertEqual(values[-1], 0)

    def test_contract_fixture_and_invalid_output(self):
        expected = dict(SCRIPT, initiator="sherman")
        self.assertEqual(validate_script(SCRIPT, "robot-example", "my-speaker"), expected)
        mutations = [
            dict(SCRIPT, schema_version=True),
            dict(SCRIPT, exchanges=[]),
            dict(SCRIPT, exchanges=CONTENT["exchanges"] * 2),
            dict(SCRIPT, response_device_id="wrong"),
            dict(SCRIPT, expires_in_seconds=10000),
            dict(SCRIPT, script_id="../x"),
            dict(SCRIPT, initiator="owner"),
        ]
        for raw in mutations:
            with self.assertRaises(ValueError):
                validate_script(raw, "robot-example", "my-speaker")
        with self.assertRaises(ValueError):
            validate_exchange(dict(CONTENT["exchanges"][0], jarvis="\nBad text"))

    def test_idle_gate_fails_closed_for_quiet_pause_tasks_and_stale_health(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "health.json"
            self.assertFalse(face_is_idle(str(path)))
            good = {
                "state": "running",
                "mode": "personality",
                "personality_degraded": False,
                "micro_behavior": "settled",
                "reason_flags": 0,
                "sleep_state": "awake",
            }
            for flags in (0, 128):
                write_json(path, dict(good, reason_flags=flags))
                self.assertTrue(face_is_idle(str(path)))
            for flags in (1, 2, 4, 8, 16, 32, 64, 256, 512, 1024, True):
                write_json(path, dict(good, reason_flags=flags))
                self.assertFalse(face_is_idle(str(path)))
            for sleep_state in (
                None,
                "falling_asleep",
                "sleeping",
                "waking_up",
                "unknown",
            ):
                write_json(path, dict(good, sleep_state=sleep_state))
                self.assertFalse(face_is_idle(str(path)))
            write_json(path, good)
            self.assertFalse(face_is_idle(str(path), lambda: path.stat().st_mtime + 16))
            write_json(path, dict(good, personality_degraded=True))
            self.assertFalse(face_is_idle(str(path)))

    def test_sleep_health_interrupts_active_exchange_and_denies_legacy_health(self):
        with tempfile.TemporaryDirectory() as folder:
            health = Path(folder) / "health.json"
            cfg = replace(Config(), history_file=folder + "/history.json")
            sleeping = json.loads(
                (
                    Path(__file__).resolve().parents[3]
                    / "proto/fixtures/sleep-health-v1.json"
                ).read_text()
            )
            awake = dict(
                sleeping, micro_behavior="settled", reason_flags=0, sleep_state="awake"
            )
            legacy = dict(awake)
            del legacy["sleep_state"]
            write_json(health, legacy)
            self.assertFalse(face_is_idle(str(health)))
            write_json(health, awake)
            client = Mock()
            client.create.return_value = SCRIPT
            speaker = Mock()

            def play(_exchange, _seed, permitted):
                self.assertTrue(permitted())
                write_json(health, dict(sleeping, sleep_state="falling_asleep"))
                self.assertFalse(permitted())
                raise RuntimeError("sleep interrupted playback")

            speaker.play.side_effect = play
            interaction = Interaction(
                cfg,
                client,
                speaker,
                lambda: face_is_idle(str(health)),
                pause=lambda _: None,
            )
            self.assertFalse(interaction.run_once())
            client.reply.assert_not_called()
            self.assertEqual(interaction.recent, [])

    def test_sequential_playback_skips_failures_and_remembers_only_performed_lines(
        self,
    ):
        with tempfile.TemporaryDirectory() as folder:
            cfg = replace(Config(), history_file=folder + "/history.json")
            calls = []
            client = Mock()
            client.create.return_value = SCRIPT
            client.reply.side_effect = lambda sid, index: calls.append(
                ("jarvis", index)
            )
            speaker = Mock()
            speaker.play.side_effect = lambda line, seed, allowed: calls.append(
                ("robot-example", seed[-1])
            )
            runtime = Interaction(
                cfg, client, speaker, lambda: True, pause=lambda _: None
            )
            self.assertTrue(runtime.run_once())
            self.assertEqual(
                calls,
                [("robot-example", "0"), ("jarvis", 0), ("robot-example", "1"), ("jarvis", 1)],
            )
            self.assertEqual(
                json.loads(Path(cfg.history_file).read_text()), CONTENT["exchanges"]
            )
            calls.clear()
            client.reply.side_effect = RuntimeError("offline")
            self.assertFalse(runtime.run_once())
            self.assertEqual(calls, [("robot-example", "0")])
            self.assertEqual(len(runtime.recent), 2)
            calls.clear()
            runtime.allowed = lambda: False
            self.assertFalse(runtime.run_once())
            self.assertEqual(calls, [])

    def test_jarvis_initiator_plays_jarvis_before_sherman_beeps(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg = replace(Config(), history_file=folder + "/history.json")
            calls = []
            client = Mock()
            client.create.return_value = dict(SCRIPT, initiator="jarvis")
            client.reply.side_effect = lambda sid, index: calls.append(
                ("jarvis", index)
            )
            speaker = Mock()
            speaker.play.side_effect = lambda line, seed, allowed: calls.append(
                ("robot-example", seed[-1])
            )
            runtime = Interaction(
                cfg, client, speaker, lambda: True, pause=lambda _: None
            )
            self.assertTrue(runtime.run_once())
            self.assertEqual(
                calls,
                [("jarvis", 0), ("robot-example", "0"), ("jarvis", 1), ("robot-example", "1")],
            )

    def test_no_reply_after_local_audio_failure_or_expired_generation(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg = replace(Config(), history_file=folder + "/history.json")
            now = [0]
            client, speaker = Mock(), Mock()
            client.create.return_value = SCRIPT
            speaker.play.side_effect = RuntimeError("ALSA unavailable")
            runtime = Interaction(
                cfg,
                client,
                speaker,
                lambda: True,
                clock=lambda: now[0],
                pause=lambda _: None,
            )
            self.assertFalse(runtime.run_once())
            client.reply.assert_not_called()

            def expired(_):
                now[0] += 181
                return SCRIPT

            client.create.side_effect = expired
            speaker.reset_mock()
            self.assertFalse(runtime.run_once())
            speaker.play.assert_not_called()
            client.reply.assert_not_called()

    def test_config_speaker_is_data_and_invalid_bounds_rejected(self):
        path = ROOT / "firmware/linux/luckfox-ultra-w/config/banter.json"
        cfg = load_config(path)
        self.assertEqual(cfg.response_device_id, "voice-example")
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "config.json"
            raw = json.loads(path.read_text())
            raw["response_device_id"] = "different-speaker"
            write_json(target, raw)
            self.assertEqual(
                load_config(target).response_device_id, "different-speaker"
            )
            for field, value in (
                ("volume", 1),
                ("mean_interval_s", 300),
                ("enabled", 1),
                ("api_url", "http://u:p@host"),
            ):
                write_json(target, {**raw, field: value})
                with self.assertRaises(ValueError):
                    load_config(target)
            write_json(target, {**raw, "volume": 0.50})
            self.assertEqual(load_config(target).volume, 0.50)
        self.assertEqual(cfg.volume, 0.50)


if __name__ == "__main__":
    unittest.main()
