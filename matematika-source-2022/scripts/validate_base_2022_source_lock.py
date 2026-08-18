#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent

EXPECTED_HASHES = {
    "ege-2022-matematika-baza-demoversiya.pdf": "8b2c6fe0e36eb1d3a749af08cd035b142ea5e7099dbdf9a14e4ff1617470e207",
    "ege-2022-matematika-baza-specifikatsiya.pdf": "6480c1fffd0c2a09e9447d21b44f3a683b83aaa251f5f8c55ceb21a00c92fe9b",
    "ege-2022-matematika-kodifikator.pdf": "28888224281fd2178f600b959e652237f3d34f80afe5b2875a9d06a6b4804813",
}
EXPECTED_COUNTS = [2, 3, 2, 3, 2, 3, 4, 2, 3, 2, 2, 3, 2, 3, 1, 3, 2, 2, 3, 2, 3]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(msg: str):
    raise SystemExit(f"BASE 2022 SOURCE LOCK FAIL: {msg}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis-dir", type=Path, default=None)
    args = ap.parse_args()

    for filename, expected in EXPECTED_HASHES.items():
        path = ROOT / filename
        if not path.exists():
            fail(f"missing source PDF: {filename}")
        actual = sha256(path)
        if actual != expected:
            fail(f"SHA mismatch for {filename}: {actual} != {expected}")

    lock_dir = ROOT / "source-lock"
    exam = load_json(lock_dir / "EXAM-LOCK.json")
    answers = load_json(lock_dir / "ANSWER-LOCK.json")
    visual = load_json(lock_dir / "VISUAL-INVENTORY.json")

    if exam["year"] != 2022 or exam["exam_structure"]["task_count"] != 21:
        fail("exam lock year/task_count")
    if exam["exam_structure"]["duration_minutes"] != 180:
        fail("duration must be 180")
    if exam["exam_structure"]["max_primary_score"] != 21:
        fail("max primary score must be 21")
    if exam["exam_structure"]["examples_per_task"] != EXPECTED_COUNTS:
        fail("examples_per_task changed")
    if sum(EXPECTED_COUNTS) != 52 or exam["exam_structure"]["official_example_count"] != 52:
        fail("official example count must be 52")
    if exam["exam_structure"]["reference_printed_pages"] != [4, 5, 6, 7]:
        fail("reference page lock changed")
    if exam["exam_structure"]["answer_table_printed_page"] != 25:
        fail("answer table page must be 25")

    answer_tasks = answers.get("tasks", {})
    if sorted(map(int, answer_tasks.keys())) != list(range(1, 22)):
        fail("answer task keys are not 1..21")
    variant_count = sum(len(v) for v in answer_tasks.values())
    if variant_count != 52:
        fail(f"answer variant count {variant_count} != 52")
    for task_num, expected_count in enumerate(EXPECTED_COUNTS, 1):
        if len(answer_tasks[str(task_num)]) != expected_count:
            fail(f"task {task_num} answer count mismatch")

    variants = exam["variant_source_pages"]
    if len(variants) != 52:
        fail(f"variant_source_pages count {len(variants)} != 52")
    for task_num, expected_count in enumerate(EXPECTED_COUNTS, 1):
        expected_ids = [f"{task_num}.{i}" for i in range(1, expected_count + 1)]
        missing = [v for v in expected_ids if v not in variants]
        if missing:
            fail(f"missing source-page variants: {missing}")

    # Source anomaly is intentionally hard-locked so a later build cannot invent task 1.3.
    if "1.3" in variants:
        fail("phantom task 1.3 must not exist")
    task6v3 = answer_tasks["6"][2]
    if task6v3.get("variant") != "6.3" or task6v3.get("accepted") != ["9"]:
        fail("task 6.3 must be locked to answer 9")
    if answers.get("source_anomaly", {}).get("id") != "ANSWER-TABLE-6.3":
        fail("source anomaly ANSWER-TABLE-6.3 missing")

    p8 = (lock_dir / "demo" / "page-08.txt").read_text(encoding="utf-8")
    if p8.count("ИЛИ") != 3:
        fail("page 8 must contain exactly three ILI separators: 1 between task-1 variants and 2 between task-2 variants")
    if "1 Найдите значение выражения" not in p8 or "2 Баночка йогурта" not in p8:
        fail("task 1/task 2 anchors missing on page 8")

    p12 = (lock_dir / "demo" / "page-12.txt").read_text(encoding="utf-8")
    if "Площадь земель фермерского хозяйства" not in p12:
        fail("task 6.3 source anchor missing")

    p25_json = load_json(lock_dir / "demo" / "page-25.json")
    words = p25_json["words"]
    misplaced_nine = [w for w in words if w["text"] == "9" and abs(w["y0"] - 141.251) < 0.2 and 275 < w["x0"] < 295]
    if not misplaced_nine:
        fail("expected page-25 misplaced 9 evidence not found")

    if visual.get("source_sha256") != EXPECTED_HASHES["ege-2022-matematika-baza-demoversiya.pdf"]:
        fail("visual inventory source SHA mismatch")
    if visual.get("counts", {}).get("reference_full_page_renders") != 4:
        fail("visual reference-page count mismatch")
    for item in visual.get("items", []):
        if item["variant"] not in variants:
            fail(f"visual item references unknown variant {item['variant']}")
        if item["printed_page"] != variants[item["variant"]]:
            fail(f"visual item page mismatch: {item['id']}")

    if args.analysis_dir:
        generated = load_json(args.analysis_dir / "SOURCE-LOCK.json")
        for label, filename in (
            ("demo", "ege-2022-matematika-baza-demoversiya.pdf"),
            ("spec", "ege-2022-matematika-baza-specifikatsiya.pdf"),
            ("cod", "ege-2022-matematika-kodifikator.pdf"),
        ):
            if generated[label]["sha256"] != EXPECTED_HASHES[filename]:
                fail(f"generated analysis SHA mismatch for {label}")
        if generated["demo"]["physical_pdf_pages"] != 13 or generated["demo"]["generated_printed_pages"] != 25:
            fail("generated demo page map mismatch")
        if generated["spec"]["physical_pdf_pages"] != 4 or generated["spec"]["generated_printed_pages"] != 8:
            fail("generated spec page map mismatch")
        if generated["cod"]["physical_pdf_pages"] != 22 or generated["cod"]["generated_printed_pages"] != 44:
            fail("generated codifier page map mismatch")

    print("BASE 2022 SOURCE LOCK PASS")
    print("sources: 3/3 SHA locked")
    print("exam: 21 tasks / 52 official examples / 180 min / max 21")
    print("reference pages: 4/4 locked")
    print("answers: 52/52 variants locked")
    print("source anomaly: ANSWER-TABLE-6.3 locked; phantom 1.3 forbidden")
    print(f"visual source elements: {visual['counts']['total_locked_source_elements']} inventoried")


if __name__ == "__main__":
    main()
