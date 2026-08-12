#!/usr/bin/env python3
"""Build a minimal learner-safe runtime payload for the future Exceptions Trainer.

Consumes only machine-built canonical exception/practice data plus derived launch
priority. Excludes raw books, provenance and audit notes. No production write.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOPIC_MAP = {
    "orthographic_norms": ("orthography", "Орфография", 10),
    "punctuation_norms": ("punctuation", "Пунктуация", 20),
    "morphological_norms": ("morphology", "Морфология", 30),
    "syntactic_norms": ("syntax", "Синтаксис", 40),
    "lexical_norms_and_semantics": ("lexical_norms", "Лексические нормы", 50),
    "orthoepic_norms": ("orthoepy", "Орфоэпия", 60),
}


class BuildError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise BuildError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(f"Invalid JSON in {path}: {exc}") from exc


def topic_for(exception: dict[str, Any]) -> tuple[str, str, int]:
    skills = exception.get("skill_ids")
    if not isinstance(skills, list) or not skills or not isinstance(skills[0], str):
        raise BuildError(f"{exception.get('exception_id')}: missing primary skill_id")
    skill = skills[0]
    if skill not in TOPIC_MAP:
        raise BuildError(
            f"{exception.get('exception_id')}: no learner topic mapping for primary skill {skill!r}"
        )
    return TOPIC_MAP[skill]


def compact_feedback(feedback: Any) -> dict[str, Any]:
    if not isinstance(feedback, dict):
        raise BuildError("Practice feedback must be object")
    allowed = ("correct_answer", "why", "rule_ref", "explanation_id", "exception_contrast_ids", "next_action")
    return {key: feedback[key] for key in allowed if key in feedback}


def stable_content_version(
    topics: list[dict[str, Any]],
    exceptions: dict[str, dict[str, Any]],
    practice_items: dict[str, dict[str, Any]],
) -> str:
    """Content-address the learner runtime; timestamps must not create fake versions."""
    raw = json.dumps(
        {"topics": topics, "exceptions": exceptions, "practice_items": practice_items},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256-" + hashlib.sha256(raw).hexdigest()[:20]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--exceptions", type=Path, default=root / "build" / "RUSSIAN-EXCEPTIONS-BANK-CANONICAL.json")
    parser.add_argument("--practice", type=Path, default=root / "build" / "RUSSIAN-EXCEPTIONS-PRACTICE-CANONICAL.json")
    parser.add_argument("--priority", type=Path, default=root / "build" / "RUSSIAN-EXCEPTIONS-LAUNCH-PRIORITY.json")
    parser.add_argument("--output", type=Path, default=root / "build" / "RUSSIAN-EXCEPTIONS-RUNTIME.json")
    args = parser.parse_args()

    try:
        exception_data = load_json(args.exceptions)
        practice_data = load_json(args.practice)
        priority_data = load_json(args.priority)
        exception_items = exception_data.get("items") if isinstance(exception_data, dict) else None
        practice_items = practice_data.get("items") if isinstance(practice_data, dict) else None
        priority_items = priority_data.get("items") if isinstance(priority_data, dict) else None
        if not isinstance(exception_items, list): raise BuildError("Canonical Exceptions Bank missing items[]")
        if not isinstance(practice_items, list): raise BuildError("Canonical Practice Bank missing items[]")
        if not isinstance(priority_items, list): raise BuildError("Priority build missing items[]")

        priorities = {row.get("exception_id"): row for row in priority_items if isinstance(row, dict) and isinstance(row.get("exception_id"), str)}
        practices_by_exception: dict[str, list[str]] = {}
        runtime_practice: dict[str, dict[str, Any]] = {}
        seen_practice: set[str] = set()
        for row in practice_items:
            if not isinstance(row, dict): raise BuildError("Non-object practice item")
            pid = row.get("practice_item_id"); exception_id = row.get("exception_id")
            if not isinstance(pid, str) or not pid: raise BuildError("Practice item missing practice_item_id")
            if pid in seen_practice: raise BuildError(f"Duplicate practice_item_id: {pid}")
            seen_practice.add(pid)
            if not isinstance(exception_id, str) or not exception_id: raise BuildError(f"{pid}: missing exception_id")
            if row.get("status") not in {"source_verified", "reviewed"}: continue
            compact = {
                "practice_item_id": pid, "exception_id": exception_id, "mode": row.get("mode"),
                "response_kind": row.get("response_kind"), "prompt": row.get("prompt"), "answer": row.get("answer"),
                "feedback": compact_feedback(row.get("feedback")), "context_signature": row.get("context_signature"),
                "transfer_level": row.get("transfer_level"), "status": "enabled",
            }
            if "alt_answers" in row: compact["alt_answers"] = row["alt_answers"]
            if "distractors" in row: compact["distractors"] = row["distractors"]
            runtime_practice[pid] = compact
            practices_by_exception.setdefault(exception_id, []).append(pid)

        runtime_exceptions: dict[str, dict[str, Any]] = {}
        topics: dict[str, dict[str, Any]] = {}
        seen_exception: set[str] = set()
        for row in exception_items:
            if not isinstance(row, dict): raise BuildError("Non-object exception item")
            exception_id = row.get("exception_id")
            if not isinstance(exception_id, str) or not exception_id: raise BuildError("Exception missing exception_id")
            if exception_id in seen_exception: raise BuildError(f"Duplicate exception_id: {exception_id}")
            seen_exception.add(exception_id)
            if row.get("status") not in {"source_verified", "reviewed"}: continue
            practice_ids = sorted(practices_by_exception.get(exception_id, []))
            if not practice_ids: continue
            topic_id, label, order = topic_for(row)
            topics.setdefault(topic_id, {"topic_id":topic_id,"label":label,"order":order})
            priority = priorities.get(exception_id)
            if priority is None: raise BuildError(f"{exception_id}: missing launch priority row")
            runtime_exceptions[exception_id] = {
                "exception_id": exception_id,
                "label": row.get("prompt_label") or row.get("canonical_form") or exception_id,
                "topic_id": topic_id,
                "practice_item_ids": practice_ids,
                "rule_ref": row.get("rule_ref"),
                "launch_priority": priority.get("launch_priority"),
                "status": "enabled",
            }

        orphan_practice = sorted(pid for pid, row in runtime_practice.items() if row["exception_id"] not in runtime_exceptions)
        if orphan_practice: raise BuildError(f"Enabled practice items without runtime exception: {orphan_practice[:10]}")

        runtime_topics = sorted(topics.values(), key=lambda row:(row["order"], row["topic_id"]))
        version = stable_content_version(runtime_topics, runtime_exceptions, runtime_practice)
        payload = {
            "schema_version":"1.0.0",
            "product_id":"russian_exceptions",
            "content_version":version,
            "generated_at":datetime.now(timezone.utc).isoformat(),
            "topics":runtime_topics,
            "exceptions":runtime_exceptions,
            "practice_items":runtime_practice,
            "build_meta":{
                "exceptions_enabled":len(runtime_exceptions),
                "practice_items_enabled":len(runtime_practice),
                "source_exception_items":len(exception_items),
                "source_practice_items":len(practice_items),
                "priority_rows":len(priority_items),
                "production_integration":"not_connected"
            }
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(f"PASS: runtime exceptions={len(runtime_exceptions)}, practice={len(runtime_practice)}, topics={len(topics)}, version={version}")
        print(f"Output: {args.output}")
        return 0
    except BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
