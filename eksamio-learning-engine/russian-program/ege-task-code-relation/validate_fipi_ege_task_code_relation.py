#!/usr/bin/env python3
from __future__ import annotations

import copy

from build_fipi_ege_task_code_relation import (
    EXPECTED_SPEC_SHA,
    EXPECTED_TASKS,
    build_relation,
    expand_expression,
    load_codifier_codes,
)


def validate_relation(relation: dict[str, object]) -> None:
    source = relation["source"]
    if source["source_id"] != "FIPI-EGE-RU-2026-FINAL":
        raise AssertionError("provisional/nonlaunch source entered EGE task relation")
    if source["document_id"] != "EGE_SPEC" or source["sha256"] != EXPECTED_SPEC_SHA:
        raise AssertionError("EGE specification fingerprint drift")
    if source["printed_pages"] != [18, 19, 20] or source["pdf_physical_pages"] != [9, 10]:
        raise AssertionError("EGE specification table-page locator drift")
    if relation["relation_policy"]["semantic_admission_implied"] is not False:
        raise AssertionError("task-code source relation cannot imply semantic admission")

    rows = relation["rows"]
    tasks = [int(row["task"]) for row in rows]
    if len(rows) != 27 or set(tasks) != EXPECTED_TASKS or len(set(tasks)) != 27:
        raise AssertionError("EGE task 1-27 relation coverage drift")
    if tasks != list(range(1, 28)):
        raise AssertionError("EGE task relation row order drift")

    codifier_codes = load_codifier_codes()
    requirement_codes = codifier_codes.get("section_1_checked_requirements", set())
    content_codes = codifier_codes.get("section_2_content_elements", set())
    if not requirement_codes or not content_codes:
        raise AssertionError("canonical EGE codifier code sets are unavailable")

    for row in rows:
        task = int(row["task"])
        locator = row["locator"]
        if locator["document_id"] != "EGE_SPEC" or locator["source_sha256"] != EXPECTED_SPEC_SHA:
            raise AssertionError(f"task {task} locator source drift")
        if locator["row"] != f"task-{task}" or not locator["table"]:
            raise AssertionError(f"task {task} missing precise table-row locator")
        if int(locator["printed_page"]) not in {18, 19, 20} or int(locator["pdf_physical_page"]) not in {9, 10}:
            raise AssertionError(f"task {task} page locator drift")
        if row["provenance_status"] != "EXPLICIT_FIPI_TABLE_ROW":
            raise AssertionError(f"task {task} provenance drift")

        expected_content: list[str] = []
        for expression in row["content_code_expressions"]:
            expected_content.extend(code for code in expand_expression(expression) if code not in expected_content)
        expected_requirements: list[str] = []
        for expression in row["requirement_code_expressions"]:
            expected_requirements.extend(code for code in expand_expression(expression) if code not in expected_requirements)
        if row["content_codes_expanded"] != expected_content:
            raise AssertionError(f"task {task} content-code range collapsed/drifted")
        if row["requirement_codes_expanded"] != expected_requirements:
            raise AssertionError(f"task {task} requirement-code range collapsed/drifted")
        if not set(expected_content).issubset(content_codes):
            raise AssertionError(f"task {task} contains content code absent from canonical EGE codifier")
        if not set(expected_requirements).issubset(requirement_codes):
            raise AssertionError(f"task {task} contains requirement code absent from canonical EGE codifier")
        if row["difficulty"] not in {"Б", "П"} or int(row["max_primary_score"]) <= 0:
            raise AssertionError(f"task {task} difficulty/score row drift")

    summary = relation["summary"]
    if summary["task_rows"] != 27 or summary["tasks"] != list(range(1, 28)):
        raise AssertionError("EGE task relation summary coverage drift")
    if summary["basic_tasks"] != 24 or summary["advanced_tasks"] != 3:
        raise AssertionError("EGE task difficulty totals drift")
    if summary["max_primary_score_total"] != 50:
        raise AssertionError("EGE max primary score total drift")


def expect_failure(fn, label: str) -> None:
    try:
        fn()
    except (AssertionError, ValueError):
        return
    raise AssertionError(f"negative test did not fail: {label}")


def negative_tests(relation: dict[str, object]) -> None:
    expect_failure(lambda: expand_expression("3.5.6–3.5.2"), "descending range")
    expect_failure(lambda: expand_expression("3.5–4.1"), "cross-prefix range")
    expect_failure(lambda: expand_expression("TASK-3"), "topic/task text fabricated as codifier code")

    bad = copy.deepcopy(relation)
    bad["source"]["source_id"] = "FIPI-EGE-RU-2027-PROJECT"
    expect_failure(lambda: validate_relation(bad), "provisional 2027 source")

    bad = copy.deepcopy(relation)
    bad["source"]["sha256"] = "0" * 64
    expect_failure(lambda: validate_relation(bad), "wrong source fingerprint")

    bad = copy.deepcopy(relation)
    bad["rows"][0]["locator"]["row"] = ""
    expect_failure(lambda: validate_relation(bad), "missing table-row locator")

    bad = copy.deepcopy(relation)
    bad["rows"][0]["task"] = 28
    expect_failure(lambda: validate_relation(bad), "task outside 1-27")

    bad = copy.deepcopy(relation)
    bad["rows"].append(copy.deepcopy(bad["rows"][0]))
    expect_failure(lambda: validate_relation(bad), "duplicate task row")

    bad = copy.deepcopy(relation)
    task7 = next(row for row in bad["rows"] if row["task"] == 7)
    task7["content_codes_expanded"] = ["3.5.2", "3.4.2", "3.6.3"]
    expect_failure(lambda: validate_relation(bad), "composite/range relation collapsed")

    bad = copy.deepcopy(relation)
    bad["rows"][0]["content_codes_expanded"] = ["9.9.9"]
    bad["rows"][0]["content_code_expressions"] = ["9.9.9"]
    expect_failure(lambda: validate_relation(bad), "fabricated codifier code")

    bad = copy.deepcopy(relation)
    bad["relation_policy"]["semantic_admission_implied"] = True
    expect_failure(lambda: validate_relation(bad), "source relation promoted to semantic admission")


def main() -> int:
    first = build_relation()
    second = build_relation()
    if first != second:
        raise AssertionError("FIPI EGE task-code relation is nondeterministic")
    validate_relation(first)
    negative_tests(first)
    print("FIPI_EGE_2026_TASK_CODE_RELATION_VALIDATION=PASS")
    print(f"normalized_sha256={first['normalized_sha256']}")
    for key, value in first["summary"].items():
        print(f"{key}={value}")
    print("negative_tests=PASS")
    print("semantic_admissions=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
