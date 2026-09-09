#!/usr/bin/env python3
"""Fail-closed readiness gate for the source-bounded RU01 vowel-system candidate.

No semantic admission, source-object closure, or mastery is created by this gate.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT = PROGRAM / "production-learning-content" / "RU-PROG-01-VOWEL-SYSTEM-WAVE-007-v0.1.json"
OWNER = HERE / "build_ru01_phonetics_broad_header_owner_resolution_review.py"
SEMANTIC = "ru-phonetics-vowel-system"
CLAUSES = ["EDSOO59-P187-4.1.1", "OGE-COD-P020-4.1.1"]
VERIFICATION_IDS = [f"p01-u9-v{i}" for i in range(1, 6)]
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
    require(owner_rows[0].get("candidate_semantic_id") == SEMANTIC, "candidate semantic drift")
    require(owner_rows[0].get("source_clause_ids") == CLAUSES, "source clause drift")

    owner_gate = [row for row in provenance if row.get("kind") == "exact_head_prerequisite_gate"]
    require(len(owner_gate) == 1, "owner gate missing")
    require(owner_gate[0].get("run_id") == OWNER_RUN and owner_gate[0].get("head_sha") == OWNER_HEAD, "owner exact-head drift")
    require(owner_gate[0].get("conclusion") == "SUCCESS", "owner gate not successful")

    gap_gate = [row for row in provenance if row.get("kind") == "candidate_content_gap_gate"]
    require(len(gap_gate) == 1, "gap gate missing")
    require(gap_gate[0].get("run_id") == GAP_RUN and gap_gate[0].get("head_sha") == GAP_HEAD, "gap exact-head drift")
    require(gap_gate[0].get("conclusion") == "SUCCESS", "gap gate not successful")
    require(gap_gate[0].get("result_before_this_wave") == "NO_DEDICATED_CANDIDATE_CONTENT_FOUND", "pre-wave state drift")

    official = [row for row in provenance if row.get("kind") in {"official_program", "official_codifier"}]
    require(len(official) == 2, "official source pair missing")
    require({row.get("official_requirement") for row in official} == {"Система гласных звуков"}, "official scope widened")
    require({row.get("document_id") for row in official} == {"EDSOO59", "OGE_COD"}, "official documents drift")
    require(any("4.1.1" in str(row.get("source_locator")) for row in official if row.get("document_id") == "EDSOO59"), "EDSOO locator drift")
    require(any("4.1.1" in str(row.get("source_locator")) for row in official if row.get("document_id") == "OGE_COD"), "OGE locator drift")

    guard = data.get("copyright_guard") or {}
    require(guard.get("source_passages_copied") == 0, "source passage bytes copied")
    require(guard.get("learner_explanations") == "ORIGINAL_EKSAMIO" and guard.get("learner_examples") == "ORIGINAL_EKSAMIO", "learner content origin drift")
    require(guard.get("commercial_textbook_bytes_in_git") == 0, "commercial textbook bytes admitted")

    identity = data.get("identity_boundary") or {}
    require(identity.get("proposed_semantic_id") == SEMANTIC, "identity drift")
    require(identity.get("source_taxonomy_id") == "vowel_system", "taxonomy drift")
    require(identity.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "candidate became canonical")
    for key in (
        "vowel_consonant_features_partial_owner_may_substitute",
        "consonant_system_semantic_may_substitute",
        "sound_letter_relation_semantic_may_substitute",
        "sound_composition_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "normative_stress_semantic_may_substitute",
        "generic_ru01_result_can_emit_exact_component_mastery",
    ):
        require(identity.get(key) is False, f"boundary opened: {key}")

    units = data.get("units") or []
    require(len(units) == 1 and units[0].get("proposed_semantic_id") == SEMANTIC, "bounded unit drift")
    unit = units[0]
    explanation = unit.get("canonical_explanation") or {}
    text = " ".join([str(explanation.get("short", "")), *map(str, explanation.get("boundaries") or [])]).lower()
    require("гласн" in text and "букв" in text, "sound-letter boundary missing")
    require("согласн" in text, "consonant-system boundary missing")
    require("удар" in text and "произнош" in text, "stress/pronunciation boundary missing")

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

    owner_text = OWNER.read_text(encoding="utf-8")
    require('"ru-phonetics-vowel-system"' in owner_text, "owner candidate missing")
    require('"EDSOO59-P187-4.1.1", "OGE-COD-P020-4.1.1"' in owner_text, "owner clauses drift")
    require("FULL_VOWEL_SYSTEM_SCOPE" in owner_text, "owner boundary drift")

    print("RU01_VOWEL_SYSTEM_CANDIDATE_CONTENT_READINESS=PASS")
    print("CANDIDATE_STATUS=PROPOSED_NOT_CANONICAL")
    print("SOURCE_CLAUSES=2")
    print("COMPONENT_SPECIFIC_VERIFICATION_ITEMS=5")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
