#!/usr/bin/env python3
"""Fail-closed content-adequacy review for the bounded RU01 whole sound-system candidate.

This review is deliberately non-admitting: it may declare the exact pinned learner
content adequate for a later semantic-acceptance gate, but it cannot itself create
or close a semantic, source object, or mastery state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT = PROGRAM / "production-learning-content" / "RU-PROG-01-SOUND-SYSTEM-INTEGRATION-WAVE-010-v0.1.json"

SEMANTIC = "ru-phonetics-sound-system"
TAXONOMY = "sound_system"
SOURCE_CLAUSES = ["EDSOO59-P181-4.1-C"]
VERIFICATION_IDS = [f"p01-u12-v{i}" for i in range(1, 6)]
FORBIDDEN_COMPONENT_EVIDENCE = [
    *[f"p01-u9-v{i}" for i in range(1, 6)],
    *[f"p01-u10-v{i}" for i in range(1, 6)],
]
CONTENT_GIT_BLOB = "aeba08fe00dbe5626748427e2792e196976b8256"
READINESS_GATE = {
    "workflow": "Russian RU01 sound system content readiness",
    "run_id": 34529979810,
    "head_sha": "ec14cb3f20e475626060891ac5862cb3924fcd53",
    "conclusion": "SUCCESS",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def git_blob_sha(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def text_of(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "\n".join(text_of(child) for child in value.values())
    if isinstance(value, list):
        return "\n".join(text_of(child) for child in value)
    return str(value)


def build_review() -> dict[str, Any]:
    raw = CONTENT.read_bytes()
    require(git_blob_sha(raw) == CONTENT_GIT_BLOB, "sound-system content blob drift")
    data = json.loads(raw.decode("utf-8"))

    require(data.get("schema_version") == "0.1.0", "schema drift")
    require(data.get("status") == "CONTENT_AND_EVIDENCE_READY_SEMANTIC_ACCEPTANCE_REQUIRED", "content status drift")
    require(data.get("subject") == "russian", "subject drift")
    require(data.get("module_id") == "RU-PROG-01", "module drift")

    provenance = [row for row in data.get("source_provenance", []) if isinstance(row, dict)]
    owner = next((row for row in provenance if row.get("kind") == "exact_sound_system_owner_resolution"), None)
    require(owner is not None, "exact sound-system owner-resolution provenance missing")
    require(owner.get("candidate_semantic_id") == SEMANTIC, "candidate semantic drift")
    require(owner.get("source_clause_ids") == SOURCE_CLAUSES, "source-clause drift")
    require(owner.get("admission_unit_id") == "RAU-5a6511267f156745f93c", "admission-unit drift")
    require(owner.get("requirement_id") == "RSK-EDSOO59-4-1-P181", "requirement drift")
    require(owner.get("semantic_review_id") == "RUS-SEM-REVIEW-048", "semantic-review drift")
    coverage_note = str(owner.get("coverage_note") or "").lower()
    require("no single canonical whole-sound-system owner" in coverage_note, "missing no-current-owner boundary")
    require("cannot create the parent semantic" in coverage_note, "component-to-parent prohibition missing")

    prerequisite = next((row for row in provenance if row.get("kind") == "exact_head_prerequisite_gate"), None)
    require(prerequisite is not None, "component-set prerequisite provenance missing")
    require(prerequisite.get("run_id") == 34510774242, "component-set prerequisite run drift")
    require(prerequisite.get("head_sha") == "03397a71a723bed3df27aa27a9e60b2b386e120a", "component-set prerequisite sha drift")
    require(prerequisite.get("conclusion") == "SUCCESS", "component-set prerequisite is not successful")

    components = next((row for row in provenance if row.get("kind") == "accepted_component_semantics"), None)
    require(components is not None, "accepted component-semantic inventory missing")
    require(components.get("component_refs") == ["ru-phonetics-vowel-system", "ru-phonetics-consonant-system"], "component semantic refs drift")
    require(components.get("existing_component_evidence_refs") == FORBIDDEN_COMPONENT_EVIDENCE, "component evidence inventory drift")
    require(components.get("parent_evidence_reuse_allowed") is False, "component evidence reuse opened")

    official = [row for row in provenance if row.get("kind") == "official_program"]
    require(len(official) == 1, "official source missing or duplicated")
    source = official[0]
    require(source.get("source_id") == "EDSOO-RU-5-9-2025", "official source id drift")
    require(source.get("document_id") == "EDSOO59", "official document drift")
    require(source.get("source_locator") == "EDSOO-RU-5-9-2025/EDSOO59 p.181 4.1", "official source locator drift")
    require(str(source.get("official_requirement") or "").lower() == "характеризовать систему звуков", "official requirement drift")

    guard = data.get("copyright_guard") or {}
    require(guard.get("source_passages_copied") == 0, "source bytes copied")
    require(guard.get("learner_explanations") == "ORIGINAL_EKSAMIO", "learner explanation provenance drift")
    require(guard.get("learner_examples") == "ORIGINAL_EKSAMIO", "learner example provenance drift")
    require(guard.get("commercial_textbook_bytes_in_git") == 0, "commercial textbook bytes forbidden")

    identity = data.get("identity_boundary") or {}
    require(identity.get("proposed_semantic_id") == SEMANTIC, "identity semantic drift")
    require(identity.get("source_taxonomy_id") == TAXONOMY, "taxonomy drift")
    require(identity.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "candidate self-admitted")
    require(identity.get("proposed_item_identity_prefix") == "p01-u12", "integrated item lineage drift")
    for key in (
        "vowel_system_semantic_may_substitute_parent",
        "consonant_system_semantic_may_substitute_parent",
        "sound_characterization_semantic_may_substitute_parent",
        "sound_letter_relation_semantic_may_substitute_parent",
        "normative_pronunciation_semantic_may_substitute_parent",
        "normative_stress_semantic_may_substitute_parent",
        "existing_p01_u9_or_u10_evidence_may_be_reused_as_parent_evidence",
        "generic_ru01_result_can_emit_exact_sound_system_mastery",
    ):
        require(identity.get(key) is False, f"fail-closed identity boundary opened: {key}")

    units = [row for row in data.get("units", []) if isinstance(row, dict)]
    require(len(units) == 1, "exactly one bounded sound-system unit required")
    unit = units[0]
    require(unit.get("proposed_semantic_id") == SEMANTIC, "unit semantic drift")

    explanation = unit.get("canonical_explanation") or {}
    explanation_text = text_of(explanation).lower()
    for token in ("систем", "гласн", "согласн", "признак", "букв", "произнош", "удар"):
        require(token in explanation_text, f"content boundary missing: {token}")
    require("две" in explanation_text or "обе" in explanation_text, "two-subsystem integration boundary missing")

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

    algorithm_text = text_of(unit.get("decision_algorithm") or []).lower()
    for token in ("звук", "гласн", "согласн", "признак", "букв", "произнош", "удар"):
        require(token in algorithm_text, f"decision algorithm boundary missing: {token}")
    require("обе" in algorithm_text, "decision algorithm does not require both subsystems")

    verification = unit.get("independent_verification") or []
    ids = [str(row.get("id")) for row in verification]
    require(ids == VERIFICATION_IDS and len(set(ids)) == 5, "integrated verification lineage drift")
    measures = {str(row.get("measures")) for row in verification}
    require(measures == {
        "integrate_vowel_consonant_partition",
        "preserve_subsystem_feature_boundaries",
        "require_integrated_parent_evidence",
        "preserve_sound_letter_boundary_in_system",
        "preserve_sound_system_vs_orthoepy_boundary",
    }, "integrated verification coverage incomplete")
    for row in verification:
        require(row.get("type") == "single_choice", f"verification type drift: {row.get('id')}")
        require(row.get("exact_item_identity_required") is True, f"exact item identity missing: {row.get('id')}")
        require(row.get("registered_user_identity_ref_required") is True, f"registered identity missing: {row.get('id')}")
        require(row.get("received_at_server_required") is True, f"server timestamp missing: {row.get('id')}")

    expected_indices = {"p01-u12-v1": 0, "p01-u12-v2": 1, "p01-u12-v3": 1, "p01-u12-v4": 1, "p01-u12-v5": 2}
    for row in verification:
        require(row.get("correct_option_index") == expected_indices[row["id"]], f"answer-key drift: {row.get('id')}")

    v1 = next(row for row in verification if row.get("id") == "p01-u12-v1")
    v1_text = text_of(v1).lower()
    require("гласн" in v1_text and "согласн" in v1_text and "[а]" in v1_text and "[м’]" in v1_text, "subsystem partition evidence incomplete")
    v2 = next(row for row in verification if row.get("id") == "p01-u12-v2")
    v2_text = text_of(v2).lower()
    require("удар" in v2_text and "звонк" in v2_text and "твёрд" in v2_text, "subsystem feature-boundary evidence incomplete")
    v3 = next(row for row in verification if row.get("id") == "p01-u12-v3")
    v3_text = text_of(v3).lower()
    require("p01-u9" in v3_text and "p01-u10" in v3_text and "нов" in v3_text and "интеграц" in v3_text, "new parent-evidence requirement incomplete")
    v4 = next(row for row in verification if row.get("id") == "p01-u12-v4")
    v4_text = text_of(v4).lower()
    require("букв" in v4_text and "звук" in v4_text, "sound-letter system boundary incomplete")
    v5 = next(row for row in verification if row.get("id") == "p01-u12-v5")
    v5_text = text_of(v5).lower()
    require("произнош" in v5_text and "ударен" in v5_text, "sound-system versus orthoepy boundary incomplete")

    lineage = unit.get("evidence_lineage") or {}
    require(lineage.get("new_integrated_verification_refs") == VERIFICATION_IDS, "new integrated lineage drift")
    require(lineage.get("reused_component_verification_refs") == [], "component evidence reused as parent evidence")
    require(lineage.get("forbidden_parent_substitution_refs") == FORBIDDEN_COMPONENT_EVIDENCE, "forbidden component evidence inventory drift")
    lineage_rule = str(lineage.get("lineage_rule") or "").lower()
    require("new integrated p01-u12" in lineage_rule and "supporting context only" in lineage_rule, "parent lineage rule weakened")

    peis = unit.get("peis_evidence") or {}
    require(peis.get("semantic_ref") == SEMANTIC, "PEIS semantic drift")
    require(peis.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "PEIS self-admission")
    require(peis.get("independent_verification_required") is True, "independent verification requirement weakened")
    require(peis.get("assistance_must_be_recorded") is True, "assistance recording requirement weakened")
    require(peis.get("user_identity_ref") == "REGISTERED_USER_REQUIRED", "registered learner boundary weakened")
    require(peis.get("item_identity") == "EXACT_VERSIONED_ITEM_REQUIRED", "exact item boundary weakened")
    require(peis.get("received_at") == "SERVER_OWNED_TIMESTAMP_REQUIRED", "server-owned timestamp weakened")
    require(peis.get("today_timezone") == "Europe/Moscow", "Today timezone drift")
    require(peis.get("durable_evidence_event_required") is True, "durable EvidenceEvent boundary weakened")
    require(peis.get("durable_outbox_required") is True, "durable outbox boundary weakened")
    require(peis.get("mastery_before_separate_semantic_acceptance") is False, "pre-acceptance mastery opened")
    require(peis.get("generic_ru01_attempt_can_emit_exact_mastery") is False, "generic RU01 exact mastery opened")
    require(peis.get("anonymous_progress_allowed") is False, "anonymous canonical progress opened")
    require(peis.get("device_only_canonical_state_allowed") is False, "device-only canonical state opened")

    tutor = unit.get("tutor_grounding") or {}
    allowed_text = text_of(tutor.get("allowed") or []).lower()
    forbidden_text = text_of(tutor.get("forbidden") or []).lower()
    require("vowel" in allowed_text and "consonant" in allowed_text, "Tutor integrated subsystem grounding missing")
    require("p01-u9" in forbidden_text and "p01-u10" in forbidden_text, "Tutor component-to-parent mastery prohibition missing")
    require("pronunciation" in forbidden_text and "stress" in forbidden_text, "Tutor orthoepy inference prohibition missing")

    admission = data.get("admission_boundary") or {}
    for key in ("semantic_admissions", "object_level_closures", "exact_mastery_admissions", "false_exact_mastery_admissions"):
        require(admission.get(key) == 0, f"{key} must remain zero")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_SOUND_SYSTEM_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION",
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
            "path": "russian-program/production-learning-content/RU-PROG-01-SOUND-SYSTEM-INTEGRATION-WAVE-010-v0.1.json",
            "git_blob_sha1": CONTENT_GIT_BLOB,
            "original_eksamio_explanations": True,
            "original_eksamio_examples": True,
            "new_integrated_verification_ids": VERIFICATION_IDS,
            "forbidden_component_parent_evidence_ids": FORBIDDEN_COMPONENT_EVIDENCE,
            "registered_user_identity_required": True,
            "exact_item_identity_required": True,
            "server_owned_received_at_required": True,
            "durable_evidence_event_required_before_future_canonical_write": True,
        },
        "adequacy_decision": {
            "content_exact_for_bounded_sound_system_candidate": True,
            "official_clause_scope_covered": True,
            "vowel_and_consonant_subsystems_integrated": True,
            "subsystem_feature_boundaries_preserved": True,
            "new_parent_specific_evidence_required": True,
            "old_component_evidence_not_reused_as_parent_evidence": True,
            "sound_letter_boundary_preserved": True,
            "normative_pronunciation_not_inferred": True,
            "normative_stress_not_inferred": True,
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
            "component_evidence_auto_promotes_parent": False,
            "generic_ru01_attempt_can_emit_exact_component_mastery": False,
            "anonymous_or_device_only_canonical_progress_allowed": False,
            "accepted_demo_scorer_tilda_surfaces_may_change": False,
        },
        "summary": {
            "exact_candidate_content_units": 1,
            "new_integrated_verification_items": 5,
            "forbidden_component_parent_evidence_items": 10,
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
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    if args.emit or not args.output:
        print(rendered, end="")
    else:
        print(f"status={result['status']}")
        print(f"normalized_sha256={result['normalized_sha256']}")
        print("semantic_admissions=0")
        print("object_level_closures=0")
        print("exact_mastery_admissions=0")
        print("false_exact_mastery_admissions=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
