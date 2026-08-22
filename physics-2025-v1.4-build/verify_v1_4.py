#!/usr/bin/env python3
"""Bounded static/package regression for the Physics 2025 v1.4 checkpoint."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

from lxml import html

from build_v1_4 import (
    ASSET_RE,
    EXPECTED_INPUT_TREE_SHA256,
    FIXED_CROPS,
    INPUT,
    PREFIX,
    ROOT,
    T123_LIMIT,
    file_sha,
    input_tree_sha,
    manifest_lines,
    read_assets,
    sha256,
)


OUTPUT = ROOT / "ege-fizika-demoversiya-2025-v1.4-TILDA-HQ-SOURCE"
ZIP_PATH = ROOT / "physics-2025-v1.4-build" / "dist" / "ege-fizika-demoversiya-2025-v1.4-TILDA-HQ-SOURCE.zip"
REFERENCE_2026 = ROOT / "ege-fizika-demoversiya-v3-1-fixed"


def check(condition: bool, label: str, evidence: object = True) -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{label}: {evidence}")
    return {"status": "PASS", "evidence": evidence}


def extract_function(source: str, name: str) -> str:
    match = re.search(rf"function {re.escape(name)}\([^\n]*", source)
    if not match:
        raise AssertionError(f"function not found: {name}")
    start = match.start()
    opening = source.find("{", match.start())
    depth = 0
    quote = None
    escaped = False
    for index in range(opening, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "'\"`":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"unterminated function: {name}")


def task_definitions(source: str) -> str:
    match = re.search(
        r'<script type="application/json" id="ephys-task-definitions">(.*?)</script>', source, re.S
    )
    if not match:
        raise AssertionError("task definitions not found")
    parsed = json.loads(match.group(1))
    return json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def result_order(source: str) -> list[str]:
    result = re.search(r'<div class="ephys-result">(.*?)</div>\s*<div class="ephys-modal"', source, re.S)
    if not result:
        raise AssertionError("result DOM not found")
    return re.findall(r'<h2 class="ep-section-title">([^<]+)</h2>', result.group(1))


def asset_payloads(blocks: list[str]) -> dict[str, bytes]:
    parts: dict[str, list[tuple[int, int, str]]] = {}
    for block in blocks:
        for match in ASSET_RE.finditer(block):
            name, _mime, part, total, payload = match.groups()
            parts.setdefault(name, []).append((int(part), int(total), payload))
    result = {}
    for name, values in parts.items():
        values.sort()
        assert len(values) == values[0][1]
        result[name] = base64.b64decode("".join(value[2] for value in values))
    return result


def direct_text_nodes(document_path: Path) -> dict[str, list[str]]:
    tree = html.document_fromstring(document_path.read_bytes())
    result = {}
    for selector, nodes in {
        "html": tree.xpath("/html"),
        "body": tree.xpath("/html/body"),
        "root": tree.xpath('//*[@id="ege-physics-demo-2025"]'),
    }.items():
        texts = []
        for node in nodes:
            if node.text and node.text.strip():
                texts.append(node.text.strip())
            for child in node:
                if child.tail and child.tail.strip():
                    texts.append(child.tail.strip())
        result[selector] = texts
    return result


def main() -> int:
    report: dict[str, object] = {}
    report["immutable_input"] = check(
        input_tree_sha() == EXPECTED_INPUT_TREE_SHA256,
        "immutable input tree",
        EXPECTED_INPUT_TREE_SHA256,
    )

    block_paths = sorted(OUTPUT.glob(f"{PREFIX}-T123-[0-9][0-9].txt"))
    blocks = [path.read_text(encoding="utf-8") for path in block_paths]
    report["t123"] = check(
        len(blocks) == 48 and all(path.stat().st_size < T123_LIMIT for path in block_paths),
        "T123 count/limit",
        {"count": len(blocks), "max_bytes": max(path.stat().st_size for path in block_paths)},
    )

    lint = json.loads((OUTPUT / f"{PREFIX}-TILDA-HTML-LINT.json").read_text(encoding="utf-8"))
    report["html_lint"] = check(lint["all_pass"] and lint["no_tag_split_across_blocks"], "HTML lint")

    packaged_assets = asset_payloads(blocks)
    gate = json.loads((OUTPUT / f"{PREFIX}-VISUAL-FOUR-EDGE-GATE.json").read_text(encoding="utf-8"))
    report["visual_assets"] = check(
        len(packaged_assets) == 56
        and gate["all_assets_pass"]
        and all(sha256(raw) == gate["assets"][name]["sha256"] for name, raw in packaged_assets.items()),
        "visual assets",
        {"asset_count": len(packaged_assets), "corrected_crops": len(FIXED_CROPS), "four_edge": "56/56"},
    )

    old_ui = (INPUT / f"{PREFIX}-T123-01.txt").read_text(encoding="utf-8")
    new_ui = blocks[0]
    report["task_definitions"] = check(
        task_definitions(old_ui) == task_definitions(new_ui),
        "task definitions unchanged",
        sha256(task_definitions(new_ui).encode("utf-8")),
    )

    old_runtime = (INPUT / f"{PREFIX}-T123-47.txt").read_text(encoding="utf-8")
    new_runtime = blocks[-1]
    invariant_functions = [
        "loadState", "saveState", "strictNumberString", "orderedValues", "unorderedScore",
        "scoreTask", "startExam", "resumeExam", "calculateShortScore", "finishExam",
        "selfDefinitions", "extendedScore", "installSymbolKeyboards", "calcEvaluate",
    ]
    function_hashes = {}
    for name in invariant_functions:
        old_function = extract_function(old_runtime, name)
        new_function = extract_function(new_runtime, name)
        if old_function != new_function:
            raise AssertionError(f"invariant function changed: {name}")
        function_hashes[name] = sha256(new_function.encode("utf-8"))
    report["runtime_invariants"] = check(True, "runtime invariants", function_hashes)

    reference_ui = (REFERENCE_2026 / "ege-fizika-demoversiya-T123-01.txt").read_text(encoding="utf-8")
    expected_generic_order = [
        "Результат попытки", "Самооценка заданий 21–26", "Проверка заданий", "Источники и статус страницы"
    ]
    report["result_parity"] = check(
        result_order(new_ui) == expected_generic_order
        and len(result_order(reference_ui)) == 4
        and result_order(old_ui) != expected_generic_order,
        "result composition",
        {"v1_3": result_order(old_ui), "v1_4": result_order(new_ui), "reference_2026": result_order(reference_ui)},
    )

    all_t123 = "\n".join(blocks)
    report["no_2026_leak"] = check(
        "ФИПИ 2026" not in all_t123
        and "physics-demo-2026" not in all_t123
        and "physics_demo_2026" not in all_t123,
        "2026 content leak",
        "no 2026 year/content/runtime identifiers in v1.4 T123",
    )
    ref_runtime = (REFERENCE_2026 / "ege-fizika-demoversiya-T123-06.txt").read_text(encoding="utf-8")
    key_2025 = re.search(r'STORAGE_KEY="([^"]+)"', new_runtime).group(1)
    key_2026 = re.search(r'STORAGE_KEY="([^"]+)"', ref_runtime).group(1)
    report["storage_isolation"] = check(key_2025 != key_2026, "storage isolation", {"2025": key_2025, "2026": key_2026})

    head = (OUTPUT / f"{PREFIX}-HEAD.txt").read_bytes()
    head_text = head.decode("utf-8")
    dom_text = direct_text_nodes(OUTPUT / f"{PREFIX}-TILDA-SHELL-PREVIEW.html")
    report["top_of_page"] = check(
        not head.startswith(b"\xef\xbb\xbf")
        and head_text.lstrip().startswith("<")
        and "PAGE HEAD / TILDA SEO" not in head_text
        and "Что это за страница" not in head_text
        and not any(dom_text.values()),
        "top-of-page physical DOM",
        {"utf8": True, "bom": False, "direct_text_nodes": dom_text},
    )

    manifest_path = OUTPUT / f"{PREFIX}-OUTPUT-MANIFEST.sha256"
    expected_manifest = "\n".join(manifest_lines(OUTPUT, {
        "SHA256SUMS.txt", f"{PREFIX}-OUTPUT-MANIFEST.sha256", f"{PREFIX}-OUTPUT-BUILD-SHA256.txt"
    })) + "\n"
    actual_manifest = manifest_path.read_text(encoding="utf-8")
    recorded_build = re.search(
        r"OUTPUT_BUILD_SHA256=([0-9a-f]{64})",
        (OUTPUT / f"{PREFIX}-OUTPUT-BUILD-SHA256.txt").read_text(encoding="utf-8"),
    ).group(1)
    report["output_manifest"] = check(
        actual_manifest == expected_manifest and sha256(actual_manifest.encode("utf-8")) == recorded_build,
        "output manifest",
        recorded_build,
    )

    with zipfile.ZipFile(ZIP_PATH) as archive:
        bad = archive.testzip()
        names = archive.namelist()
    report["zip"] = check(
        bad is None and names == sorted(names),
        "clean deterministic zip",
        {"sha256": file_sha(ZIP_PATH), "entries": len(names), "sorted": True},
    )

    report["status"] = "PASS"
    result_path = ROOT / "physics-2025-v1.4-build" / "STATIC-REGRESSION.json"
    result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
