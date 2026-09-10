#!/usr/bin/env python3
"""Fail-closed readiness gate for the source-bounded RU01 sound-characterization candidate.

This gate creates no semantic admission, source-object closure, or mastery.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT = PROGRAM / "production-learning-content" / "RU-PROG-01-SOUND-CHARACTERIZATION-WAVE-009-v0.1.json"
OWNER = HERE / "build_ru01_phonetics_broad_header_owner_resolution_current_v23.py"
SEMANTIC = "ru-phonetics-sound-characterization"
CLAUSES = ["EDSOO59-P181-4.1-A"]
VERIFICATION_IDS = [f"p01-u11-v{i}" for i in range(1, 6)]
OWNER_RUN = 34452615277
OWNER_HEAD = "9d517d293f4bba899ab7a268eacde0cc787adcd4"
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
    current_rows = [row for row in provenance if row.get("kind") == "current_v23_owner_resolution"]
    require(len(current_rows) == 1, "current-v23 owner provenance missing or duplicated")
    current = current_rows[0]
    require(current.get("candidate_semantic_id") == SEMANTIC, "candidate semantic drift")
    require(current.get("source_clause_ids") == CLAUSES, "source clause drift")
    require("narrower partial owner" in str(current.get("coverage_note", "")).lower(), "partial-owner boundary missing")

    owner_gate = [row for row in provenance if row.get("kind") == "exact_head_prerequisite_gate"]
    require(len(owner_gate) == 1, "owner gate missing")
    require(owner_gate[0].get("run_id") == OWNER_RUN and owner_gate[0].get("head_sha") == OWNER_HEAD, "owner exact-head drift")
    require(owner_gate[0].get("conclusion") == "SUCCESS", "owner gate not successful")

    gap_gate = [row for row in provenance if row.get("kind") == "candidate_content_gap_gate"]
    require(len(gap_gate) == 1, "gap gate missing")
    require(gap_gate[0].get("run_id") == GAP_RUN and gap_gate[0].get("head_sha") == GAP_HEAD, "gap exact-head drift")
    require(gap_gate[0].get("conclusion") == "SUCCESS", "gap gate not successful")
    require(gap_gate[0].get("result_before_this_wave") == "NO_DEDICATED_CANDIDATE_CONTENT_FOUND", "pre-wave state drift")

    official = [row for row in provenance if row.get("kind") == "official_program"]
    require(len(official) == 1, "official source missing or duplicated")
    require(official[0].get("document_id") == "EDSOO59", "official document drift")
    require(official[0].get("official_requirement") == "Характеризовать звуки", "official scope widened")
    require("p.181 4.1-A" in str(official[0].get("source_locator")), "EDSOO locator drift")

    guard = data.get("copyright_guard") or {}
    require(guard.get("source_passages_copied") == 0, "source passage bytes copied")
    require(guard.get("learner_explanations") == "ORIGINAL_EKSAMIO" and guard.get("learner_examples") == "ORIGINAL_EKSAMIO", "learner content origin drift")
    require(guard.get("commercial_textbook_bytes_in_git") == 0, "commercial textbook bytes admitted")

    identity = data.get("identity_boundary") or {}
    require(identity.get("proposed_semantic_id") == SEMANTIC, "identity drift")
    require(identity.get("source_taxonomy_id") == "sound_characterization", "taxonomy drift")
    require(identity.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "candidate became canonical")
    for key in (
        "vowel_consonant_features_partial_owner_may_substitute",
        "vowel_system_semantic_may_substitute",
        "consonant_system_semantic_may_substitute",
        "sound_system_semantic_may_substitute",
        "sound_letter_relation_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "generic_ru01_result_can_emit_exact_component_mastery",
    ):
        require(identity.get(key) is False, f"boundary opened: {key}")

    owner_text = OWNER.read_text(encoding="utf-8")
    require('"ru-phonetics-sound-characterization"' in owner_text, "current-v23 candidate missing")
    require('"EDSOO59-P181-4.1-A"' in owner_text, "current-v23 source clause drift")
    require('"PARTIAL_CURRENT_OWNER_ONLY_REMAINS_UNRESOLVED"' in owner_text, "current owner status drift")
    require('"ru-phonetics-vowel-consonant-features"' in owner_text, "partial current owner ref drift")
    require("RESOLVE_SOUND_CHARACTERIZATION_WITH_COMPONENT_SPECIFIC_CONTENT_EVIDENCE_OR_PROVE_AN_EXACT_CURRENT OWNER" in owner_text, "current-v23 next-action boundary drift")

    units = data.get("units") or []
    require(len(units) == 1 and units[0].get("proposed_semantic_id") == SEMANTIC, "bounded unit drift")
    unit = units[0]
    explanation = unit.get("canonical_explanation") or {}
    text = " ".join([str(explanation.get("short", "")), *map(str, explanation.get("boundaries") or [])]).lower()
    require("звук" in text and "букв" in text, "sound-letter boundary missing")
    require("гласн" in text and "согласн" in text, "type-specific characterization boundary missing")
    require("звонк" in text and "глух" in text and "твёрд" in text and "мягк" in text, "consonant feature boundary missing")
    require("систем" in text and "произнош" in text, "system/pronunciation boundary missing")

    evidence = unit.get("independent_verification") or []
    require([row.get("id") for row in evidence] == VERIFICATION_IDS, "verification ids drift")
    require(len({row.get("measures") for row in evidence}) == 5, "verification measures not distinct")
    for row in evidence:
        require(row.get("exact_item_identity_required") is True, f"exact item identity missing: {row.get('id')}")
        require(row.get("registered_user_identity_ref_required") is True, f"registered identity missing: {row.get('id')}")
        require(row.get("received_at_server_required") is True, f"server timestamp missing: {row.get('id')}")

    peis = unit.get("peis_evidence") or {}
    require(peis.get("semantic_ref") == SEMANTIC and peis.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "PEIS semantic drift")
    require(peis.get("user_identity_ref") == "REGISTERED_USER_REQUIRED", "registered learner boundary drift")
    require(peis.get("item_identity") == "EXACT_VERSIONED_ITEM_REQUIRED", "item identity boundary drift")
    require(peis.get("received_at") == "SERVER_OWNED_TIMESTAMP_REQUIRED", "server timestamp boundary drift")
    require(peis.get("today_timezone") == "Europe/Moscow", "Today timezone drift")
    require(peis.get("durable_evidence_event_required") is True, "durable evidence event boundary drift")
    require(peis.get("mastery_before_separate_semantic_acceptance") is False, "premature mastery opened")
    require(peis.get("generic_ru01_attempt_can_emit_exact_mastery") is False, "generic exact mastery opened")
    require(peis.get("anonymous_progress_allowed") is False and peis.get("device_only_canonical_state_allowed") is False, "registered-only boundary opened")

    admission = data.get("admission_boundary") or {}
    require(admission.get("semantic_admissions") == 0, "content self-admitted semantic")
    require(admission.get("object_level_closures") == 0, "content self-closed object")
    require(admission.get("exact_mastery_admissions") == 0, "content self-admitted mastery")
    require(admission.get("false_exact_mastery_admissions") == 0, "false exact mastery drift")

    print("RU01_SOUND_CHARACTERIZATION_CANDIDATE_CONTENT_READINESS=PASS")
    print("CANDIDATE_STATUS=PROPOSED_NOT_CANONICAL")
    print("SOURCE_CLAUSES=1")
    print("COMPONENT_SPECIFIC_VERIFICATION_ITEMS=5")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
