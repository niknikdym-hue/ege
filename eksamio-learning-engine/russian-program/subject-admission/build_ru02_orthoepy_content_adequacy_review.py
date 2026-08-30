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
CONTENT = PROGRAM / "production-learning-content/RU-PROG-02-ORTHOEPY-STRESS-WAVE-002-v0.1.json"
BOUNDARY_BUILDER = HERE / "build_ru02_orthoepy_candidate_boundary_review.py"
SOURCE_RESOLVER = HERE / "build_ru02_orthoepy_source_identity_resolution.py"

CANDIDATES = [f"candidate-{number:03d}" for number in range(18, 25)]
FORM_UNIT = "ru-orthoepy-stress-form-sensitive"
SOURCE_CHECK_UNIT = "ru-orthoepy-norm-source-check"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    boundary = runpy.run_path(str(BOUNDARY_BUILDER))["build_review"]()
    if boundary.get("status") != "CENTRAL_BRAIN_RU02_ORTHOEPY_REUSE_FIRST_BOUNDARY_REVIEW_ACCEPTANCE_NOT_ADMITTED":
        raise ValueError("RU02 boundary prerequisite drift")
    source_resolution = runpy.run_path(str(SOURCE_RESOLVER))["build_resolution"]()
    if source_resolution.get("status") != "CENTRAL_BRAIN_RU02_SOURCE_IDENTITIES_RESOLVED_SUBJECT_ACCEPTANCE_NOT_ADMITTED":
        raise ValueError("RU02 source-resolution prerequisite drift")
    if int((source_resolution.get("summary") or {}).get("exact_source_identity_resolutions", -1)) != 7:
        raise ValueError("RU02 source identity resolution incomplete")
    if int((source_resolution.get("summary") or {}).get("semantic_admissions", -1)) != 0:
        raise ValueError("RU02 source resolution unexpectedly admitted semantics")

    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-02":
        raise ValueError("RU02 content authority/status drift")
    units = {
        str(row.get("proposed_semantic_id")): row
        for row in (content.get("units") or [])
        if isinstance(row, dict)
    }
    if set(units) != {FORM_UNIT, SOURCE_CHECK_UNIT}:
        raise ValueError("RU02 learner unit set drift")

    form = units[FORM_UNIT]
    if form.get("title_ru") != "Ударение зависит от слова и конкретной формы":
        raise ValueError("RU02 form-sensitive title drift")
    form_examples = [str(row.get("prompt")) for row in (form.get("worked_examples") or []) if isinstance(row, dict)]
    if form_examples != ["отбылА", "отдалА", "перезвонИт"]:
        raise ValueError("RU02 form-sensitive worked-example boundary drift")
    form_short = str((form.get("canonical_explanation") or {}).get("short") or "")
    if "конкретной грамматической форме" not in form_short or "проверить её норму" not in form_short:
        raise ValueError("RU02 form-sensitive semantic boundary drift")

    source_check = units[SOURCE_CHECK_UNIT]
    if source_check.get("title_ru") != "Орфоэпическая норма: когда нужна словарная проверка":
        raise ValueError("RU02 source-check title drift")
    source_check_short = str((source_check.get("canonical_explanation") or {}).get("short") or "")
    if "обратиться к актуальному орфоэпическому словарю или официальному словнику" not in source_check_short:
        raise ValueError("RU02 source-check procedure boundary drift")

    decisions = [
        {
            "content_semantic_id": FORM_UNIT,
            "adequacy_class": "PARTIAL_CROSS_CANDIDATE_IMPLEMENTATION_NOT_EXACT_CANDIDATE_CONTENT",
            "exact_candidate_owner": None,
            "candidate_overlap": {
                "candidate-018": "PARTIAL_GENERIC_STRESS_SELECTION_IMPLEMENTATION",
                "candidate-021": "PARTIAL_VERB_FORM_EXAMPLE_OVERLAP",
            },
            "no_direct_content_evidence_for": [
                "candidate-019",
                "candidate-020",
                "candidate-022",
                "candidate-023",
                "candidate-024",
            ],
            "evidence": {
                "semantic_boundary": "form-sensitive stress checking for a concrete word/form",
                "worked_examples": form_examples,
                "worked_example_part_of_speech_scope": "VERB_FORMS_ONLY",
            },
            "admission_effect": "NONE",
            "reason": "The unit is narrower than the generic normative-stress candidate and its concrete worked examples are verb forms. It therefore cannot prove exact learner-content adequacy for candidate-018, candidate-021, or any other RU02 candidate.",
        },
        {
            "content_semantic_id": SOURCE_CHECK_UNIT,
            "adequacy_class": "NORMATIVE_SOURCE_CHECK_META_PROCEDURE_NOT_EXACT_CANDIDATE_CONTENT",
            "exact_candidate_owner": None,
            "candidate_overlap": {},
            "no_direct_content_evidence_for": CANDIDATES,
            "evidence": {
                "semantic_boundary": "fail-closed procedure for checking an uncertain orthoepic norm in an authoritative source",
            },
            "admission_effect": "NONE",
            "reason": "The unit teaches verification procedure rather than one of the seven stress-selection subject components; examples inside the procedure do not turn it into candidate-specific learner content.",
        },
    ]

    candidate_gap_status = [
        {
            "candidate_ref": candidate,
            "exact_candidate_content_status": "MISSING_EXACT_CANDIDATE_LEARNER_CONTENT",
            "basis": (
                "ONLY_PARTIAL_EXISTING_CONTENT_OVERLAP"
                if candidate in {"candidate-018", "candidate-021"}
                else "NO_DIRECT_EXISTING_CONTENT_EVIDENCE"
            ),
            "semantic_admission_effect": "NONE",
        }
        for candidate in CANDIDATES
    ]

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU02_EXISTING_CONTENT_ADEQUACY_REVIEW_COMPLETE_EXACT_CANDIDATE_CONTENT_GAPS_PROVEN_NO_ADMISSION",
        "authority_issue": 161,
        "module_id": "RU-PROG-02",
        "prerequisite_boundary_sha256": boundary["normalized_sha256"],
        "prerequisite_source_resolution_sha256": source_resolution["normalized_sha256"],
        "policy": {
            "content_example_overlap_is_exact_semantic_equivalence": False,
            "meta_procedure_is_subject_component": False,
            "partial_content_can_admit_candidate": False,
            "candidate_content_gap_proof_is_semantic_admission": False,
            "candidate_content_gap_proof_is_object_closure": False,
            "component_specific_independent_evidence_required_for_mastery": True,
            "keyword_or_fuzzy_inference_allowed": False,
        },
        "content_adequacy_decisions": decisions,
        "candidate_gap_status": candidate_gap_status,
        "summary": {
            "existing_learner_units_reviewed": 2,
            "exact_candidate_content_units": 0,
            "partial_cross_candidate_units": 1,
            "meta_procedure_units": 1,
            "candidate_exact_content_gaps_proven": 7,
            "semantic_admissions": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "false_exact_mastery_admissions": 0,
        },
        "next_exact_work": {
            "candidate_source_identities_unresolved": 0,
            "candidate_exact_content_gaps_remaining": 7,
            "candidates_with_partial_skill_graph_evidence_requiring_semantic_acceptance_review": 6,
            "first_candidate_with_confirmed_skill_graph_evidence_and_proven_exact_content_gap": "candidate-018",
            "new_content_may_self_admit_semantics": False,
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
        print("RU02_ORTHOEPY_CONTENT_ADEQUACY_REVIEW=PASS")
        print("EXISTING_LEARNER_UNITS_REVIEWED=2")
        print("EXACT_CANDIDATE_CONTENT_UNITS=0")
        print("CANDIDATE_EXACT_CONTENT_GAPS_PROVEN=7")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_LEVEL_CLOSURES=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
