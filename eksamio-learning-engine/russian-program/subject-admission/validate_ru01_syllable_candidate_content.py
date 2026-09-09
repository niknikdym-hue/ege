#!/usr/bin/env python3
"""Exact structural/content-readiness gate for RU01 phonetic syllable candidate.

This gate proves only that the already source-backed candidate now has dedicated
original Eksamio learner content and component-specific independent verification.
It deliberately does not rebuild the expensive whole-subject owner/gap chain:
those prerequisite reviews are pinned to exact successful remote runs in the
content provenance, while the workflow proves the post-gate diff is syllable-only.
No semantic, source-object or mastery admission is created here.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT = PROGRAM / "production-learning-content" / "RU-PROG-01-SYLLABLE-WAVE-005-v0.1.json"

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
OWNER_GATE = {
    "kind": "exact_head_prerequisite_gate",
    "workflow": "Russian RU01 phonetics broad-header owner resolution review",
    "run_id": 34306870268,
    "head_sha": "41dc6749d96697f393a11e67ca3da36ab73e6aa1",
    "conclusion": "SUCCESS",
}
GAP_GATE = {
    "kind": "candidate_content_gap_gate",
    "workflow": "Russian RU01 phonetics broad-header candidate content gap review",
    "run_id": 34311280167,
    "head_sha": "07a93daf82b66f5357d8b3bac8b03522b8afa135",
    "conclusion": "SUCCESS",
    "result_before_this_wave": "NO_DEDICATED_CANDIDATE_CONTENT_FOUND",
}


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

    provenance = data.get("source_provenance") or []
    owner_resolution = next((row for row in provenance if row.get("kind") == "bounded_owner_resolution"), None)
    require(owner_resolution is not None, "bounded owner resolution provenance missing")
    require(owner_resolution.get("candidate_semantic_id") == SEMANTIC_ID, "owner candidate semantic drift")
    require(owner_resolution.get("source_clause_ids") == EXPECTED_SOURCE_CLAUSES, "source clause drift")
    require(OWNER_GATE in provenance, "exact successful owner-resolution prerequisite gate drift")
    require(GAP_GATE in provenance, "exact successful pre-wave gap gate drift")

    require(any(row.get("document_id") == "EDSOO59" and row.get("document_sha256") == EDSOO_SHA and row.get("official_requirement") == "Слог" for row in provenance), "EDSOO exact provenance missing")
    require(any(row.get("document_id") == "OGE_COD" and row.get("document_sha256") == OGE_SHA and row.get("official_requirement") == "Слог" for row in provenance), "OGE exact provenance missing")

    identity = data.get("identity_boundary") or {}
    require(identity.get("proposed_semantic_id") == SEMANTIC_ID, "identity semantic drift")
    require(identity.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "identity status drift")
    require(identity.get("object_level_admission_effect") == "NONE_UNTIL_SEPARATE_SEMANTIC_AND_EXACT_OBJECT_ACCEPTANCE", "object boundary drift")
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

    print("RU01_SYLLABLE_CANDIDATE_CONTENT_READINESS=PASS")
    print("SEMANTIC_ID=" + SEMANTIC_ID)
    print("SOURCE_CLAUSES=" + ",".join(EXPECTED_SOURCE_CLAUSES))
    print("COMPONENT_SPECIFIC_VERIFICATION_IDS=" + ",".join(EXPECTED_VERIFICATION_IDS))
    print("PREREQUISITE_OWNER_GATE=34306870268@41dc6749d96697f393a11e67ca3da36ab73e6aa1:SUCCESS")
    print("PREREQUISITE_GAP_GATE=34311280167@07a93daf82b66f5357d8b3bac8b03522b8afa135:SUCCESS")
    print("REMAINING_BROAD_HEADER_CANDIDATE_CONTENT_GAPS=5")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
