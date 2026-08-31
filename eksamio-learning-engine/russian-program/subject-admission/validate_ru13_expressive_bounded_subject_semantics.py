#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ACCEPTANCE = HERE / "RU13-EXPRESSIVE-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
BOUNDARY = HERE / "RU13-EXPRESSIVE-COMPONENT-BOUNDARY-REVIEW-v0.1.json"
REVIEWED_SETS = HERE / "RUSSIAN-SUBJECT-REVIEWED-SETS-v0.1.json"
WAVES = [
    PROGRAM / "production-learning-content/RU-PROG-13-EXPRESSIVE-MEANS-WAVE-001-v0.1.json",
    PROGRAM / "production-learning-content/RU-PROG-13-EXPRESSIVE-MEANS-WAVE-002-v0.1.json",
]

EXPECTED_IDS = {
    "ru-expressive-alliteration", "ru-expressive-personification",
    "ru-expressive-syntactic-parallelism", "ru-expressive-question-answer-form",
    "ru-expressive-gradation", "ru-expressive-inversion",
    "ru-expressive-lexical-repetition", "ru-expressive-epiphora",
    "ru-expressive-antithesis", "ru-expressive-rhetorical-question",
    "ru-expressive-rhetorical-exclamation", "ru-expressive-polysyndeton",
    "ru-expressive-asyndeton", "ru-expressive-litotes",
}
EXPECTED_REQUIREMENTS = {
    "RSK-EDSOO59-8-1-P201", "RSK-OGE_COD-1-1-2-P002",
    "RSK-EDSOO59-8-1-P227", "RSK-EDSOO59-8-1-P231",
    "RSK-EGE_COD-3-12-P004", "RSK-EGE_COD-1-1-1-P002",
}
EXPECTED_UNITS = {
    "RAU-170745c79503b789e72b", "RAU-359cfc7d0ad59a2f6e95",
    "RAU-6a7b2dccf1d2430a2777", "RAU-b5712ae284c6178d10fd",
    "RAU-f8b3979c6b1889dbb949",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    reviewed = json.loads(REVIEWED_SETS.read_text(encoding="utf-8"))
    waves = [json.loads(path.read_text(encoding="utf-8")) for path in WAVES]

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU13_EXPRESSIVE_BOUNDED_SUBJECT_SEMANTICS":
        raise AssertionError("RU13 first-wave acceptance status drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU13 first-wave acceptance must remain an overlay")
    expected_summary = {
        "accepted_bounded_subject_semantics": 14,
        "accepted_ru_subject_semantics": 14,
        "existing_candidates_admitted_by_this_authority": 0,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }
    if acceptance.get("summary") != expected_summary:
        raise AssertionError("RU13 first-wave acceptance summary drift")

    authority = acceptance.get("authority") or {}
    if set(authority.get("tier_a_exact_requirement_ids") or []) != EXPECTED_REQUIREMENTS:
        raise AssertionError("RU13 Tier-A requirement set drift")
    if set(authority.get("tier_a_exact_admission_unit_ids") or []) != EXPECTED_UNITS:
        raise AssertionError("RU13 Tier-A admission-unit set drift")
    if authority.get("ege_route_scope") != "FIPI-EGE-2026-TASK-CODE-RELATION-v1.0.json#task=22 requirement_code=3.12":
        raise AssertionError("RU13 EGE task-22 route scope drift")

    matches = [
        row for row in (reviewed.get("reviewed_sets") or [])
        if isinstance(row, dict) and row.get("set_id") == "CB-RU13-EXPRESSIVE-BROAD-DOMAIN-001"
    ]
    if len(matches) != 1:
        raise AssertionError("RU13 broad-domain reviewed set missing")
    broad = matches[0]
    if broad.get("disposition") != "PARTIAL_OR_COMPOSITE" or broad.get("subject_review_status") != "CENTRAL_BRAIN_ACCEPTED_CLASSIFICATION":
        raise AssertionError("RU13 broad-domain classification weakened")
    mastery = broad.get("mastery_boundary") or {}
    if mastery.get("generic_domain_attempt_can_emit_exact_component_mastery") is not False:
        raise AssertionError("RU13 generic broad attempt can emit exact mastery")
    if mastery.get("component_mastery_requires_component_specific_independent_evidence") is not True:
        raise AssertionError("RU13 component-specific evidence guard missing")

    # The first-wave gate protects only these 14 decisions. The boundary may
    # legitimately show the other 10 source-verified candidates as accepted by
    # their separate authority; this validator must not veto that later closure.
    if boundary.get("status") not in {
        "CENTRAL_BRAIN_COMPONENT_BOUNDARY_REVIEW_PARTIAL_WITH_14_BOUNDED_SEMANTICS_ACCEPTED",
        "CENTRAL_BRAIN_COMPONENT_BOUNDARY_REVIEW_24_OF_24_BOUNDED_SEMANTICS_ACCEPTED",
    }:
        raise AssertionError("RU13 component boundary status drift")
    proposed = boundary.get("proposed_content_components") or []
    if len(proposed) != 14:
        raise AssertionError("RU13 first-wave boundary must contain 14 proposed components")
    boundary_by_id = {str(row.get("semantic_id")): row for row in proposed if isinstance(row, dict)}
    if set(boundary_by_id) != EXPECTED_IDS:
        raise AssertionError("RU13 first-wave boundary identity set drift")

    decisions = acceptance.get("decisions") or []
    if len(decisions) != 14:
        raise AssertionError("RU13 first-wave authority must contain exactly 14 decisions")
    decision_by_id = {str(row.get("accepted_semantic_id")): row for row in decisions if isinstance(row, dict)}
    if set(decision_by_id) != EXPECTED_IDS or "ru-expressive-rhetorical-address" in decision_by_id:
        raise AssertionError("RU13 first-wave accepted semantic set drift")

    content_units: dict[str, dict[str, Any]] = {}
    for wave in waves:
        if wave.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or wave.get("module_id") != "RU-PROG-13":
            raise AssertionError("RU13 source content weakened/self-admitted")
        if (wave.get("authority") or {}).get("admission_unit_binding") != "PENDING_EXACT_OBJECT_LEVEL_DISPOSITION":
            raise AssertionError("RU13 source content claimed object-level binding")
        for unit in wave.get("units") or []:
            if isinstance(unit, dict) and unit.get("proposed_semantic_id"):
                sid = str(unit["proposed_semantic_id"])
                if sid in content_units:
                    raise AssertionError(f"duplicate RU13 first-wave content unit: {sid}")
                content_units[sid] = unit
    if set(content_units) != EXPECTED_IDS:
        raise AssertionError("RU13 first-wave content waves do not exactly cover accepted semantics")

    for sid in sorted(EXPECTED_IDS):
        decision = decision_by_id[sid]
        boundary_row = boundary_by_id[sid]
        unit = content_units[sid]
        if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
            raise AssertionError(f"RU13 semantic not explicitly accepted: {sid}")
        if boundary_row.get("status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
            raise AssertionError(f"RU13 boundary lost first-wave acceptance: {sid}")
        if decision.get("boundary_guard") != boundary_row.get("boundary_guard"):
            raise AssertionError(f"RU13 boundary guard mismatch: {sid}")
        peis = unit.get("peis_evidence") or {}
        if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL" or peis.get("independent_verification_required") is not True:
            raise AssertionError(f"RU13 learner evidence guard weakened: {sid}")
        verification = unit.get("independent_verification")
        if not isinstance(verification, list) or len(verification) < 2:
            raise AssertionError(f"RU13 independent verification missing: {sid}")

    policies = acceptance.get("policy") or {}
    if policies.get("subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding") is not False:
        raise AssertionError("RU13 first-wave acceptance can falsely reduce object counts")
    if policies.get("generic_expressive_attempt_can_emit_exact_component_mastery") is not False:
        raise AssertionError("RU13 first-wave acceptance can falsely exact-master a broad attempt")

    serialized = canonical_bytes(acceptance)
    if b'"object_level_admission_units_closed":1' in serialized or b'"object_level_requirements_closed":1' in serialized:
        raise AssertionError("RU13 first-wave acceptance falsely closes object accounting")

    print("RU13_EXPRESSIVE_BOUNDED_SUBJECT_SEMANTICS=PASS")
    print("ACCEPTED_BOUNDED_SUBJECT_SEMANTICS=14")
    print("LATER_EXISTING_CANDIDATE_ACCEPTANCE_COMPATIBLE=PASS")
    print("OBJECT_LEVEL_ADMISSION_UNITS_CLOSED=0")
    print("OBJECT_LEVEL_REQUIREMENTS_CLOSED=0")
    print("RHETORICAL_ADDRESS_DUPLICATE=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("ACCEPTANCE_SHA256=" + hashlib.sha256(canonical_bytes(acceptance)).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
