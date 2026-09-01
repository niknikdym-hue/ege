#!/usr/bin/env python3
"""Build the exact current OGE-2026 6.14 object-acceptance candidate.

The builder is deliberately fail-closed and does not alter aggregate progress. It
binds the unique OGE_COD 6.14 object identity to the already accepted exact
orthography component projection and to the final effective independent learner-
evidence proof. A broad/composite 6.14 attempt never emits exact component
mastery; only validated single-component evidence may support its exact owner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DERIVATION = HERE / "build_oge_6_14_current_exact_component_derivation.py"
EVIDENCE_V5 = HERE / "build_oge_6_14_reuse_first_evidence_audit_v5.py"
IDENTITY = HERE / "build_oge_6_14_object_identity_binding_review.py"
PACKET = HERE / "build_russian_semantic_acceptance_packet.py"
ACCOUNTING = HERE / "build_russian_subject_accounting_complete.py"

EXPECTED_DERIVATION_SHA = "1b792cb24ea88873fb3317d74fa12977a648683727f2e381281554a73c898829"
EXPECTED_EVIDENCE_V5_SHA = "cb106fb78cf66ec77daa25662bdd7db931dc4a8108e4de2dcfd84780f6bd6036"
EXPECTED_IDENTITY_SHA = "1e687783350650d4bc0b7622e5004553600452f95f209840379cb60a2bd16516"
EXPECTED_PACKET_SHA = "b35fb420f7a6e96ea11f47e321cae0affe363dc5ed8d6fb79ea8640ac5ac94c4"
EXPECTED_ACCOUNTING_SHA = "f3aef83dab99b554a4cdec9ef8d8fbc8036d557182259ae69db182efa11b925c"
EXPECTED_REUSE_EXHAUSTION_SHA = "9aae09034623cdd73c043bd5c515b9a8271e422d6cac70205300daceaa5a6773"
EXPECTED_UNIT = "RAU-af3fa30939d38a3ea03d"
EXPECTED_REQUIREMENT = "RSK-OGE_COD-6-14-P025"
EXPECTED_GROUP = "RUS-SEM-REVIEW-056"
EXPECTED_OWNER_COUNT = 83
EXPECTED_EVIDENCE_ITEMS = 262


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalized_sha(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def build_acceptance() -> dict[str, Any]:
    derivation = runpy.run_path(str(DERIVATION))["build_derivation"]()
    evidence = runpy.run_path(str(EVIDENCE_V5))["build_audit_v5"]()
    identity = runpy.run_path(str(IDENTITY))["build_review"]()
    packet = runpy.run_path(str(PACKET))["build_packet"]()
    accounting = runpy.run_path(str(ACCOUNTING))["build_accounting"]()

    if derivation.get("normalized_sha256") != EXPECTED_DERIVATION_SHA:
        raise ValueError("6.14 exact component derivation fingerprint drift")
    if evidence.get("normalized_sha256") != EXPECTED_EVIDENCE_V5_SHA:
        raise ValueError("6.14 final effective evidence fingerprint drift")
    if identity.get("normalized_sha256") != EXPECTED_IDENTITY_SHA:
        raise ValueError("6.14 object identity fingerprint drift")
    if packet.get("normalized_sha256") != EXPECTED_PACKET_SHA:
        raise ValueError("Russian semantic packet fingerprint drift")
    if accounting.get("normalized_sha256") != EXPECTED_ACCOUNTING_SHA:
        raise ValueError("Russian object-accounting fingerprint drift")

    official = identity["official_object"]
    duplicate = identity["duplicate_accounting_review"]
    source = derivation["official_source"]
    d = derivation["derivation"]
    es = evidence["summary"]
    historical = evidence["historical_reuse_proof_guard"]

    expected_identity = {
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "document_id": "OGE_COD",
        "content_code": "6.14",
        "label_ru": "Орфографический анализ",
        "classification": "EXAM_ONLY_COMPOSITE",
        "admission_unit_id": EXPECTED_UNIT,
        "requirement_id": EXPECTED_REQUIREMENT,
        "packet_group": EXPECTED_GROUP,
    }
    for key, value in expected_identity.items():
        if official.get(key) != value:
            raise ValueError(f"6.14 object identity drift: {key}")
    if source != {
        "source_system": "OGE_COD",
        "cycle": 2026,
        "code": "6.14",
        "label": "Орфографический анализ",
        "classification": "EXAM_ONLY_COMPOSITE",
        "fabricated_subcodes": 0,
    }:
        raise ValueError("6.14 official composite boundary drift")
    if duplicate != {
        "accepted_rows_with_content_code_6_14": 0,
        "accepted_rows_with_same_admission_unit_or_requirement": 0,
        "historical_or_current_object_already_counted": False,
        "aggregate_delta_if_later_exact_acceptance_passes": 1,
    }:
        raise ValueError("6.14 duplicate-accounting review drift")

    owners = [str(ref) for ref in d["applicable_component_refs"]]
    evidence_owners = [str(ref) for ref in evidence["exact_owner_refs"]]
    if len(owners) != EXPECTED_OWNER_COUNT or len(set(owners)) != EXPECTED_OWNER_COUNT:
        raise ValueError("6.14 exact owner frontier is not 83 unique owners")
    if owners != sorted(owners):
        raise ValueError("6.14 exact owner frontier is not deterministically ordered")
    if evidence_owners != owners:
        raise ValueError("6.14 evidence owner frontier differs from exact derivation")
    if d["source_codes"] != [f"6.{index}" for index in range(2, 14)]:
        raise ValueError("6.14 source-code projection drift")
    if d["component_memberships_before_deduplication"] != 90 or d["shared_component_ref_count"] != 7:
        raise ValueError("6.14 component projection cardinality drift")
    if d["placeholder_owner_used"] or d["manual_broad_list_used"] or d["keyword_or_fuzzy_inference_used"] or d["all_school_identities_used"]:
        raise ValueError("6.14 exact frontier used a forbidden broad inference path")

    expected_evidence_status = (
        "CENTRAL_BRAIN_OGE_6_14_COMPONENT_EVIDENCE_COMPLETE_STRUCTURED_BRANCH_COVERAGE_AND_"
        "HISTORICAL_REUSE_GUARD_PROVEN_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE_NOT_ACCEPTED"
    )
    if evidence.get("status") != expected_evidence_status:
        raise ValueError("6.14 final evidence status drift")
    if es["exact_owner_frontier"] != EXPECTED_OWNER_COUNT:
        raise ValueError("6.14 evidence frontier count drift")
    if es["owners_with_explicit_component_specific_independent_evidence"] != EXPECTED_OWNER_COUNT:
        raise ValueError("6.14 evidence-ready owner count drift")
    if es["exact_independent_items_reused"] != EXPECTED_EVIDENCE_ITEMS:
        raise ValueError("6.14 exact independent evidence denominator drift")
    if es["effective_wave_002_owner_count"] != 16 or es["effective_wave_002_independent_items"] != 48:
        raise ValueError("6.14 effective wave-002 denominator drift")
    if es["structured_repair_owner_count"] != 2 or es["structured_repair_replaced_item_count"] != 6:
        raise ValueError("6.14 structured-repair replacement drift")
    if es["structured_repair_additional_item_count"] != 0:
        raise ValueError("6.14 structured repair became additive")
    if es["structured_branch_coverage_complete"] is not True:
        raise ValueError("6.14 structured branch coverage is incomplete")
    if es["historical_reuse_proof_fingerprint_preserved"] is not True:
        raise ValueError("6.14 historical reuse proof fingerprint is not preserved")
    if es["ready_for_separate_exact_object_acceptance"] is not True:
        raise ValueError("6.14 evidence is not ready for separate exact object acceptance")
    if es["semantic_admissions"] != 0 or es["object_closures"] != 0 or es["false_exact_mastery_admissions"] != 0:
        raise ValueError("6.14 evidence stage performed a forbidden admission")
    if historical["expected_and_observed_reuse_exhaustion_normalized_sha256"] != EXPECTED_REUSE_EXHAUSTION_SHA:
        raise ValueError("6.14 historical reuse-exhaustion fingerprint drift")
    if historical["broad_exclusion_used"] is not False:
        raise ValueError("6.14 historical proof used a broad exclusion")
    if evidence["safety"]["learner_audio_persistence"] != 0:
        raise ValueError("learner audio persistence must remain zero")

    decision = {
        "acceptance_reason": (
            "FIPI OGE-2026 code 6.14 is one exam-only orthographic-analysis composite, not a new school identity. "
            "The current frontier is derived only from the already accepted exact OGE orthography authorities for "
            "6.2–6.13: 90 memberships deduplicate to 83 current canonical school owners. The final effective reuse-first "
            "evidence audit proves independent component-specific learner evidence for all 83 owners (262 effective exact "
            "items), including bounded replacement-only structured coverage for the two composite owners, while preserving "
            "the historical pre-materialization reuse fingerprint. The unique 6.14 admission unit/requirement is not "
            "already counted. Acceptance therefore binds this object to those 83 components as PARTIAL_OR_COMPOSITE; a "
            "generic 6.14 route attempt cannot emit exact component mastery."
        ),
        "admission_unit_id": EXPECTED_UNIT,
        "requirement_id": EXPECTED_REQUIREMENT,
        "source_id": official["source_id"],
        "document_id": official["document_id"],
        "content_code": official["content_code"],
        "source_locator": official["source_locator"],
        "disposition": "PARTIAL_OR_COMPOSITE",
        "route_inventory_classification": "EXAM_ROUTE_ONLY",
        "normalized_meaning": official["normalized_meaning"],
        "modules": ["RU-PROG-08"],
        "routes": ["oge"],
        "canonical_component_refs": owners,
        "component_count": len(owners),
        "authority": {
            "current_exact_component_derivation": DERIVATION.name,
            "final_effective_evidence_audit": EVIDENCE_V5.name,
            "object_identity_binding_review": IDENTITY.name,
            "source_component_codes": d["source_codes"],
            "packet_group": EXPECTED_GROUP,
        },
        "evidence_readiness": {
            "current_exact_component_derivation_normalized_sha256": EXPECTED_DERIVATION_SHA,
            "final_effective_evidence_audit_normalized_sha256": EXPECTED_EVIDENCE_V5_SHA,
            "object_identity_binding_normalized_sha256": EXPECTED_IDENTITY_SHA,
            "historical_reuse_exhaustion_normalized_sha256": EXPECTED_REUSE_EXHAUSTION_SHA,
            "owners_with_valid_component_evidence": EXPECTED_OWNER_COUNT,
            "independent_items_total": EXPECTED_EVIDENCE_ITEMS,
            "effective_wave_002_items": 48,
            "structured_repair_replaced_items": 6,
            "structured_repair_additional_items": 0,
            "structured_branch_coverage_complete": True,
        },
        "mastery_boundary": {
            "accepted_mapping_can_emit_partial_or_composite_evidence": True,
            "route_or_broad_composite_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
            "validated_exact_component_item_may_support_only_its_single_canonical_ref": True,
        },
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "scope": "FIPI_OGE_2026_CONTENT_CODE_6_14_CURRENT_EXACT_OWNER_FRONTIER_WITH_VALIDATED_COMPONENT_EVIDENCE",
        "status": "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_14_CANONICAL_COMPONENT_SET",
        "semantic_packet_sha256": EXPECTED_PACKET_SHA,
        "object_accounting_sha256": EXPECTED_ACCOUNTING_SHA,
        "decisions": [decision],
        "policy": {
            "reuse_first": True,
            "all_owners_derived_only_from_current_accepted_exact_orthography_authorities": True,
            "historical_placeholder_is_canonical_owner": False,
            "manufactured_fipi_subbranches_allowed": False,
            "new_school_canonical_identity_required": False,
            "component_specific_independent_evidence_required": True,
            "validated_component_evidence_required_before_object_acceptance": True,
            "generic_composite_attempt_can_exact_master_components": False,
            "keyword_or_fuzzy_mapping_allowed": False,
            "historical_reuse_proof_fingerprint_must_be_preserved": True,
            "structured_repair_is_replacement_only": True,
            "aggregate_delta_after_separate_acceptance_green": 1,
        },
        "summary": {
            "accepted_admission_units": 1,
            "accepted_requirements": 1,
            "accepted_content_codes": 1,
            "canonical_component_refs_unique": EXPECTED_OWNER_COUNT,
            "reused_current_canonical_owners": EXPECTED_OWNER_COUNT,
            "new_school_canonical_identities_materialized_in_current_authority_chain": 0,
            "independent_component_evidence_items": EXPECTED_EVIDENCE_ITEMS,
            "effective_wave_002_independent_items": 48,
            "structured_repair_replaced_items": 6,
            "structured_repair_additional_items": 0,
            "ru_proposal_identities_admitted": 0,
            "false_exact_mastery_admissions": 0,
        },
        "safety": {
            "accepted_demo_or_scorer_change": False,
            "tilda_change": False,
            "learner_audio_persistence": 0,
            "production_peis_write": False,
            "provider_execution": False,
            "public_traffic": False,
            "real_payment_or_refund": False,
            "real_message_delivery": False,
        },
    }
    result["normalized_sha256"] = normalized_sha(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_acceptance()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        s = result["summary"]
        print("RUSSIAN_OGE_6_14_CURRENT_EXACT_ACCEPTANCE_CANDIDATE=PASS")
        print("ADMISSION_UNIT_ID=" + EXPECTED_UNIT)
        print("REQUIREMENT_ID=" + EXPECTED_REQUIREMENT)
        print("PACKET_GROUP=" + EXPECTED_GROUP)
        print(f"EXACT_OWNER_FRONTIER={s['canonical_component_refs_unique']}")
        print(f"INDEPENDENT_COMPONENT_EVIDENCE_ITEMS={s['independent_component_evidence_items']}")
        print("AGGREGATE_DELTA_AFTER_SEPARATE_ACCEPTANCE_GREEN=1")
        print("FALSE_EXACT_MASTERY=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print("ACCEPTANCE_NORMALIZED_SHA256=" + result["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
