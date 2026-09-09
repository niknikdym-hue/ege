#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT = PROGRAM / "production-learning-content/RU-PROG-01-PHONETIC-STRESS-WAVE-006-v0.1.json"

SEMANTIC = "ru-phonetics-stress"
TAXONOMY = "phonetic_stress"
SOURCE_CLAUSES = ["EDSOO59-P187-4.1.6", "OGE-COD-P020-4.1.6"]
VERIFICATION_IDS = ["p01-u8-v1", "p01-u8-v2", "p01-u8-v3", "p01-u8-v4", "p01-u8-v5"]
CONTENT_GIT_BLOB = "d3deae35b2ccdd58f18e01a0bf3256a0f9446a06"
READINESS_GATE = {
    "workflow": "Russian RU01 phonetic stress candidate content readiness",
    "run_id": 34361525841,
    "head_sha": "5277f4522c9c1b5f993b7542354492b742e1fd2c",
    "conclusion": "SUCCESS",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def build_review() -> dict[str, Any]:
    raw = CONTENT.read_bytes()
    require(git_blob_sha(raw) == CONTENT_GIT_BLOB, "phonetic-stress content blob drift")
    data = json.loads(raw.decode("utf-8"))

    require(data.get("status") == "CONTENT_AND_EVIDENCE_READY_SEMANTIC_ACCEPTANCE_REQUIRED", "content status drift")
    require(data.get("subject") == "russian" and data.get("module_id") == "RU-PROG-01", "module drift")

    provenance = [row for row in data.get("source_provenance", []) if isinstance(row, dict)]
    owner = next((row for row in provenance if row.get("kind") == "bounded_owner_resolution"), None)
    require(owner is not None, "bounded owner-resolution provenance missing")
    require(owner.get("candidate_semantic_id") == SEMANTIC, "candidate semantic drift")
    require(owner.get("source_clause_ids") == SOURCE_CLAUSES, "source-clause drift")

    exact_docs = {
        str(row.get("document_id")): row
        for row in provenance
        if row.get("kind") in {"official_program", "official_codifier"}
    }
    require(exact_docs.get("EDSOO59", {}).get("document_sha256") == "1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d", "EDSOO authority drift")
    require(exact_docs.get("OGE_COD", {}).get("document_sha256") == "2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a", "OGE authority drift")
    require(exact_docs.get("EDSOO59", {}).get("official_requirement") == "Ударение", "EDSOO requirement drift")
    require(exact_docs.get("OGE_COD", {}).get("official_requirement") == "Ударение", "OGE requirement drift")

    guard = data.get("copyright_guard") or {}
    require(guard.get("source_passages_copied") == 0, "source bytes copied")
    require(guard.get("learner_explanations") == "ORIGINAL_EKSAMIO", "learner explanation provenance drift")
    require(guard.get("learner_examples") == "ORIGINAL_EKSAMIO", "learner example provenance drift")
    require(guard.get("commercial_textbook_bytes_in_git") == 0, "commercial textbook bytes forbidden")

    identity = data.get("identity_boundary") or {}
    require(identity.get("proposed_semantic_id") == SEMANTIC, "identity semantic drift")
    require(identity.get("source_taxonomy_id") == TAXONOMY, "taxonomy drift")
    require(identity.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "candidate self-admitted")
    for key in (
        "normative_orthoepy_stress_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "spelling_may_determine_unmarked_stress",
        "syllable_count_alone_may_determine_stress",
        "word_analysis_semantic_may_substitute",
        "candidate_name_or_route_or_task_number_can_create_acceptance",
        "generic_ru01_result_can_emit_exact_component_mastery",
    ):
        require(identity.get(key) is False, f"fail-closed identity boundary opened: {key}")

    units = [row for row in data.get("units", []) if isinstance(row, dict)]
    require(len(units) == 1, "exactly one bounded generic-stress unit required")
    unit = units[0]
    require(unit.get("proposed_semantic_id") == SEMANTIC, "unit semantic drift")

    explanation = unit.get("canonical_explanation") or {}
    explanation_text = (str(explanation.get("short") or "") + "\n" + "\n".join(map(str, explanation.get("boundaries") or []))).lower()
    for token in ("ударен", "слог", "звуч", "норматив", "орфоэп", "произнош"):
        require(token in explanation_text, f"content boundary missing: {token}")
    require("количество слогов" in explanation_text or "число слогов" in explanation_text, "syllable-count separation not explicit")
    require("написан" in explanation_text or "орфограф" in explanation_text, "spelling-to-stress fail-closed boundary missing")

    minimums = {
        "decision_algorithm": 6,
        "worked_examples": 4,
        "misconceptions": 4,
        "guided_practice": 3,
        "independent_practice": 3,
        "mixed_transfer_practice": 2,
        "independent_verification": 5,
    }
    for field, minimum in minimums.items():
        value = unit.get(field)
        require(isinstance(value, list) and len(value) >= minimum, f"learner content too thin: {field}")

    verification = unit["independent_verification"]
    ids = [str(row.get("id")) for row in verification]
    require(ids == VERIFICATION_IDS and len(set(ids)) == len(ids), "component-specific verification set drift")
    measures = {str(row.get("measures")) for row in verification}
    require(
        measures
        == {
            "identify_explicit_stress",
            "reject_stress_from_syllable_count_only",
            "read_stress_mark_without_normative_overclaim",
            "separate_generic_from_normative_stress",
            "preserve_component_boundaries",
        },
        "component-specific verification coverage incomplete",
    )
    for row in verification:
        require(row.get("exact_item_identity_required") is True, f"exact item identity missing: {row.get('id')}")
        require(row.get("registered_user_identity_ref_required") is True, f"registered identity missing: {row.get('id')}")
        require(row.get("received_at_server_required") is True, f"server timestamp missing: {row.get('id')}")

    v2 = next(row for row in verification if row.get("id") == "p01-u8-v2")
    require("не определяет" in str(v2.get("expected") or "").lower(), "syllable-count fail-closed evidence drift")
    v4 = next(row for row in verification if row.get("id") == "p01-u8-v4")
    v4_expected = str(v4.get("expected") or "").lower()
    require("нужна" in v4_expected and "normative" in v4_expected and "authority" in v4_expected, "normative-stress separation evidence drift")
    v5 = next(row for row in verification if row.get("id") == "p01-u8-v5")
    v5_expected = str(v5.get("expected") or "").lower()
    require("pronunciation" in v5_expected and "transcription" in v5_expected and "component-specific" in v5_expected, "adjacent-component evidence boundary drift")

    peis = unit.get("peis_evidence") or {}
    require(peis.get("semantic_ref") == SEMANTIC, "PEIS semantic drift")
    require(peis.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "PEIS self-admission")
    require(peis.get("user_identity_ref") == "REGISTERED_USER_REQUIRED", "registered learner boundary weakened")
    require(peis.get("item_identity") == "EXACT_VERSIONED_ITEM_REQUIRED", "exact item boundary weakened")
    require(peis.get("received_at") == "SERVER_OWNED_TIMESTAMP_REQUIRED", "server-owned timestamp weakened")
    require(peis.get("today_timezone") == "Europe/Moscow", "Today timezone drift")
    require(peis.get("evidence_event_outbox") == "DURABLE_REQUIRED_BEFORE_FUTURE_CANONICAL_WRITE", "durable evidence boundary weakened")
    require(peis.get("mastery_before_separate_semantic_acceptance") is False, "pre-acceptance mastery opened")
    require(peis.get("generic_ru01_attempt_can_emit_exact_mastery") is False, "generic RU01 exact mastery opened")
    require(peis.get("anonymous_progress_allowed") is False, "anonymous canonical progress opened")
    require(peis.get("device_only_canonical_state_allowed") is False, "device-only canonical state opened")

    admission = data.get("admission_boundary") or {}
    require(admission.get("semantic_admissions") == 0, "content wave self-admitted semantic")
    require(admission.get("object_level_closures") == 0, "content wave self-closed object")
    require(admission.get("exact_mastery_admissions") == 0, "content wave self-admitted exact mastery")
    require(admission.get("false_exact_mastery_admissions") == 0, "false exact mastery drift")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_PHONETIC_STRESS_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION",
        "authority_pr": 164,
        "module_id": "RU-PROG-01",
        "candidate": {
            "semantic_id": SEMANTIC,
            "source_taxonomy_id": TAXONOMY,
            "source_clause_ids": SOURCE_CLAUSES,
            "semantic_ref_status": "PROPOSED_NOT_CANONICAL",
        },
        "prerequisite_remote_gate": READINESS_GATE,
        "learner_content": {
            "path": "russian-program/production-learning-content/RU-PROG-01-PHONETIC-STRESS-WAVE-006-v0.1.json",
            "git_blob_sha1": CONTENT_GIT_BLOB,
            "original_eksamio_explanations": True,
            "original_eksamio_examples": True,
            "component_specific_verification_ids": VERIFICATION_IDS,
            "registered_user_identity_required": True,
            "exact_item_identity_required": True,
            "server_owned_received_at_required": True,
            "durable_evidence_event_required_before_future_canonical_write": True,
        },
        "adequacy_decision": {
            "content_exact_for_bounded_generic_phonetic_stress_candidate": True,
            "official_clause_scope_covered": True,
            "explicit_stress_recognition_covered": True,
            "syllable_count_does_not_determine_stress": True,
            "spelling_does_not_determine_unmarked_normative_stress": True,
            "normative_orthoepy_stress_selection_separated": True,
            "normative_pronunciation_separated": True,
            "transcription_and_full_phonetic_analysis_separated": True,
            "adjacent_ru01_semantics_do_not_substitute": True,
            "semantic_admission_by_this_review": False,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "exact_mastery_admissions": 0,
            "false_exact_mastery_admissions": 0,
            "next_status": "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE",
        },
        "policy": {
            "title_route_task_or_fuzzy_inference_allowed": False,
            "content_adequacy_review_is_semantic_admission": False,
            "content_adequacy_review_is_object_closure": False,
            "component_specific_independent_verification_required": True,
            "generic_ru01_attempt_can_emit_exact_component_mastery": False,
            "anonymous_or_device_only_canonical_progress_allowed": False,
            "accepted_demo_scorer_tilda_surfaces_may_change": False,
        },
        "summary": {
            "exact_candidate_content_units": 1,
            "component_specific_verification_items": 5,
            "semantic_admissions": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "exact_mastery_admissions": 0,
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
        print("RU01_PHONETIC_STRESS_CONTENT_ADEQUACY=PASS")
        print("SEMANTIC_ID=" + SEMANTIC)
        print("EXACT_CANDIDATE_CONTENT_UNITS=1")
        print("COMPONENT_SPECIFIC_VERIFICATION_ITEMS=5")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_LEVEL_CLOSURES=0")
        print("EXACT_MASTERY_ADMISSIONS=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
