#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT = PROGRAM / "production-learning-content/RU-PROG-09-EDSOO59-P222-8-1-WAVE-002-v0.1.json"
OWNER = HERE / "RU09-EDSOO59-P222-8-1-SOURCE-BACKED-OWNER-RESOLUTION-v0.1.json"

EXPECTED = {
    "edsoo59-p222-8-1-sentence-formulation-means": {
        "semantic_id": "ru-syntax-sentence-formulation-means",
        "verification_ids": {"p09-u6-v1", "p09-u6-v2", "p09-u6-v3", "p09-u6-v4"},
        "axes": {"logical_stress", "punctuation_boundary", "intonation_boundary", "cross_form_alignment"},
    },
    "edsoo59-p222-8-1-inversion-norm": {
        "semantic_id": "ru-syntax-inversion-norm",
        "verification_ids": {"p09-u7-v1", "p09-u7-v2", "p09-u7-v3", "p09-u7-v4"},
        "axes": {"normative_vs_error", "ambiguity_detection", "control_reordering", "contextual_norm"},
    },
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def require_list(value: Any, minimum: int, label: str) -> list[Any]:
    if not isinstance(value, list) or len(value) < minimum:
        raise AssertionError(f"{label} requires at least {minimum} entries")
    return value


def main() -> int:
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    owner = json.loads(OWNER.read_text(encoding="utf-8"))

    if data.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise AssertionError("candidate content self-admitted")
    if data.get("module_id") != "RU-PROG-09" or data.get("subject") != "russian":
        raise AssertionError("RU09 module/subject drift")

    source_rows = data.get("source_provenance") or []
    official = next((row for row in source_rows if row.get("kind") == "official_program_scope"), None)
    if not official:
        raise AssertionError("official source provenance missing")
    if official.get("document_sha256") != "1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d":
        raise AssertionError("official source digest drift")
    if official.get("exact_text") != "Средства оформления предложения в устной и письменной речи (интонация, логическое ударение, знаки препинания). Нормы использования инверсии":
        raise AssertionError("official p222 8.1 text drift")

    guard = data.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes_in_git") != 0:
        raise AssertionError("copyright/source-byte guard weakened")
    if guard.get("learner_explanations") != "ORIGINAL_EKSAMIO" or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("learner content originality marker missing")

    identity = data.get("identity_boundary") or {}
    expected_identity = {
        "candidate_status_after_content": "DRAFT_NOT_ADMITTED",
        "semantic_ref_status": "PROPOSED_NOT_CANONICAL",
        "object_level_admission_effect": "NONE_UNTIL_SEPARATE_EXACT_OBJECT_BINDING",
        "generic_module_attempt_can_emit_exact_component_mastery": False,
        "future_canonical_evidence_requires_registered_user_identity_ref": True,
        "content_or_verification_presence_self_admits_semantics": False,
    }
    for key, expected in expected_identity.items():
        if identity.get(key) != expected:
            raise AssertionError(f"identity boundary drift: {key}")

    proposed_owner_rows = {
        row.get("source_component_id"): row
        for row in owner.get("proposed_owners", [])
        if isinstance(row, dict)
    }
    if set(proposed_owner_rows) != set(EXPECTED):
        raise AssertionError("owner candidate set drift")

    units = data.get("units")
    if not isinstance(units, list) or len(units) != 2:
        raise AssertionError("p222 content must contain exactly two bounded units")
    by_component = {
        row.get("source_component_id"): row
        for row in units
        if isinstance(row, dict)
    }
    if set(by_component) != set(EXPECTED):
        raise AssertionError("content component set drift")

    seen_ids: set[str] = set()
    for component_id, spec in EXPECTED.items():
        owner_row = proposed_owner_rows[component_id]
        if owner_row.get("status") != "PROPOSED_NOT_CANONICAL":
            raise AssertionError(f"owner self-admitted: {component_id}")
        if owner_row.get("proposed_semantic_id") != spec["semantic_id"]:
            raise AssertionError(f"owner semantic id drift: {component_id}")
        if owner_row.get("existing_exact_owner_found") is not False:
            raise AssertionError(f"unexpected exact owner claim: {component_id}")

        unit = by_component[component_id]
        if unit.get("proposed_semantic_id") != spec["semantic_id"]:
            raise AssertionError(f"content semantic id drift: {component_id}")

        explanation = unit.get("canonical_explanation") or {}
        if not isinstance(explanation.get("short"), str) or len(explanation["short"].strip()) < 120:
            raise AssertionError(f"explanation too thin: {component_id}")
        require_list(explanation.get("boundaries"), 5, f"{component_id} boundaries")
        require_list(unit.get("decision_algorithm"), 5, f"{component_id} algorithm")

        for field, minimum in (
            ("worked_examples", 3),
            ("misconceptions", 2),
            ("guided_practice", 2),
            ("independent_practice", 3),
            ("mixed_transfer_practice", 1),
            ("retention_items", 2),
            ("independent_verification", 4),
        ):
            rows = require_list(unit.get(field), minimum, f"{component_id} {field}")
            if any(not isinstance(row, dict) for row in rows):
                raise AssertionError(f"{component_id} {field} contains non-object")

        for field in ("guided_practice", "independent_practice", "mixed_transfer_practice", "retention_items"):
            for item in unit[field]:
                item_id = str(item.get("id") or "")
                if not item_id or item_id in seen_ids:
                    raise AssertionError(f"duplicate/missing practice id: {item_id}")
                seen_ids.add(item_id)

        verifications = unit["independent_verification"]
        ids = {str(item.get("id") or "") for item in verifications}
        axes = {str(item.get("component_evidence_axis") or "") for item in verifications}
        if ids != spec["verification_ids"]:
            raise AssertionError(f"verification id set drift: {component_id}")
        if axes != spec["axes"]:
            raise AssertionError(f"component evidence axis set drift: {component_id}")
        for item in verifications:
            item_id = str(item.get("id") or "")
            if item_id in seen_ids:
                raise AssertionError(f"duplicate verification id: {item_id}")
            seen_ids.add(item_id)
            if item.get("type") not in {"single_choice", "constructed_response"}:
                raise AssertionError(f"unsupported verification type: {item_id}")

        peis = unit.get("peis_evidence") or {}
        if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
            raise AssertionError(f"unit self-admitted: {component_id}")
        if peis.get("independent_verification_required") is not True:
            raise AssertionError(f"independent verification weakened: {component_id}")
        if peis.get("component_specific_evidence_required") is not True:
            raise AssertionError(f"component evidence guard missing: {component_id}")
        if peis.get("assistance_must_be_recorded") is not True:
            raise AssertionError(f"assistance evidence guard missing: {component_id}")
        if peis.get("registered_user_identity_ref_required_for_future_canonical_evidence") is not True:
            raise AssertionError(f"registered identity guard missing: {component_id}")
        if peis.get("generic_syntax_score_can_emit_exact_mastery") is not False:
            raise AssertionError(f"generic score can emit exact mastery: {component_id}")

        grounding = unit.get("tutor_grounding") or {}
        require_list(grounding.get("allowed"), 3, f"{component_id} tutor allowed")
        require_list(grounding.get("forbidden"), 3, f"{component_id} tutor forbidden")

    serialized = canonical_json(data)
    for forbidden in (
        b'"status":"CENTRAL_BRAIN_ACCEPTED',
        b'"semantic_ref_status":"CANONICAL"',
        b'"object_level_admission_effect":"CLOSED"',
        b'"exact_mastery_effect":"ADMIT"',
    ):
        if forbidden in serialized:
            raise AssertionError("candidate content contains forbidden admission marker")

    print("RU09_EDSOO59_P222_8_1_CANDIDATE_CONTENT=PASS")
    print("BOUNDED_UNITS=2")
    print("PROPOSED_SEMANTICS=2")
    print("INDEPENDENT_COMPONENT_EVIDENCE_ITEMS=8")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("EXACT_MASTERY_ADMISSIONS=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("CONTENT_SHA256=" + hashlib.sha256(canonical_json(data)).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
