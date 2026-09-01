#!/usr/bin/env python3
"""OGE 6.14 reuse-first evidence audit v3 after final OGE 6.2 wave.

This is evidence completion only. The accepted 83-ref component frontier is
immutable here and no OGE 6.14 object/component-set admission is made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
BASE_V2 = HERE / "build_oge_6_14_reuse_first_evidence_audit_v2.py"
REUSE_EXHAUSTION = HERE / "build_oge_6_14_remaining_6_2_reuse_exhaustion.py"
PACK = ENGINE / "russian-program/production-learning-content/RU-PROG-08-OGE-6.14-GAP-EVIDENCE-WAVE-002-v0.1.json"
VALIDATOR = "russian-program/subject-admission/validate_oge_6_14_gap_evidence_wave_002.py"
EXPECTED_V2_SHA = "abf91f61ae203d6a8c918536271e1eeabcf99de63fb07ef0355b8732ea6e954c"
EXPECTED_EXHAUSTION_SHA = "9aae09034623cdd73c043bd5c515b9a8271e422d6cac70205300daceaa5a6773"
EXPECTED_WAVE_OWNERS = [
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
MIN_ITEMS = 3


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def build_audit_v3() -> dict[str, Any]:
    base = runpy.run_path(str(BASE_V2))["build_audit_v2"]()
    if base.get("normalized_sha256") != EXPECTED_V2_SHA:
        raise ValueError("accepted v2 evidence audit fingerprint drift")
    if base.get("status") != "CENTRAL_BRAIN_OGE_6_14_REUSE_EVIDENCE_GAPS_PROVEN_AFTER_WAVE_001_NO_OBJECT_ACCEPTANCE":
        raise ValueError("v2 audit no longer exposes the accepted post-wave-001 state")
    if len(base.get("exact_owner_refs") or []) != 83:
        raise ValueError("6.14 exact owner frontier drift")
    summary = base.get("summary") or {}
    if summary.get("owners_with_explicit_component_specific_independent_evidence") != 67:
        raise ValueError("v2 ready-owner count drift")
    if summary.get("exact_independent_items_reused") != 214:
        raise ValueError("v2 exact item denominator drift")
    if base.get("missing_owner_refs") != EXPECTED_WAVE_OWNERS:
        raise ValueError("v2 missing frontier is no longer the exact reviewed 6.2 set")

    exhaustion = runpy.run_path(str(REUSE_EXHAUSTION))["build_review"]()
    if exhaustion.get("normalized_sha256") != EXPECTED_EXHAUSTION_SHA:
        raise ValueError("6.2 reuse-exhaustion fingerprint drift")
    if exhaustion.get("summary", {}).get("reuse_exhausted_for_all_remaining_owners") is not True:
        raise ValueError("6.2 reuse is no longer exhausted")
    if exhaustion.get("reuse_search", {}).get("reusable_exact_items_found") != 0:
        raise ValueError("new reusable exact 6.2 evidence appeared; wave 002 requires re-review")

    pack = load(PACK)
    if pack.get("status") != "CURRENT_LAUNCH_OGE_6_14_GAP_EVIDENCE_WAVE_002_NO_OBJECT_ADMISSION":
        raise ValueError("wave 002 pack status drift")
    rows = [row for row in pack.get("owner_evidence") or [] if isinstance(row, dict)]
    if [str(row.get("canonical_ref") or "") for row in rows] != EXPECTED_WAVE_OWNERS:
        raise ValueError("wave 002 owner order/set drift")

    result = json.loads(json.dumps(base, ensure_ascii=False))
    reviews = {str(row["canonical_ref"]): row for row in result["owner_reviews"]}
    added = 0
    for row in rows:
        owner = str(row["canonical_ref"])
        review = reviews[owner]
        if review.get("evidence_status") != "NO_INDEPENDENT_LEARNER_EVIDENCE":
            raise ValueError(f"wave 002 owner unexpectedly had prior evidence: {owner}")
        if int(review.get("exact_component_independent_item_count") or 0) != 0:
            raise ValueError(f"wave 002 owner exact evidence count drift: {owner}")
        items = [item for item in row.get("independent_verification") or [] if isinstance(item, dict)]
        if len(items) != MIN_ITEMS:
            raise ValueError(f"wave 002 owner item count drift: {owner}")
        types = {str(item.get("type")) for item in items}
        if not {"single_choice", "constructed_response"}.issubset(types):
            raise ValueError(f"wave 002 owner lacks selected+constructed modes: {owner}")
        evidence = []
        for item in items:
            item_id = str(item.get("id") or "")
            if item.get("evidence_mode") != "INDEPENDENT":
                raise ValueError(f"non-independent wave 002 item: {item_id}")
            if item.get("school_semantic_refs") != [owner]:
                raise ValueError(f"mixed/wrong wave 002 item: {item_id}")
            evidence.append({
                "source_kind": "VALIDATED_OGE_6_14_GAP_EVIDENCE_WAVE_002",
                "source_system": "current_launch_original_eksamio_component_evidence",
                "source_id": item_id,
                "review_status": "validated_gap_component_evidence_wave_002",
                "school_semantic_refs": [owner],
                "evidence_provenance_refs": [str(PACK.relative_to(ENGINE)), VALIDATOR],
                "source_oge_code": "6.2",
            })
            added += 1
        review["evidence_status"] = "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT"
        review["exact_component_independent_item_count"] = len(evidence)
        review["exact_component_independent_items"] = evidence

    ready = 0
    insufficient = 0
    mixed_only = 0
    none = 0
    exact_total = 0
    mixed_total = 0
    missing: list[str] = []
    for ref in result["exact_owner_refs"]:
        review = reviews[str(ref)]
        exact_count = int(review.get("exact_component_independent_item_count") or 0)
        mixed_count = int(review.get("mixed_semantic_independent_item_count") or 0)
        exact_total += exact_count
        mixed_total += mixed_count
        if exact_count >= MIN_ITEMS:
            review["evidence_status"] = "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT"
            ready += 1
        elif exact_count:
            review["evidence_status"] = "INSUFFICIENT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE"
            insufficient += 1
            missing.append(str(ref))
        elif mixed_count:
            review["evidence_status"] = "MIXED_SEMANTIC_LEARNER_EVIDENCE_ONLY_NOT_EXACT_ENOUGH"
            mixed_only += 1
            missing.append(str(ref))
        else:
            review["evidence_status"] = "NO_INDEPENDENT_LEARNER_EVIDENCE"
            none += 1
            missing.append(str(ref))

    if added != 48:
        raise ValueError("wave 002 added-item count drift")
    if ready != 83 or insufficient != 0 or mixed_only != 0 or none != 0 or missing:
        raise ValueError("post-wave-002 evidence readiness is not complete 83/83")
    if exact_total != 262 or mixed_total != 0:
        raise ValueError("post-wave-002 exact/mixed item accounting drift")

    result["status"] = "CENTRAL_BRAIN_OGE_6_14_COMPONENT_EVIDENCE_COMPLETE_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE_NOT_ACCEPTED"
    result["scope"] = "OGE_2026_CONTENT_CODE_6_14_REUSE_FIRST_EXACT_COMPONENT_EVIDENCE_AUDIT_V3"
    result["validated_existing_evidence_sources"].append({
        "content_code": "6.14-gap-wave-002",
        "pack": str(PACK.relative_to(ENGINE)),
        "validator": VALIDATOR,
        "exact_owner_count": 16,
        "independent_item_count": 48,
        "v2_audit_normalized_sha256": EXPECTED_V2_SHA,
        "reuse_exhaustion_normalized_sha256": EXPECTED_EXHAUSTION_SHA,
    })
    result["missing_owner_refs"] = []
    result["summary"] = {
        "exact_owner_frontier": 83,
        "owners_with_explicit_component_specific_independent_evidence": 83,
        "owners_with_insufficient_exact_evidence": 0,
        "owners_with_mixed_semantic_evidence_only": 0,
        "owners_with_no_independent_evidence": 0,
        "exact_independent_items_reused": 262,
        "mixed_semantic_independent_items_not_counted_as_exact": 0,
        "ready_without_new_materialization": True,
        "ready_for_separate_exact_object_acceptance": True,
        "materialized_new_items_this_audit": 0,
        "materialized_gap_items_reused_from_wave_001": 39,
        "materialized_gap_items_reused_from_wave_002": 48,
        "semantic_admissions": 0,
        "object_closures": 0,
        "false_exact_mastery_admissions": 0,
    }
    result["next_gate"] = (
        "Central Brain subject-review wave 002, then create a separate OGE 6.14 exact object acceptance "
        "bound to this unchanged 83-ref frontier and evidence-complete v3 audit. Do not count or merge here."
    )
    result.pop("normalized_sha256", None)
    result["normalized_sha256"] = sha(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_audit_v3()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        s = result["summary"]
        print("OGE_6_14_REUSE_FIRST_EVIDENCE_AUDIT_V3=PASS")
        print(f"EXACT_OWNER_FRONTIER={s['exact_owner_frontier']}")
        print(f"OWNERS_WITH_EXACT_COMPONENT_EVIDENCE={s['owners_with_explicit_component_specific_independent_evidence']}")
        print(f"OWNERS_WITH_NO_INDEPENDENT_EVIDENCE={s['owners_with_no_independent_evidence']}")
        print(f"MISSING_OWNER_REFS={len(result['missing_owner_refs'])}")
        print(f"EXACT_INDEPENDENT_ITEMS={s['exact_independent_items_reused']}")
        print(f"WAVE_001_ITEMS_REUSED={s['materialized_gap_items_reused_from_wave_001']}")
        print(f"WAVE_002_ITEMS_REUSED={s['materialized_gap_items_reused_from_wave_002']}")
        print("READY_FOR_SEPARATE_EXACT_OBJECT_ACCEPTANCE=1")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_CLOSURES=0")
        print("FALSE_EXACT_MASTERY=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
