#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from build_object_level_review_queue import (
    EXPECTED_REQUIREMENTS,
    FORBIDDEN_SOURCE,
    PR139_HEAD,
    build_queue,
    exact_group_resolution,
    group_signature,
    load_exact_canonical_authority,
    load_requirements,
    review_group_id,
    route_priority,
)


def validate_queue(queue: dict[str, Any]) -> None:
    index, rows = load_requirements()
    rows_by_id = {str(row[0]): row for row in rows}
    if len(rows_by_id) != EXPECTED_REQUIREMENTS:
        raise AssertionError("source requirement IDs are not unique")
    canonical_targets, direct = load_exact_canonical_authority()

    groups = queue.get("groups", [])
    if not groups:
        raise AssertionError("review queue is empty")
    if queue.get("module_or_keyword_auto_resolution_allowed") is not False:
        raise AssertionError("module/keyword auto-resolution must remain forbidden")

    seen: set[str] = set()
    previous_sort_key: tuple[int, int, str] | None = None
    resolved_groups = 0
    resolved_requirements = 0
    proposed_context_groups = 0
    proposed_context_requirements = 0
    review_groups = 0
    review_requirements = 0

    for group in groups:
        signature = group["signature"]
        expected_group_id = review_group_id(signature)
        if group.get("review_group_id") != expected_group_id:
            raise AssertionError("review group signature/id drift")
        expected_priority_rank, expected_priority_route = route_priority(signature["routes"])
        if group.get("priority_rank") != expected_priority_rank or group.get("priority_route") != expected_priority_route:
            raise AssertionError("review queue priority drift")
        sort_key = (expected_priority_rank, -int(group["member_count"]), expected_group_id)
        if previous_sort_key is not None and sort_key < previous_sort_key:
            raise AssertionError("review queue ordering drift")
        previous_sort_key = sort_key

        members = group.get("members", [])
        if int(group.get("member_count", 0)) != len(members) or not members:
            raise AssertionError("review group member count drift")
        member_ids: list[str] = []
        expected_grades: set[str] = set()
        expected_sources: set[str] = set()
        expected_documents: set[str] = set()

        for member in members:
            requirement_id = str(member.get("requirement_id", ""))
            if requirement_id not in rows_by_id:
                raise AssertionError(f"unknown requirement in review queue: {requirement_id}")
            if requirement_id in seen:
                raise AssertionError(f"duplicate requirement membership: {requirement_id}")
            seen.add(requirement_id)
            member_ids.append(requirement_id)
            row = rows_by_id[requirement_id]
            if group_signature(row, index) != signature:
                raise AssertionError(f"incompatible requirement mixed into group: {requirement_id}")
            document = index["catalogs"]["documents"][int(row[1])]
            source_id = str(document["source_id"])
            if source_id == FORBIDDEN_SOURCE or member.get("source_id") != source_id:
                raise AssertionError("provisional/wrong source in review queue")
            if member.get("document_id") != document["document_id"] or member.get("source_sha256") != document["sha256"]:
                raise AssertionError("document identity/fingerprint drift in review queue")
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
            expected_sources.add(source_id)
            expected_documents.add(str(document["document_id"]))

        if set(group.get("grades_represented", [])) != expected_grades:
            raise AssertionError("group grade aggregate drift")
        if set(group.get("source_ids", [])) != expected_sources:
            raise AssertionError("group source aggregate drift")
        if set(group.get("document_ids", [])) != expected_documents:
            raise AssertionError("group document aggregate drift")

        exact = exact_group_resolution(member_ids, direct, canonical_targets)
        status = group.get("admission_status")
        target = group.get("exact_canonical_semantic_id")
        if exact is None:
            if status != "SUBJECT_REVIEW_REQUIRED" or target is not None:
                raise AssertionError("module/keyword/proposed context illegally auto-admitted a group")
            review_groups += 1
            review_requirements += len(members)
        else:
            if status != "AUTO_RESOLVED_CANONICAL" or target != exact:
                raise AssertionError("exact canonical auto-resolution drift")
            if exact not in canonical_targets or not exact.startswith("school-"):
                raise AssertionError("auto-resolution target is not canonical school identity")
            resolved_groups += 1
            resolved_requirements += len(members)

        contexts = group.get("proposed_context_refs", [])
        if contexts:
            proposed_context_groups += 1
            proposed_context_requirements += len(members)
        for context in contexts:
            if context.get("pr_head") != PR139_HEAD:
                raise AssertionError("PR #139 proposed context is not pinned to exact head")
            if context.get("authority") != "CONTEXT_ONLY_PROPOSED_NOT_CANONICAL":
                raise AssertionError("proposed context was promoted beyond context-only authority")

    if seen != set(rows_by_id) or len(seen) != EXPECTED_REQUIREMENTS:
        missing = sorted(set(rows_by_id) - seen)[:5]
        raise AssertionError(f"requirements not assigned exactly once: {missing}")

    summary = queue["summary"]
    expected_summary = {
        "requirements_total": EXPECTED_REQUIREMENTS,
        "review_groups_total": len(groups),
        "auto_resolved_canonical_groups": resolved_groups,
        "auto_resolved_canonical_requirements": resolved_requirements,
        "proposed_context_groups": proposed_context_groups,
        "proposed_context_requirements": proposed_context_requirements,
        "subject_review_required_groups": review_groups,
        "subject_review_required_requirements": review_requirements,
    }
    if summary != expected_summary:
        raise AssertionError(f"review queue summary drift: {summary} != {expected_summary}")


def expect_failure(fn, label: str) -> None:
    try:
        fn()
    except AssertionError:
        return
    raise AssertionError(f"negative test did not fail: {label}")


def negative_tests(queue: dict[str, Any]) -> None:
    bad = copy.deepcopy(queue)
    bad["groups"][0]["members"].pop()
    bad["groups"][0]["member_count"] -= 1
    expect_failure(lambda: validate_queue(bad), "lost requirement")

    bad = copy.deepcopy(queue)
    duplicate = copy.deepcopy(bad["groups"][0]["members"][0])
    bad["groups"][1]["members"].append(duplicate)
    bad["groups"][1]["member_count"] += 1
    expect_failure(lambda: validate_queue(bad), "duplicate membership")

    bad = copy.deepcopy(queue)
    bad["groups"][0]["review_group_id"] = "RRG-tampered"
    expect_failure(lambda: validate_queue(bad), "group signature drift")

    bad = copy.deepcopy(queue)
    bad["groups"][0]["signature"]["normalized_meaning"] += " tampered"
    expect_failure(lambda: validate_queue(bad), "mixed incompatible meaning")

    bad = copy.deepcopy(queue)
    bad["groups"][0]["members"][0]["source_id"] = FORBIDDEN_SOURCE
    expect_failure(lambda: validate_queue(bad), "provisional 2027 source")

    bad = copy.deepcopy(queue)
    candidate = next(group for group in bad["groups"] if group["admission_status"] == "SUBJECT_REVIEW_REQUIRED")
    candidate["admission_status"] = "AUTO_RESOLVED_CANONICAL"
    candidate["exact_canonical_semantic_id"] = "school-fake-module-keyword-match"
    expect_failure(lambda: validate_queue(bad), "module-only auto admission")

    bad = copy.deepcopy(queue)
    candidate = next(group for group in bad["groups"] if group["admission_status"] == "SUBJECT_REVIEW_REQUIRED")
    candidate["admission_status"] = "AUTO_RESOLVED_CANONICAL"
    candidate["exact_canonical_semantic_id"] = "ru-proposed-fake"
    expect_failure(lambda: validate_queue(bad), "proposed identity marked canonical")

    bad = copy.deepcopy(queue)
    bad["groups"][0]["members"][0]["page"] = 0
    expect_failure(lambda: validate_queue(bad), "missing locator")


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
        print(f"priority[{key}].groups={value['groups']}")
        print(f"priority[{key}].requirements={value['requirements']}")
    print("negative_tests=PASS")
    print("module_keyword_auto_resolution=FORBIDDEN")
    print("pr139_proposed_identity_admission=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
