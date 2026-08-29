#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT = PROGRAM / "production-learning-content"
FILES = [
    CONTENT / "RU-PROG-13-EXPRESSIVE-MEANS-WAVE-001-v0.1.json",
    CONTENT / "RU-PROG-13-EXPRESSIVE-MEANS-WAVE-002-v0.1.json",
]
EXPECTED_IDS = {
    "ru-expressive-alliteration",
    "ru-expressive-personification",
    "ru-expressive-syntactic-parallelism",
    "ru-expressive-question-answer-form",
    "ru-expressive-gradation",
    "ru-expressive-inversion",
    "ru-expressive-lexical-repetition",
    "ru-expressive-epiphora",
    "ru-expressive-antithesis",
    "ru-expressive-rhetorical-question",
    "ru-expressive-rhetorical-exclamation",
    "ru-expressive-polysyndeton",
    "ru-expressive-asyndeton",
    "ru-expressive-litotes",
}
EXISTING_CANDIDATES = {
    "candidate-033": "assonance",
    "candidate-034": "hyperbole",
    "candidate-035": "metonymy",
    "candidate-036": "anaphora",
    "candidate-037": "parceling",
    "candidate-038": "homogeneous-member row expressive",
    "candidate-039": "address expressive / rhetorical-address boundary review",
    "candidate-040": "epithet",
    "candidate-041": "metaphor",
    "candidate-042": "comparison",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def require_list(value: Any, name: str, minimum: int) -> list[Any]:
    if not isinstance(value, list) or len(value) < minimum:
        raise AssertionError(f"{name} must contain at least {minimum} items")
    return value


def validate_unit(unit: dict[str, Any], *, source_file: str) -> None:
    semantic_id = unit.get("proposed_semantic_id")
    if semantic_id not in EXPECTED_IDS:
        raise AssertionError(f"unexpected RU13 proposed semantic id in {source_file}: {semantic_id}")
    if not isinstance(unit.get("title_ru"), str) or not unit["title_ru"].strip():
        raise AssertionError(f"missing title: {semantic_id}")
    explanation = unit.get("canonical_explanation")
    if not isinstance(explanation, dict) or not isinstance(explanation.get("short"), str):
        raise AssertionError(f"missing explanation: {semantic_id}")
    require_list(explanation.get("boundaries"), f"boundaries[{semantic_id}]", 2)
    require_list(unit.get("decision_algorithm"), f"decision_algorithm[{semantic_id}]", 3)
    require_list(unit.get("worked_examples"), f"worked_examples[{semantic_id}]", 2)
    require_list(unit.get("misconceptions"), f"misconceptions[{semantic_id}]", 1)
    require_list(unit.get("guided_practice"), f"guided_practice[{semantic_id}]", 1)
    require_list(unit.get("independent_practice"), f"independent_practice[{semantic_id}]", 2)
    require_list(unit.get("mixed_transfer_practice"), f"mixed_transfer_practice[{semantic_id}]", 1)
    require_list(unit.get("retention_items"), f"retention_items[{semantic_id}]", 1)
    verification = require_list(unit.get("independent_verification"), f"independent_verification[{semantic_id}]", 2)
    if not any(item.get("type") == "constructed_response" and isinstance(item.get("scoring"), dict) for item in verification):
        raise AssertionError(f"constructed-response scoring missing: {semantic_id}")
    peis = unit.get("peis_evidence")
    if not isinstance(peis, dict) or peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError(f"PEIS semantic boundary weakened: {semantic_id}")
    if peis.get("independent_verification_required") is not True or peis.get("assistance_must_be_recorded") is not True:
        raise AssertionError(f"PEIS evidence requirements incomplete: {semantic_id}")
    tutor = unit.get("tutor_grounding")
    if not isinstance(tutor, dict):
        raise AssertionError(f"Tutor grounding missing: {semantic_id}")
    require_list(tutor.get("allowed"), f"tutor.allowed[{semantic_id}]", 1)
    require_list(tutor.get("forbidden"), f"tutor.forbidden[{semantic_id}]", 1)


def main() -> int:
    units: list[dict[str, Any]] = []
    payloads: list[dict[str, Any]] = []
    for path in FILES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payloads.append(payload)
        if payload.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
            raise AssertionError(f"RU13 content self-admitted: {path.name}")
        if payload.get("module_id") != "RU-PROG-13":
            raise AssertionError(f"wrong module: {path.name}")
        authority = payload.get("authority")
        if not isinstance(authority, dict):
            raise AssertionError(f"missing authority: {path.name}")
        if authority.get("admission_unit_binding") != "PENDING_EXACT_OBJECT_LEVEL_DISPOSITION":
            raise AssertionError(f"content claimed exact admission binding prematurely: {path.name}")
        tier_a = set(authority.get("tier_a_scope") or [])
        if not {"FIPI-EGE-RU-2026-FINAL", "FIPI-OGE-RU-2026-FINAL"}.issubset(tier_a):
            raise AssertionError(f"official EGE/OGE authority missing: {path.name}")
        guard = payload.get("copyright_guard")
        if not isinstance(guard, dict):
            raise AssertionError(f"copyright guard missing: {path.name}")
        for key in ("source_passages_copied", "fipi_examples_copied", "textbook_examples_copied", "commercial_source_bytes_in_git"):
            if guard.get(key) != 0:
                raise AssertionError(f"copyright/source-byte guard failed {key}: {path.name}")
        if guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
            raise AssertionError(f"original-example guard failed: {path.name}")
        file_units = payload.get("units")
        if not isinstance(file_units, list) or len(file_units) != 7:
            raise AssertionError(f"expected 7 units in {path.name}")
        for unit in file_units:
            if not isinstance(unit, dict):
                raise AssertionError(f"invalid unit in {path.name}")
            validate_unit(unit, source_file=path.name)
            units.append(unit)

    actual_ids = [str(unit["proposed_semantic_id"]) for unit in units]
    if len(actual_ids) != len(set(actual_ids)):
        raise AssertionError("duplicate RU13 proposed semantic ids")
    if set(actual_ids) != EXPECTED_IDS:
        raise AssertionError(f"RU13 missing/unexpected identities: {sorted(set(actual_ids) ^ EXPECTED_IDS)}")

    wave2 = payloads[1]
    dependency = wave2.get("review_dependency")
    if not isinstance(dependency, dict):
        raise AssertionError("rhetorical-address duplicate guard missing")
    if dependency.get("existing_candidate") != "candidate-039" or dependency.get("decision") != "EXACT_BOUNDARY_REVIEW_REQUIRED_BEFORE_NEW_ID":
        raise AssertionError("candidate-039 rhetorical-address boundary was not preserved")

    serialized = canonical_bytes(payloads)
    banned_claims = [b'"CANONICAL"', b'"SUBJECT_ACCEPTED"', b'"EXACT_MASTERY"']
    if any(marker in serialized for marker in banned_claims):
        raise AssertionError("RU13 proposed content contains premature acceptance claim")

    normalized_sha = hashlib.sha256(serialized).hexdigest()
    print("RU13_EXPRESSIVE_CONTENT_CANDIDATE=PASS")
    print(f"new_proposed_units={len(units)}")
    print(f"existing_candidate_boundary_refs={len(EXISTING_CANDIDATES)}")
    print("rhetorical_address_new_identity=0")
    print("semantic_admissions=0")
    print("source_passages_copied=0")
    print("commercial_source_bytes_in_git=0")
    print(f"normalized_sha256={normalized_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
