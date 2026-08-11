#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parents[1]
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

import resolve_russian_explanation as resolver


def runtime_fixture():
    return {
        "units": {
            "exact_rule": {"explanation_id":"exact_rule","short_rule":"s","rule":"r","algorithm":[],"common_traps":[],"examples":[]},
            "broad_rule": {"explanation_id":"broad_rule","short_rule":"s","rule":"r","algorithm":[],"common_traps":[],"examples":[]},
            "second_rule": {"explanation_id":"second_rule","short_rule":"s","rule":"r","algorithm":[],"common_traps":[],"examples":[]},
        },
        "routes": {
            "item1::position::pos_1": {
                "route_id":"item1::position::pos_1",
                "trainer_item_id":"item1",
                "task_number":15,
                "precision":"position",
                "candidate_explanation_ids":["exact_rule"],
                "exact_explanation_id":"exact_rule",
                "fallback":"current_trainer_feedback",
                "legacy":False,
                "status":"enabled",
            },
            "item1::position::pos_2": {
                "route_id":"item1::position::pos_2",
                "trainer_item_id":"item1",
                "task_number":15,
                "precision":"position",
                "candidate_explanation_ids":["second_rule"],
                "exact_explanation_id":"second_rule",
                "fallback":"current_trainer_feedback",
                "legacy":False,
                "status":"enabled",
            },
            "item2::word::word_1": {
                "route_id":"item2::word::word_1",
                "trainer_item_id":"item2",
                "task_number":9,
                "precision":"word",
                "candidate_explanation_ids":["broad_rule"],
                "exact_explanation_id":None,
                "fallback":"current_trainer_feedback",
                "legacy":False,
                "status":"partial",
            },
        },
        "task_defaults": {
            **{str(i):{"task_number":i,"candidate_explanation_ids":[],"external_fallback_explanation_id":None,"fallback":"current_trainer_feedback"} for i in range(1,28)},
            "13":{"task_number":13,"candidate_explanation_ids":["broad_rule"],"external_fallback_explanation_id":"broad_rule","fallback":"external_then_current"},
        },
    }


class ResolverTests(unittest.TestCase):
    def test_exact_wrong_position_resolves_exact(self):
        result = {
            "trainer_item_id":"item1","task_number":15,"mode":"practice",
            "item_is_complete":True,"completion_complete":False,"item_is_correct":False,
            "evidence":[{"precision":"position","key":"pos_1","is_correct":False}],
        }
        out = resolver.resolve(runtime_fixture(), result)
        self.assertEqual(out["resolution"], "exact")
        self.assertEqual(out["explanation_ids"], ["exact_rule"])
        self.assertTrue(out["current_trainer_answer_authoritative"])

    def test_multiple_wrong_positions_return_distinct_explanations(self):
        result = {
            "trainer_item_id":"item1","task_number":15,"mode":"practice",
            "item_is_complete":True,"completion_complete":False,"item_is_correct":False,
            "evidence":[
                {"precision":"position","key":"pos_1","is_correct":False},
                {"precision":"position","key":"pos_2","is_correct":False},
            ],
        }
        out = resolver.resolve(runtime_fixture(), result)
        self.assertEqual(out["explanation_ids"], ["exact_rule","second_rule"])

    def test_partial_route_is_not_reported_exact(self):
        result = {
            "trainer_item_id":"item2","task_number":9,"mode":"practice",
            "item_is_complete":True,"completion_complete":False,"item_is_correct":False,
            "evidence":[{"precision":"word","key":"word_1","is_correct":False}],
        }
        out = resolver.resolve(runtime_fixture(), result)
        self.assertEqual(out["resolution"], "partial_safe")
        self.assertEqual(out["explanation_ids"], ["broad_rule"])

    def test_wrong_without_exact_evidence_uses_task_fallback_when_available(self):
        result = {
            "trainer_item_id":"item13","task_number":13,"mode":"practice",
            "item_is_complete":True,"completion_complete":False,"item_is_correct":False,
            "evidence":[],
        }
        out = resolver.resolve(runtime_fixture(), result)
        self.assertEqual(out["resolution"], "task_fallback")
        self.assertEqual(out["explanation_ids"], ["broad_rule"])

    def test_wrong_without_safe_external_mapping_preserves_current_feedback_only(self):
        result = {
            "trainer_item_id":"item8","task_number":8,"mode":"practice",
            "item_is_complete":True,"completion_complete":False,"item_is_correct":False,
            "evidence":[],
        }
        out = resolver.resolve(runtime_fixture(), result)
        self.assertEqual(out["resolution"], "none")
        self.assertEqual(out["explanation_ids"], [])
        self.assertTrue(out["current_feedback_preserved"])

    def test_demo_suppresses_before_attempt_completion(self):
        result = {
            "trainer_item_id":"item1","task_number":15,"mode":"demo",
            "item_is_complete":True,"completion_complete":False,"item_is_correct":False,
            "evidence":[{"precision":"position","key":"pos_1","is_correct":False}],
        }
        out = resolver.resolve(runtime_fixture(), result)
        self.assertFalse(out["external_explanation_allowed"])
        self.assertEqual(out["gate_reason"], "demo_not_complete")
        self.assertEqual(out["explanation_ids"], [])

    def test_demo_allows_after_attempt_completion(self):
        result = {
            "trainer_item_id":"item1","task_number":15,"mode":"demo",
            "item_is_complete":True,"completion_complete":True,"item_is_correct":False,
            "evidence":[{"precision":"position","key":"pos_1","is_correct":False}],
        }
        out = resolver.resolve(runtime_fixture(), result)
        self.assertTrue(out["external_explanation_allowed"])
        self.assertEqual(out["resolution"], "exact")

    def test_control_suppresses_before_set_completion(self):
        result = {
            "trainer_item_id":"item1","task_number":15,"mode":"control",
            "item_is_complete":True,"completion_complete":False,"item_is_correct":False,
            "evidence":[{"precision":"position","key":"pos_1","is_correct":False}],
        }
        out = resolver.resolve(runtime_fixture(), result)
        self.assertFalse(out["external_explanation_allowed"])
        self.assertEqual(out["gate_reason"], "control_not_complete")

    def test_unanswered_item_never_shows_external_explanation(self):
        result = {
            "trainer_item_id":"item1","task_number":15,"mode":"practice",
            "item_is_complete":False,"completion_complete":False,"item_is_correct":None,
            "evidence":[],
        }
        out = resolver.resolve(runtime_fixture(), result)
        self.assertFalse(out["external_explanation_allowed"])
        self.assertEqual(out["gate_reason"], "item_not_complete")


if __name__ == "__main__":
    unittest.main()
