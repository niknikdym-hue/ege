#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
LEGACY_PATH = HERE / "RUSSIAN-SUBJECT-DISPOSITIONS-v0.1.json"
SET_PATHS = (
    HERE / "RUSSIAN-SUBJECT-REVIEWED-SETS-v0.1.json",
    HERE / "RUSSIAN-SUBJECT-REVIEWED-COMPOSITES-v0.1.json",
)
QUEUE_BUILDER = PROGRAM / "object-review" / "build_object_level_review_queue.py"
SEMANTIC_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

EXPECTED_QUEUE_SHA256 = "aa334efc455c68707d2d31de48b4364c879a619cf18dd07c9183d53890be5309"
EXPECTED_UNIT_TOTAL = 1325
EXPECTED_REQUIREMENT_TOTAL = 1400
ALLOWED_DISPOSITIONS = {
    "CANONICAL_SEMANTIC_COVERED",
    "PROPOSED_SEMANTIC_WITH_CONTENT",
    "NEW_PROPOSED_SEMANTIC_REQUIRED",
    "CONTENT_GAP",
    "PARTIAL_OR_COMPOSITE",
    "ROUTE_OR_FORMAT_ONLY",
    "RIGHTS_BLOCKED",
}
DERIVED_COMPOSITE_STATUS = "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_queue() -> dict[str, Any]:
    namespace = runpy.run_path(str(QUEUE_BUILDER))
    queue = namespace["build_queue"]()
    if queue.get("normalized_sha256") != EXPECTED_QUEUE_SHA256:
        raise ValueError("object-review queue authority drift")
    if queue.get("summary", {}).get("admission_units_total") != EXPECTED_UNIT_TOTAL:
        raise ValueError("admission-unit total drift")
    if queue.get("summary", {}).get("requirements_total") != EXPECTED_REQUIREMENT_TOTAL:
        raise ValueError("requirement total drift")
    return queue


def queue_row(unit: dict[str, Any]) -> dict[str, Any]:
    review = unit["admission_signature"]["review_signature"]
    member_rows = []
    for member in unit["members"]:
        member_rows.append(
            {
                "requirement_id": str(member["requirement_id"]),
                "source_locator": f"{member['source_id']}/{member['document_id']} p.{member['page']} {member['code']}",
                "source_id": str(member["source_id"]),
                "document_id": str(member["document_id"]),
                "page": int(member["page"]),
                "code": str(member["code"]),
                "grades": list(member["grades"]),
                "confidence": str(member["confidence"]),
            }
        )
    return {
        "admission_unit_id": str(unit["admission_unit_id"]),
        "requirement_class": str(review["requirement_class"]),
        "normalized_meaning": str(review["normalized_meaning"]),
        "modules": list(review["modules"]),
        "routes": list(review["routes"]),
        "priority_route": str(unit["priority_route"]),
        "members": member_rows,
    }


def load_candidate_refs() -> set[str]:
    payload = json.loads(SEMANTIC_INVENTORY.read_text(encoding="utf-8"))
    refs: set[str] = set()
    for row in payload.get("objects", []):
        if isinstance(row, dict) and row.get("source_system") == "semantic_candidate":
            source_id = row.get("source_id")
            if isinstance(source_id, str):
                refs.add(source_id)
    return refs


def content_contains_semantic(content_ref: str, semantic_ref: str) -> bool:
    path = PROGRAM / content_ref
    if not path.is_file():
        return False
    payload = json.loads(path.read_text(encoding="utf-8"))
    return any(
        isinstance(unit, dict) and unit.get("proposed_semantic_id") == semantic_ref
        for unit in payload.get("units", [])
    )


def derived_capability_components(meaning: str) -> list[dict[str, str]]:
    clauses = [clause.strip() for clause in meaning.split(". ") if clause.strip()]
    if len(clauses) < 2:
        raise ValueError("derived composite classification requires multiple exact capability clauses")
    result: list[dict[str, str]] = []
    for clause in clauses:
        label = clause if clause.endswith(".") else clause + "."
        digest = hashlib.sha256(label.encode("utf-8")).hexdigest()[:12]
        result.append(
            {
                "ref_kind": "review_capability_boundary",
                "ref": f"review-boundary:{digest}",
                "label": label,
                "status": DERIVED_COMPOSITE_STATUS,
            }
        )
    return result


def normalize_components(
    components: Any,
    *,
    disposition: str,
    expected_meaning: str | None,
    candidate_refs: set[str],
    set_id: str,
) -> list[dict[str, Any]]:
    if components is None and disposition == "PARTIAL_OR_COMPOSITE" and expected_meaning:
        components = derived_capability_components(expected_meaning)
    if disposition == "PARTIAL_OR_COMPOSITE" and (not isinstance(components, list) or not components):
        raise ValueError(f"PARTIAL_OR_COMPOSITE requires component refs: {set_id}")

    normalized: list[dict[str, Any]] = []
    for component in components or []:
        if not isinstance(component, dict):
            raise ValueError(f"invalid component in {set_id}")
        kind = str(component.get("ref_kind", ""))
        ref = str(component.get("ref", ""))
        status = str(component.get("status", ""))
        if kind == "existing_semantic_candidate":
            if ref not in candidate_refs or not status.endswith("NOT_ADMITTED_BY_THIS_SET"):
                raise ValueError(f"invalid existing candidate component {ref} in {set_id}")
        elif kind == "proposed_semantic_with_content":
            content_ref = str(component.get("content_ref", ""))
            if not ref.startswith("ru-") or status != "PROPOSED_NOT_CANONICAL":
                raise ValueError(f"proposed component self-admitted in {set_id}: {ref}")
            if not content_contains_semantic(content_ref, ref):
                raise ValueError(f"content ref does not materialize {ref}: {content_ref}")
        elif kind == "review_capability_boundary":
            if not ref.startswith("review-boundary:") or status != DERIVED_COMPOSITE_STATUS:
                raise ValueError(f"invalid non-semantic review boundary in {set_id}: {ref}")
            if not isinstance(component.get("label"), str) or not component["label"].strip():
                raise ValueError(f"review capability boundary lacks exact label in {set_id}")
        else:
            raise ValueError(f"unsupported component kind in {set_id}: {kind}")
        normalized.append(dict(component))
    return normalized


def build_ledger() -> dict[str, Any]:
    queue = load_queue()
    units = {str(unit["admission_unit_id"]): unit for unit in queue["admission_units"]}
    legacy = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    candidate_refs = load_candidate_refs()

    aggregate: list[dict[str, Any]] = []
    seen_units: set[str] = set()
    seen_requirements: set[str] = set()

    for record in legacy.get("dispositions", []):
        unit_id = str(record.get("admission_unit_id", ""))
        unit = units.get(unit_id)
        if unit is None:
            raise ValueError(f"legacy disposition references unknown unit {unit_id}")
        if unit_id in seen_units:
            raise ValueError(f"duplicate disposition for {unit_id}")
        exact = queue_row(unit)
        member_ids = [row["requirement_id"] for row in exact["members"]]
        if len(member_ids) != 1 or record.get("requirement_id") != member_ids[0]:
            raise ValueError(f"legacy requirement mismatch for {unit_id}")
        if record.get("disposition") != "ROUTE_OR_FORMAT_ONLY":
            raise ValueError(f"legacy slice may only contain ROUTE_OR_FORMAT_ONLY: {unit_id}")
        if record.get("semantic_identity_ref") is not None:
            raise ValueError(f"route/format legacy record created semantic identity: {unit_id}")
        aggregate.append(
            {
                **exact,
                "disposition": "ROUTE_OR_FORMAT_ONLY",
                "subject_review_status": "CENTRAL_BRAIN_ACCEPTED",
                "semantic_identity_ref": None,
                "component_refs": [],
                "decision_source": LEGACY_PATH.name,
                "decision_set_id": None,
                "rationale": "Exam structure/scoring/resource/route metadata; no learner semantic mastery.",
            }
        )
        seen_units.add(unit_id)
        for requirement_id in member_ids:
            if requirement_id in seen_requirements:
                raise ValueError(f"duplicate requirement disposition {requirement_id}")
            seen_requirements.add(requirement_id)

    seen_set_ids: set[str] = set()
    for set_path in SET_PATHS:
        reviewed = json.loads(set_path.read_text(encoding="utf-8"))
        if reviewed.get("object_review_queue_sha256") != EXPECTED_QUEUE_SHA256:
            raise ValueError(f"reviewed-set queue authority drift: {set_path.name}")
        sets = reviewed.get("reviewed_sets")
        if not isinstance(sets, list):
            raise ValueError(f"reviewed_sets must be a list: {set_path.name}")
        if set_path.name == "RUSSIAN-SUBJECT-REVIEWED-COMPOSITES-v0.1.json":
            summary = reviewed.get("summary", {})
            if summary != {
                "reviewed_sets": 26,
                "accepted_classification_units": 102,
                "accepted_classification_requirements": 104,
                "semantic_admissions": 0,
            }:
                raise ValueError("composite reviewed-set summary drift")

        for decision in sets:
            if not isinstance(decision, dict):
                raise ValueError("invalid reviewed-set row")
            set_id = str(decision.get("set_id", ""))
            if not set_id or set_id in seen_set_ids:
                raise ValueError(f"invalid/duplicate reviewed set id {set_id!r}")
            seen_set_ids.add(set_id)
            disposition = str(decision.get("disposition", ""))
            if disposition not in ALLOWED_DISPOSITIONS:
                raise ValueError(f"unsupported disposition in {set_id}: {disposition}")
            if decision.get("subject_review_status") != "CENTRAL_BRAIN_ACCEPTED_CLASSIFICATION":
                raise ValueError(f"reviewed set lacks Central Brain acceptance: {set_id}")
            unit_ids = decision.get("exact_admission_unit_ids")
            if not isinstance(unit_ids, list) or not unit_ids or len(unit_ids) != len(set(unit_ids)):
                raise ValueError(f"invalid exact unit ids in {set_id}")

            expected_meaning = decision.get("expected_normalized_meaning")
            if expected_meaning is not None and not isinstance(expected_meaning, str):
                raise ValueError(f"invalid expected normalized meaning in {set_id}")
            normalized_components = normalize_components(
                decision.get("components"),
                disposition=disposition,
                expected_meaning=expected_meaning,
                candidate_refs=candidate_refs,
                set_id=set_id,
            )
            mastery_boundary = decision.get("mastery_boundary")
            if mastery_boundary is None and disposition == "PARTIAL_OR_COMPOSITE":
                mastery_boundary = {
                    "generic_domain_attempt_can_emit_exact_component_mastery": False,
                    "generic_domain_attempt_can_emit_partial_or_composite_evidence": True,
                    "component_mastery_requires_component_specific_independent_evidence": True,
                }

            actual_requirement_ids: set[str] = set()
            for raw_unit_id in unit_ids:
                unit_id = str(raw_unit_id)
                if unit_id in seen_units:
                    raise ValueError(f"unit is dispositioned twice: {unit_id}")
                unit = units.get(unit_id)
                if unit is None:
                    raise ValueError(f"reviewed set references unknown unit {unit_id}")
                exact = queue_row(unit)
                if expected_meaning is not None and exact["normalized_meaning"] != expected_meaning:
                    raise ValueError(f"normalized meaning mismatch for {unit_id} in {set_id}")
                for member in exact["members"]:
                    requirement_id = str(member["requirement_id"])
                    if requirement_id in seen_requirements:
                        raise ValueError(f"requirement is dispositioned twice: {requirement_id}")
                    actual_requirement_ids.add(requirement_id)
                aggregate.append(
                    {
                        **exact,
                        "disposition": disposition,
                        "subject_review_status": "CENTRAL_BRAIN_ACCEPTED_CLASSIFICATION",
                        "semantic_identity_ref": None,
                        "component_refs": normalized_components,
                        "decision_source": set_path.name,
                        "decision_set_id": set_id,
                        "rationale": str(
                            decision.get(
                                "rationale",
                                "Exact official meaning spans multiple independently assessable capability boundaries; classification only, no semantic admission.",
                            )
                        ),
                        "mastery_boundary": mastery_boundary,
                        "route_authority_refs": decision.get("route_authority_refs", []),
                    }
                )
                seen_units.add(unit_id)
                for requirement_id in [str(member["requirement_id"]) for member in exact["members"]]:
                    seen_requirements.add(requirement_id)

            expected_requirement_ids = decision.get("exact_requirement_ids")
            if expected_requirement_ids is not None:
                if not isinstance(expected_requirement_ids, list) or len(expected_requirement_ids) != len(set(expected_requirement_ids)):
                    raise ValueError(f"invalid exact requirement list in {set_id}")
                if actual_requirement_ids != {str(value) for value in expected_requirement_ids}:
                    raise ValueError(f"exact requirement set mismatch in {set_id}")

    aggregate.sort(key=lambda row: str(row["admission_unit_id"]))
    by_disposition: dict[str, dict[str, int]] = {}
    for row in aggregate:
        bucket = by_disposition.setdefault(row["disposition"], {"admission_units": 0, "requirements": 0})
        bucket["admission_units"] += 1
        bucket["requirements"] += len(row["members"])

    payload: dict[str, Any] = {
        "schema_version": "0.3.0",
        "status": "RUSSIAN_FULL_SUBJECT_ACCEPTANCE_LEDGER_PARTIAL",
        "baseline_main": legacy.get("baseline_main"),
        "object_review_queue_sha256": queue["normalized_sha256"],
        "policy": {
            "every_disposition_is_exact_admission_unit_specific": True,
            "keyword_or_module_fanout_allowed": False,
            "review_batch_is_admission_authority": False,
            "component_ref_implies_semantic_admission": False,
        },
        "summary": {
            "admission_units_total": EXPECTED_UNIT_TOTAL,
            "requirements_total": EXPECTED_REQUIREMENT_TOTAL,
            "accepted_classification_units": len(seen_units),
            "accepted_classification_requirements": len(seen_requirements),
            "remaining_subject_review_units": EXPECTED_UNIT_TOTAL - len(seen_units),
            "remaining_subject_review_requirements": EXPECTED_REQUIREMENT_TOTAL - len(seen_requirements),
            "canonical_semantic_admissions": 0,
            "ru_proposal_admissions": 0,
            "false_exact_mastery_admissions": 0,
        },
        "by_disposition": dict(sorted(by_disposition.items())),
        "dispositions": aggregate,
    }
    payload["normalized_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = build_ledger()
    if args.output:
        Path(args.output).write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_SUBJECT_LEDGER_BUILD=PASS")
        print(f"normalized_sha256={payload['normalized_sha256']}")
        for key, value in payload["summary"].items():
            print(f"{key}={value}")
        for disposition, counts in payload["by_disposition"].items():
            print(f"{disposition}.admission_units={counts['admission_units']}")
            print(f"{disposition}.requirements={counts['requirements']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
