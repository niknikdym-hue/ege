#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
TRACKED = HERE / "RU16-TASK27-BOUNDED-ROUTE-SEMANTIC-ACCEPTANCE-v0.1.json"
BUILDER = HERE / "build_ru16_task27_route_semantic_acceptance.py"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
BOUNDARY = HERE / "RU16-ESSAY-COMPONENT-BOUNDARY-REVIEW-v0.1.json"

EXPECTED = {
    "candidate-048": ("ru-ege-essay-author-position", "K1"),
    "candidate-049": ("ru-ege-essay-source-examples-explanation", "K2_COMPONENT"),
    "candidate-050": ("ru-ege-essay-example-semantic-relation", "K2_COMPONENT"),
    "candidate-051": ("ru-ege-essay-own-relation-justification", "K3"),
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    tracked = json.loads(TRACKED.read_text(encoding="utf-8"))
    generated = runpy.run_path(str(BUILDER))["build_acceptance"]()
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))

    if tracked.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU16_TASK27_K1_K3_ROUTE_SEMANTICS":
        raise AssertionError("tracked RU16 acceptance status drift")
    if tracked.get("canonical_school_registry_mutated") is not False or tracked.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU16 acceptance must be an overlay, not a second/canonical registry mutation")

    expected_summary = {
        "accepted_route_semantics": 4,
        "accepted_criteria_routes": 3,
        "k2_semantic_components": 2,
        "accepted_ru_route_semantics": 4,
        "new_school_canonical_identities": 0,
        "k4_k6_acceptances": 0,
        "k7_k10_acceptances": 0,
        "false_exact_mastery_admissions": 0,
    }
    if tracked.get("summary") != expected_summary:
        raise AssertionError(f"RU16 tracked acceptance summary drift: {tracked.get('summary')}")
    if generated.get("summary", {}).get("accepted_route_semantics") != 4:
        raise AssertionError("derived RU16 acceptance no longer proves four semantics")
    if generated.get("summary", {}).get("false_exact_mastery_admissions") != 0:
        raise AssertionError("derived RU16 acceptance permits false exact mastery")

    tracked_decisions = {
        str(row.get("candidate_ref")): row
        for row in tracked.get("decisions", [])
        if isinstance(row, dict)
    }
    generated_decisions = {
        str(row.get("candidate_ref")): row
        for row in generated.get("decisions", [])
        if isinstance(row, dict)
    }
    if set(tracked_decisions) != set(EXPECTED) or set(generated_decisions) != set(EXPECTED):
        raise AssertionError("RU16 accepted candidate set drift")
    for candidate_ref, (semantic_id, criterion_route) in EXPECTED.items():
        tracked_row = tracked_decisions[candidate_ref]
        generated_row = generated_decisions[candidate_ref]
        if tracked_row.get("accepted_semantic_id") != semantic_id or generated_row.get("accepted_semantic_id") != semantic_id:
            raise AssertionError(f"RU16 accepted semantic drift: {candidate_ref}")
        if tracked_row.get("criterion_route") != criterion_route:
            raise AssertionError(f"RU16 tracked criterion route drift: {candidate_ref}")
        generated_criterion = generated_row.get("criterion_route")
        expected_generated = "K2" if criterion_route == "K2_COMPONENT" else criterion_route
        if generated_criterion != expected_generated:
            raise AssertionError(f"RU16 derived criterion route drift: {candidate_ref}")
        if tracked_row.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_ROUTE_SEMANTIC":
            raise AssertionError(f"RU16 tracked semantic not explicitly accepted: {candidate_ref}")
        mastery = str(tracked_row.get("mastery_boundary", ""))
        if "mastery" not in mastery.casefold() and "K2" not in mastery:
            raise AssertionError(f"RU16 mastery boundary missing: {candidate_ref}")

    authority = tracked.get("authority", {})
    if authority.get("tier_a_fipi_spec_sha256") != "3b71ec81f954bc32b574a0b3b997ee37bb3bc19ae8825f11217fd7149198b476":
        raise AssertionError("RU16 Tier-A source fingerprint drift")
    if authority.get("tier_a_locator") != "printed_page=20;pdf_page=10;panel=right;task=27":
        raise AssertionError("RU16 Task-27 exact locator drift")
    if set(authority.get("tier_a_content_codes") or []) != {"1.4", "1.5"}:
        raise AssertionError("RU16 Task-27 content-code scope drift")
    if set(authority.get("tier_a_checked_requirement_codes") or []) != {"1.5", "1.7"}:
        raise AssertionError("RU16 Task-27 requirement-code scope drift")
    if authority.get("tier_a_max_primary_score") != 22:
        raise AssertionError("RU16 Task-27 score authority drift")

    nonaccepted = {
        str(row.get("candidate_ref")): row
        for row in tracked.get("explicit_non_acceptances", [])
        if isinstance(row, dict)
    }
    if set(nonaccepted) != {"candidate-052", "candidate-053", "candidate-054", "candidate-055"}:
        raise AssertionError("RU16 explicit non-acceptance set drift")
    if nonaccepted["candidate-054"].get("criterion_route") != "K4":
        raise AssertionError("candidate-054 K4 guard drift")
    if nonaccepted["candidate-053"].get("criterion_route") != "K9_CONTRIBUTOR_ONLY":
        raise AssertionError("candidate-053 narrow K9 contributor guard drift")

    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    c54 = [row for row in objects if row.get("object_key") == "semantic_candidate::candidate-054"]
    if len(c54) != 1 or c54[0].get("review_status") != "needs_review":
        raise AssertionError("candidate-054 granularity review was silently closed")
    c53 = [row for row in objects if row.get("object_key") == "semantic_candidate::candidate-053"]
    if len(c53) != 1 or set(c53[0].get("current_semantic_refs") or []) != {"comparison_degree_forms"}:
        raise AssertionError("candidate-053 narrow morphology truth drift")

    cross = tracked.get("cross_module_non_acceptances")
    if not isinstance(cross, list) or {row.get("criterion_route") for row in cross if isinstance(row, dict)} != {"K7", "K8", "K9", "K10"}:
        raise AssertionError("RU16 K7-K10 pending reuse set drift")
    if any(row.get("status") != "EXACT_COMPONENT_REUSE_PENDING" for row in cross):
        raise AssertionError("RU16 K7-K10 was silently admitted")

    k2 = boundary.get("k2_decomposition", {})
    if set(k2.get("components") or []) != {
        "ru-ege-essay-source-examples-explanation",
        "ru-ege-essay-example-semantic-relation",
    }:
        raise AssertionError("RU16 K2 decomposition collapsed")
    c053_guard = boundary.get("candidate_053_guard", {})
    if c053_guard.get("status") != "NARROW_GRAMMAR_CONTRIBUTOR_ONLY_NOT_K9_OWNER":
        raise AssertionError("RU16 candidate-053 boundary broadened")

    serialized = canonical_json(tracked).replace(b" ", b"")
    for forbidden in (
        b"ru-essay-language-correctness",
        b'"k4_k6_acceptances":1',
        b'"k7_k10_acceptances":1',
        b'"canonical_school_registry_mutated":true',
    ):
        if forbidden in serialized:
            raise AssertionError("RU16 bounded acceptance violated a hard boundary")

    print("RU16_TASK27_BOUNDED_ROUTE_SEMANTIC_ACCEPTANCE=PASS")
    print("ACCEPTED_ROUTE_SEMANTICS=4")
    print("K1_ACCEPTED_COMPONENTS=1")
    print("K2_ACCEPTED_COMPONENTS=2")
    print("K3_ACCEPTED_COMPONENTS=1")
    print("K4_K6_ACCEPTANCES=0")
    print("K7_K10_ACCEPTANCES=0")
    print("CANDIDATE_054_GRANULARITY_REVIEW_OPEN=1")
    print("CANDIDATE_053_GENERAL_K9_OWNER=0")
    print("NEW_SCHOOL_CANONICAL_IDENTITIES=0")
    print("TRACKED_ACCEPTANCE_SHA256=" + hashlib.sha256(canonical_json(tracked)).hexdigest())
    print("DERIVED_ACCEPTANCE_SHA256=" + str(generated["normalized_sha256"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
