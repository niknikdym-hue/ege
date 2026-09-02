#!/usr/bin/env python3
"""OGE 6.14 reuse-first evidence audit v2 after proven-gap wave 001.

The accepted 83-owner frontier is immutable here. This wrapper starts from the
already-green v1 audit, proves its exact 29-owner gap fingerprint, adds only the
13 explicitly materialized single-owner evidence rows from wave 001, and
recomputes evidence readiness. It performs no semantic/object admission.
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
BASE_AUDIT = HERE / "build_oge_6_14_reuse_first_evidence_audit.py"
PACK = ENGINE / "russian-program/production-learning-content/RU-PROG-08-OGE-6.14-GAP-EVIDENCE-WAVE-001-v0.1.json"
VALIDATOR = "russian-program/subject-admission/validate_oge_6_14_gap_evidence_wave_001.py"
EXPECTED_BASE_NORMALIZED_SHA = "762983d941220598a43161bac0cceecc1cc1bc3a5f4b50a16b02057c4761b696"
EXPECTED_WAVE_OWNERS = [
    "school-adverb-final-soft-sign-after-sibilant-base",
    "school-denominal-adjective-n-nn-base",
    "school-i-y-after-prefix-retain-i-boundary",
    "school-i-y-after-prefix-vzimat-exception",
    "school-i-y-after-russian-prefix-base",
    "school-invariable-prefix-spelling-base",
    "school-nn-derived-noun-adverb-inheritance",
    "school-participle-verbal-adjective-n-nn-base",
    "school-pre-pri-lexical-contrast-family",
    "school-pre-pri-semantic-base",
    "school-prefix-z-s-selection",
    "school-separating-hard-soft-sign-boundary",
    "school-verb-soft-sign-forms"
]
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
    "school-zar-zor-stress-alternation"
]
MIN_ITEMS = 3

def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _sha(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()

def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value

def build_audit_v2() -> dict[str, Any]:
    base = runpy.run_path(str(BASE_AUDIT))["build_audit"]()
    if base.get("normalized_sha256") != EXPECTED_BASE_NORMALIZED_SHA:
        raise ValueError("6.14 base audit fingerprint drift; re-review before materializing against a changed gap set")
    if base.get("status") != "CENTRAL_BRAIN_OGE_6_14_REUSE_EVIDENCE_GAPS_PROVEN_NO_OBJECT_ACCEPTANCE":
        raise ValueError("6.14 base audit no longer reports the reviewed materialization gaps")
    if len(base.get("exact_owner_refs") or []) != 83:
        raise ValueError("6.14 exact owner frontier drift")
    if int((base.get("summary") or {}).get("owners_with_explicit_component_specific_independent_evidence", -1)) != 54:
        raise ValueError("6.14 base ready-owner count drift")
    if len(base.get("missing_owner_refs") or []) != 29:
        raise ValueError("6.14 base missing-owner count drift")
    base_missing = set(str(ref) for ref in base["missing_owner_refs"])
    wave_set = set(EXPECTED_WAVE_OWNERS)
    if not wave_set.issubset(base_missing):
        raise ValueError("wave 001 contains an owner that was not a proven v1 gap")
    if sorted(base_missing - wave_set) != EXPECTED_REMAINING:
        raise ValueError("wave 001 no longer leaves exactly the reviewed 6.2 gap set")

    pack = _load(PACK)
    if pack.get("status") != "CURRENT_LAUNCH_OGE_6_14_GAP_EVIDENCE_WAVE_001_NO_OBJECT_ADMISSION":
        raise ValueError("wave 001 pack status drift")
    rows = [row for row in pack.get("owner_evidence") or [] if isinstance(row, dict)]
    if sorted(str(row.get("canonical_ref") or "") for row in rows) != EXPECTED_WAVE_OWNERS:
        raise ValueError("wave 001 owner set drift")

    result = json.loads(json.dumps(base, ensure_ascii=False))
    reviews = {str(row["canonical_ref"]): row for row in result["owner_reviews"]}
    added_items = 0
    for row in rows:
        owner = str(row["canonical_ref"])
        review = reviews[owner]
        if review["evidence_status"] != "NO_INDEPENDENT_LEARNER_EVIDENCE":
            raise ValueError(f"wave owner unexpectedly had reusable evidence before materialization: {owner}")
        if int(review["exact_component_independent_item_count"]) != 0:
            raise ValueError(f"wave owner exact evidence count drift: {owner}")
        items = [item for item in row.get("independent_verification") or [] if isinstance(item, dict)]
        if len(items) != MIN_ITEMS:
            raise ValueError(f"wave owner item count drift: {owner}")
        evidence = []
        for item in items:
            item_id = str(item.get("id") or "")
            if item.get("evidence_mode") != "INDEPENDENT":
                raise ValueError(f"non-independent wave item: {item_id}")
            if item.get("school_semantic_refs") != [owner]:
                raise ValueError(f"mixed/wrong wave item: {item_id}")
            evidence.append({
                "source_kind": "VALIDATED_OGE_6_14_GAP_EVIDENCE_WAVE_001",
                "source_system": "current_launch_original_eksamio_component_evidence",
                "source_id": item_id,
                "review_status": "validated_gap_component_evidence_wave_001",
                "school_semantic_refs": [owner],
                "evidence_provenance_refs": [
                    str(PACK.relative_to(ENGINE)),
                    VALIDATOR,
                ],
                "source_oge_code": str(row["source_oge_code"]),
            })
            added_items += 1
        review["evidence_status"] = "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT"
        review["exact_component_independent_item_count"] = len(evidence)
        review["exact_component_independent_items"] = evidence

    ready = 0
    insufficient = 0
    mixed_only = 0
    none = 0
    exact_total = 0
    mixed_total = 0
    missing = []
    for ref in result["exact_owner_refs"]:
        row = reviews[str(ref)]
        exact_count = int(row["exact_component_independent_item_count"])
        mixed_count = int(row["mixed_semantic_independent_item_count"])
        exact_total += exact_count
        mixed_total += mixed_count
        if exact_count >= MIN_ITEMS:
            row["evidence_status"] = "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT"
            ready += 1
        elif exact_count:
            row["evidence_status"] = "INSUFFICIENT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE"
            insufficient += 1
            missing.append(str(ref))
        elif mixed_count:
            row["evidence_status"] = "MIXED_SEMANTIC_LEARNER_EVIDENCE_ONLY_NOT_EXACT_ENOUGH"
            mixed_only += 1
            missing.append(str(ref))
        else:
            row["evidence_status"] = "NO_INDEPENDENT_LEARNER_EVIDENCE"
            none += 1
            missing.append(str(ref))
    if missing != EXPECTED_REMAINING:
        raise ValueError("post-wave missing frontier is not the exact reviewed 6.2 set")
    if added_items != 39:
        raise ValueError("wave 001 added-item count drift")

    result["status"] = "CENTRAL_BRAIN_OGE_6_14_REUSE_EVIDENCE_GAPS_PROVEN_AFTER_WAVE_001_NO_OBJECT_ACCEPTANCE"
    result["scope"] = "OGE_2026_CONTENT_CODE_6_14_REUSE_FIRST_EXACT_COMPONENT_EVIDENCE_AUDIT_V2"
    result["validated_existing_evidence_sources"].append({
        "content_code": "6.14-gap-wave-001",
        "pack": str(PACK.relative_to(ENGINE)),
        "validator": VALIDATOR,
        "exact_owner_count": len(EXPECTED_WAVE_OWNERS),
        "independent_item_count": added_items,
        "base_audit_normalized_sha256": EXPECTED_BASE_NORMALIZED_SHA,
    })
    result["missing_owner_refs"] = missing
    result["summary"] = {
        "exact_owner_frontier": 83,
        "owners_with_explicit_component_specific_independent_evidence": ready,
        "owners_with_insufficient_exact_evidence": insufficient,
        "owners_with_mixed_semantic_evidence_only": mixed_only,
        "owners_with_no_independent_evidence": none,
        "exact_independent_items_reused": exact_total,
        "mixed_semantic_independent_items_not_counted_as_exact": mixed_total,
        "ready_without_new_materialization": False,
        "materialized_new_items_this_audit": 0,
        "materialized_gap_items_reused_from_wave_001": added_items,
        "semantic_admissions": 0,
        "object_closures": 0,
        "false_exact_mastery_admissions": 0,
    }
    if ready != 67 or none != 16 or insufficient != 0 or mixed_only != 0:
        raise ValueError("post-wave readiness accounting drift")
    if exact_total != 214 or mixed_total != 0:
        raise ValueError("post-wave exact/mixed item accounting drift")
    result["next_gate"] = (
        "Materialize original Eksamio evidence only for the remaining 16 proven OGE 6.2 gaps, "
        "minimum three independent single-owner items per ref; then rerun a new audit. "
        "Do not accept 6.14 or change its 83-owner frontier before all 83 owners are evidence-ready."
    )
    result.pop("normalized_sha256", None)
    result["normalized_sha256"] = _sha(result)
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_audit_v2()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        s = result["summary"]
        print("OGE_6_14_REUSE_FIRST_EVIDENCE_AUDIT_V2=PASS")
        print(f"EXACT_OWNER_FRONTIER={s['exact_owner_frontier']}")
        print(f"OWNERS_WITH_EXACT_COMPONENT_EVIDENCE={s['owners_with_explicit_component_specific_independent_evidence']}")
        print(f"OWNERS_WITH_NO_INDEPENDENT_EVIDENCE={s['owners_with_no_independent_evidence']}")
        print(f"MISSING_OWNER_REFS={len(result['missing_owner_refs'])}")
        print(f"EXACT_INDEPENDENT_ITEMS={s['exact_independent_items_reused']}")
        print(f"WAVE_001_ITEMS_REUSED={s['materialized_gap_items_reused_from_wave_001']}")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_CLOSURES=0")
        print("FALSE_EXACT_MASTERY=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
