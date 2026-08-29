#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
PATH = PROGRAM / "production-learning-content" / "RU-PROG-16-EGE-ESSAY-WAVE-001-v0.1.json"

EXPECTED_BINDINGS = {
    "candidate-048": ("ru-ege-essay-author-position", "K1"),
    "candidate-049": ("ru-ege-essay-source-examples-explanation", "K2_COMPONENT"),
    "candidate-050": ("ru-ege-essay-example-semantic-relation", "K2_COMPONENT"),
    "candidate-051": ("ru-ege-essay-own-relation-justification", "K3"),
    "candidate-054": ("ru-ege-essay-factual-accuracy", "K4"),
    "candidate-052": ("ru-ege-essay-logical-composition-cohesion", "K5"),
    "candidate-055": ("ru-ege-essay-ethical-norm", "K6"),
}
EXPECTED_CROSS_MODULE = {
    "K7": ("orthographic_norms", {"RU-PROG-08"}),
    "K8": ("punctuation_norms", {"RU-PROG-10"}),
    "K9": ("grammar_norms", {"RU-PROG-07", "RU-PROG-09"}),
    "K10": ("speech_norms", {"RU-PROG-14"}),
}


def require_list(value: Any, name: str, minimum: int) -> list[Any]:
    if not isinstance(value, list) or len(value) < minimum:
        raise AssertionError(f"{name} must contain at least {minimum} items")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def validate_unit(unit: dict[str, Any]) -> None:
    semantic_id = str(unit.get("proposed_semantic_id", ""))
    candidate_ref = str(unit.get("candidate_ref", ""))
    if candidate_ref not in EXPECTED_BINDINGS:
        raise AssertionError(f"unexpected RU16 candidate binding: {candidate_ref}")
    expected_semantic, expected_criterion = EXPECTED_BINDINGS[candidate_ref]
    if semantic_id != expected_semantic or unit.get("criterion_route") != expected_criterion:
        raise AssertionError(f"RU16 semantic/criterion binding drift: {candidate_ref}")
    if not isinstance(unit.get("title_ru"), str) or not unit["title_ru"].strip():
        raise AssertionError(f"missing RU16 title: {semantic_id}")

    explanation = unit.get("canonical_explanation")
    if not isinstance(explanation, dict) or not isinstance(explanation.get("short"), str):
        raise AssertionError(f"missing RU16 explanation: {semantic_id}")
    require_list(explanation.get("boundaries"), f"boundaries[{semantic_id}]", 2)
    require_list(unit.get("decision_algorithm"), f"decision_algorithm[{semantic_id}]", 3)
    require_list(unit.get("worked_examples"), f"worked_examples[{semantic_id}]", 2)
    require_list(unit.get("misconceptions"), f"misconceptions[{semantic_id}]", 1)
    require_list(unit.get("guided_practice"), f"guided_practice[{semantic_id}]", 1)
    require_list(unit.get("independent_practice"), f"independent_practice[{semantic_id}]", 2)
    require_list(unit.get("mixed_transfer_practice"), f"mixed_transfer_practice[{semantic_id}]", 1)
    require_list(unit.get("retention_items"), f"retention_items[{semantic_id}]", 2)
    verification = require_list(unit.get("independent_verification"), f"independent_verification[{semantic_id}]", 2)
    if not any(
        item.get("type") == "constructed_response" and isinstance(item.get("scoring"), dict)
        for item in verification
        if isinstance(item, dict)
    ):
        raise AssertionError(f"constructed-response scoring missing: {semantic_id}")

    peis = unit.get("peis_evidence")
    if not isinstance(peis, dict):
        raise AssertionError(f"PEIS evidence missing: {semantic_id}")
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError(f"RU16 content self-admitted: {semantic_id}")
    if peis.get("independent_verification_required") is not True or peis.get("assistance_must_be_recorded") is not True:
        raise AssertionError(f"PEIS evidence requirements incomplete: {semantic_id}")

    tutor = unit.get("tutor_grounding")
    if not isinstance(tutor, dict):
        raise AssertionError(f"Tutor grounding missing: {semantic_id}")
    require_list(tutor.get("allowed"), f"tutor.allowed[{semantic_id}]", 1)
    require_list(tutor.get("forbidden"), f"tutor.forbidden[{semantic_id}]", 1)


def main() -> int:
    payload = json.loads(PATH.read_text(encoding="utf-8"))
    if payload.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise AssertionError("RU16 bundle must remain subject-acceptance-required")
    if payload.get("module_id") != "RU-PROG-16":
        raise AssertionError("RU16 bundle module drift")

    authority = payload.get("authority")
    if not isinstance(authority, dict):
        raise AssertionError("RU16 authority missing")
    if authority.get("route") != "EGE_2026_TASK_27" or authority.get("route_scoring_max_points") != 22:
        raise AssertionError("RU16 task-27 route/scoring authority drift")
    if authority.get("route_scoring_criteria") != ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9", "K10"]:
        raise AssertionError("RU16 K1-K10 route inventory drift")
    if authority.get("admission_unit_binding") != "PENDING_EXACT_OBJECT_LEVEL_DISPOSITION":
        raise AssertionError("RU16 content claimed exact admission binding prematurely")
    if "do not become semantic identities automatically" not in str(authority.get("criterion_semantic_rule", "")):
        raise AssertionError("scoring criterion -> semantic identity guard weakened")

    guard = payload.get("copyright_guard")
    if not isinstance(guard, dict):
        raise AssertionError("RU16 copyright guard missing")
    for key in ("source_passages_copied", "fipi_examples_copied", "textbook_examples_copied", "commercial_source_bytes_in_git"):
        if guard.get(key) != 0:
            raise AssertionError(f"RU16 source/copyright guard failed: {key}")
    if guard.get("learner_examples") != "ORIGINAL_EKSAMIO_SYNTHETIC_CONTEXTS":
        raise AssertionError("RU16 examples must remain original Eksamio synthetic contexts")

    bindings = payload.get("candidate_bindings")
    if not isinstance(bindings, list) or len(bindings) != 7:
        raise AssertionError("RU16 must contain exactly seven K1-K6 candidate bindings")
    actual_bindings: dict[str, tuple[str, str]] = {}
    for row in bindings:
        if not isinstance(row, dict):
            raise AssertionError("invalid RU16 candidate binding row")
        candidate_ref = str(row.get("candidate_ref", ""))
        actual_bindings[candidate_ref] = (
            str(row.get("proposed_semantic_id", "")),
            str(row.get("criterion_route", "")),
        )
        if row.get("relation") != "PROPOSED_SAME_BOUNDED_ABILITY_SUBJECT_REVIEW_REQUIRED":
            raise AssertionError(f"candidate self-admission detected: {candidate_ref}")
    if actual_bindings != EXPECTED_BINDINGS:
        raise AssertionError(f"RU16 candidate binding drift: {actual_bindings}")

    k2 = payload.get("k2_decomposition")
    if not isinstance(k2, dict) or k2.get("status") != "PRESERVED" or k2.get("criterion_route") != "K2":
        raise AssertionError("RU16 K2 decomposition not preserved")
    if set(k2.get("components") or []) != {
        "ru-ege-essay-source-examples-explanation",
        "ru-ege-essay-example-semantic-relation",
    }:
        raise AssertionError("RU16 K2 components collapsed or drifted")

    cross = payload.get("cross_module_quality_bindings")
    if not isinstance(cross, list) or len(cross) != 4:
        raise AssertionError("RU16 must bind K7-K10 through four cross-module dimensions")
    actual_cross: dict[str, tuple[str, set[str]]] = {}
    for row in cross:
        if not isinstance(row, dict):
            raise AssertionError("invalid RU16 cross-module binding")
        criterion = str(row.get("criterion_route", ""))
        if row.get("status") != "CROSS_MODULE_BINDING_SUBJECT_REVIEW_REQUIRED":
            raise AssertionError(f"RU16 cross-module binding self-admitted: {criterion}")
        actual_cross[criterion] = (
            str(row.get("quality_dimension", "")),
            set(str(value) for value in row.get("module_refs") or []),
        )
    if actual_cross != EXPECTED_CROSS_MODULE:
        raise AssertionError(f"RU16 K7-K10 cross-module binding drift: {actual_cross}")

    c53 = payload.get("candidate_053_guard")
    if not isinstance(c53, dict) or c53.get("candidate_ref") != "candidate-053":
        raise AssertionError("candidate-053 explicit guard missing")
    if c53.get("allowed_role") != "NARROW_GRAMMAR_CONTRIBUTOR_ONLY_IF_EXACTLY_APPLICABLE":
        raise AssertionError("candidate-053 role broadened")
    forbidden = set(c53.get("forbidden_roles") or [])
    if not {"K9_GENERAL_PROXY", "GENERAL_ESSAY_CORRECTNESS", "RU_PROG_16_SINGLE_LANGUAGE_CORRECTNESS_OWNER"}.issubset(forbidden):
        raise AssertionError("candidate-053 general-correctness guard weakened")

    units = payload.get("units")
    if not isinstance(units, list) or len(units) != 7:
        raise AssertionError("RU16 must materialize exactly seven K1-K6 learner units")
    for unit in units:
        if not isinstance(unit, dict):
            raise AssertionError("invalid RU16 learner unit")
        validate_unit(unit)
    actual_ids = {str(unit["proposed_semantic_id"]) for unit in units}
    expected_ids = {semantic for semantic, _ in EXPECTED_BINDINGS.values()}
    if actual_ids != expected_ids:
        raise AssertionError(f"RU16 unit set drift: {sorted(actual_ids ^ expected_ids)}")

    serialized = canonical_bytes(payload)
    if b'ru-essay-language-correctness' in serialized:
        raise AssertionError("forbidden broad essay-language-correctness identity invented")
    if b'"CANONICAL"' in serialized or b'"SUBJECT_ACCEPTED"' in serialized or b'"EXACT_MASTERY"' in serialized:
        raise AssertionError("RU16 proposed content contains premature acceptance claim")

    normalized_sha = hashlib.sha256(serialized).hexdigest()
    print("RU16_EGE_ESSAY_CONTENT_CANDIDATE=PASS")
    print("new_proposed_units=7")
    print("k2_components=2")
    print("k7_k10_cross_module_bindings=4")
    print("candidate_053_general_proxy=0")
    print("broad_essay_language_correctness_identity=0")
    print("semantic_admissions=0")
    print("source_passages_copied=0")
    print("commercial_source_bytes_in_git=0")
    print(f"normalized_sha256={normalized_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
