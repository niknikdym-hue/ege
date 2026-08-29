#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
CONTENT = PROGRAM / "production-learning-content/RU-PROG-09-SYNTAX-NORMS-WAVE-001-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

EXPECTED = {
    "candidate-028": ("government_case_norm", "ru-syntax-government-case-norm"),
    "candidate-029": ("indirect_speech_construction", "ru-syntax-indirect-speech-norm"),
    "candidate-030": ("uncoordinated_apposition_construction", "ru-syntax-uncoordinated-apposition-norm"),
    "candidate-031": ("gerundial_construction_norm", "ru-syntax-gerundial-agent-norm"),
    "candidate-032": ("homogeneous_members_construction", "ru-syntax-homogeneous-members-norm"),
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def require_nonempty_strings(values: Any, *, minimum: int, label: str) -> None:
    if not isinstance(values, list) or len(values) < minimum:
        raise AssertionError(f"{label} requires at least {minimum} entries")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise AssertionError(f"{label} contains empty/non-string entry")


def main() -> int:
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    if data.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise AssertionError("RU09 content self-admitted or status drifted")
    if data.get("module_id") != "RU-PROG-09" or data.get("subject") != "russian":
        raise AssertionError("RU09 content module/subject drift")
    copyright_guard = data.get("copyright_guard") or {}
    if copyright_guard.get("source_passages_copied") != 0 or copyright_guard.get("commercial_textbook_bytes_in_git") != 0:
        raise AssertionError("RU09 copyright/source-byte guard weakened")
    identity = data.get("identity_boundary") or {}
    if identity.get("candidate_status_after_content") != "DRAFT_NOT_ADMITTED":
        raise AssertionError("RU09 content promoted draft candidate")
    if identity.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError("RU09 proposed semantic self-canonicalized")
    if identity.get("object_level_admission_effect") != "NONE_UNTIL_SEPARATE_EXACT_OBJECT_BINDING":
        raise AssertionError("RU09 content claimed object closure")
    if identity.get("generic_module_attempt_can_emit_exact_component_mastery") is not False:
        raise AssertionError("generic RU09 attempt can emit exact mastery")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    units = data.get("units")
    if not isinstance(units, list) or len(units) != 5:
        raise AssertionError("RU09 content must contain exactly five bounded units")
    by_candidate = {str(row.get("candidate_ref")): row for row in units if isinstance(row, dict)}
    if set(by_candidate) != set(EXPECTED):
        raise AssertionError("RU09 content candidate set drift")
    semantic_ids = [str(row.get("proposed_semantic_id") or "") for row in units]
    if len(set(semantic_ids)) != 5 or any(not semantic_id.startswith("ru-syntax-") for semantic_id in semantic_ids):
        raise AssertionError("RU09 proposed semantic IDs invalid/non-unique")

    verification_ids: set[str] = set()
    practice_ids: set[str] = set()
    for candidate_ref, (taxonomy_id, semantic_id) in EXPECTED.items():
        unit = by_candidate[candidate_ref]
        if unit.get("source_taxonomy_id") != taxonomy_id:
            raise AssertionError(f"RU09 taxonomy binding drift: {candidate_ref}")
        if unit.get("proposed_semantic_id") != semantic_id:
            raise AssertionError(f"RU09 proposed semantic ID drift: {candidate_ref}")

        candidates = [
            row for row in objects
            if row.get("source_system") == "semantic_candidate" and row.get("source_id") == candidate_ref
        ]
        if len(candidates) != 1:
            raise AssertionError(f"RU09 candidate inventory mismatch: {candidate_ref}")
        candidate = candidates[0]
        if candidate.get("authority_status") != "current" or candidate.get("review_status") != "draft":
            raise AssertionError(f"RU09 candidate no longer current/draft: {candidate_ref}")
        if candidate.get("candidate_canonical_owner") != candidate_ref:
            raise AssertionError(f"RU09 candidate owner drift: {candidate_ref}")
        if candidate.get("current_semantic_refs") != [taxonomy_id]:
            raise AssertionError(f"RU09 exact taxonomy ref drift: {candidate_ref}")
        backings = [
            row for row in objects
            if row.get("source_system") == "ege_skill_graph"
            and row.get("source_id") == taxonomy_id
            and row.get("candidate_canonical_owner") == candidate_ref
        ]
        if len(backings) != 1 or backings[0].get("authority_status") != "current" or backings[0].get("review_status") != "source_verified":
            raise AssertionError(f"RU09 source-verified taxonomy backing missing: {candidate_ref}")

        explanation = unit.get("canonical_explanation") or {}
        if not isinstance(explanation.get("short"), str) or len(explanation["short"].strip()) < 80:
            raise AssertionError(f"RU09 explanation too thin: {candidate_ref}")
        require_nonempty_strings(explanation.get("boundaries"), minimum=4, label=f"{candidate_ref} boundaries")
        require_nonempty_strings(unit.get("decision_algorithm"), minimum=5, label=f"{candidate_ref} algorithm")

        for field, minimum in (
            ("worked_examples", 3),
            ("misconceptions", 2),
            ("guided_practice", 2),
            ("independent_practice", 3),
            ("mixed_transfer_practice", 1),
            ("retention_items", 2),
            ("independent_verification", 2),
        ):
            rows = unit.get(field)
            if not isinstance(rows, list) or len(rows) < minimum or any(not isinstance(row, dict) for row in rows):
                raise AssertionError(f"RU09 {field} incomplete: {candidate_ref}")

        for field in ("guided_practice", "independent_practice", "mixed_transfer_practice", "retention_items"):
            for item in unit[field]:
                item_id = str(item.get("id") or "")
                if not item_id or item_id in practice_ids:
                    raise AssertionError(f"duplicate/missing RU09 practice id: {item_id}")
                practice_ids.add(item_id)

        for verification in unit["independent_verification"]:
            verification_id = str(verification.get("id") or "")
            if not verification_id or verification_id in verification_ids:
                raise AssertionError(f"duplicate/missing RU09 verification id: {verification_id}")
            verification_ids.add(verification_id)
            if verification.get("type") not in {"single_choice", "constructed_response"}:
                raise AssertionError(f"unsupported RU09 verification type: {candidate_ref}")

        peis = unit.get("peis_evidence") or {}
        if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
            raise AssertionError(f"RU09 unit self-admitted: {candidate_ref}")
        if peis.get("independent_verification_required") is not True:
            raise AssertionError(f"RU09 independent verification weakened: {candidate_ref}")
        if peis.get("assistance_must_be_recorded") is not True:
            raise AssertionError(f"RU09 assistance evidence guard missing: {candidate_ref}")
        if peis.get("generic_syntax_score_can_emit_exact_mastery") is not False:
            raise AssertionError(f"RU09 generic syntax score can emit mastery: {candidate_ref}")

        grounding = unit.get("tutor_grounding") or {}
        require_nonempty_strings(grounding.get("allowed"), minimum=2, label=f"{candidate_ref} Tutor allowed")
        require_nonempty_strings(grounding.get("forbidden"), minimum=2, label=f"{candidate_ref} Tutor forbidden")

    serialized = canonical_json(data)
    for forbidden in (b'"status":"CENTRAL_BRAIN_ACCEPTED', b'"semantic_ref_status":"CANONICAL"', b'"object_level_admission_effect":"CLOSED"'):
        if forbidden in serialized:
            raise AssertionError("RU09 content contains forbidden self-admission marker")

    print("RU09_SYNTAX_PRODUCTION_CONTENT=PASS")
    print("CONTENT_UNITS=5")
    print("CANDIDATES_REMAIN_DRAFT=5")
    print("PROPOSED_SEMANTICS=5")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("SOURCE_PASSAGES_COPIED=0")
    print("COMMERCIAL_TEXTBOOK_BYTES_IN_GIT=0")
    print("CONTENT_SHA256=" + hashlib.sha256(canonical_json(data)).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
