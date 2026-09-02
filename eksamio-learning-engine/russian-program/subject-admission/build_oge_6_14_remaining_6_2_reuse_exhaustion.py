#!/usr/bin/env python3
"""Prove reuse exhaustion for the 16 remaining OGE 6.14 evidence gaps.

This is a fail-closed audit, not learner-content materialization.  It proves that
all post-wave-001 gaps are exactly the already accepted OGE 6.2 owner set and
that no current reviewed inventory item, validated production evidence byte, or
embedded 6.2 acceptance payload supplies single-owner independent evidence for
those refs.  Only after this proof may a later bounded wave create new original
Eksamio evidence for the 16 gaps.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any, Iterator

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
AUDIT_V2 = HERE / "build_oge_6_14_reuse_first_evidence_audit_v2.py"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
ACCEPTANCE_6_2 = HERE / "RUSSIAN-OGE-6.2-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
CONTENT_DIR = ENGINE / "russian-program/production-learning-content"
POST_PROOF_MATERIALIZATION_FILES = {
    "RU-PROG-08-OGE-6.14-GAP-EVIDENCE-WAVE-002-v0.1.json",
    "RU-PROG-08-OGE-6.14-GAP-EVIDENCE-WAVE-002-STRUCTURED-REPAIR-v0.1.json",
}
MIN_ITEMS = 3
EXPECTED_6_2_ACCEPTANCE_SHA = "ef5cf03c7df2b2b4b327e040c62ef07707dc6ba772e7bf3cc1961564669554f4"
EXPECTED_REMAINING = [
    "school-double-consonants-morpheme-junction",
    "school-gor-gar-rare-exception-set",
    "school-i-e-alternating-verb-roots-stressed-a",
    "school-kas-kos-a-suffix-alternation",
    "school-klan-klon-stress-alternation",
    "school-lag-lozh-polog-exception",
    "school-rast-rashch-ros-exception-set",
    "school-root-consonant-dictionary-unverifiable",
    "school-root-i-y-after-ts-base",
    "school-root-o-yo-after-sibilants-base",
    "school-root-voiced-voiceless-consonant-verification",
    "school-root-vowel-dictionary-unverifiable",
    "school-root-vowel-stress-verification",
    "school-skak-skoch-exception-set",
    "school-unpronounceable-consonant-verification",
    "school-zar-zor-stress-alternation",
]
INDEPENDENT_LEARNER_SYSTEMS = {"trainer_item", "practice_item"}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _walk(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def build_reuse_exhaustion() -> dict[str, Any]:
    v2 = runpy.run_path(str(AUDIT_V2))["build_audit_v2"]()
    if v2.get("status") != "CENTRAL_BRAIN_OGE_6_14_REUSE_EVIDENCE_GAPS_PROVEN_AFTER_WAVE_001_NO_OBJECT_ACCEPTANCE":
        raise ValueError("OGE 6.14 v2 audit is not at the reviewed post-wave gap state")
    if len(v2.get("exact_owner_refs") or []) != 83:
        raise ValueError("OGE 6.14 exact owner frontier drift")
    summary = v2.get("summary") or {}
    if int(summary.get("owners_with_explicit_component_specific_independent_evidence", -1)) != 67:
        raise ValueError("OGE 6.14 post-wave ready count drift")
    if int(summary.get("exact_independent_items_reused", -1)) != 214:
        raise ValueError("OGE 6.14 post-wave exact evidence count drift")
    missing = [str(ref) for ref in v2.get("missing_owner_refs") or []]
    if missing != EXPECTED_REMAINING:
        raise ValueError("remaining OGE 6.14 gap set drift")

    reviews = {str(row.get("canonical_ref")): row for row in v2.get("owner_reviews") or [] if isinstance(row, dict)}
    for owner in EXPECTED_REMAINING:
        row = reviews.get(owner)
        if not row:
            raise ValueError(f"missing v2 owner review: {owner}")
        if row.get("source_oge_codes") != ["6.2"]:
            raise ValueError(f"remaining gap is not exclusively sourced from OGE 6.2: {owner}")
        if row.get("evidence_status") != "NO_INDEPENDENT_LEARNER_EVIDENCE":
            raise ValueError(f"remaining gap unexpectedly has evidence: {owner}")
        if int(row.get("exact_component_independent_item_count", -1)) != 0:
            raise ValueError(f"remaining gap exact evidence count drift: {owner}")
        if int(row.get("mixed_semantic_independent_item_count", -1)) != 0:
            raise ValueError(f"remaining gap mixed evidence must remain zero before materialization: {owner}")

    accepted_6_2 = _load(ACCEPTANCE_6_2)
    if accepted_6_2.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_2_CANONICAL_COMPONENT_SET":
        raise ValueError("OGE 6.2 exact semantic acceptance status drift")
    if accepted_6_2.get("normalized_sha256") != EXPECTED_6_2_ACCEPTANCE_SHA:
        raise ValueError("OGE 6.2 exact semantic acceptance fingerprint drift")
    decisions = [row for row in accepted_6_2.get("decisions") or [] if isinstance(row, dict)]
    if len(decisions) != 1:
        raise ValueError("OGE 6.2 exact semantic acceptance must contain one decision")
    decision = decisions[0]
    if decision.get("content_code") != "6.2" or int(decision.get("component_count", -1)) != 16:
        raise ValueError("OGE 6.2 accepted owner accounting drift")
    if sorted(str(ref) for ref in decision.get("canonical_component_refs") or []) != EXPECTED_REMAINING:
        raise ValueError("OGE 6.2 accepted exact owner set no longer equals the remaining 6.14 gaps")
    boundary = decision.get("mastery_boundary") or {}
    if boundary.get("component_specific_independent_evidence_required") is not True:
        raise ValueError("OGE 6.2 component-specific evidence requirement weakened")
    if boundary.get("route_or_broad_composite_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("OGE 6.2 false-mastery boundary weakened")
    embedded_evidence_keys = sorted({
        key
        for obj in _walk(accepted_6_2)
        for key in obj
        if key in {"owner_evidence", "independent_verification", "exact_component_independent_items"}
    })
    if embedded_evidence_keys:
        raise ValueError(f"OGE 6.2 acceptance now embeds evidence and must be reuse-reviewed: {embedded_evidence_keys}")

    inventory = _load(INVENTORY)
    missing_set = set(EXPECTED_REMAINING)
    inventory_exact_hits: dict[str, list[str]] = {owner: [] for owner in EXPECTED_REMAINING}
    inventory_mixed_hits: dict[str, list[str]] = {owner: [] for owner in EXPECTED_REMAINING}
    for row in inventory.get("objects") or []:
        if not isinstance(row, dict) or row.get("source_system") not in INDEPENDENT_LEARNER_SYSTEMS:
            continue
        if row.get("authority_status") != "current" or row.get("review_status") not in {"reviewed", "source_verified"}:
            continue
        school_refs = sorted({str(ref) for ref in row.get("current_semantic_refs") or [] if str(ref).startswith("school-")})
        linked = missing_set.intersection(school_refs)
        if not linked:
            continue
        source_id = str(row.get("source_id") or "")
        if len(school_refs) == 1:
            inventory_exact_hits[school_refs[0]].append(source_id)
        else:
            for owner in linked:
                inventory_mixed_hits[owner].append(source_id)
    if any(inventory_exact_hits.values()) or any(inventory_mixed_hits.values()):
        raise ValueError("current reviewed inventory now contains reusable evidence for a remaining gap")

    production_hits: dict[str, list[str]] = {owner: [] for owner in EXPECTED_REMAINING}
    scanned_json_files = 0
    for path in sorted(CONTENT_DIR.glob("*.json")):
        if path.name in POST_PROOF_MATERIALIZATION_FILES:
            continue
        scanned_json_files += 1
        doc = _load(path)
        for obj in _walk(doc):
            if obj.get("evidence_mode") != "INDEPENDENT":
                continue
            refs = [str(ref) for ref in obj.get("school_semantic_refs") or []]
            if len(refs) != 1 or refs[0] not in missing_set:
                continue
            item_id = str(obj.get("id") or obj.get("source_id") or "")
            production_hits[refs[0]].append(f"{path.name}#{item_id}")
    if any(production_hits.values()):
        raise ValueError("production learning content now contains reusable exact evidence for a remaining gap")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "date": "2026-09-02",
        "status": "CENTRAL_BRAIN_OGE_6_14_REMAINING_6_2_REUSE_EXHAUSTED_MATERIALIZATION_REQUIRED_NO_OBJECT_ACCEPTANCE",
        "scope": "OGE_2026_6_14_REMAINING_6_2_EXACT_EVIDENCE_REUSE_EXHAUSTION",
        "policy": {
            "reuse_first": True,
            "exact_source_identity_required": True,
            "keyword_or_fuzzy_reuse_allowed": False,
            "new_semantic_identity_allowed_here": False,
            "exact_owner_frontier_may_change_here": False,
            "evidence_materialization_allowed_here": False,
            "object_acceptance_allowed_here": False,
            "route_attempt_can_emit_exact_component_mastery": False,
        },
        "post_wave_state": {
            "exact_owner_frontier": 83,
            "evidence_ready_owners": 67,
            "exact_independent_items": 214,
            "remaining_owner_count": 16,
            "remaining_owner_refs": EXPECTED_REMAINING,
            "remaining_source_content_codes": ["6.2"],
        },
        "reuse_search": {
            "accepted_6_2_semantic_authority": str(ACCEPTANCE_6_2.relative_to(ENGINE)),
            "accepted_6_2_normalized_sha256": EXPECTED_6_2_ACCEPTANCE_SHA,
            "accepted_6_2_embedded_learner_evidence_keys": embedded_evidence_keys,
            "current_reviewed_inventory_exact_hits": inventory_exact_hits,
            "current_reviewed_inventory_mixed_hits": inventory_mixed_hits,
            "production_learning_content_json_files_scanned": scanned_json_files,
            "production_exact_independent_hits": production_hits,
            "reusable_exact_items_found": 0,
            "reusable_mixed_items_found": 0,
        },
        "materialization_floor": {
            "owners_requiring_new_original_eksamio_evidence": 16,
            "minimum_independent_single_owner_items_per_owner": MIN_ITEMS,
            "minimum_new_items_required": 16 * MIN_ITEMS,
        },
        "summary": {
            "reuse_exhausted_for_all_remaining_owners": True,
            "semantic_admissions": 0,
            "object_closures": 0,
            "false_exact_mastery_admissions": 0,
            "new_school_identities": 0,
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
            "Materialize one bounded original-Eksamio OGE 6.14 evidence wave for exactly these 16 accepted OGE 6.2 owners, "
            "minimum three independent single-owner items per owner. Pin each row to the existing 6.2 exact semantic authority; "
            "do not change the 83-owner frontier and do not accept 6.14 until a post-materialization audit proves all 83 owners evidence-ready."
        ),
    }
    result["normalized_sha256"] = _sha(result)
    return result


def build_review() -> dict[str, Any]:
    """Compatibility alias for downstream final-evidence gates."""
    return build_reuse_exhaustion()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_reuse_exhaustion()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("OGE_6_14_REMAINING_6_2_REUSE_EXHAUSTION=PASS")
        print("EXACT_OWNER_FRONTIER=83")
        print("EVIDENCE_READY_OWNERS=67")
        print("REMAINING_6_2_GAPS=16")
        print("REUSABLE_EXACT_ITEMS_FOUND=0")
        print("MINIMUM_NEW_ORIGINAL_ITEMS_REQUIRED=48")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_CLOSURES=0")
        print("FALSE_EXACT_MASTERY=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
