#!/usr/bin/env python3
"""Release validator for Eksamio interactive EGE demo packages.

Usage:
    python validate_demo_package.py /path/to/<prefix>-PACKAGE-CONTRACT.json
    python validate_demo_package.py --self-test

The validator uses the Python standard library only. It does not prove subject
correctness by itself; it enforces the package contract and prevents known
classes of production errors discovered during the 2026 prelaunch audit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


STATUS_ORDER = [
    "DRAFT",
    "SOURCE_GATE_PASSED",
    "CONTENT_LOCKED",
    "BUILD_COMPLETE",
    "LOCAL_TEST_PASS",
    "READY_FOR_TILDA_TEST",
    "PUBLISHED_SMOKE_PASS",
    "RELEASED",
]

SOURCE_ROLES = {"demo", "specification", "codifier"}
SHORT_ANSWER_TYPES = {
    "exact_text",
    "exact_ordered_digits",
    "exact_unordered_digits",
    "position_partial",
    "set_difference_partial",
    "numeric_exact",
    "multi_field",
}
GENERATED_BUILD_STATUSES = {
    "BUILD_COMPLETE",
    "LOCAL_TEST_PASS",
    "READY_FOR_TILDA_TEST",
    "PUBLISHED_SMOKE_PASS",
    "RELEASED",
}
TESTED_STATUSES = {
    "LOCAL_TEST_PASS",
    "READY_FOR_TILDA_TEST",
    "PUBLISHED_SMOKE_PASS",
    "RELEASED",
}
RELEASE_STATUSES = {
    "READY_FOR_TILDA_TEST",
    "PUBLISHED_SMOKE_PASS",
    "RELEASED",
}

MANIFEST_RE = re.compile(r"^([0-9a-f]{64})\s{2}(.+)$")
JSON_SCRIPT_RE = re.compile(
    r"<script\b[^>]*type=[\"']application/(?:json|ld\+json)[\"'][^>]*>(.*?)</script>",
    re.I | re.S,
)
SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.I | re.S)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: int = 0

    def check(self, condition: bool, message: str) -> bool:
        self.checks += 1
        if not condition:
            self.errors.append(message)
            return False
        return True

    def warn(self, condition: bool, message: str) -> bool:
        self.checks += 1
        if not condition:
            self.warnings.append(message)
            return False
        return True

    @property
    def ok(self) -> bool:
        return not self.errors


def load_json(path: Path, result: ValidationResult, label: str) -> Any:
    if not result.check(path.is_file(), f"Missing {label}: {path}"):
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result.errors.append(f"Invalid {label} JSON {path}: {exc}")
        return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def status_at_least(status: str, expected: str) -> bool:
    try:
        return STATUS_ORDER.index(status) >= STATUS_ORDER.index(expected)
    except ValueError:
        return False


def read_text(path: Path, result: ValidationResult, label: str) -> str:
    if not result.check(path.is_file(), f"Missing {label}: {path}"):
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        result.errors.append(f"Cannot read UTF-8 {label} {path}: {exc}")
        return ""


def validate_contract(contract: dict[str, Any], result: ValidationResult) -> None:
    result.check(contract.get("schema_version") == "1.0", "Unsupported contract schema_version")
    package = contract.get("package") or {}
    page = contract.get("page") or {}
    exam = contract.get("exam") or {}
    build = contract.get("build") or {}
    scoring = contract.get("scoring") or {}
    storage = contract.get("storage") or {}
    publication = contract.get("publication") or {}

    prefix = package.get("prefix")
    status = package.get("status")
    result.check(isinstance(prefix, str) and bool(prefix), "package.prefix is required")
    result.check(status in STATUS_ORDER, f"Invalid package.status: {status!r}")
    result.check(bool(package.get("version")), "package.version is required")
    result.check(bool(package.get("release_zip")), "package.release_zip is required")

    url = page.get("url")
    canonical = page.get("canonical")
    result.check(isinstance(url, str) and url.startswith("https://eksamio.ru/"), "Invalid page.url")
    result.check(canonical == url, "page.canonical must equal page.url")
    result.check(not re.search(r"/20\d{2}(?:/|$)", str(url)), "Year is forbidden in permanent page URL")
    result.check(bool(page.get("slug")), "page.slug is required")

    for field_name in ("task_positions", "official_examples", "duration_minutes", "primary_max"):
        value = exam.get(field_name)
        result.check(isinstance(value, int) and value >= 0, f"exam.{field_name} must be a non-negative integer")

    result.check(build.get("generated_files_must_not_be_edited") is True, "Generated-file lock must be enabled")
    result.check(isinstance(build.get("t123_order"), list) and bool(build.get("t123_order")), "build.t123_order is required")
    result.check(scoring.get("default_reject_extra_characters") is True, "Strict input rejection must be the default")
    result.check(scoring.get("expert_self_assessment_affects_official_total") is False, "Expert self-assessment must not affect official total")
    result.check(scoring.get("all_dependencies_enforced_in_ui_and_scorer") is True, "Dependencies must be enforced in UI and scorer")
    result.check(scoring.get("technical_heuristics_are_advisory_only") is True, "Technical heuristics must be advisory only")
    result.check(storage.get("safe_wrapper_required") is True, "Safe localStorage wrapper is required")
    result.check(storage.get("absolute_end_time_required") is True, "Absolute timer end time is required")
    result.check(storage.get("variant_choice_persistence_required") is True, "Variant persistence is required")

    production_checked = publication.get("production_checked") is True
    if not production_checked:
        result.check(status not in {"PUBLISHED_SMOKE_PASS", "RELEASED"}, "Production status cannot be claimed before production_checked=true")


def validate_sources(root: Path, contract: dict[str, Any], result: ValidationResult) -> set[str]:
    sources = contract.get("sources") or []
    roles = {item.get("role") for item in sources if isinstance(item, dict)}
    result.check(roles == SOURCE_ROLES, f"Exactly three source roles are required: {sorted(SOURCE_ROLES)}")
    result.check(len(sources) == 3, "Exactly three final FIPI source files are required")

    source_paths: set[str] = set()
    for item in sources:
        if not isinstance(item, dict):
            result.errors.append("Every sources entry must be an object")
            continue
        role = item.get("role")
        path_value = item.get("path")
        status = str(item.get("status", ""))
        expected_hash = str(item.get("sha256", ""))
        pages = item.get("pages")
        if not isinstance(path_value, str):
            result.errors.append(f"Source {role!r} has no path")
            continue
        path = root / path_value
        source_paths.add(path_value)
        result.check(path_value.startswith("source/"), f"Source must be inside source/: {path_value}")
        result.check(status == "final", f"Source {path_value} must have status=final")
        result.check(not re.search(r"(?:project|proekt|draft|проект)", path_value, re.I), f"Project/draft source filename is forbidden: {path_value}")
        result.check(path.suffix.lower() == ".pdf", f"Source must be PDF: {path_value}")
        if result.check(path.is_file(), f"Missing source file: {path_value}"):
            actual_hash = sha256(path)
            result.check(bool(re.fullmatch(r"[0-9a-f]{64}", expected_hash)), f"Invalid SHA-256 in contract for {path_value}")
            if re.fullmatch(r"[0-9a-f]{64}", expected_hash):
                result.check(actual_hash == expected_hash, f"Source SHA-256 mismatch: {path_value}")
        result.check(isinstance(pages, int) and pages > 0, f"Source page count must be positive: {path_value}")
    return source_paths


def validate_task_map(root: Path, contract: dict[str, Any], result: ValidationResult) -> tuple[dict[tuple[int, int], dict[str, Any]], set[str]]:
    maps = contract.get("maps") or {}
    task_path = root / str(maps.get("tasks", ""))
    data = load_json(task_path, result, "TASK MAP")
    if not isinstance(data, dict):
        return {}, set()
    tasks = data.get("tasks")
    if not result.check(isinstance(tasks, list) and bool(tasks), "TASK MAP tasks must be a non-empty list"):
        return {}, set()

    lookup: dict[tuple[int, int], dict[str, Any]] = {}
    required_case_ids: set[str] = set()
    maxima_by_number: dict[int, set[int]] = {}

    for index, task in enumerate(tasks):
        label = f"task[{index}]"
        if not isinstance(task, dict):
            result.errors.append(f"{label} must be an object")
            continue
        number = task.get("number")
        variant = task.get("variant")
        kind = task.get("kind")
        result.check(isinstance(number, int) and number > 0, f"{label}.number must be positive")
        result.check(isinstance(variant, int) and variant > 0, f"{label}.variant must be positive")
        if not isinstance(number, int) or not isinstance(variant, int):
            continue
        key = (number, variant)
        result.check(key not in lookup, f"Duplicate task number/variant: {key}")
        lookup[key] = task

        prompt = task.get("prompt_html")
        result.check(isinstance(prompt, str) and bool(prompt.strip()), f"Empty prompt for task {key}")
        source = task.get("source") or {}
        result.check(isinstance(source.get("prompt_pdf_page"), int) and source.get("prompt_pdf_page") > 0, f"Missing prompt PDF page for task {key}")
        result.check(isinstance(source.get("answer_pdf_page"), int) and source.get("answer_pdf_page") > 0, f"Missing answer PDF page for task {key}")

        max_score = task.get("max_score")
        result.check(isinstance(max_score, int) and max_score >= 0, f"Invalid max_score for task {key}")
        if isinstance(max_score, int):
            maxima_by_number.setdefault(number, set()).add(max_score)

        answer = task.get("answer") or {}
        answer_type = answer.get("type")
        if kind == "short":
            result.check(answer_type in SHORT_ANSWER_TYPES, f"Invalid short answer type for task {key}: {answer_type!r}")
            accepted = answer.get("accepted")
            result.check(isinstance(accepted, list) and bool(accepted), f"Short task {key} needs accepted answers")
            accepted_values: list[str] = []
            if isinstance(accepted, list):
                for accepted_item in accepted:
                    if not isinstance(accepted_item, dict):
                        result.errors.append(f"Accepted answer in task {key} must be an object")
                        continue
                    value = accepted_item.get("value")
                    result.check(isinstance(value, str) and value != "", f"Empty accepted answer in task {key}")
                    result.check(isinstance(accepted_item.get("source_pdf_page"), int) and accepted_item.get("source_pdf_page") > 0, f"Accepted answer without source page in task {key}")
                    result.check(bool(accepted_item.get("basis")), f"Accepted answer without basis in task {key}")
                    if isinstance(value, str):
                        accepted_values.append(value)
                result.check(len(accepted_values) == len(set(accepted_values)), f"Duplicate accepted answers in task {key}")
                canonical = answer.get("canonical")
                result.check(canonical in accepted_values, f"Canonical answer is not in accepted list for task {key}")

            normalization = answer.get("normalization") or {}
            for dangerous_field in ("remove_internal_spaces", "remove_punctuation", "remove_non_digits"):
                result.check(normalization.get(dangerous_field) is not True, f"Dangerous permissive normalization {dangerous_field}=true in task {key}")
            result.check(normalization.get("trim") is not True, f"Whitespace trimming is forbidden by default in task {key}; model allowed forms explicitly")

            partial = task.get("partial_scoring")
            if answer_type in {"position_partial", "set_difference_partial"}:
                result.check(isinstance(partial, dict), f"Partial scoring configuration required for task {key}")
                if isinstance(partial, dict):
                    result.check(partial.get("extra_characters_forbidden") is True, f"Extra characters must be forbidden in partial scoring task {key}")
                    branches = partial.get("branches")
                    result.check(isinstance(branches, list) and bool(branches), f"Partial scoring branches required for task {key}")
                    if isinstance(branches, list):
                        for branch in branches:
                            result.check(isinstance(branch, dict) and isinstance(branch.get("score"), int), f"Invalid partial branch in task {key}")
                            result.check(isinstance(branch, dict) and isinstance(branch.get("source_pdf_page"), int) and branch.get("source_pdf_page") > 0, f"Partial branch without source page in task {key}")
        elif kind == "extended":
            result.check(answer_type == "expert_only", f"Extended task {key} must use expert_only")
            criteria = task.get("criteria")
            result.check(isinstance(criteria, list) and bool(criteria), f"Extended task {key} needs criteria")
            criterion_scores: set[int] = set()
            branch_ids: set[str] = set()
            if isinstance(criteria, list):
                for criterion in criteria:
                    if not isinstance(criterion, dict):
                        result.errors.append(f"Criterion in task {key} must be an object")
                        continue
                    score = criterion.get("score")
                    branch_id = criterion.get("branch_id")
                    text = criterion.get("text")
                    page = criterion.get("source_pdf_page")
                    result.check(isinstance(score, int) and 0 <= score <= int(max_score or 0), f"Invalid criterion score in task {key}")
                    result.check(isinstance(branch_id, str) and bool(branch_id), f"Criterion branch_id missing in task {key}")
                    result.check(branch_id not in branch_ids, f"Duplicate criterion branch_id {branch_id!r} in task {key}")
                    result.check(isinstance(text, str) and len(text.strip()) >= 20, f"Criterion text is too short in task {key}, branch {branch_id!r}")
                    result.check(isinstance(page, int) and page > 0, f"Criterion source page missing in task {key}, branch {branch_id!r}")
                    if isinstance(score, int):
                        criterion_scores.add(score)
                    if isinstance(branch_id, str):
                        branch_ids.add(branch_id)
                result.check(0 in criterion_scores, f"Extended task {key} has no 0-point branch")
                result.check(max_score in criterion_scores, f"Extended task {key} has no maximum-score branch")

            self_assessment = task.get("self_assessment") or {}
            result.check(self_assessment.get("official") is False, f"Self-assessment must be unofficial in task {key}")
            result.check(self_assessment.get("affects_official_total") is False, f"Self-assessment must not affect official total in task {key}")

            for dependency in task.get("dependencies") or []:
                if not isinstance(dependency, dict):
                    result.errors.append(f"Dependency in task {key} must be an object")
                    continue
                result.check(dependency.get("enforce_in_ui") is True, f"Dependency must be enforced in UI in task {key}")
                result.check(dependency.get("enforce_in_scorer") is True, f"Dependency must be enforced in scorer in task {key}")
                result.check(isinstance(dependency.get("source_pdf_page"), int) and dependency.get("source_pdf_page") > 0, f"Dependency source page missing in task {key}")

            for zero_reason in task.get("general_zero_reasons") or []:
                if not isinstance(zero_reason, dict):
                    result.errors.append(f"General zero reason in task {key} must be an object")
                    continue
                result.check(bool(zero_reason.get("id")), f"General zero reason id missing in task {key}")
                result.check(isinstance(zero_reason.get("text"), str) and len(zero_reason.get("text", "").strip()) >= 20, f"General zero reason text is too short in task {key}")
                result.check(isinstance(zero_reason.get("source_pdf_page"), int) and zero_reason.get("source_pdf_page") > 0, f"General zero reason source page missing in task {key}")
        else:
            result.errors.append(f"Invalid task kind for {key}: {kind!r}")

        required = task.get("required_acceptance_case_ids")
        result.check(isinstance(required, list) and bool(required), f"Task {key} must list required acceptance cases")
        if isinstance(required, list):
            for case_id in required:
                result.check(isinstance(case_id, str) and bool(case_id), f"Invalid acceptance case id in task {key}")
                if isinstance(case_id, str):
                    required_case_ids.add(case_id)

    for number, maxima in maxima_by_number.items():
        result.check(len(maxima) == 1, f"All variants of task {number} must have the same max_score")

    exam = contract.get("exam") or {}
    unique_numbers = {number for number, _variant in lookup}
    result.check(len(unique_numbers) == exam.get("task_positions"), "exam.task_positions does not match TASK MAP")
    result.check(len(lookup) == exam.get("official_examples"), "exam.official_examples does not match TASK MAP")
    total_max = sum(next(iter(maxima)) for maxima in maxima_by_number.values() if maxima)
    result.check(total_max == exam.get("primary_max"), f"Primary maximum mismatch: TASK MAP={total_max}, contract={exam.get('primary_max')}")

    return lookup, required_case_ids


def validate_acceptance_cases(root: Path, contract: dict[str, Any], task_lookup: dict[tuple[int, int], dict[str, Any]], required_ids: set[str], result: ValidationResult) -> None:
    maps = contract.get("maps") or {}
    cases_path = root / str(maps.get("acceptance_cases", ""))
    data = load_json(cases_path, result, "ACCEPTANCE CASES")
    if not isinstance(data, dict):
        return
    cases = data.get("cases")
    if not result.check(isinstance(cases, list) and bool(cases), "ACCEPTANCE CASES must contain a non-empty cases list"):
        return

    by_id: dict[str, dict[str, Any]] = {}
    positive_by_task: set[tuple[int, int]] = set()
    negative_by_task: set[tuple[int, int]] = set()
    for case in cases:
        if not isinstance(case, dict):
            result.errors.append("Acceptance case must be an object")
            continue
        case_id = case.get("id")
        result.check(isinstance(case_id, str) and bool(case_id), "Acceptance case id is required")
        if not isinstance(case_id, str):
            continue
        result.check(case_id not in by_id, f"Duplicate acceptance case id: {case_id}")
        by_id[case_id] = case
        key = (case.get("task_number"), case.get("variant"))
        result.check(key in task_lookup, f"Acceptance case {case_id} references missing task {key}")
        result.check(isinstance(case.get("expected_score"), int), f"Acceptance case {case_id} needs integer expected_score")
        result.check(bool(case.get("basis")), f"Acceptance case {case_id} needs basis")
        category = str(case.get("category", ""))
        if category == "positive":
            positive_by_task.add(key)  # type: ignore[arg-type]
        if category.startswith("negative") or category in {"dependency-security", "general-zero"}:
            negative_by_task.add(key)  # type: ignore[arg-type]

    result.check(required_ids.issubset(by_id), f"Missing required acceptance cases: {sorted(required_ids - set(by_id))}")
    for key, task in task_lookup.items():
        if task.get("kind") == "short":
            result.check(key in positive_by_task, f"Short task {key} has no positive acceptance case")
            result.check(key in negative_by_task, f"Short task {key} has no negative acceptance case")


def validate_asset_map(root: Path, contract: dict[str, Any], task_lookup: dict[tuple[int, int], dict[str, Any]], result: ValidationResult) -> None:
    maps = contract.get("maps") or {}
    asset_path = root / str(maps.get("assets", ""))
    data = load_json(asset_path, result, "ASSET MAP")
    if not isinstance(data, dict):
        return
    assets = data.get("assets")
    result.check(isinstance(assets, list), "ASSET MAP assets must be a list")
    if not isinstance(assets, list):
        return

    asset_ids: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            result.errors.append("Asset entry must be an object")
            continue
        asset_id = asset.get("id")
        path_value = asset.get("path")
        result.check(isinstance(asset_id, str) and bool(asset_id), "Asset id is required")
        if isinstance(asset_id, str):
            result.check(asset_id not in asset_ids, f"Duplicate asset id: {asset_id}")
            asset_ids.add(asset_id)
        result.check(isinstance(path_value, str) and path_value.startswith("assets/"), f"Asset must be in assets/: {path_value!r}")
        if isinstance(path_value, str):
            path = root / path_value
            result.check(path.is_file(), f"Missing asset file: {path_value}")
            if path.suffix.lower() == ".svg" and path.is_file():
                svg = read_text(path, result, "SVG")
                result.check("<svg" in svg and "</svg>" in svg, f"Invalid SVG structure: {path_value}")
                result.check("<script" not in svg.lower(), f"Scripts are forbidden in SVG: {path_value}")
                result.check("<title" in svg.lower(), f"SVG title is required: {path_value}")
        source = asset.get("source") or {}
        result.check(isinstance(source.get("pdf_page"), int) and source.get("pdf_page") > 0, f"Asset source page missing: {asset_id}")
        invariants = asset.get("content_invariants")
        result.check(isinstance(invariants, list) and bool(invariants), f"Asset invariants required: {asset_id}")
        technical = asset.get("technical_invariants") or {}
        result.check(technical.get("standalone_and_embedded_identical") is True, f"Standalone/embed identity required: {asset_id}")
        verification = asset.get("verification") or {}
        result.check(verification.get("independent_visual_check_required") is True, f"Independent visual check required: {asset_id}")
        if (contract.get("package") or {}).get("status") in TESTED_STATUSES:
            result.check(verification.get("visual_check_status") == "PASS", f"Visual check must be PASS for tested package: {asset_id}")

    referenced_assets = {
        asset_id
        for task in task_lookup.values()
        for asset_id in (task.get("asset_ids") or [])
        if isinstance(asset_id, str)
    }
    result.check(referenced_assets.issubset(asset_ids), f"Tasks reference missing assets: {sorted(referenced_assets - asset_ids)}")


def parse_manifest(path: Path, result: ValidationResult) -> dict[str, str]:
    text = read_text(path, result, "manifest")
    entries: dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = MANIFEST_RE.fullmatch(line)
        if not match:
            result.errors.append(f"Invalid manifest line {line_number}: {line!r}")
            continue
        digest, file_name = match.groups()
        result.check(file_name not in entries, f"Duplicate manifest entry: {file_name}")
        entries[file_name] = digest
    return entries


def known_release_files(root: Path, contract_path: Path, contract: dict[str, Any]) -> set[str]:
    package = contract.get("package") or {}
    maps = contract.get("maps") or {}
    build = contract.get("build") or {}
    result = {
        rel(root, contract_path),
        str(maps.get("exam", "")),
        str(maps.get("tasks", "")),
        str(maps.get("assets", "")),
        str(maps.get("acceptance_cases", "")),
        str(build.get("head", "")),
        str(build.get("preview", "")),
        str(build.get("evidence", "")),
        str(build.get("test_report", "")),
    }
    result.update(str(path) for path in build.get("t123_order") or [])
    result.update(str(item.get("path")) for item in contract.get("sources") or [] if isinstance(item, dict))
    prefix = package.get("prefix")
    if isinstance(prefix, str):
        for suffix in ("SEO.txt", "SOURCE-GATE.txt", "SOURCE-REGISTER.json", "INSTALLATION.txt", "IMPLEMENTATION-RULES.txt", "PAGE-STATUS.txt"):
            candidate = f"{prefix}-{suffix}"
            if (root / candidate).exists():
                result.add(candidate)
    return {item for item in result if item and item != "."}


def validate_build_files(root: Path, contract_path: Path, contract: dict[str, Any], result: ValidationResult) -> None:
    package = contract.get("package") or {}
    build = contract.get("build") or {}
    status = package.get("status")
    if status not in GENERATED_BUILD_STATUSES:
        return

    t123_order = [root / str(value) for value in build.get("t123_order") or []]
    head_path = root / str(build.get("head", ""))
    preview_path = root / str(build.get("preview", ""))
    manifest_path = root / str(build.get("manifest", ""))
    evidence_path = root / str(build.get("evidence", ""))
    report_path = root / str(build.get("test_report", ""))
    zip_path = root / str(package.get("release_zip", ""))

    head = read_text(head_path, result, "HEAD")
    preview = read_text(preview_path, result, "preview")
    for path in t123_order:
        read_text(path, result, "T123")
    read_text(evidence_path, result, "test evidence")
    read_text(report_path, result, "test report")

    source_year = str((contract.get("page") or {}).get("source_year", ""))
    if (contract.get("page") or {}).get("evergreen_public_metadata") is True and source_year:
        seo_path = root / f"{package.get('prefix')}-SEO.txt"
        seo = read_text(seo_path, result, "SEO") if seo_path.exists() else ""
        result.check(source_year not in seo, f"Source year {source_year} is forbidden in evergreen SEO")
        result.check(source_year not in head, f"Source year {source_year} is forbidden in evergreen HEAD/OG/JSON-LD")

    forbidden_patterns = [str(value) for value in contract.get("forbidden_release_patterns") or []]
    interface_paths = t123_order + [preview_path]
    for path in interface_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern in {"__pycache__", "node_modules"}:
                continue
            result.check(pattern not in text, f"Forbidden release text {pattern!r} found in {rel(root, path)}")
        result.check("/mnt/data/" not in text, f"Absolute local path found in {rel(root, path)}")
        result.check(text.lower().count("<script") == text.lower().count("</script>"), f"Unbalanced script tags in {rel(root, path)}")
        result.check(text.lower().count("<style") == text.lower().count("</style>"), f"Unbalanced style tags in {rel(root, path)}")
        for payload in JSON_SCRIPT_RE.findall(text):
            try:
                json.loads(payload)
            except json.JSONDecodeError as exc:
                result.errors.append(f"Invalid embedded JSON in {rel(root, path)}: {exc}")

    cursor = -1
    for path in t123_order:
        if not path.is_file():
            continue
        block = path.read_text(encoding="utf-8").rstrip()
        position = preview.find(block)
        result.check(position >= 0, f"T123 block is not embedded exactly in preview: {rel(root, path)}")
        if position >= 0:
            result.check(position > cursor, f"T123 order mismatch in preview: {rel(root, path)}")
            result.check(preview.count(block) == 1, f"T123 block must appear exactly once in preview: {rel(root, path)}")
            cursor = position

    node = shutil.which("node")
    if node:
        for path in t123_order:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for index, (attrs, script) in enumerate(SCRIPT_RE.findall(text), 1):
                if re.search(r"type=[\"']application/(?:json|ld\+json)[\"']", attrs, re.I):
                    continue
                with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as stream:
                    stream.write(script)
                    temp_path = Path(stream.name)
                try:
                    completed = subprocess.run([node, "--check", str(temp_path)], capture_output=True, text=True, check=False)
                    result.check(completed.returncode == 0, f"JavaScript syntax error in {rel(root, path)} script {index}: {completed.stderr.strip()}")
                finally:
                    temp_path.unlink(missing_ok=True)
    else:
        result.warnings.append("Node.js not found; JavaScript syntax check skipped")

    entries = parse_manifest(manifest_path, result)
    required_files = known_release_files(root, contract_path, contract)
    for file_name in sorted(required_files):
        path = root / file_name
        result.check(path.is_file(), f"Known release file is missing: {file_name}")
        result.check(file_name in entries, f"Known release file is missing from manifest: {file_name}")
    for file_name, expected_hash in entries.items():
        path = root / file_name
        if result.check(path.is_file(), f"Manifest references missing file: {file_name}"):
            result.check(sha256(path) == expected_hash, f"Manifest SHA-256 mismatch: {file_name}")
    result.check(rel(root, manifest_path) not in entries, "Manifest must not include itself")
    result.check(str(package.get("release_zip")) not in entries, "Manifest must not include release ZIP")

    if status in RELEASE_STATUSES:
        if result.check(zip_path.is_file(), f"Release ZIP is missing: {zip_path.name}"):
            try:
                with zipfile.ZipFile(zip_path) as archive:
                    bad_member = archive.testzip()
                    result.check(bad_member is None, f"Corrupt ZIP member: {bad_member}")
                    names = set(archive.namelist())
                    for file_name in required_files | {rel(root, manifest_path)}:
                        result.check(file_name in names, f"Release ZIP is missing: {file_name}")
                    for name in names:
                        result.check("__pycache__" not in name, f"Forbidden __pycache__ in ZIP: {name}")
                        result.check("node_modules" not in name, f"Forbidden node_modules in ZIP: {name}")
                        result.check(not name.endswith(".log"), f"Temporary log in ZIP: {name}")
                        result.check(not re.search(r"(?:project|proekt|draft|проект)", name, re.I), f"Project/draft file in ZIP: {name}")
            except zipfile.BadZipFile as exc:
                result.errors.append(f"Invalid release ZIP: {exc}")


def validate_package(contract_path: Path) -> ValidationResult:
    result = ValidationResult()
    contract_path = contract_path.resolve()
    root = contract_path.parent
    contract = load_json(contract_path, result, "PACKAGE CONTRACT")
    if not isinstance(contract, dict):
        return result

    validate_contract(contract, result)
    validate_sources(root, contract, result)

    maps = contract.get("maps") or {}
    exam_map_path = root / str(maps.get("exam", ""))
    exam_map = load_json(exam_map_path, result, "EXAM MAP")
    if isinstance(exam_map, dict):
        exam_contract = contract.get("exam") or {}
        for key in ("task_positions", "official_examples", "duration_minutes", "primary_max"):
            result.check(exam_map.get(key) == exam_contract.get(key), f"EXAM MAP mismatch for {key}")

    task_lookup, required_ids = validate_task_map(root, contract, result)
    validate_acceptance_cases(root, contract, task_lookup, required_ids, result)
    validate_asset_map(root, contract, task_lookup, result)
    validate_build_files(root, contract_path, contract, result)
    return result


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_self_test_package(root: Path, permissive: bool = False) -> Path:
    prefix = "ege-test-demoversiya"
    source_dir = root / "source"
    source_dir.mkdir(parents=True)
    sources = []
    for role, name in (
        ("demo", "demo.pdf"),
        ("specification", "specification.pdf"),
        ("codifier", "codifier.pdf"),
    ):
        path = source_dir / name
        path.write_bytes(b"%PDF-1.4\n% validator self-test\n")
        sources.append({"role": role, "path": f"source/{name}", "status": "final", "sha256": sha256(path), "pages": 1})

    task_map = {
        "schema_version": "1.0",
        "prefix": prefix,
        "tasks": [
            {
                "number": 1,
                "variant": 1,
                "kind": "short",
                "title": "Test",
                "prompt_html": "<p>Полное условие для тестового задания.</p>",
                "source": {"file_role": "demo", "prompt_pdf_page": 1, "answer_pdf_page": 1, "criteria_pdf_pages": []},
                "answer": {
                    "type": "exact_ordered_digits",
                    "canonical": "123",
                    "accepted": [{"value": "123", "source_pdf_page": 1, "basis": "official_answer_table"}],
                    "normalization": {
                        "trim": False,
                        "remove_internal_spaces": False,
                        "remove_punctuation": False,
                        "remove_non_digits": permissive,
                        "case_fold": False,
                        "yo_to_e": False,
                        "allow_decimal_comma": False,
                        "allow_decimal_point": False,
                    },
                },
                "max_score": 1,
                "partial_scoring": None,
                "dependencies": [],
                "asset_ids": [],
                "required_acceptance_case_ids": ["task-1-correct", "task-1-extra"],
            }
        ],
    }
    acceptance = {
        "schema_version": "1.0",
        "cases": [
            {"id": "task-1-correct", "task_number": 1, "variant": 1, "category": "positive", "input": "123", "expected_score": 1, "basis": "official"},
            {"id": "task-1-extra", "task_number": 1, "variant": 1, "category": "negative-extra-character", "input": "1a23", "expected_score": 0, "basis": "strict"},
        ],
    }
    exam_map = {"task_positions": 1, "official_examples": 1, "duration_minutes": 60, "primary_max": 1}
    asset_map = {"schema_version": "1.0", "assets": []}
    write_json(root / f"{prefix}-TASK-MAP.json", task_map)
    write_json(root / f"{prefix}-ACCEPTANCE-CASES.json", acceptance)
    write_json(root / f"{prefix}-EXAM-MAP.json", exam_map)
    write_json(root / f"{prefix}-ASSET-MAP.json", asset_map)

    head_name = f"{prefix}-HEAD.txt"
    t123_name = f"{prefix}-T123-01.txt"
    preview_name = f"{prefix}-PREVIEW.html"
    evidence_name = f"{prefix}-INDEPENDENT-TEST-EVIDENCE.json"
    report_name = f"{prefix}-TEST-REPORT.txt"
    manifest_name = f"{prefix}-MANIFEST.txt"
    zip_name = f"{prefix}-fixed.zip"
    seo_name = f"{prefix}-SEO.txt"

    head = '<link rel="canonical" href="https://eksamio.ru/ege/test/demoversiya/">'
    t123 = '<script type="application/json" id="data">{"tasks":[1]}</script>\n<script>window.demoReady=true;</script>'
    preview = f"<!doctype html><html><head>{head}</head><body>{t123}</body></html>\n"
    (root / head_name).write_text(head, encoding="utf-8")
    (root / t123_name).write_text(t123, encoding="utf-8")
    (root / preview_name).write_text(preview, encoding="utf-8")
    (root / evidence_name).write_text('{"status":"PASS"}\n', encoding="utf-8")
    (root / report_name).write_text("PASS — READY_FOR_TILDA_TEST\n", encoding="utf-8")
    (root / seo_name).write_text("Title: Тестовая демоверсия\n", encoding="utf-8")

    contract = {
        "schema_version": "1.0",
        "package": {"prefix": prefix, "version": "1.0.0", "status": "READY_FOR_TILDA_TEST", "release_zip": zip_name},
        "page": {
            "url": "https://eksamio.ru/ege/test/demoversiya/",
            "canonical": "https://eksamio.ru/ege/test/demoversiya/",
            "slug": "ege-test-demoversiya",
            "evergreen_public_metadata": True,
            "source_year": 2026,
        },
        "exam": exam_map,
        "sources": sources,
        "maps": {
            "exam": f"{prefix}-EXAM-MAP.json",
            "tasks": f"{prefix}-TASK-MAP.json",
            "assets": f"{prefix}-ASSET-MAP.json",
            "acceptance_cases": f"{prefix}-ACCEPTANCE-CASES.json",
        },
        "build": {
            "generated_files_must_not_be_edited": True,
            "t123_order": [t123_name],
            "head": head_name,
            "preview": preview_name,
            "manifest": manifest_name,
            "evidence": evidence_name,
            "test_report": report_name,
        },
        "storage": {
            "key": "eksamio_test_v1",
            "safe_wrapper_required": True,
            "absolute_end_time_required": True,
            "variant_choice_persistence_required": True,
        },
        "scoring": {
            "default_reject_extra_characters": True,
            "expert_self_assessment_affects_official_total": False,
            "all_dependencies_enforced_in_ui_and_scorer": True,
            "technical_heuristics_are_advisory_only": True,
        },
        "responsive_widths": [320, 360, 390, 768, 1280],
        "forbidden_release_patterns": ["ПРОЕКТ", "Локальный пакет проверен", "/mnt/data/", "__pycache__", "node_modules"],
        "publication": {"local_max_status": "READY_FOR_TILDA_TEST", "production_status": "PUBLISHED_SMOKE_PASS", "production_checked": False},
    }
    contract_path = root / f"{prefix}-PACKAGE-CONTRACT.json"
    write_json(contract_path, contract)

    files_for_manifest = [
        contract_path,
        root / f"{prefix}-EXAM-MAP.json",
        root / f"{prefix}-TASK-MAP.json",
        root / f"{prefix}-ASSET-MAP.json",
        root / f"{prefix}-ACCEPTANCE-CASES.json",
        root / head_name,
        root / t123_name,
        root / preview_name,
        root / evidence_name,
        root / report_name,
        root / seo_name,
        *[root / item["path"] for item in sources],
    ]
    manifest_lines = [f"{sha256(path)}  {rel(root, path)}" for path in sorted(files_for_manifest)]
    (root / manifest_name).write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    with zipfile.ZipFile(root / zip_name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files_for_manifest + [root / manifest_name]):
            archive.write(path, rel(root, path))
    return contract_path


def run_self_test() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "valid"
        root.mkdir()
        valid_contract = create_self_test_package(root, permissive=False)
        valid_result = validate_package(valid_contract)
        if not valid_result.ok:
            print("SELF-TEST VALID PACKAGE FAILED", file=sys.stderr)
            for error in valid_result.errors:
                print(f"- {error}", file=sys.stderr)
            return 1

        bad_root = Path(directory) / "bad"
        bad_root.mkdir()
        bad_contract = create_self_test_package(bad_root, permissive=True)
        bad_result = validate_package(bad_contract)
        if bad_result.ok or not any("remove_non_digits" in error for error in bad_result.errors):
            print("SELF-TEST DID NOT DETECT PERMISSIVE NORMALIZATION", file=sys.stderr)
            return 1

    print("validate_demo_package self-test: PASS")
    return 0


def print_result(result: ValidationResult) -> None:
    print(f"Checks: {result.checks}")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
        print("STATUS: FAIL")
    else:
        print("STATUS: PASS")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", nargs="?", type=Path, help="Path to PACKAGE-CONTRACT.json")
    parser.add_argument("--self-test", action="store_true", help="Run validator internal tests")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()
    if args.contract is None:
        parser.error("contract path is required unless --self-test is used")

    result = validate_package(args.contract)
    print_result(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
