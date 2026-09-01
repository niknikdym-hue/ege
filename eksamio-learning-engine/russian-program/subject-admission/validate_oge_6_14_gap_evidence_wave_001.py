#!/usr/bin/env python3
"""Fail-closed validator for OGE 6.14 proven-gap evidence wave 001."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
PACK = ENGINE / "russian-program/production-learning-content/RU-PROG-08-OGE-6.14-GAP-EVIDENCE-WAVE-001-v0.1.json"
EXPECTED_BY_CODE = {
    "6.3": [
        "school-invariable-prefix-spelling-base",
        "school-pre-pri-lexical-contrast-family",
        "school-pre-pri-semantic-base",
        "school-prefix-z-s-selection",
    ],
    "6.4": [
        "school-adverb-final-soft-sign-after-sibilant-base",
        "school-separating-hard-soft-sign-boundary",
        "school-verb-soft-sign-forms",
    ],
    "6.5": [
        "school-i-y-after-prefix-retain-i-boundary",
        "school-i-y-after-prefix-vzimat-exception",
        "school-i-y-after-russian-prefix-base",
    ],
    "6.10": [
        "school-denominal-adjective-n-nn-base",
        "school-nn-derived-noun-adverb-inheritance",
        "school-participle-verbal-adjective-n-nn-base",
    ],
}
EXPECTED_OWNERS = sorted(ref for refs in EXPECTED_BY_CODE.values() for ref in refs)
EXPECTED_AUTHORITY_SHA = "c9b40069b7d2f8bb692cfa4e3b1e5ae21fd785e23542d8f6e74b391b0a8674dc"
EXPECTED_BASE_AUDIT_SHA = "762983d941220598a43161bac0cceecc1cc1bc3a5f4b50a16b02057c4761b696"
MIN_ITEMS = 3


def main() -> int:
    d = json.loads(PACK.read_text(encoding="utf-8"))
    assert d["schema_version"] == "0.1.0"
    assert d["status"] == "CURRENT_LAUNCH_OGE_6_14_GAP_EVIDENCE_WAVE_001_NO_OBJECT_ADMISSION"
    target = d["target"]
    assert target == {
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "document_id": "OGE_COD",
        "content_code": "6.14",
        "label_ru": "Орфографический анализ",
        "classification": "EXAM_ONLY_COMPOSITE",
    }

    policy = d["evidence_policy"]
    assert policy["base_reuse_audit_normalized_sha256"] == EXPECTED_BASE_AUDIT_SHA
    assert policy["base_exact_owner_frontier"] == 83
    assert policy["base_evidence_ready_owners"] == 54
    assert policy["base_missing_owners"] == 29
    assert policy["materialize_only_proven_missing_owner_refs"] is True
    assert policy["wave_owner_count"] == len(EXPECTED_OWNERS) == 13
    assert policy["minimum_independent_items_per_owner"] == MIN_ITEMS
    assert policy["each_item_must_reference_exactly_one_school_semantic"] is True
    assert policy["new_semantic_identity_created"] is False
    assert policy["exact_owner_frontier_may_change_here"] is False
    assert policy["route_attempt_can_emit_exact_component_mastery"] is False
    assert policy["evidence_readiness_is_object_acceptance"] is False
    assert policy["cross_route_fuzzy_reuse_used"] is False
    assert policy["mastery_guard"] == {
        "minimum_independent_items_required": 3,
        "component_specific_only": True,
        "generic_oge_route_result_can_emit_exact_mastery": False,
        "assisted_attempt_can_count_as_independent_evidence": False,
    }

    authorities = d["source_exact_authorities"]
    assert set(authorities) == set(EXPECTED_BY_CODE)
    for code, authority in authorities.items():
        assert authority["accepted_authority_id"] == "RUSSIAN_OGE_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"
        assert authority["accepted_authority_sha256"] == EXPECTED_AUTHORITY_SHA
        assert authority["requirement_id"].startswith(f"RSK-OGE_COD-{code.replace(chr(46), chr(45))}-")
        assert authority["admission_unit_id"].startswith("RAU-")

    rows = d["owner_evidence"]
    owners = [row["canonical_ref"] for row in rows]
    assert sorted(owners) == EXPECTED_OWNERS
    assert len(owners) == len(set(owners)) == 13

    all_ids: list[str] = []
    for row in rows:
        owner = row["canonical_ref"]
        code = row["source_oge_code"]
        assert owner in EXPECTED_BY_CODE[code]
        assert row["evidence_status"] == "CURRENT_LAUNCH_ORIGINAL_EKSAMIO_COMPONENT_EVIDENCE"
        assert len(row["title_ru"].strip()) >= 10
        assert len(row["semantic_boundary"].strip()) >= 40

        items = row["independent_verification"]
        assert len(items) == MIN_ITEMS
        types = {item.get("type") for item in items}
        # Pedagogical acceptance: recognition alone is insufficient. Every exact
        # owner must have at least one selected-response item and one item where
        # the learner independently states/applies the rule boundary.
        assert "single_choice" in types, f"selected-response evidence missing: {owner}"
        assert "constructed_response" in types, f"constructed-response evidence missing: {owner}"

        for item in items:
            iid = item["id"]
            all_ids.append(iid)
            assert iid.startswith("oge614-w1-")
            assert item["evidence_mode"] == "INDEPENDENT"
            assert item["school_semantic_refs"] == [owner]
            assert len(item["prompt"].strip()) >= 15

            if item["type"] == "single_choice":
                options = item["options"]
                idx = item["correct_option_index"]
                assert len(options) == 3
                assert len(set(options)) == 3
                assert 0 <= idx < len(options)
                assert len(item["feedback"].strip()) >= 15
            elif item["type"] == "constructed_response":
                assert len(item["answer_outline"].strip()) >= 25
                scoring = item["scoring"]
                assert scoring["max_points"] == 2
                criteria = scoring["criteria"]
                assert len(criteria) == 2
                assert all(isinstance(c, str) and len(c.strip()) >= 20 for c in criteria)
            else:
                raise AssertionError(f"unsupported evidence type: {item['type']}")

    assert len(all_ids) == 39
    assert len(all_ids) == len(set(all_ids))

    rights = d["copyright_and_source_guard"]
    assert rights["learner_wording"] == "ORIGINAL_EKSAMIO"
    assert rights["official_source_passages_copied"] is False
    assert rights["commercial_textbook_bytes_used"] is False

    s = d["summary"]
    assert s["wave_owner_count"] == 13
    assert s["materialized_new_independent_items"] == 39
    assert s["remaining_missing_owner_refs_after_wave_if_valid"] == 16
    assert s["semantic_admissions"] == 0
    assert s["object_closures"] == 0
    assert s["false_exact_mastery_admissions"] == 0
    assert s["new_school_identities"] == 0

    safety = d["safety"]
    assert safety["accepted_demo_or_scorer_change"] is False
    assert safety["tilda_change"] is False
    assert safety["learner_audio_persistence"] == 0
    assert safety["production_peis_write"] is False
    assert safety["provider_execution"] is False
    assert safety["public_traffic"] is False
    assert safety["real_payment_or_refund"] is False
    assert safety["real_message_delivery"] is False

    print("OGE_6_14_GAP_WAVE_001_OWNER_COUNT=13")
    print("OGE_6_14_GAP_WAVE_001_INDEPENDENT_ITEMS=39")
    print("OGE_6_14_GAP_WAVE_001_RESPONSE_MODE_PER_OWNER=SELECTED_PLUS_CONSTRUCTED")
    print("OGE_6_14_GAP_WAVE_001_SEMANTIC_ADMISSIONS=0")
    print("OGE_6_14_GAP_WAVE_001_OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print("RUSSIAN_OGE_6_14_GAP_EVIDENCE_WAVE_001_GUARD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
