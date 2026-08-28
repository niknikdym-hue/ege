#!/usr/bin/env python3
from __future__ import annotations

import copy
from typing import Any

from build_object_level_review_queue import (
    EXPECTED_REQUIREMENTS,
    FORBIDDEN_SOURCE,
    PR139_HEAD,
    admission_signature,
    admission_unit_id,
    build_queue,
    exact_unit_resolution,
    load_exact_canonical_authority,
    load_requirements,
    review_batch_id,
    review_signature,
    route_priority,
)


def validate_contexts(contexts: list[dict[str, str]]) -> None:
    for context in contexts:
        if context.get("pr_head") != PR139_HEAD:
            raise AssertionError("PR #139 proposed context is not pinned to exact head")
        if context.get("authority") != "CONTEXT_ONLY_PROPOSED_NOT_CANONICAL":
            raise AssertionError("proposed context was promoted beyond context-only authority")


def validate_queue(queue: dict[str, Any]) -> None:
    index, rows = load_requirements()
    rows_by_id = {str(row[0]): row for row in rows}
    if len(rows_by_id) != EXPECTED_REQUIREMENTS:
        raise AssertionError("source requirement IDs are not unique")
    canonical_targets, direct = load_exact_canonical_authority()

    units = queue.get("admission_units", [])
    batches = queue.get("review_batches", [])
    if not units or not batches:
        raise AssertionError("object-level queue is empty")
    if queue.get("module_or_keyword_auto_resolution_allowed") is not False:
        raise AssertionError("module/keyword auto-resolution must remain forbidden")
    if queue.get("review_batch_authority") != "WORK_BATCH_ONLY_NOT_SEMANTIC_ADMISSION":
        raise AssertionError("review batch was promoted to admission authority")

    seen_requirements: set[str] = set()
    seen_units: set[str] = set()
    previous_unit_sort: tuple[int, int, str] | None = None
    resolved_units = 0
    resolved_requirements = 0
    context_units = 0
    context_requirements = 0
    review_units = 0
    review_requirements = 0

    for unit in units:
        signature = unit["admission_signature"]
        expected_unit_id = admission_unit_id(signature)
        if unit.get("admission_unit_id") != expected_unit_id:
            raise AssertionError("admission unit signature/id drift")
        review = signature["review_signature"]
        expected_batch_id = review_batch_id(review)
        if unit.get("review_batch_id") != expected_batch_id:
            raise AssertionError("admission unit review-batch link drift")
        expected_rank, expected_route = route_priority(review["routes"])
        if unit.get("priority_rank") != expected_rank or unit.get("priority_route") != expected_route:
            raise AssertionError("admission-unit priority drift")
        sort_key = (expected_rank, -int(unit["member_count"]), expected_unit_id)
        if previous_unit_sort is not None and sort_key < previous_unit_sort:
            raise AssertionError("admission-unit ordering drift")
        previous_unit_sort = sort_key

        members = unit.get("members", [])
        if not members or int(unit.get("member_count", 0)) != len(members):
            raise AssertionError("admission-unit member count drift")
        member_ids: list[str] = []
        expected_grades: set[str] = set()
        for member in members:
            requirement_id = str(member.get("requirement_id", ""))
            if requirement_id not in rows_by_id:
                raise AssertionError(f"unknown requirement in admission unit: {requirement_id}")
            if requirement_id in seen_requirements:
                raise AssertionError(f"duplicate requirement membership: {requirement_id}")
            seen_requirements.add(requirement_id)
            member_ids.append(requirement_id)
            row = rows_by_id[requirement_id]
            if admission_signature(row, index) != signature:
                raise AssertionError(f"incompatible requirement mixed into admission unit: {requirement_id}")
            document = index["catalogs"]["documents"][int(row[1])]
            source_id = str(document["source_id"])
            if source_id == FORBIDDEN_SOURCE or member.get("source_id") != source_id:
                raise AssertionError("provisional/wrong source in admission unit")
            if member.get("document_id") != document["document_id"] or member.get("source_sha256") != document["sha256"]:
                raise AssertionError("document identity/fingerprint drift")
            if int(member.get("page", 0)) != int(row[2]) or int(member.get("page", 0)) <= 0:
                raise AssertionError("missing/drifted page locator")
            if str(member.get("code", "")) != str(row[3]) or not str(member.get("code", "")).strip():
                raise AssertionError("missing/drifted code locator")
            expected_section = str(index["catalogs"]["sections"][int(row[4])])
            if member.get("section") != expected_section:
                raise AssertionError("section locator drift")
            row_grades = {str(value) for value in index["catalogs"]["grades"][int(row[6])]}
            if set(member.get("grades", [])) != row_grades:
                raise AssertionError("grade evidence drift")
            expected_grades.update(row_grades)
        if set(unit.get("grades_represented", [])) != expected_grades:
            raise AssertionError("admission-unit grade aggregate drift")

        exact = exact_unit_resolution(member_ids, direct, canonical_targets)
        status = unit.get("admission_status")
        target = unit.get("exact_canonical_semantic_id")
        if exact is None:
            if status != "SUBJECT_REVIEW_REQUIRED" or target is not None:
                raise AssertionError("module/keyword/context illegally auto-admitted an admission unit")
            review_units += 1
            review_requirements += len(members)
        else:
            if status != "AUTO_RESOLVED_CANONICAL" or target != exact:
                raise AssertionError("exact canonical auto-resolution drift")
            if exact not in canonical_targets or not exact.startswith("school-"):
                raise AssertionError("auto-resolution target is not canonical school identity")
            resolved_units += 1
            resolved_requirements += len(members)

        contexts = unit.get("proposed_context_refs", [])
        validate_contexts(contexts)
        if contexts:
            context_units += 1
            context_requirements += len(members)
        seen_units.add(expected_unit_id)

    if seen_requirements != set(rows_by_id) or len(seen_requirements) != EXPECTED_REQUIREMENTS:
        missing = sorted(set(rows_by_id) - seen_requirements)[:5]
        raise AssertionError(f"requirements not assigned exactly once: {missing}")
    if len(seen_units) != len(units):
        raise AssertionError("duplicate admission unit ID")

    units_by_batch: dict[str, list[dict[str, Any]]] = {}
    for unit in units:
        units_by_batch.setdefault(str(unit["review_batch_id"]), []).append(unit)

    seen_batch_units: set[str] = set()
    previous_batch_sort: tuple[int, int, str] | None = None
    context_batches = 0
    for batch in batches:
        review = batch["review_signature"]
        expected_batch_id = review_batch_id(review)
        if batch.get("review_batch_id") != expected_batch_id:
            raise AssertionError("review batch signature/id drift")
        if batch.get("authority") != "BATCH_ONLY_NOT_ADMISSION_DECISION":
            raise AssertionError("review batch authority drift")
        expected_rank, expected_route = route_priority(review["routes"])
        if batch.get("priority_rank") != expected_rank or batch.get("priority_route") != expected_route:
            raise AssertionError("review-batch priority drift")
        sort_key = (expected_rank, -int(batch["requirement_count"]), expected_batch_id)
        if previous_batch_sort is not None and sort_key < previous_batch_sort:
            raise AssertionError("review-batch ordering drift")
        previous_batch_sort = sort_key

        linked = units_by_batch.get(expected_batch_id, [])
        linked_ids = {str(unit["admission_unit_id"]) for unit in linked}
        if set(batch.get("admission_unit_ids", [])) != linked_ids:
            raise AssertionError("review batch admission-unit membership drift")
        if int(batch.get("admission_unit_count", 0)) != len(linked):
            raise AssertionError("review batch admission-unit count drift")
        if int(batch.get("requirement_count", 0)) != sum(int(unit["member_count"]) for unit in linked):
            raise AssertionError("review batch requirement count drift")
        for unit in linked:
            if unit["admission_signature"]["review_signature"] != review:
                raise AssertionError("review batch mixed incompatible semantic signatures")
            unit_id = str(unit["admission_unit_id"])
            if unit_id in seen_batch_units:
                raise AssertionError("admission unit appears in multiple review batches")
            seen_batch_units.add(unit_id)
        contexts = batch.get("proposed_context_refs", [])
        validate_contexts(contexts)
        if contexts:
            context_batches += 1

    if seen_batch_units != seen_units:
        raise AssertionError("not every admission unit is assigned to exactly one review batch")

    summary = queue["summary"]
    expected_summary = {
        "requirements_total": EXPECTED_REQUIREMENTS,
        "review_batches_total": len(batches),
        "admission_units_total": len(units),
        "auto_resolved_canonical_units": resolved_units,
        "auto_resolved_canonical_requirements": resolved_requirements,
        "proposed_context_batches": context_batches,
        "proposed_context_units": context_units,
        "proposed_context_requirements": context_requirements,
        "subject_review_required_units": review_units,
        "subject_review_required_requirements": review_requirements,
    }
    if summary != expected_summary:
        raise AssertionError(f"queue summary drift: {summary} != {expected_summary}")


def expect_failure(fn, label: str) -> None:
    try:
        fn()
    except AssertionError:
        return
    raise AssertionError(f"negative test did not fail: {label}")


def negative_tests(queue: dict[str, Any]) -> None:
    bad = copy.deepcopy(queue)
    bad["admission_units"][0]["members"].pop()
    bad["admission_units"][0]["member_count"] -= 1
    expect_failure(lambda: validate_queue(bad), "lost requirement")

    bad = copy.deepcopy(queue)
    duplicate = copy.deepcopy(bad["admission_units"][0]["members"][0])
    bad["admission_units"][1]["members"].append(duplicate)
    bad["admission_units"][1]["member_count"] += 1
    expect_failure(lambda: validate_queue(bad), "duplicate membership")

    bad = copy.deepcopy(queue)
    bad["admission_units"][0]["admission_unit_id"] = "RAU-tampered"
    expect_failure(lambda: validate_queue(bad), "admission unit signature drift")

    bad = copy.deepcopy(queue)
    bad["review_batches"][0]["review_batch_id"] = "RRB-tampered"
    expect_failure(lambda: validate_queue(bad), "review batch signature drift")

    bad = copy.deepcopy(queue)
    bad["admission_units"][0]["admission_signature"]["review_signature"]["normalized_meaning"] += " tampered"
    expect_failure(lambda: validate_queue(bad), "mixed incompatible meaning")

    bad = copy.deepcopy(queue)
    bad["admission_units"][0]["members"][0]["source_id"] = FORBIDDEN_SOURCE
    expect_failure(lambda: validate_queue(bad), "provisional 2027 source")

    bad = copy.deepcopy(queue)
    candidate = next(unit for unit in bad["admission_units"] if unit["admission_status"] == "SUBJECT_REVIEW_REQUIRED")
    candidate["admission_status"] = "AUTO_RESOLVED_CANONICAL"
    candidate["exact_canonical_semantic_id"] = "school-fake-module-keyword-match"
    expect_failure(lambda: validate_queue(bad), "module-only auto admission")

    bad = copy.deepcopy(queue)
    candidate = next(unit for unit in bad["admission_units"] if unit["admission_status"] == "SUBJECT_REVIEW_REQUIRED")
    candidate["admission_status"] = "AUTO_RESOLVED_CANONICAL"
    candidate["exact_canonical_semantic_id"] = "ru-proposed-fake"
    expect_failure(lambda: validate_queue(bad), "proposed identity marked canonical")

    bad = copy.deepcopy(queue)
    bad["admission_units"][0]["members"][0]["page"] = 0
    expect_failure(lambda: validate_queue(bad), "missing locator")

    bad = copy.deepcopy(queue)
    unit = bad["admission_units"][0]
    unit["admission_signature"]["code"] = str(unit["admission_signature"]["code"]) + ".tampered"
    expect_failure(lambda: validate_queue(bad), "code boundary drift")


def main() -> int:
    first = build_queue()
    second = build_queue()
    if first != second:
        raise AssertionError("object-level review queue is nondeterministic")
    validate_queue(first)
    negative_tests(first)
    print("RUSSIAN_OBJECT_LEVEL_REVIEW_QUEUE_VALIDATION=PASS")
    print(f"normalized_sha256={first['normalized_sha256']}")
    for key, value in first["summary"].items():
        print(f"{key}={value}")
    for key, value in first["by_priority_route"].items():
        print(f"priority[{key}].review_batches={value['review_batches']}")
        print(f"priority[{key}].admission_units={value['admission_units']}")
        print(f"priority[{key}].requirements={value['requirements']}")
    print("negative_tests=PASS")
    print("review_batches_are_admission_authority=FALSE")
    print("module_keyword_auto_resolution=FORBIDDEN")
    print("pr139_proposed_identity_admission=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
