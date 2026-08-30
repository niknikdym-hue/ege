#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
AUTHORITY = HERE / "RU13-EXPRESSIVE-EXISTING-CANDIDATES-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
BOUNDARY = HERE / "RU13-EXPRESSIVE-COMPONENT-BOUNDARY-REVIEW-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
REGISTRY_CONTRACT = ENGINE / "272-RUSSIAN-UNIFIED-SEMANTIC-IDENTITY-REGISTRY-CONTRACT-v1.0.txt"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-13-EXPRESSIVE-MEANS-WAVE-003-v0.1.json"

EXPECTED = {
    "candidate-033": ("device_assonance", "ru-expressive-assonance"),
    "candidate-034": ("device_hyperbole", "ru-expressive-hyperbole"),
    "candidate-035": ("device_metonymy", "ru-expressive-metonymy"),
    "candidate-036": ("device_anaphora", "ru-expressive-anaphora"),
    "candidate-037": ("device_parcellation", "ru-expressive-parcellation"),
    "candidate-038": ("device_homogeneous_rows", "ru-expressive-homogeneous-rows"),
    "candidate-039": ("device_address", "ru-expressive-address"),
    "candidate-040": ("device_epithet", "ru-expressive-epithet"),
    "candidate-041": ("device_metaphor", "ru-expressive-metaphor"),
    "candidate-042": ("device_comparison", "ru-expressive-comparison"),
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    contract = REGISTRY_CONTRACT.read_text(encoding="utf-8")

    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU13_EXISTING_CANDIDATE_BOUNDED_SUBJECT_SEMANTICS":
        raise AssertionError("RU13 existing-candidate acceptance status drift")
    if authority.get("canonical_school_registry_mutated") is not False or authority.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU13 existing-candidate acceptance must remain an overlay")
    if authority.get("registry_contract_ref") != REGISTRY_CONTRACT.name:
        raise AssertionError("RU13 registry contract ref drift")
    for required_text in (
        "New subject-level identities must use a stable namespace",
        "ru-<domain>-<stable-slug>",
        "Never create a new `ru-*` identity when an existing `school-*` identity already expresses the same canonical decision.",
        "The EGE Skill Graph must remain a valid exam/product taxonomy.",
        "It must NOT be promoted unchanged into the universal subject identity registry.",
    ):
        if required_text not in contract:
            raise AssertionError("unified registry contract drift")

    summary = authority.get("summary") or {}
    expected_summary = {
        "accepted_bounded_subject_semantics": 10,
        "accepted_ru_subject_semantics": 10,
        "source_verified_candidates_consumed": 10,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }
    if summary != expected_summary:
        raise AssertionError(f"RU13 existing-candidate summary drift: {summary}")

    policy = authority.get("policy") or {}
    required_true = {
        "source_verified_taxonomy_required",
        "existing_missing_subject_candidate_required",
        "school_duplicate_forbidden",
        "component_specific_independent_evidence_required",
        "rhetorical_address_duplicate_forbidden",
    }
    for key in required_true:
        if policy.get(key) is not True:
            raise AssertionError(f"RU13 existing-candidate policy weakened: {key}")
    for key in (
        "ege_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
        "generic_expressive_attempt_can_emit_exact_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"RU13 existing-candidate fail-closed policy weakened: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU13 new subject identity namespace drift")

    decisions = authority.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 10:
        raise AssertionError("RU13 existing-candidate acceptance must contain 10 decisions")
    by_candidate = {str(row.get("candidate_ref")): row for row in decisions if isinstance(row, dict)}
    if set(by_candidate) != set(EXPECTED):
        raise AssertionError("RU13 accepted candidate set drift")
    accepted_ids = {str(row.get("accepted_semantic_id")) for row in decisions}
    if accepted_ids != {semantic_id for _, semantic_id in EXPECTED.values()}:
        raise AssertionError("RU13 accepted stable semantic id set drift")
    if any(not semantic_id.startswith("ru-expressive-") for semantic_id in accepted_ids):
        raise AssertionError("RU13 accepted id escaped stable ru-expressive namespace")
    if "ru-expressive-rhetorical-address" in accepted_ids:
        raise AssertionError("duplicate rhetorical-address semantic admitted")

    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    canonical_school = {
        str(row.get("source_id"))
        for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and row.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
        and row.get("review_status") == "reviewed"
    }
    if len(canonical_school) != 185:
        raise AssertionError(f"frozen school denominator drift: {len(canonical_school)}")
    if canonical_school & accepted_ids:
        raise AssertionError("RU13 accepted subject id duplicates a school canonical id")

    legacy_current_refs = {
        str(ref)
        for row in objects
        for ref in (row.get("current_semantic_refs") or [])
        if isinstance(ref, str)
    }
    # Exact stable ids are new materializations; pre-existing exact-id collision is forbidden.
    if legacy_current_refs & accepted_ids:
        raise AssertionError("RU13 new stable semantic id already existed in the inventoried legacy refs")

    content_units = content.get("units")
    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or not isinstance(content_units, list) or len(content_units) != 10:
        raise AssertionError("RU13 existing-candidate learner-content boundary drift")
    content_by_candidate = {
        str(row.get("semantic_candidate_ref")): row
        for row in content_units
        if isinstance(row, dict)
    }
    if set(content_by_candidate) != set(EXPECTED):
        raise AssertionError("RU13 existing-candidate content set drift")
    if (content.get("authority") or {}).get("admission_unit_binding") != "PENDING_EXACT_OBJECT_LEVEL_DISPOSITION":
        raise AssertionError("RU13 source content falsely claims object-level closure")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_source_bytes_in_git") != 0:
        raise AssertionError("RU13 existing-candidate content violates source-byte guard")

    boundary_existing = boundary.get("existing_candidate_components")
    if not isinstance(boundary_existing, list) or len(boundary_existing) != 10:
        raise AssertionError("RU13 boundary no longer exposes ten existing candidate components")
    boundary_by_candidate = {str(row.get("ref")): row for row in boundary_existing if isinstance(row, dict)}
    if set(boundary_by_candidate) != set(EXPECTED):
        raise AssertionError("RU13 boundary candidate set drift")

    for candidate_ref, (source_id, semantic_id) in EXPECTED.items():
        decision = by_candidate[candidate_ref]
        if decision.get("source_taxonomy_id") != source_id or decision.get("accepted_semantic_id") != semantic_id:
            raise AssertionError(f"RU13 candidate acceptance binding drift: {candidate_ref}")
        if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
            raise AssertionError(f"RU13 candidate not explicitly accepted: {candidate_ref}")
        if decision.get("entity_type") != "RECOGNITION_SKILL":
            raise AssertionError(f"RU13 expressive entity type drift: {candidate_ref}")
        if len(str(decision.get("boundary_guard", ""))) < 30:
            raise AssertionError(f"RU13 accepted candidate lacks bounded definition: {candidate_ref}")

        candidate_rows = [row for row in objects if row.get("object_key") == f"semantic_candidate::{candidate_ref}"]
        if len(candidate_rows) != 1:
            raise AssertionError(f"RU13 semantic candidate inventory mismatch: {candidate_ref}")
        candidate = candidate_rows[0]
        if candidate.get("authority_status") != "current" or candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
            raise AssertionError(f"RU13 candidate is not a current missing subject semantic: {candidate_ref}")
        if candidate.get("candidate_canonical_owner") != candidate_ref or candidate.get("current_semantic_refs") != [source_id]:
            raise AssertionError(f"RU13 candidate exact source binding drift: {candidate_ref}")

        taxonomy_rows = [
            row for row in objects
            if row.get("candidate_canonical_owner") == candidate_ref
            and row.get("source_id") == source_id
            and row.get("audit_classification") == "EGE_TAXONOMY_NODE"
        ]
        if len(taxonomy_rows) != 1:
            raise AssertionError(f"RU13 source taxonomy evidence mismatch: {candidate_ref}")
        taxonomy = taxonomy_rows[0]
        if taxonomy.get("authority_status") != "current" or taxonomy.get("review_status") != "source_verified":
            raise AssertionError(f"RU13 taxonomy evidence is not current/source-verified: {candidate_ref}")
        expected_provenance = f"03-RUSSIAN-SKILL-GRAPH.json#skills[{source_id}]"
        if expected_provenance not in set(taxonomy.get("evidence_provenance_refs") or []):
            raise AssertionError(f"RU13 taxonomy provenance drift: {candidate_ref}")

        unit = content_by_candidate[candidate_ref]
        if unit.get("source_semantic_ref") != source_id:
            raise AssertionError(f"RU13 learner content source ref drift: {candidate_ref}")
        if unit.get("proposed_semantic_id") is not None:
            raise AssertionError(f"RU13 source bundle independently invented a duplicate stable id: {candidate_ref}")
        peis = unit.get("peis_evidence") or {}
        if peis.get("semantic_ref_status") != "EXISTING_CANDIDATE_NOT_CANONICAL" or peis.get("independent_verification_required") is not True:
            raise AssertionError(f"RU13 source learner-content evidence guard drift: {candidate_ref}")
        verification = unit.get("independent_verification")
        if not isinstance(verification, list) or len(verification) < 2:
            raise AssertionError(f"RU13 source learner content lacks independent verification: {candidate_ref}")

        boundary_row = boundary_by_candidate[candidate_ref]
        if boundary_row.get("source_id") != source_id:
            raise AssertionError(f"RU13 component boundary source drift: {candidate_ref}")

    c039 = by_candidate["candidate-039"]
    if c039.get("accepted_semantic_id") != "ru-expressive-address":
        raise AssertionError("candidate-039 accepted owner drift")
    non_acceptances = authority.get("explicit_non_acceptances") or []
    if not any(row.get("semantic_ref") == "ru-expressive-rhetorical-address" for row in non_acceptances if isinstance(row, dict)):
        raise AssertionError("RU13 rhetorical-address duplicate guard missing")

    serialized = canonical_bytes(authority)
    if b'"object_level_admission_units_closed":1' in serialized or b'"object_level_requirements_closed":1' in serialized:
        raise AssertionError("RU13 existing-candidate acceptance falsely closes object accounting")

    print("RU13_EXISTING_CANDIDATE_BOUNDED_SUBJECT_SEMANTICS=PASS")
    print("ACCEPTED_BOUNDED_SUBJECT_SEMANTICS=10")
    print("SOURCE_VERIFIED_CANDIDATES_CONSUMED=10")
    print("NEW_SCHOOL_CANONICAL_IDENTITIES=0")
    print("EGE_TAXONOMY_IDS_PROMOTED_UNCHANGED=0")
    print("CANDIDATE_IDS_USED_AS_SEMANTIC_IDS=0")
    print("OBJECT_LEVEL_ADMISSION_UNITS_CLOSED=0")
    print("OBJECT_LEVEL_REQUIREMENTS_CLOSED=0")
    print("RHETORICAL_ADDRESS_DUPLICATE=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("ACCEPTANCE_SHA256=" + hashlib.sha256(canonical_bytes(authority)).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
