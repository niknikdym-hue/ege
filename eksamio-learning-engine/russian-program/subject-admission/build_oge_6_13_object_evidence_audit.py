#!/usr/bin/env python3
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
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
OWNER_REVIEW = HERE / "build_oge_6_13_compound_words_exact_owner_resolution.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"

TARGET_CODE = "6.13"
TARGET_SOURCE = "FIPI-OGE-RU-2026-FINAL"
TARGET_DOCUMENT = "OGE_COD"
INDEPENDENT_LEARNER_SYSTEMS = {"trainer_item", "practice_item"}
MINIMUM_EXACT_ITEMS_PER_OWNER = 3
EXPECTED_OWNERS = [
    "school-compound-linking-vowel",
    "school-compound-first-part-without-linking-vowel-system",
    "school-compound-noun-solid-hyphen-system",
    "school-compound-adjective-solid-hyphen-separate-system",
    "school-abbreviations-capitalization-formation",
]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def resolve_target() -> dict[str, Any]:
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for group in packet.get("semantic_review_groups") or []:
        if not isinstance(group, dict):
            continue
        for req in group.get("requirements") or []:
            if not isinstance(req, dict):
                continue
            if (
                req.get("source_id") == TARGET_SOURCE
                and req.get("document_id") == TARGET_DOCUMENT
                and str(req.get("code")) == TARGET_CODE
            ):
                matches.append((group, req))
    if len(matches) != 1:
        raise ValueError(f"expected one exact OGE_COD 6.13 requirement, got {len(matches)}")
    group, requirement = matches[0]
    requirement_id = str(requirement.get("requirement_id") or "")
    rows = [
        row for row in accounting.get("dispositions") or []
        if isinstance(row, dict)
        and any(
            isinstance(member, dict) and str(member.get("requirement_id")) == requirement_id
            for member in row.get("members") or []
        )
    ]
    if len(rows) != 1:
        raise ValueError("OGE 6.13 requirement must map to exactly one accounting unit")
    row = rows[0]
    if len(row.get("members") or []) != 1:
        raise ValueError("OGE 6.13 accounting unit must remain single-member before component acceptance")
    if row.get("disposition") != "PARTIAL_OR_COMPOSITE":
        raise ValueError("OGE 6.13 pre-acceptance disposition drift")
    if row.get("semantic_identity_ref") is not None:
        raise ValueError("OGE 6.13 must not already carry a singular semantic identity")
    return {
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "content_code": TARGET_CODE,
        "requirement_id": requirement_id,
        "admission_unit_id": str(row.get("admission_unit_id") or ""),
        "source_locator": str(requirement.get("source_locator") or ""),
        "packet_group": str(group.get("group_id") or ""),
        "normalized_meaning": str(row.get("normalized_meaning") or ""),
        "modules": list(row.get("modules") or []),
        "routes": list(row.get("routes") or []),
        "current_disposition": str(row.get("disposition") or ""),
    }


def build_audit() -> dict[str, Any]:
    inventory = load(INVENTORY)
    resolution = runpy.run_path(str(OWNER_REVIEW))["build_resolution"]()
    target = resolve_target()

    if resolution.get("status") != "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_EVIDENCE_AUDIT_REQUIRED":
        raise ValueError("6.13 exact owner authority is not ready for evidence audit")
    owner_resolution = resolution.get("exact_owner_resolution") or {}
    owners = [str(x) for x in owner_resolution.get("exact_current_canonical_owners") or []]
    if owners != EXPECTED_OWNERS or owner_resolution.get("exact_owner_count") != 5:
        raise ValueError("6.13 exact owner set drift")
    if owner_resolution.get("unresolved_owner_candidates") != 0:
        raise ValueError("6.13 owner frontier remains unresolved")
    if owner_resolution.get("current_inventory_route_already_matches_exact_owner_set") is not True:
        raise ValueError("6.13 current route no longer matches exact owner set")
    if owner_resolution.get("current_route_supersession_required") is not False:
        raise ValueError("6.13 unexpectedly requires route supersession")

    objects = [row for row in inventory.get("objects") or [] if isinstance(row, dict)]
    route_rows = [
        row for row in objects
        if row.get("object_key") == "oge_2026_orthography_route::oge-2026-orthography-6-13"
    ]
    if len(route_rows) != 1:
        raise ValueError("6.13 inventory route missing")
    route_refs = [str(x) for x in route_rows[0].get("current_semantic_refs") or []]
    if len(route_refs) != 5 or set(route_refs) != set(owners):
        raise ValueError("6.13 route refs drift from exact owner set")

    canonical_rows = {
        str(row.get("source_id")): row
        for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and row.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
        and row.get("review_status") == "reviewed"
    }
    if any(owner not in canonical_rows for owner in owners):
        raise ValueError("6.13 exact owner missing current reviewed canonical row")

    linked_by_owner: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in objects:
        refs = [str(ref) for ref in row.get("current_semantic_refs") or []]
        for owner in owners:
            if owner in refs:
                linked_by_owner[owner].append(row)

    owner_reviews: list[dict[str, Any]] = []
    ready_count = 0
    insufficient_count = 0
    mixed_only_count = 0
    none_count = 0
    exact_item_total = 0
    mixed_item_total = 0
    for owner in owners:
        exact_items: list[dict[str, Any]] = []
        mixed_items: list[dict[str, Any]] = []
        for row in linked_by_owner.get(owner, []):
            if row.get("source_system") not in INDEPENDENT_LEARNER_SYSTEMS:
                continue
            if row.get("authority_status") != "current":
                continue
            if row.get("review_status") not in {"reviewed", "source_verified"}:
                continue
            refs = [str(ref) for ref in row.get("current_semantic_refs") or []]
            school_refs = sorted({ref for ref in refs if ref.startswith("school-")})
            item = {
                "source_system": str(row.get("source_system")),
                "source_id": str(row.get("source_id")),
                "review_status": str(row.get("review_status")),
                "school_semantic_refs": school_refs,
                "evidence_provenance_refs": [str(ref) for ref in row.get("evidence_provenance_refs") or []],
            }
            if school_refs == [owner]:
                exact_items.append(item)
            else:
                mixed_items.append(item)
        exact_items.sort(key=lambda x: (x["source_system"], x["source_id"]))
        mixed_items.sort(key=lambda x: (x["source_system"], x["source_id"]))
        exact_item_total += len(exact_items)
        mixed_item_total += len(mixed_items)
        if len(exact_items) >= MINIMUM_EXACT_ITEMS_PER_OWNER:
            status = "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT"
            ready_count += 1
        elif exact_items:
            status = "INSUFFICIENT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE"
            insufficient_count += 1
        elif mixed_items:
            status = "MIXED_SEMANTIC_LEARNER_EVIDENCE_ONLY_NOT_EXACT_ENOUGH"
            mixed_only_count += 1
        else:
            status = "NO_INDEPENDENT_LEARNER_EVIDENCE"
            none_count += 1
        owner_reviews.append({
            "canonical_ref": owner,
            "canonical_label": str(canonical_rows[owner].get("observed_label") or ""),
            "evidence_status": status,
            "minimum_exact_items_required": MINIMUM_EXACT_ITEMS_PER_OWNER,
            "exact_component_independent_item_count": len(exact_items),
            "mixed_semantic_independent_item_count": len(mixed_items),
            "exact_component_independent_items": exact_items,
            "mixed_semantic_independent_items": mixed_items,
        })

    ready = ready_count == len(owners) and insufficient_count == mixed_only_count == none_count == 0
    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "date": "2026-09-01",
        "status": (
            "CENTRAL_BRAIN_OGE_6_13_PREEXISTING_COMPONENT_EVIDENCE_READY_NO_OBJECT_ACCEPTANCE"
            if ready else "CENTRAL_BRAIN_OGE_6_13_COMPONENT_EVIDENCE_GAPS_PROVEN_NO_OBJECT_ACCEPTANCE"
        ),
        "scope": "OGE_2026_CONTENT_CODE_6_13_REUSE_FIRST_PREEXISTING_EVIDENCE_AUDIT",
        "policy": {
            "reuse_first": True,
            "exact_source_content_identity_required": True,
            "keyword_or_fuzzy_inference_allowed": False,
            "module_or_packet_meaning_equivalence_allowed": False,
            "cross_route_reuse_whitelist": {},
            "cross_route_reuse_requires_explicit_item_level_semantic_proof": True,
            "component_specific_independent_evidence_required": True,
            "minimum_exact_independent_items_per_owner": MINIMUM_EXACT_ITEMS_PER_OWNER,
            "mixed_semantic_item_can_prove_exact_component_evidence": False,
            "route_attempt_can_emit_exact_component_mastery": False,
            "evidence_readiness_is_object_acceptance": False,
        },
        "target": target,
        "exact_owner_refs": owners,
        "owner_reviews": owner_reviews,
        "summary": {
            "exact_owner_frontier": len(owners),
            "owners_with_preexisting_exact_component_evidence": ready_count,
            "owners_with_insufficient_exact_evidence": insufficient_count,
            "owners_with_mixed_semantic_evidence_only": mixed_only_count,
            "owners_with_no_independent_evidence": none_count,
            "preexisting_exact_independent_items": exact_item_total,
            "mixed_semantic_independent_items": mixed_item_total,
            "ready_without_materialization": ready,
            "semantic_admissions": 0,
            "object_closures": 0,
            "false_exact_mastery_admissions": 0,
        },
        "safety": {
            "accepted_demo_or_scorer_change": False,
            "tilda_change": False,
            "learner_audio_persistence": 0,
            "production_peis_write": False,
            "provider_execution": False,
            "public_traffic": False,
            "real_payment_or_refund": False,
            "real_message_delivery": False,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_audit()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    s = result["summary"]
    print("OGE_6_13_PREEXISTING_OBJECT_EVIDENCE_AUDIT=PASS")
    print(f"REQUIREMENT_ID={result['target']['requirement_id']}")
    print(f"ADMISSION_UNIT_ID={result['target']['admission_unit_id']}")
    print(f"EXACT_OWNER_FRONTIER={s['exact_owner_frontier']}")
    print(f"OWNERS_WITH_PREEXISTING_EXACT_EVIDENCE={s['owners_with_preexisting_exact_component_evidence']}")
    print(f"OWNERS_WITH_INSUFFICIENT_EXACT_EVIDENCE={s['owners_with_insufficient_exact_evidence']}")
    print(f"OWNERS_WITH_MIXED_ONLY_EVIDENCE={s['owners_with_mixed_semantic_evidence_only']}")
    print(f"OWNERS_WITH_NO_INDEPENDENT_EVIDENCE={s['owners_with_no_independent_evidence']}")
    print(f"PREEXISTING_EXACT_INDEPENDENT_ITEMS={s['preexisting_exact_independent_items']}")
    print(f"READY_WITHOUT_MATERIALIZATION={int(s['ready_without_materialization'])}")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
