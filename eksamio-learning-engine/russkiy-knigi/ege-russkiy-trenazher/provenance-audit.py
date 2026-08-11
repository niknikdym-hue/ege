#!/usr/bin/env python3
"""Independent round-trip audit of every generated trainer card."""

from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
PAGES = HERE.parent
PACKAGES = {
    2022: PAGES / "ege-russkiy-demoversiya-2022-v1.0.0",
    2023: PAGES / "ege-russkiy-demoversiya-2023-v1.0.0",
    2024: PAGES / "ege-russkiy-demoversiya-2024-v1.0.1",
    2025: PAGES / "ege-russkiy-demoversiya-2025-v1.0.2",
    2026: PAGES / "ege-russkiy-demoversiya-2026-v4.2",
}
TASK_MAP = {
    2022: {1: 3, 2: 1, 3: 2, 22: 23, 23: 24, 24: 25, 25: 26, 26: 22},
    2023: {22: 23, 23: 24, 24: 25, 25: 26, 26: 22},
    2024: {22: 23, 23: 24, 24: 25, 25: 26, 26: 22},
}
OFFICIAL_CORRECTIONS = {
    tuple(map(int, key.split("-"))): value
    for key, value in json.loads(
        (HERE / "OFFICIAL-CORRECTIONS.json").read_text(encoding="utf-8")
    ).items()
}
SOURCE_CORRECTIONS = json.loads(
    (HERE / "SOURCE-CORRECTIONS.json").read_text(encoding="utf-8")
)
ORTHOEPIC_BANK = json.loads(
    (HERE / "ORTHOEPIC-TRAINER-BANK.json").read_text(encoding="utf-8")
)
ORTHOEPIC_ENTRIES = {
    str(entry["id"]): entry for entry in ORTHOEPIC_BANK["entries"]
}


def payload(path: Path) -> dict:
    match = re.search(
        r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
        path.read_text(encoding="utf-8"),
        re.S,
    )
    if not match:
        raise AssertionError(f"JSON payload missing: {path}")
    return json.loads(match.group(1))


def compact(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def package(year: int) -> tuple[dict[int, dict], dict]:
    tasks: dict[int, dict] = {}
    sources: dict = {}
    for part in (2, 3, 4):
        data = payload(PACKAGES[year] / f"ege-russkiy-demoversiya-T123-0{part}.txt")
        sources.update(data.get("sources", {}))
        for task in data.get("tasks", []):
            tasks[int(task["number"])] = task
    assert len(tasks) == 27, f"{year}: expected 27 source tasks, got {len(tasks)}"
    return tasks, sources


def source_html(value: object) -> str:
    return str(value.get("html", "")) if isinstance(value, dict) else str(value or "")


def stress_markup(value: str) -> str:
    positions = [index for index, char in enumerate(value) if char in "АЕЁИОУЫЭЮЯ"]
    if len(positions) != 1:
        raise AssertionError(f"Expected one stress vowel in {value!r}")
    index = positions[0]
    return (
        html.escape(value[:index])
        + f"<strong>{html.escape(value[index])}</strong>"
        + html.escape(value[index + 1 :])
    )


def main() -> None:
    cards: list[dict] = []
    generated_sources: dict = {}
    for path in sorted(HERE.glob("ege-russkiy-trenazher-T123-0[2-9].txt")):
        data = payload(path)
        cards.extend(data.get("cards", []))
        generated_sources.update(data.get("sources", {}))

    source_packages = {year: package(year) for year in PACKAGES}
    failures: list[str] = []
    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(message)

    for card in cards:
        cid = card.get("id", "unknown")
        year = int(card["sourceYear"])
        original = int(card["originalNumber"])
        variant_number = int(card["variant"])
        if card.get("bankSource") == "orthoepic-list-2026":
            entry_ids = [str(value) for value in card.get("bankEntryIds", [])]
            answer = str(card.get("answer", ""))
            check(card["task"] == 4, f"{cid}: supplemental task must be 4")
            check(year == 2026 and original == 4, f"{cid}: bad supplemental provenance")
            check(101 <= variant_number < 101 + int(ORTHOEPIC_BANK["cardCount"]), f"{cid}: bad supplemental variant")
            check(len(entry_ids) == 5 and len(set(entry_ids)) == 5, f"{cid}: supplemental card needs five unique entries")
            check(all(value in ORTHOEPIC_ENTRIES for value in entry_ids), f"{cid}: unknown orthoepic entry")
            if len(entry_ids) != 5 or not all(value in ORTHOEPIC_ENTRIES for value in entry_ids):
                continue
            items: list[str] = []
            norms: list[str] = []
            for position, entry_id in enumerate(entry_ids, 1):
                entry = ORTHOEPIC_ENTRIES[entry_id]
                shown = entry["correct"] if str(position) in answer else entry["wrong"]
                context = str(entry.get("context", "")).strip()
                suffix = f" {html.escape(context)}" if context else ""
                items.append(f"<li>{stress_markup(str(shown))}{suffix}</li>")
                norms.append(str(entry["correct"]) + (f" {context}" if context else ""))
            expected_prompt = (
                "<p>Укажите варианты ответов, в которых верно выделена буква, "
                "обозначающая ударный гласный звук. Запишите номера ответов.</p><ol>"
                + "".join(items)
                + "</ol>"
            )
            expected_explanation = "Нормативно: " + ", ".join(norms) + f". Поэтому верны варианты {', '.join(answer)}."
            check(card["promptHtml"] == expected_prompt, f"{cid}: supplemental prompt changed")
            check(card["explanation"] == expected_explanation, f"{cid}: supplemental explanation changed")
            check(card["kind"] == "unordered_digits", f"{cid}: wrong supplemental field")
            check(card["options"] == ["1", "2", "3", "4", "5"], f"{cid}: wrong supplemental options")
            check(len(answer) in {2, 3} and len(set(answer)) == len(answer), f"{cid}: bad supplemental key")
            check(card["maxScore"] == 1 and not card["legacyFormat"], f"{cid}: bad supplemental scoring")
            continue
        tasks, sources = source_packages[year]
        base = tasks[original]
        variants = base.get("variants") or [base]
        check(1 <= variant_number <= len(variants), f"{cid}: invalid source variant")
        if not 1 <= variant_number <= len(variants):
            continue
        merged = {key: value for key, value in base.items() if key != "variants"}
        merged.update(variants[variant_number - 1])
        mapped = TASK_MAP.get(year, {}).get(original, original)
        sid = merged.get("sourceId", base.get("sourceId"))
        original_source = source_html(sources.get(sid)) if sid else ""
        source_correction = SOURCE_CORRECTIONS.get(f"{year}:{sid}", {})
        for old, new in source_correction.get("replacements", []):
            original_source = original_source.replace(old, new)
        expected_key = (
            f"src-{hashlib.sha1(original_source.encode('utf-8')).hexdigest()[:12]}"
            if original_source
            else None
        )
        expected_max = 22 if mapped == 27 else 2 if mapped in {8, 22} else 1
        correction = OFFICIAL_CORRECTIONS.get((year, original, variant_number), {})
        expected_alts = [str(x) for x in merged.get("altAnswers", [])]
        for extra_answer in correction.get("addAltAnswers", []):
            if extra_answer not in expected_alts and extra_answer != str(merged.get("answer", "")):
                expected_alts.append(extra_answer)
        expected_explanation = compact(
            correction.get("explanation", merged.get("explanation", ""))
        )

        check(card["task"] == mapped, f"{cid}: task mapping {card['task']} != {mapped}")
        expected_prompt = str(
            correction.get("promptHtml", merged.get("promptHtml", ""))
        ).strip()
        for old, new in correction.get("promptReplacements", []):
            expected_prompt = expected_prompt.replace(old, new)
        check(card["promptHtml"] == expected_prompt, f"{cid}: promptHtml changed")
        check(card["answer"] == str(correction.get("answer", merged.get("answer", ""))), f"{cid}: answer changed")
        check(card["kind"] == str(merged.get("kind", base.get("kind", "word"))), f"{cid}: kind changed")
        check(card["altAnswers"] == expected_alts, f"{cid}: altAnswers changed")
        check(card["explanation"] == expected_explanation, f"{cid}: explanation changed")
        check(card["maxScore"] == expected_max, f"{cid}: current maxScore is wrong")
        expected_legacy = (
            mapped in {13, 14} and year < 2024
        ) or (
            mapped == 22 and year < 2025
        ) or (
            mapped == 4 and year < 2025
        )
        check(card["legacyFormat"] == expected_legacy, f"{cid}: legacy-format flag is wrong")
        check(card.get("sourceKey") == expected_key, f"{cid}: source key changed")
        if expected_key:
            check(generated_sources.get(expected_key) == original_source, f"{cid}: source HTML changed")

    counts = Counter(card["task"] for card in cards)
    for task in range(1, 28):
        group = sorted((c for c in cards if c["task"] == task), key=lambda c: c["bankIndex"])
        check([c["bankIndex"] for c in group] == list(range(1, len(group) + 1)), f"task {task}: broken bankIndex")
        check(all(c["bankTotal"] == len(group) for c in group), f"task {task}: broken bankTotal")
        check(counts[task] >= 2, f"task {task}: fewer than two examples")

    if failures:
        raise SystemExit("\n".join(failures) + f"\nFAIL {len(failures)}/{checks}")
    print(
        f"PASS provenance: {checks} checks, {len(cards)} cards, "
        f"{len(generated_sources)} exact source texts"
    )


if __name__ == "__main__":
    main()
