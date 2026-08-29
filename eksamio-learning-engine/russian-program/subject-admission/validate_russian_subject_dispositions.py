#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
LEDGER_PATH = HERE / "RUSSIAN-SUBJECT-DISPOSITIONS-v0.1.json"
QUEUE_BUILDER = PROGRAM / "object-review" / "build_object_level_review_queue.py"

EXPECTED_BASELINE = "0e7cb3cd05cd999ea97606d65cf5aef5625fcb3f"
EXPECTED_QUEUE_SHA256 = "aa334efc455c68707d2d31de48b4364c879a619cf18dd07c9183d53890be5309"
EXPECTED_UNIT_TOTAL = 1325
EXPECTED_REQUIREMENT_TOTAL = 1400
EXPECTED_ROUTE_ONLY_UNITS = 9
ROUTE_ONLY_CLASSES = {"exam_format_constraint", "scoring_or_format_constraint"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fail(message: str) -> None:
    raise SystemExit(f"RUSSIAN_SUBJECT_DISPOSITIONS_FAIL: {message}")


def main() -> int:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    builder_ns = runpy.run_path(str(QUEUE_BUILDER))
    queue = builder_ns["build_queue"]()

    if ledger.get("status") != "RUSSIAN_FULL_SUBJECT_ACCEPTANCE_CANDIDATE_PARTIAL":
        fail("candidate status drift")
    if ledger.get("baseline_main") != EXPECTED_BASELINE:
        fail("baseline main drift")
    authority = ledger.get("object_review_authority") or {}
    if authority.get("normalized_queue_sha256") != EXPECTED_QUEUE_SHA256:
        fail("ledger object-review hash drift")
    if queue.get("normalized_sha256") != EXPECTED_QUEUE_SHA256:
        fail("rebuilt object-review queue no longer matches accepted authority")
    if queue.get("summary", {}).get("admission_units_total") != EXPECTED_UNIT_TOTAL:
        fail("admission-unit total drift")
    if queue.get("summary", {}).get("requirements_total") != EXPECTED_REQUIREMENT_TOTAL:
        fail("requirement total drift")

    units = {str(unit["admission_unit_id"]): unit for unit in queue["admission_units"]}
    target_units = {
        unit_id: unit
        for unit_id, unit in units.items()
        if unit["admission_signature"]["review_signature"]["requirement_class"] in ROUTE_ONLY_CLASSES
    }
    if len(target_units) != EXPECTED_ROUTE_ONLY_UNITS:
        fail(f"expected {EXPECTED_ROUTE_ONLY_UNITS} route/format units, got {len(target_units)}")

    dispositions = ledger.get("dispositions")
    if not isinstance(dispositions, list) or len(dispositions) != EXPECTED_ROUTE_ONLY_UNITS:
        fail("ledger must contain exactly nine route/format dispositions")

    seen_units: set[str] = set()
    seen_requirements: set[str] = set()
    for record in dispositions:
        unit_id = str(record.get("admission_unit_id", ""))
        requirement_id = str(record.get("requirement_id", ""))
        if unit_id in seen_units or requirement_id in seen_requirements:
            fail("duplicate unit or requirement disposition")
        seen_units.add(unit_id)
        seen_requirements.add(requirement_id)

        unit = target_units.get(unit_id)
        if unit is None:
            fail(f"unknown or non-route/format unit {unit_id}")
        if int(unit.get("member_count", 0)) != 1 or len(unit.get("members", [])) != 1:
            fail(f"route/format unit {unit_id} must remain one exact requirement")
        member = unit["members"][0]
        review = unit["admission_signature"]["review_signature"]

        if requirement_id != member["requirement_id"]:
            fail(f"requirement mismatch for {unit_id}")
        if record.get("requirement_class") != review["requirement_class"]:
            fail(f"requirement class mismatch for {unit_id}")
        if record.get("normalized_meaning") != review["normalized_meaning"]:
            fail(f"meaning mismatch for {unit_id}")
        if record.get("modules") != review["modules"]:
            fail(f"module mismatch for {unit_id}")
        if record.get("routes") != review["routes"]:
            fail(f"route mismatch for {unit_id}")
        expected_locator = f"{member['source_id']}/{member['document_id']} p.{member['page']} {member['code']}"
        if record.get("source_locator") != expected_locator:
            fail(f"source locator mismatch for {unit_id}")
        if record.get("disposition") != "ROUTE_OR_FORMAT_ONLY":
            fail(f"invalid disposition for {unit_id}")
        if record.get("semantic_identity_ref") is not None:
            fail(f"route/format unit {unit_id} must not create semantic identity")
        if record.get("subject_review_status") != "CENTRAL_BRAIN_ACCEPTED":
            fail(f"route/format unit {unit_id} is not explicitly accepted")

    if seen_units != set(target_units):
        fail("route/format disposition set is incomplete")

    progress = ledger.get("progress") or {}
    if progress != {
        "accepted_units": 9,
        "accepted_requirements": 9,
        "remaining_units_subject_review_required": 1316,
        "remaining_requirements_subject_review_required": 1391,
    }:
        fail("progress totals drift")

    policy = ledger.get("policy") or {}
    if policy.get("semantic_identity_creation_allowed") is not False:
        fail("semantic identity creation must remain disabled for this slice")
    if int(policy.get("canonical_semantic_admissions", -1)) != 0:
        fail("this slice must not admit canonical semantics")
    if int(policy.get("ru_proposal_admissions", -1)) != 0:
        fail("this slice must not admit ru-* proposals")

    normalized_sha = hashlib.sha256(canonical_json(ledger)).hexdigest()
    print("RUSSIAN_SUBJECT_DISPOSITIONS=PASS")
    print(f"ROUTE_OR_FORMAT_ONLY_UNITS={len(seen_units)}")
    print(f"ROUTE_OR_FORMAT_ONLY_REQUIREMENTS={len(seen_requirements)}")
    print("CANONICAL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=0")
    print("FALSE_MASTERY_ADMISSIONS=0")
    print(f"REMAINING_SUBJECT_REVIEW_UNITS={EXPECTED_UNIT_TOTAL - len(seen_units)}")
    print(f"REMAINING_SUBJECT_REVIEW_REQUIREMENTS={EXPECTED_REQUIREMENT_TOTAL - len(seen_requirements)}")
    print(f"NORMALIZED_LEDGER_SHA256={normalized_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
