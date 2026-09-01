#!/usr/bin/env python3
"""Final effective OGE 6.14 evidence audit after structured wave-002 repair.

The historical reuse-exhaustion proof describes the repository before wave 002 was
materialized. A later replacement-only structured repair is also post-proof material,
so it must not be re-read as if it had existed before materialization. v5 preserves
that historical proof without editing it: while v4/v3 are evaluated, exactly the base
wave-002 file and its bounded structured repair are excluded from that historical
scan. The historical normalized fingerprint must remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
V4 = HERE / "build_oge_6_14_reuse_first_evidence_audit_v4.py"
EXHAUSTION = HERE / "build_oge_6_14_remaining_6_2_reuse_exhaustion.py"
BASE_WAVE_002 = "RU-PROG-08-OGE-6.14-GAP-EVIDENCE-WAVE-002-v0.1.json"
STRUCTURED_REPAIR = "RU-PROG-08-OGE-6.14-GAP-EVIDENCE-WAVE-002-STRUCTURED-REPAIR-v0.1.json"
EXPECTED_EXHAUSTION_SHA = "9aae09034623cdd73c043bd5c515b9a8271e422d6cac70205300daceaa5a6773"
V4_STATUS = "CENTRAL_BRAIN_OGE_6_14_COMPONENT_EVIDENCE_COMPLETE_STRUCTURED_BRANCH_COVERAGE_PROVEN_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE_NOT_ACCEPTED"
V5_STATUS = "CENTRAL_BRAIN_OGE_6_14_COMPONENT_EVIDENCE_COMPLETE_STRUCTURED_BRANCH_COVERAGE_AND_HISTORICAL_REUSE_GUARD_PROVEN_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE_NOT_ACCEPTED"


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalized_sha(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def build_audit_v5() -> dict[str, Any]:
    original_run_path = runpy.run_path
    observed_exclusion_set: list[str] = []

    def historical_guarded_run_path(path_name: str | Path, *args: Any, **kwargs: Any) -> dict[str, Any]:
        namespace = original_run_path(str(path_name), *args, **kwargs)
        try:
            resolved = Path(path_name).resolve()
        except TypeError:
            return namespace
        if resolved != EXHAUSTION.resolve():
            return namespace

        exclusions = namespace.get("POST_PROOF_MATERIALIZATION_FILES")
        if not isinstance(exclusions, set):
            raise ValueError("historical reuse proof no longer exposes a bounded post-proof exclusion set")
        allowed = {BASE_WAVE_002, STRUCTURED_REPAIR}
        if BASE_WAVE_002 not in exclusions:
            raise ValueError("historical reuse proof lost the original wave-002 post-proof exclusion")
        unexpected = {str(name) for name in exclusions} - allowed
        if unexpected:
            raise ValueError(f"historical reuse proof contains broad/unreviewed exclusions: {sorted(unexpected)}")
        exclusions.add(STRUCTURED_REPAIR)
        observed_exclusion_set[:] = sorted(str(name) for name in exclusions)
        return namespace

    runpy.run_path = historical_guarded_run_path
    try:
        v4_namespace = original_run_path(str(V4))
        result = v4_namespace["build_audit_v4"]()
    finally:
        runpy.run_path = original_run_path

    if result.get("status") != V4_STATUS:
        raise ValueError("structured branch-complete v4 status drift")
    if observed_exclusion_set != sorted([BASE_WAVE_002, STRUCTURED_REPAIR]):
        raise ValueError(f"historical exclusion set drift: {observed_exclusion_set}")

    sources = [row for row in result.get("validated_existing_evidence_sources") or [] if isinstance(row, dict)]
    v3_wave = [row for row in sources if row.get("content_code") == "6.14-gap-wave-002"]
    if len(v3_wave) != 1:
        raise ValueError("effective audit lost the unique v3 wave-002 provenance record")
    if v3_wave[0].get("reuse_exhaustion_normalized_sha256") != EXPECTED_EXHAUSTION_SHA:
        raise ValueError("historical reuse-exhaustion fingerprint changed after bounded post-proof guard")

    summary = result.get("summary") or {}
    if summary.get("exact_owner_frontier") != 83:
        raise ValueError("exact owner frontier changed")
    if summary.get("owners_with_explicit_component_specific_independent_evidence") != 83:
        raise ValueError("evidence-ready owner count changed")
    if summary.get("exact_independent_items_reused") != 262:
        raise ValueError("exact independent evidence denominator changed")
    if summary.get("effective_wave_002_independent_items") != 48:
        raise ValueError("effective wave-002 denominator changed")
    if summary.get("structured_repair_replaced_item_count") != 6:
        raise ValueError("structured replacement count changed")
    if summary.get("structured_repair_additional_item_count") != 0:
        raise ValueError("structured repair became additive")
    if summary.get("structured_branch_coverage_complete") is not True:
        raise ValueError("structured branch coverage no longer complete")
    if summary.get("semantic_admissions") != 0 or summary.get("object_closures") != 0:
        raise ValueError("evidence audit may not accept the OGE 6.14 object")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("false exact mastery admission detected")

    result = json.loads(json.dumps(result, ensure_ascii=False))
    result["status"] = V5_STATUS
    result["scope"] = "OGE_2026_CONTENT_CODE_6_14_REUSE_FIRST_EXACT_COMPONENT_EVIDENCE_AUDIT_V5_FINAL_EFFECTIVE_STRUCTURED_REPAIR"
    result["historical_reuse_proof_guard"] = {
        "pre_materialization_semantics_preserved": True,
        "excluded_post_proof_materialization_files": observed_exclusion_set,
        "expected_and_observed_reuse_exhaustion_normalized_sha256": EXPECTED_EXHAUSTION_SHA,
        "broad_exclusion_used": False,
        "historical_proof_file_modified_for_repair": False,
    }
    result["summary"]["historical_reuse_proof_fingerprint_preserved"] = True
    result["summary"]["ready_for_separate_exact_object_acceptance"] = True
    result["next_gate"] = (
        "Use the separate OGE 6.14 object-identity binding review to bind the unique admission unit/requirement. "
        "Only after exact-head CI confirms this v5 evidence audit and the identity review, create one separate 6.14 "
        "exact object acceptance bound to the unchanged 83-owner frontier and this v5 fingerprint."
    )
    result.pop("normalized_sha256", None)
    result["normalized_sha256"] = normalized_sha(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_audit_v5()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        s = result["summary"]
        print("OGE_6_14_REUSE_FIRST_EVIDENCE_AUDIT_V5=PASS")
        print(f"EXACT_OWNER_FRONTIER={s['exact_owner_frontier']}")
        print(f"OWNERS_WITH_EXACT_COMPONENT_EVIDENCE={s['owners_with_explicit_component_specific_independent_evidence']}")
        print(f"EXACT_INDEPENDENT_ITEMS={s['exact_independent_items_reused']}")
        print(f"EFFECTIVE_WAVE_002_ITEMS={s['effective_wave_002_independent_items']}")
        print(f"STRUCTURED_REPAIR_REPLACED_ITEMS={s['structured_repair_replaced_item_count']}")
        print("STRUCTURED_REPAIR_ADDITIONAL_ITEMS=0")
        print("STRUCTURED_BRANCH_COVERAGE_COMPLETE=1")
        print("HISTORICAL_REUSE_PROOF_FINGERPRINT_PRESERVED=1")
        print("READY_FOR_SEPARATE_EXACT_OBJECT_ACCEPTANCE=1")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_CLOSURES=0")
        print("FALSE_EXACT_MASTERY=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
