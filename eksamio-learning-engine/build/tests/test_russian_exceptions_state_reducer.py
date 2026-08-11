#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parents[1]
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

import reduce_russian_exceptions_learner_state as reducer


def event(
    event_id: str,
    *,
    correct: bool,
    transfer_level: str = "recognition",
    source: str = "exceptions_all",
    context: str = "ctx1",
) -> dict:
    return {
        "event_id": event_id,
        "practice_item_id": f"practice-{event_id}",
        "exception_id": "ex_a",
        "mode": "context_choice",
        "started_at": "2026-08-11T18:59:50+00:00",
        "answered_at": "2026-08-11T19:00:00+00:00",
        "is_correct": correct,
        "response": "x",
        "source": source,
        "transfer_level": transfer_level,
        "context_signature": context,
    }


class StateReducerTests(unittest.TestCase):
    def test_wrong_creates_active_error_state(self):
        profile, applied = reducer.apply_event(None, event("e1", correct=False))
        self.assertTrue(applied)
        state = profile["exceptions"]["ex_a"]
        self.assertEqual(state["seen_count"], 1)
        self.assertEqual(state["wrong_count"], 1)
        self.assertEqual(state["correct_count"], 0)
        self.assertEqual(state["active_error_count"], 1)
        self.assertEqual(state["status"], "active")
        self.assertEqual(state["retention_stage"], "learning")

    def test_replayed_event_is_idempotent(self):
        first, applied1 = reducer.apply_event(None, event("e1", correct=False))
        second, applied2 = reducer.apply_event(first, event("e1", correct=False))
        self.assertTrue(applied1)
        self.assertFalse(applied2)
        self.assertEqual(first, second)
        self.assertEqual(second["exceptions"]["ex_a"]["wrong_count"], 1)
        self.assertEqual(second["state_revision"], 1)

    def test_correct_recognition_does_not_mark_stabilized_or_transfer(self):
        profile, _ = reducer.apply_event(None, event("e1", correct=True, transfer_level="recognition"))
        state = profile["exceptions"]["ex_a"]
        self.assertEqual(state["status"], "active")
        self.assertFalse(state["transfer_passed"])
        self.assertFalse(state["retention_passed"])
        self.assertEqual(state["consecutive_correct"], 1)

    def test_independent_context_correct_sets_transfer_but_not_stabilized(self):
        profile, _ = reducer.apply_event(None, event("e1", correct=True, transfer_level="independent_context"))
        state = profile["exceptions"]["ex_a"]
        self.assertTrue(state["transfer_passed"])
        self.assertEqual(state["status"], "stabilizing")
        self.assertFalse(state["retention_passed"])
        self.assertNotEqual(state["status"], "stabilized")

    def test_retention_correct_sets_retention_but_not_permanent_mastery(self):
        profile, _ = reducer.apply_event(
            None,
            event("e1", correct=True, transfer_level="transfer", source="retention"),
        )
        state = profile["exceptions"]["ex_a"]
        self.assertTrue(state["transfer_passed"])
        self.assertTrue(state["retention_passed"])
        self.assertEqual(state["retention_stage"], "delayed_review")
        self.assertEqual(state["status"], "stabilizing")

    def test_wrong_transfer_resets_transfer_evidence(self):
        profile, _ = reducer.apply_event(None, event("e1", correct=True, transfer_level="transfer"))
        self.assertTrue(profile["exceptions"]["ex_a"]["transfer_passed"])
        later = event("e2", correct=False, transfer_level="transfer", context="ctx2")
        later["answered_at"] = "2026-08-11T19:05:00+00:00"
        updated, _ = reducer.apply_event(profile, later)
        state = updated["exceptions"]["ex_a"]
        self.assertFalse(state["transfer_passed"])
        self.assertEqual(state["status"], "active")
        self.assertEqual(state["consecutive_correct"], 0)

    def test_recent_contexts_are_deduplicated_and_ordered(self):
        profile, _ = reducer.apply_event(None, event("e1", correct=False, context="ctx1"))
        e2 = event("e2", correct=True, context="ctx2")
        e2["answered_at"] = "2026-08-11T19:01:00+00:00"
        profile, _ = reducer.apply_event(profile, e2)
        e3 = event("e3", correct=True, context="ctx1")
        e3["answered_at"] = "2026-08-11T19:02:00+00:00"
        profile, _ = reducer.apply_event(profile, e3)
        self.assertEqual(profile["exceptions"]["ex_a"]["recent_context_signatures"], ["ctx2", "ctx1"])

    def test_state_revision_increments_only_for_new_events(self):
        profile, _ = reducer.apply_event(None, event("e1", correct=True))
        self.assertEqual(profile["state_revision"], 1)
        profile2, applied = reducer.apply_event(profile, event("e1", correct=True))
        self.assertFalse(applied)
        self.assertEqual(profile2["state_revision"], 1)
        e2 = event("e2", correct=True, context="ctx2")
        e2["answered_at"] = "2026-08-11T19:03:00+00:00"
        profile3, _ = reducer.apply_event(profile2, e2)
        self.assertEqual(profile3["state_revision"], 2)


if __name__ == "__main__":
    unittest.main()
