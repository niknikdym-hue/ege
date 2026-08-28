#!/usr/bin/env python3
from __future__ import annotations

import copy

from build_ege_exact_route_bridge import (
    EXPECTED_EGE_REQUIREMENTS,
    EXPECTED_EGE_UNITS,
    build_bridge,
    classify_tasks,
    proven_tasks_for_unit,
    relation_indexes,
)
from build_fipi_ege_task_code_relation import build_relation


def validate_bridge(bridge: dict[str, object]) -> None:
    summary = bridge["summary"]
    records = bridge["records"]
    if summary["ege_admission_units"] != EXPECTED_EGE_UNITS or len(records) != EXPECTED_EGE_UNITS:
        raise AssertionError("EGE admission-unit parity drift")
    if summary["ege_requirements"] != EXPECTED_EGE_REQUIREMENTS:
        raise AssertionError("EGE requirement parity drift")
    if summary["semantic_admissions"] != 0:
        raise AssertionError("candidate bridge must never admit semantics")

    policy = bridge["matching_policy"]
    if policy["task_identity_source"] != "EXPLICIT_FIPI_EGE_2026_TASK_CODE_TABLE":
        raise AssertionError("official EGE task-code authority source drift")
    if policy["codifier_section_and_exact_code_required"] is not True:
        raise AssertionError("exact codifier section+code boundary weakened")
    if policy["dotted_codifier_code_is_not_itself_a_task_id"] is not True:
        raise AssertionError("dotted codifier code was promoted to task ID")
    if policy["module_meaning_keyword_inference_allowed"] is not False:
        raise AssertionError("module/meaning/keyword inference must remain forbidden")
    if policy["candidate_is_admission"] is not False:
        raise AssertionError("candidate was promoted to admission")

    relation = build_relation()
    indexes = relation_indexes(relation)
    if bridge["task_code_relation"]["normalized_sha256"] != relation["normalized_sha256"]:
        raise AssertionError("EGE bridge task-code relation hash drift")

    seen: set[str] = set()
    requirement_count = 0
    class_counts: dict[str, int] = {}
    proven_units = 0
    proven_requirements = 0
    task_distribution: dict[str, int] = {}

    for row in records:
        unit_id = str(row["admission_unit_id"])
        if unit_id in seen:
            raise AssertionError(f"duplicate EGE admission unit: {unit_id}")
        seen.add(unit_id)
        member_count = int(row["member_count"])
        requirement_count += member_count
        if row["admission_status"] != "SUBJECT_REVIEW_REQUIRED":
            raise AssertionError("candidate bridge changed subject admission truth")

        expected_tasks = proven_tasks_for_unit(
            str(row["document_id"]), str(row["section"]), str(row["code"]), indexes
        )
        stored_tasks = [int(task) for task in row["proven_tasks"]]
        if stored_tasks != expected_tasks:
            raise AssertionError("stored task set differs from exact FIPI task-code relation")

        candidate_class = str(row["candidate_class"])
        class_counts[candidate_class] = class_counts.get(candidate_class, 0) + 1
        targets = list(row["canonical_candidate_targets"])
        refs = list(row["reviewed_task_authority_refs"])

        if not stored_tasks:
            if candidate_class != "TASK_ID_NOT_PROVEN" or targets or refs or row["task_relation_authority"] is not None:
                raise AssertionError("unproven task set received route/canonical evidence")
        else:
            proven_units += 1
            proven_requirements += member_count
            relation_authority = row["task_relation_authority"]
            if relation_authority is None:
                raise AssertionError("proven task set lacks official task-code authority")
            if relation_authority["source_document_id"] != "EGE_SPEC" or relation_authority["source_sha256"] != relation["source"]["sha256"]:
                raise AssertionError("proven task set source authority drift")
            if relation_authority["relation_hash"] != relation["normalized_sha256"]:
                raise AssertionError("proven task set relation fingerprint drift")
            for task in stored_tasks:
                task_distribution[str(task)] = task_distribution.get(str(task), 0) + 1
            for target in targets:
                if not isinstance(target, str) or not target.startswith("school-"):
                    raise AssertionError("candidate target is not canonical school namespace")
            for task_ref in refs:
                if int(task_ref["task"]) not in stored_tasks:
                    raise AssertionError("task authority ref outside proven task set")
                for authority_ref in task_ref["authority_refs"]:
                    if authority_ref.get("review_status") != "reviewed":
                        raise AssertionError("unreviewed task mapping entered candidate authority")
            if candidate_class == "EXACT_SINGLE_TASK_SINGLE_CANONICAL_CANDIDATE":
                if len(stored_tasks) != 1 or len(targets) != 1:
                    raise AssertionError("single-task/single-target candidate shape drift")
            elif candidate_class == "EXACT_SINGLE_TASK_COMPOSITE_CANONICAL_SET":
                if len(stored_tasks) != 1 or len(targets) <= 1:
                    raise AssertionError("single-task composite candidate shape drift")
            elif candidate_class == "EXACT_SINGLE_TASK_ROUTE_WITHOUT_CANONICAL_TARGET":
                if len(stored_tasks) != 1 or targets:
                    raise AssertionError("single-task route-only candidate shape drift")
            elif candidate_class == "EXACT_MULTI_TASK_CANONICAL_CANDIDATE_SET":
                if len(stored_tasks) <= 1 or not targets:
                    raise AssertionError("multi-task canonical candidate shape drift")
            elif candidate_class == "EXACT_MULTI_TASK_ROUTE_WITHOUT_CANONICAL_TARGET":
                if len(stored_tasks) <= 1 or targets:
                    raise AssertionError("multi-task route-only candidate shape drift")
            else:
                raise AssertionError(f"unsupported proven-task candidate class: {candidate_class}")

    if len(seen) != EXPECTED_EGE_UNITS or requirement_count != EXPECTED_EGE_REQUIREMENTS:
        raise AssertionError("EGE unit/requirement accounting incomplete")
    if class_counts != summary["candidate_classes"]:
        raise AssertionError("candidate class accounting drift")
    if proven_units != summary["task_proven_units"] or proven_requirements != summary["task_proven_requirements"]:
        raise AssertionError("task-proven unit/requirement accounting drift")
    if EXPECTED_EGE_UNITS - proven_units != summary["task_unproven_units"]:
        raise AssertionError("task-unproven unit accounting drift")
    if EXPECTED_EGE_REQUIREMENTS - proven_requirements != summary["task_unproven_requirements"]:
        raise AssertionError("task-unproven requirement accounting drift")
    if task_distribution != summary["proven_task_distribution"]:
        raise AssertionError("proven task distribution drift")


def expect_failure(fn, label: str) -> None:
    try:
        fn()
    except AssertionError:
        return
    raise AssertionError(f"negative test did not fail: {label}")


def negative_tests(bridge: dict[str, object]) -> None:
    relation = build_relation()
    indexes = relation_indexes(relation)
    if proven_tasks_for_unit("EDSOO1011", "grade_10_distributed_codifier", "3.9", indexes):
        raise AssertionError("module/source-external code was incorrectly bridged to EGE tasks")
    if proven_tasks_for_unit("EGE_COD", "section_2_content_elements", "3.11", indexes):
        raise AssertionError("requirement code 3.11 was incorrectly treated as content-element relation")
    if proven_tasks_for_unit("EGE_COD", "section_1_checked_requirements", "3.11", indexes) != [2]:
        raise AssertionError("exact requirement code 3.11 should prove task 2 only")
    if proven_tasks_for_unit("EGE_COD", "section_1_checked_requirements", "3.9", indexes) != list(range(9, 16)):
        raise AssertionError("requirement code 3.9 must preserve tasks 9-15 as a multi-task relation")

    single_class, single_targets, _ = classify_tasks([10], {10: {"canonical_targets": ["school-one"], "authority_refs": []}})
    if single_class != "EXACT_SINGLE_TASK_SINGLE_CANONICAL_CANDIDATE" or single_targets != ["school-one"]:
        raise AssertionError("single-task/single-target classification contract failed")
    composite_class, composite_targets, _ = classify_tasks([10], {10: {"canonical_targets": ["school-a", "school-b"], "authority_refs": []}})
    if composite_class != "EXACT_SINGLE_TASK_COMPOSITE_CANONICAL_SET" or len(composite_targets) != 2:
        raise AssertionError("single-task composite classification contract failed")
    multi_class, multi_targets, _ = classify_tasks([9, 10], {
        9: {"canonical_targets": ["school-a"], "authority_refs": []},
        10: {"canonical_targets": ["school-b"], "authority_refs": []},
    })
    if multi_class != "EXACT_MULTI_TASK_CANONICAL_CANDIDATE_SET" or multi_targets != ["school-a", "school-b"]:
        raise AssertionError("multi-task classification contract failed")

    bad = copy.deepcopy(bridge)
    bad["records"][0]["admission_status"] = "AUTO_RESOLVED_CANONICAL"
    expect_failure(lambda: validate_bridge(bad), "candidate promoted to admission")

    bad = copy.deepcopy(bridge)
    unproven = next(row for row in bad["records"] if not row["proven_tasks"])
    unproven["proven_tasks"] = [3]
    unproven["candidate_class"] = "EXACT_SINGLE_TASK_SINGLE_CANONICAL_CANDIDATE"
    unproven["canonical_candidate_targets"] = ["school-fake-module-keyword-match"]
    expect_failure(lambda: validate_bridge(bad), "task inferred from module/meaning rather than official relation")

    bad = copy.deepcopy(bridge)
    proven = next(row for row in bad["records"] if row["proven_tasks"])
    proven["canonical_candidate_targets"] = ["ru-proposed-fake"]
    expect_failure(lambda: validate_bridge(bad), "proposed ru identity entered candidate target")

    bad = copy.deepcopy(bridge)
    bad["records"].append(copy.deepcopy(bad["records"][0]))
    bad["summary"]["ege_admission_units"] += 1
    expect_failure(lambda: validate_bridge(bad), "duplicate EGE unit")


def main() -> int:
    first = build_bridge()
    second = build_bridge()
    if first != second:
        raise AssertionError("EGE task-code bridge is nondeterministic")
    validate_bridge(first)
    negative_tests(first)
    print("RUSSIAN_EGE_EXACT_ROUTE_BRIDGE_VALIDATION=PASS")
    print(f"normalized_sha256={first['normalized_sha256']}")
    for key, value in first["summary"].items():
        print(f"{key}={value}")
    print("semantic_admissions=0")
    print("module_keyword_task_inference=FORBIDDEN")
    print("negative_tests=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
