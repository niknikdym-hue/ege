#!/usr/bin/env python3
"""Fail-closed exact OGE-2026 punctuation component slice for issue #161.

The accepted positions were reviewed against the repository-pinned official
OGE_COD PDF (SHA-256 below).  Only positions whose exact official topic is
covered by exact current reviewed school identities in the already-closed OGE
punctuation overlay are eligible.  Descriptive placeholders, broad analysis
routes and fuzzy/module inference remain excluded.
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

# `overlay_topic` is exact text from punctuation_overlay.families.
# 7.15/7.16 isolate explicit exact branch owners inside the mixed family;
# the descriptive introductory-system placeholder is deliberately not imported.
EXPECTED_EXACT: dict[str, dict[str, Any]] = {
    "7.2": {
        "official_text": "Тире между подлежащим и сказуемым",
        "overlay_topic": "dash between subject and predicate",
        "owners": (
            "school-dash-subject-predicate-basic-placement",
            "school-dash-subject-predicate-no-dash-boundaries",
            "school-dash-subject-predicate-closing-comma-boundary",
        ),
        "mapping_mode": "COMPLETE_EXACT_OVERLAY_FAMILY",
    },
    "7.3": {
        "official_text": "Тире в неполном предложении",
        "overlay_topic": "dash in incomplete sentence",
        "owners": ("school-dash-incomplete-sentence",),
        "mapping_mode": "COMPLETE_EXACT_OVERLAY_FAMILY",
    },
    "7.13": {
        "official_text": "Знаки препинания в предложении со сравнительным оборотом; нормы постановки знаков препинания в предложениях со сравнительным оборотом",
        "overlay_topic": "comparative constructions",
        "owners": ("school-kak-comma-functional-boundary",),
        "mapping_mode": "COMPLETE_EXACT_OVERLAY_FAMILY",
    },
    "7.15": {
        "official_text": "Знаки препинания в предложении с обращениями; нормы постановки знаков препинания в предложениях с обращениями",
        "overlay_topic": "introductory/parenthetical constructions, addresses, interjections",
        "owners": ("school-address-punctuation-boundary",),
        "mapping_mode": "EXACT_EXPLICIT_BRANCH_OWNER",
    },
    "7.16": {
        "official_text": "Знаки препинания в предложении с междометиями; пунктуационное выделение междометий и звукоподражательных слов; нормы постановки знаков препинания в предложениях с междометиями",
        "overlay_topic": "introductory/parenthetical constructions, addresses, interjections",
        "owners": ("school-interjection-particle-punctuation",),
        "mapping_mode": "EXACT_EXPLICIT_BRANCH_OWNER",
    },
    "7.18": {
        "official_text": "Знаки препинания в сложносочинённом предложении; нормы постановки знаков препинания в сложных предложениях (обобщение)",
        "overlay_topic": "SSP",
        "owners": (
            "school-ssp-comma-base",
            "school-ssp-semicolon-boundary",
            "school-ssp-dash-boundary",
        ),
        "mapping_mode": "COMPLETE_EXACT_OVERLAY_FAMILY",
    },
    "7.20": {
        "official_text": "Знаки препинания в сложноподчинённом предложении; нормы постановки знаков препинания в сложноподчинённых предложениях",
        "overlay_topic": "SPP",
        "owners": (
            "school-spp-main-subordinate-comma-base",
            "school-spp-complex-subordinator-comma-boundary",
            "school-spp-multiple-subordinate-punctuation",
            "school-spp-special-signs-family",
            "school-semantically-integral-expression-comma-boundary",
        ),
        "mapping_mode": "COMPLETE_EXACT_OVERLAY_FAMILY",
    },
    "7.22": {
        "official_text": "Знаки препинания в бессоюзном сложном предложении: запятая, точка с запятой, двоеточие и тире по официальным смысловым отношениям",
        "overlay_topic": "BSP",
        "owners": (
            "school-bsp-comma-semicolon-base",
            "school-colon-bsp-vs-generalizing-word",
            "school-bsp-dash-boundary",
            "school-bsp-comma-dash-boundary",
        ),
        "mapping_mode": "COMPLETE_EXACT_OVERLAY_FAMILY",
    },
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_school(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for obj in inventory.get("objects", []):
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

    school = canonical_school(inventory)
    if len(school) != 185:
        raise ValueError(f"expected 185 current reviewed school identities, got {len(school)}")
    families = punctuation.get("families")
    if not isinstance(families, list):
        raise ValueError("OGE punctuation families missing")
    by_topic = {str(row.get("topic")): row for row in families if isinstance(row, dict)}

    for code, expected in EXPECTED_EXACT.items():
        family = by_topic.get(str(expected["overlay_topic"]))
        if family is None or not isinstance(family.get("owners"), list):
            raise ValueError(f"punctuation family/owners missing: {code}")
        owners = family["owners"]
        selected = tuple(expected["owners"])
        if expected["mapping_mode"] == "COMPLETE_EXACT_OVERLAY_FAMILY":
            if tuple(owners) != selected:
                raise ValueError(f"complete exact punctuation owners drift: {code}")
        elif expected["mapping_mode"] == "EXACT_EXPLICIT_BRANCH_OWNER":
            if len(selected) != 1 or selected[0] not in owners:
                raise ValueError(f"explicit punctuation branch owner drift: {code}")
        else:
            raise ValueError(f"unknown mapping mode: {code}")
        if any(ref not in school for ref in selected):
            raise ValueError(f"non-current/noncanonical punctuation owner: {code}")

    packet_requirements = {
        str(req["requirement_id"]): (group, req)
        for group in packet["semantic_review_groups"]
        for req in group["requirements"]
    }
    accounting_by_req: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accounting["dispositions"]:
        for member in row.get("members", []):
            accounting_by_req[str(member["requirement_id"])].append(row)

    decisions: list[dict[str, Any]] = []
    for code, expected in sorted(EXPECTED_EXACT.items(), key=lambda item: tuple(int(x) for x in item[0].split("."))):
        matches = [
            (rid, group, req)
            for rid, (group, req) in packet_requirements.items()
            if req.get("source_id") == "FIPI-OGE-RU-2026-FINAL" and req.get("document_id") == "OGE_COD" and str(req.get("code")) == code
        ]
        if len(matches) != 1:
            raise ValueError(f"OGE punctuation source/code requirement is not unique: {code}")
        requirement_id, group, req = matches[0]
        units = accounting_by_req.get(requirement_id, [])
        if len(units) != 1 or len(units[0].get("members", [])) != 1:
            raise ValueError(f"OGE punctuation requirement is not a one-member admission unit: {code}")
        unit = units[0]
        if unit.get("disposition") != "PARTIAL_OR_COMPOSITE" or unit.get("semantic_identity_ref") is not None:
            raise ValueError(f"unexpected pre-acceptance state: {code}")
        owners = list(expected["owners"])
        decisions.append({
            "admission_unit_id": str(unit["admission_unit_id"]),
            "requirement_id": requirement_id,
            "source_id": str(req["source_id"]),
            "document_id": str(req["document_id"]),
            "source_locator": str(req["source_locator"]),
            "content_code": code,
            "official_content_text_reviewed": str(expected["official_text"]),
            "normalized_meaning": str(unit["normalized_meaning"]),
            "modules": list(unit.get("modules", [])),
            "routes": list(unit.get("routes", [])),
            "disposition": "PARTIAL_OR_COMPOSITE",
            "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
            "canonical_component_refs": owners,
            "component_count": len(owners),
            "mapping_mode": str(expected["mapping_mode"]),
            "authority": {
                "official_oge_codifier_sha256": OGE_COD_SHA256,
                "official_oge_codifier_review": f"OGE_COD#content_code={code}",
                "final_oge_overlay": f"265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json#punctuation_overlay.families[topic={expected['overlay_topic']}]",
                "school_denominator": "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json#final_school_canonical_denominator=185",
                "packet_group": str(group["group_id"]),
            },
            "acceptance_reason": "Exact Central-Brain review of the pinned official OGE-2026 codifier position plus explicit exact ownership in the closed OGE punctuation overlay. Descriptive placeholders and broader punctuation-analysis routes are excluded.",
            "mastery_boundary": {
                "route_or_broad_composite_attempt_can_emit_exact_component_mastery": False,
                "component_specific_independent_evidence_required": True,
                "accepted_mapping_can_emit_partial_or_composite_evidence": True,
            },
        })

    if {row["content_code"] for row in decisions} != set(EXPECTED_EXACT):
        raise ValueError("exact OGE punctuation acceptance set drift")
    if len({row["admission_unit_id"] for row in decisions}) != len(decisions):
        raise ValueError("duplicate admission unit in OGE punctuation acceptance set")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_PUNCTUATION_CANONICAL_COMPONENT_SLICE",
        "scope": "FIPI_OGE_2026_EXACT_PUNCTUATION_CODES_WITH_EXACT_CLOSED_OVERLAY_OWNERS",
        "official_oge_codifier_sha256": OGE_COD_SHA256,
        "object_accounting_sha256": str(accounting["normalized_sha256"]),
        "semantic_packet_sha256": str(packet["normalized_sha256"]),
        "policy": {
            "central_brain_exact_official_source_review_required": True,
            "pinned_oge_codifier_sha_required": True,
            "final_oge_punctuation_overlay_required": True,
            "all_selected_owners_must_be_exact_current_reviewed_canonical_school_ids": True,
            "descriptive_family_placeholders_allowed": False,
            "broad_punctuation_analysis_route_allowed": False,
            "keyword_or_fuzzy_mapping_allowed": False,
            "module_only_mapping_allowed": False,
            "generic_composite_attempt_can_exact_master_components": False,
        },
        "summary": {
            "accepted_admission_units": len(decisions),
            "accepted_requirements": len(decisions),
            "accepted_content_codes": len(decisions),
            "canonical_component_refs_unique": len({ref for row in decisions for ref in row["canonical_component_refs"]}),
            "new_semantic_identities_created": 0,
            "ru_proposal_identities_admitted": 0,
            "false_exact_mastery_admissions": 0,
        },
        "decisions": decisions,
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
        print("RUSSIAN_OGE_PUNCTUATION_EXACT_CANONICAL_COMPONENT_ACCEPTANCE=PASS")
        for key, value in result["summary"].items():
            print(f"{key}={value}")
        print("accepted_content_codes=" + ",".join(row["content_code"] for row in result["decisions"]))
        print(f"NORMALIZED_ACCEPTANCE_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
