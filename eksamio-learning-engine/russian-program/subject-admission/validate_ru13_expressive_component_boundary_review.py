#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
CONTENT = PROGRAM / "production-learning-content"
REVIEW = HERE / "RU13-EXPRESSIVE-COMPONENT-BOUNDARY-REVIEW-v0.1.json"
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
EXPECTED_PROPOSED = {
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
    expected_summary = {
        "explicit_components": 24,
        "new_proposed_components_with_content": 14,
        "existing_candidate_components_with_content": 10,
        "component_content_complete": 24,
        "existing_candidates_requiring_exact_boundary_acceptance": 10,
        "proposed_components_requiring_subject_acceptance": 14,
        "canonical_semantic_admissions": 0,
        "ru_proposal_admissions": 0,
    }
    if review.get("summary") != expected_summary:
        raise AssertionError(f"RU13 component review summary drift: {review.get('summary')}")
    if review.get("status") != "CENTRAL_BRAIN_COMPONENT_BOUNDARY_REVIEW_CONTENT_COMPLETE_ACCEPTANCE_PENDING":
        raise AssertionError("RU13 component review status drift")
    if review.get("admission_effect") != "NONE_UNTIL_EXPLICIT_CANONICAL_SEMANTIC_ACCEPTANCE":
        raise AssertionError("RU13 boundary review admission effect weakened")

    policy = review.get("policy", {})
    expected_policy = {
        "reuse_existing_semantics_first": True,
        "content_presence_implies_admission": False,
        "candidate_presence_implies_admission": False,
        "generic_expressive_attempt_can_emit_component_mastery": False,
        "component_specific_independent_evidence_required": True,
        "rhetorical_address_duplicate_forbidden": True,
    }
    if policy != expected_policy:
        raise AssertionError(f"RU13 review policy drift: {policy}")

    existing = review.get("existing_candidate_components")
    proposed = review.get("proposed_content_components")
    if not isinstance(existing, list) or not isinstance(proposed, list):
        raise AssertionError("RU13 component arrays are invalid")
    actual_sources = {str(row.get("ref")): str(row.get("source_id")) for row in existing}
    if actual_sources != EXPECTED_CANDIDATE_SOURCES:
        raise AssertionError(f"RU13 existing candidate/source mapping drift: {actual_sources}")
    proposed_ids = {str(row.get("semantic_id")) for row in proposed}
    if proposed_ids != EXPECTED_PROPOSED:
        raise AssertionError("RU13 proposed content semantic set drift")

    expected_existing_content = "production-learning-content/RU-PROG-13-EXPRESSIVE-MEANS-WAVE-003-v0.1.json"
    for row in existing:
        if row.get("status") != "CONTENT_READY_EXACT_BOUNDARY_ACCEPTANCE_REQUIRED_NOT_ADMITTED":
            raise AssertionError("existing RU13 candidate was silently admitted or lost content-ready state")
        if row.get("content_ref") != expected_existing_content:
            raise AssertionError(f"existing RU13 content ref drift: {row.get('ref')}")
    address = next(row for row in existing if row.get("ref") == "candidate-039")
    if address.get("special_guard") != "OWNS_RHETORICAL_ADDRESS_BOUNDARY_NO_DUPLICATE_ID":
        raise AssertionError("candidate-039 rhetorical-address ownership guard drift")

    for row in proposed:
        if row.get("status") != "CONTENT_READY_DEFINITION_BOUNDARY_READY_FOR_SUBJECT_ACCEPTANCE_NOT_CANONICAL":
            raise AssertionError("RU13 proposed semantic was silently canonicalized or lost content-ready state")
        if not str(row.get("content_ref", "")).startswith("production-learning-content/RU-PROG-13-EXPRESSIVE-MEANS-WAVE-"):
            raise AssertionError(f"RU13 proposed semantic lacks production content ref: {row.get('semantic_id')}")
        if len(str(row.get("boundary_guard", "")).strip()) < 20:
            raise AssertionError(f"RU13 proposed semantic lacks bounded scope: {row.get('semantic_id')}")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    inventory_objects = inventory.get("objects", [])
    for candidate_ref, source_id in EXPECTED_CANDIDATE_SOURCES.items():
        matches = [
            row for row in inventory_objects
            if isinstance(row, dict)
            and row.get("candidate_canonical_owner") == candidate_ref
            and row.get("source_id") == source_id
        ]
        if len(matches) != 1:
            raise AssertionError(f"exact existing candidate/source evidence mismatch: {candidate_ref}/{source_id}")
        row = matches[0]
        if row.get("authority_status") != "current" or row.get("review_status") != "source_verified":
            raise AssertionError(f"existing RU13 source evidence is not current/source-verified: {candidate_ref}")
        if row.get("audit_classification") != "EGE_TAXONOMY_NODE":
            raise AssertionError(f"existing RU13 source evidence classification drift: {candidate_ref}")
        expected_ref = f"03-RUSSIAN-SKILL-GRAPH.json#skills[{source_id}]"
        if expected_ref not in (row.get("evidence_provenance_refs") or []):
            raise AssertionError(f"existing RU13 source provenance drift: {candidate_ref}")

    proposed_texts = [path.read_text(encoding="utf-8") for path in PROPOSED_WAVES]
    for semantic_id in EXPECTED_PROPOSED:
        if sum(semantic_id in text for text in proposed_texts) != 1:
            raise AssertionError(f"proposed RU13 semantic must belong to exactly one content wave: {semantic_id}")
    if any("ru-expressive-rhetorical-address" in text for text in proposed_texts):
        raise AssertionError("duplicate rhetorical-address semantic was materialized")

    existing_payload = json.loads(EXISTING_WAVE.read_text(encoding="utf-8"))
    existing_units = existing_payload.get("units")
    if not isinstance(existing_units, list) or len(existing_units) != 10:
        raise AssertionError("RU13 existing-candidate content wave must contain exactly 10 units")
    content_candidates = {str(row.get("semantic_candidate_ref")): str(row.get("source_semantic_ref")) for row in existing_units}
    if content_candidates != EXPECTED_CANDIDATE_SOURCES:
        raise AssertionError(f"RU13 existing-candidate content coverage drift: {content_candidates}")
    if any(row.get("proposed_semantic_id") for row in existing_units):
        raise AssertionError("existing RU13 candidate content created duplicate proposed identity")

    guards = review.get("cross_boundary_guards")
    if not isinstance(guards, list) or len(guards) < 9:
        raise AssertionError("RU13 cross-boundary guard inventory incomplete")

    serialized = json.dumps(review, ensure_ascii=False, sort_keys=True)
    if '"canonical_semantic_admissions": 1' in serialized or '"ru_proposal_admissions": 1' in serialized:
        raise AssertionError("RU13 boundary review contains semantic self-admission")

    print("RU13_EXPRESSIVE_COMPONENT_BOUNDARY_REVIEW=PASS")
    print("EXPLICIT_COMPONENTS=24")
    print("COMPONENT_CONTENT_READY=24")
    print("PROPOSED_CONTENT_READY=14")
    print("EXISTING_CANDIDATE_CONTENT_READY=10")
    print("EXISTING_CANDIDATE_SOURCE_EVIDENCE_VERIFIED=10")
    print("CANONICAL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=0")
    print("RHETORICAL_ADDRESS_DUPLICATES=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
