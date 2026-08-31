#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

ACCEPTANCE = HERE / "RU11-PRITYAZHATELNOE-PRONOUN-COHESION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
BROADER = PROGRAM / "production-learning-content/RU-PROG-11-TEXT-COHESION-WAVE-002-v0.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-11-PRITYAZHATELNOE-PRONOUN-COHESION-WAVE-011-v0.1.json"

CANDIDATE = "candidate-004"
TAXONOMY = "cohesion_possessive_pronoun"
SEMANTIC = "ru-text-cohesion-possessive-pronoun"
CANONICAL_LABEL = "Притяжательное местоимение как средство связи"
EXPECTED_CHECK_IDS = {"p11-pos-v1", "p11-pos-v2", "p11-pos-v3"}
EXPECTED_BROADER_CHECK_IDS = {"p11-u2-v1", "p11-u2-v2"}
EXPECTED_CANDIDATES = {
    "candidate-001", "candidate-002", "candidate-003", "candidate-004",
    "candidate-005", "candidate-006", "candidate-007", "candidate-043",
    "candidate-044", "candidate-045", "candidate-046", "candidate-047",
}


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    broader = json.loads(BROADER.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU11_POSSESSIVE_PRONOUN_COHESION_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU11 candidate-004 acceptance status drift")
    if acceptance.get("authority_issue") != 161:
        raise AssertionError("RU11 candidate-004 authority issue drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU11 candidate-004 registry boundary drift")

    sg = acceptance.get("source_truth_guard") or {}
    if sg.get("inventory_candidate_review_status") != "draft" or sg.get("inventory_candidate_status_silently_upgraded") is not False:
        raise AssertionError("RU11 candidate-004 inventory guard drift")
    if sg.get("taxonomy_backing_review_status") != "source_verified" or sg.get("skill_graph_evidence_status") != "confirmed":
        raise AssertionError("RU11 candidate-004 source status drift")
    if sg.get("skill_graph_parent") != "text_cohesion" or sg.get("skill_graph_task_numbers") != [26]:
        raise AssertionError("RU11 candidate-004 graph boundary drift")
    if len(sg.get("accepted_positive_scope") or []) != 3:
        raise AssertionError("RU11 candidate-004 positive scope drift")
    for key in (
        "full_pronoun_morphology_mastery_admitted",
        "demonstrative_pronoun_mastery_admitted",
        "determinative_pronoun_mastery_admitted",
        "generic_task26_mastery_admitted",
        "object_form_at_verb_counts_as_possessive_mastery",
    ):
        if sg.get(key) is not False:
            raise AssertionError(f"RU11 candidate-004 source boundary weakened: {key}")

    policy = acceptance.get("policy") or {}
    for key in (
        "exact_current_source_identity_required",
        "source_verified_taxonomy_backing_required",
        "confirmed_skill_graph_evidence_required",
        "current_missing_subject_candidate_required",
        "draft_candidate_status_must_be_preserved",
        "exact_school_meaning_collision_forbidden",
        "reuse_first",
        "component_specific_independent_evidence_required",
        "school_duplicate_forbidden",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"RU11 candidate-004 policy weakened: {key}")
    if policy.get("minimum_component_specific_independent_checks") != 2 or policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU11 candidate-004 evidence/namespace policy drift")
    for key in (
        "ege_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
        "adjacent_candidates_admitted",
        "full_pronoun_morphology_mastery_admitted_by_this_authority",
        "demonstrative_or_determinative_pronoun_mastery_admitted_by_this_authority",
        "generic_task26_result_can_emit_exact_component_mastery",
        "object_form_at_verb_can_emit_exact_candidate_004_mastery",
        "broader_link_means_result_can_emit_exact_candidate_004_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "content_presence_alone_is_semantic_admission",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"RU11 candidate-004 fail-closed policy drift: {key}")

    modules = {str(r.get("module_id")): r for r in program.get("modules", []) if isinstance(r, dict)}
    module = modules.get("RU-PROG-11")
    if not isinstance(module, dict) or module.get("semantic_binding_mode") != "DRAFT_CANDIDATE_BINDING":
        raise AssertionError("RU11 module semantic binding drift")
    if set(module.get("candidate_refs") or []) != EXPECTED_CANDIDATES:
        raise AssertionError("RU11 candidate set drift")

    objects = [r for r in inventory.get("objects", []) if isinstance(r, dict)]
    candidate = one([
        r for r in objects
        if r.get("source_system") == "semantic_candidate"
        and r.get("source_id") == CANDIDATE
        and r.get("authority_status") == "current"
    ], "RU11 candidate-004")
    if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
        raise AssertionError("RU11 candidate-004 classification drift")
    if candidate.get("candidate_canonical_owner") != CANDIDATE or candidate.get("current_semantic_refs") != [TAXONOMY]:
        raise AssertionError("RU11 candidate-004 inventory identity drift")
    if candidate.get("review_status") != "draft" or normalized(candidate.get("observed_meaning")) != CANONICAL_LABEL:
        raise AssertionError("RU11 candidate-004 inventory meaning/status drift")

    backing = one([
        r for r in objects
        if r.get("source_system") == "ege_skill_graph"
        and r.get("source_id") == TAXONOMY
        and r.get("authority_status") == "current"
        and r.get("candidate_canonical_owner") == CANDIDATE
    ], "RU11 candidate-004 backing")
    if backing.get("review_status") != "source_verified" or backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise AssertionError("RU11 candidate-004 taxonomy backing drift")
    if normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU11 candidate-004 taxonomy meaning drift")

    skill = one([r for r in graph.get("skills", []) if isinstance(r, dict) and r.get("skill_id") == TAXONOMY], "RU11 possessive-pronoun graph node")
    if skill.get("evidence_status") != "confirmed" or skill.get("parent_skill_id") != "text_cohesion" or skill.get("exam_task_numbers") != [26]:
        raise AssertionError("RU11 candidate-004 graph evidence/route drift")
    if skill.get("name_ru") != CANONICAL_LABEL or normalized(skill.get("description")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU11 candidate-004 graph/source meaning drift")

    if any(SEMANTIC in {str(ref) for ref in (r.get("current_semantic_refs") or [])} for r in objects if r.get("authority_status") == "current"):
        raise AssertionError("RU11 candidate-004 semantic collision")
    if any(
        r.get("source_system") == "school_canonical"
        and r.get("authority_status") == "current"
        and normalized(r.get("observed_meaning")) == normalized(candidate.get("observed_meaning"))
        for r in objects
    ):
        raise AssertionError("RU11 candidate-004 exact school meaning exists; reuse required")

    broad_unit = one([
        r for r in broader.get("units", [])
        if isinstance(r, dict) and r.get("proposed_semantic_id") == "ru-text-cohesion-link-means"
    ], "RU11 broader cohesion-link-means unit")
    broad_checks = [r for r in (broad_unit.get("independent_verification") or []) if isinstance(r, dict)]
    if {str(r.get("id")) for r in broad_checks} != EXPECTED_BROADER_CHECK_IDS:
        raise AssertionError("RU11 broader cohesion check set drift")
    direct: list[str] = []
    for row in broad_checks:
        text = json.dumps(row, ensure_ascii=False).lower()
        if "притяж" in text or ("чей" in text and "местоим" in text):
            direct.append(str(row.get("id")))
    if direct:
        raise AssertionError(f"RU11 broader direct possessive-pronoun evidence drift: {direct}")
    demonstrative_check = one([r for r in broad_checks if str(r.get("id")) == "p11-u2-v2"], "RU11 broader demonstrative check")
    if "указатель" not in json.dumps(demonstrative_check, ensure_ascii=False).lower():
        raise AssertionError("RU11 broader p11-u2-v2 no longer proves demonstrative-only reuse boundary")

    reuse = acceptance.get("reuse_first_decision") or {}
    if reuse.get("broader_existing_unit_present") is not True or reuse.get("broader_existing_unit_reused_as_scope_and_explanation_evidence") is not True:
        raise AssertionError("RU11 candidate-004 reuse-first guard drift")
    if reuse.get("broader_existing_unit_is_exact_candidate_004_mastery_evidence") is not False:
        raise AssertionError("RU11 candidate-004 broader exact-evidence drift")
    if reuse.get("broader_existing_unit_direct_possessive_pronoun_independent_checks") != 0:
        raise AssertionError("RU11 candidate-004 broader direct-check count drift")
    if reuse.get("broader_existing_direct_check_ids") != []:
        raise AssertionError("RU11 candidate-004 broader direct-check identity drift")
    if reuse.get("minimum_component_specific_independent_checks_for_this_acceptance") != 2:
        raise AssertionError("RU11 candidate-004 minimum evidence drift")
    if reuse.get("exact_new_unit_component_specific_possessive_pronoun_checks") != 3:
        raise AssertionError("RU11 candidate-004 new-check count drift")
    if reuse.get("new_content_materialized_only_for_proven_component_verification_gap") is not True:
        raise AssertionError("RU11 candidate-004 content-gap justification drift")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-11":
        raise AssertionError("RU11 candidate-004 content status/module drift")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes") != 0 or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU11 candidate-004 copyright guard drift")
    content_reuse = content.get("reuse_review") or {}
    if content_reuse.get("broader_existing_unit_direct_possessive_pronoun_independent_checks") != 0:
        raise AssertionError("RU11 candidate-004 content reuse count drift")
    if content_reuse.get("broader_existing_direct_check_ids") != []:
        raise AssertionError("RU11 candidate-004 content reuse identity drift")
    if content_reuse.get("broader_existing_unit_reused_as_exact_candidate_004_mastery_evidence") is not False:
        raise AssertionError("RU11 candidate-004 content false reuse")

    unit = one([r for r in content.get("units", []) if isinstance(r, dict) and r.get("proposed_semantic_id") == SEMANTIC], "RU11 candidate-004 learner unit")
    if unit.get("title_ru") != CANONICAL_LABEL:
        raise AssertionError("RU11 candidate-004 learner title drift")
    for key, minimum in (
        ("decision_algorithm", 6),
        ("worked_examples", 4),
        ("misconceptions", 4),
        ("guided_practice", 3),
        ("independent_practice", 4),
        ("mixed_transfer_practice", 2),
        ("retention_items", 2),
        ("independent_verification", 3),
    ):
        if not isinstance(unit.get(key), list) or len(unit[key]) < minimum:
            raise AssertionError(f"RU11 candidate-004 learner section incomplete: {key}")

    checks = [r for r in (unit.get("independent_verification") or []) if isinstance(r, dict)]
    if {str(r.get("id")) for r in checks} != EXPECTED_CHECK_IDS or len(checks) != 3:
        raise AssertionError("RU11 candidate-004 exact verification ids drift")
    if any(r.get("type") != "constructed_response" for r in checks):
        raise AssertionError("RU11 candidate-004 verification must remain constructed-response")
    if any((r.get("scoring") or {}).get("max_points") != 3 or len((r.get("scoring") or {}).get("criteria") or []) != 3 for r in checks):
        raise AssertionError("RU11 candidate-004 verification scoring drift")
    criteria_text = " ".join(str(c).lower() for r in checks for c in ((r.get("scoring") or {}).get("criteria") or []))
    for needle in ("притяж", "референт", "связ"):
        if needle not in criteria_text:
            raise AssertionError(f"RU11 candidate-004 scoring boundary missing: {needle}")

    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL" or peis.get("source_candidate_ref") != CANDIDATE or peis.get("source_candidate_review_status") != "draft":
        raise AssertionError("RU11 candidate-004 PEIS source identity drift")
    if peis.get("independent_verification_required") is not True or peis.get("exact_mastery_requires_two_or_more_component_specific_possessive_pronoun_checks") is not True:
        raise AssertionError("RU11 candidate-004 PEIS independent-evidence guard drift")
    for key in (
        "generic_task26_result_can_emit_exact_component_mastery",
        "demonstrative_or_determinative_pronoun_result_can_emit_this_mastery",
        "broader_link_means_unit_can_emit_exact_possessive_pronoun_mastery",
    ):
        if peis.get(key) is not False:
            raise AssertionError(f"RU11 candidate-004 PEIS fail-closed drift: {key}")

    decision = one([r for r in (acceptance.get("decisions") or []) if isinstance(r, dict)], "RU11 candidate-004 decision")
    if decision.get("candidate_ref") != CANDIDATE or decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("RU11 candidate-004 decision identity drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU11 candidate-004 decision status drift")
    if decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("RU11 candidate-004 object-binding drift")

    summary = acceptance.get("summary") or {}
    expected_zero = (
        "adjacent_candidates_admitted",
        "full_pronoun_morphology_masteries_admitted",
        "demonstrative_or_determinative_pronoun_masteries_admitted",
        "new_school_canonical_identities",
        "object_level_admission_units_closed",
        "object_level_requirements_closed",
        "false_exact_mastery_admissions",
    )
    if summary.get("accepted_bounded_subject_semantics") != 1 or summary.get("accepted_ru_subject_semantics") != 1:
        raise AssertionError("RU11 candidate-004 accepted summary drift")
    if summary.get("source_backed_candidates_consumed") != 1 or summary.get("new_original_production_content_units_used") != 1:
        raise AssertionError("RU11 candidate-004 source/content summary drift")
    if any(summary.get(key) != 0 for key in expected_zero):
        raise AssertionError("RU11 candidate-004 fail-closed summary drift")

    normalized_hash = hashlib.sha256(
        json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print("RU11_POSSESSIVE_PRONOUN_COHESION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print("SOURCE_CANDIDATE_REVIEW_STATUS=draft")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print("BROADER_EXISTING_DIRECT_POSSESSIVE_PRONOUN_CHECKS=0")
    print("EXACT_COMPONENT_CHECKS=3")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_AUTHORITY_SHA256={normalized_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
