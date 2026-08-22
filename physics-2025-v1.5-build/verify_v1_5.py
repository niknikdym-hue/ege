#!/usr/bin/env python3
"""Static and package regression for Physics 2025 v1.5."""

from __future__ import annotations

import base64
import io
import json
import re
import sys
import zipfile
from pathlib import Path

from lxml import html
from PIL import Image

from build_v1_5 import (
    EXPECTED_INPUT_BUILD_SHA256,
    INPUT,
    PREFIX,
    ROOT,
    T123_LIMIT,
    file_sha,
    manifest_lines,
    sha256,
    verify_input,
)


OUTPUT = ROOT / "ege-fizika-demoversiya-2025-v1.5-TILDA-HQ-SOURCE"
ZIP_PATH = ROOT / "physics-2025-v1.5-build" / "dist" / "ege-fizika-demoversiya-2025-v1.5-TILDA-HQ-SOURCE.zip"
STATIC_REPORT = ROOT / "physics-2025-v1.5-build" / "STATIC-REGRESSION.json"
ASSET_RE = re.compile(
    r'<script type="text/plain" class="ephys-asset-part" '
    r'data-asset="([^"]+)" data-mime="([^"]+)" '
    r'data-part="(\d+)" data-total="(\d+)">([^<]*)</script>'
)


def check(condition: bool, label: str, evidence: object = True) -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{label}: {evidence}")
    return {"status": "PASS", "evidence": evidence}


def extract_function(source: str, name: str) -> str:
    match = re.search(rf"function {re.escape(name)}\([^\n]*", source)
    if not match:
        raise AssertionError(f"function not found: {name}")
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
                return source[match.start() : index + 1]
    raise AssertionError(f"unterminated function: {name}")


def task_definitions(source: str) -> tuple[str, dict[str, object]]:
    match = re.search(r'<script type="application/json" id="ephys-task-definitions">(.*?)</script>', source, re.S)
    if not match:
        raise AssertionError("task definitions not found")
    parsed = json.loads(match.group(1))
    normalized = json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return normalized, parsed


def result_dom(source: str):
    match = re.search(r'<div class="ephys-result">(.*?)</div>\s*</div></div>\s*<div class="ephys-modal"', source, re.S)
    if not match:
        raise AssertionError("result DOM not found")
    fragment = html.fragment_fromstring('<div class="ephys-result">' + match.group(1) + "</div>")
    return fragment


def asset_payloads(blocks: list[str]) -> dict[str, bytes]:
    parts: dict[str, list[tuple[int, int, str]]] = {}
    for block in blocks:
        for match in ASSET_RE.finditer(block):
            name, _mime, part, total, payload = match.groups()
            parts.setdefault(name, []).append((int(part), int(total), payload))
    result = {}
    for name, values in parts.items():
        values.sort()
        if len(values) != values[0][1]:
            raise AssertionError(f"asset part count: {name}")
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
    verify_input()
    report["immutable_v1_4"] = check(True, "immutable v1.4", EXPECTED_INPUT_BUILD_SHA256)

    old_paths = sorted(INPUT.glob(f"{PREFIX}-T123-[0-9][0-9].txt"))
    new_paths = sorted(OUTPUT.glob(f"{PREFIX}-T123-[0-9][0-9].txt"))
    old_blocks = [path.read_text(encoding="utf-8") for path in old_paths]
    new_blocks = [path.read_text(encoding="utf-8") for path in new_paths]
    report["t123"] = check(
        len(new_paths) == 48 and all(path.stat().st_size < T123_LIMIT for path in new_paths),
        "T123 count/size",
        {"count": len(new_paths), "max_bytes": max(path.stat().st_size for path in new_paths)},
    )
    changed_t123 = [new.name for old, new in zip(old_paths, new_paths) if old.read_bytes() != new.read_bytes()]
    report["tilda_patch"] = check(
        changed_t123 == [f"{PREFIX}-T123-01.txt", f"{PREFIX}-T123-48.txt"],
        "bounded Tilda patch",
        {"HEAD": "unchanged", "changed": changed_t123},
    )
    report["head"] = check(
        (INPUT / f"{PREFIX}-HEAD.txt").read_bytes() == (OUTPUT / f"{PREFIX}-HEAD.txt").read_bytes()
        and (INPUT / f"{PREFIX}-SEO-HEAD-CODE.html").read_bytes() == (OUTPUT / f"{PREFIX}-SEO-HEAD-CODE.html").read_bytes(),
        "head unchanged",
    )

    old_defs, old_data = task_definitions(old_blocks[0])
    new_defs, new_data = task_definitions(new_blocks[0])
    report["content_invariance"] = check(
        old_defs == new_defs,
        "task definitions/content/answers/solutions/criteria/points unchanged",
        {"sha256": sha256(new_defs.encode("utf-8")), "tasks": len(new_data["tasks"]) + 1},
    )
    report["payload_blocks"] = check(
        all(old.read_bytes() == new.read_bytes() for old, new in zip(old_paths[1:47], new_paths[1:47])),
        "asset T123 blocks unchanged",
        "T123-02..47 byte-identical",
    )

    old_assets = asset_payloads(old_blocks)
    new_assets = asset_payloads(new_blocks)
    report["visuals"] = check(
        len(new_assets) == 56
        and old_assets.keys() == new_assets.keys()
        and all(old_assets[name] == new_assets[name] for name in old_assets),
        "visual assets unchanged",
        "56/56 byte-identical to accepted v1.4",
    )
    task12 = new_assets["prompt-12"]
    with Image.open(io.BytesIO(task12)) as image:
        task12_size = list(image.size)
    report["task_12"] = check(
        sha256(task12) == "89be94f5daab071bb7f7f7bdd3e77e7e025806ae49814ee0a3601f495aa6477a"
        and task12_size == [1254, 326],
        "Task 12 unchanged",
        {"sha256": sha256(task12), "dimensions": task12_size, "crop": [55, 197, 1309, 523]},
    )

    old_runtime = old_blocks[-1]
    new_runtime = new_blocks[-1]
    invariant_functions = [
        "loadState", "saveState", "strictNumberString", "orderedValues", "unorderedScore",
        "scoreTask", "answerField", "bindAnswer", "startExam", "resumeExam",
        "calculateShortScore", "finishExam", "selfDefinitions", "extendedComplete",
        "extendedScore", "buildSelfAssessment", "renderScoreCards", "resetAttempt",
        "installSymbolKeyboards", "calcEvaluate",
    ]
    function_hashes = {}
    for name in invariant_functions:
        old_function = extract_function(old_runtime, name)
        new_function = extract_function(new_runtime, name)
        if old_function != new_function:
            raise AssertionError(f"invariant function changed: {name}")
        function_hashes[name] = sha256(new_function.encode("utf-8"))
    scorer_evidence = json.loads((OUTPUT / f"{PREFIX}-SCORER-EVIDENCE.json").read_text(encoding="utf-8"))
    short_max = sum(int(task["maxScore"]) for task in new_data["tasks"] if int(task["number"]) <= 20)
    extended_max = sum(int(task["maxScore"]) for task in new_data["tasks"] if int(task["number"]) >= 21) + int(new_data["variants26"][0]["maxScore"])
    report["scorer"] = check(
        short_max == 28 and extended_max == 17 and all(case["pass"] for case in scorer_evidence),
        "scorer invariance",
        {"short": "28/28", "extended": "17/17", "total": "45/45", "function_hashes": function_hashes},
    )

    dom = result_dom(new_blocks[0])
    headings = ["".join(node.itertext()).strip() for node in dom.xpath('.//h2[contains(@class,"ep-section-title")]')]
    review_sections = dom.xpath('.//section[.//h2[normalize-space()="Проверка заданий"]]')
    self_sections = dom.xpath('.//section[.//h2[normalize-space()="Самооценка заданий 21–26"]]')
    report["result_structure"] = check(
        headings == ["Результат попытки", "Проверка заданий", "Самооценка заданий 21–26", "Источники и статус страницы"]
        and len(review_sections) == 1
        and len(self_sections) == 1
        and len(review_sections[0].xpath('.//*[@id="ephys-review"]')) == 1
        and len(self_sections[0].xpath('.//*[@id="ephys-self-grid"]')) == 1
        and len(self_sections[0].xpath('.//*[@id="ephys-extended-review"]')) == 1,
        "result DOM order",
        headings,
    )
    report["renderer_structure"] = check(
        'allTasks().filter(function(t){return t.number<=20})' in extract_function(new_runtime, "renderReview")
        and 'allTasks().filter(function(t){return t.number>20})' in extract_function(new_runtime, "renderExtendedReview")
        and extract_function(new_runtime, "renderResults").endswith("renderReview();buildSelfAssessment();renderExtendedReview()}"),
        "semantic renderer split",
        "DOM/source logic; no CSS ordering",
    )

    combined = "\n".join(new_blocks)
    report["no_2026_leak"] = check(
        "ФИПИ 2026" not in combined
        and "physics-demo-2026" not in combined
        and "physics_demo_2026" not in combined,
        "2026 leakage",
        0,
    )
    direct = direct_text_nodes(OUTPUT / f"{PREFIX}-TILDA-SHELL-PREVIEW.html")
    head_bytes = (OUTPUT / f"{PREFIX}-HEAD.txt").read_bytes()
    report["top_of_page"] = check(
        not head_bytes.startswith(b"\xef\xbb\xbf")
        and head_bytes.decode("utf-8").lstrip().startswith("<")
        and not any(direct.values()),
        "no garbled/foreign top text",
        direct,
    )

    lint = json.loads((OUTPUT / f"{PREFIX}-TILDA-HTML-LINT.json").read_text(encoding="utf-8"))
    report["html_lint"] = check(lint["all_pass"] and lint["no_tag_split_across_blocks"], "HTML lint")
    excluded = {"SHA256SUMS.txt", f"{PREFIX}-OUTPUT-MANIFEST.sha256", f"{PREFIX}-OUTPUT-BUILD-SHA256.txt"}
    expected_manifest = "\n".join(manifest_lines(OUTPUT, excluded)) + "\n"
    actual_manifest = (OUTPUT / f"{PREFIX}-OUTPUT-MANIFEST.sha256").read_text(encoding="utf-8")
    recorded_build = re.search(
        r"OUTPUT_BUILD_SHA256=([0-9a-f]{64})",
        (OUTPUT / f"{PREFIX}-OUTPUT-BUILD-SHA256.txt").read_text(encoding="utf-8"),
    ).group(1)
    report["manifest"] = check(
        expected_manifest == actual_manifest and sha256(actual_manifest.encode("utf-8")) == recorded_build,
        "output manifest",
        recorded_build,
    )

    with zipfile.ZipFile(ZIP_PATH) as archive:
        bad = archive.testzip()
        names = archive.namelist()
        root_prefix = OUTPUT.name + "/"
        clean_names = all(name.startswith(root_prefix) and ".." not in Path(name).parts for name in names)
    report["clean_package"] = check(
        bad is None and names == sorted(names) and clean_names,
        "clean deterministic ZIP",
        {"sha256": file_sha(ZIP_PATH), "entries": len(names), "sorted": True},
    )
    report["status"] = "PASS"
    STATIC_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
