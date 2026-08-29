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
ACCEPTANCE = HERE / "RU09-SYNTAX-CANDIDATES-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-09-SYNTAX-NORMS-WAVE-001-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
BOUNDARY_BUILDER = HERE / "build_ru09_syntax_reuse_first_boundary_review.py"

EXPECTED = {
    "candidate-028": ("government_case_norm", "ru-syntax-government-case-norm"),
    "candidate-029": ("indirect_speech_construction", "ru-syntax-indirect-speech-norm"),
    "candidate-030": ("uncoordinated_apposition_construction", "ru-syntax-uncoordinated-apposition-norm"),
    "candidate-031": ("gerundial_construction_norm", "ru-syntax-gerundial-agent-norm"),
    "candidate-032": ("homogeneous_members_construction", "ru-syntax-homogeneous-members-norm"),
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    boundary = runpy.run_path(str(BOUNDARY_BUILDER))["build_review"]()

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU09_SYNTAX_CANDIDATE_BOUNDED_SUBJECT_SEMANTICS":
        raise AssertionError("RU09 acceptance status drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("RU09 acceptance mutated canonical school registry")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU09 acceptance created a parallel registry")

    policy = acceptance.get("policy") or {}
    required_policy = {
        "source_verified_taxonomy_backing_required": True,
        "draft_missing_subject_candidate_required": True,
        "original_bounded_learner_content_required": True,
        "school_duplicate_forbidden": True,
        "ege_taxonomy_id_promoted_unchanged": False,
        "candidate_id_used_as_semantic_id": False,
        "punctuation_identity_may_not_substitute_for_syntax_norm": True,
        "generic_ege_syntax_attempt_can_emit_exact_component_mastery": False,
        "component_specific_independent_evidence_required": True,
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
    }
    for key, expected in required_policy.items():
        if policy.get(key) is not expected:
            raise AssertionError(f"RU09 acceptance policy drift: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU09 acceptance namespace drift")

    summary = acceptance.get("summary") or {}
    expected_summary = {
        "accepted_bounded_subject_semantics": 5,
        "accepted_ru_subject_semantics": 5,
        "source_backed_candidates_consumed": 5,
        "original_production_content_units": 5,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }
    if summary != expected_summary:
        raise AssertionError(f"RU09 acceptance summary drift: {summary}")

    if boundary.get("status") != "CENTRAL_BRAIN_RU09_SYNTAX_REUSE_FIRST_BOUNDARY_REVIEW_IN_PROGRESS_NO_NEW_ADMISSION":
        raise AssertionError("RU09 boundary review status drift")
    bs = boundary.get("summary") or {}
    if bs.get("draft_subject_candidates") != 5 or bs.get("source_verified_taxonomy_backings") != 5:
        raise AssertionError("RU09 boundary candidate/source truth drift")
    if bs.get("candidate_exact_school_meaning_overlap_count") != 0:
        raise AssertionError("RU09 candidate exact-school overlap appeared and requires new review")
    if bs.get("new_semantic_admissions") != 0 or bs.get("new_object_level_closures") != 0:
        raise AssertionError("RU09 review self-admitted before acceptance")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-09":
        raise AssertionError("RU09 learner content self-admitted or module drift")
    content_units = content.get("units")
    if not isinstance(content_units, list) or len(content_units) != 5:
        raise AssertionError("RU09 learner content count drift")
    content_by_candidate = {str(row.get("candidate_ref")): row for row in content_units if isinstance(row, dict)}
    if set(content_by_candidate) != set(EXPECTED):
        raise AssertionError("RU09 learner content candidate set drift")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 5:
        raise AssertionError("RU09 acceptance must contain five decisions")
    by_candidate = {str(row.get("candidate_ref")): row for row in decisions if isinstance(row, dict)}
    if set(by_candidate) != set(EXPECTED):
        raise AssertionError("RU09 acceptance candidate set drift")

    accepted_refs: set[str] = set()
    for candidate_ref, (taxonomy_id, semantic_id) in EXPECTED.items():
        decision = by_candidate[candidate_ref]
        unit = content_by_candidate[candidate_ref]
        if decision.get("source_taxonomy_id") != taxonomy_id:
            raise AssertionError(f"RU09 acceptance taxonomy drift: {candidate_ref}")
        if decision.get("accepted_semantic_id") != semantic_id:
            raise AssertionError(f"RU09 accepted semantic drift: {candidate_ref}")
        if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
            raise AssertionError(f"RU09 decision not explicitly accepted: {candidate_ref}")
        if decision.get("entity_type") != "CONSTRUCTION_NORM_SKILL":
            raise AssertionError(f"RU09 entity type drift: {candidate_ref}")
        if decision.get("content_ref") != "russian-program/production-learning-content/RU-PROG-09-SYNTAX-NORMS-WAVE-001-v0.1.json":
            raise AssertionError(f"RU09 accepted content ref drift: {candidate_ref}")
        if len(str(decision.get("boundary_guard") or "")) < 80:
            raise AssertionError(f"RU09 accepted boundary too weak: {candidate_ref}")
        nearby = decision.get("nearby_existing_boundaries")
        if not isinstance(nearby, list) or not nearby:
            raise AssertionError(f"RU09 nearby-boundary review missing: {candidate_ref}")

        if unit.get("source_taxonomy_id") != taxonomy_id or unit.get("proposed_semantic_id") != semantic_id:
            raise AssertionError(f"RU09 content/acceptance crosswalk drift: {candidate_ref}")
        peis = unit.get("peis_evidence") or {}
        if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
            raise AssertionError(f"RU09 source content was mutated to self-admit: {candidate_ref}")
        if peis.get("independent_verification_required") is not True:
            raise AssertionError(f"RU09 independent verification weakened: {candidate_ref}")
        if peis.get("generic_syntax_score_can_emit_exact_mastery") is not False:
            raise AssertionError(f"RU09 generic syntax score can emit exact mastery: {candidate_ref}")

        candidates = [
            row for row in objects
            if row.get("source_system") == "semantic_candidate" and row.get("source_id") == candidate_ref
        ]
        if len(candidates) != 1:
            raise AssertionError(f"RU09 candidate inventory mismatch: {candidate_ref}")
        candidate = candidates[0]
        if candidate.get("authority_status") != "current" or candidate.get("review_status") != "draft":
            raise AssertionError(f"RU09 candidate source is no longer current/draft: {candidate_ref}")
        if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
            raise AssertionError(f"RU09 candidate source classification drift: {candidate_ref}")
        if candidate.get("current_semantic_refs") != [taxonomy_id]:
            raise AssertionError(f"RU09 candidate taxonomy ref drift: {candidate_ref}")

        backing = [
            row for row in objects
            if row.get("source_system") == "ege_skill_graph"
            and row.get("source_id") == taxonomy_id
            and row.get("candidate_canonical_owner") == candidate_ref
        ]
        if len(backing) != 1:
            raise AssertionError(f"RU09 taxonomy backing mismatch: {candidate_ref}")
        if backing[0].get("authority_status") != "current" or backing[0].get("review_status") != "source_verified":
            raise AssertionError(f"RU09 taxonomy backing not current/source-verified: {candidate_ref}")
        if backing[0].get("audit_classification") != "EGE_TAXONOMY_NODE":
            raise AssertionError(f"RU09 taxonomy backing classification drift: {candidate_ref}")

        for ref in nearby:
            ref = str(ref)
            if ref.startswith("school-"):
                matches = [row for row in objects if row.get("source_system") == "school_canonical" and row.get("source_id") == ref]
                if len(matches) != 1 or matches[0].get("authority_status") != "current":
                    raise AssertionError(f"RU09 nearby school boundary missing/current drift: {candidate_ref}/{ref}")
        accepted_refs.add(semantic_id)

    if accepted_refs != {semantic_id for _, semantic_id in EXPECTED.values()}:
        raise AssertionError("RU09 accepted semantic set drift")
    if any(ref in accepted_refs for ref in ("government_case_norm", "indirect_speech_construction", "uncoordinated_apposition_construction", "gerundial_construction_norm", "homogeneous_members_construction")):
        raise AssertionError("RU09 promoted EGE taxonomy IDs unchanged")

    crosswalk = acceptance.get("crosswalk_policy") or {}
    if crosswalk.get("mapping_relation") != "ROUTES_TO / CONTRIBUTES_TO":
        raise AssertionError("RU09 crosswalk relation drift")
    if crosswalk.get("generic_task8_result_can_emit_exact_component_mastery") is not False:
        raise AssertionError("RU09 generic Task-8 result can emit exact mastery")

    serialized = canonical_json(acceptance)
    for forbidden in (
        b'"object_level_admission_units_closed":1',
        b'"object_level_requirements_closed":1',
        b'"canonical_school_registry_mutated":true',
        b'"new_parallel_registry_created":true',
    ):
        if forbidden in serialized:
            raise AssertionError("RU09 bounded acceptance violated a hard boundary")

    print("RU09_SYNTAX_BOUNDED_SUBJECT_SEMANTICS=PASS")
    print("ACCEPTED_BOUNDED_SUBJECT_SEMANTICS=5")
    print("CANDIDATE_SOURCES_REMAIN_DRAFT=5")
    print("OBJECT_LEVEL_ADMISSION_UNITS_CLOSED=0")
    print("OBJECT_LEVEL_REQUIREMENTS_CLOSED=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("ACCEPTANCE_SHA256=" + hashlib.sha256(canonical_json(acceptance)).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
