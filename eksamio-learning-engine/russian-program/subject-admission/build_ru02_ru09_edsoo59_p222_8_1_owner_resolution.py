#!/usr/bin/env python3
"""Fail-closed owner resolution for EDSOO59 p.222 8.1 (RU02 + RU09 composite).

This review starts from the CI-proven current-v29 aggregate. It verifies the exact
source object, proves that the orthoepy clause already has accepted component
owners plus component-specific independent evidence, searches the current
canonical school inventory for an exact syntax-clause owner, and exposes only
source-backed bounded RU09 candidates when no exact syntax owner exists.

It deliberately does NOT choose among the RU09 candidates, accept the source
object, admit a semantic identity, or emit mastery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]

CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v29.py"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
PRON_ACCEPTANCE = HERE / "RU02-NORMATIVE-PRONUNCIATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
STRESS_ACCEPTANCE = HERE / "RU02-NORMATIVE-STRESS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
STRESS_CONTENT = ENGINE / "russian-program/production-learning-content/RU-PROG-02-ORTHOEPY-NORMATIVE-STRESS-WAVE-003-v0.1.json"
SYNTAX_ACCEPTANCE = HERE / "RU09-SYNTAX-CANDIDATES-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"

CURRENT_HEAD = "cb90377c4ebe00e88e22c39824b7c484651ebcc4"
CURRENT_RUN_ID = 34624859121
CURRENT_SHA = "7e7b74ddf4aa4fc9df9744ec74191d8893b6ae251b703c36dcd2ef911273d8e4"

GROUP = "RUS-SEM-REVIEW-048"
TARGET_UNIT = "RAU-3ceb45ca22608d520ddf"
TARGET_REQUIREMENT = "RSK-EDSOO59-8-1-P222"
TARGET_SOURCE = "EDSOO-RU-5-9-2025"
TARGET_DOCUMENT = "EDSOO59"
TARGET_PAGE = 222
TARGET_CODE = "8.1"
TARGET_LOCATOR = "EDSOO-RU-5-9-2025/EDSOO59 p.222 8.1"
TARGET_GRADES = ["8"]
TARGET_MEANING = "Применять нормативное произношение и ударение. Анализировать синтаксическую конструкцию и её нормативность."
ORTHOEPY_CLAUSE = "Применять нормативное произношение и ударение."
SYNTAX_CLAUSE = "Анализировать синтаксическую конструкцию и её нормативность."
TARGET_MODULES = ["RU-PROG-02", "RU-PROG-09", "RU-PROG-13", "RU-PROG-14"]
TARGET_ROUTES = ["school"]

PRON_REF = "ru-orthoepy-normative-pronunciation-selection"
STRESS_REF = "ru-orthoepy-normative-stress-selection"
PRON_EVIDENCE = [f"p02-u4-v{i}" for i in range(1, 6)]
STRESS_EVIDENCE = [f"p02-u3-v{i}" for i in range(1, 5)]

EXPECTED_SYNTAX_CANDIDATES = {
    "candidate-028": ("government_case_norm", "ru-syntax-government-case-norm"),
    "candidate-029": ("indirect_speech_construction", "ru-syntax-indirect-speech-norm"),
    "candidate-030": ("uncoordinated_apposition_construction", "ru-syntax-uncoordinated-apposition-norm"),
    "candidate-031": ("gerundial_construction_norm", "ru-syntax-gerundial-agent-norm"),
    "candidate-032": ("homogeneous_members_construction", "ru-syntax-homogeneous-members-norm"),
}

EXPECTED_CURRENT_SUMMARY = {
    "semantic_units_with_accepted_component_sets": 45,
    "semantic_requirements_with_accepted_component_sets": 45,
    "subject_disposed_units_total": 46,
    "subject_disposed_requirements_total": 46,
    "subject_review_units_remaining": 1270,
    "subject_review_requirements_remaining": 1345,
    "accepted_bounded_ru_subject_semantics": 75,
    "accepted_bounded_ru_semantics_total": 84,
    "canonical_component_refs_reused_unique": 125,
    "fully_accepted_semantic_groups": 1,
    "false_exact_mastery_admissions": 0,
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def one_decision(payload: dict[str, Any], semantic_id: str) -> dict[str, Any]:
    rows = [
        row
        for row in payload.get("decisions", [])
        if isinstance(row, dict) and row.get("accepted_semantic_id") == semantic_id
    ]
    if len(rows) != 1:
        raise ValueError(f"semantic decision missing or duplicated: {semantic_id}")
    return rows[0]


def independent_ids(content: dict[str, Any], semantic_id: str) -> list[str]:
    units = [
        row
        for row in content.get("units", [])
        if isinstance(row, dict) and row.get("proposed_semantic_id") == semantic_id
    ]
    if len(units) != 1:
        raise ValueError(f"learner-content unit missing or duplicated: {semantic_id}")
    rows = units[0].get("independent_verification")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"independent verification missing: {semantic_id}")
    ids = [str(row.get("id", "")) for row in rows if isinstance(row, dict)]
    if not all(ids) or len(ids) != len(rows) or len(set(ids)) != len(ids):
        raise ValueError(f"independent verification ids invalid: {semantic_id}")
    return ids


def build_review() -> dict[str, Any]:
    current = runpy.run_path(str(CURRENT))["build_progress"]()
    if current.get("schema_version") != "0.31.0":
        raise ValueError("current-v29 schema drift")
    if current.get("normalized_sha256") != CURRENT_SHA:
        raise ValueError("current-v29 normalized SHA drift")
    summary = current.get("progress_summary") or {}
    for key, expected in EXPECTED_CURRENT_SUMMARY.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v29 summary drift: {key}")
    if len(current.get("accepted_authorities") or []) != 75:
        raise ValueError("current-v29 accepted authority count drift")

    groups = [
        row
        for row in current.get("semantic_review_groups", [])
        if isinstance(row, dict) and row.get("group_id") == GROUP
    ]
    if len(groups) != 1:
        raise ValueError("target review group missing or duplicated")
    group = groups[0]
    if norm(group.get("normalized_meaning")) != TARGET_MEANING:
        raise ValueError("target group meaning drift")
    if group.get("admission_unit_count") != 1 or group.get("requirement_count") != 1:
        raise ValueError("target group denominator drift")
    if group.get("admission_unit_ids") != [TARGET_UNIT]:
        raise ValueError("target admission-unit identity drift")
    if group.get("accepted_component_set_count") not in (None, 0):
        raise ValueError("target group unexpectedly has accepted component set")
    if group.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("target group unexpectedly changed status")

    requirements = [
        row
        for row in group.get("requirements", [])
        if isinstance(row, dict) and row.get("requirement_id") == TARGET_REQUIREMENT
    ]
    if len(requirements) != 1:
        raise ValueError("target requirement missing or duplicated")
    req = requirements[0]
    exact_source = {
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "page": TARGET_PAGE,
        "code": TARGET_CODE,
        "source_locator": TARGET_LOCATOR,
        "grades": TARGET_GRADES,
        "confidence": "MEDIUM",
    }
    for key, expected in exact_source.items():
        if req.get(key) != expected:
            raise ValueError(f"target source identity drift: {key}")
    if sorted(req.get("modules") or []) != sorted(TARGET_MODULES):
        raise ValueError("target modules drift")
    if sorted(req.get("routes") or []) != TARGET_ROUTES:
        raise ValueError("target routes drift")

    pron = load(PRON_ACCEPTANCE)
    if pron.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU02_NORMATIVE_PRONUNCIATION_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("pronunciation semantic acceptance missing")
    pron_decision = one_decision(pron, PRON_REF)
    if pron_decision.get("source_taxonomy_id") != "normative_pronunciation_selection":
        raise ValueError("pronunciation taxonomy drift")
    if pron_decision.get("source_evidence_status") != "confirmed":
        raise ValueError("pronunciation evidence not confirmed")
    if pron_decision.get("independent_verification_item_ids") != PRON_EVIDENCE:
        raise ValueError("pronunciation evidence ids drift")
    if pron_decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise ValueError("pronunciation object-binding boundary drift")
    if (pron.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("pronunciation acceptance opened false exact mastery")

    stress = load(STRESS_ACCEPTANCE)
    if stress.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU02_NORMATIVE_STRESS_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("stress semantic acceptance missing")
    stress_decision = one_decision(stress, STRESS_REF)
    if stress_decision.get("candidate_ref") != "candidate-018":
        raise ValueError("stress candidate drift")
    if stress_decision.get("source_taxonomy_id") != "normative_stress_selection":
        raise ValueError("stress taxonomy drift")
    if stress_decision.get("source_evidence_status") != "confirmed":
        raise ValueError("stress evidence not confirmed")
    if stress_decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise ValueError("stress object-binding boundary drift")
    if (stress.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("stress acceptance opened false exact mastery")
    stress_ids = independent_ids(load(STRESS_CONTENT), STRESS_REF)
    if stress_ids != STRESS_EVIDENCE:
        raise ValueError("stress independent evidence ids drift")
    if set(PRON_EVIDENCE) & set(STRESS_EVIDENCE):
        raise ValueError("orthoepy component evidence lineages overlap")

    inventory = load(INVENTORY)
    if inventory.get("active_school_identity_count_observed") != 185:
        raise ValueError("current school identity denominator drift")
    exact_syntax_school_owners: list[dict[str, Any]] = []
    for obj in inventory.get("objects", []):
        if not isinstance(obj, dict):
            continue
        if obj.get("source_system") != "school_canonical":
            continue
        if obj.get("authority_status") != "current":
            continue
        if obj.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY":
            continue
        if obj.get("review_status") != "reviewed":
            continue
        if norm(obj.get("observed_meaning")) == SYNTAX_CLAUSE:
            exact_syntax_school_owners.append(obj)
    if exact_syntax_school_owners:
        raise ValueError("an exact current canonical syntax owner now exists; blocker must be re-resolved")

    syntax = load(SYNTAX_ACCEPTANCE)
    if syntax.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU09_SYNTAX_CANDIDATE_BOUNDED_SUBJECT_SEMANTICS":
        raise ValueError("RU09 bounded syntax acceptance missing")
    if (syntax.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("RU09 syntax acceptance opened false exact mastery")
    if (syntax.get("summary") or {}).get("object_level_admission_units_closed") != 0:
        raise ValueError("RU09 syntax semantics unexpectedly closed objects")
    syntax_rows: list[dict[str, Any]] = []
    actual_refs: set[str] = set()
    for candidate_ref, (taxonomy, semantic_id) in EXPECTED_SYNTAX_CANDIDATES.items():
        row = one_decision(syntax, semantic_id)
        if row.get("candidate_ref") != candidate_ref:
            raise ValueError(f"RU09 candidate ref drift: {semantic_id}")
        if row.get("source_taxonomy_id") != taxonomy:
            raise ValueError(f"RU09 taxonomy drift: {semantic_id}")
        if row.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
            raise ValueError(f"RU09 bounded semantic status drift: {semantic_id}")
        actual_refs.add(candidate_ref)
        syntax_rows.append(
            {
                "candidate_ref": candidate_ref,
                "source_taxonomy_id": taxonomy,
                "accepted_semantic_id": semantic_id,
                "canonical_label_ru": str(row.get("canonical_label_ru", "")),
                "boundary_guard": str(row.get("boundary_guard", "")),
                "selection_status": "SOURCE_BACKED_BOUNDED_CANDIDATE_NOT_SELECTED_FOR_THIS_OBJECT",
            }
        )
    if actual_refs != set(EXPECTED_SYNTAX_CANDIDATES):
        raise ValueError("RU09 source-backed candidate set drift")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_EDSOO59_P222_8_1_OWNER_RESOLUTION_BLOCKED_MISSING_EXACT_SYNTAX_OWNER",
        "current_v29_exact_head_gate": {
            "workflow": "Russian RU02 OGE p21 4.1.6 current exact acceptance",
            "run_id": CURRENT_RUN_ID,
            "head_sha": CURRENT_HEAD,
            "conclusion": "SUCCESS",
            "normalized_sha256": CURRENT_SHA,
        },
        "selected_object": {
            "admission_unit_id": TARGET_UNIT,
            "requirement_id": TARGET_REQUIREMENT,
            "packet_group": GROUP,
            "source_id": TARGET_SOURCE,
            "document_id": TARGET_DOCUMENT,
            "page": TARGET_PAGE,
            "code": TARGET_CODE,
            "source_locator": TARGET_LOCATOR,
            "grades": TARGET_GRADES,
            "confidence": "MEDIUM",
            "normalized_meaning": TARGET_MEANING,
            "modules": TARGET_MODULES,
            "routes": TARGET_ROUTES,
        },
        "component_resolution": {
            "orthoepy_clause": {
                "source_clause": ORTHOEPY_CLAUSE,
                "status": "EXACT_ACCEPTED_COMPONENT_OWNERS_WITH_COMPONENT_SPECIFIC_EVIDENCE_AVAILABLE",
                "canonical_component_refs": [PRON_REF, STRESS_REF],
                "component_specific_independent_evidence": {
                    PRON_REF: PRON_EVIDENCE,
                    STRESS_REF: STRESS_EVIDENCE,
                },
                "independent_evidence_items": 9,
            },
            "syntax_clause": {
                "source_clause": SYNTAX_CLAUSE,
                "exact_current_canonical_school_owner_refs": [],
                "exact_current_canonical_school_owner_count": 0,
                "status": "BLOCKED_NO_EXACT_CURRENT_CANONICAL_OWNER",
                "source_backed_bounded_candidates": syntax_rows,
                "candidate_selection_allowed": False,
                "required_next_resolution": (
                    "Obtain exact source-backed decomposition of EDSOO59 p.222 8.1 syntax scope "
                    "to one or more accepted component owners, or create a separately reviewed "
                    "bounded owner with component-specific independent evidence. Do not infer "
                    "from module, route, title, task number, nearby school identities, or candidate labels."
                ),
            },
        },
        "policy": {
            "exact_current_owner_search_performed_first": True,
            "source_backed_candidate_fallback_only": True,
            "keyword_or_fuzzy_owner_inference_allowed": False,
            "module_route_title_or_task_number_inference_allowed": False,
            "nearby_semantic_candidate_auto_selection_allowed": False,
            "object_acceptance_allowed_by_this_review": False,
            "semantic_admission_allowed_by_this_review": False,
            "mastery_admission_allowed_by_this_review": False,
            "registered_user_identity_required_for_future_canonical_learner_evidence": True,
            "anonymous_or_device_only_canonical_progress_allowed": False,
            "false_exact_mastery_must_remain_zero": True,
        },
        "blocker": {
            "kind": "MISSING_EXACT_SYNTAX_OWNER_OR_EXACT_SOURCE_DECOMPOSITION",
            "owner_decision_required_now": False,
            "bounded_resolution_available_in_repo": True,
            "object_remains_subject_review_required": True,
        },
        "summary": {
            "exact_orthoepy_component_owners": 2,
            "orthoepy_component_specific_independent_evidence_items": 9,
            "exact_current_canonical_syntax_owners": 0,
            "source_backed_bounded_syntax_candidates": len(syntax_rows),
            "semantic_admissions": 0,
            "object_level_closures": 0,
            "exact_mastery_admissions": 0,
            "false_exact_mastery_admissions": 0,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_bytes(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_review()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_EDSOO59_P222_8_1_OWNER_RESOLUTION=BLOCKED_FAIL_CLOSED")
        print(f"TARGET_UNIT={TARGET_UNIT}")
        print(f"TARGET_REQUIREMENT={TARGET_REQUIREMENT}")
        print(f"EXACT_SYNTAX_OWNERS={result['summary']['exact_current_canonical_syntax_owners']}")
        print(f"BOUNDED_SYNTAX_CANDIDATES={result['summary']['source_backed_bounded_syntax_candidates']}")
        print(f"FALSE_EXACT_MASTERY={result['summary']['false_exact_mastery_admissions']}")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
