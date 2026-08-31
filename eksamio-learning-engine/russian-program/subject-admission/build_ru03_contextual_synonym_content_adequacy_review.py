#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
GAP_REVIEWER = HERE / "build_ru03_contextual_synonym_content_gap_review.py"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-03-CONTEXTUAL-SYNONYM-SELECTION-WAVE-008-v0.1.json"

CANDIDATE = "candidate-015"
TAXONOMY = "contextual_synonym_selection"
SEMANTIC = "ru-lexis-contextual-synonym-text-fit"
LABEL = "Подбор контекстного синонима к слову исходного текста"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    gap = runpy.run_path(str(GAP_REVIEWER))["build_review"]()
    if gap.get("status") != "CENTRAL_BRAIN_RU03_CONTEXTUAL_SYNONYM_CONTENT_GAP_REVIEW_COMPLETE_NO_ADMISSION":
        raise ValueError("candidate-015 content-gap prerequisite drift")
    if not (gap.get("decision") or {}).get("candidate_specific_content_gap_proven"):
        raise ValueError("candidate-015 content gap is not proven")
    if (gap.get("decision") or {}).get("proposed_bounded_semantic_id") != SEMANTIC:
        raise ValueError("candidate-015 proposed semantic drift")

    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    if data.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("candidate-015 learner content self-admitted")
    if data.get("subject") != "russian" or data.get("module_id") != "RU-PROG-03":
        raise ValueError("candidate-015 learner content module drift")
    guard = data.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes") != 0:
        raise ValueError("candidate-015 learner content copied protected source bytes")
    if guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise ValueError("candidate-015 learner examples are not original Eksamio")

    units = [row for row in data.get("units", []) if isinstance(row, dict)]
    if len(units) != 1:
        raise ValueError("candidate-015 learner wave must contain exactly one bounded unit")
    unit = units[0]
    if unit.get("proposed_semantic_id") != SEMANTIC:
        raise ValueError("candidate-015 learner semantic id drift")
    if unit.get("candidate_ref") != CANDIDATE or unit.get("source_taxonomy_id") != TAXONOMY:
        raise ValueError("candidate-015 learner crosswalk drift")
    if unit.get("title_ru") != LABEL:
        raise ValueError("candidate-015 learner label drift")

    explanation = unit.get("canonical_explanation") or {}
    text = (str(explanation.get("short") or "") + "\n" + "\n".join(str(v) for v in explanation.get("boundaries", []))).lower()
    for token in ("контекст", "замен", "смысл", "граммат", "стилист"):
        if token not in text:
            raise ValueError(f"candidate-015 exact explanation missing boundary token: {token}")
    for token in ("фразеолог", "пароним", "task-25", "component-specific"):
        if token not in text:
            raise ValueError(f"candidate-015 exclusion boundary missing token: {token}")

    minimums = {
        "decision_algorithm": 7,
        "worked_examples": 4,
        "misconceptions": 4,
        "guided_practice": 2,
        "independent_practice": 4,
        "mixed_transfer_practice": 2,
        "retention_items": 2,
        "independent_verification": 2,
    }
    for key, minimum in minimums.items():
        value = unit.get(key)
        if not isinstance(value, list) or len(value) < minimum:
            raise ValueError(f"candidate-015 learner content too thin: {key}")

    verification = unit["independent_verification"]
    ids = [row.get("id") for row in verification if isinstance(row, dict)]
    if len(ids) != len(set(ids)) or any(not value for value in ids):
        raise ValueError("candidate-015 independent verification ids invalid")
    if {row.get("type") for row in verification} != {"single_choice", "constructed_response"}:
        raise ValueError("candidate-015 independent verification mode drift")
    single = next(row for row in verification if row.get("type") == "single_choice")
    if single.get("correct_option_index") != 0 or single.get("options", [None])[0] != "холодно":
        raise ValueError("candidate-015 single-choice key drift")
    constructed = next(row for row in verification if row.get("type") == "constructed_response")
    scoring = constructed.get("scoring") or {}
    if scoring.get("max_points") != 2 or len(scoring.get("criteria") or []) != 2:
        raise ValueError("candidate-015 constructed-response scoring drift")

    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise ValueError("candidate-015 content self-admitted semantic")
    if peis.get("independent_verification_required") is not True:
        raise ValueError("candidate-015 independent verification not required")
    if peis.get("assistance_must_be_recorded") is not True:
        raise ValueError("candidate-015 assistance recording weakened")
    if peis.get("generic_task_result_can_emit_exact_mastery") is not False:
        raise ValueError("candidate-015 generic Task-25 mastery leakage")
    if peis.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise ValueError("candidate-015 object-binding drift")

    tutor = unit.get("tutor_grounding") or {}
    allowed = "\n".join(str(v).lower() for v in tutor.get("allowed", []))
    forbidden = "\n".join(str(v).lower() for v in tutor.get("forbidden", []))
    for token in ("supplied fragment", "substitution", "grammatical", "context-only"):
        if token not in allowed:
            raise ValueError(f"candidate-015 tutor allowed grounding missing: {token}")
    for token in ("thematic association", "phraseologism_identification", "generic task-25"):
        if token not in forbidden:
            raise ValueError(f"candidate-015 tutor forbidden grounding missing: {token}")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU03_CONTEXTUAL_SYNONYM_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION",
        "authority_issue": 161,
        "module_id": "RU-PROG-03",
        "source_identity": {
            "candidate_ref": CANDIDATE,
            "source_taxonomy_id": TAXONOMY,
            "label_ru": LABEL,
            "source_identity_status": gap["source_identity_prerequisite"]["source_identity_status"],
            "current_official_authority": gap["source_identity_prerequisite"]["current_official_authority"],
        },
        "reuse_first_result": {
            "preexisting_exact_content_reusable": False,
            "candidate_specific_content_gap_proven": True,
            "broader_neighbor_semantic_id": gap["reuse_first_inventory"]["broader_neighbor"]["semantic_id"],
            "broader_neighbor_relation": "ADJACENT_BUT_NOT_EXACT",
        },
        "learner_content": {
            "path": "russian-program/production-learning-content/RU-PROG-03-CONTEXTUAL-SYNONYM-SELECTION-WAVE-008-v0.1.json",
            "proposed_semantic_id": SEMANTIC,
            "original_examples": True,
            "source_passages_copied": 0,
            "commercial_textbook_bytes": 0,
            "independent_verification_present": True,
            "assistance_recording_required": True,
            "tutor_grounding_bounded": True,
        },
        "review_decision": {
            "content_exact_for_candidate_015": True,
            "content_duplicate_of_existing_ru03_unit": False,
            "semantic_admission_by_this_review": False,
            "new_school_canonical_identities": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "false_exact_mastery_admissions": 0,
            "next_status": "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE",
        },
        "policy": {
            "contextual_meaning_mastery_implies_contextual_synonym_mastery": False,
            "generic_task25_result_can_emit_exact_component_mastery": False,
            "component_specific_independent_verification_required": True,
            "content_adequacy_review_is_semantic_admission": False,
            "accepted_demos_or_scorers_may_change": False,
        },
        "summary": {
            "exact_candidate_content_units": 1,
            "semantic_admissions": 0,
            "new_school_canonical_identities": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "false_exact_mastery_admissions": 0,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
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
        print("RU03_CONTEXTUAL_SYNONYM_CONTENT_ADEQUACY=PASS")
        print("EXACT_CANDIDATE_CONTENT_UNITS=1")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_CLOSURES=0/0")
        print("FALSE_EXACT_MASTERY=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
