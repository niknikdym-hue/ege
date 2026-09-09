#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT = PROGRAM / "production-learning-content/RU-PROG-01-SYLLABLE-WAVE-005-v0.1.json"

SEMANTIC = "ru-phonetics-syllable"
TAXONOMY = "phonetic_syllable"
SOURCE_CLAUSES = ["EDSOO59-P187-4.1.5", "OGE-COD-P020-4.1.5"]
VERIFICATION_IDS = ["p01-u7-v1", "p01-u7-v2", "p01-u7-v3", "p01-u7-v4", "p01-u7-v5"]
CONTENT_GIT_BLOB = "24281db6ee3d5cea24656c1e5e0be9b787392a08"
READINESS_GATE = {
    "workflow": "Russian RU01 phonetic syllable candidate content readiness",
    "run_id": 34323472320,
    "head_sha": "e4ad473e0750bf3ff8b917ab541f41317fc1dd38",
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
    require(git_blob_sha(raw) == CONTENT_GIT_BLOB, "syllable content blob drift")
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
    require(exact_docs.get("EDSOO59", {}).get("official_requirement") == "Слог", "EDSOO requirement drift")
    require(exact_docs.get("OGE_COD", {}).get("official_requirement") == "Слог", "OGE requirement drift")

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
        "word_transfer_rules_may_substitute",
        "normative_stress_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "phonetic_transcription_semantic_may_substitute",
        "word_analysis_semantic_may_substitute",
        "vowel_consonant_features_semantic_may_substitute",
        "ambiguous_syllable_boundary_can_be_guessed",
        "generic_ru01_result_can_emit_exact_component_mastery",
    ):
        require(identity.get(key) is False, f"fail-closed identity boundary opened: {key}")

    units = [row for row in data.get("units", []) if isinstance(row, dict)]
    require(len(units) == 1, "exactly one bounded syllable unit required")
    unit = units[0]
    require(unit.get("proposed_semantic_id") == SEMANTIC, "unit semantic drift")

    explanation = unit.get("canonical_explanation") or {}
    explanation_text = (str(explanation.get("short") or "") + "\n" + "\n".join(map(str, explanation.get("boundaries") or []))).lower()
    for token in ("слог", "звуч", "гласн", "перенос", "ударен", "стечени"):
        require(token in explanation_text, f"content boundary missing: {token}")

    minimums = {
        "decision_algorithm": 6,
        "worked_examples": 4,
        "misconceptions": 4,
        "guided_practice": 3,
        "independent_practice": 3,
        "mixed_transfer_practice": 3,
        "retention_items": 2,
        "independent_verification": 5,
    }
    for field, minimum in minimums.items():
        value = unit.get(field)
        require(isinstance(value, list) and len(value) >= minimum, f"learner content too thin: {field}")

    verification = unit["independent_verification"]
    ids = [str(row.get("id")) for row in verification]
    require(ids == VERIFICATION_IDS and len(set(ids)) == len(ids), "component-specific verification set drift")
    skills = {str(row.get("skill")) for row in verification}
    required_skills = {
        "count_syllables_from_established_spoken_form",
        "identify_syllabic_centre",
        "distinguish_syllable_from_adjacent_semantics",
        "respect_ambiguous_syllable_boundary",
        "separate_syllable_from_normative_stress",
    }
    require(required_skills.issubset(skills), "component-specific verification coverage incomplete")
    v3 = next(row for row in verification if row.get("id") == "p01-u7-v3")
    require(v3.get("type") == "selected_response" and v3.get("answer") == "C", "adjacent-semantic verification key drift")
    v4 = next(row for row in verification if row.get("id") == "p01-u7-v4")
    require("не может" in str(v4.get("expected") or "").lower() and "границ" in str(v4.get("expected") or "").lower(), "ambiguous-boundary fail-closed evidence drift")
    v5 = next(row for row in verification if row.get("id") == "p01-u7-v5")
    v5_expected = str(v5.get("expected") or "").lower()
    require("отдельн" in v5_expected and ("stress" in v5_expected or "ударен" in v5_expected), "stress-separation evidence drift")

    peis = unit.get("peis_evidence") or {}
    require(peis.get("semantic_ref") == SEMANTIC, "PEIS semantic drift")
    require(peis.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "PEIS self-admission")
    require(peis.get("verification_ids") == VERIFICATION_IDS, "PEIS verification lineage drift")
    require(peis.get("requires_exact_item_identity") is True, "exact item identity weakened")
    require(peis.get("requires_registered_user_identity_ref") is True, "registered identity weakened")
    require(peis.get("requires_server_owned_received_at") is True, "server timestamp weakened")
    require(peis.get("mastery_emission_before_semantic_acceptance") is False, "pre-acceptance mastery opened")
    require(peis.get("object_mastery_emission_before_exact_object_acceptance") is False, "pre-object mastery opened")
    require(peis.get("false_exact_mastery_admissions") == 0, "false exact mastery drift")

    tutor = unit.get("tutor_grounding") or {}
    forbidden = "\n".join(map(str, tutor.get("forbidden") or [])).lower()
    for token in ("disputed pronunciation", "word-transfer", "normative stress", "canonical", "exact mastery"):
        require(token in forbidden, f"Tutor fail-closed grounding missing: {token}")

    release = data.get("release_boundary") or {}
    require(release.get("semantic_acceptance_effect") == "NONE", "content wave self-admitted semantic")
    require(release.get("object_acceptance_effect") == "NONE", "content wave self-closed object")
    require(release.get("school_canonical_identity_created") is False, "school identity created")
    require(release.get("false_exact_mastery_admissions") == 0, "release false exact mastery drift")
    require(release.get("public_runtime_change") is False, "public runtime change forbidden")
    require(release.get("production_peis_write") is False, "production PEIS write forbidden")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_PHONETIC_SYLLABLE_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION",
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
            "path": "russian-program/production-learning-content/RU-PROG-01-SYLLABLE-WAVE-005-v0.1.json",
            "git_blob_sha1": CONTENT_GIT_BLOB,
            "original_eksamio_explanations": True,
            "original_eksamio_examples": True,
            "component_specific_verification_ids": VERIFICATION_IDS,
            "registered_user_identity_required": True,
            "exact_item_identity_required": True,
            "server_owned_received_at_required": True,
        },
        "adequacy_decision": {
            "content_exact_for_bounded_phonetic_syllable_candidate": True,
            "official_clause_scope_covered": True,
            "word_transfer_separated": True,
            "normative_stress_separated": True,
            "disputed_pronunciation_fail_closed": True,
            "ambiguous_consonant_cluster_boundary_fail_closed": True,
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
        print("RU01_PHONETIC_SYLLABLE_CONTENT_ADEQUACY=PASS")
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
