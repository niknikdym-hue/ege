#!/usr/bin/env python3
"""Build the finite Central-Brain Russian semantic acceptance packet for SEP-1.

The packet is derived only from the already fail-closed complete object accounting.
It does not admit semantics or content.  Its purpose is to reduce 1316 learner-
semantic admission-unit rows / 1391 requirements to a finite exact 74-group review
set while preserving every source locator, reuse/proposal clue and rights blocker.
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
RIGHTS_SALVAGE = HERE / "PR139-RIGHTS-BLOCKED-SALVAGE-v0.1.json"
EXPECTED_MODULES = [f"RU-PROG-{number:02d}" for number in range(1, 17)]


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _source_member(member: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": str(member["requirement_id"]),
        "source_id": str(member["source_id"]),
        "document_id": str(member["document_id"]),
        "page": member["page"],
        "source_locator": str(member["source_locator"]),
        "code": member.get("code"),
        "confidence": member.get("confidence"),
        "grades": list(member.get("grades", [])),
    }


def _candidate_ref(component: dict[str, Any]) -> dict[str, Any]:
    row = {
        "ref_kind": str(component["ref_kind"]),
        "ref": str(component["ref"]),
        "status": str(component["status"]),
    }
    if component.get("label") is not None:
        row["label"] = str(component["label"])
    if component.get("content_ref") is not None:
        row["content_ref"] = str(component["content_ref"])
    return row


def build_packet() -> dict[str, Any]:
    namespace = runpy.run_path(str(ACCOUNTING_BUILDER))
    accounting: dict[str, Any] = namespace["build_accounting"]()
    summary = accounting.get("summary", {})
    semantic = accounting.get("semantic_acceptance", {})
    if summary.get("accepted_classification_units") != 1325 or summary.get("accepted_classification_requirements") != 1400:
        raise ValueError("complete object accounting is not complete")
    if semantic.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("semantic acceptance boundary is not fail-closed")
    if semantic.get("russian_content_ready") is not False:
        raise ValueError("Russian content was marked ready before semantic acceptance")
    if summary.get("canonical_semantic_admissions") != 0 or summary.get("ru_proposal_admissions") != 0:
        raise ValueError("semantic admissions must remain zero while building review packet")

    dispositions = accounting.get("dispositions", [])
    partial_rows = [row for row in dispositions if row.get("disposition") == "PARTIAL_OR_COMPOSITE"]
    route_rows = [row for row in dispositions if row.get("disposition") == "ROUTE_OR_FORMAT_ONLY"]
    if len(partial_rows) != 1316 or len(route_rows) != 9:
        raise ValueError("complete accounting disposition inventory drift")

    by_meaning: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in partial_rows:
        by_meaning[str(row["normalized_meaning"])].append(row)
    semantic_groups = semantic.get("groups", [])
    expected_meanings = [str(row["normalized_meaning"]) for row in semantic_groups]
    if len(expected_meanings) != 74 or len(set(expected_meanings)) != 74 or set(expected_meanings) != set(by_meaning):
        raise ValueError("finite 74-group semantic review universe drift")

    review_groups: list[dict[str, Any]] = []
    for index, meaning in enumerate(sorted(by_meaning), 1):
        group_rows = by_meaning[meaning]
        unit_ids = sorted(str(row["admission_unit_id"]) for row in group_rows)
        requirements: dict[str, dict[str, Any]] = {}
        modules: set[str] = set()
        routes: set[str] = set()
        priority_routes: set[str] = set()
        requirement_classes: set[str] = set()
        decision_sources: set[str] = set()
        candidates: dict[tuple[str, str], dict[str, Any]] = {}
        boundaries: dict[str, dict[str, Any]] = {}

        for row in group_rows:
            modules.update(str(value) for value in row.get("modules", []))
            routes.update(str(value) for value in row.get("routes", []))
            priority_routes.add(str(row.get("priority_route", "")))
            requirement_classes.add(str(row.get("requirement_class", "")))
            decision_sources.add(str(row.get("decision_source", "")))
            for member in row.get("members", []):
                normalized = _source_member(member)
                requirement_id = normalized["requirement_id"]
                existing = requirements.get(requirement_id)
                if existing is not None and existing != normalized:
                    raise ValueError(f"requirement source locator conflict: {requirement_id}")
                requirements[requirement_id] = normalized
            for component in row.get("component_refs", []) or []:
                kind = str(component.get("ref_kind", ""))
                ref = str(component.get("ref", ""))
                if kind in {"existing_semantic_candidate", "proposed_semantic_with_content"}:
                    normalized_candidate = _candidate_ref(component)
                    key = (kind, ref)
                    existing_candidate = candidates.get(key)
                    if existing_candidate is not None and existing_candidate != normalized_candidate:
                        raise ValueError(f"semantic candidate metadata conflict: {key}")
                    candidates[key] = normalized_candidate
                elif kind == "review_capability_boundary":
                    boundary = _candidate_ref(component)
                    existing_boundary = boundaries.get(ref)
                    if existing_boundary is not None and existing_boundary != boundary:
                        raise ValueError(f"review-boundary metadata conflict: {ref}")
                    boundaries[ref] = boundary
                else:
                    raise ValueError(f"unsupported semantic-review component kind: {kind}")

        source_rows = [requirements[key] for key in sorted(requirements)]
        candidate_rows = [candidates[key] for key in sorted(candidates)]
        boundary_rows = [boundaries[key] for key in sorted(boundaries)]
        action = "REVIEW_EXPLICIT_COMPONENT_CANDIDATES" if candidate_rows else "DECOMPOSE_AND_MAP_EXACT_COMPONENTS"
        review_groups.append(
            {
                "group_id": f"RUS-SEM-REVIEW-{index:03d}",
                "status": "SUBJECT_ACCEPTANCE_REQUIRED",
                "required_action": action,
                "normalized_meaning": meaning,
                "admission_unit_count": len(unit_ids),
                "requirement_count": len(source_rows),
                "admission_unit_ids": unit_ids,
                "requirements": source_rows,
                "source_ids": sorted({row["source_id"] for row in source_rows}),
                "modules": sorted(modules),
                "routes": sorted(routes),
                "priority_routes": sorted(value for value in priority_routes if value),
                "requirement_classes": sorted(value for value in requirement_classes if value),
                "decision_sources": sorted(value for value in decision_sources if value),
                "explicit_semantic_candidates": candidate_rows,
                "review_capability_boundaries": boundary_rows,
                "acceptance_boundary": {
                    "keyword_or_fuzzy_inference_allowed": False,
                    "module_only_mapping_allowed": False,
                    "content_presence_implies_admission": False,
                    "generic_group_attempt_can_emit_exact_component_mastery": False,
                    "exact_mastery_requires_component_specific_independent_evidence": True,
                    "canonical_or_proposed_admission_requires_explicit_central_brain_acceptance": True,
                },
            }
        )

    module_matrix: list[dict[str, Any]] = []
    for module_id in EXPECTED_MODULES:
        module_rows = [row for row in dispositions if module_id in row.get("modules", [])]
        requirement_ids = {
            str(member["requirement_id"])
            for row in module_rows
            for member in row.get("members", [])
        }
        partial_module_rows = [row for row in module_rows if row.get("disposition") == "PARTIAL_OR_COMPOSITE"]
        route_module_rows = [row for row in module_rows if row.get("disposition") == "ROUTE_OR_FORMAT_ONLY"]
        group_ids = {
            group["group_id"]
            for group in review_groups
            if module_id in group["modules"]
        }
        if not module_rows or not requirement_ids:
            raise ValueError(f"module has zero exact official accounting: {module_id}")
        module_matrix.append(
            {
                "module_id": module_id,
                "accounted_admission_unit_memberships": len({str(row["admission_unit_id"]) for row in module_rows}),
                "accounted_requirement_memberships": len(requirement_ids),
                "partial_or_composite_unit_memberships": len({str(row["admission_unit_id"]) for row in partial_module_rows}),
                "route_or_format_only_unit_memberships": len({str(row["admission_unit_id"]) for row in route_module_rows}),
                "semantic_review_group_memberships": len(group_ids),
                "note": "Module counts are membership counts and may overlap across modules; they must not be summed as global totals.",
            }
        )

    rights = json.loads(RIGHTS_SALVAGE.read_text(encoding="utf-8"))
    variants = rights.get("variants", [])
    asset_refs = sorted({str(asset) for variant in variants for asset in variant.get("assets", [])})
    if rights.get("status") != "RIGHTS_BLOCKED_SALVAGE_PINNED" or len(variants) != 5 or len(asset_refs) != 10:
        raise ValueError("PR139 rights-blocked salvage authority drift")
    rights_summary = {
        "status": "RIGHTS_BLOCKED",
        "authorship": str(rights["decision"]["authorship"]),
        "production_admission": str(rights["decision"]["production_admission"]),
        "semantic_or_mastery_admission": bool(rights["decision"]["semantic_or_mastery_admission"]),
        "copied_asset_bytes": 0,
        "variant_count": len(variants),
        "asset_ref_count": len(asset_refs),
        "variant_ids": sorted(str(variant["item_id"]) for variant in variants),
        "asset_refs": asset_refs,
        "salvage_pr": int(rights["salvage_source"]["pr"]),
        "salvage_head": str(rights["salvage_source"]["head"]),
    }

    route_format = []
    for row in sorted(route_rows, key=lambda item: str(item["admission_unit_id"])):
        route_format.append(
            {
                "admission_unit_id": str(row["admission_unit_id"]),
                "normalized_meaning": str(row["normalized_meaning"]),
                "modules": sorted(str(value) for value in row.get("modules", [])),
                "routes": sorted(str(value) for value in row.get("routes", [])),
                "requirements": [_source_member(member) for member in row.get("members", [])],
                "status": "ACCOUNTED_NON_SEMANTIC_ROUTE_OR_FORMAT_ONLY",
            }
        )

    packet: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED",
        "russian_content_ready": False,
        "object_accounting": {
            "status": str(accounting["status"]),
            "normalized_sha256": str(accounting["normalized_sha256"]),
            "object_review_queue_sha256": str(accounting["object_review_queue_sha256"]),
            "admission_units_accounted": 1325,
            "requirements_accounted": 1400,
            "partial_or_composite_units": 1316,
            "partial_or_composite_requirements": 1391,
            "route_or_format_only_units": 9,
            "route_or_format_only_requirements": 9,
            "canonical_semantic_admissions": 0,
            "ru_proposal_admissions": 0,
            "false_exact_mastery_admissions": 0,
        },
        "review_summary": {
            "finite_semantic_review_groups": len(review_groups),
            "groups_with_explicit_semantic_candidates": sum(bool(group["explicit_semantic_candidates"]) for group in review_groups),
            "distinct_explicit_semantic_candidates": len({
                (candidate["ref_kind"], candidate["ref"])
                for group in review_groups
                for candidate in group["explicit_semantic_candidates"]
            }),
            "semantic_groups_accepted": 0,
            "remaining_semantic_review_groups": len(review_groups),
        },
        "policy": {
            "reuse_first": True,
            "exact_source_and_semantic_truth_required": True,
            "keyword_or_fuzzy_inference_allowed": False,
            "module_presence_is_semantic_admission": False,
            "content_presence_is_semantic_admission": False,
            "proposed_ru_identity_is_canonical": False,
            "object_accounting_is_launch_readiness": False,
            "new_content_before_exact_reuse_gap_proof": False,
        },
        "module_matrix": module_matrix,
        "semantic_review_groups": review_groups,
        "route_or_format_only": route_format,
        "rights_blocked": rights_summary,
    }
    packet["normalized_sha256"] = hashlib.sha256(canonical_json(packet)).hexdigest()
    return packet


def render_markdown(packet: dict[str, Any]) -> str:
    obj = packet["object_accounting"]
    review = packet["review_summary"]
    lines = [
        "# Russian Full-Subject Semantic Acceptance Packet",
        "",
        f"Status: `{packet['status']}`  ",
        f"Russian content ready: `{str(packet['russian_content_ready']).lower()}`  ",
        f"Object-accounting SHA-256: `{obj['normalized_sha256']}`  ",
        f"Packet SHA-256: `{packet['normalized_sha256']}`",
        "",
        "## Exact boundary",
        "",
        f"Object accounting is complete: **{obj['admission_units_accounted']}/1325 admission units** and **{obj['requirements_accounted']}/1400 official requirements**. This does not admit semantics or content. The remaining bounded subject decision set is **{review['finite_semantic_review_groups']} exact normalized semantic review groups**.",
        "",
        "No canonical semantic identity or proposed `ru-*` identity is admitted by this packet. Keyword/fuzzy/module-only mapping is forbidden. Content presence is not admission; exact mastery requires component-specific independent evidence.",
        "",
        "## 16-module accounting matrix",
        "",
        "| Module | Unit memberships | Requirement memberships | Partial/composite | Route/format | Review groups |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in packet["module_matrix"]:
        lines.append(
            f"| {row['module_id']} | {row['accounted_admission_unit_memberships']} | {row['accounted_requirement_memberships']} | {row['partial_or_composite_unit_memberships']} | {row['route_or_format_only_unit_memberships']} | {row['semantic_review_group_memberships']} |"
        )
    lines.extend([
        "",
        "Module counts are membership counts and can overlap; they are not global totals.",
        "",
        "## Finite semantic review set",
        "",
        "| Group | Exact normalized meaning | Units | Requirements | Modules | Explicit candidates | Required action |",
        "|---|---|---:|---:|---|---:|---|",
    ])
    for group in packet["semantic_review_groups"]:
        meaning = str(group["normalized_meaning"]).replace("|", "\\|")
        modules = ", ".join(group["modules"])
        lines.append(
            f"| {group['group_id']} | {meaning} | {group['admission_unit_count']} | {group['requirement_count']} | {modules} | {len(group['explicit_semantic_candidates'])} | `{group['required_action']}` |"
        )
    rights = packet["rights_blocked"]
    lines.extend([
        "",
        "## Rights-blocked salvage",
        "",
        f"PR #{rights['salvage_pr']} Task-1 salvage remains fail-closed: authorship `{rights['authorship']}`, production admission `{rights['production_admission']}`, **{rights['variant_count']} variants / {rights['asset_ref_count']} MP3+TXT references**, copied asset bytes = **0**, semantic/mastery admission = **0**.",
        "",
        "## Next acceptance rule",
        "",
        "Review each group reuse-first against exact existing canonical/admitted semantics. Admit a canonical or proposed semantic target only with explicit Central Brain subject acceptance and exact source/boundary proof. Materialize new learner content only after an exact reuse/content-gap proof.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output")
    parser.add_argument("--markdown-output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    packet = build_packet()
    markdown = render_markdown(packet)
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(markdown, encoding="utf-8")
    if args.emit:
        print(json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_SEMANTIC_ACCEPTANCE_PACKET=PASS")
        print(f"OBJECT_ACCOUNTING_SHA256={packet['object_accounting']['normalized_sha256']}")
        print(f"PACKET_SHA256={packet['normalized_sha256']}")
        print(f"SEMANTIC_REVIEW_GROUPS={packet['review_summary']['finite_semantic_review_groups']}")
        print(f"GROUPS_WITH_EXPLICIT_CANDIDATES={packet['review_summary']['groups_with_explicit_semantic_candidates']}")
        print(f"DISTINCT_EXPLICIT_CANDIDATES={packet['review_summary']['distinct_explicit_semantic_candidates']}")
        print("SEMANTIC_GROUPS_ACCEPTED=0")
        print("RUSSIAN_CONTENT_READY=false")
        print("CANONICAL_SEMANTIC_ADMISSIONS=0")
        print("RU_PROPOSAL_ADMISSIONS=0")
        print("FALSE_MASTERY_ADMISSIONS=0")
        print("RIGHTS_BLOCKED_VARIANTS=5")
        print("RIGHTS_BLOCKED_ASSET_REFS=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
