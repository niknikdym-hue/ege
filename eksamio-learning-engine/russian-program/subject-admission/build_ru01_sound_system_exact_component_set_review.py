#!/usr/bin/env python3
"""Fail-closed current-v24 exact owner/component-set review for RU01 sound system."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v24.py"
DECOMPOSITION = HERE / "build_ru01_phonetics_broad_header_clause_decomposition_review.py"
OWNER = HERE / "RU01-SOUND-SYSTEM-OWNER-RESOLUTION-v0.1.json"
VOWEL = HERE / "RU01-VOWEL-SYSTEM-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
CONSONANT = HERE / "RU01-CONSONANT-SYSTEM-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"

TARGET_UNIT = "RAU-5a6511267f156745f93c"
TARGET_REQ = "RSK-EDSOO59-4-1-P181"
TARGET_CLAUSE = "EDSOO59-P181-4.1-C"
TARGET_LOCATOR = "EDSOO-RU-5-9-2025/EDSOO59 p.181 4.1"
VOWEL_REF = "ru-phonetics-vowel-system"
CONSONANT_REF = "ru-phonetics-consonant-system"
SOUND_SYSTEM_REF = "ru-phonetics-sound-system"
VOWEL_EVIDENCE = [f"p01-u9-v{i}" for i in range(1, 6)]
CONSONANT_EVIDENCE = [f"p01-u10-v{i}" for i in range(1, 6)]

EXPECTED_SUMMARY = {
    "semantic_units_with_accepted_component_sets": 41,
    "semantic_requirements_with_accepted_component_sets": 41,
    "semantic_units_remaining_without_accepted_component_set": 1275,
    "semantic_requirements_remaining_without_accepted_component_set": 1350,
    "subject_disposed_units_total": 42,
    "subject_disposed_requirements_total": 42,
    "subject_review_units_remaining": 1274,
    "subject_review_requirements_remaining": 1349,
    "canonical_component_refs_reused_unique": 122,
    "review_groups_with_accepted_component_sets": 14,
    "accepted_bounded_ru_route_semantics": 9,
    "accepted_bounded_ru_subject_semantics": 74,
    "accepted_bounded_ru_semantics_total": 83,
    "false_exact_mastery_admissions": 0,
}

def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path.name}")
    return value

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def one_decision(doc: dict[str, Any], semantic_ref: str) -> dict[str, Any]:
    rows = [
        row for row in doc.get("decisions", [])
        if isinstance(row, dict) and row.get("accepted_semantic_id") == semantic_ref
    ]
    if len(rows) != 1:
        raise ValueError(f"accepted semantic decision not unique: {semantic_ref}")
    return rows[0]

def accepted_semantics() -> set[str]:
    refs: set[str] = set()
    for path in sorted(HERE.glob("*.json")):
        try:
            doc = load(path)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            continue
        for row in doc.get("decisions", []):
            if isinstance(row, dict) and row.get("accepted_semantic_id"):
                refs.add(str(row["accepted_semantic_id"]))
    return refs

def build_review() -> dict[str, Any]:
    current = runpy.run_path(str(CURRENT))["build_progress"]()
    summary = current.get("progress_summary") or {}
    for key, expected in EXPECTED_SUMMARY.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v24 aggregate drift: {key}")
    if len(current.get("accepted_authorities") or []) != 70:
        raise ValueError("current-v24 accepted authority count drift")
    predecessor = current.get("newly_accepted_bounded_subject_semantic") or {}
    if predecessor.get("semantic_id") != "ru-phonetics-sound-characterization":
        raise ValueError("current-v24 predecessor semantic drift")
    if predecessor.get("parent_object_count_requiring_future_complete_component_set_acceptance") != 1:
        raise ValueError("current-v24 parent frontier drift")

    decomposition = runpy.run_path(str(DECOMPOSITION))["build_review"]()
    rows = {
        str(row.get("clause_id")): row
        for row in decomposition.get("records", [])
        if isinstance(row, dict)
    }
    clause = rows.get(TARGET_CLAUSE)
    if clause is None:
        raise ValueError("sound-system exact source clause missing")
    if clause.get("requirement_id") != TARGET_REQ or clause.get("admission_unit_id") != TARGET_UNIT:
        raise ValueError("sound-system parent identity drift")
    if clause.get("source_id") != "EDSOO-RU-5-9-2025" or clause.get("source_locator") != "EDSOO59 p.181 4.1":
        raise ValueError("sound-system source identity drift")
    if clause.get("official_clause_ru") != "характеризовать систему звуков":
        raise ValueError("sound-system official clause drift")
    if clause.get("owner_match_status") != "UNBOUND_EXACT_CLAUSE" or clause.get("current_owner_refs") != []:
        raise ValueError("historical exact-owner boundary drift")

    refs = accepted_semantics()
    if SOUND_SYSTEM_REF in refs:
        raise ValueError("sound-system unexpectedly already accepted")

    vowel = load(VOWEL)
    consonant = load(CONSONANT)
    v = one_decision(vowel, VOWEL_REF)
    c = one_decision(consonant, CONSONANT_REF)
    if v.get("independent_verification_item_ids") != VOWEL_EVIDENCE:
        raise ValueError("vowel-system evidence drift")
    if c.get("independent_verification_item_ids") != CONSONANT_EVIDENCE:
        raise ValueError("consonant-system evidence drift")
    if set(VOWEL_EVIDENCE) & set(CONSONANT_EVIDENCE):
        raise ValueError("vowel/consonant evidence lineages overlap")
    if v.get("parent_object_binding_status") != "NOT_BOUND_AS_COMPLETE_COMPONENT_SET_TO_EITHER_BROAD_4_1_PARENT_OBJECT":
        raise ValueError("vowel parent-boundary drift")
    if c.get("parent_object_binding_status") != "NOT_BOUND_AS_COMPLETE_COMPONENT_SET_TO_EITHER_BROAD_4_1_PARENT_OBJECT":
        raise ValueError("consonant parent-boundary drift")

    owner = load(OWNER)
    if owner.get("status") != "CENTRAL_BRAIN_RU01_SOUND_SYSTEM_OWNER_RESOLUTION_CANDIDATE_NOT_ACCEPTED":
        raise ValueError("sound-system owner-resolution status drift")
    target = owner.get("target") or {}
    expected_target = {
        "admission_unit_id": TARGET_UNIT,
        "requirement_id": TARGET_REQ,
        "source_id": "EDSOO-RU-5-9-2025",
        "document_id": "EDSOO59",
        "source_locator": TARGET_LOCATOR,
        "clause_id": TARGET_CLAUSE,
        "official_clause_ru": "характеризовать систему звуков",
        "module_id": "RU-PROG-01",
    }
    if target != expected_target:
        raise ValueError("sound-system owner target drift")
    search = owner.get("existing_owner_search") or {}
    if search.get("resolution") != "NO_EXACT_CURRENT_SINGLE_SOUND_SYSTEM_OWNER":
        raise ValueError("sound-system exact owner search drift")
    if search.get("exact_single_owner_refs") != []:
        raise ValueError("sound-system exact owner unexpectedly present")
    proposed = owner.get("proposed_owner") or {}
    if proposed.get("semantic_id") != SOUND_SYSTEM_REF or proposed.get("status") != "PROPOSED_NOT_CANONICAL":
        raise ValueError("sound-system proposed owner drift")
    if proposed.get("canonical_school_registry_mutation") is not False or proposed.get("parallel_registry_creation") is not False:
        raise ValueError("sound-system proposed owner mutated canonical registry")

    candidate = owner.get("source_backed_component_candidate") or {}
    if candidate.get("candidate_component_refs") != [VOWEL_REF, CONSONANT_REF]:
        raise ValueError("sound-system candidate component refs drift")
    if candidate.get("component_evidence_items") != 10 or candidate.get("component_evidence_overlap") != []:
        raise ValueError("sound-system component evidence boundary drift")
    if candidate.get("exact_parent_component_set_proven") is not False:
        raise ValueError("sound-system parent component set was auto-proven")
    if (owner.get("summary") or {}).get("integrated_sound_system_evidence_items") != 0:
        raise ValueError("sound-system integrated evidence unexpectedly present")

    for group in current.get("semantic_review_groups") or []:
        if not isinstance(group, dict):
            continue
        for row in group.get("accepted_component_sets") or []:
            if not isinstance(row, dict):
                continue
            if row.get("admission_unit_id") == TARGET_UNIT or row.get("requirement_id") == TARGET_REQ:
                raise ValueError("sound-system parent object already has an accepted component set")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_SOUND_SYSTEM_EXACT_COMPONENT_SET_REVIEW_COMPLETE_COMPONENT_CANDIDATE_NOT_ACCEPTED",
        "base_current_label": "current-v24",
        "base_current_normalized_sha256": current.get("normalized_sha256"),
        "selected_source_clause": expected_target,
        "exact_current_owner_search": {
            "result": "NO_EXACT_CURRENT_SINGLE_SOUND_SYSTEM_OWNER",
            "accepted_sound_system_owner_refs": [],
            "search_basis": "EXACT_CURRENT_V24_ACCEPTED_AUTHORITIES_ONLY; NO_TITLE_ROUTE_TASK_KEYWORD_FUZZY_OR_EMBEDDING_INFERENCE",
        },
        "source_backed_component_candidate": {
            "candidate_component_refs": [VOWEL_REF, CONSONANT_REF],
            "component_status": "BOTH_INDEPENDENTLY_ACCEPTED_BOUNDED_SUBJECT_SEMANTICS",
            "vowel_source_clauses": ["EDSOO59-P187-4.1.1", "OGE-COD-P020-4.1.1"],
            "consonant_source_clauses": ["EDSOO59-P187-4.1.2", "OGE-COD-P020-4.1.2"],
            "component_specific_independent_evidence_refs": VOWEL_EVIDENCE + CONSONANT_EVIDENCE,
            "component_specific_independent_evidence_items": 10,
            "component_evidence_overlap": [],
            "exact_parent_component_set_ready": False,
            "blocker": "NO_DEDICATED_INTEGRATED_SOUND_SYSTEM_EVIDENCE_FOR_EDSOO59_P181_4_1_C",
        },
        "next_required_action": {
            "action": "BUILD_DEDICATED_SOURCE_BOUND_RU01_SOUND_SYSTEM_LEARNER_CONTENT_WITH_NEW_INTEGRATED_INDEPENDENT_VERIFICATION_THEN_RUN_SEPARATE_CONTENT_ADEQUACY_AND_BOUNDED_SEMANTIC_ACCEPTANCE",
            "minimum_distinct_integrated_verification_items": 5,
            "reuse_component_evidence_as_parent_evidence_without_new_lineage": False,
            "separate_parent_object_acceptance_after_semantic_acceptance": True,
        },
        "policy": {
            "review_is_acceptance": False,
            "review_can_create_school_identity": False,
            "review_can_create_ru_semantic_identity": False,
            "review_can_reduce_object_counts": False,
            "two_component_titles_can_auto_create_sound_system_owner": False,
            "component_presence_can_auto_close_parent": False,
            "generic_ru01_attempt_can_emit_exact_sound_system_mastery": False,
            "anonymous_or_device_only_evidence_can_be_canonical": False,
            "registered_user_identity_ref_required_for_future_canonical_evidence": True,
            "server_owned_received_at_required_for_future_canonical_evidence": True,
            "durable_evidence_event_required_for_future_canonical_evidence": True,
        },
        "summary": {
            "reviewed_admission_units": 1,
            "reviewed_requirements": 1,
            "reviewed_exact_source_clauses": 1,
            "exact_single_current_owner_refs": 0,
            "candidate_component_refs": 2,
            "component_specific_independent_evidence_items": 10,
            "integrated_sound_system_evidence_items": 0,
            "exact_component_set_ready_units": 0,
            "exact_component_set_ready_requirements": 0,
            "semantic_admissions": 0,
            "object_level_closures": 0,
            "exact_mastery_admissions": 0,
            "false_exact_mastery_admissions": 0,
            "current_subject_review_units_remaining": 1274,
            "current_subject_review_requirements_remaining": 1349,
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
        s = result["summary"]
        print("RU01_SOUND_SYSTEM_EXACT_COMPONENT_SET_REVIEW=PASS")
        print("EXACT_SINGLE_CURRENT_OWNER_REFS=0")
        print("CANDIDATE_COMPONENT_REFS=2")
        print("COMPONENT_SPECIFIC_EVIDENCE_ITEMS=10")
        print("INTEGRATED_SOUND_SYSTEM_EVIDENCE_ITEMS=0")
        print("EXACT_COMPONENT_SET_READY_UNITS=0")
        print(f"SUBJECT_REVIEW_UNITS_REMAINING={s['current_subject_review_units_remaining']}")
        print(f"SUBJECT_REVIEW_REQUIREMENTS_REMAINING={s['current_subject_review_requirements_remaining']}")
        print("FALSE_EXACT_MASTERY=0")
        print("NORMALIZED_SHA256=" + result["normalized_sha256"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
