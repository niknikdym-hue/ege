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
CURRENT_ROUTE = ENGINE / "279-RUSSIAN-FIPI-2026-OGE-6.7-CURRENT-ROUTE-SUPERSESSION-v0.1.json"
REUSE_COMPONENT_EVIDENCE = (
    ENGINE
    / "russian-program"
    / "production-learning-content"
    / "RU-PROG-08-OGE-6.6-COMPONENT-EVIDENCE-WAVE-001-v0.1.json"
)
REUSE_COMPONENT_VALIDATOR = HERE / "validate_oge_6_6_component_evidence.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"

TARGET_CODE = "6.7"
TARGET_SOURCE = "FIPI-OGE-RU-2026-FINAL"
TARGET_DOCUMENT = "OGE_COD"
INDEPENDENT_LEARNER_SYSTEMS = {"trainer_item", "practice_item"}
MINIMUM_EXACT_ITEMS_PER_OWNER = 3

# Reuse is deliberately narrower than canonical-owner identity. OGE 6.7 tests
# endings only, so suffix-only evidence from the OGE 6.6 pack must not be
# promoted merely because it shares a canonical owner. These IDs were reviewed
# against the current 6.7 source frontier and are the only cross-route items
# permitted by this audit.
ROUTE_SCOPED_REUSE_ITEM_IDS: dict[str, set[str]] = {
    "school-o-e-after-sibilants-suffix-ending": {
        "oge66-shib-v1",  # врачом: stressed noun ending after a sibilant
        "oge66-shib-v2",  # товарищем: unstressed noun ending after a sibilant
    },
    "school-vowels-after-ts-suffix-ending": {
        "oge66-ts-v1",  # бойцом: stressed noun ending after ц
        "oge66-ts-v2",  # пальцем: unstressed noun ending after ц
        "oge66-ts-v3",  # улицы vs цифры: ending/root boundary
    },
}
EXPECTED_REUSE_FEEDBACK = {
    "oge66-shib-v1": "В ударном окончании после ч пишется о: врачом.",
    "oge66-shib-v2": "В безударном окончании после щ пишется е: товарищем.",
    "oge66-ts-v1": "В ударном окончании после ц пишется о: бойцом.",
    "oge66-ts-v2": "В безударном окончании после ц пишется е: пальцем.",
}
EXPECTED_REUSE_CONSTRUCTED_PROMPTS = {
    "oge66-ts-v3": "Сравни «улицы» и «цифры». Почему ы в «улицы» относится к этой семантике, а и в «цифры» — нет?",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def validated_route_scoped_reuse() -> dict[str, list[dict[str, Any]]]:
    pack = load(REUSE_COMPONENT_EVIDENCE)
    validation = runpy.run_path(str(REUSE_COMPONENT_VALIDATOR))["validate"]()
    summary = validation.get("summary") or {}
    if summary.get("exact_owner_frontier") != 10:
        raise ValueError("OGE 6.6 reuse validator owner frontier drift")
    if summary.get("owners_with_valid_component_evidence") != 10:
        raise ValueError("OGE 6.6 reuse evidence pack is not complete")
    if summary.get("minimum_items_per_owner", 0) < 3:
        raise ValueError("OGE 6.6 reuse evidence pack lost its three-item owner floor")
    if summary.get("object_closures") != 0 or summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("OGE 6.6 reuse evidence pack weakened the no-admission boundary")

    rows = pack.get("owner_evidence") or []
    by_owner = {
        str(row.get("canonical_ref")): row
        for row in rows
        if isinstance(row, dict)
    }
    selected: dict[str, list[dict[str, Any]]] = {}
    selected_ids: set[str] = set()
    for owner, allowed_ids in ROUTE_SCOPED_REUSE_ITEM_IDS.items():
        row = by_owner.get(owner)
        if row is None:
            raise ValueError(f"route-scoped reusable owner missing from validated 6.6 pack: {owner}")
        items = [item for item in row.get("independent_verification") or [] if isinstance(item, dict)]
        item_by_id = {str(item.get("id")): item for item in items}
        if not allowed_ids <= set(item_by_id):
            raise ValueError(f"route-scoped reusable item disappeared for {owner}")
        owner_selected: list[dict[str, Any]] = []
        for item_id in sorted(allowed_ids):
            item = item_by_id[item_id]
            if item.get("evidence_mode") != "INDEPENDENT":
                raise ValueError(f"reused evidence is not independent: {item_id}")
            if item.get("school_semantic_refs") != [owner]:
                raise ValueError(f"reused evidence owner drift: {item_id}")
            if item_id in EXPECTED_REUSE_FEEDBACK and item.get("feedback") != EXPECTED_REUSE_FEEDBACK[item_id]:
                raise ValueError(f"reused ending evidence content drift: {item_id}")
            if (
                item_id in EXPECTED_REUSE_CONSTRUCTED_PROMPTS
                and item.get("prompt") != EXPECTED_REUSE_CONSTRUCTED_PROMPTS[item_id]
            ):
                raise ValueError(f"reused ending/root boundary content drift: {item_id}")
            if item_id in selected_ids:
                raise ValueError(f"duplicate reused evidence id: {item_id}")
            selected_ids.add(item_id)
            owner_selected.append(item)
        selected[owner] = owner_selected

    if selected_ids != set().union(*ROUTE_SCOPED_REUSE_ITEM_IDS.values()):
        raise ValueError("route-scoped reuse whitelist accounting drift")
    return selected


def build_audit() -> dict[str, Any]:
    inventory = load(INVENTORY)
    route = load(CURRENT_ROUTE)
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()
    reusable_by_owner = validated_route_scoped_reuse()

    if route.get("status") != "CURRENT_OGE_2026_6_7_ROUTE_SUPERSESSION_EXACT_OWNER_FRONTIER_NO_OBJECT_ADMISSION":
        raise ValueError("OGE 6.7 current route is not the fail-closed exact-owner supersession")
    owners = [str(ref) for ref in route.get("exact_owner_refs") or []]
    if len(owners) != 12 or len(set(owners)) != 12:
        raise ValueError("OGE 6.7 exact owner frontier must contain 12 unique refs")
    if not set(reusable_by_owner) <= set(owners):
        raise ValueError("cross-route reuse escaped the OGE 6.7 owner frontier")
    mastery = route.get("mastery_boundary") or {}
    if mastery.get("route_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("OGE 6.7 route mastery boundary weakened")
    if mastery.get("component_specific_independent_evidence_required") is not True:
        raise ValueError("OGE 6.7 component-specific evidence requirement weakened")

    objects = [row for row in inventory.get("objects") or [] if isinstance(row, dict)]
    canonical_rows = {
        str(row.get("source_id")): row
        for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and row.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
        and row.get("review_status") == "reviewed"
    }
    missing_canonical = [owner for owner in owners if owner not in canonical_rows]
    if missing_canonical:
        raise ValueError("current reviewed canonical owner missing: " + ",".join(missing_canonical))

    packet_matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
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
                packet_matches.append((group, req))
    if len(packet_matches) != 1:
        raise ValueError(f"expected one exact OGE_COD 6.7 requirement, got {len(packet_matches)}")
    group, requirement = packet_matches[0]
    requirement_id = str(requirement["requirement_id"])

    accounting_matches = [
        row
        for row in accounting.get("dispositions") or []
        if isinstance(row, dict)
        and any(
            isinstance(member, dict) and str(member.get("requirement_id")) == requirement_id
            for member in row.get("members") or []
        )
    ]
    if len(accounting_matches) != 1:
        raise ValueError("OGE 6.7 requirement must map to exactly one accounting unit")
    accounting_row = accounting_matches[0]
    if len(accounting_row.get("members") or []) != 1:
        raise ValueError("OGE 6.7 accounting unit must remain single-member during evidence audit")
    if accounting_row.get("semantic_identity_ref") is not None:
        raise ValueError("OGE 6.7 must not already carry a singular semantic identity")

    linked_by_owner: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in objects:
        refs = [str(ref) for ref in row.get("current_semantic_refs") or []]
        for owner in owners:
            if owner in refs:
                linked_by_owner[owner].append(row)

    owner_reviews: list[dict[str, Any]] = []
    exact_ready_count = 0
    insufficient_exact_count = 0
    mixed_only_count = 0
    no_evidence_count = 0
    reused_item_total = 0
    for owner in owners:
        canonical_row = canonical_rows[owner]
        exact_component_items: list[dict[str, Any]] = []
        mixed_component_items: list[dict[str, Any]] = []
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
                exact_component_items.append(item)
            else:
                mixed_component_items.append(item)

        for source_item in reusable_by_owner.get(owner, []):
            item_id = str(source_item["id"])
            exact_component_items.append(
                {
                    "source_system": "reused_original_eksamio_component_evidence",
                    "source_id": item_id,
                    "review_status": "validated_current_launch_route_scoped_reuse",
                    "school_semantic_refs": [owner],
                    "evidence_provenance_refs": [
                        "russian-program/production-learning-content/RU-PROG-08-OGE-6.6-COMPONENT-EVIDENCE-WAVE-001-v0.1.json",
                        "russian-program/subject-admission/validate_oge_6_6_component_evidence.py",
                    ],
                    "reuse_scope": "OGE_2026_6_7_ENDINGS_ONLY",
                }
            )
            reused_item_total += 1

        exact_component_items.sort(key=lambda row: (row["source_system"], row["source_id"]))
        mixed_component_items.sort(key=lambda row: (row["source_system"], row["source_id"]))
        if len(exact_component_items) >= MINIMUM_EXACT_ITEMS_PER_OWNER:
            status = "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT"
            exact_ready_count += 1
        elif exact_component_items:
            status = "INSUFFICIENT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE"
            insufficient_exact_count += 1
        elif mixed_component_items:
            status = "MIXED_SEMANTIC_LEARNER_EVIDENCE_ONLY_NOT_EXACT_ENOUGH"
            mixed_only_count += 1
        else:
            status = "NO_INVENTORIED_INDEPENDENT_LEARNER_EVIDENCE"
            no_evidence_count += 1

        owner_reviews.append({
            "canonical_ref": owner,
            "canonical_label": str(canonical_row.get("observed_label")),
            "canonical_review_status": str(canonical_row.get("review_status")),
            "canonical_evidence_provenance_refs": [str(ref) for ref in canonical_row.get("evidence_provenance_refs") or []],
            "evidence_status": status,
            "minimum_exact_items_required": MINIMUM_EXACT_ITEMS_PER_OWNER,
            "exact_component_independent_item_count": len(exact_component_items),
            "mixed_semantic_independent_item_count": len(mixed_component_items),
            "exact_component_independent_items": exact_component_items,
            "mixed_semantic_independent_items": mixed_component_items,
        })

    ready = (
        exact_ready_count == len(owners)
        and insufficient_exact_count == 0
        and mixed_only_count == 0
        and no_evidence_count == 0
    )
    result: dict[str, Any] = {
        "schema_version": "0.2.0",
        "date": "2026-08-31",
        "status": (
            "CENTRAL_BRAIN_OGE_6_7_INVENTORIED_COMPONENT_EVIDENCE_COMPLETE_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE"
            if ready
            else "CENTRAL_BRAIN_OGE_6_7_COMPONENT_EVIDENCE_GAPS_PROVEN_NO_OBJECT_ACCEPTANCE"
        ),
        "scope": "OGE_2026_CONTENT_CODE_6_7_INVENTORIED_COMPONENT_EVIDENCE_AUDIT",
        "policy": {
            "reuse_first": True,
            "exact_source_content_identity_required": True,
            "keyword_or_fuzzy_inference_allowed": False,
            "module_or_packet_meaning_equivalence_allowed": False,
            "cross_route_reuse_requires_explicit_item_whitelist": True,
            "suffix_only_6_6_item_can_prove_6_7_ending_evidence": False,
            "component_specific_independent_evidence_required": True,
            "minimum_exact_independent_items_per_owner": MINIMUM_EXACT_ITEMS_PER_OWNER,
            "mixed_semantic_item_can_prove_exact_component_evidence": False,
            "route_attempt_can_emit_exact_component_mastery": False,
            "evidence_readiness_is_object_acceptance": False
        },
        "target": {
            "content_code": TARGET_CODE,
            "requirement_id": requirement_id,
            "admission_unit_id": str(accounting_row["admission_unit_id"]),
            "source_locator": str(requirement["source_locator"]),
            "packet_group": str(group["group_id"]),
            "normalized_meaning": str(accounting_row["normalized_meaning"]),
            "modules": list(accounting_row.get("modules") or []),
            "routes": list(accounting_row.get("routes") or []),
            "current_disposition": str(accounting_row["disposition"]),
        },
        "cross_route_reuse": {
            "source_pack": "russian-program/production-learning-content/RU-PROG-08-OGE-6.6-COMPONENT-EVIDENCE-WAVE-001-v0.1.json",
            "source_validator": "russian-program/subject-admission/validate_oge_6_6_component_evidence.py",
            "route_scoped_item_ids": {
                owner: sorted(ids) for owner, ids in sorted(ROUTE_SCOPED_REUSE_ITEM_IDS.items())
            },
            "reused_item_total": reused_item_total,
            "excluded_same_owner_suffix_only_item_ids": ["oge66-shib-v3"],
            "reason": "OGE 6.7 accepts only ending evidence. The suffix-only O/E-after-sibilants item is deliberately excluded even though it shares a canonical owner.",
        },
        "exact_owner_refs": owners,
        "owner_reviews": owner_reviews,
        "summary": {
            "exact_owner_frontier": len(owners),
            "owners_with_explicit_component_specific_independent_evidence": exact_ready_count,
            "owners_with_insufficient_exact_evidence": insufficient_exact_count,
            "owners_with_mixed_semantic_evidence_only": mixed_only_count,
            "owners_with_no_inventoried_independent_evidence": no_evidence_count,
            "reused_route_scoped_independent_items": reused_item_total,
            "ready_for_separate_exact_object_acceptance": ready,
            "semantic_admissions": 0,
            "object_closures": 0,
            "false_exact_mastery_admissions": 0
        },
        "safety": {
            "accepted_demo_or_scorer_change": False,
            "tilda_change": False,
            "learner_audio_persistence": 0,
            "production_peis_write": False,
            "provider_execution": False,
            "public_traffic": False,
            "real_payment_or_refund": False,
            "real_message_delivery": False
        }
    }
    result["normalized_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_audit()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        summary = result["summary"]
        print("OGE_6_7_OBJECT_EVIDENCE_AUDIT=PASS")
        print(f"REQUIREMENT_ID={result['target']['requirement_id']}")
        print(f"ADMISSION_UNIT_ID={result['target']['admission_unit_id']}")
        print(f"EXACT_OWNER_FRONTIER={summary['exact_owner_frontier']}")
        print("OWNERS_WITH_EXACT_COMPONENT_EVIDENCE=" + str(summary["owners_with_explicit_component_specific_independent_evidence"]))
        print("OWNERS_WITH_INSUFFICIENT_EXACT=" + str(summary["owners_with_insufficient_exact_evidence"]))
        print("OWNERS_WITH_MIXED_ONLY=" + str(summary["owners_with_mixed_semantic_evidence_only"]))
        print("OWNERS_WITH_NO_INDEPENDENT_EVIDENCE=" + str(summary["owners_with_no_inventoried_independent_evidence"]))
        print("REUSED_ROUTE_SCOPED_ITEMS=" + str(summary["reused_route_scoped_independent_items"]))
        print("READY_FOR_EXACT_OBJECT_ACCEPTANCE=" + ("1" if summary["ready_for_separate_exact_object_acceptance"] else "0"))
        print("OBJECT_CLOSURES=0")
        print("FALSE_EXACT_MASTERY=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
