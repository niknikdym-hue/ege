#!/usr/bin/env python3
"""Overlay accepted exact component-set decisions onto the finite semantic packet.

The base 74-group packet stays the complete review universe. This overlay records
only subject decisions already accepted by explicit exact authority. A group is
not marked fully accepted merely because one admission unit inside it has an
accepted component set.
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
EGE_ACCEPTANCE = HERE / "RUSSIAN-EGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_progress() -> dict[str, Any]:
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    authority = json.loads(EGE_ACCEPTANCE.read_text(encoding="utf-8"))

    if packet.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("base semantic packet is not fail-closed")
    if packet.get("russian_content_ready") is not False:
        raise ValueError("base packet is unexpectedly content-ready")
    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_EGE_CANONICAL_COMPONENT_SLICE":
        raise ValueError("exact EGE component authority status drift")
    if authority.get("semantic_packet_sha256") != packet.get("normalized_sha256"):
        raise ValueError("exact EGE authority is not bound to this semantic packet")
    if authority.get("object_accounting_sha256") != packet.get("object_accounting", {}).get("normalized_sha256"):
        raise ValueError("exact EGE authority is not bound to this object accounting")

    decisions = authority.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 5:
        raise ValueError("expected exactly five accepted EGE component-set decisions")
    if len({str(row.get("admission_unit_id")) for row in decisions}) != 5:
        raise ValueError("accepted EGE admission units are not unique")
    if len({str(row.get("requirement_id")) for row in decisions}) != 5:
        raise ValueError("accepted EGE requirements are not unique")

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
            "admission_unit_id": unit_id,
            "requirement_id": requirement_id,
            "content_code": str(decision["content_code"]),
            "official_ege_task": int(decision["official_ege_task"]),
            "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
            "canonical_component_refs": list(refs),
            "component_count": len(refs),
            "mastery_boundary": deepcopy(mastery),
            "authority": deepcopy(decision["authority"]),
        }
        group.setdefault("accepted_component_sets", []).append(projection)
        group["status"] = "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET"
        group["accepted_component_set_count"] = len(group["accepted_component_sets"])
        group["remaining_group_action"] = "CONTINUE_EXACT_COMPONENT_REVIEW; DO_NOT TREAT PARTIAL GROUP PROGRESS AS WHOLE-GROUP ACCEPTANCE"
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
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_IN_PROGRESS",
        "russian_content_ready": False,
        "base_packet_sha256": str(packet["normalized_sha256"]),
        "object_accounting_sha256": str(packet["object_accounting"]["normalized_sha256"]),
        "accepted_authorities": [
            {
                "id": "RUSSIAN_EGE_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
                "sha256": str(authority["normalized_sha256"]),
                "status": str(authority["status"]),
            }
        ],
        "progress_summary": {
            "finite_semantic_review_groups": len(groups),
            "fully_accepted_semantic_groups": 0,
            "review_groups_with_accepted_component_sets": len(touched_groups),
            "semantic_units_with_accepted_component_sets": len(accepted_units),
            "semantic_requirements_with_accepted_component_sets": len(accepted_requirements),
            "semantic_units_remaining_without_accepted_component_set": partial_units - len(accepted_units),
            "semantic_requirements_remaining_without_accepted_component_set": partial_requirements - len(accepted_requirements),
            "canonical_component_refs_reused_unique": len(accepted_refs),
            "new_semantic_identities_created": 0,
            "ru_proposal_identities_admitted": 0,
            "false_exact_mastery_admissions": 0,
        },
        "policy": {
            "reuse_first": True,
            "whole_group_acceptance_from_partial_unit_progress": False,
            "generic_composite_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
            "keyword_or_fuzzy_inference_allowed": False,
            "module_only_mapping_allowed": False,
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
