#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
ACCEPTANCE = HERE / "RU02-NORMATIVE-STRESS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-02-ORTHOEPY-NORMATIVE-STRESS-WAVE-003-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
SKILL_GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
TRAINER_BANK = ENGINE / "russkiy-knigi/ege-russkiy-trenazher/ORTHOEPIC-TRAINER-BANK.json"
SOURCE_RESOLVER = HERE / "build_ru02_orthoepy_source_identity_resolution.py"
GAP_REVIEW = HERE / "build_ru02_orthoepy_content_adequacy_review.py"

CANDIDATE = "candidate-018"
TAXONOMY = "normative_stress_selection"
SEMANTIC = "ru-orthoepy-normative-stress-selection"
ADJACENT = {f"candidate-{number:03d}" for number in range(19, 25)}
EXPECTED_CORE_FACTS = {"catalog", "prettier", "calls"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(SKILL_GRAPH.read_text(encoding="utf-8"))
    bank = json.loads(TRAINER_BANK.read_text(encoding="utf-8"))
    source_resolution = runpy.run_path(str(SOURCE_RESOLVER))["build_resolution"]()
    gap_review = runpy.run_path(str(GAP_REVIEW))["build_review"]()

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU02_NORMATIVE_STRESS_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU02 candidate-018 acceptance status drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("RU02 candidate-018 acceptance mutated school registry")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU02 candidate-018 acceptance created parallel registry")

    policy = acceptance.get("policy") or {}
    required_policy = {
        "exact_current_source_identity_required": True,
        "confirmed_skill_graph_evidence_required": True,
        "current_missing_subject_candidate_required": True,
        "exact_school_meaning_collision_forbidden": True,
        "original_exact_learner_content_required": True,
        "school_duplicate_forbidden": True,
        "ege_taxonomy_id_promoted_unchanged": False,
        "candidate_id_used_as_semantic_id": False,
        "adjacent_partial_evidence_candidates_admitted": False,
        "generic_task4_result_can_emit_exact_component_mastery": False,
        "component_specific_independent_evidence_required": True,
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
        "content_presence_alone_is_semantic_admission": False,
    }
    for key, expected in required_policy.items():
        if policy.get(key) is not expected:
            raise AssertionError(f"RU02 candidate-018 acceptance policy drift: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU02 candidate-018 namespace drift")

    if source_resolution.get("status") != "CENTRAL_BRAIN_RU02_SOURCE_IDENTITIES_RESOLVED_SUBJECT_ACCEPTANCE_NOT_ADMITTED":
        raise AssertionError("RU02 source-resolution prerequisite drift")
    resolved = {
        str(row.get("candidate_ref")): row
        for row in source_resolution.get("resolutions", [])
        if isinstance(row, dict)
    }
    if set(resolved) != {f"candidate-{number:03d}" for number in range(18, 25)}:
        raise AssertionError("RU02 source-resolution candidate set drift")
    source_row = resolved[CANDIDATE]
    if source_row.get("source_taxonomy_id") != TAXONOMY:
        raise AssertionError("RU02 candidate-018 source taxonomy drift")
    if source_row.get("source_identity_resolution") != "EXACT_CURRENT_SOURCE_VERIFIED_INVENTORY_BACKING_GRAPH_EVIDENCE_PRESERVED":
        raise AssertionError("RU02 candidate-018 source identity is not exact/current/source-verified")
    if source_row.get("skill_graph_evidence_status") != "confirmed":
        raise AssertionError("RU02 candidate-018 is not confirmed in skill graph")
    if any(resolved[c].get("skill_graph_evidence_status") != "partial" for c in ADJACENT):
        raise AssertionError("RU02 adjacent candidate evidence changed; acceptance requires new review")

    if gap_review.get("status") != "CENTRAL_BRAIN_RU02_EXISTING_CONTENT_ADEQUACY_REVIEW_COMPLETE_EXACT_CANDIDATE_CONTENT_GAPS_PROVEN_NO_ADMISSION":
        raise AssertionError("RU02 pre-materialization gap review drift")
    gaps = {
        str(row.get("candidate_ref")): row
        for row in gap_review.get("candidate_gap_status", [])
        if isinstance(row, dict)
    }
    if gaps.get(CANDIDATE, {}).get("exact_candidate_content_status") != "MISSING_EXACT_CANDIDATE_LEARNER_CONTENT":
        raise AssertionError("RU02 candidate-018 pre-materialization gap is no longer proven")
    if int((gap_review.get("summary") or {}).get("semantic_admissions", -1)) != 0:
        raise AssertionError("RU02 gap review self-admitted semantics")

    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    candidates = [
        row for row in objects
        if row.get("source_system") == "semantic_candidate"
        and row.get("source_id") == CANDIDATE
        and row.get("authority_status") == "current"
    ]
    if len(candidates) != 1:
        raise AssertionError("RU02 candidate-018 current inventory mismatch")
    candidate = candidates[0]
    if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
        raise AssertionError("RU02 candidate-018 classification drift")
    if candidate.get("candidate_canonical_owner") != CANDIDATE:
        raise AssertionError("RU02 candidate-018 owner drift")
    if candidate.get("review_status") not in {"draft", "needs_review"}:
        raise AssertionError("RU02 candidate-018 review status is not fail-closed")
    if candidate.get("observed_label") != "Определение нормативной позиции ударения":
        raise AssertionError("RU02 candidate-018 label drift")
    if candidate.get("current_semantic_refs") != [TAXONOMY]:
        raise AssertionError("RU02 candidate-018 taxonomy refs drift")

    backing = [
        row for row in objects
        if row.get("source_system") == "ege_skill_graph"
        and row.get("source_id") == TAXONOMY
        and row.get("authority_status") == "current"
        and row.get("candidate_canonical_owner") == CANDIDATE
    ]
    if len(backing) != 1:
        raise AssertionError("RU02 candidate-018 taxonomy backing mismatch")
    if backing[0].get("review_status") != "source_verified" or backing[0].get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise AssertionError("RU02 candidate-018 taxonomy backing is not source-verified")
    if normalized(backing[0].get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU02 candidate-018 inventory meanings drift")

    graph_rows = [row for row in graph.get("skills", []) if isinstance(row, dict) and row.get("skill_id") == TAXONOMY]
    if len(graph_rows) != 1:
        raise AssertionError("RU02 candidate-018 graph node mismatch")
    graph_row = graph_rows[0]
    if graph_row.get("name_ru") != candidate.get("observed_label"):
        raise AssertionError("RU02 candidate-018 graph label drift")
    if normalized(graph_row.get("description")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU02 candidate-018 graph meaning drift")
    if graph_row.get("parent_skill_id") != "orthoepic_norms" or graph_row.get("exam_task_numbers") != [4]:
        raise AssertionError("RU02 candidate-018 graph route boundary drift")
    if graph_row.get("evidence_status") != "confirmed":
        raise AssertionError("RU02 candidate-018 graph evidence is not confirmed")

    collisions = []
    for row in objects:
        if row.get("authority_status") != "current":
            continue
        refs = {str(ref) for ref in (row.get("current_semantic_refs") or [])}
        if SEMANTIC in refs:
            collisions.append(str(row.get("object_key")))
    if collisions:
        raise AssertionError(f"RU02 accepted semantic id collides with current inventory: {collisions}")

    exact_school_meaning = [
        row for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and normalized(row.get("observed_meaning")) == normalized(candidate.get("observed_meaning"))
    ]
    if exact_school_meaning:
        raise AssertionError("RU02 candidate-018 exact school meaning already exists; reuse required")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-02":
        raise AssertionError("RU02 candidate-018 content status/module drift")
    copyright_guard = content.get("copyright_guard") or {}
    if copyright_guard.get("source_passages_copied") != 0 or copyright_guard.get("commercial_textbook_bytes_in_git") != 0:
        raise AssertionError("RU02 candidate-018 copyright boundary weakened")
    if copyright_guard.get("learner_explanations") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU02 candidate-018 learner explanation provenance drift")

    units = content.get("units")
    if not isinstance(units, list) or len(units) != 1:
        raise AssertionError("RU02 candidate-018 content must contain exactly one bounded unit")
    unit = units[0]
    if unit.get("candidate_ref") != CANDIDATE or unit.get("source_taxonomy_id") != TAXONOMY or unit.get("proposed_semantic_id") != SEMANTIC:
        raise AssertionError("RU02 candidate-018 content crosswalk drift")
    explanation = unit.get("canonical_explanation") or {}
    if len(str(explanation.get("short") or "")) < 180:
        raise AssertionError("RU02 candidate-018 explanation too weak")
    boundaries = explanation.get("boundaries")
    if not isinstance(boundaries, list) or len(boundaries) < 4:
        raise AssertionError("RU02 candidate-018 boundary set incomplete")
    if not any("candidate-019…024" in str(row) for row in boundaries):
        raise AssertionError("RU02 candidate-018 adjacent-candidate exclusion missing")

    for key, minimum in (
        ("decision_algorithm", 5),
        ("worked_examples", 3),
        ("misconceptions", 3),
        ("guided_practice", 2),
        ("independent_practice", 3),
        ("mixed_transfer_practice", 1),
        ("retention_items", 2),
        ("independent_verification", 4),
    ):
        value = unit.get(key)
        if not isinstance(value, list) or len(value) < minimum:
            raise AssertionError(f"RU02 candidate-018 learner-content section incomplete: {key}")

    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError("RU02 candidate-018 content self-admitted")
    if peis.get("independent_verification_required") is not True or peis.get("component_specific_independent_evidence_required") is not True:
        raise AssertionError("RU02 candidate-018 independent-evidence boundary weakened")
    if peis.get("generic_task4_score_can_emit_exact_mastery") is not False:
        raise AssertionError("RU02 candidate-018 generic Task-4 score can emit exact mastery")
    tutor = unit.get("tutor_grounding") or {}
    if not isinstance(tutor.get("allowed"), list) or not tutor["allowed"] or not isinstance(tutor.get("forbidden"), list) or not tutor["forbidden"]:
        raise AssertionError("RU02 candidate-018 Tutor grounding missing")

    bank_by_id = {str(row.get("id")): row for row in bank.get("entries", []) if isinstance(row, dict)}
    if not EXPECTED_CORE_FACTS <= set(bank_by_id):
        raise AssertionError("RU02 candidate-018 core normative facts missing from audited trainer bank")
    referenced_fact_ids: set[str] = set()
    for section in ("worked_examples", "guided_practice", "independent_practice", "retention_items", "independent_verification"):
        for row in unit.get(section) or []:
            if not isinstance(row, dict) or "source_fact_id" not in row:
                continue
            fact_id = str(row["source_fact_id"])
            fact = bank_by_id.get(fact_id)
            if fact is None:
                raise AssertionError(f"RU02 candidate-018 references unknown normative fact: {fact_id}")
            expected_ref = f"ORTHOEPIC-TRAINER-BANK.json#entries[id={fact_id}]"
            if row.get("source_fact_ref") != expected_ref:
                raise AssertionError(f"RU02 candidate-018 normative fact ref drift: {fact_id}")
            serialized_row = json.dumps(row, ensure_ascii=False)
            if str(fact.get("correct")) not in serialized_row:
                raise AssertionError(f"RU02 candidate-018 content does not preserve correct bank form: {fact_id}")
            referenced_fact_ids.add(fact_id)
    if not EXPECTED_CORE_FACTS <= referenced_fact_ids:
        raise AssertionError("RU02 candidate-018 content lacks cross-category core normative facts")

    verification = unit["independent_verification"]
    choice_rows = [row for row in verification if isinstance(row, dict) and row.get("type") == "single_choice"]
    if len(choice_rows) != 3:
        raise AssertionError("RU02 candidate-018 must have three source-bound independent choices")
    for row in choice_rows:
        fact = bank_by_id[str(row["source_fact_id"])]
        options = row.get("options")
        index = row.get("correct_option_index")
        if not isinstance(options, list) or not isinstance(index, int) or index < 0 or index >= len(options):
            raise AssertionError("RU02 candidate-018 independent choice schema drift")
        if options[index] != fact.get("correct") or str(fact.get("wrong")) not in options:
            raise AssertionError(f"RU02 candidate-018 independent choice answer drift: {row['source_fact_id']}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("RU02 candidate-018 acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("candidate_ref") != CANDIDATE or decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("RU02 candidate-018 acceptance decision crosswalk drift")
    if decision.get("canonical_label_ru") != candidate.get("observed_label"):
        raise AssertionError("RU02 candidate-018 acceptance label drift")
    if decision.get("entity_type") != "STRESS_SELECTION_SKILL":
        raise AssertionError("RU02 candidate-018 entity type drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU02 candidate-018 is not explicitly bounded-accepted")
    if decision.get("source_evidence_status") != "confirmed":
        raise AssertionError("RU02 candidate-018 acceptance overstates/loses source evidence")
    if decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("RU02 candidate-018 acceptance falsely claims object binding")
    if set(decision.get("excluded_adjacent_candidate_refs") or []) != ADJACENT:
        raise AssertionError("RU02 candidate-018 adjacent candidate exclusion drift")
    if len(str(decision.get("boundary_guard") or "")) < 180:
        raise AssertionError("RU02 candidate-018 acceptance boundary too weak")

    summary = acceptance.get("summary") or {}
    expected_summary = {
        "accepted_bounded_subject_semantics": 1,
        "accepted_ru_subject_semantics": 1,
        "source_backed_candidates_consumed": 1,
        "original_production_content_units": 1,
        "adjacent_partial_evidence_candidates_admitted": 0,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }
    if summary != expected_summary:
        raise AssertionError(f"RU02 candidate-018 acceptance summary drift: {summary}")

    crosswalk = acceptance.get("crosswalk_policy") or {}
    if crosswalk.get("mapping_relation") != "ROUTES_TO / CONTRIBUTES_TO":
        raise AssertionError("RU02 candidate-018 crosswalk relation drift")
    if crosswalk.get("exam_task_number_is_semantic_identity") is not False:
        raise AssertionError("RU02 candidate-018 task number promoted to semantic identity")
    if crosswalk.get("generic_task4_result_can_emit_exact_component_mastery") is not False:
        raise AssertionError("RU02 candidate-018 crosswalk allows false exact mastery")

    serialized = canonical_json(acceptance)
    for forbidden in (
        b'"object_level_admission_units_closed":1',
        b'"object_level_requirements_closed":1',
        b'"canonical_school_registry_mutated":true',
        b'"new_parallel_registry_created":true',
    ):
        if forbidden in serialized:
            raise AssertionError("RU02 candidate-018 bounded acceptance violated a hard boundary")

    print("RU02_NORMATIVE_STRESS_BOUNDED_SUBJECT_SEMANTIC=PASS")
    print("ACCEPTED_BOUNDED_SUBJECT_SEMANTICS=1")
    print("SOURCE_SKILL_GRAPH_EVIDENCE=confirmed")
    print("ADJACENT_PARTIAL_CANDIDATES_ADMITTED=0")
    print("OBJECT_LEVEL_ADMISSION_UNITS_CLOSED=0")
    print("OBJECT_LEVEL_REQUIREMENTS_CLOSED=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("ACCEPTANCE_SHA256=" + hashlib.sha256(canonical_json(acceptance)).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
