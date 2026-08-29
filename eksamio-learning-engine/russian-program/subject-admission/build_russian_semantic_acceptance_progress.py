#!/usr/bin/env python3
"""Overlay accepted exact subject decisions onto the finite semantic packet.

The base 74-group packet stays the complete review universe. Object-bound
canonical component-set acceptances reduce the remaining object count only when
an exact admission-unit/requirement binding is proven. Bounded route-semantic
acceptances (currently RU16 Task-27 K1-K3 and K5) are tracked separately and
never subtract an object-level requirement until a separate exact binding exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
OBJECT_AUTHORITIES = (
    (
        HERE / "RUSSIAN-EGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
        "CENTRAL_BRAIN_ACCEPTED_EXACT_EGE_CANONICAL_COMPONENT_SLICE",
        5,
        "RUSSIAN_EGE_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
    ),
    (
        HERE / "RUSSIAN-OGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
        "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_CANONICAL_COMPONENT_SLICE",
        4,
        "RUSSIAN_OGE_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
    ),
    (
        HERE / "RUSSIAN-OGE-PUNCTUATION-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
        "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_PUNCTUATION_CANONICAL_COMPONENT_SLICE",
        8,
        "RUSSIAN_OGE_PUNCTUATION_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
    ),
)
ROUTE_SEMANTIC_AUTHORITIES = (
    (
        HERE / "RU16-TASK27-BOUNDED-ROUTE-SEMANTIC-ACCEPTANCE-v0.1.json",
        "CENTRAL_BRAIN_ACCEPTED_RU16_TASK27_K1_K3_ROUTE_SEMANTICS",
        4,
        "RU16_TASK27_BOUNDED_ROUTE_SEMANTIC_ACCEPTANCE_v0.1",
    ),
    (
        HERE / "RU16-TASK27-K5-BOUNDED-ROUTE-SEMANTIC-ACCEPTANCE-v0.1.json",
        "CENTRAL_BRAIN_ACCEPTED_RU16_TASK27_K5_ROUTE_SEMANTIC",
        1,
        "RU16_TASK27_K5_BOUNDED_ROUTE_SEMANTIC_ACCEPTANCE_v0.1",
    ),
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_progress() -> dict[str, Any]:
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    if packet.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("base semantic packet is not fail-closed")
    if packet.get("russian_content_ready") is not False:
        raise ValueError("base packet is unexpectedly content-ready")

    authorities: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for path, expected_status, expected_count, authority_id in OBJECT_AUTHORITIES:
        authority = json.loads(path.read_text(encoding="utf-8"))
        if authority.get("status") != expected_status:
            raise ValueError(f"exact component authority status drift: {path.name}")
        if authority.get("semantic_packet_sha256") != packet.get("normalized_sha256"):
            raise ValueError(f"authority is not bound to this semantic packet: {path.name}")
        if authority.get("object_accounting_sha256") != packet.get("object_accounting", {}).get("normalized_sha256"):
            raise ValueError(f"authority is not bound to this object accounting: {path.name}")
        rows = authority.get("decisions")
        if not isinstance(rows, list) or len(rows) != expected_count:
            raise ValueError(f"unexpected accepted decision count: {path.name}")
        authorities.append(
            {
                "id": authority_id,
                "authority_kind": "OBJECT_BOUND_CANONICAL_COMPONENT_SET",
                "sha256": str(authority["normalized_sha256"]),
                "status": str(authority["status"]),
                "accepted_admission_units": expected_count,
                "accepted_requirements": expected_count,
                "accepted_route_semantics": 0,
            }
        )
        for row in rows:
            decision = deepcopy(row)
            decision["accepted_authority_id"] = authority_id
            decisions.append(decision)

    accepted_route_semantics: set[str] = set()
    for path, expected_status, expected_count, authority_id in ROUTE_SEMANTIC_AUTHORITIES:
        authority = json.loads(path.read_text(encoding="utf-8"))
        if authority.get("status") != expected_status:
            raise ValueError(f"bounded route-semantic authority status drift: {path.name}")
        if authority.get("canonical_school_registry_mutated") is not False:
            raise ValueError(f"route-semantic authority mutated the school registry: {path.name}")
        if authority.get("new_parallel_registry_created") is not False:
            raise ValueError(f"route-semantic authority created a parallel registry: {path.name}")
        rows = authority.get("decisions")
        if rows is None and isinstance(authority.get("decision"), dict):
            rows = [authority["decision"]]
        if not isinstance(rows, list) or len(rows) != expected_count:
            raise ValueError(f"unexpected route-semantic decision count: {path.name}")
        refs = {str(row.get("accepted_semantic_id", "")) for row in rows}
        if len(refs) != expected_count or any(not ref.startswith("ru-") for ref in refs):
            raise ValueError(f"invalid bounded ru route-semantic set: {path.name}")
        if any(row.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_ROUTE_SEMANTIC" for row in rows):
            raise ValueError(f"route-semantic decision is not explicitly accepted: {path.name}")
        if accepted_route_semantics & refs:
            raise ValueError("route-semantic authorities overlap")
        accepted_route_semantics.update(refs)
        authorities.append(
            {
                "id": authority_id,
                "authority_kind": "BOUNDED_ROUTE_SEMANTIC_ACCEPTANCE_WITHOUT_OBJECT_BINDING",
                "sha256": hashlib.sha256(canonical_json(authority)).hexdigest(),
                "status": str(authority["status"]),
                "accepted_admission_units": 0,
                "accepted_requirements": 0,
                "accepted_route_semantics": expected_count,
            }
        )

    unit_ids = [str(row.get("admission_unit_id")) for row in decisions]
    requirement_ids = [str(row.get("requirement_id")) for row in decisions]
    if len(unit_ids) != len(set(unit_ids)):
        raise ValueError("accepted component authorities overlap on an admission unit")
    if len(requirement_ids) != len(set(requirement_ids)):
        raise ValueError("accepted component authorities overlap on a requirement")

    by_group = {str(group["group_id"]): deepcopy(group) for group in packet["semantic_review_groups"]}
    accepted_units: set[str] = set()
    accepted_requirements: set[str] = set()
    accepted_refs: set[str] = set()
    touched_groups: set[str] = set()

    for decision in decisions:
        if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET":
            raise ValueError("component-set decision is not Central-Brain accepted")
        mastery = decision.get("mastery_boundary", {})
        if mastery.get("route_or_broad_composite_attempt_can_emit_exact_component_mastery") is not False:
            raise ValueError("accepted component set weakened false-mastery guard")
        if mastery.get("component_specific_independent_evidence_required") is not True:
            raise ValueError("accepted component set lacks independent-evidence guard")
        refs = decision.get("canonical_component_refs")
        if not isinstance(refs, list) or not refs or any(not str(ref).startswith("school-") for ref in refs):
            raise ValueError("accepted component set contains non-canonical component ref")

        group_id = str(decision.get("authority", {}).get("packet_group", ""))
        group = by_group.get(group_id)
        if group is None:
            raise ValueError(f"accepted decision references unknown group: {group_id}")
        unit_id = str(decision["admission_unit_id"])
        requirement_id = str(decision["requirement_id"])
        if unit_id not in set(group.get("admission_unit_ids", [])):
            raise ValueError(f"accepted unit is not a member of packet group: {unit_id}")
        requirements = {str(row["requirement_id"]): row for row in group.get("requirements", [])}
        source_row = requirements.get(requirement_id)
        if source_row is None:
            raise ValueError(f"accepted requirement is not a member of packet group: {requirement_id}")
        if str(source_row.get("source_id")) != str(decision.get("source_id")):
            raise ValueError(f"accepted requirement source drift: {requirement_id}")
        if str(source_row.get("document_id")) != str(decision.get("document_id")):
            raise ValueError(f"accepted requirement document drift: {requirement_id}")
        if str(source_row.get("code")) != str(decision.get("content_code")):
            raise ValueError(f"accepted requirement code drift: {requirement_id}")
        if str(source_row.get("source_locator")) != str(decision.get("source_locator")):
            raise ValueError(f"accepted requirement locator drift: {requirement_id}")

        projection = {
            "accepted_authority_id": str(decision["accepted_authority_id"]),
            "admission_unit_id": unit_id,
            "requirement_id": requirement_id,
            "content_code": str(decision["content_code"]),
            "source_id": str(decision["source_id"]),
            "document_id": str(decision["document_id"]),
            "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
            "canonical_component_refs": list(refs),
            "component_count": len(refs),
            "mastery_boundary": deepcopy(mastery),
            "authority": deepcopy(decision["authority"]),
        }
        if "official_ege_task" in decision:
            projection["official_ege_task"] = int(decision["official_ege_task"])
        if "overlay_classification" in decision:
            projection["overlay_classification"] = str(decision["overlay_classification"])
        group.setdefault("accepted_component_sets", []).append(projection)
        group["status"] = "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET"
        group["accepted_component_set_count"] = len(group["accepted_component_sets"])
        group["remaining_group_action"] = "CONTINUE_EXACT_COMPONENT_REVIEW; DO NOT TREAT PARTIAL GROUP PROGRESS AS WHOLE-GROUP ACCEPTANCE"
        touched_groups.add(group_id)
        accepted_units.add(unit_id)
        accepted_requirements.add(requirement_id)
        accepted_refs.update(str(ref) for ref in refs)

    groups = [by_group[str(group["group_id"])] for group in packet["semantic_review_groups"]]
    for group in groups:
        if "accepted_component_sets" not in group:
            group["accepted_component_sets"] = []
            group["accepted_component_set_count"] = 0

    partial_units = int(packet["object_accounting"]["partial_or_composite_units"])
    partial_requirements = int(packet["object_accounting"]["partial_or_composite_requirements"])
    result: dict[str, Any] = {
        "schema_version": "0.3.0",
        "status": "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_IN_PROGRESS",
        "russian_content_ready": False,
        "base_packet_sha256": str(packet["normalized_sha256"]),
        "object_accounting_sha256": str(packet["object_accounting"]["normalized_sha256"]),
        "accepted_authorities": authorities,
        "progress_summary": {
            "finite_semantic_review_groups": len(groups),
            "fully_accepted_semantic_groups": 0,
            "review_groups_with_accepted_component_sets": len(touched_groups),
            "semantic_units_with_accepted_component_sets": len(accepted_units),
            "semantic_requirements_with_accepted_component_sets": len(accepted_requirements),
            "semantic_units_remaining_without_accepted_component_set": partial_units - len(accepted_units),
            "semantic_requirements_remaining_without_accepted_component_set": partial_requirements - len(accepted_requirements),
            "canonical_component_refs_reused_unique": len(accepted_refs),
            "accepted_bounded_ru_route_semantics": len(accepted_route_semantics),
            "accepted_route_semantics_without_object_binding": len(accepted_route_semantics),
            "new_semantic_identities_created": 0,
            "ru_proposal_identities_admitted": len(accepted_route_semantics),
            "false_exact_mastery_admissions": 0,
        },
        "accepted_route_semantic_refs": sorted(accepted_route_semantics),
        "policy": {
            "reuse_first": True,
            "whole_group_acceptance_from_partial_unit_progress": False,
            "generic_composite_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
            "keyword_or_fuzzy_inference_allowed": False,
            "module_only_mapping_allowed": False,
            "route_semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
        },
        "semantic_review_groups": groups,
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_progress()
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_SEMANTIC_ACCEPTANCE_PROGRESS=PASS")
        for key, value in result["progress_summary"].items():
            print(f"{key}={value}")
        print(f"NORMALIZED_PROGRESS_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
