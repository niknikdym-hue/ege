#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
ACCEPTANCE = HERE / "RUSSIAN-OGE-6.13-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
SOURCE_FRONTIER = HERE / "build_oge_6_13_compound_words_source_bound_frontier_review.py"
OWNER_REVIEW = HERE / "build_oge_6_13_compound_words_exact_owner_resolution.py"
PREEXISTING_AUDITOR = HERE / "build_oge_6_13_object_evidence_audit.py"
COMPONENT_VALIDATOR = HERE / "validate_oge_6_13_component_evidence.py"
CURRENT_EVIDENCE_AUDITOR = HERE / "build_oge_6_13_current_evidence_audit.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"

EXPECTED_OWNERS = [
    "school-compound-linking-vowel",
    "school-compound-first-part-without-linking-vowel-system",
    "school-compound-noun-solid-hyphen-system",
    "school-compound-adjective-solid-hyphen-separate-system",
    "school-abbreviations-capitalization-formation",
]
REQ = "RSK-OGE_COD-6-13-P025"
UNIT = "RAU-479a0fc6f772ea8434b1"
GROUP = "RUS-SEM-REVIEW-054"
PREEXISTING_SHA = "face08306a4e8fde936149b9ead73ab4a108d66f041ed27833996e092e5f9b1f"
COMPONENT_SHA = "e23d1f23aeb5962fbf7cddde16fa779fc9073d24bc049ca755bc79e3419f0d4d"
CURRENT_EVIDENCE_SHA = "5d139a3bf7250fc6f41615f63323c2dc2a5ce7d907e311ce69140084af5e2ba4"
ACCEPTANCE_SHA = "c1334e8348c24b3a8cd7d2612a0f5643c92e6b74991119c3e0b3767439a18e4d"
ROUTE_OBJECT_KEY = "oge_2026_orthography_route::oge-2026-orthography-6-13"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> None:
    inventory = load(INVENTORY)
    acceptance = load(ACCEPTANCE)
    source = runpy.run_path(str(SOURCE_FRONTIER))["build_review"]()
    owners = runpy.run_path(str(OWNER_REVIEW))["build_resolution"]()
    preexisting = runpy.run_path(str(PREEXISTING_AUDITOR))["build_audit"]()
    component = runpy.run_path(str(COMPONENT_VALIDATOR))["validate"]()
    evidence = runpy.run_path(str(CURRENT_EVIDENCE_AUDITOR))["build_audit"]()
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()

    assert source["status"] == "SOURCE_BOUND_FRONTIER_ONLY_EXACT_OWNER_REVIEW_REQUIRED"
    assert source["official_source"]["source_system"] == "OGE_COD"
    assert source["official_source"]["code"] == "6.13"
    assert source["official_source"]["explicit_subbranches"] == []
    assert source["official_source"]["fabricated_subcodes"] == 0

    assert owners["status"] == "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_EVIDENCE_AUDIT_REQUIRED"
    ores = owners["exact_owner_resolution"]
    assert ores["exact_current_canonical_owners"] == EXPECTED_OWNERS
    assert ores["exact_owner_count"] == 5
    assert ores["unresolved_owner_candidates"] == 0
    assert ores["new_school_identities_required"] == 0
    assert ores["current_inventory_route_already_matches_exact_owner_set"] is True
    assert ores["current_route_supersession_required"] is False
    assert ores["evidence_gate_required_before_object_acceptance"] is True

    objects = [row for row in inventory.get("objects") or [] if isinstance(row, dict)]
    route_rows = [row for row in objects if row.get("object_key") == ROUTE_OBJECT_KEY]
    assert len(route_rows) == 1
    route_refs = [str(x) for x in route_rows[0].get("current_semantic_refs") or []]
    assert len(route_refs) == 5 and set(route_refs) == set(EXPECTED_OWNERS)
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

    ps = preexisting["summary"]
    assert preexisting["status"] == "CENTRAL_BRAIN_OGE_6_13_COMPONENT_EVIDENCE_GAPS_PROVEN_NO_OBJECT_ACCEPTANCE"
    assert preexisting["normalized_sha256"] == PREEXISTING_SHA
    assert preexisting["exact_owner_refs"] == EXPECTED_OWNERS
    assert ps["exact_owner_frontier"] == 5
    assert ps["owners_with_preexisting_exact_component_evidence"] == 0
    assert ps["preexisting_exact_independent_items"] == 0
    assert ps["ready_without_materialization"] is False
    assert ps["semantic_admissions"] == 0 and ps["object_closures"] == 0
    assert ps["false_exact_mastery_admissions"] == 0

    cs = component["summary"]
    assert component["status"] == "CENTRAL_BRAIN_OGE_6_13_COMPONENT_EVIDENCE_MATERIALIZED_NO_OBJECT_ADMISSION"
    assert component["normalized_sha256"] == COMPONENT_SHA
    assert component["exact_owner_refs"] == EXPECTED_OWNERS
    assert cs["exact_owner_frontier"] == 5
    assert cs["owners_with_valid_component_evidence"] == 5
    assert cs["independent_items_total"] == 15
    assert cs["minimum_items_per_owner"] == 3
    assert cs["selected_response_items"] == 10
    assert cs["constructed_response_items"] == 5
    assert cs["existing_exact_inventory_items"] == 0
    assert cs["materialized_new_items"] == 15
    assert cs["semantic_admissions"] == 0 and cs["object_closures"] == 0
    assert cs["false_exact_mastery_admissions"] == 0

    es = evidence["summary"]
    assert evidence["status"] == "CENTRAL_BRAIN_OGE_6_13_COMPONENT_EVIDENCE_FRONTIER_COMPLETE_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE"
    assert evidence["normalized_sha256"] == CURRENT_EVIDENCE_SHA
    assert evidence["exact_owner_refs"] == EXPECTED_OWNERS
    assert evidence["evidence_chain"]["preexisting_audit_normalized_sha256"] == PREEXISTING_SHA
    assert evidence["evidence_chain"]["component_validator_normalized_sha256"] == COMPONENT_SHA
    assert es["official_fipi_source_objects"] == 1
    assert es["official_fipi_explicit_subbranches"] == 0
    assert es["exact_owner_frontier"] == 5
    assert es["owners_with_explicit_component_specific_independent_evidence"] == 5
    assert es["owners_with_insufficient_exact_evidence"] == 0
    assert es["owners_with_mixed_semantic_evidence_only"] == 0
    assert es["owners_with_no_independent_evidence"] == 0
    assert es["materialized_exact_independent_items"] == 15
    assert es["reused_preexisting_exact_inventory_items"] == 0
    assert es["ready_for_separate_exact_object_acceptance"] is True
    assert es["semantic_admissions"] == 0 and es["object_closures"] == 0
    assert es["false_exact_mastery_admissions"] == 0

    target = evidence["target"]
    assert target == {
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "document_id": "OGE_COD",
        "content_code": "6.13",
        "requirement_id": REQ,
        "admission_unit_id": UNIT,
        "source_locator": "FIPI-OGE-RU-2026-FINAL/OGE_COD p.25 6.13",
        "packet_group": GROUP,
        "normalized_meaning": "Применять орфографическое правило к слову или форме.",
        "modules": ["RU-PROG-08"],
        "routes": ["oge"],
        "current_disposition": "PARTIAL_OR_COMPOSITE",
    }

    assert acceptance["status"] == "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_13_CANONICAL_COMPONENT_SET"
    assert acceptance["semantic_packet_sha256"] == packet["normalized_sha256"]
    assert acceptance["object_accounting_sha256"] == accounting["normalized_sha256"]

    packet_matches = []
    for packet_group in packet["semantic_review_groups"]:
        for req in packet_group["requirements"]:
            if req["requirement_id"] == REQ:
                packet_matches.append((packet_group, req))
    assert len(packet_matches) == 1
    packet_group, req = packet_matches[0]
    assert packet_group["group_id"] == GROUP
    assert req["source_id"] == target["source_id"]
    assert req["document_id"] == target["document_id"]
    assert str(req["code"]) == target["content_code"]
    assert req["source_locator"] == target["source_locator"]

    accounting_rows = [
        row for row in accounting["dispositions"]
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
    assert decision["source_id"] == target["source_id"]
    assert decision["document_id"] == target["document_id"]
    assert decision["content_code"] == target["content_code"]
    assert decision["source_locator"] == target["source_locator"]
    assert decision["disposition"] == accounting_row["disposition"]
    assert decision["route_inventory_classification"] == "EXAM_ROUTE_ONLY"
    assert decision["normalized_meaning"] == accounting_row["normalized_meaning"] == target["normalized_meaning"]
    assert decision["modules"] == accounting_row["modules"] == target["modules"]
    assert decision["routes"] == accounting_row["routes"] == target["routes"]
    assert decision["canonical_component_refs"] == EXPECTED_OWNERS
    assert decision["component_count"] == 5
    assert decision["authority"]["packet_group"] == GROUP
    assert decision["authority"]["current_inventory_route"].endswith(ROUTE_OBJECT_KEY)

    readiness = decision["evidence_readiness"]
    assert readiness["preexisting_evidence_audit_normalized_sha256"] == PREEXISTING_SHA
    assert readiness["component_validator_normalized_sha256"] == COMPONENT_SHA
    assert readiness["current_evidence_audit_normalized_sha256"] == CURRENT_EVIDENCE_SHA
    assert readiness["owners_with_valid_component_evidence"] == 5
    assert readiness["independent_items_total"] == 15
    assert readiness["minimum_independent_items_per_owner"] == 3
    assert readiness["preexisting_exact_inventory_items_reused"] == 0

    mastery = decision["mastery_boundary"]
    assert mastery["accepted_mapping_can_emit_partial_or_composite_evidence"] is True
    assert mastery["route_or_broad_composite_attempt_can_emit_exact_component_mastery"] is False
    assert mastery["component_specific_independent_evidence_required"] is True
    assert mastery["validated_exact_component_item_may_support_only_its_single_canonical_ref"] is True
    assert decision["subject_semantic_status"] == "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET"

    policy = acceptance["policy"]
    assert policy == {
        "reuse_first": True,
        "all_owners_must_be_exact_current_reviewed_canonical_school_ids": True,
        "component_specific_independent_evidence_required": True,
        "validated_component_evidence_required_before_object_acceptance": True,
        "minimum_independent_items_per_owner": 3,
        "cross_route_reuse_requires_explicit_item_whitelist": True,
        "cross_route_reuse_used": False,
        "generic_composite_attempt_can_exact_master_components": False,
        "keyword_or_fuzzy_mapping_allowed": False,
        "legacy_family_placeholders_allowed": False,
        "manufactured_fipi_subbranches_allowed": False,
        "current_route_supersession_required": False,
    }

    summary = acceptance["summary"]
    assert summary == {
        "accepted_admission_units": 1,
        "accepted_requirements": 1,
        "accepted_content_codes": 1,
        "canonical_component_refs_unique": 5,
        "reused_current_canonical_owners": 5,
        "new_school_canonical_identities_materialized_in_current_authority_chain": 0,
        "independent_component_evidence_items": 15,
        "preexisting_exact_inventory_items_reused": 0,
        "ru_proposal_identities_admitted": 0,
        "false_exact_mastery_admissions": 0,
    }

    expected_safety = {
        "accepted_demo_or_scorer_change": False,
        "tilda_change": False,
        "learner_audio_persistence": 0,
        "production_peis_write": False,
        "provider_execution": False,
        "public_traffic": False,
        "real_payment_or_refund": False,
        "real_message_delivery": False,
    }
    assert acceptance["safety"] == expected_safety
    assert component["safety"] == expected_safety
    assert evidence["safety"] == expected_safety

    normalized = deepcopy(acceptance)
    digest = normalized.pop("normalized_sha256")
    assert digest == ACCEPTANCE_SHA
    assert digest == hashlib.sha256(canonical(normalized)).hexdigest()

    print("RUSSIAN_OGE_6_13_CURRENT_ACCEPTANCE=PASS")
    print("REQUIREMENT_ID=" + REQ)
    print("ADMISSION_UNIT_ID=" + UNIT)
    print("PACKET_GROUP=" + GROUP)
    print("OFFICIAL_FIPI_SOURCE_OBJECTS=1")
    print("OFFICIAL_FIPI_EXPLICIT_SUBBRANCHES=0")
    print("EXACT_OWNER_FRONTIER=5")
    print("REUSED_CURRENT_CANONICAL_OWNERS=5")
    print("NEW_SCHOOL_CANONICAL_IDENTITIES=0")
    print("CURRENT_ROUTE_SUPERSESSION_REQUIRED=0")
    print("INDEPENDENT_COMPONENT_EVIDENCE_ITEMS=15")
    print("PREEXISTING_EXACT_INVENTORY_ITEMS_REUSED=0")
    print("ACCEPTED_OBJECT_UNITS=1")
    print("ACCEPTED_REQUIREMENTS=1")
    print("FALSE_EXACT_MASTERY=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print("ACCEPTANCE_NORMALIZED_SHA256=" + digest)


if __name__ == "__main__":
    main()
