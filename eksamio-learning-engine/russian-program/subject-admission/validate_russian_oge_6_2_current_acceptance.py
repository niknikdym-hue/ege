#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
BASE_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
MATERIALIZATION = ENGINE / "275-RUSSIAN-SCHOOL-OGE-6.2-REOPEN-MATERIALIZATION-v0.1.json"
CURRENT_ROUTE = ENGINE / "276-RUSSIAN-FIPI-2026-OGE-6.2-CURRENT-ROUTE-SUPERSESSION-v0.1.json"
CURRENT_FREEZE = ENGINE / "277-RUSSIAN-SCHOOL-CURRENT-LAUNCH-REFREEZE-v1.1.json"
SUPPLEMENT = HERE / "RUSSIAN-OGE-6.2-CANONICAL-INVENTORY-SUPPLEMENT-v0.1.json"
ACCEPTANCE = HERE / "RUSSIAN-OGE-6.2-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"

EXPECTED_OWNERS = [
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
    "school-root-consonant-dictionary-unverifiable",
]
NEW_OWNER = EXPECTED_OWNERS[-1]
REQ = "RSK-OGE_COD-6-2-P024"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> None:
    base = load(BASE_INVENTORY)
    materialization = load(MATERIALIZATION)
    route = load(CURRENT_ROUTE)
    freeze = load(CURRENT_FREEZE)
    supplement = load(SUPPLEMENT)
    acceptance = load(ACCEPTANCE)

    assert base["active_school_identity_count_observed"] == 185
    base_rows = [r for r in base["objects"] if r.get("source_system") == "school_canonical" and r.get("authority_status") == "current" and r.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY" and r.get("review_status") == "reviewed"]
    assert len(base_rows) == 185
    base_ids = {r["source_id"] for r in base_rows}
    assert len(base_ids) == 185 and NEW_OWNER not in base_ids

    assert materialization["status"] == "SCHOOL_LAYER_REOPENED_FROM_OFFICIAL_FIPI_ONE_IDENTITY_MATERIALIZED_CURRENT_186"
    assert materialization["count_assertion"] == {"absorptions": 0, "current_school_denominator_after": 186, "new_independent_school_identities": 1, "school_denominator_before": 185, "scope_only_expansions": 0}
    unit = materialization["canonical_units"]
    assert len(unit) == 1 and unit[0]["unit_id"] == NEW_OWNER and unit[0]["count_effect"] == 1

    assert supplement["status"] == "CURRENT_LAUNCH_CANONICAL_SCHOOL_INVENTORY_SUPPLEMENT"
    assert supplement["base_active_school_identity_count"] == 185
    assert supplement["supplement_count"] == 1 and supplement["current_active_school_identity_count"] == 186
    rows = supplement["objects"]
    assert len(rows) == 1
    new_row = rows[0]
    assert new_row["source_id"] == NEW_OWNER
    assert new_row["current_semantic_refs"] == [NEW_OWNER]
    assert new_row["authority_status"] == "current" and new_row["review_status"] == "reviewed"
    assert new_row["audit_classification"] == "CANONICAL_SCHOOL_IDENTITY"
    current_ids = base_ids | {NEW_OWNER}
    assert len(current_ids) == 186

    assert freeze["status"] == "CURRENT_LAUNCH_SCHOOL_DENOMINATOR_REFROZEN_AT_186_OGE_6_2_GAP_CLOSED"
    assert freeze["current_school_canonical_denominator"] == 186
    assert freeze["current_source_closure"]["current_unowned_oge_6_2_school_topics"] == 0
    assert freeze["current_source_closure"]["current_oge_6_2_reopen_candidates"] == 0
    assert freeze["current_source_closure"]["open_holds"] == 0
    assert freeze["historical_authority"]["mutated"] is False

    assert route["status"] == "CURRENT_OGE_2026_6_2_ROUTE_SUPERSESSION_EXACT"
    assert route["position"] == "6.2" and route["school_baseline_for_route"] == 186
    assert route["classification"] == "SCHOOL_IDENTITY_ROUTE"
    assert route["exact_owner_refs"] == EXPECTED_OWNERS
    assert len(set(route["exact_owner_refs"])) == 16
    assert set(route["exact_owner_refs"]) <= current_ids
    assert route["owner_accounting"] == {"legacy_family_placeholders": 0, "newly_materialized_current_canonical": 1, "owner_count": 16, "reused_preexisting_current_canonical": 15, "unresolved_owners": 0}
    assert route["mastery_boundary"]["route_attempt_can_emit_exact_component_mastery"] is False

    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()
    assert acceptance["object_accounting_sha256"] == accounting["normalized_sha256"]
    assert acceptance["semantic_packet_sha256"] == packet["normalized_sha256"]

    group_matches = []
    for group in packet["semantic_review_groups"]:
        for req in group["requirements"]:
            if req["requirement_id"] == REQ:
                group_matches.append((group, req))
    assert len(group_matches) == 1
    group, req = group_matches[0]
    assert group["group_id"] == "RUS-SEM-REVIEW-022"
    assert req["source_id"] == "FIPI-OGE-RU-2026-FINAL" and req["document_id"] == "OGE_COD"
    assert str(req["code"]) == "6.2" and req["source_locator"] == "FIPI-OGE-RU-2026-FINAL/OGE_COD p.24 6.2"

    accounting_rows = [r for r in accounting["dispositions"] if any(m["requirement_id"] == REQ for m in r.get("members", []))]
    assert len(accounting_rows) == 1
    accounting_row = accounting_rows[0]
    assert accounting_row["admission_unit_id"] == "RAU-085b9955399af22c784f"
    assert accounting_row["disposition"] == "PARTIAL_OR_COMPOSITE"
    assert len(accounting_row["members"]) == 1

    assert acceptance["status"] == "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_2_CANONICAL_COMPONENT_SET"
    decisions = acceptance["decisions"]
    assert len(decisions) == 1
    decision = decisions[0]
    assert decision["admission_unit_id"] == accounting_row["admission_unit_id"]
    assert decision["requirement_id"] == REQ
    assert decision["normalized_meaning"] == accounting_row["normalized_meaning"]
    assert decision["modules"] == accounting_row["modules"]
    assert decision["routes"] == accounting_row["routes"]
    assert decision["authority"]["packet_group"] == group["group_id"]
    assert decision["canonical_component_refs"] == EXPECTED_OWNERS
    assert decision["component_count"] == 16
    assert decision["mastery_boundary"]["route_or_broad_composite_attempt_can_emit_exact_component_mastery"] is False
    assert decision["mastery_boundary"]["component_specific_independent_evidence_required"] is True
    assert acceptance["summary"]["false_exact_mastery_admissions"] == 0
    assert acceptance["summary"]["new_school_canonical_identities_materialized_in_current_authority_chain"] == 1
    assert acceptance["summary"]["ru_proposal_identities_admitted"] == 0

    normalized = deepcopy(acceptance)
    digest = normalized.pop("normalized_sha256")
    assert digest == hashlib.sha256(canonical(normalized)).hexdigest()

    for authority in (materialization, route, freeze, supplement):
        safety = authority["safety"]
        assert safety["accepted_demo_or_scorer_change"] is False
        assert safety["learner_audio_persistence"] == 0
        assert safety["provider_execution"] is False
        assert safety["production_peis_write"] is False
        assert safety["public_traffic"] is False

    print("RUSSIAN_OGE_6_2_CURRENT_ACCEPTANCE=PASS")
    print("CURRENT_SCHOOL_DENOMINATOR=186")
    print("EXACT_OWNER_FRONTIER=16")
    print("REUSED_CURRENT_CANONICAL_OWNERS=15")
    print("NEW_SCHOOL_CANONICAL_IDENTITIES=1")
    print("ACCEPTED_OBJECT_UNITS=1")
    print("ACCEPTED_REQUIREMENTS=1")
    print("FALSE_EXACT_MASTERY=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print("ACCEPTANCE_NORMALIZED_SHA256=" + digest)


if __name__ == "__main__":
    main()
