#!/usr/bin/env python3
"""Fail-closed exact object-binding review for the selected RU02 orthoepy object."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CONTENT = HERE.parent / "production-learning-content"
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v2.py"
STRESS_ACCEPTANCE = HERE / "RU02-NORMATIVE-STRESS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
PRON_ACCEPTANCE = HERE / "RU02-NORMATIVE-PRONUNCIATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
PRON_OWNER = HERE / "RU02-NORMATIVE-PRONUNCIATION-OWNER-RESOLUTION-v0.1.json"
STRESS_CONTENT = CONTENT / "RU-PROG-02-ORTHOEPY-NORMATIVE-STRESS-WAVE-003-v0.1.json"
PRON_CONTENT = CONTENT / "RU-PROG-02-ORTHOEPY-NORMATIVE-PRONUNCIATION-WAVE-004-v0.1.json"

CURRENT_SHA = "f25202c09baf0452fce2392726ddb02ce8a17dd111851f25f58e5334e873a4c7"
TARGET_UNIT = "RAU-a8f2ad0b357c9e369c51"
TARGET_REQUIREMENT = "RSK-EDSOO1011-2-2-4-P074"
TARGET_GROUP = "RUS-SEM-REVIEW-047"
TARGET_SOURCE = "EDSOO-RU-10-11-BASIC-2025"
TARGET_DOCUMENT = "EDSOO1011"
TARGET_CODE = "2.2.4"
TARGET_PAGE = 74
TARGET_LOCATOR = "EDSOO-RU-10-11-BASIC-2025/EDSOO1011 p.74 2.2.4"
TARGET_MEANING = "Применять нормативное произношение и ударение."
STRESS_REF = "ru-orthoepy-normative-stress-selection"
PRON_REF = "ru-orthoepy-normative-pronunciation-selection"
STRESS_EVIDENCE = ["p02-u3-v1", "p02-u3-v2", "p02-u3-v3", "p02-u3-v4"]
PRON_EVIDENCE = ["p02-u4-v1", "p02-u4-v2", "p02-u4-v3", "p02-u4-v4", "p02-u4-v5"]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def one_decision(doc: dict[str, Any], semantic_ref: str) -> dict[str, Any]:
    rows = [row for row in doc.get("decisions", []) if isinstance(row, dict) and row.get("accepted_semantic_id") == semantic_ref]
    if len(rows) != 1:
        raise ValueError(f"accepted semantic decision not unique: {semantic_ref}")
    return rows[0]


def one_content_unit(doc: dict[str, Any], semantic_ref: str) -> dict[str, Any]:
    rows = []
    for row in doc.get("units", []):
        if not isinstance(row, dict):
            continue
        ref = row.get("proposed_semantic_id")
        if ref == semantic_ref:
            rows.append(row)
    if len(rows) != 1:
        raise ValueError(f"content unit not unique: {semantic_ref}")
    return rows[0]


def evidence_ids(unit: dict[str, Any]) -> list[str]:
    rows = unit.get("independent_verification", [])
    if not isinstance(rows, list) or not rows:
        raise ValueError("independent verification missing")
    ids = [str(row.get("id")) for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or len(ids) != len(set(ids)):
        raise ValueError("independent verification ids are missing or duplicated")
    return ids


def build_review() -> dict[str, Any]:
    current = runpy.run_path(str(CURRENT))["build_progress"]()
    if current.get("normalized_sha256") != CURRENT_SHA:
        raise ValueError("current-v2 launch fingerprint drift")
    summary = current.get("progress_summary") or {}
    expected_summary = {
        "semantic_units_with_accepted_component_sets": 28,
        "semantic_requirements_with_accepted_component_sets": 28,
        "subject_disposed_units_total": 29,
        "subject_disposed_requirements_total": 29,
        "subject_review_units_remaining": 1287,
        "subject_review_requirements_remaining": 1362,
        "false_exact_mastery_admissions": 0,
    }
    for key, value in expected_summary.items():
        if summary.get(key) != value:
            raise ValueError(f"current-v2 launch aggregate drift: {key}")
    if len(current.get("accepted_authorities", [])) != 49:
        raise ValueError("current-v2 accepted authority count drift")

    groups = [row for row in current.get("semantic_review_groups", []) if isinstance(row, dict) and row.get("group_id") == TARGET_GROUP]
    if len(groups) != 1:
        raise ValueError("selected RU02 packet group is not unique")
    group = groups[0]
    if TARGET_UNIT not in {str(value) for value in group.get("admission_unit_ids", [])}:
        raise ValueError("selected RU02 admission unit missing from packet group")
    if str(group.get("normalized_meaning")) != TARGET_MEANING:
        raise ValueError("selected RU02 normalized source meaning drift")

    requirements = [row for row in group.get("requirements", []) if isinstance(row, dict) and row.get("requirement_id") == TARGET_REQUIREMENT]
    if len(requirements) != 1:
        raise ValueError("selected RU02 requirement is not unique")
    requirement = requirements[0]
    expected_requirement = {
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "page": TARGET_PAGE,
        "code": TARGET_CODE,
        "source_locator": TARGET_LOCATOR,
    }
    for key, value in expected_requirement.items():
        if requirement.get(key) != value:
            raise ValueError(f"selected RU02 source identity drift: {key}")

    for current_group in current.get("semantic_review_groups", []):
        if not isinstance(current_group, dict):
            continue
        for row in current_group.get("accepted_component_sets", []):
            if not isinstance(row, dict):
                continue
            if row.get("admission_unit_id") == TARGET_UNIT or row.get("requirement_id") == TARGET_REQUIREMENT:
                raise ValueError("selected RU02 object is already closed by a component-set authority")
        for row in current_group.get("accepted_nonsemantic_object_dispositions", []):
            if not isinstance(row, dict):
                continue
            if row.get("admission_unit_id") == TARGET_UNIT or row.get("requirement_id") == TARGET_REQUIREMENT:
                raise ValueError("selected RU02 object is already disposed nonsemantically")

    stress = load(STRESS_ACCEPTANCE)
    if stress.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU02_NORMATIVE_STRESS_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("stress semantic is not independently accepted")
    stress_decision = one_decision(stress, STRESS_REF)
    if stress_decision.get("candidate_ref") != "candidate-018" or stress_decision.get("source_taxonomy_id") != "normative_stress_selection":
        raise ValueError("stress source identity drift")
    if stress_decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise ValueError("stress semantic object-binding boundary drift")
    if stress_decision.get("source_evidence_status") != "confirmed":
        raise ValueError("stress source evidence is not confirmed")
    if (stress.get("summary") or {}).get("object_level_admission_units_closed") != 0 or (stress.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("stress semantic acceptance changed object counts or false mastery")

    pronunciation = load(PRON_ACCEPTANCE)
    if pronunciation.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU02_NORMATIVE_PRONUNCIATION_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("pronunciation semantic is not independently accepted")
    pron_decision = one_decision(pronunciation, PRON_REF)
    if pron_decision.get("source_taxonomy_id") != "normative_pronunciation_selection":
        raise ValueError("pronunciation source identity drift")
    if pron_decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise ValueError("pronunciation semantic object-binding boundary drift")
    if pron_decision.get("source_evidence_status") != "confirmed":
        raise ValueError("pronunciation source evidence is not confirmed")
    if pron_decision.get("independent_verification_item_ids") != PRON_EVIDENCE:
        raise ValueError("pronunciation accepted evidence ids drift")
    if (pronunciation.get("summary") or {}).get("object_level_admission_units_closed") != 0 or (pronunciation.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("pronunciation semantic acceptance changed object counts or false mastery")

    owner = load(PRON_OWNER)
    target = owner.get("target_object") or {}
    expected_target = {
        "admission_unit_id": TARGET_UNIT,
        "requirement_id": TARGET_REQUIREMENT,
        "review_group_id": TARGET_GROUP,
        "source_locator": "EDSOO1011 2.2.4 p.74",
        "module_id": "RU-PROG-02",
        "normalized_meaning": TARGET_MEANING,
    }
    for key, value in expected_target.items():
        if target.get(key) != value:
            raise ValueError(f"pronunciation owner target drift: {key}")
    if (owner.get("existing_owner_search") or {}).get("resolution") != "NO_EXACT_CURRENT_PRONUNCIATION_OWNER":
        raise ValueError("pronunciation reuse-first owner search drift")
    proposed_owner = owner.get("proposed_owner") or {}
    if proposed_owner.get("semantic_id") != PRON_REF or proposed_owner.get("source_taxonomy_id") != "normative_pronunciation_selection":
        raise ValueError("pronunciation owner semantic identity drift")
    owner_boundary = owner.get("acceptance_boundary") or {}
    if owner_boundary.get("semantic_admission_effect") != "NONE" or owner_boundary.get("object_closure_effect") != "NONE" or owner_boundary.get("false_exact_mastery") != 0:
        raise ValueError("pronunciation owner resolution self-admitted")

    stress_unit = one_content_unit(load(STRESS_CONTENT), STRESS_REF)
    pron_unit = one_content_unit(load(PRON_CONTENT), PRON_REF)
    if evidence_ids(stress_unit) != STRESS_EVIDENCE:
        raise ValueError("stress independent verification ids drift")
    if evidence_ids(pron_unit) != PRON_EVIDENCE:
        raise ValueError("pronunciation independent verification ids drift")
    if set(STRESS_EVIDENCE) & set(PRON_EVIDENCE):
        raise ValueError("stress/pronunciation evidence lineages overlap")
    if (stress_unit.get("peis_evidence") or {}).get("component_specific_independent_evidence_required") is not True:
        raise ValueError("stress PEIS component-specific evidence guard drift")
    if (pron_unit.get("peis_evidence") or {}).get("component_specific_independent_evidence_required") is not True:
        raise ValueError("pronunciation PEIS component-specific evidence guard drift")

    component_set = [PRON_REF, STRESS_REF]
    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU02_ORTHOEPY_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED",
        "current_launch_progress_sha256": CURRENT_SHA,
        "selected_object": {
            "admission_unit_id": TARGET_UNIT,
            "requirement_id": TARGET_REQUIREMENT,
            "packet_group": TARGET_GROUP,
            "source_id": TARGET_SOURCE,
            "document_id": TARGET_DOCUMENT,
            "page": TARGET_PAGE,
            "code": TARGET_CODE,
            "source_locator": TARGET_LOCATOR,
            "module_id": "RU-PROG-02",
            "normalized_meaning": TARGET_MEANING,
        },
        "source_backed_exact_component_decomposition": {
            "relation": "EXPLICIT_COORDINATED_COMPONENTS",
            "proof": "The exact official requirement states applying normative pronunciation and stress. The independently accepted stress authority explicitly excludes non-stress pronunciation, while the independently accepted pronunciation authority explicitly excludes stress; together they cover the two coordinated source operations without overlap or title/route inference.",
            "exact_component_refs": component_set,
            "components": [
                {
                    "semantic_ref": PRON_REF,
                    "source_taxonomy_id": "normative_pronunciation_selection",
                    "independent_evidence_refs": PRON_EVIDENCE,
                    "evidence_count": len(PRON_EVIDENCE),
                },
                {
                    "semantic_ref": STRESS_REF,
                    "source_taxonomy_id": "normative_stress_selection",
                    "candidate_ref": "candidate-018",
                    "independent_evidence_refs": STRESS_EVIDENCE,
                    "evidence_count": len(STRESS_EVIDENCE),
                },
            ],
            "component_count": 2,
            "independent_evidence_items": 9,
            "missing_source_components": [],
            "overlapping_component_boundaries": [],
        },
        "acceptance_readiness": {
            "exact_source_identity_verified": True,
            "target_still_in_current_v2_remainder": True,
            "all_source_components_have_independently_accepted_semantic_owners": True,
            "all_components_have_component_specific_independent_evidence": True,
            "separate_object_acceptance_required": True,
            "object_accepted_by_this_review": False,
        },
        "policy": {
            "review_is_acceptance": False,
            "review_can_reduce_object_counts": False,
            "review_can_create_school_identity": False,
            "review_can_create_ru_semantic_identity": False,
            "task_module_route_title_keyword_fuzzy_or_embedding_inference_allowed": False,
            "generic_orthoepy_attempt_can_emit_exact_component_mastery": False,
            "stress_evidence_can_substitute_for_pronunciation": False,
            "pronunciation_evidence_can_substitute_for_stress": False,
            "component_specific_independent_evidence_required": True,
        },
        "summary": {
            "reviewed_admission_units": 1,
            "reviewed_requirements": 1,
            "exact_component_set_ready_units": 1,
            "exact_component_set_ready_requirements": 1,
            "exact_component_refs": 2,
            "independent_evidence_items": 9,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "new_school_canonical_identities": 0,
            "new_ru_semantic_identities": 0,
            "false_exact_mastery_admissions": 0,
            "current_subject_review_units_remaining": 1287,
            "current_subject_review_requirements_remaining": 1362,
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
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        summary = result["summary"]
        print("RU02_ORTHOEPY_EXACT_OBJECT_BINDING_REVIEW=PASS")
        print(f"SELECTED_UNIT={TARGET_UNIT}")
        print("EXACT_COMPONENT_REFS=2")
        print("INDEPENDENT_EVIDENCE_ITEMS=9")
        print("MISSING_SOURCE_COMPONENTS=0")
        print("OBJECT_CLOSURES_BY_REVIEW=0")
        print(f"CURRENT_SUBJECT_REVIEW_UNITS_REMAINING={summary['current_subject_review_units_remaining']}")
        print(f"CURRENT_SUBJECT_REVIEW_REQUIREMENTS_REMAINING={summary['current_subject_review_requirements_remaining']}")
        print(f"normalized_sha256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
