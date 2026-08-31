#!/usr/bin/env python3
"""Build a review candidate for exact unique school-canonical reuse.

This builder is deliberately narrower than ordinary semantic matching:
- exact normalized-meaning equality only;
- exactly one current reviewed canonical `school-*` identity may own the meaning;
- exactly one official requirement may belong to the admission unit;
- pre-existing object-bound accepted units are excluded;
- no keyword, fuzzy, module, route, taxonomy or range inference is permitted;
- output is REVIEW CANDIDATE ONLY and has no admission effect.
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
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

EXISTING_OBJECT_AUTHORITIES = (
    HERE / "RUSSIAN-EGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    HERE / "RUSSIAN-OGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    HERE / "RUSSIAN-OGE-PUNCTUATION-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    HERE / "RUSSIAN-OGE-DIRECT-SPEECH-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    HERE / "RUSSIAN-OGE-INDIRECT-SPEECH-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalized(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def authority_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("decisions")
    if rows is None and isinstance(payload.get("decision"), dict):
        rows = [payload["decision"]]
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("existing object authority decisions missing")
    return rows


def build_candidate() -> dict[str, Any]:
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))

    if packet.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("semantic packet is not fail-closed")
    if inventory.get("active_school_identity_count_observed") != 185:
        raise ValueError("frozen school denominator drift")

    canonical_by_meaning: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for obj in inventory.get("objects", []):
        if not isinstance(obj, dict) or obj.get("source_system") != "school_canonical":
            continue
        if obj.get("authority_status") != "current" or obj.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY" or obj.get("review_status") != "reviewed":
            continue
        source_id = str(obj.get("source_id", ""))
        if not source_id.startswith("school-") or obj.get("current_semantic_refs") != [source_id]:
            raise ValueError(f"canonical school self-ref drift: {source_id}")
        meaning = normalized(obj.get("observed_meaning"))
        if not meaning:
            raise ValueError(f"canonical school meaning missing: {source_id}")
        canonical_by_meaning[meaning].append(obj)
    if sum(len(rows) for rows in canonical_by_meaning.values()) != 185:
        raise ValueError("canonical school inventory count drift")

    already_accepted_units: set[str] = set()
    already_accepted_requirements: set[str] = set()
    for path in EXISTING_OBJECT_AUTHORITIES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in authority_rows(payload):
            unit_id = str(row.get("admission_unit_id", ""))
            requirement_id = str(row.get("requirement_id", ""))
            if not unit_id or not requirement_id:
                raise ValueError(f"existing object authority lacks exact ids: {path.name}")
            if unit_id in already_accepted_units or requirement_id in already_accepted_requirements:
                raise ValueError("existing object authorities overlap")
            already_accepted_units.add(unit_id)
            already_accepted_requirements.add(requirement_id)

    packet_req: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
        str(req["requirement_id"]): (group, req)
        for group in packet.get("semantic_review_groups", [])
        for req in group.get("requirements", [])
    }

    candidates: list[dict[str, Any]] = []
    ambiguous_exact_meanings: list[dict[str, Any]] = []
    multi_member_exact_units = 0
    nonunique_canonical_exact_units = 0

    for unit in accounting.get("dispositions", []):
        if unit.get("disposition") != "PARTIAL_OR_COMPOSITE" or unit.get("semantic_identity_ref") is not None:
            continue
        unit_id = str(unit.get("admission_unit_id", ""))
        if not unit_id or unit_id in already_accepted_units:
            continue
        members = unit.get("members")
        if not isinstance(members, list) or not members:
            raise ValueError(f"admission unit members missing: {unit_id}")
        meaning = normalized(unit.get("normalized_meaning"))
        exact_owners = canonical_by_meaning.get(meaning, [])
        if not exact_owners:
            continue
        if len(members) != 1:
            multi_member_exact_units += 1
            continue
        if len(exact_owners) != 1:
            nonunique_canonical_exact_units += 1
            ambiguous_exact_meanings.append({
                "admission_unit_id": unit_id,
                "normalized_meaning": meaning,
                "canonical_owner_refs": sorted(str(row["source_id"]) for row in exact_owners),
                "admission_effect": "NONE_AMBIGUOUS_REVIEW_ONLY",
            })
            continue

        requirement_id = str(members[0].get("requirement_id", ""))
        if not requirement_id or requirement_id in already_accepted_requirements:
            continue
        group_req = packet_req.get(requirement_id)
        if group_req is None:
            raise ValueError(f"packet requirement missing for exact candidate: {requirement_id}")
        group, req = group_req
        if normalized(req.get("normalized_meaning")) != meaning:
            raise ValueError(f"packet/accounting meaning drift: {requirement_id}")
        owner = exact_owners[0]
        owner_id = str(owner["source_id"])
        candidates.append({
            "admission_unit_id": unit_id,
            "requirement_id": requirement_id,
            "source_id": str(req.get("source_id", "")),
            "document_id": str(req.get("document_id", "")),
            "source_locator": str(req.get("source_locator", "")),
            "content_code": str(req.get("code", "")),
            "normalized_meaning": meaning,
            "modules": list(unit.get("modules", [])),
            "routes": list(unit.get("routes", [])),
            "exact_unique_canonical_owner": owner_id,
            "canonical_owner_observed_meaning": str(owner.get("observed_meaning", "")),
            "canonical_owner_provenance_refs": sorted(str(value) for value in owner.get("evidence_provenance_refs", [])),
            "packet_group": str(group.get("group_id", "")),
            "review_status": "CENTRAL_BRAIN_REVIEW_REQUIRED_EXACT_UNIQUE_CANONICAL_REUSE_CANDIDATE",
            "admission_effect": "NONE_REVIEW_CANDIDATE_ONLY",
        })

    candidates.sort(key=lambda row: (row["source_id"], row["document_id"], row["content_code"], row["requirement_id"]))
    if len({row["admission_unit_id"] for row in candidates}) != len(candidates):
        raise ValueError("candidate admission-unit duplication")
    if len({row["requirement_id"] for row in candidates}) != len(candidates):
        raise ValueError("candidate requirement duplication")

    by_owner: dict[str, int] = defaultdict(int)
    by_source: dict[str, int] = defaultdict(int)
    for row in candidates:
        by_owner[row["exact_unique_canonical_owner"]] += 1
        by_source[row["source_id"]] += 1

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_REVIEW_REQUIRED_EXACT_UNIQUE_CANONICAL_REUSE_CANDIDATE",
        "object_accounting_sha256": str(accounting["normalized_sha256"]),
        "semantic_packet_sha256": str(packet["normalized_sha256"]),
        "policy": {
            "exact_normalized_meaning_equality_only": True,
            "unique_current_reviewed_school_owner_required": True,
            "one_member_admission_unit_required": True,
            "preexisting_object_acceptances_excluded": True,
            "keyword_or_fuzzy_inference_allowed": False,
            "module_or_route_only_inference_allowed": False,
            "candidate_can_self_admit": False,
            "central_brain_acceptance_required": True,
            "generic_route_attempt_can_exact_master_owner": False,
        },
        "summary": {
            "review_candidates": len(candidates),
            "unique_canonical_owners": len(by_owner),
            "sources_represented": len(by_source),
            "existing_object_bound_units_excluded": len(already_accepted_units),
            "multi_member_exact_units_excluded": multi_member_exact_units,
            "nonunique_canonical_exact_units_excluded": nonunique_canonical_exact_units,
            "semantic_admissions": 0,
            "object_level_closures": 0,
        },
        "counts_by_source": dict(sorted(by_source.items())),
        "counts_by_canonical_owner": dict(sorted(by_owner.items())),
        "candidates": candidates,
        "ambiguous_exact_meanings": sorted(ambiguous_exact_meanings, key=lambda row: row["admission_unit_id"]),
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_candidate()
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_UNIQUE_EXACT_CANONICAL_REUSE_CANDIDATE=PASS")
        for key, value in result["summary"].items():
            print(f"{key}={value}")
        for source, count in result["counts_by_source"].items():
            print(f"source[{source}]={count}")
        print(f"NORMALIZED_CANDIDATE_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
