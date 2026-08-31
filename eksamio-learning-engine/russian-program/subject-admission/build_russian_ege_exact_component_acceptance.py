#!/usr/bin/env python3
"""Materialize the first exact canonical-component subject acceptances for #161.

This is intentionally narrow.  A FIPI EGE content code is accepted only when:
1. merged official task↔code authority maps that exact code to one task only;
2. the final 2026 EGE route overlay classifies that task as EXAM_ONLY_COMPOSITE;
3. every listed school_identity_families entry is an exact current reviewed
   canonical school identity from the frozen 185 denominator; and
4. the exact EGE codifier requirement is a one-member admission unit in the
   current complete object accounting.

Descriptions such as "other owners", ranges, route names, keyword/fuzzy matches,
and PARTIAL_SCHOOL_OVERLAP examples are never admitted by this builder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import runpy
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
TASK_RELATION = ENGINE / "russian-program/ege-task-code-relation/FIPI-EGE-2026-TASK-CODE-RELATION-v1.0.json"
EGE_OVERLAY = ENGINE / "264-RUSSIAN-FIPI-2026-EGE-ROUTE-OVERLAY-v0.1.json"
SCHOOL_FREEZE = ENGINE / "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
EXACT_CODE_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)+$")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _canonical_school_objects(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for obj in inventory.get("objects", []):
        if obj.get("source_system") != "school_canonical":
            continue
        if obj.get("authority_status") != "current" or obj.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY":
            continue
        if obj.get("review_status") != "reviewed":
            continue
        source_id = str(obj.get("source_id", ""))
        if not source_id or obj.get("current_semantic_refs") != [source_id]:
            raise ValueError(f"canonical school identity self-ref drift: {source_id}")
        rows[source_id] = obj
    return rows


def build_acceptance() -> dict[str, Any]:
    relation = json.loads(TASK_RELATION.read_text(encoding="utf-8"))
    overlay = json.loads(EGE_OVERLAY.read_text(encoding="utf-8"))
    freeze = json.loads(SCHOOL_FREEZE.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()

    if relation.get("status") != "OFFICIAL_FIPI_EGE_2026_TASK_TO_CODE_RELATION":
        raise ValueError("official EGE task-code relation status drift")
    if relation.get("relation_policy", {}).get("semantic_admission_implied") is not False:
        raise ValueError("task-code authority must not self-admit semantics")
    if overlay.get("status") != "EGE_2026_FIPI_ROUTE_OVERLAY_COMPLETE / ZERO_SCHOOL_REOPEN_CANDIDATES":
        raise ValueError("final EGE route overlay status drift")
    if freeze.get("final_school_canonical_denominator") != 185 or freeze.get("final_source_closure", {}).get("open_holds") != 0:
        raise ValueError("frozen 185 school denominator is not closed")
    canonical = _canonical_school_objects(inventory)
    if len(canonical) != 185:
        raise ValueError(f"expected 185 current reviewed school identities, got {len(canonical)}")

    relation_rows = {int(row["task"]): row for row in relation.get("rows", [])}
    if set(relation_rows) != set(range(1, 28)):
        raise ValueError("official EGE relation must cover tasks 1..27 exactly")
    overlay_rows = {
        int(row["task"]): row
        for row in overlay.get("route_map", [])
        if isinstance(row.get("task"), int)
    }

    exact_code_tasks: dict[str, list[int]] = defaultdict(list)
    for task, row in relation_rows.items():
        for expression in row.get("content_code_expressions", []):
            if isinstance(expression, str) and EXACT_CODE_RE.fullmatch(expression):
                exact_code_tasks[expression].append(task)

    eligible_task_components: dict[int, list[str]] = {}
    for task, row in overlay_rows.items():
        if row.get("classification") != "EXAM_ONLY_COMPOSITE":
            continue
        families = row.get("school_identity_families")
        if not isinstance(families, list) or not families:
            continue
        if any(not isinstance(ref, str) or ref not in canonical for ref in families):
            # Any descriptive family placeholder makes the task incomplete for exact acceptance.
            continue
        eligible_task_components[task] = sorted(families)

    accepted_codes: dict[str, dict[str, Any]] = {}
    for code, tasks in sorted(exact_code_tasks.items()):
        unique_tasks = sorted(set(tasks))
        if len(unique_tasks) != 1:
            continue
        task = unique_tasks[0]
        components = eligible_task_components.get(task)
        if not components:
            continue
        accepted_codes[code] = {"task": task, "canonical_component_refs": components}

    packet_requirements = {
        str(req["requirement_id"]): (group, req)
        for group in packet["semantic_review_groups"]
        for req in group["requirements"]
    }
    accounting_by_requirement: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accounting["dispositions"]:
        for member in row.get("members", []):
            accounting_by_requirement[str(member["requirement_id"])].append(row)

    decisions: list[dict[str, Any]] = []
    for code, evidence in sorted(accepted_codes.items()):
        matches = [
            (rid, group, req)
            for rid, (group, req) in packet_requirements.items()
            if req.get("source_id") == "FIPI-EGE-RU-2026-FINAL"
            and req.get("document_id") == "EGE_COD"
            and str(req.get("code")) == code
        ]
        if len(matches) != 1:
            # Exact source/code must identify one current launch requirement; otherwise remain unaccepted.
            continue
        requirement_id, group, req = matches[0]
        units = accounting_by_requirement.get(requirement_id, [])
        if len(units) != 1 or len(units[0].get("members", [])) != 1:
            continue
        unit = units[0]
        if unit.get("disposition") != "PARTIAL_OR_COMPOSITE" or unit.get("semantic_identity_ref") is not None:
            raise ValueError(f"unexpected pre-acceptance state for {requirement_id}")
        task = int(evidence["task"])
        components = list(evidence["canonical_component_refs"])
        decisions.append(
            {
                "admission_unit_id": str(unit["admission_unit_id"]),
                "requirement_id": requirement_id,
                "source_id": str(req["source_id"]),
                "document_id": str(req["document_id"]),
                "source_locator": str(req["source_locator"]),
                "content_code": code,
                "official_ege_task": task,
                "normalized_meaning": str(unit["normalized_meaning"]),
                "modules": list(unit.get("modules", [])),
                "routes": list(unit.get("routes", [])),
                "disposition": "PARTIAL_OR_COMPOSITE",
                "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
                "canonical_component_refs": components,
                "component_count": len(components),
                "authority": {
                    "official_task_code_relation": f"FIPI-EGE-2026-TASK-CODE-RELATION-v1.0.json#task={task}:content_code={code}",
                    "final_route_overlay": f"264-RUSSIAN-FIPI-2026-EGE-ROUTE-OVERLAY-v0.1.json#route_map[task={task}]",
                    "school_denominator": "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json#final_school_canonical_denominator=185",
                    "packet_group": str(group["group_id"]),
                },
                "acceptance_reason": "The official 2026 FIPI table binds this exact content code to exactly one EGE task; the final closed EGE route overlay for that task lists only exact current reviewed identities from the frozen 185 school denominator, with no descriptive family placeholder or partial-overlap example.",
                "mastery_boundary": {
                    "route_or_broad_composite_attempt_can_emit_exact_component_mastery": False,
                    "component_specific_independent_evidence_required": True,
                    "accepted_mapping_can_emit_partial_or_composite_evidence": True,
                },
            }
        )

    expected_codes = {"3.7.3", "3.7.4", "3.7.6", "3.7.8", "3.8.4"}
    actual_codes = {row["content_code"] for row in decisions}
    if actual_codes != expected_codes:
        raise ValueError(f"exact safe EGE code acceptance set drift: {sorted(actual_codes)}")
    if len({row["admission_unit_id"] for row in decisions}) != len(decisions):
        raise ValueError("duplicate admission unit in EGE exact acceptance set")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_ACCEPTED_EXACT_EGE_CANONICAL_COMPONENT_SLICE",
        "scope": "FIPI_EGE_2026_EXACT_CONTENT_CODES_WITH_COMPLETE_CANONICAL_ROUTE_COMPONENTS",
        "object_accounting_sha256": str(accounting["normalized_sha256"]),
        "semantic_packet_sha256": str(packet["normalized_sha256"]),
        "policy": {
            "official_task_code_relation_required": True,
            "unique_exact_content_code_task_required": True,
            "final_route_overlay_required": True,
            "all_route_components_must_be_exact_current_reviewed_canonical_school_ids": True,
            "descriptive_family_placeholders_allowed": False,
            "partial_school_overlap_examples_allowed": False,
            "range_code_expansion_allowed": False,
            "keyword_or_fuzzy_mapping_allowed": False,
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
        "decisions": sorted(decisions, key=lambda row: row["content_code"]),
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
        print("RUSSIAN_EGE_EXACT_CANONICAL_COMPONENT_ACCEPTANCE=PASS")
        for key, value in result["summary"].items():
            print(f"{key}={value}")
        print("accepted_content_codes=" + ",".join(row["content_code"] for row in result["decisions"]))
        print(f"NORMALIZED_ACCEPTANCE_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
