#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT = PROGRAM / "production-learning-content"
PROPOSED_FILES = [
    CONTENT / "RU-PROG-13-EXPRESSIVE-MEANS-WAVE-001-v0.1.json",
    CONTENT / "RU-PROG-13-EXPRESSIVE-MEANS-WAVE-002-v0.1.json",
]
EXISTING_FILE = CONTENT / "RU-PROG-13-EXPRESSIVE-MEANS-WAVE-003-v0.1.json"
EXPECTED_PROPOSED_IDS = {
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
EXPECTED_EXISTING = {
    "candidate-033": "device_assonance",
    "candidate-034": "device_hyperbole",
    "candidate-035": "device_metonymy",
    "candidate-036": "device_anaphora",
    "candidate-037": "device_parcellation",
    "candidate-038": "device_homogeneous_rows",
    "candidate-039": "device_address",
    "candidate-040": "device_epithet",
    "candidate-041": "device_metaphor",
    "candidate-042": "device_comparison",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def require_list(value: Any, name: str, minimum: int) -> list[Any]:
    if not isinstance(value, list) or len(value) < minimum:
        raise AssertionError(f"{name} must contain at least {minimum} items")
    return value


def validate_common_unit(unit: dict[str, Any], *, unit_ref: str, expected_status: str) -> None:
    if not isinstance(unit.get("title_ru"), str) or not unit["title_ru"].strip():
        raise AssertionError(f"missing title: {unit_ref}")
    explanation = unit.get("canonical_explanation")
    if not isinstance(explanation, dict) or not isinstance(explanation.get("short"), str):
        raise AssertionError(f"missing explanation: {unit_ref}")
    require_list(explanation.get("boundaries"), f"boundaries[{unit_ref}]", 2)
    require_list(unit.get("decision_algorithm"), f"decision_algorithm[{unit_ref}]", 3)
    require_list(unit.get("worked_examples"), f"worked_examples[{unit_ref}]", 2)
    require_list(unit.get("misconceptions"), f"misconceptions[{unit_ref}]", 1)
    require_list(unit.get("guided_practice"), f"guided_practice[{unit_ref}]", 1)
    require_list(unit.get("independent_practice"), f"independent_practice[{unit_ref}]", 2)
    require_list(unit.get("mixed_transfer_practice"), f"mixed_transfer_practice[{unit_ref}]", 1)
    require_list(unit.get("retention_items"), f"retention_items[{unit_ref}]", 1)
    verification = require_list(unit.get("independent_verification"), f"independent_verification[{unit_ref}]", 2)
    if not any(item.get("type") == "constructed_response" and isinstance(item.get("scoring"), dict) for item in verification):
        raise AssertionError(f"constructed-response scoring missing: {unit_ref}")
    peis = unit.get("peis_evidence")
    if not isinstance(peis, dict) or peis.get("semantic_ref_status") != expected_status:
        raise AssertionError(f"PEIS semantic boundary weakened: {unit_ref}")
    if peis.get("independent_verification_required") is not True or peis.get("assistance_must_be_recorded") is not True:
        raise AssertionError(f"PEIS evidence requirements incomplete: {unit_ref}")
    tutor = unit.get("tutor_grounding")
    if not isinstance(tutor, dict):
        raise AssertionError(f"Tutor grounding missing: {unit_ref}")
    require_list(tutor.get("allowed"), f"tutor.allowed[{unit_ref}]", 1)
    require_list(tutor.get("forbidden"), f"tutor.forbidden[{unit_ref}]", 1)


def validate_payload(payload: dict[str, Any], path: Path) -> None:
    if payload.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise AssertionError(f"RU13 content self-admitted: {path.name}")
    if payload.get("module_id") != "RU-PROG-13":
        raise AssertionError(f"wrong module: {path.name}")
    authority = payload.get("authority")
    if not isinstance(authority, dict) or authority.get("admission_unit_binding") != "PENDING_EXACT_OBJECT_LEVEL_DISPOSITION":
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


def main() -> int:
    payloads: list[dict[str, Any]] = []
    proposed_units: list[dict[str, Any]] = []
    for path in PROPOSED_FILES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payloads.append(payload)
        validate_payload(payload, path)
        units = payload.get("units")
        if not isinstance(units, list) or len(units) != 7:
            raise AssertionError(f"expected 7 proposed units in {path.name}")
        for unit in units:
            semantic_id = unit.get("proposed_semantic_id")
            if semantic_id not in EXPECTED_PROPOSED_IDS:
                raise AssertionError(f"unexpected proposed semantic id: {semantic_id}")
            validate_common_unit(unit, unit_ref=str(semantic_id), expected_status="PROPOSED_NOT_CANONICAL")
            proposed_units.append(unit)

    existing_payload = json.loads(EXISTING_FILE.read_text(encoding="utf-8"))
    payloads.append(existing_payload)
    validate_payload(existing_payload, EXISTING_FILE)
    existing_units = existing_payload.get("units")
    if not isinstance(existing_units, list) or len(existing_units) != 10:
        raise AssertionError("expected 10 existing-candidate learner units in wave 003")

    seen_existing: dict[str, str] = {}
    for unit in existing_units:
        candidate_ref = unit.get("semantic_candidate_ref")
        source_ref = unit.get("source_semantic_ref")
        if candidate_ref not in EXPECTED_EXISTING:
            raise AssertionError(f"unexpected existing candidate ref: {candidate_ref}")
        if source_ref != EXPECTED_EXISTING[candidate_ref]:
            raise AssertionError(f"candidate/source semantic mismatch: {candidate_ref} -> {source_ref}")
        if unit.get("proposed_semantic_id") is not None:
            raise AssertionError(f"existing candidate duplicated with a new proposed id: {candidate_ref}")
        if candidate_ref in seen_existing:
            raise AssertionError(f"duplicate existing candidate learner unit: {candidate_ref}")
        seen_existing[str(candidate_ref)] = str(source_ref)
        validate_common_unit(unit, unit_ref=str(candidate_ref), expected_status="EXISTING_CANDIDATE_NOT_CANONICAL")

    proposed_ids = [str(unit["proposed_semantic_id"]) for unit in proposed_units]
    if len(proposed_ids) != len(set(proposed_ids)) or set(proposed_ids) != EXPECTED_PROPOSED_IDS:
        raise AssertionError("RU13 proposed identity coverage drift")
    if seen_existing != EXPECTED_EXISTING:
        raise AssertionError("RU13 existing candidate content coverage drift")

    wave2 = payloads[1]
    dependency = wave2.get("review_dependency")
    if not isinstance(dependency, dict):
        raise AssertionError("rhetorical-address duplicate guard missing")
    if dependency.get("existing_candidate") != "candidate-039" or dependency.get("decision") != "EXACT_BOUNDARY_REVIEW_REQUIRED_BEFORE_NEW_ID":
        raise AssertionError("candidate-039 rhetorical-address boundary was not preserved")
    candidate_039 = next(unit for unit in existing_units if unit["semantic_candidate_ref"] == "candidate-039")
    if "duplicate" not in " ".join(candidate_039["canonical_explanation"]["boundaries"]).casefold():
        raise AssertionError("candidate-039 learner content lost no-duplicate rhetorical-address boundary")

    serialized = canonical_bytes(payloads)
    banned_claims = [b'"CANONICAL"', b'"SUBJECT_ACCEPTED"', b'"EXACT_MASTERY"']
    if any(marker in serialized for marker in banned_claims):
        raise AssertionError("RU13 content contains premature acceptance claim")

    normalized_sha = hashlib.sha256(serialized).hexdigest()
    print("RU13_EXPRESSIVE_CONTENT_CANDIDATE=PASS")
    print(f"new_proposed_units={len(proposed_units)}")
    print(f"existing_candidate_content_units={len(existing_units)}")
    print("total_component_content_units=24")
    print("rhetorical_address_new_identity=0")
    print("semantic_admissions=0")
    print("source_passages_copied=0")
    print("commercial_source_bytes_in_git=0")
    print(f"normalized_sha256={normalized_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
