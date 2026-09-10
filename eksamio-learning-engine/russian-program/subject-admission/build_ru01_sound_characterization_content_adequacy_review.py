#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT = PROGRAM / "production-learning-content" / "RU-PROG-01-SOUND-CHARACTERIZATION-WAVE-009-v0.1.json"

SEMANTIC = "ru-phonetics-sound-characterization"
TAXONOMY = "sound_characterization"
SOURCE_CLAUSES = ["EDSOO59-P181-4.1-A"]
VERIFICATION_IDS = ["p01-u11-v1", "p01-u11-v2", "p01-u11-v3", "p01-u11-v4", "p01-u11-v5"]
CONTENT_GIT_BLOB = "b150eb27fa112034b96d4bdb7c6d2f631c2b5979"
READINESS_GATE = {
    "workflow": "Russian RU01 sound characterization candidate content readiness",
    "run_id": 34457434857,
    "head_sha": "a185d5f5e957d5ed602d7a5dafbecad86e19bc24",
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
    require(git_blob_sha(raw) == CONTENT_GIT_BLOB, "sound-characterization content blob drift")
    data = json.loads(raw.decode("utf-8"))

    require(data.get("schema_version") == "0.1.0", "schema drift")
    require(data.get("status") == "CONTENT_AND_EVIDENCE_READY_SEMANTIC_ACCEPTANCE_REQUIRED", "content status drift")
    require(data.get("subject") == "russian" and data.get("module_id") == "RU-PROG-01", "module drift")

    provenance = [row for row in data.get("source_provenance", []) if isinstance(row, dict)]
    owner = next((row for row in provenance if row.get("kind") == "current_v23_owner_resolution"), None)
    require(owner is not None, "current-v23 owner-resolution provenance missing")
    require(owner.get("candidate_semantic_id") == SEMANTIC, "candidate semantic drift")
    require(owner.get("source_clause_ids") == SOURCE_CLAUSES, "source-clause drift")
    coverage_note = str(owner.get("coverage_note") or "").lower()
    require("narrower partial owner" in coverage_note, "partial-current-owner boundary missing")

    readiness = next((row for row in provenance if row.get("kind") == "exact_head_prerequisite_gate"), None)
    require(readiness is not None, "owner prerequisite gate missing")
    require(readiness.get("conclusion") == "SUCCESS", "owner prerequisite gate not successful")

    official = [row for row in provenance if row.get("kind") == "official_program"]
    require(len(official) == 1, "official source missing or duplicated")
    source = official[0]
    require(source.get("source_id") == "EDSOO-RU-5-9-2025", "official source id drift")
    require(source.get("document_id") == "EDSOO59", "official document drift")
    require(source.get("source_locator") == "EDSOO-RU-5-9-2025/EDSOO59 p.181 4.1-A", "official source locator drift")
    require(source.get("official_requirement") == "Характеризовать звуки", "official requirement drift")

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
        "vowel_consonant_features_partial_owner_may_substitute",
        "vowel_system_semantic_may_substitute",
        "consonant_system_semantic_may_substitute",
        "sound_system_semantic_may_substitute",
        "sound_letter_relation_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "generic_ru01_result_can_emit_exact_component_mastery",
    ):
        require(identity.get(key) is False, f"fail-closed identity boundary opened: {key}")

    units = [row for row in data.get("units", []) if isinstance(row, dict)]
    require(len(units) == 1, "exactly one bounded sound-characterization unit required")
    unit = units[0]
    require(unit.get("proposed_semantic_id") == SEMANTIC, "unit semantic drift")

    explanation = unit.get("canonical_explanation") or {}
    explanation_text = (str(explanation.get("short") or "") + "\n" + "\n".join(map(str, explanation.get("boundaries") or []))).lower()
    for token in ("звук", "букв", "гласн", "согласн", "звонк", "глух", "твёрд", "мягк", "систем", "произнош"):
        require(token in explanation_text, f"content boundary missing: {token}")
    require("одн" in explanation_text or "конкрет" in explanation_text, "single-sound scope missing")

    minimums = {
        "decision_algorithm": 5,
        "worked_examples": 3,
        "guided_practice": 2,
        "independent_practice": 3,
        "mixed_transfer_practice": 2,
        "retention_items": 2,
        "independent_verification": 5,
    }
    for field, minimum in minimums.items():
        value = unit.get(field)
        require(isinstance(value, list) and len(value) >= minimum, f"learner content too thin: {field}")

    algorithm_text = "\n".join(map(str, unit.get("decision_algorithm") or [])).lower()
    require("конкрет" in algorithm_text and "звук" in algorithm_text, "decision algorithm sound-object boundary incomplete")
    require("гласн" in algorithm_text and "согласн" in algorithm_text, "decision algorithm type split incomplete")
    require("букв" in algorithm_text, "decision algorithm sound-letter boundary incomplete")
    require("произнош" in algorithm_text, "decision algorithm pronunciation boundary incomplete")
    require("систем" in algorithm_text, "decision algorithm whole-system boundary incomplete")

    verification = unit.get("independent_verification") or []
    ids = [str(row.get("id")) for row in verification]
    require(ids == VERIFICATION_IDS and len(set(ids)) == len(ids), "component-specific verification set drift")
    measures = {str(row.get("measures")) for row in verification}
    require(
        measures
        == {
            "characterize_presented_consonant",
            "characterize_presented_vowel",
            "preserve_sound_letter_boundary",
            "select_type_specific_features",
            "preserve_characterization_scope_boundary",
        },
        "component-specific verification coverage incomplete",
    )
    for row in verification:
        require(row.get("exact_item_identity_required") is True, f"exact item identity missing: {row.get('id')}")
        require(row.get("registered_user_identity_ref_required") is True, f"registered identity missing: {row.get('id')}")
        require(row.get("received_at_server_required") is True, f"server timestamp missing: {row.get('id')}")

    v1 = next(row for row in verification if row.get("id") == "p01-u11-v1")
    require(v1.get("correct_option_index") == 1, "presented-consonant evidence drift")
    v1_text = (str(v1.get("prompt") or "") + " " + " ".join(map(str, v1.get("options") or []))).lower()
    require("[м’]" in v1_text and "звонк" in v1_text and "мягк" in v1_text, "presented-consonant feature evidence incomplete")

    v2 = next(row for row in verification if row.get("id") == "p01-u11-v2")
    require(v2.get("correct_option_index") == 0, "presented-vowel evidence drift")
    v2_text = (str(v2.get("prompt") or "") + " " + " ".join(map(str, v2.get("options") or []))).lower()
    require("[а]" in v2_text and "гласн" in v2_text and "удар" in v2_text, "presented-vowel feature evidence incomplete")

    v3 = next(row for row in verification if row.get("id") == "p01-u11-v3")
    require(v3.get("correct_option_index") == 1, "sound-letter evidence drift")
    v3_text = (str(v3.get("prompt") or "") + " " + " ".join(map(str, v3.get("options") or []))).lower()
    require("букв" in v3_text and "звук" in v3_text, "sound-letter evidence boundary incomplete")

    v4 = next(row for row in verification if row.get("id") == "p01-u11-v4")
    require(v4.get("correct_option_index") == 1, "type-specific feature evidence drift")
    v4_text = (str(v4.get("prompt") or "") + " " + " ".join(map(str, v4.get("options") or []))).lower()
    require("согласн" in v4_text and "звонк" in v4_text and "глух" in v4_text and "твёрд" in v4_text and "мягк" in v4_text, "type-specific feature evidence incomplete")

    v5 = next(row for row in verification if row.get("id") == "p01-u11-v5")
    require(v5.get("correct_option_index") == 0, "scope-boundary evidence drift")
    v5_text = (str(v5.get("prompt") or "") + " " + " ".join(map(str, v5.get("options") or []))).lower()
    require("один" in v5_text and "систем" in v5_text and "произнош" in v5_text, "scope-boundary evidence incomplete")

    peis = unit.get("peis_evidence") or {}
    require(peis.get("semantic_ref") == SEMANTIC, "PEIS semantic drift")
    require(peis.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "PEIS self-admission")
    require(peis.get("user_identity_ref") == "REGISTERED_USER_REQUIRED", "registered learner boundary weakened")
    require(peis.get("item_identity") == "EXACT_VERSIONED_ITEM_REQUIRED", "exact item boundary weakened")
    require(peis.get("received_at") == "SERVER_OWNED_TIMESTAMP_REQUIRED", "server-owned timestamp weakened")
    require(peis.get("today_timezone") == "Europe/Moscow", "Today timezone drift")
    require(peis.get("durable_evidence_event_required") is True, "durable evidence boundary weakened")
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
        "status": "CENTRAL_BRAIN_RU01_SOUND_CHARACTERIZATION_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION",
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
            "path": "russian-program/production-learning-content/RU-PROG-01-SOUND-CHARACTERIZATION-WAVE-009-v0.1.json",
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
            "content_exact_for_bounded_sound_characterization_candidate": True,
            "official_clause_scope_covered": True,
            "explicit_sound_object_required_before_characterization": True,
            "vowel_and_consonant_feature_paths_distinguished": True,
            "sound_letter_boundary_preserved": True,
            "partial_vowel_consonant_feature_owner_not_promoted_to_exact_owner": True,
            "vowel_system_not_substituted": True,
            "consonant_system_not_substituted": True,
            "whole_sound_system_not_substituted": True,
            "normative_pronunciation_not_inferred": True,
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
        print("RU01_SOUND_CHARACTERIZATION_CONTENT_ADEQUACY=PASS")
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
