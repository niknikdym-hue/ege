#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parents[1]
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

import select_russian_exceptions_session as base
import select_russian_exceptions_session_current as current

NOW = datetime(2026, 8, 11, 19, 0, 0, tzinfo=timezone.utc)


def exception(exception_id: str, skill: str, priority: str = "P2") -> dict:
    return {
        "exception_id": exception_id,
        "skill_ids": [skill],
        "launch_priority": priority,
        "status": "source_verified",
    }


def practice(
    pid: str,
    exception_id: str,
    transfer_level: str,
    context: str,
    mode: str = "context_choice",
) -> dict:
    return {
        "practice_item_id": pid,
        "exception_id": exception_id,
        "mode": mode,
        "transfer_level": transfer_level,
        "context_signature": context,
        "status": "source_verified",
    }


class SessionSelectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.exceptions = {
            "ex_a": exception("ex_a", "orthographic_norms", "P0"),
            "ex_b": exception("ex_b", "punctuation_norms", "P1"),
            "ex_c": exception("ex_c", "morphological_norms", "P2"),
            "ex_d": exception("ex_d", "lexical_norms_and_semantics", "P2"),
        }
        self.by_exception = {
            "ex_a": [
                practice("a_rec", "ex_a", "recognition", "a_rec_ctx", "recognize_exception"),
                practice("a_recall", "ex_a", "guided_recall", "a_recall_ctx", "recall_form"),
                practice("a_transfer", "ex_a", "transfer", "a_transfer_ctx"),
            ],
            "ex_b": [practice("b_ctx", "ex_b", "independent_context", "b_ctx")],
            "ex_c": [practice("c_ctx", "ex_c", "independent_context", "c_ctx")],
            "ex_d": [practice("d_ctx", "ex_d", "independent_context", "d_ctx")],
        }

    def select(self, *, states=None, count=10, source="all_exceptions", handoff=None):
        return current.select_session_current(
            self.exceptions,
            self.by_exception,
            states or {},
            count=count,
            now=NOW,
            source=source,
            handoff=set(handoff or []),
        )

    def test_empty_learner_is_deterministic_and_unique(self):
        first = self.select(count=4)
        second = self.select(count=4)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 4)
        self.assertEqual(len({x["practice_item_id"] for x in first}), 4)
        self.assertEqual(len({x["context_signature"] for x in first}), 4)
        self.assertEqual(first[0]["exception_id"], "ex_a")

    def test_due_item_precedes_new_item(self):
        states = {
            "ex_c": {
                "status": "due",
                "seen_count": 2,
                "next_due_at": "2026-08-10T10:00:00+00:00",
                "retention_passed": False,
            }
        }
        rows = self.select(states=states, count=2)
        self.assertEqual(rows[0]["exception_id"], "ex_c")
        self.assertEqual(rows[0]["reason_code"], "due_review")

    def test_recognition_success_prefers_recall_next(self):
        states = {
            "ex_a": {
                "status": "active",
                "seen_count": 1,
                "last_result": "correct",
                "last_transfer_level": "recognition",
                "transfer_passed": False,
                "active_error_count": 0,
            }
        }
        rows = self.select(states=states, count=1, source="handoff", handoff=["ex_a"])
        self.assertEqual(rows[0]["practice_item_id"], "a_recall")

    def test_broad_empty_handoff_fails_closed(self):
        rows = self.select(count=5, source="handoff", handoff=[])
        self.assertEqual(rows, [])

    def test_single_exception_handoff_can_use_multiple_distinct_contexts(self):
        rows = self.select(count=3, source="work_on_errors", handoff=["ex_a"])
        self.assertEqual(len(rows), 3)
        self.assertEqual({x["exception_id"] for x in rows}, {"ex_a"})
        self.assertEqual(len({x["practice_item_id"] for x in rows}), 3)
        self.assertEqual(len({x["context_signature"] for x in rows}), 3)
        self.assertTrue(any(x["soft_constraints_relaxed"]["exception_gap"] for x in rows[1:]))

    def test_my_exceptions_excludes_unseen(self):
        states = {
            "ex_b": {
                "status": "active",
                "seen_count": 1,
                "active_error_count": 1,
                "last_result": "wrong",
            }
        }
        rows = self.select(states=states, count=5, source="my_exceptions")
        self.assertEqual([x["exception_id"] for x in rows], ["ex_b"])

    def test_short_candidate_set_does_not_pad_duplicates(self):
        exceptions = {"ex_b": self.exceptions["ex_b"]}
        by_exception = {"ex_b": self.by_exception["ex_b"]}
        rows = current.select_session_current(
            exceptions,
            by_exception,
            {},
            count=10,
            now=NOW,
            source="all_exceptions",
            handoff=set(),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["practice_item_id"], "b_ctx")

    def test_recent_context_is_deprioritized_when_alternative_exists(self):
        states = {
            "ex_a": {
                "status": "active",
                "seen_count": 2,
                "last_result": "wrong",
                "active_error_count": 1,
                "recent_context_signatures": ["a_recall_ctx"],
            }
        }
        rows = self.select(states=states, count=1, source="handoff", handoff=["ex_a"])
        self.assertNotEqual(rows[0]["context_signature"], "a_recall_ctx")


if __name__ == "__main__":
    unittest.main()
