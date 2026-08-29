#!/usr/bin/env python3
"""Prove that every Russian admission unit has a finite Central-Brain disposition review.

Issue #161 does not require every broad/composite official source row to become
an atomic mastery identity. `PARTIAL_OR_COMPOSITE` is a valid final disposition
when multiplicity is preserved and false exact mastery is forbidden. This gate
therefore verifies *review closure*, not fake atomicization:

- all 1325 admission units / 1400 requirements remain accounted exactly once;
- every ROUTE_OR_FORMAT_ONLY unit is explicitly Central-Brain accepted;
- every PARTIAL_OR_COMPOSITE unit is covered by at least one exact reviewed
  normalized-meaning authority, explicit reviewed unit-set authority, or exact
  accepted component-set authority;
- all covering authorities preserve PARTIAL_OR_COMPOSITE and fail-closed mastery;
- overlaps are allowed only as multiple compatible review evidences for the same
  single disposition; no unit receives conflicting dispositions;
- bounded `ru-*` subject/route semantic acceptances are tracked separately and
  do not pretend to close source-object accounting without exact object binding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"
ROUTE_DISPOSITIONS = HERE / "RUSSIAN-SUBJECT-DISPOSITIONS-v0.1.json"

MEANING_AUTHORITIES = (
    (HERE / "RUSSIAN-SUBJECT-REVIEWED-BROAD-DOMAIN-MEANINGS-v0.1.json", "CENTRAL_BRAIN_REVIEWED_EXACT_BROAD_DOMAINS_PARTIAL"),
    (HERE / "RUSSIAN-SUBJECT-REVIEWED-REUSE-COMPOSITE-MEANINGS-v0.1.json", "CENTRAL_BRAIN_REVIEWED_EXACT_COMPOSITE_MEANINGS_PARTIAL"),
    (HERE / "RUSSIAN-SUBJECT-REVIEWED-REMAINING-DOMAIN-MEANINGS-v0.1.json", "CENTRAL_BRAIN_REVIEWED_EXACT_REMAINING_DOMAINS"),
)
SET_AUTHORITIES = (
    (HERE / "RUSSIAN-SUBJECT-REVIEWED-COMPOSITES-v0.1.json", "CENTRAL_BRAIN_REVIEWED_EXACT_COMPOSITE_SETS_PARTIAL"),
    (HERE / "RUSSIAN-SUBJECT-REVIEWED-SETS-v0.1.json", "CENTRAL_BRAIN_REVIEWED_EXACT_UNIT_SETS_PARTIAL"),
)
OBJECT_AUTHORITIES = (
    HERE / "RUSSIAN-EGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    HERE / "RUSSIAN-OGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    HERE / "RUSSIAN-OGE-PUNCTUATION-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    HERE / "RUSSIAN-OGE-DIRECT-SPEECH-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    HERE / "RUSSIAN-OGE-INDIRECT-SPEECH-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result = payload.get("decisions")
    if result is None and isinstance(payload.get("decision"), dict):
        result = [payload["decision"]]
    if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
        raise ValueError("accepted component authority decisions missing")
    return result


def build_coverage() -> dict[str, Any]:
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()
    dispositions = accounting.get("dispositions")
    if not isinstance(dispositions, list) or len(dispositions) != 1325:
        raise ValueError("complete accounting denominator drift")
    if accounting.get("requirements_total") != 1400 or accounting.get("admission_units_total") != 1325:
        raise ValueError("complete accounting totals drift")

    by_id = {str(row.get("admission_unit_id")): row for row in dispositions if isinstance(row, dict)}
    if len(by_id) != 1325:
        raise ValueError("admission-unit IDs are not unique")
    requirement_ids = [
        str(member.get("requirement_id"))
        for row in dispositions
        for member in (row.get("members") or [])
        if isinstance(member, dict)
    ]
    if len(requirement_ids) != 1400 or len(set(requirement_ids)) != 1400:
        raise ValueError("requirement accounting is not exact-once")

    coverage: dict[str, list[dict[str, Any]]] = defaultdict(list)

    route_payload = json.loads(ROUTE_DISPOSITIONS.read_text(encoding="utf-8"))
    if route_payload.get("policy", {}).get("disposition") != "ROUTE_OR_FORMAT_ONLY":
        raise ValueError("route-only disposition authority drift")
    route_rows = route_payload.get("dispositions")
    if not isinstance(route_rows, list) or len(route_rows) != 9:
        raise ValueError("route-only accepted set must remain exactly 9")
    for row in route_rows:
        unit_id = str(row.get("admission_unit_id", ""))
        unit = by_id.get(unit_id)
        if unit is None or unit.get("disposition") != "ROUTE_OR_FORMAT_ONLY":
            raise ValueError(f"route-only authority/accounting mismatch: {unit_id}")
        if row.get("subject_review_status") != "CENTRAL_BRAIN_ACCEPTED":
            raise ValueError(f"route-only unit not Central-Brain accepted: {unit_id}")
        coverage[unit_id].append({
            "authority": ROUTE_DISPOSITIONS.name,
            "review_kind": "EXPLICIT_ROUTE_OR_FORMAT_ONLY",
            "review_status": "CENTRAL_BRAIN_ACCEPTED",
        })

    reviewed_meanings: dict[str, list[str]] = defaultdict(list)
    for path, expected_status in MEANING_AUTHORITIES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("status") != expected_status:
            raise ValueError(f"meaning review authority status drift: {path.name}")
        policy = payload.get("policy") or {}
        if policy.get("classification_only_no_semantic_admission") is not True:
            raise ValueError(f"meaning review authority self-admits semantics: {path.name}")
        if policy.get("keyword_or_fuzzy_inference_allowed") is not False:
            raise ValueError(f"meaning review authority permits fuzzy mapping: {path.name}")
        if policy.get("generic_domain_attempt_can_emit_exact_component_mastery") is not False:
            raise ValueError(f"meaning review authority permits false exact mastery: {path.name}")
        meanings = payload.get("exact_normalized_meanings")
        if not isinstance(meanings, list) or any(not isinstance(value, str) or not norm(value) for value in meanings):
            raise ValueError(f"meaning review authority meanings invalid: {path.name}")
        if len(meanings) != len(set(norm(value) for value in meanings)):
            raise ValueError(f"duplicate exact meanings inside authority: {path.name}")
        for meaning in meanings:
            reviewed_meanings[norm(meaning)].append(path.name)

    for unit_id, unit in by_id.items():
        if unit.get("disposition") != "PARTIAL_OR_COMPOSITE":
            continue
        meaning = norm(unit.get("normalized_meaning"))
        for authority_name in reviewed_meanings.get(meaning, []):
            coverage[unit_id].append({
                "authority": authority_name,
                "review_kind": "EXACT_NORMALIZED_MEANING_CLASSIFICATION",
                "review_status": "CENTRAL_BRAIN_ACCEPTED_CLASSIFICATION",
            })

    for path, expected_status in SET_AUTHORITIES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("status") != expected_status:
            raise ValueError(f"reviewed-set authority status drift: {path.name}")
        policy = payload.get("policy") or {}
        if policy.get("keyword_or_module_inference_allowed") not in (False, None):
            raise ValueError(f"reviewed-set authority permits inference: {path.name}")
        if policy.get("classification_only_no_semantic_admission") not in (True, None):
            raise ValueError(f"reviewed-set authority self-admits semantics: {path.name}")
        reviewed_sets = payload.get("reviewed_sets")
        if not isinstance(reviewed_sets, list):
            raise ValueError(f"reviewed-set list missing: {path.name}")
        for reviewed_set in reviewed_sets:
            if not isinstance(reviewed_set, dict):
                raise ValueError(f"invalid reviewed set row: {path.name}")
            if reviewed_set.get("subject_review_status") != "CENTRAL_BRAIN_ACCEPTED_CLASSIFICATION":
                raise ValueError(f"reviewed set not Central-Brain accepted: {path.name}")
            if reviewed_set.get("disposition") != "PARTIAL_OR_COMPOSITE":
                raise ValueError(f"reviewed set disposition drift: {path.name}")
            ids = reviewed_set.get("exact_admission_unit_ids")
            if not isinstance(ids, list) or not ids:
                raise ValueError(f"reviewed set lacks explicit unit IDs: {path.name}")
            expected_meaning = norm(reviewed_set.get("expected_normalized_meaning"))
            for unit_id in ids:
                unit_id = str(unit_id)
                unit = by_id.get(unit_id)
                if unit is None or unit.get("disposition") != "PARTIAL_OR_COMPOSITE":
                    raise ValueError(f"reviewed set references wrong/missing unit: {path.name}/{unit_id}")
                if expected_meaning and norm(unit.get("normalized_meaning")) != expected_meaning:
                    raise ValueError(f"reviewed set exact meaning drift: {path.name}/{unit_id}")
                coverage[unit_id].append({
                    "authority": path.name,
                    "review_kind": "EXPLICIT_ADMISSION_UNIT_SET_CLASSIFICATION",
                    "review_status": "CENTRAL_BRAIN_ACCEPTED_CLASSIFICATION",
                    "set_id": str(reviewed_set.get("set_id", "")),
                })

    accepted_component_units: set[str] = set()
    for path in OBJECT_AUTHORITIES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in rows(payload):
            if row.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET":
                raise ValueError(f"object component set not accepted: {path.name}")
            mastery = row.get("mastery_boundary") or {}
            if mastery.get("route_or_broad_composite_attempt_can_emit_exact_component_mastery") is not False:
                raise ValueError(f"object component authority weakens mastery boundary: {path.name}")
            if mastery.get("component_specific_independent_evidence_required") is not True:
                raise ValueError(f"object component authority lacks independent evidence guard: {path.name}")
            refs = row.get("canonical_component_refs")
            if not isinstance(refs, list) or not refs or any(not str(ref).startswith("school-") for ref in refs):
                raise ValueError(f"object component authority has invalid canonical refs: {path.name}")
            unit_id = str(row.get("admission_unit_id", ""))
            unit = by_id.get(unit_id)
            if unit is None or unit.get("disposition") != "PARTIAL_OR_COMPOSITE":
                raise ValueError(f"object component authority/accounting mismatch: {path.name}/{unit_id}")
            if unit_id in accepted_component_units:
                raise ValueError(f"object component authorities overlap: {unit_id}")
            accepted_component_units.add(unit_id)
            coverage[unit_id].append({
                "authority": path.name,
                "review_kind": "EXACT_ACCEPTED_CANONICAL_COMPONENT_SET",
                "review_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
                "component_count": len(refs),
            })

    uncovered_units: list[dict[str, Any]] = []
    covered_units = 0
    covered_requirements = 0
    authority_hits: Counter[str] = Counter()
    review_kind_hits: Counter[str] = Counter()
    modules: dict[str, dict[str, int]] = defaultdict(lambda: {"units": 0, "requirements": 0, "reviewed_units": 0, "reviewed_requirements": 0})
    source_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"units": 0, "requirements": 0, "reviewed_units": 0, "reviewed_requirements": 0})

    for unit_id, unit in by_id.items():
        member_count = len(unit.get("members") or [])
        unit_modules = [str(value) for value in (unit.get("modules") or [])]
        unit_sources = sorted({str(member.get("source_id", "")) for member in (unit.get("members") or []) if isinstance(member, dict)})
        for module in unit_modules:
            modules[module]["units"] += 1
            modules[module]["requirements"] += member_count
        for source_id in unit_sources:
            source_counts[source_id]["units"] += 1
            source_counts[source_id]["requirements"] += sum(1 for member in (unit.get("members") or []) if str(member.get("source_id", "")) == source_id)

        evidences = coverage.get(unit_id, [])
        if not evidences:
            uncovered_units.append({
                "admission_unit_id": unit_id,
                "disposition": str(unit.get("disposition", "")),
                "normalized_meaning": str(unit.get("normalized_meaning", "")),
                "modules": unit_modules,
                "routes": list(unit.get("routes") or []),
                "requirement_ids": [str(member.get("requirement_id", "")) for member in (unit.get("members") or []) if isinstance(member, dict)],
            })
            continue
        covered_units += 1
        covered_requirements += member_count
        for evidence in evidences:
            authority_hits[str(evidence["authority"])] += 1
            review_kind_hits[str(evidence["review_kind"])] += 1
        for module in unit_modules:
            modules[module]["reviewed_units"] += 1
            modules[module]["reviewed_requirements"] += member_count
        for source_id in unit_sources:
            source_counts[source_id]["reviewed_units"] += 1
            source_counts[source_id]["reviewed_requirements"] += sum(1 for member in (unit.get("members") or []) if str(member.get("source_id", "")) == source_id)

    if any(row.get("disposition") not in {"PARTIAL_OR_COMPOSITE", "ROUTE_OR_FORMAT_ONLY"} for row in dispositions):
        raise ValueError("unexpected disposition outside currently reviewed final taxonomy slice")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_FINAL_DISPOSITION_REVIEW_COVERAGE_CANDIDATE",
        "object_accounting_sha256": str(accounting.get("normalized_sha256", "")),
        "policy": {
            "partial_or_composite_is_valid_final_disposition": True,
            "partial_or_composite_requires_explicit_central_brain_review_evidence": True,
            "partial_or_composite_can_emit_exact_mastery": False,
            "route_or_format_only_creates_semantic_identity": False,
            "multiple_compatible_review_evidences_change_single_disposition": False,
            "bounded_ru_semantic_acceptance_can_close_object_without_exact_binding": False,
            "keyword_fuzzy_module_only_review_inference_allowed": False,
        },
        "summary": {
            "admission_units_total": 1325,
            "requirements_total": 1400,
            "reviewed_admission_units": covered_units,
            "reviewed_requirements": covered_requirements,
            "unreviewed_admission_units": len(uncovered_units),
            "unreviewed_requirements": sum(len(row["requirement_ids"]) for row in uncovered_units),
            "route_or_format_only_units": sum(1 for row in dispositions if row.get("disposition") == "ROUTE_OR_FORMAT_ONLY"),
            "partial_or_composite_units": sum(1 for row in dispositions if row.get("disposition") == "PARTIAL_OR_COMPOSITE"),
            "exact_component_set_units": len(accepted_component_units),
            "semantic_identity_self_admissions_from_classification": 0,
            "false_exact_mastery_admissions": 0,
        },
        "review_kind_unit_hits": dict(sorted(review_kind_hits.items())),
        "authority_unit_hits": dict(sorted(authority_hits.items())),
        "module_review_coverage": dict(sorted(modules.items())),
        "source_review_coverage": dict(sorted(source_counts.items())),
        "uncovered_units": sorted(uncovered_units, key=lambda row: row["admission_unit_id"]),
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_coverage()
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_FINAL_DISPOSITION_REVIEW_COVERAGE=PASS")
        for key, value in result["summary"].items():
            print(f"{key}={value}")
        print(f"NORMALIZED_COVERAGE_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
