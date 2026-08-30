#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

REVIEW = HERE / "RU11-NARRATION-IDENTIFICATION-CONTENT-ADEQUACY-REVIEW-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
BROADER = PROGRAM / "production-learning-content/RU-PROG-11-TEXT-COHESION-WAVE-002-v0.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-11-NARRATION-IDENTIFICATION-WAVE-006-v0.1.json"

CANDIDATE = "candidate-044"
TAXONOMY = "narration_identification"
SEMANTIC = "ru-text-narration-identification"
SOURCE_LABEL = "Определение повествования"
EXPECTED_CHECK_IDS = {"p11-nar-v1", "p11-nar-v2"}


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def mentions_narration(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return "повеств" in text or "narration" in text


def main() -> int:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    broader = json.loads(BROADER.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if review.get("status") != "CENTRAL_BRAIN_RU11_NARRATION_IDENTIFICATION_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("RU11 narration content-review status drift")
    if review.get("authority_issue") != 161:
        raise AssertionError("RU11 narration authority issue drift")

    source = review.get("source_identity") or {}
    if (
        source.get("candidate_ref") != CANDIDATE
        or source.get("source_taxonomy_id") != TAXONOMY
        or source.get("label_ru") != SOURCE_LABEL
        or source.get("inventory_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE"
        or source.get("inventory_review_status") != "draft"
        or source.get("skill_graph_evidence_status") != "confirmed"
        or source.get("taxonomy_backing_review_status") != "source_verified"
        or source.get("exam_task_numbers") != [24]
    ):
        raise AssertionError("RU11 narration review source truth drift")

    modules = {str(r.get("module_id")): r for r in program.get("modules", []) if isinstance(r, dict)}
    module = modules.get("RU-PROG-11")
    if not isinstance(module, dict) or CANDIDATE not in (module.get("candidate_refs") or []):
        raise AssertionError("RU11 candidate-044 is no longer a current program candidate")

    objects = [r for r in inventory.get("objects", []) if isinstance(r, dict)]
    candidate = one([
        r for r in objects
        if r.get("source_system") == "semantic_candidate"
        and r.get("source_id") == CANDIDATE
        and r.get("authority_status") == "current"
    ], "RU11 candidate-044 current inventory")
    if (
        candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE"
        or candidate.get("candidate_canonical_owner") != CANDIDATE
        or candidate.get("current_semantic_refs") != [TAXONOMY]
        or candidate.get("review_status") != "draft"
        or candidate.get("observed_label") != SOURCE_LABEL
    ):
        raise AssertionError("RU11 candidate-044 inventory ownership/review boundary drift")

    backing = one([
        r for r in objects
        if r.get("source_system") == "ege_skill_graph"
        and r.get("source_id") == TAXONOMY
        and r.get("authority_status") == "current"
        and r.get("candidate_canonical_owner") == CANDIDATE
    ], "RU11 candidate-044 taxonomy backing")
    if backing.get("review_status") != "source_verified" or backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise AssertionError("RU11 candidate-044 taxonomy backing not source-verified")
    if normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU11 candidate-044 inventory/backing meaning mismatch")

    skill = one([
        r for r in graph.get("skills", []) if isinstance(r, dict) and r.get("skill_id") == TAXONOMY
    ], "RU11 candidate-044 graph node")
    if (
        skill.get("evidence_status") != "confirmed"
        or skill.get("parent_skill_id") != "speech_type_analysis"
        or skill.get("exam_task_numbers") != [24]
        or skill.get("name_ru") != SOURCE_LABEL
        or normalized(skill.get("description")) != normalized(candidate.get("observed_meaning"))
    ):
        raise AssertionError("RU11 candidate-044 confirmed Task-24 graph boundary drift")

    if any(
        SEMANTIC in {str(ref) for ref in (r.get("current_semantic_refs") or [])}
        for r in objects if r.get("authority_status") == "current"
    ):
        raise AssertionError("RU11 narration proposed semantic id collides with current inventory")
    if any(
        r.get("source_system") == "school_canonical"
        and r.get("authority_status") == "current"
        and normalized(r.get("observed_meaning")) == normalized(candidate.get("observed_meaning"))
        for r in objects
    ):
        raise AssertionError("RU11 candidate-044 exact school meaning already exists; reuse required")

    reuse = review.get("reuse_first_review") or {}
    if (
        reuse.get("existing_unit_reused_for_explanation_and_boundary") is not True
        or reuse.get("existing_unit_exact_candidate_044_mastery") is not False
        or reuse.get("direct_narration_independent_checks_observed") != 0
    ):
        raise AssertionError("RU11 candidate-044 reuse-first review drift")

    broad_unit = one([
        r for r in broader.get("units", [])
        if isinstance(r, dict) and r.get("proposed_semantic_id") == "ru-text-speech-type-reasoning-description-narration"
    ], "RU11 broader combined speech-type unit")
    broad_checks = [r for r in (broad_unit.get("independent_verification") or []) if isinstance(r, dict)]
    direct_narration_checks = sum(1 for row in broad_checks if mentions_narration(row))
    if direct_narration_checks != 0:
        raise AssertionError(f"RU11 narration reuse-gap proof drift: expected 0 direct checks, got {direct_narration_checks}")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-11":
        raise AssertionError("RU11 narration content status/module drift")
    provenance = content.get("source_provenance") or []
    draft_source = one([
        r for r in provenance if isinstance(r, dict) and r.get("kind") == "current_draft_subject_semantic_candidate"
    ], "RU11 narration draft source provenance")
    if draft_source.get("review_status") != "draft" or draft_source.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
        raise AssertionError("RU11 narration content falsely upgrades draft source candidate")
    confirmed = one([
        r for r in provenance if isinstance(r, dict) and r.get("kind") == "confirmed_skill_graph"
    ], "RU11 narration confirmed graph provenance")
    if confirmed.get("evidence_status") != "confirmed":
        raise AssertionError("RU11 narration graph evidence status drift")

    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes") != 0 or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU11 narration provenance/copyright boundary weakened")

    unit = one([
        r for r in content.get("units", []) if isinstance(r, dict) and r.get("proposed_semantic_id") == SEMANTIC
    ], "RU11 narration learner unit")
    if unit.get("title_ru") != "Распознавание повествования":
        raise AssertionError("RU11 narration learner title widened or drifted")
    for key, minimum in (
        ("decision_algorithm", 6),
        ("worked_examples", 4),
        ("misconceptions", 4),
        ("guided_practice", 3),
        ("independent_practice", 3),
        ("mixed_transfer_practice", 2),
        ("retention_items", 2),
        ("independent_verification", 2),
    ):
        value = unit.get(key)
        if not isinstance(value, list) or len(value) < minimum:
            raise AssertionError(f"RU11 narration learner section incomplete: {key}")

    boundaries = " ".join((unit.get("canonical_explanation") or {}).get("boundaries") or []).lower()
    for token in ("глагол", "опис", "рассуж", "№24"):
        if token not in boundaries:
            raise AssertionError(f"RU11 narration exclusion missing: {token}")

    checks = [r for r in (unit.get("independent_verification") or []) if isinstance(r, dict)]
    if {r.get("id") for r in checks} != EXPECTED_CHECK_IDS or len(checks) != 2:
        raise AssertionError("RU11 narration exact verification set drift")
    if any(r.get("type") != "constructed_response" for r in checks):
        raise AssertionError("RU11 narration verification weakened from constructed response")
    if not all(mentions_narration(r) for r in checks):
        raise AssertionError("RU11 narration exact checks no longer directly test narration")

    peis = unit.get("peis_evidence") or {}
    if (
        peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL"
        or peis.get("source_candidate_review_status") != "draft"
        or peis.get("independent_verification_required") is not True
        or peis.get("assistance_must_be_recorded") is not True
        or peis.get("exact_mastery_requires_two_component_specific_narration_checks") is not True
        or peis.get("generic_task24_result_can_emit_exact_component_mastery") is not False
        or peis.get("combined_speech_type_unit_result_can_emit_exact_component_mastery") is not False
        or peis.get("description_or_reasoning_result_can_emit_this_mastery") is not False
        or peis.get("object_closure_implied") is not False
    ):
        raise AssertionError("RU11 narration PEIS fail-closed boundary weakened")

    tutor = unit.get("tutor_grounding") or {}
    forbidden = " ".join(tutor.get("forbidden") or []).lower()
    if "verb" not in forbidden and "глаг" not in forbidden:
        raise AssertionError("RU11 narration Tutor verb-count guard missing")
    if "task-24" not in forbidden:
        raise AssertionError("RU11 narration Tutor generic Task-24 guard missing")

    rd = review.get("review_decision") or {}
    if (
        rd.get("content_exact_for_current_candidate_044_source_meaning") is not True
        or rd.get("source_candidate_inventory_status_preserved_as_draft") is not True
        or rd.get("content_duplicate_of_existing_ru11_unit") is not False
        or rd.get("exact_school_meaning_collision_observed") is not False
        or rd.get("semantic_admission_by_this_review") is not False
        or rd.get("object_level_admission_units_closed") != 0
        or rd.get("object_level_requirements_closed") != 0
        or rd.get("false_exact_mastery_admissions") != 0
        or rd.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_WITH_DRAFT_CANDIDATE_GUARD"
    ):
        raise AssertionError("RU11 narration content-review decision drift")

    digest = hashlib.sha256(json.dumps(review, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    print("RU11_NARRATION_IDENTIFICATION_CONTENT_ADEQUACY=PASS")
    print(f"SOURCE_CANDIDATE_REVIEW_STATUS={candidate.get('review_status')}")
    print(f"BROADER_DIRECT_NARRATION_CHECKS={direct_narration_checks}")
    print(f"EXACT_COMPONENT_CHECKS={len(checks)}")
    print(f"PROPOSED_SEMANTIC={SEMANTIC}")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
