#!/usr/bin/env python3
"""Independently validate Russian Skill Graph against repository-visible trainer.

Designed to close the old TASK-001 source-snapshot blocker without relying on
Codex assertions. Data-only; no production mutation.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

GRAPH_REL = Path("03-RUSSIAN-SKILL-GRAPH.json")
TRAINER_DIR_REL = Path("russkiy-knigi/ege-russkiy-trenazher")
PREVIEW_REL = TRAINER_DIR_REL / "ege-russkiy-trenazher-PREVIEW.html"
MANIFEST_REL = TRAINER_DIR_REL / "BANK-MANIFEST.json"
REPORT_REL = Path("audits/RUSSIAN-SKILL-GRAPH-INDEPENDENT-VALIDATION.txt")

ITEM_ID_RE = re.compile(r"^ege-ru-(\d{2})-(\d{4})-(\d{2})-(\d{2,3})$")
SCRIPT_RE = re.compile(
    r'<script\b[^>]*class=["\'][^"\']*\ber-bank-chunk\b[^"\']*["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)

SPECIAL_TASK25_ID = "ege-ru-25-2022-24-01"


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise ValidationError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def walk(obj: Any) -> Iterable[Any]:
    yield obj
    if isinstance(obj, dict):
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def parse_trainer_cards(preview_path: Path) -> list[dict[str, Any]]:
    try:
        text = preview_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValidationError(f"Missing trainer preview: {preview_path}") from exc

    chunks = SCRIPT_RE.findall(text)
    if not chunks:
        raise ValidationError("No er-bank-chunk JSON scripts found in trainer preview")

    cards: list[dict[str, Any]] = []
    for index, raw in enumerate(chunks, start=1):
        payload_text = html.unescape(raw).strip()
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ValidationError(
                f"Invalid trainer chunk #{index}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
            ) from exc
        chunk_cards = payload.get("cards") if isinstance(payload, dict) else None
        if not isinstance(chunk_cards, list):
            raise ValidationError(f"Trainer chunk #{index} has no cards[]")
        for card in chunk_cards:
            if not isinstance(card, dict):
                raise ValidationError(f"Trainer chunk #{index} contains non-object card")
            cards.append(card)
    return cards


def collect_graph_item_ids(graph: Any) -> set[str]:
    result: set[str] = set()
    for node in walk(graph):
        if isinstance(node, str) and ITEM_ID_RE.match(node):
            result.add(node)
    return result


def collect_skill_stats(graph: Any) -> dict[str, int]:
    skill_ids: set[str] = set()
    duplicate_skill_ids: set[str] = set()
    top = 0
    child = 0
    nonnull_difficulty = 0
    nonempty_prerequisites = 0

    for node in walk(graph):
        if not isinstance(node, dict):
            continue
        skill_id = node.get("skill_id")
        if isinstance(skill_id, str) and skill_id:
            if skill_id in skill_ids:
                duplicate_skill_ids.add(skill_id)
            else:
                skill_ids.add(skill_id)
            if node.get("parent_skill_id") is None:
                top += 1
            else:
                child += 1
        if "difficulty" in node and node.get("difficulty") is not None:
            nonnull_difficulty += 1
        prerequisites = node.get("prerequisites")
        if isinstance(prerequisites, list) and prerequisites:
            nonempty_prerequisites += 1

    return {
        "skills_unique": len(skill_ids),
        "skill_id_duplicates": len(duplicate_skill_ids),
        "top_level_skills": top,
        "child_skills": child,
        "nonnull_difficulty": nonnull_difficulty,
        "nonempty_prerequisites": nonempty_prerequisites,
    }


def expected_cards_per_task(manifest: Any) -> dict[int, int]:
    raw = manifest.get("cardsPerTask") if isinstance(manifest, dict) else None
    if not isinstance(raw, dict):
        raise ValidationError("BANK-MANIFEST.json missing cardsPerTask object")
    result: dict[int, int] = {}
    for key, value in raw.items():
        try:
            task = int(key)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"Invalid cardsPerTask key: {key!r}") from exc
        if not isinstance(value, int):
            raise ValidationError(f"Invalid cardsPerTask value for {task}: {value!r}")
        result[task] = value
    return result


def validate(root: Path) -> tuple[list[str], list[str], dict[str, Any]]:
    graph = load_json(root / GRAPH_REL)
    manifest = load_json(root / MANIFEST_REL)
    cards = parse_trainer_cards(root / PREVIEW_REL)

    errors: list[str] = []
    warnings: list[str] = []

    trainer_ids: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    actual_by_task: Counter[int] = Counter()

    for card in cards:
        card_id = card.get("id")
        task = card.get("task")
        if not isinstance(card_id, str) or not ITEM_ID_RE.match(card_id):
            errors.append(f"invalid trainer card id: {card_id!r}")
            continue
        if card_id in by_id:
            errors.append(f"duplicate trainer card id: {card_id}")
        by_id[card_id] = card
        trainer_ids.append(card_id)
        if isinstance(task, int):
            actual_by_task[task] += 1
        else:
            errors.append(f"{card_id}: invalid task {task!r}")

    manifest_cards = manifest.get("cards") if isinstance(manifest, dict) else None
    if isinstance(manifest_cards, int) and manifest_cards != len(cards):
        errors.append(
            f"trainer card total mismatch: manifest={manifest_cards}, preview={len(cards)}"
        )

    expected_by_task = expected_cards_per_task(manifest)
    for task in range(1, 28):
        expected = expected_by_task.get(task)
        actual = actual_by_task.get(task, 0)
        if expected is None:
            errors.append(f"manifest cardsPerTask missing task {task}")
        elif expected != actual:
            errors.append(
                f"task {task} card count mismatch: manifest={expected}, preview={actual}"
            )

    graph_item_ids = collect_graph_item_ids(graph)
    trainer_set = set(trainer_ids)
    missing_from_graph = sorted(trainer_set - graph_item_ids)
    if missing_from_graph:
        errors.append(
            f"trainer IDs missing from Skill Graph: {len(missing_from_graph)}"
        )
    graph_only = sorted(graph_item_ids - trainer_set)
    if graph_only:
        warnings.append(
            f"Skill Graph contains {len(graph_only)} trainer-like IDs not present in current snapshot"
        )

    stats = collect_skill_stats(graph)
    if stats["skill_id_duplicates"]:
        errors.append(f"duplicate skill_id count: {stats['skill_id_duplicates']}")
    if stats["nonnull_difficulty"]:
        errors.append(
            f"difficulty must stay null unless validated; non-null count={stats['nonnull_difficulty']}"
        )
    if stats["nonempty_prerequisites"]:
        errors.append(
            f"unexpected non-empty prerequisites count={stats['nonempty_prerequisites']}"
        )

    # Expected current architecture claim; if it changes intentionally, update this validator with review.
    if stats["top_level_skills"] != 12:
        warnings.append(
            f"top-level skill count changed from reviewed 12 to {stats['top_level_skills']}"
        )
    if stats["child_skills"] != 89:
        warnings.append(
            f"child skill count changed from reviewed 89 to {stats['child_skills']}"
        )

    special_card = by_id.get(SPECIAL_TASK25_ID)
    if special_card is None:
        warnings.append(f"special historical task25 item not found: {SPECIAL_TASK25_ID}")
    else:
        if special_card.get("legacyFormat") is not False:
            warnings.append(
                f"{SPECIAL_TASK25_ID}: expected known source anomaly legacyFormat=false changed to {special_card.get('legacyFormat')!r}"
            )
        prompt = str(special_card.get("promptHtml") or "").lower()
        if "синоним" not in prompt:
            warnings.append(
                f"{SPECIAL_TASK25_ID}: historical contextual-synonym prompt signature not found"
            )

        graph_text = json.dumps(graph, ensure_ascii=False)
        pos = graph_text.find(SPECIAL_TASK25_ID)
        if pos < 0:
            errors.append(f"{SPECIAL_TASK25_ID}: not referenced in Skill Graph")
        else:
            window = graph_text[max(0, pos - 2500): pos + 2500].lower()
            if "needs_review" not in window and "legacy" not in window:
                warnings.append(
                    f"{SPECIAL_TASK25_ID}: nearby graph mapping does not visibly contain needs_review/legacy marker"
                )

    result_stats: dict[str, Any] = {
        "trainer_cards": len(cards),
        "trainer_ids_unique": len(trainer_set),
        "graph_trainer_ids": len(graph_item_ids),
        "trainer_ids_missing_from_graph": len(missing_from_graph),
        "graph_only_trainer_ids": len(graph_only),
        **stats,
        "task_counts": {str(task): actual_by_task.get(task, 0) for task in range(1, 28)},
    }
    return errors, warnings, result_stats


def write_report(path: Path, errors: list[str], warnings: list[str], stats: dict[str, Any]) -> None:
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN SKILL GRAPH — INDEPENDENT TRAINER SNAPSHOT VALIDATION",
        "",
        f"STATUS: {'PASS' if not errors else 'FAIL'}",
        f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
        "",
        "STATS",
    ]
    for key, value in stats.items():
        if key == "task_counts":
            continue
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("TASK COUNTS")
    for task, count in stats.get("task_counts", {}).items():
        lines.append(f"- {task}: {count}")
    lines.extend(["", "ERRORS"])
    lines.extend(["- none"] if not errors else [f"- {x}" for x in errors])
    lines.extend(["", "WARNINGS"])
    lines.extend(["- none"] if not warnings else [f"- {x}" for x in warnings])
    lines.extend(
        [
            "",
            "INTERPRETATION",
            "- PASS closes the repository-visible trainer snapshot coverage check, not every future runtime/integration check.",
            "- Warnings about metadata/anomalies require review but do not automatically invalidate structural coverage.",
            "- Current trainer is not modified by this validator.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=root_default)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    report = args.report or root / REPORT_REL
    try:
        errors, warnings, stats = validate(root)
    except ValidationError as exc:
        print(f"VALIDATION ERROR: {exc}", file=sys.stderr)
        return 2

    write_report(report, errors, warnings, stats)
    if errors:
        print(f"FAIL: {len(errors)} Skill Graph validation error(s); report={report}")
        return 1
    print(
        f"PASS: trainer_cards={stats['trainer_cards']}, graph_trainer_ids={stats['graph_trainer_ids']}, "
        f"warnings={len(warnings)}"
    )
    print(f"Report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
