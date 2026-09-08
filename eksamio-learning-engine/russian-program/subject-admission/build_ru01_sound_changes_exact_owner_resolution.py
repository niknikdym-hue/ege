#!/usr/bin/env python3
"""Fail-closed exact-owner search for residual RU01 sound-changes source objects."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RUSSIAN_PROGRAM = HERE.parent
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v13.py"
BINDING = HERE / "build_ru01_phonetics_exact_object_binding_review.py"

CURRENT_SHA = "f8c8c1f060eb596fc92c317b38d1c12e572a8827cb56042390ed08b0f681a426"
GROUP = "RUS-SEM-REVIEW-001"
SIGNATURE = "SOUND_CHANGES_IN_SPEECH_FLOW"
PROPOSED_ID = "ru-phonetics-sound-changes-in-speech-flow"

TARGETS = [
    {
        "admission_unit_id": "RAU-b1ba48cb81e96255122a",
        "requirement_id": "RSK-EDSOO59-4-1-3-P187",
        "source_id": "EDSOO-RU-5-9-2025",
        "document_id": "EDSOO59",
        "document_sha256": "1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d",
        "page": 187,
        "content_code": "4.1.3",
        "source_locator": "EDSOO-RU-5-9-2025/EDSOO59 p.187 4.1.3",
    },
    {
        "admission_unit_id": "RAU-f709f1855bb0b8d104bc",
        "requirement_id": "RSK-OGE_COD-4-1-3-P021",
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "document_id": "OGE_COD",
        "document_sha256": "2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a",
        "page": 21,
        "content_code": "4.1.3",
        "source_locator": "FIPI-OGE-RU-2026-FINAL/OGE_COD p.21 4.1.3",
    },
]

EXPECTED_SUMMARY = {
    "semantic_units_with_accepted_component_sets": 38,
    "semantic_requirements_with_accepted_component_sets": 38,
    "subject_disposed_units_total": 39,
    "subject_disposed_requirements_total": 39,
    "subject_review_units_remaining": 1277,
    "subject_review_requirements_remaining": 1352,
    "accepted_bounded_ru_subject_semantics": 67,
    "accepted_bounded_ru_semantics_total": 76,
    "false_exact_mastery_admissions": 0,
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def walk(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def all_strings(value: Any) -> set[str]:
    out: set[str] = set()
    if isinstance(value, str):
        out.add(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            out.add(str(key))
            out |= all_strings(item)
    elif isinstance(value, list):
        for item in value:
            out |= all_strings(item)
    return out


def accepted_semantic_ids(value: Any) -> set[str]:
    statuses = {
        item for key, item in walk(value)
        if key == "status" and isinstance(item, str) and item.startswith("CENTRAL_BRAIN_ACCEPTED")
    }
    if not statuses:
        return set()
    ids = {
        item for key, item in walk(value)
        if key == "accepted_semantic_id" and isinstance(item, str) and item.startswith("ru-")
    }
    return ids


def scan_exact_current_owner() -> dict[str, Any]:
    accepted_ids: set[str] = set()
    source_bound: list[dict[str, Any]] = []
    target_markers = {SIGNATURE}
    target_markers.update(t["requirement_id"] for t in TARGETS)
    target_markers.update(t["source_locator"] for t in TARGETS)

    for path in sorted(RUSSIAN_PROGRAM.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        ids = accepted_semantic_ids(data)
        if not ids:
            continue
        accepted_ids |= ids
        strings = all_strings(data)
        exact_markers = sorted(target_markers & strings)
        if exact_markers:
            source_bound.append({
                "path": path.relative_to(RUSSIAN_PROGRAM).as_posix(),
                "accepted_semantic_ids": sorted(ids),
                "exact_markers": exact_markers,
            })

    exact_identity_present = PROPOSED_ID in accepted_ids
    candidate_ids = sorted({
        semantic_id
        for row in source_bound
        for semantic_id in row["accepted_semantic_ids"]
    })
    return {
        "accepted_semantic_ids_scanned": len(accepted_ids),
        "proposed_source_derived_identity_exactly_present": exact_identity_present,
        "source_bound_accepted_owner_candidates": source_bound,
        "source_bound_accepted_semantic_ids": candidate_ids,
    }


def build_resolution() -> dict[str, Any]:
    current = runpy.run_path(str(CURRENT))["build_progress"]()
    if current.get("normalized_sha256") != CURRENT_SHA:
        raise ValueError("current-v13 normalized SHA drift")
    if current.get("schema_version") != "0.16.0":
        raise ValueError("current-v13 schema drift")
    if len(current.get("accepted_authorities") or []) != 60:
        raise ValueError("current-v13 authority count drift")
    summary = current.get("progress_summary") or {}
    for key, expected in EXPECTED_SUMMARY.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v13 aggregate drift: {key}")

    groups = [g for g in current.get("semantic_review_groups") or [] if g.get("group_id") == GROUP]
    if len(groups) != 1:
        raise ValueError("RU01 group not unique")
    group = groups[0]
    accepted = group.get("accepted_component_sets") or []
    accepted_units = {str(row.get("admission_unit_id")) for row in accepted if isinstance(row, dict)}
    accepted_reqs = {str(row.get("requirement_id")) for row in accepted if isinstance(row, dict)}
    requirements = {str(row.get("requirement_id")): row for row in group.get("requirements") or [] if isinstance(row, dict)}

    binding = runpy.run_path(str(BINDING))["build_review"]()
    if binding.get("status") != "CENTRAL_BRAIN_RU01_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED":
        raise ValueError("RU01 exact binding review status drift")
    records = {
        (str(row.get("admission_unit_id")), str(row.get("requirement_id"))): row
        for row in binding.get("records") or []
        if isinstance(row, dict)
    }

    verified_targets: list[dict[str, Any]] = []
    for target in TARGETS:
        unit = target["admission_unit_id"]
        req = target["requirement_id"]
        if unit in accepted_units or req in accepted_reqs:
            raise ValueError(f"sound-changes target already accepted: {unit}/{req}")
        source_row = requirements.get(req)
        if not source_row:
            raise ValueError(f"target requirement missing from RU01 group: {req}")
        for key, expected in (
            ("source_id", target["source_id"]),
            ("document_id", target["document_id"]),
            ("page", target["page"]),
            ("code", target["content_code"]),
            ("source_locator", target["source_locator"]),
        ):
            if source_row.get(key) != expected:
                raise ValueError(f"current source identity drift for {req}: {key}")

        review_row = records.get((unit, req))
        if not review_row:
            raise ValueError(f"binding review target missing: {unit}/{req}")
        for key, expected in (
            ("source_id", target["source_id"]),
            ("document_id", target["document_id"]),
            ("document_sha256", target["document_sha256"]),
            ("page", target["page"]),
            ("code", target["content_code"]),
            ("source_locator", target["source_locator"]),
            ("normalized_source_signature", SIGNATURE),
            ("review_classification", "PENDING"),
            ("blocker_or_reroute", "SOUND_CHANGES_SEMANTIC_REQUIRED"),
        ):
            if review_row.get(key) != expected:
                raise ValueError(f"binding review identity drift for {req}: {key}")
        if review_row.get("accepted_semantic_refs"):
            raise ValueError(f"binding review unexpectedly has accepted refs for {req}")

        verified_targets.append({
            **target,
            "normalized_source_signature": SIGNATURE,
            "binding_review_classification": "PENDING",
            "binding_review_blocker": "SOUND_CHANGES_SEMANTIC_REQUIRED",
        })

    owner_search = scan_exact_current_owner()
    exact_identity = owner_search["proposed_source_derived_identity_exactly_present"]
    source_bound_ids = owner_search["source_bound_accepted_semantic_ids"]
    owner_found = bool(exact_identity or source_bound_ids)

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "scope": "RU01_SOUND_CHANGES_IN_SPEECH_FLOW_EXACT_OWNER_SEARCH",
        "current_launch_progress_v13_normalized_sha256": CURRENT_SHA,
        "targets": verified_targets,
        "exact_current_owner_search": owner_search,
        "decision_boundary": {
            "review_is_semantic_acceptance": False,
            "review_is_object_acceptance": False,
            "object_closure_effect": "NONE",
            "exact_mastery_effect": "NONE",
            "generic_ru01_attempt_can_emit_exact_component_mastery": False,
            "shared_future_evidence_can_close_both_source_objects_without_separate_object_acceptance": False,
            "task_module_route_title_keyword_fuzzy_or_embedding_inference_allowed": False,
            "source_prose_committed": False,
            "false_exact_mastery": 0,
        },
        "current_launch_state": {
            "accepted_authorities": 60,
            "subject_review_units_remaining": 1277,
            "subject_review_requirements_remaining": 1352,
            "accepted_bounded_ru_subject_semantics": 67,
            "false_exact_mastery_admissions": 0,
        },
    }

    if owner_found:
        result["status"] = "CENTRAL_BRAIN_RU01_SOUND_CHANGES_EXACT_OWNER_CANDIDATE_FOUND_BINDING_REQUIRED_NOT_ACCEPTED"
        result["owner_resolution"] = {
            "resolution": "EXACT_CURRENT_OWNER_CANDIDATE_FOUND_REQUIRES_SEPARATE_SOURCE_BINDING",
            "source_derived_identity_exactly_present": exact_identity,
            "source_bound_accepted_semantic_ids": source_bound_ids,
            "new_semantic_candidate_created": False,
            "next_required_gate": "EXACT_SOURCE_BINDING_AND_COMPONENT_SPECIFIC_EVIDENCE_REVIEW",
        }
    else:
        result["status"] = "CENTRAL_BRAIN_RU01_SOUND_CHANGES_NO_EXACT_CURRENT_OWNER_FOUND_SOURCE_BACKED_CANDIDATE_NOT_ACCEPTED"
        result["owner_resolution"] = {
            "resolution": "NO_EXACT_CURRENT_CANONICAL_OWNER_WITH_EXPLICIT_SOURCE_BINDING_FOUND",
            "source_backed_candidate": {
                "candidate_semantic_id": PROPOSED_ID,
                "status": "PROPOSED_NOT_CANONICAL",
                "derivation": "TWO_EXACT_OFFICIAL_SOURCE_OBJECTS_SHARE_CONTENT_CODE_4_1_3_AND_NORMALIZED_SOURCE_SIGNATURE",
                "normalized_source_signature": SIGNATURE,
                "source_object_count": 2,
            },
            "new_semantic_candidate_created": True,
            "next_required_gates": [
                "ORIGINAL_LEARNER_CONTENT",
                "INDEPENDENT_SOUND_CHANGES_SPECIFIC_EVIDENCE",
                "BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE",
                "SEPARATE_EXACT_OBJECT_ACCEPTANCE_PER_SOURCE_OBJECT",
            ],
        }

    no_sha = dict(result)
    result["normalized_sha256"] = hashlib.sha256(canonical_json(no_sha)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    result = build_resolution()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    print("RUSSIAN_RU01_SOUND_CHANGES_EXACT_OWNER_SEARCH=PASS")
    print("STATUS=" + result["status"])
    print("TARGET_OBJECTS=" + str(len(result["targets"])))
    search = result["exact_current_owner_search"]
    print("ACCEPTED_SEMANTIC_IDS_SCANNED=" + str(search["accepted_semantic_ids_scanned"]))
    print("SOURCE_BOUND_ACCEPTED_OWNER_CANDIDATES=" + str(len(search["source_bound_accepted_owner_candidates"])))
    print("SOURCE_DERIVED_IDENTITY_EXACT_PRESENT=" + str(search["proposed_source_derived_identity_exactly_present"]).lower())
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print("NORMALIZED_SHA256=" + result["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
