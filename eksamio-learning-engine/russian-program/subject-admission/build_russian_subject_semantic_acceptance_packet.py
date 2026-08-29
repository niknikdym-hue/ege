#!/usr/bin/env python3
"""Build the finite Central Brain semantic acceptance packet from full object accounting.

This converts 1316 learner-semantic admission-unit rows into exact normalized-meaning
review groups. It does not infer semantic mappings. Existing candidate/proposed refs are
reported only when they already exist in accepted classification evidence; all other
groups remain exact-source decomposition work.
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
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_packet() -> dict[str, Any]:
    namespace = runpy.run_path(str(ACCOUNTING_BUILDER))
    accounting: dict[str, Any] = namespace["build_accounting"]()
    if accounting.get("status") != "RUSSIAN_FULL_SUBJECT_OBJECT_ACCOUNTING_COMPLETE_SEMANTIC_ACCEPTANCE_REQUIRED":
        raise ValueError("semantic packet requires complete fail-closed object accounting")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accounting.get("dispositions", []):
        if row.get("disposition") == "PARTIAL_OR_COMPOSITE":
            grouped[str(row["normalized_meaning"])].append(row)
    if len(grouped) != 74:
        raise ValueError(f"semantic acceptance group count drift: {len(grouped)}")

    groups: list[dict[str, Any]] = []
    for meaning in sorted(grouped):
        rows = grouped[meaning]
        unit_ids = sorted(str(row["admission_unit_id"]) for row in rows)
        requirement_ids = sorted(
            str(member["requirement_id"])
            for row in rows
            for member in row.get("members", [])
        )
        modules = sorted({str(module) for row in rows for module in row.get("modules", [])})
        routes = sorted({str(route) for row in rows for route in row.get("routes", [])})
        source_ids = sorted({str(member["source_id"]) for row in rows for member in row.get("members", [])})

        components: dict[tuple[str, str], dict[str, Any]] = {}
        for row in rows:
            for component in row.get("component_refs", []):
                key = (str(component.get("ref_kind", "")), str(component.get("ref", "")))
                existing = components.get(key)
                if existing is not None and existing != component:
                    raise ValueError(f"component evidence conflict for {meaning}: {key}")
                components[key] = dict(component)
        component_rows = [components[key] for key in sorted(components)]
        semantic_candidates = [
            component for component in component_rows
            if component.get("ref_kind") in {"existing_semantic_candidate", "proposed_semantic_with_content"}
        ]
        review_boundaries = [
            component for component in component_rows
            if component.get("ref_kind") == "review_capability_boundary"
        ]
        if semantic_candidates:
            next_status = "CENTRAL_BRAIN_COMPONENT_ACCEPTANCE_REQUIRED"
        else:
            next_status = "EXACT_SOURCE_COMPONENT_DECOMPOSITION_REQUIRED"

        group_id = "RUSG-" + hashlib.sha256(meaning.encode("utf-8")).hexdigest()[:16]
        groups.append(
            {
                "group_id": group_id,
                "normalized_meaning": meaning,
                "admission_units": len(unit_ids),
                "requirements": len(requirement_ids),
                "modules": modules,
                "routes": routes,
                "source_ids": source_ids,
                "exact_admission_unit_ids": unit_ids,
                "exact_requirement_ids": requirement_ids,
                "explicit_semantic_candidate_refs": semantic_candidates,
                "review_boundary_refs": review_boundaries,
                "status": next_status,
                "admission_effect": "NONE_UNTIL_EXPLICIT_SUBJECT_ACCEPTANCE",
            }
        )

    if sum(group["admission_units"] for group in groups) != 1316:
        raise ValueError("semantic packet does not cover all learner-semantic admission units")
    if sum(group["requirements"] for group in groups) != 1391:
        raise ValueError("semantic packet does not cover all learner-semantic requirements")
    explicit_groups = sum(group["status"] == "CENTRAL_BRAIN_COMPONENT_ACCEPTANCE_REQUIRED" for group in groups)
    decomposition_groups = sum(group["status"] == "EXACT_SOURCE_COMPONENT_DECOMPOSITION_REQUIRED" for group in groups)
    if explicit_groups + decomposition_groups != 74:
        raise ValueError("semantic packet group status partition drift")

    payload: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED",
        "object_accounting_sha256": accounting["normalized_sha256"],
        "policy": {
            "semantic_auto_admission_allowed": False,
            "keyword_or_fuzzy_mapping_allowed": False,
            "module_only_mapping_allowed": False,
            "content_presence_implies_admission": False,
            "partial_or_composite_can_emit_exact_mastery": False,
            "reuse_existing_semantics_first": True,
        },
        "summary": {
            "semantic_review_groups": len(groups),
            "admission_units": 1316,
            "requirements": 1391,
            "groups_with_explicit_candidate_evidence": explicit_groups,
            "groups_requiring_exact_source_decomposition": decomposition_groups,
            "canonical_semantic_admissions": 0,
            "ru_proposal_admissions": 0,
            "russian_content_ready": False,
        },
        "groups": groups,
    }
    payload["normalized_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = build_packet()
    if args.output:
        Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_SUBJECT_SEMANTIC_ACCEPTANCE_PACKET=PASS")
        print(f"normalized_sha256={payload['normalized_sha256']}")
        for key, value in payload["summary"].items():
            print(f"{key}={value}")
        print("GROUPS_BEGIN")
        for group in payload["groups"]:
            print(f"{group['group_id']}\t{group['status']}\t{group['admission_units']}\t{group['requirements']}\t{group['normalized_meaning']}")
        print("GROUPS_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
