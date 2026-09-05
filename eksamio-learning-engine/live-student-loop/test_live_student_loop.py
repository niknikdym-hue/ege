#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from unittest import mock
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("eksamio_live_student_loop", HERE / "runtime.py")
assert SPEC and SPEC.loader
runtime = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runtime
SPEC.loader.exec_module(runtime)


class LiveStudentLoopTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="eksamio-live-loop-")
        self.app = runtime.LiveStudentLoop(Path(self.temp.name) / "loop.sqlite", b"owner-test-key-32-bytes-minimum-0001")
        issued = self.app.host_identity.issue_anonymous()
        self.anon_token = issued.token
        self.anon_host = issued.host_identity

    def tearDown(self) -> None:
        self.app.close()
        self.temp.cleanup()

    @staticmethod
    def trainer_payload() -> dict:
        return {
            "adapter_id": "russian-ege-trainer-task12-v0.1",
            "payload": {
                "card_id": "ege-ru-12-2026-12-01",
                "session_started_at_ms": 1787238000000,
                "session_mode": "practice",
                "answer": ["1"],
                "occurred_at_client": "2026-09-02T12:00:00+03:00",
                "client_request_id": "owner-browser-attempt-001",
            },
        }

    def login(self, anonymous_token: str | None = None):
        identity, cookie = self.app.test_login(anonymous_token or self.anon_token)
        token = runtime._cookie_value(cookie, runtime.SESSION_COOKIE)
        self.assertIsNotNone(token)
        return identity, self.app.identity.resolve_session(token), token

    def practice_payload(self, answer: str, timestamp: int, request_id: str) -> dict:
        return {
            "card_id": runtime.FIRST_SLICE_CARD_ID,
            "answer": answer,
            "attempt_started_at_ms": timestamp,
            "client_request_id": request_id,
        }

    def test_complete_owner_loop_and_persistence(self) -> None:
        first = self.app.submit_trainer(self.trainer_payload(), self.anon_host)
        self.assertEqual(first["status"], "ACCEPTED")
        trainer_event = self.app.store.raw_event(first["event_receipt"]["event_id"])
        self.assertTrue(all(row["mapping_resolution"] == "COMPOSITE" for row in trainer_event["semantic_targets"]))
        self.assertEqual(first["directive"]["action_type"], "DIAGNOSE_TARGET")

        duplicate = self.app.submit_trainer(copy.deepcopy(self.trainer_payload()), self.anon_host)
        self.assertEqual(duplicate["status"], "ALREADY_APPLIED")
        self.assertEqual(self.app.store.event_count(learner_profile_id=self.anon_host.learner_profile_id, subject_id="russian"), 1)

        conflict = self.trainer_payload()
        conflict["payload"]["answer"] = ["2", "5"]
        with self.assertRaises(runtime.IntegrityConflict):
            self.app.submit_trainer(conflict, self.anon_host)

        identity, host, session_token = self.login()
        self.assertTrue(identity["authenticated"])
        self.assertEqual(host.learner_profile_id, self.anon_host.learner_profile_id)

        wrong_payload = self.practice_payload("сочитание", 1787238100000, "practice-wrong-001")
        wrong = self.app.submit_practice(host, wrong_payload)
        self.assertEqual(wrong["status"], "ACCEPTED")
        self.assertFalse(wrong["correct"])
        wrong_retry = self.app.submit_practice(host, copy.deepcopy(wrong_payload))
        self.assertEqual(wrong_retry["status"], "ALREADY_APPLIED")

        before_help = self.app._snapshot(host.learner_profile_id)
        tutor = self.app.tutor_turn(host, "Почему мой ответ неверен?")
        self.assertEqual(tutor["answer_received"], "сочитание")
        self.assertEqual(tutor["card_id"], runtime.FIRST_SLICE_CARD_ID)
        self.assertEqual(tutor["provider_mode"], "DETERMINISTIC_STAGING_NO_AI")
        self.assertTrue(tutor["verification_required"])
        pending = self.app.pending_tutor_context(host.learner_profile_id, runtime.FIRST_SLICE_CARD_ID)
        self.assertEqual(pending["status"], "VERIFICATION_REQUIRED")
        after_help = self.app._snapshot(host.learner_profile_id)
        self.assertEqual(before_help["state"]["mastery"], after_help["state"]["mastery"])

        correct_payload = self.practice_payload("сочетание", 1787238200000, "practice-correct-001")
        correct = self.app.submit_practice(host, correct_payload)
        self.assertTrue(correct["correct"])
        self.assertTrue(correct["verification_completed"])
        self.assertEqual(self.app.pending_tutor_context(host.learner_profile_id, runtime.FIRST_SLICE_CARD_ID), None)
        correct_retry = self.app.submit_practice(host, copy.deepcopy(correct_payload))
        self.assertEqual(correct_retry["status"], "ALREADY_APPLIED")

        profile = self.app.profile(host.learner_profile_id, grade=10, route="ege")
        self.assertEqual(profile["today"], {"solved": 3, "correct": 1, "errors": 2, "review": 2})
        self.assertNotIn(runtime.EXACT_SEMANTIC_ID, json.dumps(profile, ensure_ascii=False))
        history = self.app.history(host.learner_profile_id)
        self.assertEqual([row["next"] for row in history], [
            "Вернуться к навыку позже",
            "Пройти независимую проверку",
            "Разобрать ошибку",
            "Уточнить слабое место",
        ])
        diagnostics = self.app.diagnostics(host.learner_profile_id)
        self.assertEqual(diagnostics["steps"][-1]["status"], "PASS")
        rendered = json.dumps(diagnostics, ensure_ascii=False)
        self.assertNotIn("owner-test@learner.invalid", rendered)
        self.assertNotIn("сочитание", rendered)

        self.app.logout(session_token)
        _, relogged_host, _ = self.login()
        self.assertEqual(relogged_host.learner_profile_id, host.learner_profile_id)
        self.assertEqual(len(self.app.history(relogged_host.learner_profile_id)), 4)

        second_issued = self.app.host_identity.issue_anonymous()
        second_identity, second_host, _ = self.login(second_issued.token)
        self.assertEqual(second_identity["anonymous_link_status"], "EMPTY_ANONYMOUS_PROFILE_NOT_MERGED")
        self.assertEqual(second_host.learner_profile_id, host.learner_profile_id)
        self.assertEqual(len(self.app.history(second_host.learner_profile_id)), 4)

    def test_browser_truth_is_rejected_and_owner_mode_is_bounded(self) -> None:
        malicious = self.trainer_payload()
        malicious["payload"]["mastery"] = {"band": "STRONG"}
        with self.assertRaises(runtime.ServiceRequestError):
            self.app.submit_trainer(malicious, self.anon_host)
        self.assertEqual(self.app.store.event_count(), 0)
        with self.assertRaises(ValueError):
            runtime.LiveLoopServer(("0.0.0.0", 0), self.app)

    def test_tutor_rehelp_creates_fresh_lineage(self) -> None:
        _, host, _ = self.login()
        self.app.submit_practice(host, self.practice_payload("сочитание", 1, "wrong"))
        first = self.app.tutor_turn(host, "help")
        verified = self.app.submit_practice(host, self.practice_payload("сочетание", 2, "right"))
        self.assertTrue(verified["verification_completed"])
        second = self.app.tutor_turn(host, "help again")
        self.assertNotEqual(first["context_id"], second["context_id"])
        self.assertEqual(second["context_id"], self.app.tutor_turn(host, "duplicate")["context_id"])

    def test_today_uses_moscow_server_day(self) -> None:
        _, host, _ = self.login()
        self.app.submit_practice(host, self.practice_payload("сочитание", 1, "moscow"))
        events = self.app.store.list_events(host.learner_profile_id, "russian")
        events[-1]["timestamps"]["received_at_server"] = "2026-09-05T21:30:00+00:00"
        fixed = datetime(2026, 9, 6, 1, 0, tzinfo=runtime.REPORTING_TIMEZONE)
        with mock.patch.object(self.app.store, "list_events", return_value=events), mock.patch.object(runtime, "datetime", wraps=datetime) as dt:
            dt.now.return_value = fixed
            profile = self.app.profile(host.learner_profile_id, grade=10, route="ege")
        self.assertEqual(profile["today"]["solved"], 1)
        self.assertEqual(profile["reporting_timezone"], "Europe/Moscow")


if __name__ == "__main__":
    unittest.main(verbosity=2)
