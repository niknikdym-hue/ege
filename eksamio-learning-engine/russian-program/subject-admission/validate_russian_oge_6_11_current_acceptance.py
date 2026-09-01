#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
ACCEPTANCE = HERE / "RUSSIAN-OGE-6.11-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
OWNER_REVIEW = HERE / "build_oge_6_11_service_words_exact_owner_resolution.py"
COMPONENT_VALIDATOR = HERE / "validate_oge_6_11_component_evidence.py"
EVIDENCE_AUDITOR = HERE / "build_oge_6_11_object_evidence_audit.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"

EXPECTED_OWNERS = ['school-conjunction-solid-separate-spelling-base', 'school-nonnegative-particle-separate-hyphen-spelling-base', 'school-preposition-solid-hyphen-separate-base']
REQ = "RSK-OGE_COD-6-11-P025"
UNIT = "RAU-50d61db39b3c45d2980e"
GROUP = "RUS-SEM-REVIEW-073"
COMPONENT_SHA = "e70a8414ab5776653f123cf978c829d519a245ed610286814574b59b460c1e75"
EVIDENCE_SHA = "b6789de0ac43a1349731679691b30f1383da18897af3a2d95d1b691fb1471382"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> None:
    inventory = load(INVENTORY)
    acceptance = load(ACCEPTANCE)
    owner_resolution = runpy.run_path(str(OWNER_REVIEW))["build_resolution"]()
    component = runpy.run_path(str(COMPONENT_VALIDATOR))["validate"]()
    evidence = runpy.run_path(str(EVIDENCE_AUDITOR))["build_audit"]()
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()

    assert owner_resolution["status"] == "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_EVIDENCE_REQUIRED"
    ores = owner_resolution["exact_owner_resolution"]
    assert ores["exact_current_canonical_owners"] == EXPECTED_OWNERS
    assert ores["exact_owner_count"] == 3
    assert ores["unresolved_owner_candidates"] == 0
    assert ores["unresolved_placeholders"] == 0
    assert ores["new_school_identities_required"] == 0
    assert ores["current_route_supersession_required"] is False
    assert ores["current_inventory_route_already_matches_exact_owner_set"] is True
    assert ores["evidence_gate_required_before_object_acceptance"] is True
    assert owner_resolution["official_source_boundary"]["official_atomic_source_objects"] == 1
    assert owner_resolution["official_source_boundary"]["official_explicit_subbranches"] == 0
    assert owner_resolution["safety"]["semantic_admissions"] == 0
    assert owner_resolution["safety"]["object_closures"] == 0
    assert owner_resolution["safety"]["false_exact_mastery"] == 0
    assert owner_resolution["safety"]["learner_audio_persistence"] == 0

    objects = [row for row in inventory.get("objects") or [] if isinstance(row, dict)]
    route_key = "oge_2026_orthography_route::oge-2026-orthography-6-11"
    route_rows = [row for row in objects if row.get("object_key") == route_key]
    assert len(route_rows) == 1
    route = route_rows[0]
    assert route["authority_status"] == "current"
    assert route["review_status"] == "reviewed"
    assert route["audit_classification"] == "EXAM_ROUTE_ONLY"
    assert route["current_semantic_refs"] == EXPECTED_OWNERS

    canonical_rows = {
        str(row.get("source_id")): row
        for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and row.get("review_status") == "reviewed"
        and row.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
    }
    for owner in EXPECTED_OWNERS:
        row = canonical_rows[owner]
        assert row["current_semantic_refs"] == [owner]
        assert row["candidate_canonical_owner"] == owner

    cs = component["summary"]
    assert component["status"] == "CENTRAL_BRAIN_OGE_6_11_COMPONENT_EVIDENCE_MATERIALIZED_NO_OBJECT_ADMISSION"
    assert component["normalized_sha256"] == COMPONENT_SHA
    assert component["exact_owner_refs"] == EXPECTED_OWNERS
    assert component["reuse_first_inventory_audit"]["existing_exact_current_trainer_or_practice_items"] == 0
    assert component["reuse_first_inventory_audit"]["mixed_or_route_scoped_items_counted"] == 0
    assert cs["exact_owner_frontier"] == 3
    assert cs["owners_with_valid_component_evidence"] == 3
    assert cs["independent_items_total"] == 9
    assert cs["minimum_items_per_owner"] == 3
    assert cs["selected_response_items"] == 6
    assert cs["constructed_response_items"] == 3
    assert cs["semantic_admissions"] == 0 and cs["object_closures"] == 0
    assert cs["false_exact_mastery_admissions"] == 0
    assert component["safety"]["learner_audio_persistence"] == 0

    assert evidence["status"] == "CENTRAL_BRAIN_OGE_6_11_COMPONENT_EVIDENCE_FRONTIER_COMPLETE_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE"
    assert evidence["normalized_sha256"] == EVIDENCE_SHA
    assert evidence["exact_owner_refs"] == EXPECTED_OWNERS
    es = evidence["summary"]
    assert es["official_fipi_source_objects"] == 1
    assert es["official_fipi_explicit_subbranches"] == 0
    assert es["exact_owner_frontier"] == 3
    assert es["owners_with_explicit_component_specific_independent_evidence"] == 3
    assert es["owners_with_insufficient_exact_evidence"] == 0
    assert es["owners_with_mixed_semantic_evidence_only"] == 0
    assert es["owners_with_no_independent_evidence"] == 0
    assert es["materialized_exact_independent_items"] == 9
    assert es["reused_preexisting_exact_inventory_items"] == 0
    assert es["ready_for_separate_exact_object_acceptance"] is True
    assert es["semantic_admissions"] == 0 and es["object_closures"] == 0
    assert es["false_exact_mastery_admissions"] == 0
    assert evidence["safety"]["learner_audio_persistence"] == 0

    assert evidence["target"]["requirement_id"] == REQ
    assert evidence["target"]["admission_unit_id"] == UNIT
    assert evidence["target"]["packet_group"] == GROUP
    assert evidence["target"]["source_locator"] == "FIPI-OGE-RU-2026-FINAL/OGE_COD p.25 6.11"
    assert evidence["target"]["current_disposition"] == "PARTIAL_OR_COMPOSITE"

    assert acceptance["status"] == "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_11_CANONICAL_COMPONENT_SET"
    assert acceptance["semantic_packet_sha256"] == packet["normalized_sha256"]
    assert acceptance["object_accounting_sha256"] == accounting["normalized_sha256"]

    packet_matches = []
    for group in packet["semantic_review_groups"]:
        for req in group["requirements"]:
            if req["requirement_id"] == REQ:
                packet_matches.append((group, req))
    assert len(packet_matches) == 1
    group, req = packet_matches[0]
    assert group["group_id"] == GROUP
    assert req["source_id"] == "FIPI-OGE-RU-2026-FINAL"
    assert req["document_id"] == "OGE_COD"
    assert str(req["code"]) == "6.11"
    assert req["source_locator"] == "FIPI-OGE-RU-2026-FINAL/OGE_COD p.25 6.11"

    accounting_rows = [
        row
        for row in accounting["dispositions"]
        if any(member["requirement_id"] == REQ for member in row.get("members", []))
    ]
    assert len(accounting_rows) == 1
    accounting_row = accounting_rows[0]
    assert accounting_row["admission_unit_id"] == UNIT
    assert accounting_row["disposition"] == "PARTIAL_OR_COMPOSITE"
    assert len(accounting_row["members"]) == 1
    assert accounting_row["semantic_identity_ref"] is None

    decisions = acceptance["decisions"]
    assert len(decisions) == 1
    decision = decisions[0]
    assert decision["admission_unit_id"] == UNIT
    assert decision["requirement_id"] == REQ
    assert decision["source_id"] == req["source_id"]
    assert decision["document_id"] == req["document_id"]
    assert decision["content_code"] == str(req["code"])
    assert decision["source_locator"] == req["source_locator"]
    assert decision["disposition"] == accounting_row["disposition"]
    assert decision["route_inventory_classification"] == "EXAM_ROUTE_ONLY"
    assert decision["normalized_meaning"] == accounting_row["normalized_meaning"]
    assert decision["modules"] == accounting_row["modules"]
    assert decision["routes"] == accounting_row["routes"]
    assert decision["authority"]["packet_group"] == GROUP
    assert decision["canonical_component_refs"] == EXPECTED_OWNERS
    assert decision["component_count"] == 3

    readiness = decision["evidence_readiness"]
    assert readiness["component_validator_normalized_sha256"] == component["normalized_sha256"]
    assert readiness["current_evidence_audit_normalized_sha256"] == evidence["normalized_sha256"]
    assert readiness["owners_with_valid_component_evidence"] == 3
    assert readiness["independent_items_total"] == 9
    assert readiness["minimum_independent_items_per_owner"] == 3
    assert readiness["preexisting_exact_inventory_items_reused"] == 0

    mastery = decision["mastery_boundary"]
    assert mastery["accepted_mapping_can_emit_partial_or_composite_evidence"] is True
    assert mastery["route_or_broad_composite_attempt_can_emit_exact_component_mastery"] is False
    assert mastery["component_specific_independent_evidence_required"] is True
    assert mastery["validated_exact_component_item_may_support_only_its_single_canonical_ref"] is True
    assert decision["subject_semantic_status"] == "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET"

    policy = acceptance["policy"]
    assert policy["reuse_first"] is True
    assert policy["all_owners_must_be_exact_current_reviewed_canonical_school_ids"] is True
    assert policy["component_specific_independent_evidence_required"] is True
    assert policy["validated_component_evidence_required_before_object_acceptance"] is True
    assert policy["minimum_independent_items_per_owner"] == 3
    assert policy["cross_route_reuse_requires_explicit_item_whitelist"] is True
    assert policy["cross_route_reuse_used"] is False
    assert policy["generic_composite_attempt_can_exact_master_components"] is False
    assert policy["keyword_or_fuzzy_mapping_allowed"] is False
    assert policy["legacy_family_placeholders_allowed"] is False
    assert policy["absorbed_historical_identity_may_be_reopened"] is False
    assert policy["manufactured_fipi_subbranches_allowed"] is False
    assert policy["current_route_supersession_required"] is False

    summary = acceptance["summary"]
    assert summary["accepted_admission_units"] == 1
    assert summary["accepted_requirements"] == 1
    assert summary["accepted_content_codes"] == 1
    assert summary["canonical_component_refs_unique"] == 3
    assert summary["reused_current_canonical_owners"] == 3
    assert summary["new_school_canonical_identities_materialized_in_current_authority_chain"] == 0
    assert summary["independent_component_evidence_items"] == 9
    assert summary["preexisting_exact_inventory_items_reused"] == 0
    assert summary["ru_proposal_identities_admitted"] == 0
    assert summary["false_exact_mastery_admissions"] == 0

    normalized = deepcopy(acceptance)
    digest = normalized.pop("normalized_sha256")
    assert digest == hashlib.sha256(canonical(normalized)).hexdigest()

    safety = acceptance["safety"]
    assert safety["accepted_demo_or_scorer_change"] is False
    assert safety["tilda_change"] is False
    assert safety["learner_audio_persistence"] == 0
    assert safety["production_peis_write"] is False
    assert safety["provider_execution"] is False
    assert safety["public_traffic"] is False
    assert safety["real_payment_or_refund"] is False
    assert safety["real_message_delivery"] is False

    print("RUSSIAN_OGE_6_11_CURRENT_ACCEPTANCE=PASS")
    print("OFFICIAL_FIPI_SOURCE_OBJECTS=1")
    print("OFFICIAL_FIPI_EXPLICIT_SUBBRANCHES=0")
    print("EXACT_OWNER_FRONTIER=3")
    print("REUSED_CURRENT_CANONICAL_OWNERS=3")
    print("NEW_SCHOOL_CANONICAL_IDENTITIES=0")
    print("CURRENT_ROUTE_SUPERSESSION_REQUIRED=0")
    print("INDEPENDENT_COMPONENT_EVIDENCE_ITEMS=9")
    print("PREEXISTING_EXACT_INVENTORY_ITEMS_REUSED=0")
    print("ACCEPTED_OBJECT_UNITS=1")
    print("ACCEPTED_REQUIREMENTS=1")
    print("FALSE_EXACT_MASTERY=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print("ACCEPTANCE_NORMALIZED_SHA256=" + digest)


if __name__ == "__main__":
    main()
