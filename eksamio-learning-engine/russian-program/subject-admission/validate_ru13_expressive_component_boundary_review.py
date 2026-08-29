#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
REVIEW = HERE / "RU13-EXPRESSIVE-COMPONENT-BOUNDARY-REVIEW-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
WAVES = (
    PROGRAM / "production-learning-content" / "RU-PROG-13-EXPRESSIVE-MEANS-WAVE-001-v0.1.json",
    PROGRAM / "production-learning-content" / "RU-PROG-13-EXPRESSIVE-MEANS-WAVE-002-v0.1.json",
)

EXPECTED_CANDIDATES = {f"candidate-{number:03d}" for number in range(33, 43)}
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
    summary = review.get("summary", {})
    if summary != {
        "explicit_components": 24,
        "boundary_ready_proposed_components": 14,
        "existing_candidates_requiring_exact_boundary_evidence": 10,
        "canonical_semantic_admissions": 0,
        "ru_proposal_admissions": 0,
    }:
        raise AssertionError(f"RU13 component review summary drift: {summary}")
    if review.get("status") != "CENTRAL_BRAIN_COMPONENT_BOUNDARY_REVIEW_PARTIAL":
        raise AssertionError("RU13 component review status drift")
    if review.get("admission_effect") != "NONE_UNTIL_EXPLICIT_CANONICAL_SEMANTIC_ACCEPTANCE":
        raise AssertionError("RU13 boundary review admission effect weakened")

    policy = review.get("policy", {})
    if policy.get("reuse_existing_semantics_first") is not True:
        raise AssertionError("RU13 review reuse-first policy weakened")
    if policy.get("content_presence_implies_admission") is not False:
        raise AssertionError("RU13 content presence was allowed to imply admission")
    if policy.get("candidate_presence_implies_admission") is not False:
        raise AssertionError("RU13 candidate presence was allowed to imply admission")
    if policy.get("generic_expressive_attempt_can_emit_component_mastery") is not False:
        raise AssertionError("generic expressive evidence may emit false component mastery")
    if policy.get("component_specific_independent_evidence_required") is not True:
        raise AssertionError("component-specific independent evidence guard weakened")
    if policy.get("rhetorical_address_duplicate_forbidden") is not True:
        raise AssertionError("rhetorical-address duplicate guard weakened")

    existing = review.get("existing_candidate_components")
    proposed = review.get("proposed_content_components")
    if not isinstance(existing, list) or not isinstance(proposed, list):
        raise AssertionError("RU13 component arrays are invalid")
    if {str(row.get("ref")) for row in existing} != EXPECTED_CANDIDATES:
        raise AssertionError("RU13 existing candidate set drift")
    proposed_ids = {str(row.get("semantic_id")) for row in proposed}
    if proposed_ids != EXPECTED_PROPOSED:
        raise AssertionError("RU13 proposed content semantic set drift")
    if len({str(row.get("semantic_id")) for row in existing} | proposed_ids) != 24:
        raise AssertionError("RU13 component semantic ids overlap")

    for row in existing:
        if row.get("status") != "EXACT_BOUNDARY_EVIDENCE_REQUIRED_NOT_ADMITTED":
            raise AssertionError("existing RU13 candidate was silently admitted/boundary-accepted")
        if not str(row.get("semantic_id", "")).startswith("ru-expressive-"):
            raise AssertionError("existing RU13 candidate semantic id drift")
    address = next(row for row in existing if row.get("ref") == "candidate-039")
    if address.get("special_guard") != "OWNS_RHETORICAL_ADDRESS_BOUNDARY_NO_DUPLICATE_ID":
        raise AssertionError("candidate-039 rhetorical-address ownership guard drift")

    for row in proposed:
        if row.get("status") != "DEFINITION_BOUNDARY_READY_FOR_SUBJECT_ACCEPTANCE_NOT_CANONICAL":
            raise AssertionError("RU13 proposed semantic was silently canonicalized")
        guard = str(row.get("boundary_guard", "")).strip()
        if len(guard) < 20:
            raise AssertionError(f"RU13 proposed semantic lacks bounded scope: {row.get('semantic_id')}")

    inventory_text = INVENTORY.read_text(encoding="utf-8")
    for row in existing:
        if str(row["ref"]) not in inventory_text or str(row["semantic_id"]) not in inventory_text:
            raise AssertionError(f"existing RU13 candidate evidence missing from inventory: {row['ref']}")
    if "candidate-039" not in inventory_text or "ru-expressive-address" not in inventory_text:
        raise AssertionError("existing address semantic evidence missing")

    wave_texts = [path.read_text(encoding="utf-8") for path in WAVES]
    for semantic_id in EXPECTED_PROPOSED:
        locations = sum(semantic_id in text for text in wave_texts)
        if locations != 1:
            raise AssertionError(f"proposed RU13 semantic must belong to exactly one content wave: {semantic_id}")
    if any("ru-expressive-rhetorical-address" in text for text in wave_texts):
        raise AssertionError("duplicate rhetorical-address semantic was materialized")

    guards = review.get("cross_boundary_guards")
    if not isinstance(guards, list) or len(guards) != 6:
        raise AssertionError("RU13 cross-boundary guard inventory drift")

    serialized = json.dumps(review, ensure_ascii=False, sort_keys=True)
    forbidden_acceptance = (
        '"canonical_semantic_admissions": 1',
        '"ru_proposal_admissions": 1',
        '"status": "CANONICAL"',
    )
    if any(marker in serialized for marker in forbidden_acceptance):
        raise AssertionError("RU13 boundary review contains semantic self-admission")

    print("RU13_EXPRESSIVE_COMPONENT_BOUNDARY_REVIEW=PASS")
    print("EXPLICIT_COMPONENTS=24")
    print("PROPOSED_DEFINITION_BOUNDARIES_READY=14")
    print("EXISTING_CANDIDATE_BOUNDARIES_NEED_EXACT_EVIDENCE=10")
    print("CANONICAL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=0")
    print("RHETORICAL_ADDRESS_DUPLICATES=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
