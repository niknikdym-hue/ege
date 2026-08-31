#!/usr/bin/env python3
"""Deterministic Russian batch-eligibility + exact-component acceptance wave 001.

The operational launch board requires batch closure over the finite 74 semantic
review groups instead of continuing one-object micro-audits. This wave is
intentionally conservative: it reuses an already Central-Brain-accepted exact
canonical component set only for unresolved *single-member* admission units in
the same finite normalized-meaning group and the same pinned official source
document as an accepted anchor. All accepted anchors in the group must agree on
one canonical owner set. No keyword/fuzzy/module inference and no new semantic
identity are allowed.

This is a source-homogeneous reuse rule, not a generic semantic fan-out rule.
Cross-document/cross-source reuse remains blocked for later explicit review.
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
PREBATCH = HERE / "build_russian_semantic_acceptance_progress_launch_prebatch.py"
ACCOUNTING = HERE / "build_russian_subject_accounting_complete.py"
AUTHORITY_ID = "RUSSIAN_BATCH_WAVE_001_EXACT_NORMALIZED_MEANING_SAME_DOCUMENT_REUSE"
STATUS_ACCEPTED = "CENTRAL_BRAIN_ACCEPTED_BATCH_WAVE_001_EXACT_COMPONENT_REUSE"
STATUS_EMPTY = "CENTRAL_BRAIN_BATCH_WAVE_001_NO_SAFE_ELIGIBLE_UNITS"

EXPECTED_PREBATCH = {
    "finite_semantic_review_groups": 74,
    "semantic_units_with_accepted_component_sets": 21,
    "semantic_requirements_with_accepted_component_sets": 21,
    "semantic_units_remaining_without_accepted_component_set": 1295,
    "semantic_requirements_remaining_without_accepted_component_set": 1370,
    "accepted_bounded_ru_semantics_total": 75,
    "false_exact_mastery_admissions": 0,
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _load_prebatch() -> dict[str, Any]:
    result = runpy.run_path(str(PREBATCH))["build_progress"]()
    if result.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_IN_PROGRESS" or result.get("russian_content_ready") is not False:
        raise ValueError("pre-batch launch progress is not fail-closed")
    summary = result.get("progress_summary") or {}
    for key, expected in EXPECTED_PREBATCH.items():
        if summary.get(key) != expected:
            raise ValueError(f"pre-batch progress drift: {key}={summary.get(key)!r}, expected {expected!r}")
    return result


def _load_accounting() -> dict[str, Any]:
    result = runpy.run_path(str(ACCOUNTING))["build_accounting"]()
    if result.get("status") != "RUSSIAN_FULL_SUBJECT_OBJECT_ACCOUNTING_COMPLETE_SEMANTIC_ACCEPTANCE_REQUIRED":
        raise ValueError("object accounting status drift")
    summary = result.get("summary") or {}
    if summary.get("admission_units_total") != 1325 or summary.get("requirements_total") != 1400:
        raise ValueError("object accounting denominator drift")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("object accounting contains false exact mastery")
    return result


def _build_wave(prebatch: dict[str, Any], accounting: dict[str, Any]) -> dict[str, Any]:
    unit_rows = {str(row["admission_unit_id"]): row for row in accounting.get("dispositions", [])}
    if len(unit_rows) != 1325:
        raise ValueError("accounting unit map drift")

    all_accepted_units: set[str] = set()
    all_accepted_requirements: set[str] = set()
    for group in prebatch.get("semantic_review_groups", []):
        for accepted in group.get("accepted_component_sets", []):
            all_accepted_units.add(str(accepted["admission_unit_id"]))
            all_accepted_requirements.add(str(accepted["requirement_id"]))
    if len(all_accepted_units) != 21 or len(all_accepted_requirements) != 21:
        raise ValueError("pre-batch accepted object set drift")

    decisions: list[dict[str, Any]] = []
    eligible_group_rows: list[dict[str, Any]] = []
    skipped: dict[str, int] = {}

    def skip(reason: str) -> None:
        skipped[reason] = skipped.get(reason, 0) + 1

    for group in prebatch.get("semantic_review_groups", []):
        group_id = str(group.get("group_id", ""))
        meaning = str(group.get("normalized_meaning", ""))
        unit_ids = [str(value) for value in group.get("admission_unit_ids", [])]
        requirements = {str(row["requirement_id"]): row for row in group.get("requirements", [])}
        anchors = list(group.get("accepted_component_sets", []))
        if not anchors:
            skip("NO_ACCEPTED_EXACT_ANCHOR")
            continue

        owner_sets = {tuple(str(ref) for ref in row.get("canonical_component_refs", [])) for row in anchors}
        if len(owner_sets) != 1:
            skip("ANCHOR_OWNER_SET_DISAGREEMENT")
            continue
        owner_refs = next(iter(owner_sets))
        if not owner_refs or any(not ref.startswith("school-") for ref in owner_refs):
            raise ValueError(f"noncanonical anchor owner set in {group_id}")
        for anchor in anchors:
            mastery = anchor.get("mastery_boundary") or {}
            if mastery.get("route_or_broad_composite_attempt_can_emit_exact_component_mastery") is not False:
                raise ValueError(f"anchor false-mastery guard weakened in {group_id}")
            if mastery.get("component_specific_independent_evidence_required") is not True:
                raise ValueError(f"anchor independent-evidence guard missing in {group_id}")

        anchor_docs = {
            (str(anchor.get("source_id", "")), str(anchor.get("document_id", "")))
            for anchor in anchors
        }
        if any(not source_id or not document_id for source_id, document_id in anchor_docs):
            raise ValueError(f"anchor source-document identity missing in {group_id}")

        anchor_authority_ids = sorted({str(anchor.get("accepted_authority_id", "")) for anchor in anchors})
        anchor_unit_ids = sorted({str(anchor.get("admission_unit_id", "")) for anchor in anchors})
        group_new: list[dict[str, Any]] = []

        for unit_id in unit_ids:
            if unit_id in all_accepted_units:
                continue
            row = unit_rows.get(unit_id)
            if row is None:
                raise ValueError(f"group references unknown accounting unit: {unit_id}")
            if str(row.get("normalized_meaning", "")) != meaning:
                raise ValueError(f"group/accounting normalized meaning drift: {group_id}/{unit_id}")
            if row.get("disposition") != "PARTIAL_OR_COMPOSITE" or row.get("semantic_identity_ref") is not None:
                raise ValueError(f"unexpected unresolved accounting state: {unit_id}")
            mastery = row.get("mastery_boundary") or {}
            if mastery.get("generic_domain_attempt_can_emit_exact_component_mastery") is not False:
                raise ValueError(f"unresolved row allows false exact mastery: {unit_id}")
            if mastery.get("component_mastery_requires_component_specific_independent_evidence") is not True:
                raise ValueError(f"unresolved row independent-evidence guard missing: {unit_id}")

            members = row.get("members") or []
            if len(members) != 1:
                continue
            member = members[0]
            requirement_id = str(member.get("requirement_id", ""))
            if not requirement_id or requirement_id in all_accepted_requirements:
                continue
            source_doc = (str(member.get("source_id", "")), str(member.get("document_id", "")))
            if source_doc not in anchor_docs:
                continue
            packet_req = requirements.get(requirement_id)
            if packet_req is None:
                raise ValueError(f"group requirement missing for unit {unit_id}")
            for key in ("source_id", "document_id", "source_locator"):
                if str(member.get(key, "")) != str(packet_req.get(key, "")):
                    raise ValueError(f"packet/accounting source drift: {requirement_id}/{key}")
            if str(member.get("code", "")) != str(packet_req.get("code", "")):
                raise ValueError(f"packet/accounting code drift: {requirement_id}")

            decision = {
                "admission_unit_id": unit_id,
                "requirement_id": requirement_id,
                "source_id": str(member["source_id"]),
                "document_id": str(member["document_id"]),
                "source_locator": str(member["source_locator"]),
                "content_code": str(member.get("code", "")),
                "normalized_meaning": meaning,
                "modules": list(row.get("modules", [])),
                "routes": list(row.get("routes", [])),
                "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
                "canonical_component_refs": list(owner_refs),
                "component_count": len(owner_refs),
                "mapping_mode": "EXACT_NORMALIZED_MEANING_SAME_PINNED_OFFICIAL_DOCUMENT_REUSE",
                "authority": {
                    "packet_group": group_id,
                    "accepted_anchor_unit_ids": anchor_unit_ids,
                    "accepted_anchor_authority_ids": anchor_authority_ids,
                    "reuse_rule": "EXACT_NORMALIZED_MEANING_AND_SAME_SOURCE_ID_DOCUMENT_ID_ONLY",
                    "cross_document_reuse_allowed": False,
                    "keyword_fuzzy_module_only_inference_allowed": False,
                },
                "acceptance_reason": (
                    "Exact finite-group reuse: this unresolved single-member object has the identical normalized official meaning "
                    "and belongs to the same pinned official source document as an already accepted exact component-set anchor. "
                    "All accepted anchors in the group agree on one canonical school-* owner set."
                ),
                "mastery_boundary": {
                    "route_or_broad_composite_attempt_can_emit_exact_component_mastery": False,
                    "component_specific_independent_evidence_required": True,
                    "accepted_mapping_can_emit_partial_or_composite_evidence": True,
                },
            }
            group_new.append(decision)

        if group_new:
            group_new.sort(key=lambda row: (row["source_id"], row["document_id"], row["content_code"], row["requirement_id"], row["admission_unit_id"]))
            decisions.extend(group_new)
            eligible_group_rows.append({
                "group_id": group_id,
                "normalized_meaning": meaning,
                "canonical_component_refs": list(owner_refs),
                "accepted_anchor_unit_ids": anchor_unit_ids,
                "accepted_anchor_authority_ids": anchor_authority_ids,
                "eligible_new_units": len(group_new),
                "eligible_new_requirements": len(group_new),
                "source_documents": sorted({f"{row['source_id']}/{row['document_id']}" for row in group_new}),
            })
        else:
            skip("ANCHOR_GROUP_HAS_NO_SAME_DOCUMENT_SINGLE_MEMBER_REUSE")

    decisions.sort(key=lambda row: (row["authority"]["packet_group"], row["requirement_id"], row["admission_unit_id"]))
    unit_ids = [row["admission_unit_id"] for row in decisions]
    requirement_ids = [row["requirement_id"] for row in decisions]
    if len(unit_ids) != len(set(unit_ids)) or len(requirement_ids) != len(set(requirement_ids)):
        raise ValueError("batch wave duplicated unit/requirement")
    if set(unit_ids) & all_accepted_units or set(requirement_ids) & all_accepted_requirements:
        raise ValueError("batch wave overlaps pre-batch accepted objects")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": STATUS_ACCEPTED if decisions else STATUS_EMPTY,
        "authority_id": AUTHORITY_ID,
        "prebatch_progress_sha256": str(prebatch["normalized_sha256"]),
        "object_accounting_sha256": str(accounting["normalized_sha256"]),
        "eligibility_rule": {
            "finite_group_exact_normalized_meaning_required": True,
            "accepted_anchor_required": True,
            "all_group_anchors_must_have_identical_canonical_owner_set": True,
            "same_pinned_source_id_and_document_id_as_anchor_required": True,
            "single_member_admission_unit_required": True,
            "cross_document_reuse_allowed": False,
            "cross_source_reuse_allowed": False,
            "keyword_fuzzy_module_only_inference_allowed": False,
            "new_semantic_identity_creation_allowed": False,
            "component_specific_independent_evidence_required": True,
        },
        "summary": {
            "finite_semantic_review_groups": 74,
            "prebatch_accepted_units": len(all_accepted_units),
            "prebatch_accepted_requirements": len(all_accepted_requirements),
            "batch_eligible_groups": len(eligible_group_rows),
            "batch_accepted_units": len(decisions),
            "batch_accepted_requirements": len(decisions),
            "new_semantic_identities_created": 0,
            "false_exact_mastery_admissions": 0,
        },
        "eligible_groups": eligible_group_rows,
        "skipped_group_reason_counts": dict(sorted(skipped.items())),
        "decisions": decisions,
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def build_wave() -> dict[str, Any]:
    return _build_wave(_load_prebatch(), _load_accounting())


def apply_wave(prebatch: dict[str, Any], wave: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(prebatch)
    decisions = list(wave.get("decisions", []))
    if not decisions:
        result["batch_wave_001"] = {
            "status": str(wave["status"]),
            "authority_id": AUTHORITY_ID,
            "normalized_sha256": str(wave["normalized_sha256"]),
            "accepted_admission_units": 0,
            "accepted_requirements": 0,
        }
        result["schema_version"] = "0.5.0"
        result.pop("normalized_sha256", None)
        result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
        return result

    by_group = {str(group["group_id"]): group for group in result["semantic_review_groups"]}
    existing_units = {
        str(row["admission_unit_id"])
        for group in result["semantic_review_groups"]
        for row in group.get("accepted_component_sets", [])
    }
    existing_requirements = {
        str(row["requirement_id"])
        for group in result["semantic_review_groups"]
        for row in group.get("accepted_component_sets", [])
    }

    for decision in decisions:
        unit_id = str(decision["admission_unit_id"])
        requirement_id = str(decision["requirement_id"])
        if unit_id in existing_units or requirement_id in existing_requirements:
            raise ValueError("batch wave overlaps accepted progress")
        group_id = str((decision.get("authority") or {}).get("packet_group", ""))
        group = by_group.get(group_id)
        if group is None:
            raise ValueError(f"batch decision references unknown group: {group_id}")
        if unit_id not in set(str(value) for value in group.get("admission_unit_ids", [])):
            raise ValueError(f"batch decision unit not in packet group: {unit_id}")
        packet_req = {str(row["requirement_id"]): row for row in group.get("requirements", [])}.get(requirement_id)
        if packet_req is None:
            raise ValueError(f"batch decision requirement not in packet group: {requirement_id}")
        for key, packet_key in (("source_id", "source_id"), ("document_id", "document_id"), ("content_code", "code"), ("source_locator", "source_locator")):
            if str(decision.get(key, "")) != str(packet_req.get(packet_key, "")):
                raise ValueError(f"batch decision source drift: {requirement_id}/{key}")
        refs = decision.get("canonical_component_refs")
        if not isinstance(refs, list) or not refs or any(not str(ref).startswith("school-") for ref in refs):
            raise ValueError("batch decision contains noncanonical component ref")
        mastery = decision.get("mastery_boundary") or {}
        if mastery.get("route_or_broad_composite_attempt_can_emit_exact_component_mastery") is not False:
            raise ValueError("batch decision weakened false-mastery guard")
        if mastery.get("component_specific_independent_evidence_required") is not True:
            raise ValueError("batch decision lacks independent-evidence guard")

        projection = {
            "accepted_authority_id": AUTHORITY_ID,
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
        group.setdefault("accepted_component_sets", []).append(projection)
        group["accepted_component_sets"].sort(key=lambda row: (str(row["requirement_id"]), str(row["admission_unit_id"])))
        group["accepted_component_set_count"] = len(group["accepted_component_sets"])
        existing_units.add(unit_id)
        existing_requirements.add(requirement_id)

    all_accepted_units: set[str] = set()
    all_accepted_requirements: set[str] = set()
    all_refs: set[str] = set()
    touched = 0
    fully_accepted = 0
    for group in result["semantic_review_groups"]:
        rows = group.get("accepted_component_sets", [])
        unit_set = {str(row["admission_unit_id"]) for row in rows}
        requirement_set = {str(row["requirement_id"]) for row in rows}
        if rows:
            touched += 1
            group["status"] = "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET"
        if unit_set and unit_set == set(str(value) for value in group.get("admission_unit_ids", [])):
            fully_accepted += 1
            group["status"] = "CENTRAL_BRAIN_EXACT_COMPONENT_SET_ACCEPTED_FOR_ALL_GROUP_UNITS"
            group["remaining_group_action"] = "PRESERVE_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE; NO_GENERIC_GROUP_MASTERY"
        elif rows:
            group["remaining_group_action"] = "CONTINUE_EXACT_COMPONENT_REVIEW; DO NOT TREAT PARTIAL GROUP PROGRESS AS WHOLE-GROUP ACCEPTANCE"
        all_accepted_units.update(unit_set)
        all_accepted_requirements.update(requirement_set)
        for row in rows:
            all_refs.update(str(ref) for ref in row.get("canonical_component_refs", []))

    if len(all_accepted_units) != 21 + len(decisions) or len(all_accepted_requirements) != 21 + len(decisions):
        raise ValueError("post-batch accepted object total drift")

    summary = result["progress_summary"]
    partial_units = 1316
    partial_requirements = 1391
    summary["fully_accepted_semantic_groups"] = fully_accepted
    summary["review_groups_with_accepted_component_sets"] = touched
    summary["semantic_units_with_accepted_component_sets"] = len(all_accepted_units)
    summary["semantic_requirements_with_accepted_component_sets"] = len(all_accepted_requirements)
    summary["semantic_units_remaining_without_accepted_component_set"] = partial_units - len(all_accepted_units)
    summary["semantic_requirements_remaining_without_accepted_component_set"] = partial_requirements - len(all_accepted_requirements)
    summary["canonical_component_refs_reused_unique"] = len(all_refs)
    summary["false_exact_mastery_admissions"] = 0

    result["accepted_authorities"].append({
        "id": AUTHORITY_ID,
        "authority_kind": "BATCH_OBJECT_BOUND_CANONICAL_COMPONENT_SET_REUSE",
        "sha256": str(wave["normalized_sha256"]),
        "status": str(wave["status"]),
        "accepted_admission_units": len(decisions),
        "accepted_requirements": len(decisions),
        "accepted_route_semantics": 0,
        "accepted_subject_semantics": 0,
    })
    result["batch_wave_001"] = {
        "status": str(wave["status"]),
        "authority_id": AUTHORITY_ID,
        "normalized_sha256": str(wave["normalized_sha256"]),
        "accepted_admission_units": len(decisions),
        "accepted_requirements": len(decisions),
        "eligible_groups": int(wave["summary"]["batch_eligible_groups"]),
    }
    result["policy"]["batch_reuse_requires_exact_normalized_meaning"] = True
    result["policy"]["batch_reuse_requires_same_pinned_source_document_as_accepted_anchor"] = True
    result["policy"]["batch_cross_document_reuse_allowed"] = False
    result["policy"]["batch_keyword_fuzzy_module_only_inference_allowed"] = False
    result["schema_version"] = "0.5.0"
    result.pop("normalized_sha256", None)
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def build_batched_progress() -> tuple[dict[str, Any], dict[str, Any]]:
    prebatch = _load_prebatch()
    accounting = _load_accounting()
    wave = _build_wave(prebatch, accounting)
    progress = apply_wave(prebatch, wave)
    return wave, progress


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave-output")
    parser.add_argument("--progress-output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    wave, progress = build_batched_progress()
    if args.wave_output:
        Path(args.wave_output).write_text(json.dumps(wave, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.progress_output:
        Path(args.progress_output).write_text(json.dumps(progress, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps({"wave": wave, "progress": progress}, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        ws = wave["summary"]
        ps = progress["progress_summary"]
        print("RUSSIAN_BATCH_WAVE_001=PASS")
        print(f"WAVE_STATUS={wave['status']}")
        print(f"BATCH_ELIGIBLE_GROUPS={ws['batch_eligible_groups']}")
        print(f"BATCH_ACCEPTED_UNITS={ws['batch_accepted_units']}")
        print(f"BATCH_ACCEPTED_REQUIREMENTS={ws['batch_accepted_requirements']}")
        print(f"POST_ACCEPTED_UNITS={ps['semantic_units_with_accepted_component_sets']}")
        print(f"POST_ACCEPTED_REQUIREMENTS={ps['semantic_requirements_with_accepted_component_sets']}")
        print(f"POST_REMAINING_UNITS={ps['semantic_units_remaining_without_accepted_component_set']}")
        print(f"POST_REMAINING_REQUIREMENTS={ps['semantic_requirements_remaining_without_accepted_component_set']}")
        print(f"FULLY_ACCEPTED_GROUPS={ps['fully_accepted_semantic_groups']}")
        print(f"FALSE_EXACT_MASTERY={ps['false_exact_mastery_admissions']}")
        print(f"WAVE_SHA256={wave['normalized_sha256']}")
        print(f"PROGRESS_SHA256={progress['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
