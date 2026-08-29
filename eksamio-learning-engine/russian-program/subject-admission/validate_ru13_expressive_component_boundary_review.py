#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
CONTENT = PROGRAM / "production-learning-content"
REVIEW = HERE / "RU13-EXPRESSIVE-COMPONENT-BOUNDARY-REVIEW-v0.1.json"
ACCEPTANCE = HERE / "RU13-EXPRESSIVE-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
PROPOSED_WAVES = (
    CONTENT / "RU-PROG-13-EXPRESSIVE-MEANS-WAVE-001-v0.1.json",
    CONTENT / "RU-PROG-13-EXPRESSIVE-MEANS-WAVE-002-v0.1.json",
)
EXISTING_WAVE = CONTENT / "RU-PROG-13-EXPRESSIVE-MEANS-WAVE-003-v0.1.json"

EXPECTED_CANDIDATE_SOURCES = {
    "candidate-033": "device_assonance",
    "candidate-034": "device_hyperbole",
    "candidate-035": "device_metonymy",
    "candidate-036": "device_anaphora",
    "candidate-037": "device_parcellation",
    "candidate-038": "device_homogeneous_rows",
    "candidate-039": "device_address",
    "candidate-040": "device_epithet",
    "candidate-041": "device_metaphor",
    "candidate-042": "device_comparison",
}
EXPECTED_ACCEPTED = {
    "ru-expressive-alliteration",
    "ru-expressive-personification",
    "ru-expressive-syntactic-parallelism",
    "ru-expressive-question-answer-form",
    "ru-expressive-gradation",
    "ru-expressive-inversion",
    "ru-expressive-lexical-repetition",
    "ru-expressive-epiphora",
    "ru-expressive-antithesis",
    "ru-expressive-rhetorical-question",
    "ru-expressive-rhetorical-exclamation",
    "ru-expressive-polysyndeton",
    "ru-expressive-asyndeton",
    "ru-expressive-litotes",
}


def main() -> int:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))

    expected_summary = {
        "explicit_components": 24,
        "bounded_subject_semantics_accepted": 14,
        "existing_candidate_components_pending": 10,
        "component_content_complete": 24,
        "canonical_school_semantic_admissions": 0,
        "ru_subject_semantic_admissions": 14,
        "object_level_admission_units_closed_by_semantic_overlay": 0,
        "object_level_requirements_closed_by_semantic_overlay": 0,
    }
    if review.get("summary") != expected_summary:
        raise AssertionError(f"RU13 component review summary drift: {review.get('summary')}")
    if review.get("status") != "CENTRAL_BRAIN_COMPONENT_BOUNDARY_REVIEW_PARTIAL_WITH_14_BOUNDED_SEMANTICS_ACCEPTED":
        raise AssertionError("RU13 component review status drift")
    if review.get("admission_effect") != "FOURTEEN_PROPOSED_COMPONENTS_ACCEPTED_TEN_EXISTING_CANDIDATES_PENDING_OBJECT_COUNTS_UNCHANGED":
        raise AssertionError("RU13 boundary admission effect drift")
    if review.get("acceptance_overlay_ref") != ACCEPTANCE.name:
        raise AssertionError("RU13 acceptance overlay ref drift")

    expected_policy = {
        "reuse_existing_semantics_first": True,
        "content_presence_implies_admission": False,
        "candidate_presence_implies_admission": False,
        "generic_expressive_attempt_can_emit_component_mastery": False,
        "component_specific_independent_evidence_required": True,
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
        "rhetorical_address_duplicate_forbidden": True,
    }
    if review.get("policy") != expected_policy:
        raise AssertionError("RU13 boundary policy drift")

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU13_EXPRESSIVE_BOUNDED_SUBJECT_SEMANTICS":
        raise AssertionError("RU13 bounded acceptance authority missing")
    accepted_rows = acceptance.get("decisions") or []
    accepted_ids = {str(row.get("accepted_semantic_id")) for row in accepted_rows if isinstance(row, dict)}
    if accepted_ids != EXPECTED_ACCEPTED or len(accepted_rows) != 14:
        raise AssertionError("RU13 accepted semantic authority set drift")
    a_summary = acceptance.get("summary") or {}
    if a_summary.get("object_level_admission_units_closed") != 0 or a_summary.get("object_level_requirements_closed") != 0:
        raise AssertionError("RU13 semantic acceptance falsely closed object-level accounting")

    existing = review.get("existing_candidate_components") or []
    proposed = review.get("proposed_content_components") or []
    if len(existing) != 10 or len(proposed) != 14:
        raise AssertionError("RU13 24-component boundary drift")
    actual_sources = {str(row.get("ref")): str(row.get("source_id")) for row in existing if isinstance(row, dict)}
    if actual_sources != EXPECTED_CANDIDATE_SOURCES:
        raise AssertionError("RU13 existing candidate/source mapping drift")
    if any(row.get("status") != "CONTENT_READY_EXACT_BOUNDARY_ACCEPTANCE_REQUIRED_NOT_ADMITTED" for row in existing):
        raise AssertionError("existing RU13 candidate was silently admitted")
    address = next(row for row in existing if row.get("ref") == "candidate-039")
    if address.get("special_guard") != "OWNS_RHETORICAL_ADDRESS_BOUNDARY_NO_DUPLICATE_ID":
        raise AssertionError("candidate-039 rhetorical-address ownership guard drift")

    proposed_by_id = {str(row.get("semantic_id")): row for row in proposed if isinstance(row, dict)}
    if set(proposed_by_id) != EXPECTED_ACCEPTED:
        raise AssertionError("RU13 accepted boundary identity set drift")
    for sid, row in proposed_by_id.items():
        if row.get("status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
            raise AssertionError(f"RU13 accepted semantic lost acceptance: {sid}")
        if not str(row.get("acceptance_ref", "")).startswith(ACCEPTANCE.name + "#"):
            raise AssertionError(f"RU13 accepted semantic lacks durable authority ref: {sid}")
        if len(str(row.get("boundary_guard", "")).strip()) < 20:
            raise AssertionError(f"RU13 accepted semantic lacks bounded scope: {sid}")
        if row.get("boundary_guard") != next(item for item in accepted_rows if item.get("accepted_semantic_id") == sid).get("boundary_guard"):
            raise AssertionError(f"RU13 accepted boundary/authority mismatch: {sid}")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    objects = inventory.get("objects") or []
    for candidate_ref, source_id in EXPECTED_CANDIDATE_SOURCES.items():
        matches = [
            row for row in objects
            if isinstance(row, dict)
            and row.get("candidate_canonical_owner") == candidate_ref
            and row.get("source_id") == source_id
            and row.get("audit_classification") == "EGE_TAXONOMY_NODE"
        ]
        if len(matches) != 1:
            raise AssertionError(f"exact existing candidate/source evidence mismatch: {candidate_ref}/{source_id}")
        source = matches[0]
        if source.get("authority_status") != "current" or source.get("review_status") != "source_verified":
            raise AssertionError(f"existing RU13 source evidence not current/source-verified: {candidate_ref}")

    proposed_texts = [path.read_text(encoding="utf-8") for path in PROPOSED_WAVES]
    for semantic_id in EXPECTED_ACCEPTED:
        if sum(semantic_id in text for text in proposed_texts) != 1:
            raise AssertionError(f"accepted RU13 semantic must belong to exactly one content wave: {semantic_id}")
    if any("ru-expressive-rhetorical-address" in text for text in proposed_texts):
        raise AssertionError("duplicate rhetorical-address learner identity was materialized")

    existing_payload = json.loads(EXISTING_WAVE.read_text(encoding="utf-8"))
    existing_units = existing_payload.get("units") or []
    if len(existing_units) != 10:
        raise AssertionError("RU13 existing-candidate content wave must contain exactly 10 units")
    content_candidates = {str(row.get("semantic_candidate_ref")): str(row.get("source_semantic_ref")) for row in existing_units}
    if content_candidates != EXPECTED_CANDIDATE_SOURCES:
        raise AssertionError("RU13 existing-candidate content coverage drift")
    if any(row.get("proposed_semantic_id") for row in existing_units):
        raise AssertionError("existing RU13 candidate content created duplicate proposed identity")

    guards = review.get("cross_boundary_guards")
    if not isinstance(guards, list) or len(guards) < 9:
        raise AssertionError("RU13 cross-boundary guard inventory incomplete")

    print("RU13_EXPRESSIVE_COMPONENT_BOUNDARY_REVIEW=PASS")
    print("EXPLICIT_COMPONENTS=24")
    print("ACCEPTED_BOUNDED_SUBJECT_SEMANTICS=14")
    print("EXISTING_CANDIDATES_PENDING=10")
    print("OBJECT_LEVEL_CLOSURES_FROM_SEMANTIC_OVERLAY=0")
    print("RHETORICAL_ADDRESS_DUPLICATES=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
