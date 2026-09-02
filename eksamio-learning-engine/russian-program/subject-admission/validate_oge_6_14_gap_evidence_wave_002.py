#!/usr/bin/env python3
"""Fail-closed validator for final OGE 6.14 / OGE 6.2 gap evidence wave."""
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
PACK = ENGINE / "russian-program/production-learning-content/RU-PROG-08-OGE-6.14-GAP-EVIDENCE-WAVE-002-v0.1.json"
AUTHORITY = HERE / "RUSSIAN-OGE-6.2-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
V2_AUDIT = HERE / "build_oge_6_14_reuse_first_evidence_audit_v2.py"
REUSE_EXHAUSTION = HERE / "build_oge_6_14_remaining_6_2_reuse_exhaustion.py"

EXPECTED_OWNERS = sorted([
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
])
EXPECTED_AUTHORITY_SHA = "ef5cf03c7df2b2b4b327e040c62ef07707dc6ba772e7bf3cc1961564669554f4"
EXPECTED_V2_SHA = "abf91f61ae203d6a8c918536271e1eeabcf99de63fb07ef0355b8732ea6e954c"
EXPECTED_EXHAUSTION_SHA = "9aae09034623cdd73c043bd5c515b9a8271e422d6cac70205300daceaa5a6773"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def main() -> int:
    d = load(PACK)
    authority = load(AUTHORITY)
    v2 = runpy.run_path(str(V2_AUDIT))["build_audit_v2"]()
    exhaustion = runpy.run_path(str(REUSE_EXHAUSTION))["build_reuse_exhaustion"]()

    assert authority["status"] == "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_2_CANONICAL_COMPONENT_SET"
    assert authority["normalized_sha256"] == EXPECTED_AUTHORITY_SHA
    decisions = authority["decisions"]
    assert len(decisions) == 1
    assert decisions[0]["content_code"] == "6.2"
    assert sorted(decisions[0]["canonical_component_refs"]) == EXPECTED_OWNERS
    assert decisions[0]["component_count"] == 16

    assert v2["normalized_sha256"] == EXPECTED_V2_SHA
    assert v2["summary"]["exact_owner_frontier"] == 83
    assert v2["summary"]["owners_with_explicit_component_specific_independent_evidence"] == 67
    assert v2["summary"]["owners_with_no_independent_evidence"] == 16
    assert sorted(v2["missing_owner_refs"]) == EXPECTED_OWNERS

    assert exhaustion["normalized_sha256"] == EXPECTED_EXHAUSTION_SHA
    assert exhaustion["summary"]["reuse_exhausted_for_all_remaining_owners"] is True
    assert exhaustion["reuse_search"]["reusable_exact_items_found"] == 0
    assert exhaustion["reuse_search"]["reusable_mixed_items_found"] == 0
    assert exhaustion["materialization_floor"]["owners_requiring_new_original_eksamio_evidence"] == 16
    assert exhaustion["materialization_floor"]["minimum_new_items_required"] == 48

    assert d["schema_version"] == "0.1.0"
    assert d["status"] == "CURRENT_LAUNCH_OGE_6_14_GAP_EVIDENCE_WAVE_002_NO_OBJECT_ADMISSION"
    assert d["module_id"] == "RU-PROG-08"
    assert d["target"] == {
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "document_id": "OGE_COD",
        "content_code": "6.14",
        "source_component_code": "6.2",
        "label_ru": "Орфографический анализ",
        "classification": "EXAM_ONLY_COMPOSITE",
    }
    assert d["source_exact_authority"] == {
        "accepted_authority_id": "RUSSIAN_OGE_6_2_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
        "accepted_authority_sha256": EXPECTED_AUTHORITY_SHA,
        "admission_unit_id": "RAU-085b9955399af22c784f",
        "requirement_id": "RSK-OGE_COD-6-2-P024",
    }

    p = d["evidence_policy"]
    assert p["accepted_wave_001_post_audit_normalized_sha256"] == EXPECTED_V2_SHA
    assert p["reuse_exhaustion_normalized_sha256"] == EXPECTED_EXHAUSTION_SHA
    assert p["base_exact_owner_frontier"] == 83
    assert p["base_evidence_ready_owners"] == 67
    assert p["base_missing_owners"] == 16
    assert p["reusable_exact_items_found"] == 0
    assert p["materialize_only_proven_missing_owner_refs"] is True
    assert p["wave_owner_count"] == 16
    assert p["minimum_independent_items_per_owner"] == 3
    assert p["each_item_must_reference_exactly_one_school_semantic"] is True
    assert p["each_owner_requires_selected_and_constructed_response"] is True
    assert p["new_semantic_identity_created"] is False
    assert p["exact_owner_frontier_may_change_here"] is False
    assert p["route_attempt_can_emit_exact_component_mastery"] is False
    assert p["evidence_readiness_is_object_acceptance"] is False
    assert p["keyword_or_fuzzy_reuse_used"] is False
    assert p["mastery_guard"] == {
        "minimum_independent_items_required": 3,
        "component_specific_only": True,
        "generic_oge_route_result_can_emit_exact_mastery": False,
        "assisted_attempt_can_count_as_independent_evidence": False,
    }

    rows = d["owner_evidence"]
    assert len(rows) == 16
    refs = [str(row["canonical_ref"]) for row in rows]
    assert sorted(refs) == EXPECTED_OWNERS
    assert len(set(refs)) == 16

    item_ids: list[str] = []
    for row in rows:
        owner = str(row["canonical_ref"])
        assert row["source_oge_code"] == "6.2"
        assert row["evidence_status"] == "CURRENT_LAUNCH_ORIGINAL_EKSAMIO_COMPONENT_EVIDENCE"
        assert len(str(row["title_ru"]).strip()) >= 10
        assert len(str(row["semantic_boundary"]).strip()) >= 50
        items = row["independent_verification"]
        assert len(items) == 3
        types = {str(item.get("type")) for item in items}
        assert "single_choice" in types, f"selected response missing: {owner}"
        assert "constructed_response" in types, f"constructed response missing: {owner}"
        for item in items:
            iid = str(item["id"])
            item_ids.append(iid)
            assert iid.startswith("oge614-w2-")
            assert item["evidence_mode"] == "INDEPENDENT"
            assert item["school_semantic_refs"] == [owner]
            assert len(str(item["prompt"]).strip()) >= 15
            if item["type"] == "single_choice":
                opts = item["options"]
                idx = item["correct_option_index"]
                assert len(opts) == 3 and len(set(opts)) == 3
                assert isinstance(idx, int) and 0 <= idx < 3
                assert len(str(item["feedback"]).strip()) >= 20
            elif item["type"] == "constructed_response":
                assert len(str(item["answer_outline"]).strip()) >= 40
                scoring = item["scoring"]
                assert scoring["max_points"] == 2
                criteria = scoring["criteria"]
                assert len(criteria) == 2
                assert all(isinstance(c, str) and len(c.strip()) >= 25 for c in criteria)
            else:
                raise AssertionError(f"unsupported item type: {item['type']}")

    assert len(item_ids) == 48
    assert len(set(item_ids)) == 48

    rights = d["copyright_and_source_guard"]
    assert rights["learner_wording"] == "ORIGINAL_EKSAMIO"
    assert rights["official_source_passages_copied"] is False
    assert rights["commercial_textbook_bytes_used"] is False
    assert rights["commercial_textbook_prose_copied"] is False

    summary = d["summary"]
    assert summary == {
        "wave_owner_count": 16,
        "materialized_new_independent_items": 48,
        "remaining_missing_owner_refs_after_wave_if_valid": 0,
        "semantic_admissions": 0,
        "object_closures": 0,
        "false_exact_mastery_admissions": 0,
        "new_school_identities": 0,
    }
    safety = d["safety"]
    assert safety == {
        "accepted_demo_or_scorer_change": False,
        "tilda_change": False,
        "learner_audio_persistence": 0,
        "production_peis_write": False,
        "provider_execution": False,
        "public_traffic": False,
        "real_payment_or_refund": False,
        "real_message_delivery": False,
    }

    print("OGE_6_14_GAP_WAVE_002_OWNER_COUNT=16")
    print("OGE_6_14_GAP_WAVE_002_INDEPENDENT_ITEMS=48")
    print("OGE_6_14_GAP_WAVE_002_RESPONSE_MODE_PER_OWNER=SELECTED_PLUS_CONSTRUCTED")
    print("OGE_6_14_GAP_WAVE_002_REUSE_EXHAUSTED=1")
    print("OGE_6_14_GAP_WAVE_002_SEMANTIC_ADMISSIONS=0")
    print("OGE_6_14_GAP_WAVE_002_OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print("RUSSIAN_OGE_6_14_GAP_EVIDENCE_WAVE_002_GUARD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
