#!/usr/bin/env python3
"""Fail-closed readiness gate for source-bounded generic RU01 phonetic-stress content.

This gate creates no semantic admission, object closure or mastery. It proves only
that the remote content bundle is tied to the already-successful exact owner
resolution, has component-specific evidence, and cannot be confused with
normative orthoepic stress selection or normative pronunciation.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT = PROGRAM / "production-learning-content" / "RU-PROG-01-PHONETIC-STRESS-WAVE-006-v0.1.json"
OWNER = HERE / "build_ru01_phonetics_broad_header_owner_resolution_review.py"

SEMANTIC = "ru-phonetics-stress"
CLAUSES = ["EDSOO59-P187-4.1.6", "OGE-COD-P020-4.1.6"]
VERIFICATION_IDS = [f"p01-u8-v{i}" for i in range(1, 6)]
OWNER_RUN = 34306870268
OWNER_HEAD = "41dc6749d96697f393a11e67ca3da36ab73e6aa1"
GAP_RUN = 34311280167
GAP_HEAD = "07a93daf82b66f5357d8b3bac8b03522b8afa135"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    require(data.get("schema_version") == "0.1.0", "schema drift")
    require(data.get("status") == "CONTENT_AND_EVIDENCE_READY_SEMANTIC_ACCEPTANCE_REQUIRED", "content status drift")
    require(data.get("subject") == "russian" and data.get("module_id") == "RU-PROG-01", "module boundary drift")

    provenance = data.get("source_provenance") or []
    owner_rows = [row for row in provenance if row.get("kind") == "bounded_owner_resolution"]
    require(len(owner_rows) == 1, "owner provenance missing or duplicated")
    owner_row = owner_rows[0]
    require(owner_row.get("candidate_semantic_id") == SEMANTIC, "candidate semantic drift")
    require(owner_row.get("source_clause_ids") == CLAUSES, "exact source-clause drift")

    owner_gate = [row for row in provenance if row.get("kind") == "exact_head_prerequisite_gate"]
    require(len(owner_gate) == 1, "owner exact-head gate missing")
    require(owner_gate[0].get("run_id") == OWNER_RUN, "owner run drift")
    require(owner_gate[0].get("head_sha") == OWNER_HEAD, "owner head drift")
    require(owner_gate[0].get("conclusion") == "SUCCESS", "owner gate not successful")

    gap_gate = [row for row in provenance if row.get("kind") == "candidate_content_gap_gate"]
    require(len(gap_gate) == 1, "gap gate provenance missing")
    require(gap_gate[0].get("run_id") == GAP_RUN and gap_gate[0].get("head_sha") == GAP_HEAD, "gap gate drift")
    require(gap_gate[0].get("conclusion") == "SUCCESS", "gap gate not successful")
    require(gap_gate[0].get("result_before_this_wave") == "NO_DEDICATED_CANDIDATE_CONTENT_FOUND", "pre-wave content state drift")

    official = [row for row in provenance if row.get("kind") in {"official_program", "official_codifier"}]
    require(len(official) == 2, "official source pair missing")
    require({row.get("official_requirement") for row in official} == {"Ударение"}, "official scope widened")
    require({row.get("document_id") for row in official} == {"EDSOO59", "OGE_COD"}, "official documents drift")
    require(any("4.1.6" in str(row.get("source_locator")) for row in official if row.get("document_id") == "EDSOO59"), "EDSOO clause locator drift")
    require(any("4.1.6" in str(row.get("source_locator")) for row in official if row.get("document_id") == "OGE_COD"), "OGE clause locator drift")

    copyright_guard = data.get("copyright_guard") or {}
    require(copyright_guard.get("source_passages_copied") == 0, "source passage bytes copied")
    require(copyright_guard.get("learner_explanations") == "ORIGINAL_EKSAMIO", "learner explanation origin drift")
    require(copyright_guard.get("learner_examples") == "ORIGINAL_EKSAMIO", "learner example origin drift")
    require(copyright_guard.get("commercial_textbook_bytes_in_git") == 0, "commercial textbook bytes admitted")

    identity = data.get("identity_boundary") or {}
    require(identity.get("proposed_semantic_id") == SEMANTIC, "identity semantic drift")
    require(identity.get("source_taxonomy_id") == "phonetic_stress", "taxonomy drift")
    require(identity.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "candidate became canonical without acceptance")
    require(identity.get("normative_orthoepy_stress_semantic_may_substitute") is False, "normative stress substitution opened")
    require(identity.get("normative_pronunciation_semantic_may_substitute") is False, "normative pronunciation substitution opened")
    require(identity.get("spelling_may_determine_unmarked_stress") is False, "spelling inference opened")
    require(identity.get("syllable_count_alone_may_determine_stress") is False, "syllable-count inference opened")
    require(identity.get("generic_ru01_result_can_emit_exact_component_mastery") is False, "generic exact mastery opened")

    units = data.get("units") or []
    require(len(units) == 1, "generic stress content must remain one bounded unit")
    unit = units[0]
    require(unit.get("proposed_semantic_id") == SEMANTIC, "unit semantic drift")
    explanation = unit.get("canonical_explanation") or {}
    text = " ".join([str(explanation.get("short", "")), *map(str, explanation.get("boundaries") or [])]).lower()
    require("норматив" in text and "орфоэп" in text, "normative-stress separation not explicit")
    require("количество слогов" in text or "число слогов" in text, "syllable-count separation not explicit")
    require("произнош" in text, "pronunciation boundary not explicit")

    evidence = unit.get("independent_verification") or []
    require([row.get("id") for row in evidence] == VERIFICATION_IDS, "component-specific verification ids drift")
    require(len({row.get("measures") for row in evidence}) == 5, "verification measures must remain distinct")
    for row in evidence:
        require(row.get("exact_item_identity_required") is True, f"exact item identity missing: {row.get('id')}")
        require(row.get("registered_user_identity_ref_required") is True, f"registered identity missing: {row.get('id')}")
        require(row.get("received_at_server_required") is True, f"server timestamp missing: {row.get('id')}")

    peis = unit.get("peis_evidence") or {}
    require(peis.get("semantic_ref") == SEMANTIC and peis.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "PEIS semantic boundary drift")
    require(peis.get("user_identity_ref") == "REGISTERED_USER_REQUIRED", "registered learner boundary drift")
    require(peis.get("item_identity") == "EXACT_VERSIONED_ITEM_REQUIRED", "exact item boundary drift")
    require(peis.get("received_at") == "SERVER_OWNED_TIMESTAMP_REQUIRED", "server-owned timestamp boundary drift")
    require(peis.get("today_timezone") == "Europe/Moscow", "Today timezone drift")
    require(peis.get("mastery_before_separate_semantic_acceptance") is False, "premature mastery opened")
    require(peis.get("generic_ru01_attempt_can_emit_exact_mastery") is False, "generic RU01 mastery opened")
    require(peis.get("anonymous_progress_allowed") is False, "anonymous canonical progress opened")
    require(peis.get("device_only_canonical_state_allowed") is False, "device-only canonical state opened")

    admission = data.get("admission_boundary") or {}
    require(admission.get("semantic_admissions") == 0, "content self-admitted semantic")
    require(admission.get("object_level_closures") == 0, "content self-closed source object")
    require(admission.get("exact_mastery_admissions") == 0, "content self-admitted exact mastery")
    require(admission.get("false_exact_mastery_admissions") == 0, "false exact mastery drift")

    owner_text = OWNER.read_text(encoding="utf-8")
    require('"ru-phonetics-stress"' in owner_text, "owner-resolution candidate missing")
    require('"EDSOO59-P187-4.1.6", "OGE-COD-P020-4.1.6"' in owner_text, "owner-resolution source clauses drift")
    require("NORMATIVE_ORTHOEPY_STRESS_SELECTION_MUST_NOT_SUBSTITUTE" in owner_text, "owner-resolution normative-stress guard missing")

    print("RU01_PHONETIC_STRESS_CANDIDATE_CONTENT_READINESS=PASS")
    print("CANDIDATE_STATUS=PROPOSED_NOT_CANONICAL")
    print("SOURCE_CLAUSES=2")
    print("COMPONENT_SPECIFIC_VERIFICATION_ITEMS=5")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
