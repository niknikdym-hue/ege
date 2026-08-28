#!/usr/bin/env python3
from __future__ import annotations

import copy

from build_ege_exact_route_bridge import (
    EXPECTED_EGE_REQUIREMENTS,
    EXPECTED_EGE_UNITS,
    build_bridge,
    classify,
    parse_explicit_task_id,
)


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
    if policy["task_identity_source"] != "EXPLICIT_CODE_ONLY":
        raise AssertionError("task identity source was weakened")
    if policy["dotted_codifier_codes_are_task_ids"] is not False:
        raise AssertionError("dotted codifier code may not be treated as task ID")
    if policy["module_meaning_keyword_inference_allowed"] is not False:
        raise AssertionError("fuzzy/module/keyword inference must remain forbidden")
    if policy["candidate_is_admission"] is not False:
        raise AssertionError("candidate was promoted to admission")

    seen: set[str] = set()
    requirement_count = 0
    class_counts: dict[str, int] = {}
    proven_tasks = 0
    for row in records:
        unit_id = str(row["admission_unit_id"])
        if unit_id in seen:
            raise AssertionError(f"duplicate EGE admission unit: {unit_id}")
        seen.add(unit_id)
        requirement_count += int(row["member_count"])
        if row["admission_status"] != "SUBJECT_REVIEW_REQUIRED":
            raise AssertionError("candidate bridge changed subject admission truth")
        task = row["proven_task"]
        candidate_class = str(row["candidate_class"])
        class_counts[candidate_class] = class_counts.get(candidate_class, 0) + 1
        targets = list(row["canonical_candidate_targets"])
        refs = list(row["reviewed_authority_refs"])
        parsed = parse_explicit_task_id(str(row["document_id"]), str(row["section"]), str(row["code"]))
        if parsed != task:
            raise AssertionError("stored task identity differs from strict parser")
        if task is None:
            if candidate_class != "TASK_ID_NOT_PROVEN" or targets or refs:
                raise AssertionError("unproven task received route/canonical evidence")
        else:
            proven_tasks += 1
            for target in targets:
                if not isinstance(target, str) or not target.startswith("school-"):
                    raise AssertionError("candidate target is not canonical school namespace")
            for ref in refs:
                if ref.get("review_status") != "reviewed":
                    raise AssertionError("unreviewed task mapping entered candidate authority")
            if candidate_class == "EXACT_SINGLE_CANONICAL_CANDIDATE" and len(targets) != 1:
                raise AssertionError("single canonical candidate does not have exactly one target")
            if candidate_class == "COMPOSITE_CANONICAL_SET" and len(targets) <= 1:
                raise AssertionError("composite candidate does not have multiple targets")
            if candidate_class == "ROUTE_WITHOUT_CANONICAL_TARGET" and targets:
                raise AssertionError("route-without-target contains canonical targets")
    if len(seen) != EXPECTED_EGE_UNITS or requirement_count != EXPECTED_EGE_REQUIREMENTS:
        raise AssertionError("EGE unit/requirement accounting incomplete")
    if class_counts != summary["candidate_classes"]:
        raise AssertionError("candidate class accounting drift")
    if proven_tasks != sum(summary["proven_task_distribution"].values()):
        raise AssertionError("proven task accounting drift")


def expect_failure(fn, label: str) -> None:
    try:
        fn()
    except AssertionError:
        return
    raise AssertionError(f"negative test did not fail: {label}")


def negative_tests(bridge: dict[str, object]) -> None:
    if parse_explicit_task_id("EGE_COD", "section_1_checked_requirements", "3.11") is not None:
        raise AssertionError("content-element code 3.11 was misread as EGE task")
    if parse_explicit_task_id("EGE_COD", "section_2_content_elements", "1.2.7") is not None:
        raise AssertionError("content-element code 1.2.7 was misread as EGE task")
    if parse_explicit_task_id("EGE_SPEC", "task_table", "TASK-10") != 10:
        raise AssertionError("explicit TASK-10 parser contract failed")
    if parse_explicit_task_id("EGE_SPEC", "task_table", "EGE-2026-TASK:27") != 27:
        raise AssertionError("explicit EGE-2026-TASK:27 parser contract failed")
    if parse_explicit_task_id("EGE_SPEC", "task_table", "TASK-28") is not None:
        raise AssertionError("out-of-range EGE task was accepted")

    single_class, single_targets, _ = classify(10, {10: {"canonical_targets": ["school-one"], "authority_refs": []}})
    if single_class != "EXACT_SINGLE_CANONICAL_CANDIDATE" or single_targets != ["school-one"]:
        raise AssertionError("single target classification contract failed")
    composite_class, composite_targets, _ = classify(10, {10: {"canonical_targets": ["school-a", "school-b"], "authority_refs": []}})
    if composite_class != "COMPOSITE_CANONICAL_SET" or len(composite_targets) != 2:
        raise AssertionError("composite target classification contract failed")

    bad = copy.deepcopy(bridge)
    bad["records"][0]["admission_status"] = "AUTO_RESOLVED_CANONICAL"
    expect_failure(lambda: validate_bridge(bad), "candidate promoted to admission")

    bad = copy.deepcopy(bridge)
    bad["records"][0]["proven_task"] = 3
    bad["records"][0]["candidate_class"] = "EXACT_SINGLE_CANONICAL_CANDIDATE"
    bad["records"][0]["canonical_candidate_targets"] = ["school-fake-keyword-match"]
    expect_failure(lambda: validate_bridge(bad), "task inferred from dotted/module meaning")

    bad = copy.deepcopy(bridge)
    bad["records"][0]["canonical_candidate_targets"] = ["ru-proposed-fake"]
    expect_failure(lambda: validate_bridge(bad), "proposed ru identity entered candidate target")

    bad = copy.deepcopy(bridge)
    bad["records"].append(copy.deepcopy(bad["records"][0]))
    bad["summary"]["ege_admission_units"] += 1
    expect_failure(lambda: validate_bridge(bad), "duplicate EGE unit")


def main() -> int:
    first = build_bridge()
    second = build_bridge()
    if first != second:
        raise AssertionError("EGE exact route bridge is nondeterministic")
    validate_bridge(first)
    negative_tests(first)
    print("RUSSIAN_EGE_EXACT_ROUTE_BRIDGE_VALIDATION=PASS")
    print(f"normalized_sha256={first['normalized_sha256']}")
    print(f"ege_admission_units={first['summary']['ege_admission_units']}")
    print(f"ege_requirements={first['summary']['ege_requirements']}")
    for key, value in first["summary"]["candidate_classes"].items():
        print(f"candidate[{key}]={value}")
    print(f"proven_tasks={sum(first['summary']['proven_task_distribution'].values())}")
    print("semantic_admissions=0")
    print("dotted_code_task_inference=FORBIDDEN")
    print("negative_tests=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
