#!/usr/bin/env python3
"""Fail-closed exact OGE-2026 code 7.24 component slice for issue #161.

Code 7.24 was reviewed against the repository-pinned official OGE_COD source
and the official FIPI 2026 punctuation navigator. Only the complete explicit
six-owner direct-speech/citation/dialogue family from the already-closed OGE
punctuation overlay is reused. Adjacent 7.25 (indirect speech), broad
punctuation analysis, fuzzy inference and module-only inference remain excluded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
OGE_OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
SCHOOL_FREEZE = ENGINE / "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
SOURCE_MANIFEST = ENGINE / "russian-program/source-knowledge/RUSSIAN-OFFICIAL-SOURCE-MANIFEST-v1.0.json"
OGE_COD_SHA256 = "2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a"
CODE = "7.24"
REQUIREMENT_ID = "RSK-OGE_COD-7-24-P026"
ADMISSION_UNIT_ID = "RAU-c44b98adfa9351970445"
PACKET_GROUP = "RUS-SEM-REVIEW-013"
OVERLAY_TOPIC = "direct/indirect speech, citation, dialogue"
OFFICIAL_TEXT = (
    "Знаки препинания при передаче на письме чужой речи (прямая речь, цитирование, диалог). "
    "Пунктуационное оформление предложений с прямой речью. "
    "Пунктуационное оформление диалога на письме"
)
NORMALIZED_MEANING = (
    "Анализировать синтаксическую конструкцию и её нормативность. "
    "Выбирать нормативные знаки препинания в конструкции."
)
OWNERS = (
    "school-direct-speech-base-formatting",
    "school-direct-speech-adjacent-author-words-system",
    "school-direct-speech-author-words-middle-system",
    "school-direct-speech-inside-author-words",
    "school-citation-punctuation-formatting",
    "school-dialogue-replica-punctuation",
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_school(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for obj in inventory.get("objects", []):
        if not isinstance(obj, dict) or obj.get("source_system") != "school_canonical":
            continue
        if (
            obj.get("authority_status") != "current"
            or obj.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY"
            or obj.get("review_status") != "reviewed"
        ):
            continue
        sid = str(obj.get("source_id", ""))
        if not sid or obj.get("current_semantic_refs") != [sid]:
            raise ValueError(f"canonical school identity self-ref drift: {sid}")
        result[sid] = obj
    return result


def build_acceptance() -> dict[str, Any]:
    overlay = json.loads(OGE_OVERLAY.read_text(encoding="utf-8"))
    freeze = json.loads(SCHOOL_FREEZE.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()

    if overlay.get("status") != "OGE_2026_FIPI_ROUTE_OVERLAY_COMPLETE / ZERO_SCHOOL_REOPEN_CANDIDATES":
        raise ValueError("final OGE overlay status drift")
    punctuation = overlay.get("punctuation_overlay")
    if not isinstance(punctuation, dict) or punctuation.get("status") != "ALL_OFFICIAL_OGE_2026_PUNCTUATION_FAMILIES_OWNED_OR_COMPOSITE":
        raise ValueError("final OGE punctuation overlay status drift")
    if int(overlay.get("school_baseline_for_overlay", 0)) != 185 or overlay.get("second_pass_result", {}).get("school_reopen_candidates") != 0:
        raise ValueError("OGE overlay school denominator/reopen drift")
    if freeze.get("final_school_canonical_denominator") != 185 or freeze.get("final_source_closure", {}).get("open_holds") != 0:
        raise ValueError("frozen school denominator is not closed")
    if packet.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("semantic packet is not fail-closed")

    docs = [
        row
        for row in manifest.get("documents", [])
        if row.get("canonical_source_id") == "FIPI-OGE-RU-2026-FINAL" and row.get("document_id") == "OGE_COD"
    ]
    if len(docs) != 1 or docs[0].get("sha256") != OGE_COD_SHA256:
        raise ValueError("pinned OGE_COD SHA drift")
    if manifest.get("source_byte_policy") != "PDF_BYTES_STAY_OUT_OF_GIT; VERIFIED SOURCE ARCHIVE REFERENCES + SHA256 ONLY":
        raise ValueError("official source byte policy drift")

    school = canonical_school(inventory)
    if len(school) != 185:
        raise ValueError(f"expected 185 current reviewed school identities, got {len(school)}")
    if any(ref not in school for ref in OWNERS):
        raise ValueError("direct-speech slice contains a non-current/noncanonical owner")

    families = punctuation.get("families")
    if not isinstance(families, list):
        raise ValueError("OGE punctuation families missing")
    matches = [row for row in families if isinstance(row, dict) and str(row.get("topic")) == OVERLAY_TOPIC]
    if len(matches) != 1 or tuple(matches[0].get("owners", [])) != OWNERS:
        raise ValueError("complete direct-speech/citation/dialogue owner family drift")

    packet_requirements = {
        str(req["requirement_id"]): (group, req)
        for group in packet["semantic_review_groups"]
        for req in group["requirements"]
    }
    source_matches = [
        (rid, group, req)
        for rid, (group, req) in packet_requirements.items()
        if req.get("source_id") == "FIPI-OGE-RU-2026-FINAL"
        and req.get("document_id") == "OGE_COD"
        and str(req.get("code")) == CODE
    ]
    if len(source_matches) != 1:
        raise ValueError("OGE code 7.24 source requirement is not unique")
    requirement_id, group, req = source_matches[0]
    if requirement_id != REQUIREMENT_ID:
        raise ValueError(f"OGE code 7.24 requirement id drift: {requirement_id}")
    if str(group.get("group_id")) != PACKET_GROUP:
        raise ValueError(f"OGE code 7.24 packet group drift: {group.get('group_id')}")

    accounting_by_req: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accounting["dispositions"]:
        for member in row.get("members", []):
            accounting_by_req[str(member["requirement_id"])].append(row)
    units = accounting_by_req.get(requirement_id, [])
    if len(units) != 1 or len(units[0].get("members", [])) != 1:
        raise ValueError("OGE code 7.24 is not a one-member admission unit")
    unit = units[0]
    if str(unit.get("admission_unit_id")) != ADMISSION_UNIT_ID:
        raise ValueError(f"OGE code 7.24 admission id drift: {unit.get('admission_unit_id')}")
    if unit.get("disposition") != "PARTIAL_OR_COMPOSITE" or unit.get("semantic_identity_ref") is not None:
        raise ValueError("unexpected OGE code 7.24 pre-acceptance state")
    if str(unit.get("normalized_meaning")) != NORMALIZED_MEANING:
        raise ValueError("OGE code 7.24 normalized meaning drift")
    if list(unit.get("modules", [])) != ["RU-PROG-09", "RU-PROG-10"] or list(unit.get("routes", [])) != ["oge"]:
        raise ValueError("OGE code 7.24 module/route drift")
    if str(req.get("source_locator")) != "FIPI-OGE-RU-2026-FINAL/OGE_COD p.26 7.24":
        raise ValueError("OGE code 7.24 source locator drift")

    decision = {
        "admission_unit_id": ADMISSION_UNIT_ID,
        "requirement_id": REQUIREMENT_ID,
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "document_id": "OGE_COD",
        "source_locator": "FIPI-OGE-RU-2026-FINAL/OGE_COD p.26 7.24",
        "content_code": CODE,
        "official_content_text_reviewed": OFFICIAL_TEXT,
        "normalized_meaning": NORMALIZED_MEANING,
        "modules": ["RU-PROG-09", "RU-PROG-10"],
        "routes": ["oge"],
        "disposition": "PARTIAL_OR_COMPOSITE",
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
        "canonical_component_refs": list(OWNERS),
        "component_count": len(OWNERS),
        "mapping_mode": "COMPLETE_EXACT_OVERLAY_FAMILY",
        "authority": {
            "official_oge_codifier_sha256": OGE_COD_SHA256,
            "official_oge_codifier_review": "OGE_COD#content_code=7.24",
            "final_oge_overlay": "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json#punctuation_overlay.families[topic=direct/indirect speech, citation, dialogue]",
            "school_denominator": "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json#final_school_canonical_denominator=185",
            "packet_group": PACKET_GROUP,
        },
        "acceptance_reason": "Exact Central-Brain review of pinned official OGE-2026 code 7.24 plus the explicit complete six-owner direct-speech/citation/dialogue family in the closed OGE punctuation overlay. The adjacent 7.25 indirect-speech expansion and broad punctuation-analysis routes remain excluded.",
        "mastery_boundary": {
            "route_or_broad_composite_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
            "accepted_mapping_can_emit_partial_or_composite_evidence": True,
        },
    }

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_DIRECT_SPEECH_CANONICAL_COMPONENT_SLICE",
        "scope": "FIPI_OGE_2026_CODE_7_24_DIRECT_SPEECH_CITATION_DIALOGUE",
        "official_oge_codifier_sha256": OGE_COD_SHA256,
        "object_accounting_sha256": str(accounting["normalized_sha256"]),
        "semantic_packet_sha256": str(packet["normalized_sha256"]),
        "policy": {
            "central_brain_exact_official_source_review_required": True,
            "pinned_oge_codifier_sha_required": True,
            "final_oge_punctuation_overlay_required": True,
            "all_selected_owners_must_be_exact_current_reviewed_canonical_school_ids": True,
            "adjacent_7_25_indirect_speech_expansion_allowed": False,
            "broad_punctuation_analysis_route_allowed": False,
            "keyword_or_fuzzy_mapping_allowed": False,
            "module_only_mapping_allowed": False,
            "generic_composite_attempt_can_exact_master_components": False,
        },
        "summary": {
            "accepted_admission_units": 1,
            "accepted_requirements": 1,
            "accepted_content_codes": 1,
            "canonical_component_refs_unique": len(OWNERS),
            "new_semantic_identities_created": 0,
            "ru_proposal_identities_admitted": 0,
            "false_exact_mastery_admissions": 0,
        },
        "decisions": [decision],
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_acceptance()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_OGE_DIRECT_SPEECH_EXACT_COMPONENT_ACCEPTANCE=PASS")
        for key, value in result["summary"].items():
            print(f"{key}={value}")
        print(f"NORMALIZED_ACCEPTANCE_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
