#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
CURRENT_ROUTE = ENGINE / "279-RUSSIAN-FIPI-2026-OGE-6.7-CURRENT-ROUTE-SUPERSESSION-v0.1.json"
ACCEPTANCE = HERE / "RUSSIAN-OGE-6.7-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
EVIDENCE_AUDITOR = HERE / "build_oge_6_7_current_evidence_audit_v3.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"

EXPECTED_OWNERS = [
    "school-adjective-ending-inflection-and-special-forms",
    "school-noun-case-ending-base",
    "school-noun-case-ending-special-paradigms",
    "school-noun-genitive-plural-ending-system",
    "school-noun-special-suffix-gender-endings",
    "school-numeral-case-ending-inflection-base",
    "school-numerals-both-parts-decline-50-80-200-900",
    "school-numerals-two-form-paradigm-40-90-100",
    "school-o-e-after-sibilants-suffix-ending",
    "school-proper-name-instrumental-ending-boundary",
    "school-verb-personal-ending-conjugation-base",
    "school-vowels-after-ts-suffix-ending",
]
REQ = "RSK-OGE_COD-6-7-P025"
UNIT = "RAU-2668e140328e4edee952"
GROUP = "RUS-SEM-REVIEW-064"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> None:
    route = load(CURRENT_ROUTE)
    acceptance = load(ACCEPTANCE)
    evidence = runpy.run_path(str(EVIDENCE_AUDITOR))["build_current_audit_v3"]()
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()

    assert route["status"] == "CURRENT_OGE_2026_6_7_ROUTE_SUPERSESSION_EXACT_OWNER_FRONTIER_NO_OBJECT_ADMISSION"
    assert route["position"] == "6.7"
    assert route["classification"] == "SCHOOL_IDENTITY_ROUTE"
    assert route["school_baseline_for_route"] == 186
    assert route["exact_owner_refs"] == EXPECTED_OWNERS
    assert len(set(route["exact_owner_refs"])) == 12
    owners = route["owner_accounting"]
    assert owners["owner_count"] == 12
    assert owners["reused_current_canonical"] == 12
    assert owners["newly_materialized_current_canonical"] == 0
    assert owners["legacy_family_placeholders"] == 0
    assert owners["unresolved_owners"] == 0
    assert route["mastery_boundary"]["route_attempt_can_emit_exact_component_mastery"] is False
    assert route["mastery_boundary"]["component_specific_independent_evidence_required"] is True
    assert route["mastery_boundary"]["exact_owner_frontier_is_not_object_acceptance"] is True

    assert evidence["status"] == "CENTRAL_BRAIN_OGE_6_7_COMPONENT_EVIDENCE_COMPLETE_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE_NOT_ACCEPTED"
    es = evidence["summary"]
    assert es["exact_owner_frontier"] == 12
    assert es["owners_with_explicit_component_specific_independent_evidence"] == 12
    assert es["owners_with_insufficient_exact_evidence"] == 0
    assert es["owners_with_mixed_semantic_evidence_only"] == 0
    assert es["owners_with_no_inventoried_independent_evidence"] == 0
    assert es["total_exact_independent_items_added_or_reused_by_bounded_oge_6_7_audits"] == 36
    assert es["ready_for_separate_exact_object_acceptance"] is True
    assert es["semantic_admissions"] == 0 and es["object_closures"] == 0
    assert es["false_exact_mastery_admissions"] == 0
    assert evidence["safety"]["learner_audio_persistence"] == 0

    assert evidence["target"]["requirement_id"] == REQ
    assert evidence["target"]["admission_unit_id"] == UNIT
    assert evidence["target"]["packet_group"] == GROUP
    assert evidence["target"]["source_locator"] == "FIPI-OGE-RU-2026-FINAL/OGE_COD p.25 6.7"

    assert acceptance["status"] == "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_7_CANONICAL_COMPONENT_SET"
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
    assert str(req["code"]) == "6.7"
    assert req["source_locator"] == "FIPI-OGE-RU-2026-FINAL/OGE_COD p.25 6.7"

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

    decisions = acceptance["decisions"]
    assert len(decisions) == 1
    decision = decisions[0]
    assert decision["admission_unit_id"] == UNIT
    assert decision["requirement_id"] == REQ
    assert decision["source_id"] == req["source_id"]
    assert decision["document_id"] == req["document_id"]
    assert decision["content_code"] == str(req["code"])
    assert decision["source_locator"] == req["source_locator"]
    assert decision["normalized_meaning"] == accounting_row["normalized_meaning"]
    assert decision["modules"] == accounting_row["modules"]
    assert decision["routes"] == accounting_row["routes"]
    assert decision["authority"]["packet_group"] == GROUP
    assert decision["canonical_component_refs"] == EXPECTED_OWNERS
    assert decision["component_count"] == 12
    readiness = decision["evidence_readiness"]
    assert readiness["current_evidence_v3_normalized_sha256"] == evidence["normalized_sha256"]
    assert readiness["owners_with_valid_component_evidence"] == 12
    assert readiness["independent_items_total"] == 36
    assert readiness["minimum_independent_items_per_owner"] == 3
    assert readiness["explicit_route_scoped_reused_items"] == 5
    mastery = decision["mastery_boundary"]
    assert mastery["route_or_broad_composite_attempt_can_emit_exact_component_mastery"] is False
    assert mastery["component_specific_independent_evidence_required"] is True
    assert mastery["validated_exact_component_item_may_support_only_its_single_canonical_ref"] is True
    assert decision["subject_semantic_status"] == "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET"

    summary = acceptance["summary"]
    assert summary["accepted_admission_units"] == 1
    assert summary["accepted_requirements"] == 1
    assert summary["canonical_component_refs_unique"] == 12
    assert summary["reused_current_canonical_owners"] == 12
    assert summary["new_school_canonical_identities_materialized_in_current_authority_chain"] == 0
    assert summary["independent_component_evidence_items"] == 36
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

    print("RUSSIAN_OGE_6_7_CURRENT_ACCEPTANCE=PASS")
    print("CURRENT_SCHOOL_DENOMINATOR=186")
    print("EXACT_OWNER_FRONTIER=12")
    print("REUSED_CURRENT_CANONICAL_OWNERS=12")
    print("NEW_SCHOOL_CANONICAL_IDENTITIES=0")
    print("INDEPENDENT_COMPONENT_EVIDENCE_ITEMS=36")
    print("ACCEPTED_OBJECT_UNITS=1")
    print("ACCEPTED_REQUIREMENTS=1")
    print("FALSE_EXACT_MASTERY=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print("ACCEPTANCE_NORMALIZED_SHA256=" + digest)


if __name__ == "__main__":
    main()
