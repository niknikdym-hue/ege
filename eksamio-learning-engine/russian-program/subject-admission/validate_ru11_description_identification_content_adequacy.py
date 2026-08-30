#!/usr/bin/env python3
"""Fail-closed adequacy gate for RU11 candidate-045 description-identification content."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
CONTENT_DIR = ENGINE / "russian-program" / "production-learning-content"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
SKILL_GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
BROADER = CONTENT_DIR / "RU-PROG-11-TEXT-COHESION-WAVE-002-v0.1.json"
EXACT = CONTENT_DIR / "RU-PROG-11-DESCRIPTION-IDENTIFICATION-WAVE-007-v0.1.json"
REVIEW = HERE / "RU11-DESCRIPTION-IDENTIFICATION-CONTENT-ADEQUACY-REVIEW-v0.1.json"

CANDIDATE = "candidate-045"
TAXONOMY = "description_identification"
SEMANTIC = "ru-text-description-identification"
BROADER_SEMANTIC = "ru-text-speech-type-reasoning-description-narration"
EXPECTED_EXACT_CHECK_IDS = {"p11-desc-v1", "p11-desc-v2"}
EXPECTED_BROADER_DESCRIPTION_CHECK_IDS = {"p11-u3-v2"}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_inventory_object(data: dict[str, Any], key: str) -> dict[str, Any]:
    matches = [row for row in data["objects"] if row["object_key"] == key]
    assert len(matches) == 1, (key, len(matches))
    return matches[0]


def find_skill(data: dict[str, Any], skill_id: str) -> dict[str, Any]:
    matches = [row for row in data["skills"] if row["skill_id"] == skill_id]
    assert len(matches) == 1, (skill_id, len(matches))
    return matches[0]


def find_unit(data: dict[str, Any], semantic_id: str) -> dict[str, Any]:
    matches = [row for row in data["units"] if row["proposed_semantic_id"] == semantic_id]
    assert len(matches) == 1, (semantic_id, len(matches))
    return matches[0]


def main() -> int:
    inventory = load(INVENTORY)
    graph = load(SKILL_GRAPH)
    broader = load(BROADER)
    exact = load(EXACT)
    review = load(REVIEW)

    candidate = find_inventory_object(inventory, f"semantic_candidate::{CANDIDATE}")
    taxonomy = find_inventory_object(inventory, f"ege_skill_graph::{TAXONOMY}")
    skill = find_skill(graph, TAXONOMY)
    broader_unit = find_unit(broader, BROADER_SEMANTIC)
    exact_unit = find_unit(exact, SEMANTIC)

    assert candidate["audit_classification"] == "MISSING_SUBJECT_SEMANTIC_CANDIDATE"
    assert candidate["review_status"] == "draft"
    assert candidate["current_semantic_refs"] == [TAXONOMY]
    assert taxonomy["audit_classification"] == "EGE_TAXONOMY_NODE"
    assert taxonomy["candidate_canonical_owner"] == CANDIDATE
    assert taxonomy["review_status"] == "source_verified"
    assert skill["parent_skill_id"] == "speech_type_analysis"
    assert skill["evidence_status"] == "confirmed"
    assert skill["exam_task_numbers"] == [24]

    broader_checks = broader_unit["independent_verification"]
    broader_direct_ids = {
        row["id"] for row in broader_checks if row["id"] in EXPECTED_BROADER_DESCRIPTION_CHECK_IDS
    }
    assert broader_direct_ids == EXPECTED_BROADER_DESCRIPTION_CHECK_IDS
    assert len(broader_direct_ids) == 1

    assert review["status"] == "CENTRAL_BRAIN_RU11_DESCRIPTION_IDENTIFICATION_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION"
    source = review["source_identity"]
    assert source["candidate_ref"] == CANDIDATE
    assert source["source_taxonomy_id"] == TAXONOMY
    assert source["inventory_review_status"] == "draft"
    assert source["taxonomy_backing_review_status"] == "source_verified"
    assert source["skill_graph_evidence_status"] == "confirmed"
    reuse_review = review["reuse_first_review"]
    assert reuse_review["direct_description_independent_checks_observed"] == 1
    assert reuse_review["direct_check_ids"] == ["p11-u3-v2"]
    decision = review["review_decision"]
    assert decision["content_exact_for_current_candidate_045_source_meaning"] is True
    assert decision["source_candidate_inventory_status_preserved_as_draft"] is True
    assert decision["semantic_admission_by_this_review"] is False
    assert decision["object_level_admission_units_closed"] == 0
    assert decision["object_level_requirements_closed"] == 0
    assert decision["false_exact_mastery_admissions"] == 0
    assert decision["next_status"] == "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_WITH_DRAFT_CANDIDATE_GUARD"

    assert exact["status"] == "SUBJECT_ACCEPTANCE_REQUIRED"
    assert exact["module_id"] == "RU-PROG-11"
    assert exact["identity_boundary"].startswith("The proposed ru-* semantic is not a school-* canonical identity")
    assert exact["reuse_review"]["existing_unit_reused_as_exact_candidate_045_mastery_evidence"] is False
    assert exact["reuse_review"]["broader_existing_unit_direct_description_independent_checks"] == 1
    assert exact["reuse_review"]["new_content_materialized_only_for_proven_component_verification_gap"] is True
    assert exact["copyright_guard"]["source_passages_copied"] == 0
    assert exact["copyright_guard"]["commercial_textbook_bytes"] == 0
    assert exact["copyright_guard"]["learner_examples"] == "ORIGINAL_EKSAMIO"

    required_sections = [
        "canonical_explanation",
        "decision_algorithm",
        "worked_examples",
        "misconceptions",
        "guided_practice",
        "independent_practice",
        "mixed_transfer_practice",
        "retention_items",
        "independent_verification",
        "peis_evidence",
        "tutor_grounding",
    ]
    for section in required_sections:
        assert exact_unit.get(section), section

    ids: list[str] = []
    for section in (
        "guided_practice",
        "independent_practice",
        "mixed_transfer_practice",
        "retention_items",
        "independent_verification",
    ):
        ids.extend(str(row["id"]) for row in exact_unit[section])
    assert len(ids) == len(set(ids))

    exact_checks = exact_unit["independent_verification"]
    assert {row["id"] for row in exact_checks} == EXPECTED_EXACT_CHECK_IDS
    assert all(row["type"] == "constructed_response" for row in exact_checks)
    assert all(row["scoring"]["max_points"] == 3 for row in exact_checks)
    assert all(len(row["scoring"]["criteria"]) == 3 for row in exact_checks)

    peis = exact_unit["peis_evidence"]
    assert peis["semantic_ref_status"] == "PROPOSED_NOT_CANONICAL"
    assert peis["source_candidate_review_status"] == "draft"
    assert peis["independent_verification_required"] is True
    assert peis["exact_mastery_requires_two_component_specific_description_checks"] is True
    assert peis["generic_task24_result_can_emit_exact_component_mastery"] is False
    assert peis["broader_combined_unit_can_emit_exact_description_mastery"] is False

    forbidden = "\n".join(exact_unit["tutor_grounding"]["forbidden"]).lower()
    assert "generic task-24" in forbidden
    assert "narration" in forbidden and "reasoning" in forbidden

    print("RU11_DESCRIPTION_CANDIDATE=candidate-045")
    print("RU11_DESCRIPTION_SOURCE_TAXONOMY=description_identification")
    print("RU11_DESCRIPTION_SOURCE_EVIDENCE=confirmed")
    print("RU11_DESCRIPTION_INVENTORY_REVIEW_STATUS=draft")
    print("BROADER_EXISTING_DIRECT_DESCRIPTION_CHECKS=1")
    print("EXACT_COMPONENT_CHECKS=2")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print("RU11_DESCRIPTION_CONTENT_ADEQUACY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
