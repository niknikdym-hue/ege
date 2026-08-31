#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

ACCEPTANCE = HERE / "RU11-REASONING-IDENTIFICATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
BROADER_CONTENT = PROGRAM / "production-learning-content/RU-PROG-11-TEXT-COHESION-WAVE-002-v0.1.json"
EXACT_CONTENT = PROGRAM / "production-learning-content/RU-PROG-11-REASONING-IDENTIFICATION-WAVE-004-v0.1.json"

CANDIDATE = "candidate-046"
TAXONOMY = "reasoning_identification"
SEMANTIC = "ru-text-reasoning-identification"
LABEL = "Распознавание рассуждения"
BROADER_SEMANTIC = "ru-text-speech-type-reasoning-description-narration"
EXPECTED_CANDIDATES = {
    "candidate-001", "candidate-002", "candidate-003", "candidate-004", "candidate-005",
    "candidate-006", "candidate-007", "candidate-043", "candidate-044", "candidate-045",
    "candidate-046", "candidate-047",
}
ADJACENT = sorted(EXPECTED_CANDIDATES - {CANDIDATE})


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], message: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{message}: expected 1, got {len(rows)}")
    return rows[0]


def exact_reasoning_check(item: dict[str, Any]) -> bool:
    text = json.dumps(item, ensure_ascii=False).lower()
    has_target = "рассуждени" in text
    has_logic = any(token in text for token in ("тезис", "обосн", "основан", "причин", "вывод", "доказ"))
    has_verdict = any(token in text for token in ("определи", "является", "вердикт", "какой тип", "можно ли"))
    return has_target and has_logic and has_verdict


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    broader = json.loads(BROADER_CONTENT.read_text(encoding="utf-8"))
    content = json.loads(EXACT_CONTENT.read_text(encoding="utf-8"))

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU11_REASONING_IDENTIFICATION_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU11 candidate-046 acceptance status drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU11 candidate-046 acceptance mutated/duplicated registry")

    policy = acceptance.get("policy") or {}
    for key in (
        "exact_current_source_identity_required",
        "confirmed_skill_graph_evidence_required",
        "current_missing_subject_candidate_required",
        "exact_school_meaning_collision_forbidden",
        "reuse_first",
        "component_specific_independent_evidence_required",
        "school_duplicate_forbidden",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"RU11 candidate-046 acceptance policy weakened: {key}")
    if policy.get("minimum_component_specific_independent_checks") != 2:
        raise AssertionError("RU11 candidate-046 minimum independent checks drift")
    for key in (
        "ege_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
        "adjacent_candidates_admitted",
        "narration_mastery_admitted_by_this_authority",
        "description_mastery_admitted_by_this_authority",
        "semantic_relation_mastery_admitted_by_this_authority",
        "generic_task24_result_can_emit_exact_component_mastery",
        "combined_speech_type_result_can_emit_exact_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "content_presence_alone_is_semantic_admission",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"RU11 candidate-046 fail-closed policy drift: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU11 candidate-046 namespace drift")

    modules = {str(row.get("module_id")): row for row in program.get("modules", []) if isinstance(row, dict)}
    module = modules.get("RU-PROG-11")
    if not isinstance(module, dict):
        raise AssertionError("RU11 missing from current full-subject program")
    if module.get("semantic_binding_mode") != "DRAFT_CANDIDATE_BINDING":
        raise AssertionError("RU11 binding-mode drift")
    if set(module.get("candidate_refs") or []) != EXPECTED_CANDIDATES:
        raise AssertionError("RU11 candidate-set drift")

    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    candidate = one([
        row for row in objects
        if row.get("source_system") == "semantic_candidate"
        and row.get("source_id") == CANDIDATE
        and row.get("authority_status") == "current"
    ], "RU11 candidate-046 current inventory")
    if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE" or candidate.get("candidate_canonical_owner") != CANDIDATE:
        raise AssertionError("RU11 candidate-046 inventory ownership/classification drift")
    if candidate.get("current_semantic_refs") != [TAXONOMY]:
        raise AssertionError("RU11 candidate-046 taxonomy ref drift")
    if normalized(candidate.get("observed_meaning")) != LABEL:
        raise AssertionError("RU11 candidate-046 meaning drift")

    backing = one([
        row for row in objects
        if row.get("source_system") == "ege_skill_graph"
        and row.get("source_id") == TAXONOMY
        and row.get("authority_status") == "current"
        and row.get("candidate_canonical_owner") == CANDIDATE
    ], "RU11 candidate-046 taxonomy backing")
    if backing.get("review_status") != "source_verified" or backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise AssertionError("RU11 candidate-046 taxonomy backing not source-verified")
    if normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU11 candidate/backing meaning mismatch")

    skill = one([
        row for row in graph.get("skills", [])
        if isinstance(row, dict) and row.get("skill_id") == TAXONOMY
    ], "RU11 candidate-046 graph node")
    if skill.get("evidence_status") != "confirmed" or skill.get("parent_skill_id") != "speech_type_analysis" or skill.get("exam_task_numbers") != [24]:
        raise AssertionError("RU11 candidate-046 confirmed graph boundary drift")
    if skill.get("name_ru") != LABEL or normalized(skill.get("description")) != LABEL:
        raise AssertionError("RU11 candidate-046 graph label/description drift")

    collisions = [
        row for row in objects
        if row.get("authority_status") == "current"
        and SEMANTIC in {str(ref) for ref in (row.get("current_semantic_refs") or [])}
    ]
    if collisions:
        raise AssertionError("RU11 candidate-046 semantic id collides with current inventory")
    exact_school_meaning = [
        row for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and normalized(row.get("observed_meaning")) == LABEL
    ]
    if exact_school_meaning:
        raise AssertionError("RU11 candidate-046 exact school meaning already exists; reuse required")

    if broader.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or broader.get("module_id") != "RU-PROG-11":
        raise AssertionError("RU11 broader-content authority drift")
    broader_unit = one([
        row for row in broader.get("units", [])
        if isinstance(row, dict) and row.get("proposed_semantic_id") == BROADER_SEMANTIC
    ], "RU11 broader speech-type unit")
    broader_checks = [
        row for row in broader_unit.get("independent_verification", [])
        if isinstance(row, dict) and exact_reasoning_check(row)
    ]
    if len(broader_checks) != 1:
        raise AssertionError(f"RU11 reuse-gap proof drift: expected exactly 1 direct reasoning check, got {len(broader_checks)}")

    reuse = acceptance.get("reuse_first_decision") or {}
    if reuse.get("broader_existing_unit_present") is not True or reuse.get("broader_existing_unit_reused_as_scope_and_explanation_evidence") is not True:
        raise AssertionError("RU11 candidate-046 broader-unit reuse evidence drift")
    if reuse.get("broader_existing_unit_is_exact_candidate_046_mastery_evidence") is not False:
        raise AssertionError("RU11 candidate-046 broader combined unit incorrectly treated as exact mastery")
    if reuse.get("broader_existing_unit_direct_reasoning_independent_checks") != 1 or reuse.get("minimum_component_specific_independent_checks_for_this_acceptance") != 2:
        raise AssertionError("RU11 candidate-046 reuse-gap counts drift")
    if reuse.get("new_content_materialized_only_for_proven_component_verification_gap") is not True:
        raise AssertionError("RU11 candidate-046 content-gap materialization boundary drift")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-11":
        raise AssertionError("RU11 candidate-046 learner-content status/module drift")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes") != 0 or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU11 candidate-046 learner-content provenance boundary weakened")
    reuse_content = content.get("reuse_review") or {}
    if reuse_content.get("existing_unit_reused_as_scope_and_explanation_evidence") is not True:
        raise AssertionError("RU11 candidate-046 exact unit stopped reuse-first behavior")
    if reuse_content.get("existing_unit_reused_as_exact_candidate_046_mastery_evidence") is not False:
        raise AssertionError("RU11 candidate-046 exact unit incorrectly inherits broader mastery")
    if reuse_content.get("new_content_materialized_only_for_proven_component_verification_gap") is not True:
        raise AssertionError("RU11 candidate-046 exact content gap proof drift")

    unit = one([
        row for row in content.get("units", [])
        if isinstance(row, dict) and row.get("proposed_semantic_id") == SEMANTIC
    ], "RU11 candidate-046 exact learner unit")
    if unit.get("title_ru") != LABEL:
        raise AssertionError("RU11 candidate-046 learner-unit title drift")
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
            raise AssertionError(f"RU11 candidate-046 learner section incomplete: {key}")
    verification = [row for row in unit.get("independent_verification", []) if isinstance(row, dict)]
    exact_checks = [row for row in verification if exact_reasoning_check(row)]
    if len(exact_checks) < 2:
        raise AssertionError("RU11 candidate-046 exact independent verification must test reasoning identification twice")
    if any((row.get("scoring") or {}).get("max_points") != 3 for row in exact_checks):
        raise AssertionError("RU11 candidate-046 exact independent verification scoring drift")

    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL" or peis.get("independent_verification_required") is not True or peis.get("assistance_must_be_recorded") is not True:
        raise AssertionError("RU11 candidate-046 PEIS evidence boundary weakened")
    if peis.get("exact_mastery_requires_two_component_specific_reasoning_checks") is not True:
        raise AssertionError("RU11 candidate-046 exact mastery requirement drift")
    if peis.get("generic_task24_result_can_emit_exact_component_mastery") is not False or peis.get("combined_speech_type_unit_result_can_emit_exact_component_mastery") is not False or peis.get("narration_or_description_result_can_emit_this_mastery") is not False:
        raise AssertionError("RU11 candidate-046 PEIS mastery leak")
    tutor = unit.get("tutor_grounding") or {}
    if not tutor.get("allowed") or not tutor.get("forbidden"):
        raise AssertionError("RU11 candidate-046 Tutor grounding missing")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("RU11 candidate-046 acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("candidate_ref") != CANDIDATE or decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("RU11 candidate-046 acceptance crosswalk drift")
    if decision.get("canonical_label_ru") != LABEL:
        raise AssertionError("RU11 candidate-046 acceptance label drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC" or decision.get("source_evidence_status") != "confirmed":
        raise AssertionError("RU11 candidate-046 acceptance status/evidence drift")
    if decision.get("excluded_adjacent_candidate_refs") != ADJACENT:
        raise AssertionError("RU11 candidate-046 adjacent exclusion drift")
    if decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("RU11 candidate-046 object-binding boundary drift")

    summary = acceptance.get("summary") or {}
    if summary.get("accepted_bounded_subject_semantics") != 1 or summary.get("accepted_ru_subject_semantics") != 1:
        raise AssertionError("RU11 candidate-046 accepted semantic count drift")
    if summary.get("adjacent_candidates_admitted") != 0 or summary.get("new_school_canonical_identities") != 0:
        raise AssertionError("RU11 candidate-046 acceptance leaked adjacent/parallel identities")
    if summary.get("object_level_admission_units_closed") != 0 or summary.get("object_level_requirements_closed") != 0 or summary.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("RU11 candidate-046 acceptance falsely closes object mastery")

    digest = hashlib.sha256(json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    print("RU11_REASONING_IDENTIFICATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print("BROADER_EXISTING_DIRECT_REASONING_CHECKS=1")
    print("EXACT_COMPONENT_CHECKS=2")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
