#!/usr/bin/env python3
"""Validate the OGE-2026 6.2 pre-materialization exact-owner manifest.

This gate proves the complete prospective exact owner set and that current authority
is still fail-closed. It performs no admission and applies no denominator change.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2]
ADMISSION = Path(__file__).resolve().parent
MANIFEST = ADMISSION / "RUSSIAN-OGE-6.2-ATOMIC-MATERIALIZATION-MANIFEST-v0.1.json"
IMPACT = ADMISSION / "RUSSIAN-OGE-6.2-SCHOOL-REOPEN-AUTHORITY-IMPACT-AUDIT-v0.1.json"
OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
EXACT = ADMISSION / "RUSSIAN-OGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
NEW_OWNER = "school-root-consonant-dictionary-unverifiable"
LEGACY = {
    "alternating-root families from file 248",
    "double-consonant root systems from file 249",
}
REUSED = {
    "school-root-vowel-stress-verification",
    "school-root-vowel-dictionary-unverifiable",
    "school-root-o-yo-after-sibilants-base",
    "school-root-i-y-after-ts-base",
    "school-root-voiced-voiceless-consonant-verification",
    "school-unpronounceable-consonant-verification",
    "school-gor-gar-rare-exception-set",
    "school-i-e-alternating-verb-roots-stressed-a",
    "school-kas-kos-a-suffix-alternation",
    "school-klan-klon-stress-alternation",
    "school-lag-lozh-polog-exception",
    "school-rast-rashch-ros-exception-set",
    "school-skak-skoch-exception-set",
    "school-zar-zor-stress-alternation",
    "school-double-consonants-morpheme-junction",
}
EXPLICIT_CURRENT = {
    "school-root-vowel-stress-verification",
    "school-root-vowel-dictionary-unverifiable",
    "school-root-o-yo-after-sibilants-base",
    "school-root-i-y-after-ts-base",
    "school-root-voiced-voiceless-consonant-verification",
    "school-unpronounceable-consonant-verification",
}
ALTERNATING = {
    "school-gor-gar-rare-exception-set",
    "school-i-e-alternating-verb-roots-stressed-a",
    "school-kas-kos-a-suffix-alternation",
    "school-klan-klon-stress-alternation",
    "school-lag-lozh-polog-exception",
    "school-rast-rashch-ros-exception-set",
    "school-skak-skoch-exception-set",
    "school-zar-zor-stress-alternation",
}
DOUBLE_OWNER = "school-double-consonants-morpheme-junction"


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def walk(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def one(rows: list[dict], key: str, value: str) -> dict:
    matches = [row for row in rows if row.get(key) == value]
    assert len(matches) == 1, f"expected exactly one {key}={value}, got {len(matches)}"
    return matches[0]


def main() -> None:
    manifest = load(MANIFEST)
    impact = load(IMPACT)
    overlay = load(OVERLAY)
    inventory = load(INVENTORY)
    exact = load(EXACT)

    assert manifest["status"] == "READY_FOR_ATOMIC_MATERIALIZATION_NOT_APPLIED"
    assert manifest["target"]["content_code"] == "6.2"

    impact_decision = impact["reopen_policy_application"]
    assert impact_decision["decision"] == "REOPEN_REQUIRED"
    assert impact["denominator_impact"]["school_denominator_before"] == 185
    assert impact["denominator_impact"]["projected_school_denominator_after_materialization"] == 186
    assert impact["denominator_impact"]["count_effect_applied_now"] == 0
    assert impact["proposed_identity_contract"]["unit_id"] == NEW_OWNER
    assert impact["proposed_identity_contract"]["status"] == "PROPOSED_REOPEN_TARGET_NOT_ADMITTED"

    frontier = manifest["prospective_exact_owner_frontier"]
    owners = frontier["owners"]
    assert len(owners) == len(set(owners)) == 16
    assert set(owners) == REUSED | {NEW_OWNER}
    assert frontier["owner_count"] == 16
    assert frontier["reused_current_canonical_owner_count"] == 15
    assert frontier["new_owner_count"] == 1
    assert frontier["new_owner"] == NEW_OWNER
    assert frontier["double_consonant_owner"] == DOUBLE_OWNER
    assert frontier["generic_double_consonant_root_owner_admitted"] is False
    assert set(frontier["legacy_placeholders_to_remove"]) == LEGACY
    assert len(ALTERNATING) == 8
    assert ALTERNATING <= set(owners)
    assert DOUBLE_OWNER in owners

    school_rows = [row for row in walk(inventory) if row.get("source_system") == "school_canonical"]
    school_ids = [row.get("source_id") for row in school_rows if row.get("source_id")]
    assert inventory["active_school_identity_count_observed"] == 185
    for source_id in sorted(REUSED):
        assert school_ids.count(source_id) == 1, f"reused owner must exist exactly once: {source_id}"
    assert school_ids.count(NEW_OWNER) == 0

    route = one(overlay["orthography_codifier_overlay"], "position", "6.2")
    current_owners = set(route["owners"])
    assert EXPLICIT_CURRENT <= current_owners
    assert LEGACY <= current_owners
    assert NEW_OWNER not in current_owners
    assert DOUBLE_OWNER not in current_owners
    assert not (ALTERNATING & current_owners)

    exact_6_2 = [row for row in walk(exact) if row.get("content_code") == "6.2"]
    assert exact_6_2 == []

    current = manifest["current_state"]
    assert current == {
        "school_denominator": 185,
        "new_identity_present": False,
        "exact_6_2_acceptance_present": False,
        "legacy_placeholders_present": True,
        "count_effect_applied_now": 0,
    }

    plan = manifest["atomic_materialization_plan"]
    assert plan["partial_sync_allowed"] is False
    assert len(plan["required_sync"]) == 5
    assert plan["projected_school_denominator_after"] == 186
    assert plan["materialization_applied"] is False
    assert plan["exact_6_2_acceptance_allowed_before_sync"] is False

    launch = manifest["launch_accounting"]
    assert launch["semantic_admissions_this_manifest"] == 0
    assert launch["object_closures_this_manifest"] == 0
    assert launch["false_exact_mastery_admissions"] == 0
    assert launch["bounded_ru_semantic_count_change"] == 0
    assert launch["russian_content_status"] == "BLOCKED_SUBJECT"
    safety = manifest["safety"]
    assert safety["accepted_demo_or_scorer_change"] is False
    assert safety["learner_audio_persistence"] == 0
    assert safety["provider_execution"] is False
    assert safety["production_peis_write"] is False
    assert safety["public_traffic"] is False

    normalized = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(normalized).hexdigest()
    print("OGE_6_2_ATOMIC_MATERIALIZATION_MANIFEST=PASS")
    print("EXACT_OWNER_FRONTIER=16")
    print("REUSED_CURRENT_CANONICAL_OWNERS=15")
    print("NEW_OWNERS=1")
    print("CURRENT_SCHOOL_DENOMINATOR=185")
    print("PROJECTED_SCHOOL_DENOMINATOR=186")
    print("COUNT_EFFECT_APPLIED_NOW=0")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print("MANIFEST_NORMALIZED_SHA256=" + digest)


if __name__ == "__main__":
    main()
