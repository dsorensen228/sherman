import json
import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, Mock

from banter.client import JarvisClient, validate_trigger
from banter.config import Config
from banter.runtime import Interaction, ManualTriggers, Scheduler

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = json.loads((ROOT / "proto/fixtures/banter-poll-v1.json").read_text())
TRIGGER_ID = FIXTURE["response"]["trigger_id"]
CONTENT = json.loads((ROOT / "proto/fixtures/banter-script-v1.json").read_text())
SCRIPT = dict(
    CONTENT,
    script_id="c" * 32,
    source_device_id="robot-example",
    response_device_id="voice-example",
    expires_in_seconds=180,
)


def response(value):
    context = MagicMock()
    context.__enter__.return_value.read.return_value = json.dumps(value).encode()
    return context


class ManualTriggerTests(unittest.TestCase):
    def test_fixture_validation_rejects_missing_malformed_and_nonstring_ids(self):
        self.assertEqual(validate_trigger(FIXTURE["response"]), TRIGGER_ID)
        self.assertIsNone(validate_trigger(FIXTURE["empty_response"]))
        # Additive server fields remain compatible.
        self.assertEqual(
            validate_trigger({**FIXTURE["response"], "future": True}), TRIGGER_ID
        )
        for raw in (
            None,
            [],
            {},
            {"trigger_id": True},
            {"trigger_id": "../x"},
            {"trigger_id": "A" * 32},
            {"trigger_id": "a" * 33},
        ):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                validate_trigger(raw)

    def test_poll_uses_config_pair_and_short_timeout_for_auth_and_poll(self):
        with tempfile.TemporaryDirectory() as folder:
            credentials = Path(folder) / "credentials.json"
            credentials.write_text(json.dumps({"username": "test", "password": "test"}))
            credentials.chmod(0o600)
            cfg = replace(
                Config(),
                api_url="http://jarvis.test",
                response_device_id="voice-example",
                credentials_file=str(credentials),
            )
            client = JarvisClient(cfg)
            client.opener = Mock()
            client.opener.open.side_effect = [
                response({"access_token": "test-token", "expires_in": 3600}),
                response(FIXTURE["response"]),
            ]
            self.assertEqual(
                client.poll(ready=True, result=FIXTURE["request"]["result"]), TRIGGER_ID
            )
            auth_call, poll_call = client.opener.open.call_args_list
            self.assertEqual(auth_call.kwargs, {"timeout": 3})
            self.assertEqual(poll_call.kwargs, {"timeout": 3})
            request = poll_call.args[0]
            self.assertEqual(request.full_url, "http://jarvis.test/v1/banter/poll")
            self.assertEqual(json.loads(request.data), FIXTURE["request"])
            self.assertEqual(request.get_header("Authorization"), "Bearer test-token")

    def test_create_supplies_manual_id_only_for_explicit_request(self):
        client = JarvisClient(replace(Config(), response_device_id="voice-example"))
        client._authenticate = Mock()
        client._post = Mock(return_value=SCRIPT)
        client.create([], trigger_id=TRIGGER_ID)
        self.assertEqual(client._post.call_args.args[1]["trigger_id"], TRIGGER_ID)
        client.create([])
        self.assertNotIn("trigger_id", client._post.call_args.args[1])
        with self.assertRaises(ValueError):
            client.create([], trigger_id="bad-id")
        self.assertEqual(client._post.call_count, 2)

    def test_manual_runs_before_due_schedule_with_order_and_reports_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            now = [0.0]

            def clock():
                return now[0]

            cfg = replace(Config(), history_file=folder + "/history.json")
            client, speaker = Mock(), Mock()
            client.poll.side_effect = [TRIGGER_ID, None]
            client.create.return_value = SCRIPT
            calls = []
            speaker.play.side_effect = lambda line, seed, allowed: calls.append("beeps")
            client.reply.side_effect = lambda sid, index: calls.append("reply")
            runtime = Interaction(
                cfg, client, speaker, lambda: True, clock, lambda _: None
            )
            scheduler = Scheduler(cfg, clock, random.Random(531))
            scheduler.next_at = now[0]
            manual = ManualTriggers(client, runtime, scheduler, clock)
            self.assertTrue(manual.tick())
            self.assertEqual(calls, ["beeps", "reply", "beeps", "reply"])
            client.create.assert_called_once_with([], trigger_id=TRIGGER_ID)
            self.assertFalse(scheduler.due())
            self.assertEqual(runtime.completed, 1)
            self.assertTrue(manual.health()["manual_result_pending"])
            self.assertFalse(manual.tick())
            self.assertEqual(client.poll.call_count, 1)
            now[0] = manual.next_at
            self.assertFalse(manual.tick())
            client.poll.assert_called_with(
                ready=True, result={"trigger_id": TRIGGER_ID, "status": "completed"}
            )
            self.assertIsNone(manual.result)
            self.assertEqual(client.create.call_count, 1)

    def test_local_idle_loss_reports_failure_and_does_not_retry_consumed_trigger(self):
        with tempfile.TemporaryDirectory() as folder:
            now = [0.0]

            def clock():
                return now[0]

            cfg = replace(Config(), history_file=folder + "/history.json")
            client, speaker = Mock(), Mock()
            client.poll.side_effect = [TRIGGER_ID, TimeoutError(), None]
            allowed = Mock(side_effect=[True, False, False, True])
            runtime = Interaction(cfg, client, speaker, allowed, clock)
            scheduler = Scheduler(cfg, clock, random.Random(531))
            manual = ManualTriggers(
                client, runtime, scheduler, clock, random.Random(531)
            )
            self.assertTrue(manual.tick())
            self.assertEqual(runtime.last_status, "skipped_not_idle")
            self.assertEqual(
                manual.result, {"trigger_id": TRIGGER_ID, "status": "failed"}
            )
            client.create.assert_not_called()
            speaker.play.assert_not_called()
            for _ in range(2):
                now[0] = manual.next_at
                self.assertFalse(manual.tick())
            self.assertEqual(
                client.poll.call_args_list[1].kwargs["result"],
                client.poll.call_args_list[2].kwargs["result"],
            )
            self.assertIsNone(manual.result)
            self.assertEqual(runtime.attempts, 0)

    def test_poll_failure_backoff_is_bounded_and_leaves_normal_schedule_due(self):
        now = [0.0]

        def clock():
            return now[0]

        client, runtime = Mock(), Mock()
        client.poll.side_effect = TimeoutError()
        scheduler = Scheduler(Config(), clock, random.Random(531))
        scheduler.next_at = 0.0
        manual = ManualTriggers(client, runtime, scheduler, clock, random.Random(531))
        for index in range(20):
            self.assertFalse(manual.tick())
            self.assertGreaterEqual(manual.next_at - now[0], 4)
            self.assertLessEqual(manual.next_at - now[0], 60 + 1e-9)
            self.assertEqual(client.poll.call_count, index + 1)
            self.assertFalse(manual.tick())
            self.assertEqual(client.poll.call_count, index + 1)
            now[0] = manual.next_at
        self.assertTrue(scheduler.due())
        self.assertEqual(manual.failures, 5)
        self.assertEqual(manual.health()["manual_poll_error_type"], "TimeoutError")
        runtime.run_once.assert_not_called()
        client.poll.side_effect = None
        client.poll.return_value = None
        self.assertFalse(manual.tick())
        self.assertEqual(manual.failures, 0)
        self.assertEqual(manual.next_at - now[0], 5)

    def test_ambiguous_creation_reports_failure_without_audio_or_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            now = [0.0]

            def clock():
                return now[0]

            cfg = replace(Config(), history_file=folder + "/history.json")
            client, speaker = Mock(), Mock()
            client.poll.side_effect = [TRIGGER_ID, None]
            client.create.side_effect = TimeoutError()
            runtime = Interaction(cfg, client, speaker, lambda: True, clock)
            scheduler = Scheduler(cfg, clock, random.Random(531))
            manual = ManualTriggers(client, runtime, scheduler, clock)
            self.assertTrue(manual.tick())
            self.assertEqual(manual.result["status"], "failed")
            now[0] = manual.next_at
            self.assertFalse(manual.tick())
            client.create.assert_called_once_with([], trigger_id=TRIGGER_ID)
            speaker.play.assert_not_called()
            client.reply.assert_not_called()


if __name__ == "__main__":
    unittest.main()
