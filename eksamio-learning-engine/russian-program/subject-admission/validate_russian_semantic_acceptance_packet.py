#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"
EXPECTED_MODULES = [f"RU-PROG-{number:02d}" for number in range(1, 17)]


def _candidate_key(component: dict[str, Any]) -> tuple[str, str, str, str | None]:
    return (
        str(component.get("ref_kind", "")),
        str(component.get("ref", "")),
        str(component.get("status", "")),
        str(component["content_ref"]) if component.get("content_ref") is not None else None,
    )


def main() -> int:
    packet_ns = runpy.run_path(str(PACKET_BUILDER))
    build_packet = packet_ns["build_packet"]
    render_markdown = packet_ns["render_markdown"]
    canonical_json = packet_ns["canonical_json"]
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()

    first: dict[str, Any] = build_packet()
    second: dict[str, Any] = build_packet()
    if canonical_json(first) != canonical_json(second):
        raise AssertionError("semantic acceptance packet is not deterministic")
    if render_markdown(first) != render_markdown(second):
        raise AssertionError("human semantic acceptance packet is not deterministic")

    if first.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED":
        raise AssertionError("semantic packet status drift")
    if first.get("russian_content_ready") is not False:
        raise AssertionError("semantic packet falsely marks Russian content ready")
    obj = first.get("object_accounting", {})
    if obj.get("admission_units_accounted") != 1325 or obj.get("requirements_accounted") != 1400:
        raise AssertionError("semantic packet lost complete object-accounting truth")
    if obj.get("partial_or_composite_units") != 1316 or obj.get("partial_or_composite_requirements") != 1391:
        raise AssertionError("semantic packet partial/composite totals drift")
    if obj.get("route_or_format_only_units") != 9 or obj.get("route_or_format_only_requirements") != 9:
        raise AssertionError("semantic packet route/format totals drift")
    if obj.get("canonical_semantic_admissions") != 0 or obj.get("ru_proposal_admissions") != 0 or obj.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("semantic packet contains a false admission")
    if obj.get("normalized_sha256") != accounting.get("normalized_sha256"):
        raise AssertionError("semantic packet is not bound to current complete accounting")

    groups = first.get("semantic_review_groups")
    if not isinstance(groups, list) or len(groups) != 74:
        raise AssertionError("semantic packet must contain exactly 74 review groups")
    group_ids = [str(group.get("group_id", "")) for group in groups]
    meanings = [str(group.get("normalized_meaning", "")) for group in groups]
    if "" in group_ids or len(group_ids) != len(set(group_ids)):
        raise AssertionError("semantic packet has missing/duplicate group ids")
    if "" in meanings or len(meanings) != len(set(meanings)):
        raise AssertionError("semantic packet has missing/duplicate exact meanings")

    partial_rows = [row for row in accounting["dispositions"] if row.get("disposition") == "PARTIAL_OR_COMPOSITE"]
    expected_units = {str(row["admission_unit_id"]) for row in partial_rows}
    expected_requirements = {
        str(member["requirement_id"])
        for row in partial_rows
        for member in row.get("members", [])
    }
    packet_units: list[str] = []
    packet_requirements: list[str] = []
    accounting_by_unit = {str(row["admission_unit_id"]): row for row in partial_rows}

    for group in groups:
        if group.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
            raise AssertionError("semantic review group was silently accepted")
        candidates = group.get("explicit_semantic_candidates")
        if not isinstance(candidates, list):
            raise AssertionError("group explicit-candidate inventory missing")
        expected_action = "REVIEW_EXPLICIT_COMPONENT_CANDIDATES" if candidates else "DECOMPOSE_AND_MAP_EXACT_COMPONENTS"
        if group.get("required_action") != expected_action:
            raise AssertionError("semantic review action does not reflect exact candidate evidence")
        boundary = group.get("acceptance_boundary", {})
        if boundary.get("keyword_or_fuzzy_inference_allowed") is not False:
            raise AssertionError("keyword/fuzzy inference was enabled")
        if boundary.get("module_only_mapping_allowed") is not False:
            raise AssertionError("module-only semantic mapping was enabled")
        if boundary.get("content_presence_implies_admission") is not False:
            raise AssertionError("content presence became semantic admission")
        if boundary.get("generic_group_attempt_can_emit_exact_component_mastery") is not False:
            raise AssertionError("broad-group evidence can emit false exact mastery")
        if boundary.get("exact_mastery_requires_component_specific_independent_evidence") is not True:
            raise AssertionError("component-specific evidence guard weakened")
        if boundary.get("canonical_or_proposed_admission_requires_explicit_central_brain_acceptance") is not True:
            raise AssertionError("Central Brain semantic acceptance boundary weakened")

        unit_ids = [str(value) for value in group.get("admission_unit_ids", [])]
        source_rows = group.get("requirements")
        if not isinstance(source_rows, list):
            raise AssertionError("group source rows missing")
        requirement_ids = [str(row.get("requirement_id", "")) for row in source_rows]
        if len(unit_ids) != group.get("admission_unit_count") or len(requirement_ids) != group.get("requirement_count"):
            raise AssertionError("group count summary drift")
        if len(unit_ids) != len(set(unit_ids)) or len(requirement_ids) != len(set(requirement_ids)):
            raise AssertionError("group duplicates exact units/requirements")
        if any(not row.get("source_id") or not row.get("document_id") or row.get("page") is None or not row.get("source_locator") for row in source_rows):
            raise AssertionError("group lost exact official source locator")
        packet_units.extend(unit_ids)
        packet_requirements.extend(requirement_ids)

        source_ids_expected: set[str] = set()
        modules_expected: set[str] = set()
        routes_expected: set[str] = set()
        candidate_expected: set[tuple[str, str, str, str | None]] = set()
        exact_req_expected: set[str] = set()
        for unit_id in unit_ids:
            row = accounting_by_unit.get(unit_id)
            if row is None or str(row["normalized_meaning"]) != str(group["normalized_meaning"]):
                raise AssertionError("group unit escaped exact normalized meaning")
            modules_expected.update(str(value) for value in row.get("modules", []))
            routes_expected.update(str(value) for value in row.get("routes", []))
            for member in row.get("members", []):
                source_ids_expected.add(str(member["source_id"]))
                exact_req_expected.add(str(member["requirement_id"]))
            for component in row.get("component_refs", []) or []:
                if component.get("ref_kind") in {"existing_semantic_candidate", "proposed_semantic_with_content"}:
                    candidate_expected.add(_candidate_key(component))
        if set(group.get("source_ids", [])) != source_ids_expected:
            raise AssertionError("group source-id set drift")
        if set(group.get("modules", [])) != modules_expected:
            raise AssertionError("group module set drift")
        if set(group.get("routes", [])) != routes_expected:
            raise AssertionError("group route set drift")
        if set(requirement_ids) != exact_req_expected:
            raise AssertionError("group source requirements do not exactly match its admission units")
        candidate_actual = {_candidate_key(candidate) for candidate in candidates}
        if candidate_actual != candidate_expected:
            raise AssertionError("group explicit semantic candidates are not exact ledger-derived candidates")
        for candidate in candidates:
            kind = candidate.get("ref_kind")
            status = str(candidate.get("status", ""))
            if kind == "existing_semantic_candidate":
                if not status.endswith("NOT_ADMITTED_BY_THIS_SET"):
                    raise AssertionError("existing semantic candidate was admitted")
            elif kind == "proposed_semantic_with_content":
                if status != "PROPOSED_NOT_CANONICAL" or not candidate.get("content_ref"):
                    raise AssertionError("proposed semantic/content candidate escaped fail-closed status")
            else:
                raise AssertionError("unsupported candidate kind in semantic packet")

    if len(packet_units) != 1316 or set(packet_units) != expected_units or len(packet_units) != len(set(packet_units)):
        raise AssertionError("74-group packet does not partition all 1316 semantic admission units exactly once")
    if len(packet_requirements) != 1391 or set(packet_requirements) != expected_requirements or len(packet_requirements) != len(set(packet_requirements)):
        raise AssertionError("74-group packet does not partition all 1391 semantic requirements exactly once")

    matrix = first.get("module_matrix")
    if not isinstance(matrix, list) or [row.get("module_id") for row in matrix] != EXPECTED_MODULES:
        raise AssertionError("16-module matrix coverage/order drift")
    if any(int(row.get("accounted_admission_unit_memberships", 0)) <= 0 or int(row.get("accounted_requirement_memberships", 0)) <= 0 for row in matrix):
        raise AssertionError("one or more Russian modules have zero exact official accounting")

    route = first.get("route_or_format_only")
    if not isinstance(route, list) or len(route) != 9:
        raise AssertionError("route/format-only packet must contain exactly 9 non-semantic rows")
    if any(row.get("status") != "ACCOUNTED_NON_SEMANTIC_ROUTE_OR_FORMAT_ONLY" for row in route):
        raise AssertionError("route/format-only row escaped non-semantic status")

    rights = first.get("rights_blocked", {})
    if rights.get("status") != "RIGHTS_BLOCKED" or rights.get("authorship") != "NOT_PROVEN":
        raise AssertionError("rights-blocked salvage status drift")
    if rights.get("production_admission") != "EXCLUDED_RIGHTS_BLOCKED" or rights.get("semantic_or_mastery_admission") is not False:
        raise AssertionError("rights-blocked salvage was admitted")
    if rights.get("copied_asset_bytes") != 0 or rights.get("variant_count") != 5 or rights.get("asset_ref_count") != 10:
        raise AssertionError("rights-blocked salvage counts drift")

    review_summary = first.get("review_summary", {})
    if review_summary.get("finite_semantic_review_groups") != 74 or review_summary.get("semantic_groups_accepted") != 0 or review_summary.get("remaining_semantic_review_groups") != 74:
        raise AssertionError("finite semantic-review summary drift")

    normalized_sha = str(first.get("normalized_sha256", ""))
    unhashed = copy.deepcopy(first)
    unhashed.pop("normalized_sha256", None)
    expected_sha = hashlib.sha256(canonical_json(unhashed)).hexdigest()
    if normalized_sha != expected_sha:
        raise AssertionError("semantic packet normalized SHA-256 does not bind the packet")

    print("RUSSIAN_SEMANTIC_ACCEPTANCE_PACKET_VALIDATION=PASS")
    print("OBJECT_ACCOUNTING=1325/1325_UNITS_1400/1400_REQUIREMENTS")
    print("SEMANTIC_REVIEW_GROUPS=74")
    print(f"GROUPS_WITH_EXPLICIT_CANDIDATES={review_summary['groups_with_explicit_semantic_candidates']}")
    print(f"DISTINCT_EXPLICIT_CANDIDATES={review_summary['distinct_explicit_semantic_candidates']}")
    print("SEMANTIC_GROUPS_ACCEPTED=0")
    print("RUSSIAN_CONTENT_READY=false")
    print("CANONICAL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=0")
    print("FALSE_MASTERY_ADMISSIONS=0")
    print("MODULES_WITH_ACCOUNTING=16/16")
    print("RIGHTS_BLOCKED_VARIANTS=5")
    print("RIGHTS_BLOCKED_ASSET_REFS=10")
    print(f"PACKET_SHA256={normalized_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
