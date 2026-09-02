#!/usr/bin/env python3
"""Reuse-first learner-evidence audit for the derived OGE-2026 6.14 frontier.

This audit never invents or admits a 6.14 owner.  It starts from the exact 83-ref
projection produced by build_oge_6_14_current_exact_component_derivation.py and
counts only independent learner items that are bound to exactly one canonical
school ref.  It reuses both current reviewed inventory items and already
materialized bounded component-evidence waves.  Missing evidence remains a
materialization gap; this file itself creates no learner content and closes no
object.
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
ENGINE = HERE.parents[1]
DERIVATION = HERE / "build_oge_6_14_current_exact_component_derivation.py"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
CURRENT_6_7_AUDIT = HERE / "build_oge_6_7_current_evidence_audit_v3.py"
MINIMUM_EXACT_ITEMS_PER_OWNER = 3
INDEPENDENT_LEARNER_SYSTEMS = {"trainer_item", "practice_item"}

PACK_SPECS = (
    (
        "6.6",
        ENGINE / "russian-program/production-learning-content/RU-PROG-08-OGE-6.6-COMPONENT-EVIDENCE-WAVE-001-v0.1.json",
        "russian-program/subject-admission/validate_oge_6_6_component_evidence.py",
    ),
    (
        "6.8",
        ENGINE / "russian-program/production-learning-content/RU-PROG-08-OGE-6.8-COMPONENT-EVIDENCE-WAVE-001-v0.1.json",
        "russian-program/subject-admission/validate_oge_6_8_component_evidence.py",
    ),
    (
        "6.9",
        ENGINE / "russian-program/production-learning-content/RU-PROG-08-OGE-6.9-COMPONENT-EVIDENCE-WAVE-001-v0.1.json",
        "russian-program/subject-admission/validate_oge_6_9_component_evidence.py",
    ),
    (
        "6.11",
        ENGINE / "russian-program/production-learning-content/RU-PROG-08-OGE-6.11-COMPONENT-EVIDENCE-WAVE-001-v0.1.json",
        "russian-program/subject-admission/validate_oge_6_11_component_evidence.py",
    ),
    (
        "6.12",
        ENGINE / "russian-program/production-learning-content/RU-PROG-08-OGE-6.12-COMPONENT-EVIDENCE-WAVE-001-v0.1.json",
        "russian-program/subject-admission/validate_oge_6_12_component_evidence.py",
    ),
    (
        "6.13",
        ENGINE / "russian-program/production-learning-content/RU-PROG-08-OGE-6.13-COMPONENT-EVIDENCE-WAVE-001-v0.1.json",
        "russian-program/subject-admission/validate_oge_6_13_component_evidence.py",
    ),
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _normalized_sha(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _add_exact(
    exact: dict[str, dict[str, dict[str, Any]]],
    owner: str,
    item_id: str,
    item: dict[str, Any],
) -> None:
    if not item_id:
        raise ValueError(f"evidence item missing id for {owner}")
    exact[owner].setdefault(item_id, item)


def build_audit() -> dict[str, Any]:
    derivation = runpy.run_path(str(DERIVATION))["build_derivation"]()
    if derivation.get("status") != "CURRENT_EXACT_COMPONENT_SET_DERIVED_REUSE_EVIDENCE_AUDIT_REQUIRED":
        raise ValueError("6.14 exact component derivation is not ready for evidence audit")
    d = derivation.get("derivation") or {}
    owners = [str(ref) for ref in d.get("applicable_component_refs") or []]
    if len(owners) != 83 or len(set(owners)) != 83:
        raise ValueError("6.14 derived exact owner denominator drift")
    owner_set = set(owners)
    source_sets = {
        str(row.get("content_code")): [str(ref) for ref in row.get("canonical_component_refs") or []]
        for row in d.get("source_component_sets") or []
        if isinstance(row, dict)
    }
    if set(source_sets) != {f"6.{i}" for i in range(2, 14)}:
        raise ValueError("6.14 source-code component projection incomplete")

    inventory = _load(INVENTORY)
    objects = [row for row in inventory.get("objects") or [] if isinstance(row, dict)]
    exact: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    mixed: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)

    # First reuse current reviewed/source-verified independent learner inventory.
    for row in objects:
        if row.get("source_system") not in INDEPENDENT_LEARNER_SYSTEMS:
            continue
        if row.get("authority_status") != "current":
            continue
        if row.get("review_status") not in {"reviewed", "source_verified"}:
            continue
        refs = [str(ref) for ref in row.get("current_semantic_refs") or []]
        school_refs = sorted({ref for ref in refs if ref.startswith("school-")})
        linked_owners = owner_set.intersection(school_refs)
        if not linked_owners:
            continue
        item_id = str(row.get("source_id") or "")
        item = {
            "source_kind": "CURRENT_REVIEWED_INVENTORY",
            "source_system": str(row.get("source_system")),
            "source_id": item_id,
            "review_status": str(row.get("review_status")),
            "school_semantic_refs": school_refs,
            "evidence_provenance_refs": [str(ref) for ref in row.get("evidence_provenance_refs") or []],
        }
        if len(school_refs) == 1 and school_refs[0] in owner_set:
            _add_exact(exact, school_refs[0], item_id, item)
        else:
            for owner in linked_owners:
                if item_id:
                    mixed[owner].setdefault(item_id, item)

    # Reuse already materialized exact single-owner evidence packs.  The packs are
    # bounded to previously accepted exact OGE component sets; they are not new
    # 6.14 content and are never counted as a 6.14 admission here.
    validated_pack_sources: list[dict[str, Any]] = []
    for code, pack_path, validator_path in PACK_SPECS:
        pack = _load(pack_path)
        rows = [row for row in pack.get("owner_evidence") or [] if isinstance(row, dict)]
        pack_owners = [str(row.get("canonical_ref") or "") for row in rows]
        if not rows or len(pack_owners) != len(set(pack_owners)):
            raise ValueError(f"{code} evidence pack has missing/duplicate owner rows")
        if set(pack_owners) != set(source_sets[code]):
            raise ValueError(f"{code} evidence pack no longer equals its accepted exact component set")
        pack_item_count = 0
        for row in rows:
            owner = str(row.get("canonical_ref") or "")
            items = [item for item in row.get("independent_verification") or [] if isinstance(item, dict)]
            if len(items) < MINIMUM_EXACT_ITEMS_PER_OWNER:
                raise ValueError(f"{code} evidence pack owner below exact item floor: {owner}")
            for item in items:
                item_id = str(item.get("id") or "")
                if item.get("evidence_mode") != "INDEPENDENT":
                    raise ValueError(f"{code} non-independent materialized evidence: {item_id}")
                if item.get("school_semantic_refs") != [owner]:
                    raise ValueError(f"{code} mixed/wrong semantic evidence: {item_id}")
                _add_exact(
                    exact,
                    owner,
                    item_id,
                    {
                        "source_kind": "VALIDATED_CURRENT_COMPONENT_EVIDENCE_PACK",
                        "source_system": "current_launch_original_eksamio_component_evidence",
                        "source_id": item_id,
                        "review_status": "validated_component_evidence",
                        "school_semantic_refs": [owner],
                        "evidence_provenance_refs": [
                            str(pack_path.relative_to(ENGINE)),
                            validator_path,
                        ],
                        "source_oge_code": code,
                    },
                )
                pack_item_count += 1
        summary = pack.get("summary") or {}
        if int(summary.get("semantic_admissions", 0)) != 0 or int(summary.get("object_closures", 0)) != 0:
            raise ValueError(f"{code} evidence pack already claims a forbidden admission")
        if int(summary.get("false_exact_mastery_admissions", 0)) != 0:
            raise ValueError(f"{code} evidence pack false-mastery guard weakened")
        validated_pack_sources.append(
            {
                "content_code": code,
                "pack": str(pack_path.relative_to(ENGINE)),
                "validator": validator_path,
                "exact_owner_count": len(pack_owners),
                "independent_item_count": pack_item_count,
            }
        )

    # OGE 6.7 evidence spans three bounded waves plus explicit item-level reuse;
    # consume its already fail-closed current audit rather than reconstructing it.
    audit_6_7 = runpy.run_path(str(CURRENT_6_7_AUDIT))["build_current_audit_v3"]()
    if audit_6_7.get("status") != "CENTRAL_BRAIN_OGE_6_7_COMPONENT_EVIDENCE_COMPLETE_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE_NOT_ACCEPTED":
        raise ValueError("6.7 current exact evidence audit drift")
    rows_6_7 = [row for row in audit_6_7.get("owner_reviews") or [] if isinstance(row, dict)]
    if {str(row.get("canonical_ref")) for row in rows_6_7} != set(source_sets["6.7"]):
        raise ValueError("6.7 current evidence owner set no longer equals exact accepted components")
    for row in rows_6_7:
        owner = str(row.get("canonical_ref"))
        if row.get("evidence_status") != "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT":
            raise ValueError(f"6.7 owner is not evidence-ready: {owner}")
        items = [item for item in row.get("exact_component_independent_items") or [] if isinstance(item, dict)]
        if len(items) < MINIMUM_EXACT_ITEMS_PER_OWNER:
            raise ValueError(f"6.7 owner below exact item floor: {owner}")
        for item in items:
            item_id = str(item.get("source_id") or "")
            if item.get("school_semantic_refs") != [owner]:
                raise ValueError(f"6.7 current audit contains mixed exact evidence: {item_id}")
            _add_exact(
                exact,
                owner,
                item_id,
                {
                    "source_kind": "VALIDATED_OGE_6_7_CURRENT_EVIDENCE_AUDIT",
                    "source_system": str(item.get("source_system") or ""),
                    "source_id": item_id,
                    "review_status": str(item.get("review_status") or ""),
                    "school_semantic_refs": [owner],
                    "evidence_provenance_refs": [str(ref) for ref in item.get("evidence_provenance_refs") or []],
                    "source_oge_code": "6.7",
                },
            )

    owner_reviews: list[dict[str, Any]] = []
    ready_count = 0
    insufficient_count = 0
    mixed_only_count = 0
    none_count = 0
    exact_total = 0
    mixed_total = 0
    for owner in owners:
        exact_items = sorted(exact.get(owner, {}).values(), key=lambda item: (item["source_kind"], item["source_id"]))
        mixed_items = sorted(mixed.get(owner, {}).values(), key=lambda item: (item["source_system"], item["source_id"]))
        exact_count = len(exact_items)
        mixed_count = len(mixed_items)
        exact_total += exact_count
        mixed_total += mixed_count
        if exact_count >= MINIMUM_EXACT_ITEMS_PER_OWNER:
            status = "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT"
            ready_count += 1
        elif exact_count:
            status = "INSUFFICIENT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE"
            insufficient_count += 1
        elif mixed_count:
            status = "MIXED_SEMANTIC_LEARNER_EVIDENCE_ONLY_NOT_EXACT_ENOUGH"
            mixed_only_count += 1
        else:
            status = "NO_INDEPENDENT_LEARNER_EVIDENCE"
            none_count += 1
        owner_reviews.append(
            {
                "canonical_ref": owner,
                "source_oge_codes": sorted(
                    [code for code, refs in source_sets.items() if owner in refs],
                    key=lambda code: int(code.split(".")[1]),
                ),
                "evidence_status": status,
                "minimum_exact_items_required": MINIMUM_EXACT_ITEMS_PER_OWNER,
                "exact_component_independent_item_count": exact_count,
                "mixed_semantic_independent_item_count": mixed_count,
                "exact_component_independent_items": exact_items,
                "mixed_semantic_independent_items": mixed_items,
            }
        )

    missing_owner_refs = [
        row["canonical_ref"]
        for row in owner_reviews
        if row["evidence_status"] != "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT"
    ]
    ready = not missing_owner_refs
    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "date": "2026-09-02",
        "status": (
            "CENTRAL_BRAIN_OGE_6_14_REUSE_EVIDENCE_READY_NO_OBJECT_ACCEPTANCE"
            if ready
            else "CENTRAL_BRAIN_OGE_6_14_REUSE_EVIDENCE_GAPS_PROVEN_NO_OBJECT_ACCEPTANCE"
        ),
        "scope": "OGE_2026_CONTENT_CODE_6_14_REUSE_FIRST_EXACT_COMPONENT_EVIDENCE_AUDIT",
        "policy": {
            "reuse_first": True,
            "exact_component_frontier_source": "current accepted exact OGE orthography authorities only",
            "exact_source_content_identity_required": True,
            "keyword_or_fuzzy_inference_allowed": False,
            "module_or_packet_meaning_equivalence_allowed": False,
            "component_specific_independent_evidence_required": True,
            "minimum_exact_independent_items_per_owner": MINIMUM_EXACT_ITEMS_PER_OWNER,
            "mixed_semantic_item_can_prove_exact_component_evidence": False,
            "route_attempt_can_emit_exact_component_mastery": False,
            "evidence_readiness_is_object_acceptance": False,
            "materialize_only_proven_gaps_after_this_audit": True,
        },
        "derivation_normalized_sha256": str(derivation.get("normalized_sha256", "")),
        "exact_owner_refs": owners,
        "validated_existing_evidence_sources": validated_pack_sources + [
            {
                "content_code": "6.7",
                "audit": str(CURRENT_6_7_AUDIT.relative_to(ENGINE)),
                "exact_owner_count": len(rows_6_7),
                "ready_for_separate_object_acceptance": True,
            }
        ],
        "owner_reviews": owner_reviews,
        "missing_owner_refs": missing_owner_refs,
        "summary": {
            "exact_owner_frontier": len(owners),
            "owners_with_explicit_component_specific_independent_evidence": ready_count,
            "owners_with_insufficient_exact_evidence": insufficient_count,
            "owners_with_mixed_semantic_evidence_only": mixed_only_count,
            "owners_with_no_independent_evidence": none_count,
            "exact_independent_items_reused": exact_total,
            "mixed_semantic_independent_items_not_counted_as_exact": mixed_total,
            "ready_without_new_materialization": ready,
            "materialized_new_items_this_audit": 0,
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
        "next_gate": (
            "If missing_owner_refs is non-empty, materialize original Eksamio evidence only for those proven gaps, "
            "minimum three independent single-owner items per missing ref, then rerun this audit. If it is empty, "
            "proceed to a separate 6.14 exact object acceptance without changing the 83-ref frontier."
        ),
    }
    result["normalized_sha256"] = _normalized_sha(result)
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
        s = result["summary"]
        print("OGE_6_14_REUSE_FIRST_EVIDENCE_AUDIT=PASS")
        print(f"EXACT_OWNER_FRONTIER={s['exact_owner_frontier']}")
        print(f"OWNERS_WITH_EXACT_COMPONENT_EVIDENCE={s['owners_with_explicit_component_specific_independent_evidence']}")
        print(f"OWNERS_WITH_INSUFFICIENT_EXACT={s['owners_with_insufficient_exact_evidence']}")
        print(f"OWNERS_WITH_MIXED_ONLY={s['owners_with_mixed_semantic_evidence_only']}")
        print(f"OWNERS_WITH_NO_INDEPENDENT_EVIDENCE={s['owners_with_no_independent_evidence']}")
        print(f"MISSING_OWNER_REFS={len(result['missing_owner_refs'])}")
        print(f"READY_WITHOUT_NEW_MATERIALIZATION={int(s['ready_without_new_materialization'])}")
        print("NEW_ITEMS_MATERIALIZED_BY_AUDIT=0")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_CLOSURES=0")
        print("FALSE_EXACT_MASTERY=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
