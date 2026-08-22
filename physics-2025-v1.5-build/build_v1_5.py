#!/usr/bin/env python3
"""Build the bounded Physics 2025 v1.5 result-order checkpoint from v1.4.

The historical v1.4 tree is immutable.  This builder changes only the result
DOM and its renderer: short-answer cards 1–20 are rendered before the
self-assessment/extended-review block for tasks 21–26.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "ege-fizika-demoversiya-2025-v1.4-TILDA-HQ-SOURCE"
DEFAULT_OUTPUT = ROOT / "ege-fizika-demoversiya-2025-v1.5-TILDA-HQ-SOURCE"
BUILD_ROOT = Path(__file__).resolve().parent
PREFIX = "ege-fizika-demoversiya-2025"
EXPECTED_INPUT_BUILD_SHA256 = "2780a729967e70355a8ae52e726c67abe8597dff3ce2d5b0c55da635791f2e13"
T123_LIMIT = 42_500


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes())


def manifest_lines(directory: Path, excluded: set[str] | None = None) -> list[str]:
    excluded = excluded or set()
    lines = []
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        rel = path.relative_to(directory).as_posix()
        if rel not in excluded:
            lines.append(f"{file_sha(path)}  {rel}")
    return lines


def verify_input() -> None:
    excluded = {
        "SHA256SUMS.txt",
        f"{PREFIX}-OUTPUT-MANIFEST.sha256",
        f"{PREFIX}-OUTPUT-BUILD-SHA256.txt",
    }
    manifest = "\n".join(manifest_lines(INPUT, excluded)) + "\n"
    recorded_manifest = (INPUT / f"{PREFIX}-OUTPUT-MANIFEST.sha256").read_text(encoding="utf-8")
    if manifest != recorded_manifest:
        raise RuntimeError("immutable v1.4 manifest mismatch")
    actual = sha256(manifest.encode("utf-8"))
    if actual != EXPECTED_INPUT_BUILD_SHA256:
        raise RuntimeError(f"immutable v1.4 build mismatch: {actual}")


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new)


def patch_ui(text: str) -> str:
    old = '''<section class="ep-panel"><h2 class="ep-section-title">Самооценка заданий 21–26</h2><p>Сравните сохранённое решение с официальным возможным решением и критериями ФИПИ 2025, затем выберите балл для каждого задания. Пока оценены не все задания, общий результат не считается окончательным.</p><div class="ephys-self-grid" id="ephys-self-grid"></div></section>
<section class="ep-panel"><h2 class="ep-section-title">Проверка заданий</h2><div class="ephys-review-list" id="ephys-review"></div></section>'''
    new = '''<section class="ep-panel"><h2 class="ep-section-title">Проверка заданий</h2><div class="ephys-review-list" id="ephys-review"></div></section>
<section class="ep-panel"><h2 class="ep-section-title">Самооценка заданий 21–26</h2><p>Сравните сохранённое решение с официальным возможным решением и критериями ФИПИ 2025, затем выберите балл для каждого задания. Пока оценены не все задания, общий результат не считается окончательным.</p><div class="ephys-self-grid" id="ephys-self-grid"></div><div class="ephys-review-list" id="ephys-extended-review"></div></section>'''
    return replace_exact(text, old, new, "result section order")


def patch_runtime(text: str) -> str:
    pattern = re.compile(
        r'function renderReview\(\)\{.*?\nfunction renderResults\(\)\{applyResultSemantics\(\);buildSelfAssessment\(\);renderScoreCards\(\);renderReview\(\)\}',
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError("v1.4 review renderer block not found")
    replacement = '''function renderReview(){var w=byId("ephys-review");w.innerHTML="";allTasks().filter(function(t){return t.number<=20}).forEach(function(t){var item=document.createElement("article");item.className="ephys-review-item";var pts=scoreTask(t,getAnswer(t.number));item.setAttribute("data-correct",pts===t.maxScore?"true":"false");item.innerHTML='<h3>Задание '+t.number+' · '+pts+'/'+t.maxScore+'</h3><p>Ваш ответ: <strong>'+escapeHtml(userAnswer(t,getAnswer(t.number)))+'</strong></p><p>Ответ ФИПИ: <strong>'+escapeHtml(t.answerDisplay)+'</strong></p><p class="ephys-mini">Для этой позиции в демоверсии ФИПИ 2025 опубликован эталон краткого ответа.</p>';w.appendChild(item);bindZoom(item)})}
function renderExtendedReview(){var w=byId("ephys-extended-review");w.innerHTML="";allTasks().filter(function(t){return t.number>20}).forEach(function(t){var item=document.createElement("article");item.className="ephys-review-item";var label='ФИПИ 2025 · официальный пример '+(t.number===26?state.variant26:1);item.innerHTML='<div class="ephys-official-label">'+label+'</div><h3>Задание '+t.number+' · максимум '+t.maxScore+'</h3><p><strong>Ваше решение</strong></p><div class="ephys-solution">'+escapeHtml(getAnswer(t.number)||"Ответ не введён").replace(/\\n/g,"<br>")+'</div><details open><summary><strong>Официальное возможное решение ФИПИ</strong></summary><div class="ephys-solution">'+sourceStack(t.solutionAssets)+'</div></details><details><summary><strong>Официальные критерии оценивания ФИПИ</strong></summary><div class="ephys-criteria">'+sourceStack(t.criteriaAssets)+'</div></details>';w.appendChild(item);bindZoom(item)})}
function renderResults(){applyResultSemantics();renderScoreCards();renderReview();buildSelfAssessment();renderExtendedReview()}'''
    return text[: match.start()] + replacement + text[match.end() :]


def html_head() -> str:
    return '''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Демоверсия ЕГЭ 2025 по физике — ФИПИ | Эксамио</title><meta name="description" content="Интерактивная демоверсия ЕГЭ 2025 по физике по материалам ФИПИ: 26 заданий, 235 минут, проверка ответов, решения и критерии оценивания."><meta name="robots" content="index,follow"><link rel="canonical" href="https://eksamio.ru/ege/fizika/demoversiya/2025/"><meta property="og:type" content="website"><meta property="og:title" content="Демоверсия ЕГЭ 2025 по физике — ФИПИ | Эксамио"><meta property="og:description" content="Интерактивная демоверсия ЕГЭ 2025 по физике по материалам ФИПИ: 26 заданий, 235 минут, проверка ответов, решения и критерии оценивания."><meta property="og:url" content="https://eksamio.ru/ege/fizika/demoversiya/2025/"></head><body>\n'''


def write_html_lint(output: Path, block_paths: list[Path]) -> None:
    import json

    files = []
    for path in block_paths:
        text = path.read_text(encoding="utf-8")
        checks = {
            "script": [text.count("<script"), text.count("</script>")],
            "style": [text.count("<style"), text.count("</style>")],
            "div": [text.count("<div"), text.count("</div>")],
            "section": [text.count("<section"), text.count("</section>")],
        }
        balanced = all(opened == closed for opened, closed in checks.values())
        files.append({
            "file": path.name,
            "bytes": path.stat().st_size,
            "under_limit": path.stat().st_size < T123_LIMIT,
            "tag_counts_open_close": checks,
            "balanced": balanced,
            "independently_closed": balanced,
            "pass": balanced and path.stat().st_size < T123_LIMIT,
        })
    report = {
        "t123_count": len(files),
        "limit_bytes": T123_LIMIT,
        "no_tag_split_across_blocks": all(item["independently_closed"] for item in files),
        "all_pass": all(item["pass"] for item in files),
        "files": files,
    }
    (output / f"{PREFIX}-TILDA-HTML-LINT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_package_metadata(output: Path, block_paths: list[Path]) -> None:
    maximum = max(path.stat().st_size for path in block_paths)
    (output / "00-README-TILDA.txt").write_text(
        f'''EGE PHYSICS 2025 — TILDA FINAL HQ SOURCE BUILD v1.5

BOUNDED RESULT-ORDER FIX OVER IMMUTABLE v1.4
- content, answers, scoring, solutions, criteria, assets and tools are unchanged;
- result order is: score summary, Проверка заданий 1–20, Самооценка заданий 21–26 with unchanged extended review, source/status;
- Physics 2026 is a technical sequence reference only; all content remains Physics 2025.

TILDA PATCH FROM DEPLOYED v1.4
- HEAD: unchanged
- T123-01: replace
- T123-48: replace
- all other T123 blocks: unchanged

Paste T123-01 ... T123-48 strictly in order for a clean install.
CANONICAL=https://eksamio.ru/ege/fizika/demoversiya/2025/
''',
        encoding="utf-8",
    )
    (output / f"{PREFIX}-ACCEPTANCE.txt").write_text(
        f'''EGE PHYSICS 2025 v1.5 RESULT-ORDER FIX

INPUT_V1_4_BUILD_SHA256={EXPECTED_INPUT_BUILD_SHA256}
CONTENT_TASK_DEFINITIONS=UNCHANGED_FROM_V1.4
ANSWERS_SOLUTIONS_CRITERIA_POINTS=UNCHANGED_FROM_V1.4
SCORING_RUNTIME=UNCHANGED_FROM_V1.4
VISUAL_ASSETS=UNCHANGED_56_OF_56
TASK_12_CROP=UNCHANGED
HEAD=UNCHANGED
RESULT_ORDER=SHORT_REVIEW_1_20_THEN_SELF_ASSESSMENT_21_26
TILDA_CHANGED_ARTIFACTS=T123-01,T123-48
T123_COUNT={len(block_paths)}
MAX_T123_BYTES={maximum}
CONTENT_YEAR=2025
''',
        encoding="utf-8",
    )
    lines = ["EGE PHYSICS 2025 — TILDA HQ SOURCE BUILD v1.5", "", "LOAD ORDER:"]
    for index, path in enumerate(block_paths, 1):
        role = "UI/CSS/task definitions" if index == 1 else "runtime/scorer/state" if index == len(block_paths) else "FIPI-2025 official image payload"
        lines.append(f"{index:02d}. {path.name} | {path.stat().st_size} bytes | {role}")
    lines.extend([
        "",
        f"T123_COUNT={len(block_paths)}",
        f"MAX_T123_BYTES={maximum}",
        f"TILDA_LIMIT_BYTES={T123_LIMIT}",
        "TILDA_PATCH_FROM_V1.4=T123-01,T123-48",
        "HEAD_PATCH_FROM_V1.4=NONE",
        "IMAGE_SOURCE=unchanged exact FIPI 2025 assets from immutable v1.4",
        "",
    ])
    (output / f"{PREFIX}-T123-MANIFEST.txt").write_text("\n".join(lines), encoding="utf-8")


def write_manifest_and_hash(output: Path) -> str:
    excluded = {
        "SHA256SUMS.txt",
        f"{PREFIX}-OUTPUT-MANIFEST.sha256",
        f"{PREFIX}-OUTPUT-BUILD-SHA256.txt",
    }
    manifest = "\n".join(manifest_lines(output, excluded)) + "\n"
    build_hash = sha256(manifest.encode("utf-8"))
    (output / "SHA256SUMS.txt").write_text(manifest, encoding="utf-8")
    (output / f"{PREFIX}-OUTPUT-MANIFEST.sha256").write_text(manifest, encoding="utf-8")
    (output / f"{PREFIX}-OUTPUT-BUILD-SHA256.txt").write_text(
        f"OUTPUT_BUILD_SHA256={build_hash}\n"
        "DEFINITION=SHA-256 of OUTPUT-MANIFEST.sha256 bytes; manifest excludes itself, SHA256SUMS.txt, and this hash file.\n",
        encoding="utf-8",
    )
    return build_hash


def deterministic_zip(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            rel = (Path(source.name) / path.relative_to(source)).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(2025, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return file_sha(destination)


def build(output: Path, zip_path: Path) -> tuple[str, str]:
    verify_input()
    if output.exists():
        raise RuntimeError(f"output already exists: {output}")
    shutil.copytree(INPUT, output)

    ui_path = output / f"{PREFIX}-T123-01.txt"
    runtime_path = output / f"{PREFIX}-T123-48.txt"
    ui_path.write_text(patch_ui(ui_path.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    runtime_path.write_text(patch_runtime(runtime_path.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")

    block_paths = sorted(output.glob(f"{PREFIX}-T123-[0-9][0-9].txt"))
    blocks = [path.read_text(encoding="utf-8") for path in block_paths]
    if len(blocks) != 48 or any(path.stat().st_size >= T123_LIMIT for path in block_paths):
        raise RuntimeError("T123 count/size gate failed")

    preview = html_head() + "\n".join(blocks) + "\n</body></html>\n"
    (output / f"{PREFIX}-PREVIEW.html").write_text(preview, encoding="utf-8", newline="\n")
    (output / f"{PREFIX}-CLEAN-UNPACK-PREVIEW.html").write_text(preview, encoding="utf-8", newline="\n")
    head = (output / f"{PREFIX}-SEO-HEAD-CODE.html").read_text(encoding="utf-8")
    wrappers = "\n".join(f'<div class="r t-rec"><div class="t123">{block}</div></div>' for block in blocks)
    shell = '<!doctype html><html lang="ru"><head><meta charset="utf-8">' + head + '</head><body class="t-body"><div id="allrecords" class="t-records">' + wrappers + "</div></body></html>\n"
    (output / f"{PREFIX}-TILDA-SHELL-PREVIEW.html").write_text(shell, encoding="utf-8", newline="\n")

    write_html_lint(output, block_paths)
    write_package_metadata(output, block_paths)
    build_hash = write_manifest_and_hash(output)
    zip_hash = deterministic_zip(output, zip_path)
    return build_hash, zip_hash


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--zip",
        type=Path,
        default=BUILD_ROOT / "dist" / "ege-fizika-demoversiya-2025-v1.5-TILDA-HQ-SOURCE.zip",
    )
    args = parser.parse_args()
    build_hash, zip_hash = build(args.output.resolve(), args.zip.resolve())
    print(f"INPUT_V1_4_BUILD_SHA256={EXPECTED_INPUT_BUILD_SHA256}")
    print(f"OUTPUT_BUILD_SHA256={build_hash}")
    print(f"OUTPUT_ZIP_SHA256={zip_hash}")
    print(f"OUTPUT={args.output.resolve()}")
    print(f"ZIP={args.zip.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
