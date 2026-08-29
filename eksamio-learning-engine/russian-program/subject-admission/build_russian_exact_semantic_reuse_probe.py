#!/usr/bin/env python3
"""Find only exact, already-reviewed semantic reuse evidence for the 74-group packet.

This probe is deliberately conservative: it does not infer by keyword, module,
route, embedding or fuzzy similarity.  It compares the packet's exact normalized
meaning to existing semantic-inventory observed meanings and records only current,
reviewed/source-verified evidence.  It never admits a mapping by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[2]
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
RU1_REGISTRY = ENGINE / "russian-program/semantic-registry/RUSSIAN-SEMANTIC-REGISTRY-RU1-v1.0.json"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _exact(text: Any) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(text.strip().split())


def build_probe() -> dict[str, Any]:
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    ru1 = json.loads(RU1_REGISTRY.read_text(encoding="utf-8"))
    if inventory.get("active_school_identity_count_observed") != 185:
        raise ValueError("school semantic denominator drift")
    if ru1.get("canonical_new_ru_identity_count") != 12:
        raise ValueError("RU1 canonical registry count drift")

    inventory_objects = inventory.get("objects", [])
    reviewed_status = {"reviewed", "source_verified", "accepted"}
    groups: list[dict[str, Any]] = []
    exact_canonical_group_count = 0
    exact_existing_group_count = 0

    for group in packet["semantic_review_groups"]:
        meaning = _exact(group["normalized_meaning"])
        matches: list[dict[str, Any]] = []
        for obj in inventory_objects:
            if _exact(obj.get("observed_meaning")) != meaning:
                continue
            if obj.get("authority_status") != "current":
                continue
            if str(obj.get("review_status", "")) not in reviewed_status:
                continue
            classification = str(obj.get("audit_classification", ""))
            if classification not in {
                "CANONICAL_SCHOOL_IDENTITY",
                "SAME_MEANING_AS_EXISTING",
                "MISSING_SUBJECT_SEMANTIC_CANDIDATE",
            }:
                continue
            refs = [str(value) for value in obj.get("current_semantic_refs", []) if isinstance(value, str) and value]
            matches.append(
                {
                    "object_key": str(obj.get("object_key", "")),
                    "source_system": str(obj.get("source_system", "")),
                    "source_id": str(obj.get("source_id", "")),
                    "audit_classification": classification,
                    "current_semantic_refs": sorted(refs),
                    "candidate_canonical_owner": obj.get("candidate_canonical_owner"),
                    "evidence_provenance_refs": sorted(str(value) for value in obj.get("evidence_provenance_refs", [])),
                    "review_status": str(obj.get("review_status", "")),
                    "observed_meaning": str(obj.get("observed_meaning", "")),
                }
            )
        matches.sort(key=lambda row: (row["audit_classification"], row["object_key"]))
        canonical_matches = [row for row in matches if row["audit_classification"] == "CANONICAL_SCHOOL_IDENTITY"]
        same_existing = [row for row in matches if row["audit_classification"] == "SAME_MEANING_AS_EXISTING"]
        candidate_matches = [row for row in matches if row["audit_classification"] == "MISSING_SUBJECT_SEMANTIC_CANDIDATE"]
        if canonical_matches:
            exact_canonical_group_count += 1
            next_action = "CENTRAL_BRAIN_REVIEW_EXACT_CANONICAL_REUSE"
        elif same_existing:
            exact_existing_group_count += 1
            next_action = "CENTRAL_BRAIN_REVIEW_EXACT_EXISTING_OWNER_REUSE"
        elif candidate_matches or group["explicit_semantic_candidates"]:
            next_action = "CENTRAL_BRAIN_REVIEW_EXACT_PROPOSED_OR_CANDIDATE_COMPONENTS"
        else:
            next_action = "EXACT_COMPONENT_DECOMPOSITION_REQUIRED"
        groups.append(
            {
                "group_id": group["group_id"],
                "normalized_meaning": group["normalized_meaning"],
                "admission_unit_count": group["admission_unit_count"],
                "requirement_count": group["requirement_count"],
                "modules": group["modules"],
                "next_action": next_action,
                "exact_inventory_matches": matches,
                "exact_canonical_school_matches": len(canonical_matches),
                "exact_same_meaning_existing_matches": len(same_existing),
                "exact_missing_candidate_matches": len(candidate_matches),
                "packet_explicit_candidate_refs": group["explicit_semantic_candidates"],
                "admission_effect": "NONE_REVIEW_EVIDENCE_ONLY",
            }
        )

    payload: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "EXACT_REUSE_EVIDENCE_READY_FOR_CENTRAL_BRAIN_REVIEW",
        "packet_sha256": packet["normalized_sha256"],
        "inventory_observed_school_identity_count": 185,
        "ru1_canonical_identity_count": 12,
        "policy": {
            "exact_observed_meaning_equality_only": True,
            "keyword_or_fuzzy_similarity_allowed": False,
            "module_or_route_only_match_allowed": False,
            "probe_can_admit_semantic_identity": False,
            "explicit_central_brain_acceptance_required": True,
        },
        "summary": {
            "semantic_review_groups": len(groups),
            "groups_with_exact_canonical_school_meaning_match": exact_canonical_group_count,
            "groups_with_exact_same_meaning_existing_match": exact_existing_group_count,
            "groups_with_any_exact_inventory_match": sum(bool(group["exact_inventory_matches"]) for group in groups),
            "groups_with_packet_explicit_candidates": sum(bool(group["packet_explicit_candidate_refs"]) for group in groups),
            "semantic_admissions": 0,
            "remaining_groups_before_central_brain_decision": len(groups),
        },
        "groups": groups,
    }
    payload["normalized_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    payload = build_probe()
    if args.output:
        Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_EXACT_SEMANTIC_REUSE_PROBE=PASS")
        for key, value in payload["summary"].items():
            print(f"{key}={value}")
        print(f"NORMALIZED_REUSE_PROBE_SHA256={payload['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
