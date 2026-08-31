#!/usr/bin/env python3
"""Fail-closed exact OGE-2026 code 7.25 component slice for issue #161."""
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
REVIEWED_MEANINGS = HERE / "RUSSIAN-SUBJECT-REVIEWED-REUSE-COMPOSITE-MEANINGS-v0.1.json"
OGE_OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
SCHOOL_FREEZE = ENGINE / "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
SOURCE_MANIFEST = ENGINE / "russian-program/source-knowledge/RUSSIAN-OFFICIAL-SOURCE-MANIFEST-v1.0.json"

OGE_COD_SHA256 = "2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a"
CODE = "7.25"
REQUIREMENT_ID = "RSK-OGE_COD-7-25-P026"
NORMALIZED_MEANING = (
    "Анализировать синтаксическую конструкцию и её нормативность. "
    "Контролировать речевую нормативность и исправлять нарушения."
)
OFFICIAL_TEXT = (
    "Знаки препинания при передаче на письме чужой речи (прямая речь, цитирование, диалог). "
    "Способы включения цитат в высказывание. Нормы постановки знаков препинания "
    "в предложениях с косвенной речью, с прямой речью, при цитировании"
)
DIRECT_TOPIC = "direct/indirect speech, citation, dialogue"
SPP_TOPIC = "SPP"
DIRECT_OWNERS = (
    "school-direct-speech-base-formatting",
    "school-direct-speech-adjacent-author-words-system",
    "school-direct-speech-author-words-middle-system",
    "school-direct-speech-inside-author-words",
    "school-citation-punctuation-formatting",
    "school-dialogue-replica-punctuation",
)
INDIRECT_OWNER = "school-spp-main-subordinate-comma-base"
OWNERS = DIRECT_OWNERS + (INDIRECT_OWNER,)
OVERLAY_NOTE = (
    "Indirect-speech punctuation routes through ordinary SPP/sentence punctuation; "
    "no separate special-sign identity is needed."
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_school(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for obj in payload.get("objects", []):
        if not isinstance(obj, dict) or obj.get("source_system") != "school_canonical":
            continue
        if obj.get("authority_status") != "current" or obj.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY" or obj.get("review_status") != "reviewed":
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
    reviewed = json.loads(REVIEWED_MEANINGS.read_text(encoding="utf-8"))
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

    docs = [row for row in manifest.get("documents", []) if row.get("canonical_source_id") == "FIPI-OGE-RU-2026-FINAL" and row.get("document_id") == "OGE_COD"]
    if len(docs) != 1 or docs[0].get("sha256") != OGE_COD_SHA256:
        raise ValueError("pinned OGE_COD SHA drift")
    if manifest.get("source_byte_policy") != "PDF_BYTES_STAY_OUT_OF_GIT; VERIFIED SOURCE ARCHIVE REFERENCES + SHA256 ONLY":
        raise ValueError("official source byte policy drift")

    if reviewed.get("status") != "CENTRAL_BRAIN_REVIEWED_EXACT_COMPOSITE_MEANINGS_PARTIAL":
        raise ValueError("reviewed composite-meaning authority status drift")
    if reviewed.get("selection_rule") != "EXACT_NORMALIZED_MEANING_EQUALITY_WITHIN_PINNED_REVIEW_SLICE_ONLY":
        raise ValueError("reviewed composite-meaning selection rule drift")
    if NORMALIZED_MEANING not in list(reviewed.get("exact_normalized_meanings", [])):
        raise ValueError("7.25 normalized meaning is outside the exact reviewed meaning authority")
    policy = reviewed.get("policy", {})
    if policy.get("keyword_or_fuzzy_inference_allowed") is not False or policy.get("classification_only_no_semantic_admission") is not True:
        raise ValueError("reviewed composite-meaning fail-closed policy drift")

    school = canonical_school(inventory)
    if len(school) != 185 or any(ref not in school for ref in OWNERS):
        raise ValueError("7.25 owner set is not wholly current canonical school truth")

    families = punctuation.get("families")
    if not isinstance(families, list):
        raise ValueError("OGE punctuation families missing")
    by_topic = {str(row.get("topic")): row for row in families if isinstance(row, dict)}
    direct = by_topic.get(DIRECT_TOPIC)
    if not isinstance(direct, dict) or tuple(direct.get("owners", [])) != DIRECT_OWNERS or str(direct.get("note")) != OVERLAY_NOTE:
        raise ValueError("closed foreign-speech family/note drift")
    spp = by_topic.get(SPP_TOPIC)
    if not isinstance(spp, dict) or INDIRECT_OWNER not in list(spp.get("owners", [])):
        raise ValueError("ordinary SPP owner for indirect speech missing")

    packet_requirements = {
        str(req["requirement_id"]): (group, req)
        for group in packet["semantic_review_groups"]
        for req in group["requirements"]
    }
    matches = [
        (rid, group, req)
        for rid, (group, req) in packet_requirements.items()
        if req.get("source_id") == "FIPI-OGE-RU-2026-FINAL" and req.get("document_id") == "OGE_COD" and str(req.get("code")) == CODE
    ]
    if len(matches) != 1:
        raise ValueError("OGE code 7.25 source requirement is not unique")
    requirement_id, group, req = matches[0]
    if requirement_id != REQUIREMENT_ID:
        raise ValueError(f"OGE code 7.25 requirement id drift: {requirement_id}")

    accounting_by_req: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accounting["dispositions"]:
        for member in row.get("members", []):
            accounting_by_req[str(member["requirement_id"])].append(row)
    units = accounting_by_req.get(REQUIREMENT_ID, [])
    if len(units) != 1 or len(units[0].get("members", [])) != 1:
        raise ValueError("OGE code 7.25 is not a one-member admission unit")
    unit = units[0]
    if unit.get("disposition") != "PARTIAL_OR_COMPOSITE" or unit.get("semantic_identity_ref") is not None:
        raise ValueError("unexpected OGE code 7.25 pre-acceptance state")
    if str(unit.get("normalized_meaning")) != NORMALIZED_MEANING:
        raise ValueError("OGE code 7.25 normalized meaning drift")
    if list(unit.get("modules", [])) != ["RU-PROG-09", "RU-PROG-14"] or list(unit.get("routes", [])) != ["oge"]:
        raise ValueError("OGE code 7.25 module/route drift")
    if str(req.get("source_locator")) != "FIPI-OGE-RU-2026-FINAL/OGE_COD p.26 7.25":
        raise ValueError("OGE code 7.25 source locator drift")

    decision = {
        "admission_unit_id": str(unit["admission_unit_id"]),
        "requirement_id": REQUIREMENT_ID,
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "document_id": "OGE_COD",
        "source_locator": "FIPI-OGE-RU-2026-FINAL/OGE_COD p.26 7.25",
        "content_code": CODE,
        "official_content_text_reviewed": OFFICIAL_TEXT,
        "normalized_meaning": NORMALIZED_MEANING,
        "modules": ["RU-PROG-09", "RU-PROG-14"],
        "routes": ["oge"],
        "disposition": "PARTIAL_OR_COMPOSITE",
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
        "canonical_component_refs": list(OWNERS),
        "component_count": len(OWNERS),
        "mapping_mode": "CLOSED_FOREIGN_SPEECH_FAMILY_PLUS_ORDINARY_INDIRECT_SPEECH_SPP_BASE",
        "authority": {
            "official_oge_codifier_sha256": OGE_COD_SHA256,
            "official_oge_codifier_review": "OGE_COD#content_code=7.25",
            "official_oge_2026_punctuation_navigator": "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_7_punktuacija.pdf#7.25",
            "final_oge_foreign_speech_overlay": "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json#punctuation_overlay.families[topic=direct/indirect speech, citation, dialogue]",
            "final_oge_spp_overlay": "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json#punctuation_overlay.families[topic=SPP]",
            "reviewed_composite_meaning_authority": "RUSSIAN-SUBJECT-REVIEWED-REUSE-COMPOSITE-MEANINGS-v0.1.json",
            "school_denominator": "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json#final_school_canonical_denominator=185",
            "packet_group": str(group["group_id"]),
        },
        "acceptance_reason": "Exact review of pinned official OGE-2026 code 7.25 and the official OGE-2026 punctuation navigator, combined with the closed overlay rule that indirect speech uses ordinary SPP/sentence punctuation. Reuses only current reviewed canonical school components and creates no parallel indirect-speech identity.",
        "mastery_boundary": {
            "route_or_broad_composite_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
            "accepted_mapping_can_emit_partial_or_composite_evidence": True,
        },
    }

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_INDIRECT_SPEECH_CANONICAL_COMPONENT_SLICE",
        "scope": "FIPI_OGE_2026_CODE_7_25_FOREIGN_SPEECH_CITATION_INDIRECT_SPEECH",
        "official_oge_codifier_sha256": OGE_COD_SHA256,
        "object_accounting_sha256": str(accounting["normalized_sha256"]),
        "semantic_packet_sha256": str(packet["normalized_sha256"]),
        "policy": {
            "central_brain_exact_official_source_review_required": True,
            "pinned_oge_codifier_sha_required": True,
            "official_oge_2026_punctuation_navigator_reviewed": True,
            "final_oge_foreign_speech_overlay_required": True,
            "ordinary_spp_route_for_indirect_speech_required": True,
            "new_indirect_speech_semantic_identity_allowed": False,
            "all_selected_owners_must_be_exact_current_reviewed_canonical_school_ids": True,
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
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_OGE_INDIRECT_SPEECH_EXACT_COMPONENT_ACCEPTANCE=PASS")
        for key, value in result["summary"].items():
            print(f"{key}={value}")
        print(f"ADMISSION_UNIT_ID={result['decisions'][0]['admission_unit_id']}")
        print(f"PACKET_GROUP={result['decisions'][0]['authority']['packet_group']}")
        print(f"NORMALIZED_ACCEPTANCE_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
