#!/usr/bin/env python3
"""Fail-closed learner-content/evidence readiness for RU01 sound-composition determination."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
OWNER = HERE / "RU01-OGE-2-1-SOUND-COMPOSITION-OWNER-RESOLUTION-v0.1.json"
CONTENT = PROGRAM / "production-learning-content" / "RU-PROG-01-SOUND-COMPOSITION-WAVE-004-v0.1.json"
BASE_CONTENT = PROGRAM / "production-learning-content" / "RU-PROG-01-PHONETICS-GRAPHICS-WAVE-001-v0.1.json"
TRANSCRIPTION_CONTENT = PROGRAM / "production-learning-content" / "RU-PROG-01-PHONETIC-TRANSCRIPTION-WAVE-002-v0.1.json"
SOUND_CHANGES_CONTENT = PROGRAM / "production-learning-content" / "RU-PROG-01-SOUND-CHANGES-WAVE-003-v0.1.json"
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v16.py"

CANDIDATE = "ru-phonetics-sound-composition-determination"
TARGET_UNIT = "RAU-b6f5dff93864358672bc"
TARGET_REQUIREMENT = "RSK-OGE_COD-2-1-P010"
TARGET_LOCATOR = "FIPI-OGE-RU-2026-FINAL/OGE_COD p.10 2.1"
CURRENT_SHA = "43ccb3968f98540d32e54ef99c1c73b864c55caea22289b9e2764d77e32fc147"
OWNER_NORMALIZED_SHA = "c3c01a40b7877ba400bebe2e0de6a2ea503bca4b00eae38b96a02432d4d6bac9"
OWNER_GATE_RUN = 34248497114
OWNER_GATE_HEAD = "a975713626334adb4c2e459ed66b2235d1dec3b7"
EXPECTED_VERIFICATION_IDS = [f"p01-u6-v{i}" for i in range(1, 7)]
EXPECTED_SKILLS = {
    "determine_ordered_sound_sequence",
    "count_sounds_without_counting_letters",
    "distinguish_sound_composition_from_letter_composition",
    "separate_composition_from_feature_classification",
    "distinguish_sound_composition_from_adjacent_semantics",
    "recognize_fail_closed_pronunciation_boundary",
}
EXPECTED_CURRENT = {
    "accepted_authorities": 63,
    "subject_disposed_units_total": 41,
    "subject_disposed_requirements_total": 41,
    "subject_review_units_remaining": 1275,
    "subject_review_requirements_remaining": 1350,
    "accepted_bounded_ru_subject_semantics": 68,
    "accepted_bounded_ru_semantics_total": 77,
    "false_exact_mastery_admissions": 0,
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verification_ids(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(item.get("id"))
        for unit in data.get("units") or []
        if isinstance(unit, dict)
        for item in unit.get("independent_verification") or []
        if isinstance(item, dict)
    }


def build_readiness() -> dict[str, Any]:
    owner = json.loads(OWNER.read_text(encoding="utf-8"))
    asserted_owner_sha = owner.get("normalized_sha256")
    if asserted_owner_sha != OWNER_NORMALIZED_SHA:
        raise ValueError("owner-resolution normalized SHA drift")
    owner_without_sha = dict(owner)
    owner_without_sha.pop("normalized_sha256", None)
    if hashlib.sha256(canonical_json(owner_without_sha)).hexdigest() != OWNER_NORMALIZED_SHA:
        raise ValueError("owner-resolution embedded SHA mismatch")
    if owner.get("status") != "BOUNDED_SOURCE_BACKED_SOUND_COMPOSITION_OWNER_RESOLUTION_NO_ADMISSION":
        raise ValueError("owner-resolution status drift")
    proposed = owner.get("proposed_owner") or {}
    if proposed.get("semantic_id") != CANDIDATE or proposed.get("status") != "PROPOSED_NOT_CANONICAL":
        raise ValueError("candidate owner drift")
    target = owner.get("target_object") or {}
    if (target.get("admission_unit_id"), target.get("requirement_id"), target.get("source_locator")) != (
        TARGET_UNIT, TARGET_REQUIREMENT, TARGET_LOCATOR
    ):
        raise ValueError("target object drift")
    exact = owner.get("exact_source_requirement") or {}
    if exact.get("already_bound_component_ref") != "ru-phonetics-vowel-consonant-features":
        raise ValueError("existing partial component drift")
    if exact.get("remaining_exact_blocker") != "SOUND_COMPOSITION_FACET_UNBOUND":
        raise ValueError("sound-composition blocker drift")
    search = owner.get("existing_owner_search") or {}
    if search.get("exact_current_sound_composition_owner_found") is not False:
        raise ValueError("unexpected exact owner appeared in pinned resolution")
    boundary = owner.get("acceptance_boundary") or {}
    if boundary.get("semantic_admission_effect") != "NONE" or boundary.get("object_closure_effect") != "NONE":
        raise ValueError("owner resolution unexpectedly accepts")
    if boundary.get("false_exact_mastery") != 0:
        raise ValueError("owner-resolution false exact mastery drift")

    current = runpy.run_path(str(CURRENT))["build_progress"]()
    if current.get("normalized_sha256") != CURRENT_SHA:
        raise ValueError("current-v16 normalized SHA drift")
    summary = current.get("progress_summary") or {}
    if len(current.get("accepted_authorities") or []) != EXPECTED_CURRENT["accepted_authorities"]:
        raise ValueError("current-v16 accepted authority count drift")
    for key, value in EXPECTED_CURRENT.items():
        if key == "accepted_authorities":
            continue
        if summary.get(key) != value:
            raise ValueError(f"current-v16 aggregate drift: {key}")
    group = [g for g in current.get("semantic_review_groups") or [] if g.get("group_id") == "RUS-SEM-REVIEW-001"]
    if len(group) != 1:
        raise ValueError("RU01 review group drift")
    accepted_sets = group[0].get("accepted_component_sets") or []
    if any(
        row.get("admission_unit_id") == TARGET_UNIT or row.get("requirement_id") == TARGET_REQUIREMENT
        for row in accepted_sets
        if isinstance(row, dict)
    ):
        raise ValueError("target already accepted before content readiness")

    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    if data.get("schema_version") != "0.1.0" or data.get("status") != "CONTENT_AND_EVIDENCE_READY_SEMANTIC_ACCEPTANCE_REQUIRED":
        raise ValueError("content schema/status drift")
    if data.get("subject") != "russian" or data.get("module_id") != "RU-PROG-01":
        raise ValueError("content module drift")
    provenance = [row for row in data.get("source_provenance") or [] if isinstance(row, dict)]
    owner_refs = [row for row in provenance if row.get("kind") == "bounded_owner_resolution"]
    if len(owner_refs) != 1 or owner_refs[0].get("ref") != "russian-program/subject-admission/RU01-OGE-2-1-SOUND-COMPOSITION-OWNER-RESOLUTION-v0.1.json":
        raise ValueError("owner provenance drift")
    gates = [row for row in provenance if row.get("kind") == "exact_head_prerequisite_gate"]
    if len(gates) != 1:
        raise ValueError("owner gate provenance missing")
    gate = gates[0]
    if (gate.get("run_id"), gate.get("head_sha"), gate.get("conclusion")) != (OWNER_GATE_RUN, OWNER_GATE_HEAD, "SUCCESS"):
        raise ValueError("owner gate exact-head provenance drift")
    official = [row for row in provenance if row.get("kind") == "official_codifier"]
    if len(official) != 1:
        raise ValueError("official source pin missing")
    pin = official[0]
    expected_pin = {
        "document_id": "OGE_COD",
        "document_sha256": "2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a",
        "page": 10,
        "code": "2.1",
        "source_locator": TARGET_LOCATOR,
    }
    for key, value in expected_pin.items():
        if pin.get(key) != value:
            raise ValueError(f"official source pin drift: {key}")

    identity = data.get("identity_boundary") or {}
    if identity.get("proposed_semantic_id") != CANDIDATE or identity.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise ValueError("content candidate identity drift")
    if identity.get("vowel_consonant_features_existing_partial_component_preserved") is not True:
        raise ValueError("existing partial component not preserved")
    for key in (
        "sound_letter_relation_semantic_may_substitute",
        "vowel_consonant_features_semantic_may_substitute",
        "word_analysis_semantic_may_substitute",
        "phonetic_transcription_semantic_may_substitute",
        "sound_changes_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "normative_stress_semantic_may_substitute",
        "generic_ru01_result_can_emit_exact_component_mastery",
    ):
        if identity.get(key) is not False:
            raise ValueError(f"identity boundary opened: {key}")

    units = [row for row in data.get("units") or [] if isinstance(row, dict)]
    if len(units) != 1 or units[0].get("proposed_semantic_id") != CANDIDATE:
        raise ValueError("sound-composition learner unit must be singular and exact")
    unit = units[0]
    verification = [row for row in unit.get("independent_verification") or [] if isinstance(row, dict)]
    ids = [str(row.get("id")) for row in verification]
    if ids != EXPECTED_VERIFICATION_IDS or len(set(ids)) != len(ids):
        raise ValueError("sound-composition verification identity drift")
    skills = {str(row.get("skill")) for row in verification}
    if skills != EXPECTED_SKILLS:
        raise ValueError("sound-composition verification skill coverage drift")
    if sum(1 for row in verification if row.get("type") == "constructed_response") < 5:
        raise ValueError("sound-composition evidence needs at least five constructed responses")

    adjacent = verification_ids(BASE_CONTENT) | verification_ids(TRANSCRIPTION_CONTENT) | verification_ids(SOUND_CHANGES_CONTENT)
    expected_adjacent = {
        "p01-u1-v1", "p01-u1-v2", "p01-u2-v1", "p01-u2-v2", "p01-u3-v1", "p01-u3-v2",
        "p01-u4-v1", "p01-u4-v2", "p01-u4-v3", "p01-u4-v4", "p01-u4-v5",
        "p01-u5-v1", "p01-u5-v2", "p01-u5-v3", "p01-u5-v4", "p01-u5-v5", "p01-u5-v6",
    }
    if adjacent != expected_adjacent:
        raise ValueError("adjacent RU01 verification inventory drift")
    overlap = sorted(set(ids) & adjacent)
    if overlap:
        raise ValueError("adjacent RU01 evidence reused for sound composition")

    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref") != CANDIDATE or peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise ValueError("PEIS semantic identity/status drift")
    if peis.get("verification_ids") != EXPECTED_VERIFICATION_IDS:
        raise ValueError("PEIS verification IDs drift")
    for key in ("requires_exact_item_identity", "requires_registered_user_identity_ref", "requires_server_owned_received_at"):
        if peis.get(key) is not True:
            raise ValueError(f"registered/server-owned evidence boundary weakened: {key}")
    for key in ("mastery_emission_before_semantic_acceptance", "object_mastery_emission_before_exact_object_acceptance"):
        if peis.get(key) is not False:
            raise ValueError(f"premature mastery boundary opened: {key}")
    if peis.get("existing_partial_vowel_consonant_component_is_not_modified") is not True:
        raise ValueError("existing partial component mutation boundary drift")
    if peis.get("false_exact_mastery_admissions") != 0:
        raise ValueError("PEIS false exact mastery drift")

    forbidden = [str(x).lower() for x in ((unit.get("tutor_grounding") or {}).get("forbidden") or [])]
    required_fragments = [
        "normative pronunciation",
        "p01-u1-v1",
        "ru-phonetics-vowel-consonant-features",
        "separate semantic acceptance",
        "rsk-oge_cod-2-1-p010",
        "generic ru01",
    ]
    for fragment in required_fragments:
        if not any(fragment in row for row in forbidden):
            raise ValueError(f"tutor fail-closed boundary missing: {fragment}")

    release = data.get("release_boundary") or {}
    expected_release = {
        "semantic_acceptance_effect": "NONE",
        "object_acceptance_effect": "NONE",
        "school_canonical_identity_created": False,
        "existing_partial_component_modified": False,
        "false_exact_mastery_admissions": 0,
        "public_runtime_change": False,
        "production_peis_write": False,
    }
    if release != expected_release:
        raise ValueError("release boundary drift")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_SOUND_COMPOSITION_CONTENT_AND_EVIDENCE_READY_NOT_ACCEPTED",
        "module_id": "RU-PROG-01",
        "candidate_semantic_id": CANDIDATE,
        "owner_resolution_sha256": sha256_path(OWNER),
        "owner_resolution_normalized_sha256": OWNER_NORMALIZED_SHA,
        "owner_resolution_exact_head_gate": {
            "run_id": OWNER_GATE_RUN,
            "head_sha": OWNER_GATE_HEAD,
            "conclusion": "SUCCESS",
        },
        "content_sha256": sha256_path(CONTENT),
        "target": {
            "admission_unit_id": TARGET_UNIT,
            "requirement_id": TARGET_REQUIREMENT,
            "source_locator": TARGET_LOCATOR,
            "already_bound_component_ref_preserved": "ru-phonetics-vowel-consonant-features",
            "remaining_component_candidate": CANDIDATE,
        },
        "learner_content": {
            "dedicated_candidate_content_unit_present": True,
            "original_eksamio_content": True,
            "independent_verification_ids": ids,
            "independent_verification_count": len(ids),
            "covered_skills": sorted(skills),
        },
        "evidence_independence": {
            "adjacent_existing_evidence_ids_checked": sorted(adjacent),
            "sound_composition_evidence_ids": ids,
            "overlap": overlap,
            "adjacent_semantic_evidence_reused": False,
            "generic_ru01_evidence_can_substitute": False,
        },
        "policy": {
            "content_readiness_is_semantic_acceptance": False,
            "content_readiness_is_object_acceptance": False,
            "candidate_is_canonical_before_separate_acceptance": False,
            "existing_partial_component_is_modified": False,
            "normative_pronunciation_or_stress_inferred": False,
            "false_exact_mastery_admissions": 0,
        },
        "current_launch_aggregate_unchanged": EXPECTED_CURRENT,
        "summary": {
            "dedicated_candidate_content_units": 1,
            "component_specific_independent_verification_items": len(ids),
            "adjacent_semantic_evidence_reused": 0,
            "semantic_admissions": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "new_school_canonical_identities": 0,
            "false_exact_mastery_admissions": 0,
        },
        "next_exact_work": {
            "separate_bounded_subject_semantic_acceptance_required": True,
            "semantic_acceptance_must_bind_only_p01_u6_evidence": True,
            "separate_exact_object_component_set_acceptance_required_after_semantic_acceptance": True,
            "target_remains_pending_until_its_own_acceptance_gate_passes": True,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_readiness()
    text = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    if args.emit:
        print(text)
    else:
        print("RUSSIAN_RU01_SOUND_COMPOSITION_CONTENT_READINESS=PASS")
        print("CANDIDATE=" + CANDIDATE)
        print("TARGET=" + TARGET_UNIT + "/" + TARGET_REQUIREMENT)
        print("INDEPENDENT_EVIDENCE_ITEMS=6")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_ACCEPTANCES=0")
        print("FALSE_EXACT_MASTERY=0")
        print("NORMALIZED_SHA256=" + result["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
