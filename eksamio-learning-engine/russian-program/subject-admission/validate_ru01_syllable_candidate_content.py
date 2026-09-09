#!/usr/bin/env python3
"""Exact structural/content-readiness gate for RU01 phonetic syllable candidate.

This gate proves only that the source-backed candidate now has dedicated original
Eksamio learner content and component-specific independent verification. It does
not accept the semantic, close any source object or create mastery.
"""
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT = PROGRAM / "production-learning-content" / "RU-PROG-01-SYLLABLE-WAVE-005-v0.1.json"
OWNER = HERE / "build_ru01_phonetics_broad_header_owner_resolution_review.py"
GAP = HERE / "build_ru01_phonetics_broad_header_candidate_content_gap_review.py"

SEMANTIC_ID = "ru-phonetics-syllable"
EXPECTED_SOURCE_CLAUSES = ["EDSOO59-P187-4.1.5", "OGE-COD-P020-4.1.5"]
EXPECTED_VERIFICATION_IDS = [
    "p01-u7-v1",
    "p01-u7-v2",
    "p01-u7-v3",
    "p01-u7-v4",
    "p01-u7-v5",
]
EDSOO_SHA = "1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d"
OGE_SHA = "2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    data = json.loads(CONTENT.read_text(encoding="utf-8"))

    require(data.get("schema_version") == "0.1.0", "schema drift")
    require(data.get("status") == "CONTENT_AND_EVIDENCE_READY_SEMANTIC_ACCEPTANCE_REQUIRED", "content status drift")
    require(data.get("subject") == "russian", "subject drift")
    require(data.get("module_id") == "RU-PROG-01", "module drift")
    require((data.get("copyright_guard") or {}).get("source_passages_copied") == 0, "copyright guard drift")
    require((data.get("copyright_guard") or {}).get("learner_explanations") == "ORIGINAL_EKSAMIO", "explanation provenance drift")
    require((data.get("copyright_guard") or {}).get("learner_examples") == "ORIGINAL_EKSAMIO", "example provenance drift")
    require((data.get("copyright_guard") or {}).get("commercial_textbook_bytes_in_git") == 0, "commercial bytes forbidden")

    owner = runpy.run_path(str(OWNER))["build_review"]()
    candidate = next(
        row for row in owner.get("proposed_owner_candidates") or []
        if row.get("candidate_semantic_id") == SEMANTIC_ID
    )
    require(candidate.get("candidate_status") == "PROPOSED_NOT_CANONICAL", "candidate unexpectedly canonical")
    require(candidate.get("source_clause_ids") == EXPECTED_SOURCE_CLAUSES, "source clause drift")
    require(candidate.get("source_requirements") == ["RSK-EDSOO59-4-1-P187", "RSK-OGE_COD-4-1-P020"], "source requirement drift")
    require(candidate.get("semantic_boundary") == "PHONETIC_SYLLABLE_SCOPE_ONLY", "candidate boundary drift")
    require(candidate.get("partial_current_owner_refs") == [], "syllable must not inherit partial owner")
    require(candidate.get("semantic_admission") is False, "owner review semantic admission opened")
    require(candidate.get("object_closure") is False, "owner review object closure opened")
    require(candidate.get("mastery_admission") is False, "owner review mastery opened")

    provenance = data.get("source_provenance") or []
    require(any(row.get("document_id") == "EDSOO59" and row.get("document_sha256") == EDSOO_SHA and row.get("official_requirement") == "Слог" for row in provenance), "EDSOO exact provenance missing")
    require(any(row.get("document_id") == "OGE_COD" and row.get("document_sha256") == OGE_SHA and row.get("official_requirement") == "Слог" for row in provenance), "OGE exact provenance missing")
    gap_gate = next((row for row in provenance if row.get("kind") == "candidate_content_gap_gate"), None)
    require(gap_gate == {
        "kind": "candidate_content_gap_gate",
        "workflow": "Russian RU01 phonetics broad-header candidate content gap review",
        "run_id": 34311280167,
        "head_sha": "07a93daf82b66f5357d8b3bac8b03522b8afa135",
        "conclusion": "SUCCESS",
        "result_before_this_wave": "NO_DEDICATED_CANDIDATE_CONTENT_FOUND",
    }, "exact prior content-gap gate drift")

    identity = data.get("identity_boundary") or {}
    require(identity.get("proposed_semantic_id") == SEMANTIC_ID, "identity semantic drift")
    require(identity.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "identity status drift")
    for key in [
        "word_transfer_rules_may_substitute",
        "normative_stress_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "phonetic_transcription_semantic_may_substitute",
        "word_analysis_semantic_may_substitute",
        "vowel_consonant_features_semantic_may_substitute",
        "ambiguous_syllable_boundary_can_be_guessed",
        "generic_ru01_result_can_emit_exact_component_mastery",
    ]:
        require(identity.get(key) is False, f"fail-closed identity flag opened: {key}")

    units = data.get("units") or []
    require(len(units) == 1, "exactly one syllable unit required")
    unit = units[0]
    require(unit.get("proposed_semantic_id") == SEMANTIC_ID, "unit semantic drift")
    explanation = unit.get("canonical_explanation") or {}
    require(len(explanation.get("boundaries") or []) >= 7, "insufficient boundary coverage")
    require(len(unit.get("decision_algorithm") or []) >= 6, "insufficient decision algorithm")
    require(len(unit.get("worked_examples") or []) >= 4, "insufficient worked examples")
    require(len(unit.get("misconceptions") or []) >= 4, "insufficient misconceptions")
    require(len(unit.get("guided_practice") or []) >= 3, "insufficient guided practice")
    require(len(unit.get("independent_practice") or []) >= 3, "insufficient independent practice")
    require(len(unit.get("mixed_transfer_practice") or []) >= 3, "insufficient transfer practice")
    require(len(unit.get("retention_items") or []) >= 2, "insufficient retention practice")

    verification = unit.get("independent_verification") or []
    verification_ids = [str(row.get("id")) for row in verification]
    require(verification_ids == EXPECTED_VERIFICATION_IDS, "component-specific verification ids drift")
    require(len(set(verification_ids)) == len(verification_ids), "duplicate verification id")
    skills = {str(row.get("skill")) for row in verification}
    require("count_syllables_from_established_spoken_form" in skills, "count-syllables evidence missing")
    require("distinguish_syllable_from_adjacent_semantics" in skills, "adjacent-semantic boundary evidence missing")
    require("respect_ambiguous_syllable_boundary" in skills, "fail-closed boundary evidence missing")
    require("separate_syllable_from_normative_stress" in skills, "stress separation evidence missing")

    peis = unit.get("peis_evidence") or {}
    require(peis.get("semantic_ref") == SEMANTIC_ID, "PEIS semantic drift")
    require(peis.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "PEIS candidate unexpectedly canonical")
    require(peis.get("verification_ids") == EXPECTED_VERIFICATION_IDS, "PEIS verification set drift")
    require(peis.get("requires_exact_item_identity") is True, "exact item identity required")
    require(peis.get("requires_registered_user_identity_ref") is True, "registered identity required")
    require(peis.get("requires_server_owned_received_at") is True, "server timestamp required")
    require(peis.get("mastery_emission_before_semantic_acceptance") is False, "pre-acceptance mastery forbidden")
    require(peis.get("object_mastery_emission_before_exact_object_acceptance") is False, "pre-object mastery forbidden")
    require(peis.get("false_exact_mastery_admissions") == 0, "false exact mastery drift")

    release = data.get("release_boundary") or {}
    require(release.get("semantic_acceptance_effect") == "NONE", "content wave must not accept semantic")
    require(release.get("object_acceptance_effect") == "NONE", "content wave must not close object")
    require(release.get("school_canonical_identity_created") is False, "content wave cannot create school identity")
    require(release.get("false_exact_mastery_admissions") == 0, "release false exact mastery drift")
    require(release.get("public_runtime_change") is False, "public runtime change forbidden")
    require(release.get("production_peis_write") is False, "production PEIS write forbidden")

    gap = runpy.run_path(str(GAP))["build_review"]()
    rows = {row["candidate_semantic_id"]: row for row in gap.get("candidates") or []}
    require(rows[SEMANTIC_ID]["content_evidence_status"] == "CONTENT_AND_EVIDENCE_PRESENT_REQUIRES_SEPARATE_ADEQUACY_REVIEW", "syllable content not recognized by gap review")
    require(rows[SEMANTIC_ID]["semantic_admission"] is False, "gap review semantic admission opened")
    require(rows[SEMANTIC_ID]["object_closure"] is False, "gap review object closure opened")
    require(rows[SEMANTIC_ID]["mastery_admission"] is False, "gap review mastery opened")
    summary = gap.get("summary") or {}
    require(summary.get("proposed_owner_candidates") == 6, "candidate denominator drift")
    require(summary.get("candidates_missing_dedicated_content") == 5, "expected five remaining content gaps")
    require(summary.get("candidates_with_content_but_no_component_evidence") == 0, "unexpected evidence-less candidate content")
    require(summary.get("candidates_with_content_and_evidence_requiring_review") == 1, "expected one candidate ready for adequacy review")
    require(summary.get("semantic_admissions") == 0, "gap review semantic admission drift")
    require(summary.get("object_level_closures") == 0, "gap review object closure drift")
    require(summary.get("exact_mastery_admissions") == 0, "gap review exact mastery drift")
    require(summary.get("false_exact_mastery_admissions") == 0, "gap review false exact mastery drift")

    print("RU01_SYLLABLE_CANDIDATE_CONTENT_READINESS=PASS")
    print("SEMANTIC_ID=" + SEMANTIC_ID)
    print("COMPONENT_SPECIFIC_VERIFICATION_IDS=" + ",".join(EXPECTED_VERIFICATION_IDS))
    print("REMAINING_BROAD_HEADER_CANDIDATE_CONTENT_GAPS=5")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
