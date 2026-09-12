#!/usr/bin/env python3
"""Fail-closed validator for the bounded EDSOO59 p.222 / 8.1 semantic admission.

This gate admits exactly two source-backed RU09 subject semantics.  It must not
close the source object, dispose requirements, emit mastery, mutate the
aggregate, or create current-v30.  Exact object binding remains a separate
review after this gate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ENGINE = Path(__file__).resolve().parents[2]
RUSSIAN = ENGINE / "russian-program"
SUBJECT_ADMISSION = RUSSIAN / "subject-admission"

ACCEPTANCE_PATH = SUBJECT_ADMISSION / "RU09-EDSOO59-P222-8-1-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
OWNER_PATH = SUBJECT_ADMISSION / "RU09-EDSOO59-P222-8-1-SOURCE-BACKED-OWNER-RESOLUTION-v0.1.json"
CONTENT_PATH = RUSSIAN / "production-learning-content" / "RU-PROG-09-EDSOO59-P222-8-1-WAVE-002-v0.1.json"

SOURCE_SHA256 = "1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d"
TARGET_UNIT = "RAU-3ceb45ca22608d520ddf"
TARGET_REQUIREMENT = "RSK-EDSOO59-8-1-P222"
TARGET_REVIEW = "RUS-SEM-REVIEW-048"

EXPECTED = {
    "ru-syntax-sentence-formulation-means": {
        "component_id": "edsoo59-p222-8-1-sentence-formulation-means",
        "source_text": "Средства оформления предложения в устной и письменной речи (интонация, логическое ударение, знаки препинания)",
        "evidence": {"p09-u6-v1", "p09-u6-v2", "p09-u6-v3", "p09-u6-v4"},
    },
    "ru-syntax-inversion-norm": {
        "component_id": "edsoo59-p222-8-1-inversion-norm",
        "source_text": "Нормы использования инверсии",
        "evidence": {"p09-u7-v1", "p09-u7-v2", "p09-u7-v3", "p09-u7-v4"},
    },
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    acceptance = load(ACCEPTANCE_PATH)
    owner = load(OWNER_PATH)
    content = load(CONTENT_PATH)

    require(
        acceptance["status"] == "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTICS_OBJECT_BINDING_STILL_REQUIRED",
        "semantic acceptance status must remain bounded and object-binding-pending",
    )
    target = acceptance["target_object"]
    require(target["admission_unit_id"] == TARGET_UNIT, "wrong admission unit")
    require(target["requirement_id"] == TARGET_REQUIREMENT, "wrong requirement")
    require(target["review_group_id"] == TARGET_REVIEW, "wrong review group")
    require(acceptance["official_source"]["document_sha256"] == SOURCE_SHA256, "official source SHA drift")
    require(owner["official_source"]["document_sha256"] == SOURCE_SHA256, "owner-resolution source SHA drift")
    require(owner["existing_owner_search"]["exact_current_owner_count"] == 0, "unexpected pre-existing exact owner")

    source_provenance = content["source_provenance"]
    source_rows = [row for row in source_provenance if row.get("kind") == "official_program_scope"]
    require(len(source_rows) == 1, "content must have exactly one official_program_scope row")
    require(source_rows[0]["document_sha256"] == SOURCE_SHA256, "content source SHA drift")

    upstream = acceptance["upstream_authorities"]
    source_gate = upstream["source_identity_audit"]
    require(source_gate == {
        "workflow": "Russian EDSOO59 p222 8.1 official-source identity audit",
        "run_id": 34673330234,
        "head_sha": "bbce1d9f40c01ae7aef0c23e13048233ed08765a",
        "conclusion": "SUCCESS",
    }, "source identity audit proof changed")
    content_gate = upstream["candidate_content_readiness"]
    require(content_gate == {
        "workflow": "Russian RU09 EDSOO59 p222 8.1 candidate content readiness",
        "run_id": 34679263408,
        "head_sha": "e4085a3f556abb0a077358b2e968b5b4fd320847",
        "conclusion": "SUCCESS",
    }, "candidate content readiness proof changed")

    policy = acceptance["policy"]
    require(policy["exact_source_wording_controls_semantic_identity"] is True, "exact source wording must control")
    require(policy["keyword_fuzzy_embedding_inference_allowed"] is False, "fuzzy inference must remain forbidden")
    require(policy["route_module_title_task_number_inference_allowed"] is False, "route/title inference must remain forbidden")
    require(policy["original_bounded_learner_content_required"] is True, "original learner content is required")
    require(policy["independent_component_specific_evidence_required"] is True, "component evidence is required")
    require(policy["generic_ru09_score_can_grant_semantic_admission"] is False, "generic score cannot admit semantics")
    require(policy["generic_ru09_score_can_grant_exact_mastery"] is False, "generic score cannot grant mastery")
    require(policy["registered_user_identity_ref_required_for_future_canonical_learner_evidence"] is True, "registered identity required")
    require(policy["assistance_must_be_recorded_for_future_canonical_learner_evidence"] is True, "assistance must be recorded")
    require(policy["semantic_acceptance_can_close_object"] is False, "semantic acceptance cannot close object")
    require(policy["semantic_acceptance_can_create_current_v30"] is False, "semantic acceptance cannot create current-v30")
    require(policy["semantic_acceptance_can_mutate_aggregate"] is False, "semantic acceptance cannot mutate aggregate")
    require(policy["fail_closed_if_source_content_or_evidence_identity_changes"] is True, "identity drift must fail closed")

    accepted = acceptance["accepted_semantics"]
    require(len(accepted) == 2, "exactly two semantics may be admitted")
    require({row["semantic_id"] for row in accepted} == set(EXPECTED), "semantic admission set changed")

    owner_rows = {row["proposed_semantic_id"]: row for row in owner["proposed_owners"]}
    require(set(owner_rows) == set(EXPECTED), "owner-resolution candidate set changed")
    content_rows = {row["proposed_semantic_id"]: row for row in content["units"]}
    require(set(content_rows) == set(EXPECTED), "bounded content unit set changed")

    for row in accepted:
        semantic_id = row["semantic_id"]
        expected = EXPECTED[semantic_id]
        require(row["state"] == "ADMITTED", f"{semantic_id}: state must be ADMITTED")
        require(row["source_component_id"] == expected["component_id"], f"{semantic_id}: component id drift")
        require(row["exact_source_text"] == expected["source_text"], f"{semantic_id}: exact source text drift")
        require(row["source_backed"] is True and row["content_backed"] is True and row["evidence_backed"] is True, f"{semantic_id}: backing incomplete")
        require(set(row["independent_component_evidence_ids"]) == expected["evidence"], f"{semantic_id}: evidence id set drift")
        require(row["generic_ru09_fallback"] is False, f"{semantic_id}: generic fallback forbidden")
        require(row["object_closure_effect"] == "NONE_UNTIL_SEPARATE_EXACT_OBJECT_BINDING_REVIEW", f"{semantic_id}: object closure forbidden")
        require(row["exact_mastery_effect"] == "NONE", f"{semantic_id}: exact mastery forbidden")
        require(row["registered_user_identity_ref_required_for_future_canonical_evidence"] is True, f"{semantic_id}: registered identity required")
        require(row["assistance_must_be_recorded"] is True, f"{semantic_id}: assistance record required")
        require(row["false_exact_mastery"] == 0, f"{semantic_id}: false exact mastery must remain zero")

        prior = owner_rows[semantic_id]
        require(prior["source_component_id"] == expected["component_id"], f"{semantic_id}: owner component id drift")
        require(prior["exact_source_text"] == expected["source_text"], f"{semantic_id}: owner exact source text drift")
        require(prior["status"] == "PROPOSED_NOT_CANONICAL", f"{semantic_id}: historical owner input must remain proposed")

        unit = content_rows[semantic_id]
        require(unit["source_component_id"] == expected["component_id"], f"{semantic_id}: content component id drift")
        evidence_ids = {item["id"] for item in unit["independent_verification"]}
        require(evidence_ids == expected["evidence"], f"{semantic_id}: configured independent evidence drift")
        peis = unit["peis_evidence"]
        require(peis["independent_verification_required"] is True, f"{semantic_id}: independent verification required")
        require(peis["component_specific_evidence_required"] is True, f"{semantic_id}: component evidence required")
        require(peis["assistance_must_be_recorded"] is True, f"{semantic_id}: assistance record required in content")
        require(peis["registered_user_identity_ref_required_for_future_canonical_evidence"] is True, f"{semantic_id}: registered identity required in content")
        require(peis["generic_syntax_score_can_emit_exact_mastery"] is False, f"{semantic_id}: generic syntax score cannot emit exact mastery")

    progress = acceptance["progress_effect"]
    require(progress == {
        "semantic_admissions": 2,
        "object_level_closures": 0,
        "requirement_disposals": 0,
        "mastery_admissions": 0,
        "false_exact_mastery": 0,
        "aggregate_mutated": False,
        "current_v30_created": False,
        "current_v29_remainder_units_preserved": 1270,
        "current_v29_remainder_requirements_preserved": 1345,
    }, "progress effect must be semantic-only")

    require(acceptance["next_required_state"] == "SEMANTIC_CANDIDATES_ACCEPTED_OBJECT_BINDING_STILL_REQUIRED", "wrong next state")
    next_gate = acceptance["next_required_gate"]
    require(next_gate["kind"] == "SEPARATE_EXACT_OBJECT_BINDING_REVIEW", "object binding must remain separate")
    require(next_gate["admission_unit_id"] == TARGET_UNIT, "next gate unit drift")
    require(next_gate["requirement_id"] == TARGET_REQUIREMENT, "next gate requirement drift")
    require(set(next_gate["must_bind_exact_component_set"]) == set(EXPECTED), "next gate component set drift")
    require(next_gate["aggregate_or_current_v30_allowed_before_gate_green"] is False, "aggregate/current-v30 must remain blocked")

    v30_paths = [
        path
        for path in RUSSIAN.rglob("*")
        if path.is_file() and "current" in path.name.casefold() and "v30" in path.name.casefold()
    ]
    require(not v30_paths, f"current-v30 appeared before object binding: {v30_paths}")

    print("SEMANTIC_ADMISSIONS=2")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("REQUIREMENT_DISPOSALS=0")
    print("MASTERY_ADMISSIONS=0")
    print("FALSE_EXACT_MASTERY=0")
    print("AGGREGATE_MUTATED=0")
    print("CURRENT_V30_CREATED=0")
    print("NEXT=SEPARATE_EXACT_OBJECT_BINDING_REVIEW")


if __name__ == "__main__":
    main()
