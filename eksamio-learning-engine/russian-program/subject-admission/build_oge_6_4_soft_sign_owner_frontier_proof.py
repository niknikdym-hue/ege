#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from build_oge_6_4_soft_sign_owner_resolution_review import build_review

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
ROSENTHAL_FREEZE = ENGINE / "259-RUSSIAN-SCHOOL-ROSENTHAL-PRIMARY-COMPLETENESS-FINAL-FREEZE-v1.0.json"
FIPI_REOPEN_AUDIT = ENGINE / "262-RUSSIAN-FIPI-2026-SCHOOL-REOPEN-GAP-AUDIT-v0.1.json"
FINAL_REFREEZE = ENGINE / "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json"

TARGET_CODE = "6.4"
TARGET_TOPIC = "Ъ and Ь including separating signs"
PROVEN_OWNER_REFS = [
    "school-separating-hard-soft-sign-boundary",
    "school-verb-soft-sign-forms",
    "school-numeral-orthography-base",
    "school-adverb-final-soft-sign-after-sibilant-base",
]
ADJACENT_CODE_NONOWNERS = [
    "school-adjective-soft-sign-before-sk-base",
    "school-noun-agent-suffix-chik-shchik-soft-sign",
    "school-noun-genitive-plural-ending-system",
]
NO_EXACT_ROUTE_BINDING = [
    "school-verbal-noun-nie-nye-semantic-boundary",
]


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def build_proof() -> dict[str, Any]:
    review = build_review()
    rosenthal = load_json(ROSENTHAL_FREEZE)
    reopen = load_json(FIPI_REOPEN_AUDIT)
    refreeze = load_json(FINAL_REFREEZE)

    if review["target"]["content_code"] != TARGET_CODE or review["target"]["topic"] != TARGET_TOPIC:
        raise ValueError("OGE 6.4 review target drift")
    if review["source_bound_frontier"]["still_unresolved_candidates"] != []:
        raise ValueError("OGE 6.4 still has unresolved reviewed overlap candidates")

    supported = review["source_bound_frontier"]["fipi_supported_6_4_owner_candidates_not_yet_admitted"]
    if supported != [
        "school-adverb-final-soft-sign-after-sibilant-base",
        "school-numeral-orthography-base",
    ]:
        raise ValueError("OGE 6.4 FIPI-supported candidate set drift")
    if review["source_bound_frontier"]["adjacent_code_nonowner_candidates"] != ADJACENT_CODE_NONOWNERS:
        raise ValueError("OGE 6.4 adjacent-code nonowner set drift")
    if review["source_bound_frontier"]["no_exact_oge_2026_route_binding_candidates"] != NO_EXACT_ROUTE_BINDING:
        raise ValueError("OGE 6.4 no-exact-binding set drift")

    source_paragraphs = review["official_source_review"]["navigator"]["source_attested_soft_sign_paragraphs"]
    if len(source_paragraphs) != 4:
        raise ValueError("official OGE 6.4 source-attested decision frontier drift")

    rosenthal_closure = rosenthal.get("source_topic_closure") or {}
    if rosenthal_closure.get("orthography_unresolved") != 0:
        raise ValueError("Rosenthal orthography source closure reopened")
    if rosenthal_closure.get("candidate_families_unresolved") != 0:
        raise ValueError("Rosenthal candidate-family closure reopened")
    if rosenthal_closure.get("open_holds") != 0:
        raise ValueError("Rosenthal source closure has open holds")

    reopen_checked = [str(value) for value in reopen.get("exam_topics_checked_and_not_reopened") or []]
    if not any("hard/soft signs" in value and "existing owners" in value for value in reopen_checked):
        raise ValueError("FIPI reopen audit no longer records hard/soft signs as existing-owner coverage")
    if (reopen.get("count_assertion") or {}).get("projected_school_denominator_after_admission") != 185:
        raise ValueError("FIPI reopen denominator projection drift")

    if refreeze.get("final_school_canonical_denominator") != 185:
        raise ValueError("final school denominator drift")
    final_closure = refreeze.get("final_source_closure") or {}
    required_zeroes = [
        "rosenthal_unresolved_after_259",
        "ege_2026_second_pass_school_reopen_candidates",
        "oge_2026_second_pass_school_reopen_candidates",
        "final_unowned_official_school_orthography_topics",
        "open_holds",
    ]
    for key in required_zeroes:
        if final_closure.get(key) != 0:
            raise ValueError(f"final school/FIPI closure reopened: {key}")
    if final_closure.get("fipi_pre_reopen_school_gaps") != 6 or final_closure.get("fipi_gaps_materialized") != 6:
        raise ValueError("FIPI school-gap materialization count drift")

    explicit = review["current_overlay_truth"]["explicit_canonical_refs"]
    if explicit != PROVEN_OWNER_REFS[:2]:
        raise ValueError("current OGE 6.4 explicit overlay refs drift")
    if review["current_overlay_truth"]["unresolved_placeholder_present"] is not True:
        raise ValueError("expected unresolved OGE 6.4 placeholder is missing before source sync")
    if review["exact_acceptance_truth"]["current_exact_acceptance_for_6_4"] is not False:
        raise ValueError("OGE 6.4 was accepted before source synchronization proof completed")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "SOURCE_BOUND_OWNER_FRONTIER_PROVEN_SOURCE_SYNC_REQUIRED",
        "authority_issue": 161,
        "target": {
            "document_id": "OGE_COD",
            "content_code": TARGET_CODE,
            "topic": TARGET_TOPIC,
        },
        "proof_basis": {
            "official_fipi_6_4_decision_branches": source_paragraphs,
            "rosenthal_primary_source_unresolved": rosenthal_closure["orthography_unresolved"],
            "rosenthal_candidate_families_unresolved": rosenthal_closure["candidate_families_unresolved"],
            "fipi_reopen_audit_hard_soft_signs_existing_owner_coverage": True,
            "final_school_canonical_denominator": refreeze["final_school_canonical_denominator"],
            "oge_2026_second_pass_school_reopen_candidates": final_closure["oge_2026_second_pass_school_reopen_candidates"],
            "final_unowned_official_school_orthography_topics": final_closure["final_unowned_official_school_orthography_topics"],
            "final_open_holds": final_closure["open_holds"],
        },
        "proven_exact_owner_frontier": {
            "canonical_refs": PROVEN_OWNER_REFS,
            "source_bound_frontier_complete": True,
            "new_school_identity_required": False,
            "existing_explicit_refs": PROVEN_OWNER_REFS[:2],
            "supported_existing_refs_to_add": PROVEN_OWNER_REFS[2:],
        },
        "proven_nonowners": {
            "adjacent_code_nonowners": ADJACENT_CODE_NONOWNERS,
            "no_exact_oge_2026_route_binding": NO_EXACT_ROUTE_BINDING,
        },
        "current_repository_sync_state": {
            "overlay_placeholder_present": True,
            "overlay_exact_owner_list_complete": False,
            "identity_inventory_exact_owner_list_complete": False,
            "exact_component_acceptance_present": False,
            "source_sync_required": True,
        },
        "policy": {
            "reuse_first": True,
            "no_new_school_identity_for_6_4": True,
            "frontier_proof_is_semantic_admission": False,
            "frontier_proof_may_delete_placeholder_without_sync": False,
            "overlay_inventory_and_exact_authority_must_be_synchronized_atomically": True,
            "component_mastery_requires_component_specific_evidence": True,
        },
        "summary": {
            "proven_exact_owner_refs": len(PROVEN_OWNER_REFS),
            "adjacent_code_nonowners": len(ADJACENT_CODE_NONOWNERS),
            "no_exact_route_binding_nonowners": len(NO_EXACT_ROUTE_BINDING),
            "remaining_source_boundary_unknowns": 0,
            "semantic_admissions": 0,
            "object_level_closures": 0,
            "false_exact_mastery_admissions": 0,
        },
        "admission_effect": "NONE",
        "next_safe_step": "Synchronize OGE 6.4 to exactly the four proven canonical refs in the route overlay and identity inventory, remove the generic placeholder, then regenerate exact component acceptance and run fail-closed exact-head CI. Do not emit component mastery before that synchronized gate is green.",
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_proof()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("OGE_6_4_SOFT_SIGN_OWNER_FRONTIER_PROOF=PASS")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
        print("PROVEN_EXACT_OWNER_REFS=4")
        print("REMAINING_SOURCE_BOUNDARY_UNKNOWNS=0")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_LEVEL_CLOSURES=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
