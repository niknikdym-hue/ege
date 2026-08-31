#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REVIEW = HERE / "RU13-EXPRESSIVE-COMPONENT-BOUNDARY-REVIEW-v0.1.json"
PROPOSED_AUTH = HERE / "RU13-EXPRESSIVE-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
EXISTING_AUTH = HERE / "RU13-EXPRESSIVE-EXISTING-CANDIDATES-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"

EXPECTED_PROPOSED = {
    "ru-expressive-alliteration", "ru-expressive-personification",
    "ru-expressive-syntactic-parallelism", "ru-expressive-question-answer-form",
    "ru-expressive-gradation", "ru-expressive-inversion",
    "ru-expressive-lexical-repetition", "ru-expressive-epiphora",
    "ru-expressive-antithesis", "ru-expressive-rhetorical-question",
    "ru-expressive-rhetorical-exclamation", "ru-expressive-polysyndeton",
    "ru-expressive-asyndeton", "ru-expressive-litotes",
}
EXPECTED_EXISTING = {
    "candidate-033": "ru-expressive-assonance",
    "candidate-034": "ru-expressive-hyperbole",
    "candidate-035": "ru-expressive-metonymy",
    "candidate-036": "ru-expressive-anaphora",
    "candidate-037": "ru-expressive-parcellation",
    "candidate-038": "ru-expressive-homogeneous-rows",
    "candidate-039": "ru-expressive-address",
    "candidate-040": "ru-expressive-epithet",
    "candidate-041": "ru-expressive-metaphor",
    "candidate-042": "ru-expressive-comparison",
}


def main() -> int:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    proposed_auth = json.loads(PROPOSED_AUTH.read_text(encoding="utf-8"))
    existing_auth = json.loads(EXISTING_AUTH.read_text(encoding="utf-8"))

    if review.get("status") != "CENTRAL_BRAIN_COMPONENT_BOUNDARY_REVIEW_24_OF_24_BOUNDED_SEMANTICS_ACCEPTED":
        raise AssertionError("RU13 24/24 boundary status drift")
    if review.get("admission_effect") != "TWENTY_FOUR_COMPONENT_SEMANTICS_ACCEPTED_OBJECT_COUNTS_UNCHANGED":
        raise AssertionError("RU13 24/24 admission effect drift")
    if set(review.get("acceptance_overlay_refs") or []) != {PROPOSED_AUTH.name, EXISTING_AUTH.name}:
        raise AssertionError("RU13 24/24 acceptance overlay refs drift")

    expected_summary = {
        "explicit_components": 24,
        "bounded_subject_semantics_accepted": 24,
        "existing_candidate_components_pending": 0,
        "component_content_complete": 24,
        "canonical_school_semantic_admissions": 0,
        "ru_subject_semantic_admissions": 24,
        "object_level_admission_units_closed_by_semantic_overlay": 0,
        "object_level_requirements_closed_by_semantic_overlay": 0,
        "false_exact_mastery_admissions": 0,
    }
    if review.get("summary") != expected_summary:
        raise AssertionError(f"RU13 24/24 summary drift: {review.get('summary')}")

    policy = review.get("policy") or {}
    for key in (
        "reuse_existing_semantics_first",
        "component_specific_independent_evidence_required",
        "rhetorical_address_duplicate_forbidden",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"RU13 policy weakened: {key}")
    for key in (
        "content_presence_implies_admission",
        "candidate_presence_implies_admission",
        "generic_expressive_attempt_can_emit_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "exam_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"RU13 fail-closed policy weakened: {key}")

    if proposed_auth.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU13_EXPRESSIVE_BOUNDED_SUBJECT_SEMANTICS":
        raise AssertionError("RU13 proposed-component authority missing")
    if existing_auth.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU13_EXISTING_CANDIDATE_BOUNDED_SUBJECT_SEMANTICS":
        raise AssertionError("RU13 existing-candidate authority missing")
    for authority, expected_count in ((proposed_auth, 14), (existing_auth, 10)):
        summary = authority.get("summary") or {}
        if summary.get("accepted_bounded_subject_semantics") != expected_count:
            raise AssertionError("RU13 authority accepted-count drift")
        if summary.get("object_level_admission_units_closed") != 0 or summary.get("object_level_requirements_closed") != 0:
            raise AssertionError("RU13 semantic authority falsely closed object accounting")
        if summary.get("false_exact_mastery_admissions") != 0:
            raise AssertionError("RU13 semantic authority permits false exact mastery")

    proposed_rows = review.get("proposed_content_components") or []
    proposed_by_id = {str(row.get("semantic_id")): row for row in proposed_rows if isinstance(row, dict)}
    if set(proposed_by_id) != EXPECTED_PROPOSED or len(proposed_rows) != 14:
        raise AssertionError("RU13 proposed component set drift")
    proposed_authority_ids = {
        str(row.get("accepted_semantic_id"))
        for row in proposed_auth.get("decisions", [])
        if isinstance(row, dict)
    }
    if proposed_authority_ids != EXPECTED_PROPOSED:
        raise AssertionError("RU13 proposed authority identity set drift")
    for sid, row in proposed_by_id.items():
        if row.get("status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
            raise AssertionError(f"RU13 proposed semantic lost acceptance: {sid}")
        if not str(row.get("acceptance_ref", "")).startswith(PROPOSED_AUTH.name + "#"):
            raise AssertionError(f"RU13 proposed semantic lacks authority ref: {sid}")

    existing_rows = review.get("existing_candidate_components") or []
    existing_by_candidate = {str(row.get("ref")): row for row in existing_rows if isinstance(row, dict)}
    if set(existing_by_candidate) != set(EXPECTED_EXISTING) or len(existing_rows) != 10:
        raise AssertionError("RU13 existing candidate component set drift")
    existing_authority = {
        str(row.get("candidate_ref")): str(row.get("accepted_semantic_id"))
        for row in existing_auth.get("decisions", [])
        if isinstance(row, dict)
    }
    if existing_authority != EXPECTED_EXISTING:
        raise AssertionError("RU13 existing authority mapping drift")
    for candidate_ref, semantic_id in EXPECTED_EXISTING.items():
        row = existing_by_candidate[candidate_ref]
        if row.get("accepted_semantic_id") != semantic_id:
            raise AssertionError(f"RU13 existing accepted id drift: {candidate_ref}")
        if row.get("status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
            raise AssertionError(f"RU13 existing semantic lost acceptance: {candidate_ref}")
        if not str(row.get("acceptance_ref", "")).startswith(EXISTING_AUTH.name + "#"):
            raise AssertionError(f"RU13 existing semantic lacks authority ref: {candidate_ref}")

    address = existing_by_candidate["candidate-039"]
    if address.get("accepted_semantic_id") != "ru-expressive-address":
        raise AssertionError("RU13 address owner drift")
    if address.get("special_guard") != "OWNS_RHETORICAL_ADDRESS_BOUNDARY_NO_DUPLICATE_ID":
        raise AssertionError("RU13 rhetorical-address guard drift")
    all_ids = EXPECTED_PROPOSED | set(EXPECTED_EXISTING.values())
    if len(all_ids) != 24 or "ru-expressive-rhetorical-address" in all_ids:
        raise AssertionError("RU13 24-component identity denominator drift")

    guards = review.get("cross_boundary_guards")
    if not isinstance(guards, list) or len(guards) < 9:
        raise AssertionError("RU13 cross-boundary guard inventory incomplete")

    print("RU13_EXPRESSIVE_COMPONENT_BOUNDARY_REVIEW=PASS")
    print("EXPLICIT_COMPONENTS=24")
    print("ACCEPTED_BOUNDED_SUBJECT_SEMANTICS=24")
    print("EXISTING_CANDIDATES_PENDING=0")
    print("OBJECT_LEVEL_CLOSURES_FROM_SEMANTIC_OVERLAY=0")
    print("RHETORICAL_ADDRESS_DUPLICATES=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
