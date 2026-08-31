#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

ACCEPTANCE = HERE / "RU12-GENRE-ADDRESS-PURPOSE-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
RELATED_CONTENT = PROGRAM / "production-learning-content/RU-PROG-12-STYLES-GENRES-WAVE-002-v0.1.json"
EXACT_CONTENT = PROGRAM / "production-learning-content/RU-PROG-12-GENRE-ADDRESS-PURPOSE-WAVE-003-v0.1.json"

CANDIDATE = "candidate-017"
ADJACENT = "candidate-016"
TAXONOMY = "genre_and_communicative_purpose"
SEMANTIC = "ru-text-genre-address-purpose-identification"
LABEL = "Определение жанра, адресата и коммуникативной цели текста"


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], message: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{message}: expected 1, got {len(rows)}")
    return rows[0]


def verification_covers_three_dimensions(item: dict[str, Any]) -> bool:
    text = json.dumps(item, ensure_ascii=False).lower()
    return "жанр" in text and "адресат" in text and "цел" in text


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    related = json.loads(RELATED_CONTENT.read_text(encoding="utf-8"))
    content = json.loads(EXACT_CONTENT.read_text(encoding="utf-8"))

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU12_GENRE_ADDRESS_PURPOSE_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU12 candidate-017 acceptance status drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU12 acceptance mutated/duplicated registry")

    policy = acceptance.get("policy") or {}
    for key in (
        "exact_current_source_identity_required",
        "confirmed_skill_graph_evidence_required",
        "current_missing_subject_candidate_required",
        "exact_school_meaning_collision_forbidden",
        "original_exact_learner_content_required",
        "school_duplicate_forbidden",
        "component_specific_independent_evidence_required",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"RU12 acceptance policy weakened: {key}")
    for key in (
        "ege_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
        "adjacent_candidates_admitted",
        "functional_style_identification_admitted_by_this_authority",
        "genre_production_mastery_admitted_by_recognition_evidence",
        "generic_task3_result_can_emit_exact_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "content_presence_alone_is_semantic_admission",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"RU12 fail-closed policy drift: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU12 namespace drift")

    modules = {str(row.get("module_id")): row for row in program.get("modules", []) if isinstance(row, dict)}
    module = modules.get("RU-PROG-12")
    if not isinstance(module, dict):
        raise AssertionError("RU12 missing from current full-subject program")
    if module.get("semantic_binding_mode") != "DRAFT_CANDIDATE_BINDING":
        raise AssertionError("RU12 binding-mode drift")
    if set(module.get("candidate_refs") or []) != {CANDIDATE, ADJACENT}:
        raise AssertionError("RU12 candidate set drift")

    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    candidate = one([
        row for row in objects
        if row.get("source_system") == "semantic_candidate"
        and row.get("source_id") == CANDIDATE
        and row.get("authority_status") == "current"
    ], "RU12 candidate-017 current inventory")
    if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE" or candidate.get("candidate_canonical_owner") != CANDIDATE:
        raise AssertionError("RU12 candidate-017 inventory ownership/classification drift")
    if candidate.get("current_semantic_refs") != [TAXONOMY]:
        raise AssertionError("RU12 candidate-017 taxonomy ref drift")
    if normalized(candidate.get("observed_meaning")) != LABEL:
        raise AssertionError("RU12 candidate-017 meaning drift")

    backing = one([
        row for row in objects
        if row.get("source_system") == "ege_skill_graph"
        and row.get("source_id") == TAXONOMY
        and row.get("authority_status") == "current"
        and row.get("candidate_canonical_owner") == CANDIDATE
    ], "RU12 candidate-017 taxonomy backing")
    if backing.get("review_status") != "source_verified" or backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise AssertionError("RU12 candidate-017 taxonomy backing not source-verified")
    if normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU12 candidate/inventory backing meaning mismatch")

    skill = one([row for row in graph.get("skills", []) if isinstance(row, dict) and row.get("skill_id") == TAXONOMY], "RU12 graph node")
    if skill.get("evidence_status") != "confirmed" or skill.get("parent_skill_id") != "text_style_analysis" or skill.get("exam_task_numbers") != [3]:
        raise AssertionError("RU12 candidate-017 confirmed graph boundary drift")
    if skill.get("name_ru") != LABEL or normalized(skill.get("description")) != LABEL:
        raise AssertionError("RU12 graph label/description drift")

    collisions = [
        row for row in objects
        if row.get("authority_status") == "current"
        and SEMANTIC in {str(ref) for ref in (row.get("current_semantic_refs") or [])}
    ]
    if collisions:
        raise AssertionError("RU12 accepted semantic id collides with current inventory")
    exact_school_meaning = [
        row for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and normalized(row.get("observed_meaning")) == LABEL
    ]
    if exact_school_meaning:
        raise AssertionError("RU12 candidate-017 exact school meaning already exists; reuse required")

    if related.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or related.get("module_id") != "RU-PROG-12":
        raise AssertionError("RU12 related-content authority drift")
    related_unit = one([
        row for row in related.get("units", [])
        if isinstance(row, dict) and row.get("proposed_semantic_id") == "ru-genre-goal-structure"
    ], "RU12 related existing genre unit")
    related_verification = [row for row in related_unit.get("independent_verification", []) if isinstance(row, dict)]
    if any(verification_covers_three_dimensions(row) for row in related_verification):
        raise AssertionError("RU12 reuse-gap proof is stale: related content now has exact candidate-017 verification")
    reuse = acceptance.get("reuse_first_decision") or {}
    if reuse.get("related_existing_unit_present") is not True or reuse.get("related_existing_unit_is_exact_candidate_017_mastery_evidence") is not False or reuse.get("new_content_materialized_only_for_proven_gap") is not True:
        raise AssertionError("RU12 reuse-first decision drift")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-12":
        raise AssertionError("RU12 exact learner content status/module drift")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes") != 0 or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU12 learner-content provenance boundary weakened")
    reuse_content = content.get("reuse_review") or {}
    if reuse_content.get("existing_related_content_reused_as_exact_mastery_evidence") is not False:
        raise AssertionError("RU12 new content incorrectly treats related content as exact mastery evidence")
    unit = one([
        row for row in content.get("units", [])
        if isinstance(row, dict) and row.get("proposed_semantic_id") == SEMANTIC
    ], "RU12 exact learner unit")
    if unit.get("title_ru") != LABEL:
        raise AssertionError("RU12 learner-unit title is not exact candidate meaning")
    for key, minimum in (
        ("decision_algorithm", 6),
        ("worked_examples", 3),
        ("misconceptions", 3),
        ("guided_practice", 2),
        ("independent_practice", 3),
        ("mixed_transfer_practice", 1),
        ("retention_items", 2),
        ("independent_verification", 2),
    ):
        value = unit.get(key)
        if not isinstance(value, list) or len(value) < minimum:
            raise AssertionError(f"RU12 learner section incomplete: {key}")
    verification = [row for row in unit.get("independent_verification", []) if isinstance(row, dict)]
    if len([row for row in verification if verification_covers_three_dimensions(row)]) < 2:
        raise AssertionError("RU12 exact independent verification does not require genre+addressee+purpose twice")
    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL" or peis.get("independent_verification_required") is not True or peis.get("assistance_must_be_recorded") is not True:
        raise AssertionError("RU12 PEIS evidence boundary weakened")
    if set(peis.get("exact_mastery_requires_all_three_dimensions") or []) != {"genre", "addressee", "communicative_purpose"}:
        raise AssertionError("RU12 exact-mastery dimensions drift")
    if peis.get("generic_task3_result_can_emit_exact_component_mastery") is not False:
        raise AssertionError("RU12 generic Task-3 mastery leak")
    tutor = unit.get("tutor_grounding") or {}
    if not tutor.get("allowed") or not tutor.get("forbidden"):
        raise AssertionError("RU12 Tutor grounding missing")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("RU12 acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("candidate_ref") != CANDIDATE or decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("RU12 acceptance crosswalk drift")
    if decision.get("canonical_label_ru") != LABEL:
        raise AssertionError("RU12 acceptance label drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC" or decision.get("source_evidence_status") != "confirmed":
        raise AssertionError("RU12 acceptance status/evidence drift")
    if decision.get("excluded_adjacent_candidate_refs") != [ADJACENT]:
        raise AssertionError("RU12 adjacent candidate exclusion drift")
    if decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("RU12 object-binding boundary drift")

    summary = acceptance.get("summary") or {}
    if summary.get("accepted_bounded_subject_semantics") != 1 or summary.get("accepted_ru_subject_semantics") != 1:
        raise AssertionError("RU12 accepted semantic count drift")
    if summary.get("adjacent_candidates_admitted") != 0 or summary.get("new_school_canonical_identities") != 0:
        raise AssertionError("RU12 acceptance leaked adjacent/parallel identities")
    if summary.get("object_level_admission_units_closed") != 0 or summary.get("object_level_requirements_closed") != 0 or summary.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("RU12 acceptance falsely closes object mastery")

    digest = hashlib.sha256(json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    print("RU12_GENRE_ADDRESS_PURPOSE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print("RELATED_EXISTING_EXACT_VERIFICATION=0")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
