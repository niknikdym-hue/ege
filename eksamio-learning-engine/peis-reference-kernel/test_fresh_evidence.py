#!/usr/bin/env python3
"""F3 regressions using structural-only, schema-valid evidence (no student data).

Run: python -m unittest discover -s eksamio-learning-engine/peis-reference-kernel
"""

from __future__ import annotations

import copy
import itertools
import unittest
from datetime import datetime, timedelta, timezone

from peis_reference_kernel import assess_readiness, infer_retention, snapshot
from run_reference_kernel_validation import (
    EVENT_SCHEMA_PATH,
    MASTERY_SCHEMA_PATH,
    NBA_SCHEMA_PATH,
    READINESS_SCHEMA_PATH,
    RETENTION_SCHEMA_PATH,
    STATE_SCHEMA_PATH,
    load,
    math_event,
    nested_schema,
    validate_snapshot,
    validator,
)

TARGET = "fixture-mathematics-target-12"


def event(sequence, *, correct=True, delayed=False, verification=False, origin=None):
    value = math_event(f"f3.structural.{sequence:03d}", sequence=sequence, correct=correct)
    at = (datetime(2026, 8, 20, tzinfo=timezone.utc) + timedelta(days=sequence)).isoformat()
    value["session_id"] = f"session-f3-{sequence}"
    value["created_at"] = at
    value["timestamps"].update(occurred_at_client=at, received_at_server=at)
    if origin:
        value["transfer_context"]["origin_event_refs"] = [origin["event_id"]]
    if delayed:
        value["retention_context"] = {
            "kind": "DELAYED_RETENTION",
            "delay_seconds": int((datetime.fromisoformat(at) - datetime.fromisoformat(origin["created_at"])).total_seconds()),
            "scheduled_by_policy_version": "f3-structural-fixture",
        }
    if verification:
        value["session_id"] = origin["session_id"]
        at = (datetime.fromisoformat(origin["created_at"]) + timedelta(minutes=5)).isoformat()
        value["created_at"] = at
        value["timestamps"].update(occurred_at_client=at, received_at_server=at)
        value["transfer_context"]["kind"] = "SAME_SESSION_VERIFICATION"
        value["retention_context"] = {
            "kind": "SAME_SESSION", "delay_seconds": 0, "scheduled_by_policy_version": None,
        }
    return value


class FreshEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.event_validator = validator(load(EVENT_SCHEMA_PATH))
        cls.validators = {
            "state_validator": validator(load(STATE_SCHEMA_PATH)),
            "mastery_validator": validator(load(MASTERY_SCHEMA_PATH)),
            "readiness_validator": validator(nested_schema(load(READINESS_SCHEMA_PATH), "readiness_state")),
            "retention_validator": validator(nested_schema(load(RETENTION_SCHEMA_PATH), "state")),
            "nba_validator": validator(load(NBA_SCHEMA_PATH)),
        }

    def setUp(self):
        self.initial = event(1)
        self.retained = event(2, delayed=True, origin=self.initial)
        self.error = event(3, correct=False)
        self.verified = event(4, verification=True, origin=self.error)
        self.base = [self.initial, self.retained]

    def project(self, events):
        before = copy.deepcopy(events)
        for value in events:
            self.event_validator.validate(value)
        value = snapshot(events, TARGET, [], goal_context=None)
        validate_snapshot(value, **self.validators)
        self.assertEqual(events, before, "projection must not rewrite evidence")
        self.assertEqual(value["state"]["mastery"]["band"], value["mastery"]["mastery"]["band"])
        return value

    def assert_projection(self, value, *, mastery, retention, readiness, contradiction, action):
        self.assertEqual(value["mastery"]["mastery"]["band"], mastery)
        self.assertEqual(value["retention"]["current_state"], retention)
        self.assertEqual(value["readiness"]["status"], readiness)
        self.assertEqual(value["mastery"]["evidence_summaries"]["contradictory"]["observed"], contradiction)
        self.assertEqual(value["nba"]["action_type"], action)

    def assert_pending(self, value):
        self.assert_projection(
            value, mastery="DEVELOPING", retention="SCHEDULED", readiness="NEEDS_VERIFICATION",
            contradiction=True, action="VERIFY_UNCERTAIN_STATE",
        )
        self.assertEqual(value["mastery"]["system_inference"]["confidence_band"], "LOW")

    def test_retained_success_remains_strong_without_new_failure(self):
        self.assert_projection(
            self.project(self.base), mastery="STRONG", retention="RETAINED_AFTER_DELAYED_CHECK",
            readiness="ALREADY_STRONG_NOT_CURRENT_PRIORITY", contradiction=False, action="MOVE_TO_NEXT_TARGET",
        )

    def test_new_ordinary_error_invalidates_current_retained_claim_not_history(self):
        before = self.project(self.base)
        after = self.project(self.base + [self.error])
        self.assert_pending(after)
        self.assertEqual(after["retention"]["history"], before["retention"]["history"])
        self.assertEqual(after["retention"]["last_delayed_check"], before["retention"]["last_delayed_check"])
        self.assertIn(self.error["event_id"], after["retention"]["source_evidence_refs"])
        self.assertEqual(after["retention"]["history"]["previous_retention_failures"], 0)
        self.assertIsNone(after["retention"]["next_due_calculation"]["due_window_start"])

    def test_new_verification_resolves_contradiction_but_does_not_renew_retention(self):
        value = self.project(self.base + [self.error, self.verified])
        self.assert_projection(
            value, mastery="ESTABLISHED", retention="SCHEDULED", readiness="READY_TO_LEARN_OR_PRACTICE",
            contradiction=False, action="RETENTION_REVIEW",
        )
        self.assertEqual(value["retention"]["history"]["event_refs"], [self.retained["event_id"]])
        self.assertEqual(value["retention"]["next_due_calculation"]["input_refs"], [self.verified["event_id"]])
        self.assertEqual(value["mastery"]["system_inference"]["contradiction_status"], "NONE_OBSERVED")

    def test_single_verification_uses_existing_count_rule_not_automatic_established(self):
        value = self.project([self.error, self.verified])
        self.assertEqual(value["mastery"]["mastery"]["band"], "DEVELOPING")
        self.assertEqual(value["retention"]["current_state"], "SCHEDULED")
        self.assertFalse(value["mastery"]["evidence_summaries"]["contradictory"]["observed"])

    def test_new_delayed_success_restores_retained_after_ordinary_error(self):
        renewed = event(5, delayed=True, origin=self.verified)
        value = self.project(self.base + [self.error, self.verified, renewed])
        self.assert_projection(
            value, mastery="STRONG", retention="RETAINED_AFTER_DELAYED_CHECK",
            readiness="ALREADY_STRONG_NOT_CURRENT_PRIORITY", contradiction=False, action="MOVE_TO_NEXT_TARGET",
        )
        self.assertEqual(value["retention"]["history"]["previous_retention_successes"], 2)
        self.assertEqual(value["retention"]["last_delayed_check"]["event_ref"], renewed["event_id"])

    def test_assisted_answer_cannot_resolve_error_or_renew_retention(self):
        for level in ["RULE_EXPLANATION", "SOLUTION_EXPOSED"]:
            with self.subTest(level=level):
                helped = copy.deepcopy(self.verified)
                helped["assistance"].update(level=level, help_event_refs=["f3.help"], assistance_provider="structural-fixture")
                value = self.project(self.base + [self.error, helped])
                self.assert_pending(value)
                self.assertEqual(value["mastery"]["evidence_summaries"]["independent"]["accepted_event_count"], 3)
                self.assertEqual(value["mastery"]["evidence_summaries"]["assisted"]["accepted_event_count"], 1)

    def test_assistance_after_retained_does_not_add_independent_credit(self):
        helped = event(3)
        helped["assistance"].update(level="RULE_EXPLANATION", help_event_refs=["f3.help"], assistance_provider="structural-fixture")
        before = self.project(self.base)
        after = self.project(self.base + [helped])
        self.assertEqual(after["mastery"]["evidence_summaries"]["independent"], before["mastery"]["evidence_summaries"]["independent"])
        self.assertEqual(after["retention"]["history"], before["retention"]["history"])
        self.assertIn("INDEPENDENT_VERIFICATION_REQUIRED", after["mastery"]["system_inference"]["reason_codes"])
        self.assertEqual(after["nba"]["action_type"], "INDEPENDENT_PRACTICE")
        self.assertTrue(after["nba"]["verification_required"])

    def test_new_failed_delayed_check_requires_restabilization(self):
        failed = event(3, correct=False, delayed=True, origin=self.retained)
        value = self.project(self.base + [failed])
        self.assert_projection(
            value, mastery="DEVELOPING", retention="RETENTION_FAILURE_RESTABILIZATION_NEEDED",
            readiness="NEEDS_VERIFICATION", contradiction=True, action="GUIDED_PRACTICE",
        )
        self.assertEqual(value["retention"]["history"]["previous_retention_failures"], 1)
        self.assertEqual(value["retention"]["last_delayed_check"]["event_ref"], failed["event_id"])

    def test_error_before_successful_delayed_check_does_not_invalidate_it(self):
        old_error = event(1, correct=False)
        value = self.project([old_error, self.retained])
        self.assert_projection(
            value, mastery="STRONG", retention="RETAINED_AFTER_DELAYED_CHECK",
            readiness="ALREADY_STRONG_NOT_CURRENT_PRIORITY", contradiction=False, action="MOVE_TO_NEXT_TARGET",
        )

    def test_ordinary_success_cannot_clear_contradiction(self):
        self.assert_pending(self.project(self.base + [self.error, event(4)]))

    def test_ordinary_success_preserves_prior_independent_verification(self):
        value = self.project([self.error, self.verified, event(5), event(6)])
        self.assert_projection(
            value, mastery="ESTABLISHED", retention="SCHEDULED", readiness="READY_TO_LEARN_OR_PRACTICE",
            contradiction=False, action="RETENTION_REVIEW",
        )

    def test_ordinary_success_preserves_resolved_error_after_delayed_check(self):
        renewed = event(5, delayed=True, origin=self.verified)
        events = [self.error, self.verified, renewed, event(6)]
        expected = self.project(events)
        self.assert_projection(
            expected, mastery="STRONG", retention="RETAINED_AFTER_DELAYED_CHECK",
            readiness="ALREADY_STRONG_NOT_CURRENT_PRIORITY", contradiction=False, action="MOVE_TO_NEXT_TARGET",
        )
        for permutation in itertools.permutations(events):
            self.assertEqual(self.project(list(permutation)), expected)

    def test_new_error_reopens_previously_resolved_contradiction(self):
        renewed = event(5, delayed=True, origin=self.verified)
        new_error = event(7, correct=False)
        events = [self.error, self.verified, renewed, event(6), new_error]
        value = self.project(events)
        self.assert_pending(value)
        self.assertEqual(value["retention"]["history"]["previous_retention_failures"], 0)
        self.assertEqual(value["retention"]["last_delayed_check"]["event_ref"], renewed["event_id"])
        self.assert_pending(self.project(events + [event(8)]))

    def test_new_error_after_same_session_verification_requires_new_verification(self):
        new_error = event(6, correct=False)
        events = [self.error, self.verified, event(5), new_error]
        self.assert_pending(self.project(events))
        newer_verification = event(7, verification=True, origin=new_error)
        value = self.project(events + [newer_verification, event(8)])
        self.assert_projection(
            value, mastery="ESTABLISHED", retention="SCHEDULED", readiness="READY_TO_LEARN_OR_PRACTICE",
            contradiction=False, action="RETENTION_REVIEW",
        )

    def test_input_order_does_not_change_any_projection(self):
        for events in [self.base + [self.error], self.base + [self.error, self.verified]]:
            expected = self.project(events)
            for permutation in itertools.permutations(events):
                self.assertEqual(self.project(list(permutation)), expected)

    def test_server_sequence_wins_over_client_and_timestamp_order(self):
        self.error["created_at"] = "2026-08-19T00:00:00+00:00"
        self.error["timestamps"].update(
            occurred_at_client="2026-08-19T00:00:00+00:00",
            received_at_server="2026-08-19T00:00:00+00:00",
        )
        self.assert_pending(self.project([self.error] + self.base))

    def test_equal_sequence_uses_existing_received_at_order(self):
        for value in self.base + [self.error]:
            value["timestamps"]["server_sequence"] = 1
        self.assert_pending(self.project([self.error, self.retained, self.initial]))

    def test_other_skill_failure_does_not_invalidate_target(self):
        other = copy.deepcopy(self.error)
        other["semantic_targets"][0]["semantic_id"] = "fixture-other-skill"
        other["error_observations"][0]["semantic_id"] = "fixture-other-skill"
        self.assertEqual(self.project(self.base + [other]), self.project(self.base))

    def test_composite_failure_is_not_exact_failure(self):
        self.error["semantic_targets"][0]["mapping_resolution"] = "COMPOSITE"
        value = self.project(self.base + [self.error])
        self.assertEqual(value["mastery"]["mastery"]["band"], "STRONG")
        self.assertEqual(value["retention"]["current_state"], "RETAINED_AFTER_DELAYED_CHECK")
        self.assertFalse(value["mastery"]["evidence_summaries"]["contradictory"]["observed"])

    def test_retention_accepts_single_pass_iterables(self):
        events = self.base + [self.error, self.verified]
        self.assertEqual(infer_retention(iter(events), TARGET), infer_retention(events, TARGET))

    def test_content_guard_still_takes_precedence(self):
        value = assess_readiness(self.base + [self.error], TARGET, [], goal_context=None, content_available=False)
        self.validators["readiness_validator"].validate(value)
        self.assertEqual(value["status"], "CONTENT_UNAVAILABLE")

    def test_unreviewed_prerequisite_still_cannot_block(self):
        edge = {
            "edge_id": "f3-unreviewed-edge",
            "source_semantic_id": "fixture-other-skill",
            "target_semantic_id": TARGET,
            "relation_type": "REQUIRED",
            "review_status": "PENDING_REVIEW",
            "admission_scope": "CANONICAL_GRAPH",
        }
        value = assess_readiness(self.base + [self.error], TARGET, [edge], goal_context=None)
        self.assertEqual(value["required_prerequisite_assessments"], [])
        self.assertEqual(value["status"], "NEEDS_VERIFICATION")


if __name__ == "__main__":
    unittest.main()
