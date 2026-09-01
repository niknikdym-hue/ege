#!/usr/bin/env python3
"""Fail-closed validator for the final effective OGE 6.14 wave-002 repair."""
from __future__ import annotations

import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILDER = HERE / "build_oge_6_14_reuse_first_evidence_audit_v5.py"
DOUBLE_OWNER = "school-double-consonants-morpheme-junction"
IE_OWNER = "school-i-e-alternating-verb-roots-stressed-a"
EXPECTED_BRANCH_COUNTS = {DOUBLE_OWNER: 3, IE_OWNER: 10}
EXPECTED_STATUS = (
    "CENTRAL_BRAIN_OGE_6_14_COMPONENT_EVIDENCE_COMPLETE_STRUCTURED_BRANCH_COVERAGE_AND_"
    "HISTORICAL_REUSE_GUARD_PROVEN_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE_NOT_ACCEPTED"
)


def main() -> int:
    result = runpy.run_path(str(BUILDER))["build_audit_v5"]()
    assert result["status"] == EXPECTED_STATUS
    assert len(result["exact_owner_refs"]) == 83
    assert len(set(result["exact_owner_refs"])) == 83
    assert result["missing_owner_refs"] == []

    summary = result["summary"]
    assert summary["exact_owner_frontier"] == 83
    assert summary["owners_with_explicit_component_specific_independent_evidence"] == 83
    assert summary["owners_with_no_independent_evidence"] == 0
    assert summary["exact_independent_items_reused"] == 262
    assert summary["effective_wave_002_owner_count"] == 16
    assert summary["effective_wave_002_independent_items"] == 48
    assert summary["structured_repair_owner_count"] == 2
    assert summary["structured_repair_replaced_item_count"] == 6
    assert summary["structured_repair_additional_item_count"] == 0
    assert summary["structured_branch_coverage_complete"] is True
    assert summary["historical_reuse_proof_fingerprint_preserved"] is True
    assert summary["ready_for_separate_exact_object_acceptance"] is True
    assert summary["semantic_admissions"] == 0
    assert summary["object_closures"] == 0
    assert summary["false_exact_mastery_admissions"] == 0

    guard = result["historical_reuse_proof_guard"]
    assert guard["pre_materialization_semantics_preserved"] is True
    assert guard["excluded_post_proof_materialization_files"] == [
        "RU-PROG-08-OGE-6.14-GAP-EVIDENCE-WAVE-002-STRUCTURED-REPAIR-v0.1.json",
        "RU-PROG-08-OGE-6.14-GAP-EVIDENCE-WAVE-002-v0.1.json",
    ]
    assert guard["expected_and_observed_reuse_exhaustion_normalized_sha256"] == "9aae09034623cdd73c043bd5c515b9a8271e422d6cac70205300daceaa5a6773"
    assert guard["broad_exclusion_used"] is False
    assert guard["historical_proof_file_modified_for_repair"] is False

    reviews = {
        str(row["canonical_ref"]): row
        for row in result["owner_reviews"]
        if row.get("canonical_ref") in EXPECTED_BRANCH_COUNTS
    }
    assert set(reviews) == set(EXPECTED_BRANCH_COUNTS)
    replacement_ids: list[str] = []
    superseded_ids: list[str] = []
    for owner, expected_count in EXPECTED_BRANCH_COUNTS.items():
        row = reviews[owner]
        assert row["evidence_status"] == "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT_STRUCTURED_BRANCH_COMPLETE"
        assert len(row["required_branch_ids"]) == expected_count
        assert set(row["required_branch_ids"]) == set(row["covered_branch_ids"])
        assert row["exact_component_independent_item_count"] == 3
        exact_items = row["exact_component_independent_items"]
        assert len(exact_items) == 3
        assert all(item["source_kind"] == "VALIDATED_OGE_6_14_WAVE_002_STRUCTURED_REPLACEMENT_EVIDENCE" for item in exact_items)
        assert all(item["school_semantic_refs"] == [owner] for item in exact_items)
        replacement_ids.extend(str(item["source_id"]) for item in exact_items)
        superseded_ids.extend(str(item_id) for item_id in row["structured_repair_superseded_source_ids"])

    assert len(replacement_ids) == 6 and len(set(replacement_ids)) == 6
    assert len(superseded_ids) == 6 and len(set(superseded_ids)) == 6
    assert set(replacement_ids).isdisjoint(superseded_ids)

    safety = result["safety"]
    assert safety["accepted_demo_or_scorer_change"] is False
    assert safety["tilda_change"] is False
    assert safety["learner_audio_persistence"] == 0
    assert safety["production_peis_write"] is False
    assert safety["provider_execution"] is False
    assert safety["public_traffic"] is False
    assert safety["real_payment_or_refund"] is False
    assert safety["real_message_delivery"] is False

    print("OGE_6_14_WAVE_002_STRUCTURED_REPAIR=PASS")
    print("EXACT_OWNER_FRONTIER=83")
    print("EVIDENCE_READY_OWNERS=83")
    print("EFFECTIVE_WAVE_002_ITEMS=48")
    print("STRUCTURED_REPLACED_ITEMS=6")
    print("STRUCTURED_ADDITIONAL_ITEMS=0")
    print("STRUCTURED_BRANCH_COVERAGE_COMPLETE=1")
    print("HISTORICAL_REUSE_PROOF_FINGERPRINT_PRESERVED=1")
    print("READY_FOR_SEPARATE_EXACT_OBJECT_ACCEPTANCE=1")
    print("OGE_6_14_OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
