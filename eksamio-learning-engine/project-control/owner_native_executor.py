from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MAX_FILE_BYTES = 2_000_000
MAX_UPDATES = 12
PROTECTED_EXACT = {
    ".github/workflows/owner-agent-task-v2.yml",
    ".github/workflows/owner-agent-batch-v2.yml",
    ".github/workflows/owner-agent-native-v3.yml",
    ".github/workflows/owner-control-v2-static.yml",
    "eksamio-learning-engine/project-control/operational-board-v1.json",
    "eksamio-learning-engine/project-control/owner_control_budget_proxy.mjs",
}
PROTECTED_PARTS = {".git", ".env", "secret", "secrets"}
ALLOWED_PLAYBOOKS = {"exact_text_replace", "json_set"}


class NativeExecutionError(RuntimeError):
    pass


def _safe_path(repo_root: Path, raw: str) -> Path:
    rel = Path(str(raw))
    if rel.is_absolute() or ".." in rel.parts:
        raise NativeExecutionError("native path must be repository-relative")
    normalized = rel.as_posix()
    if normalized in PROTECTED_EXACT:
        raise NativeExecutionError(f"protected control path: {normalized}")
    lowered = {part.lower() for part in rel.parts}
    if lowered & PROTECTED_PARTS or any("secret" in part.lower() for part in rel.parts):
        raise NativeExecutionError(f"protected secret/control path: {normalized}")
    path = (repo_root / rel).resolve()
    root = repo_root.resolve()
    if path != root and root not in path.parents:
        raise NativeExecutionError("native path escaped repository root")
    if not path.is_file():
        raise NativeExecutionError(f"native target file missing: {normalized}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise NativeExecutionError(f"native target too large: {normalized}")
    return path


def _json_pointer_get_parent(doc: Any, pointer: str) -> tuple[Any, str]:
    if not pointer.startswith("/") or pointer == "/":
        raise NativeExecutionError("json_set pointer must target an existing nested key")
    parts = [p.replace("~1", "/").replace("~0", "~") for p in pointer[1:].split("/")]
    cur = doc
    for part in parts[:-1]:
        if isinstance(cur, dict):
            if part not in cur:
                raise NativeExecutionError(f"json_set missing key in pointer: {pointer}")
            cur = cur[part]
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except Exception as exc:
                raise NativeExecutionError(f"json_set invalid list index: {pointer}") from exc
        else:
            raise NativeExecutionError(f"json_set pointer crosses scalar: {pointer}")
    return cur, parts[-1]


def _exact_text_replace(path: Path, args: dict[str, Any]) -> None:
    old = args.get("old")
    new = args.get("new")
    expected = int(args.get("count", 1))
    if not isinstance(old, str) or not isinstance(new, str) or not old:
        raise NativeExecutionError("exact_text_replace requires non-empty old and string new")
    if expected < 1 or expected > MAX_UPDATES:
        raise NativeExecutionError("exact_text_replace count out of bounds")
    text = path.read_text(encoding="utf-8")
    actual = text.count(old)
    if actual != expected:
        raise NativeExecutionError(f"exact_text_replace expected {expected} matches, found {actual}")
    path.write_text(text.replace(old, new, expected), encoding="utf-8")


def _json_set(path: Path, args: dict[str, Any]) -> None:
    updates = args.get("updates")
    if not isinstance(updates, list) or not 1 <= len(updates) <= MAX_UPDATES:
        raise NativeExecutionError("json_set requires 1..12 updates")
    doc = json.loads(path.read_text(encoding="utf-8"))
    for update in updates:
        if not isinstance(update, dict) or "pointer" not in update or "value" not in update:
            raise NativeExecutionError("json_set update requires pointer and value")
        parent, key = _json_pointer_get_parent(doc, str(update["pointer"]))
        if isinstance(parent, dict):
            if key not in parent:
                raise NativeExecutionError(f"json_set refuses to create key: {key}")
            parent[key] = update["value"]
        elif isinstance(parent, list):
            try:
                idx = int(key)
                if idx < 0 or idx >= len(parent):
                    raise IndexError(idx)
            except Exception as exc:
                raise NativeExecutionError(f"json_set invalid final list index: {key}") from exc
            parent[idx] = update["value"]
        else:
            raise NativeExecutionError("json_set final parent is scalar")
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def execute(repo_root: Path, board_path: Path, task_id: str) -> dict[str, Any]:
    board = json.loads(board_path.read_text(encoding="utf-8"))
    tasks = board.get("tasks")
    if board.get("version") != "operational-board-v1" or not isinstance(tasks, list) or len(tasks) != 115:
        raise NativeExecutionError("operational board authority invariant failed")
    rows = {str(task.get("task_id")): task for task in tasks}
    task = rows.get(task_id)
    if task is None:
        raise NativeExecutionError(f"unknown task_id: {task_id}")
    if str(task.get("execution_mode") or "").lower() != "github_native":
        raise NativeExecutionError("task is not explicitly github_native")
    if task.get("astra_required") or task.get("astra_plan_required") or task.get("astra_acceptance_required"):
        raise NativeExecutionError("github_native task cannot request Astra")
    playbook = str(task.get("native_playbook") or "")
    if playbook not in ALLOWED_PLAYBOOKS:
        raise NativeExecutionError(f"unregistered native playbook: {playbook}")
    args = task.get("native_args")
    if not isinstance(args, dict):
        raise NativeExecutionError("native_args must be an object")
    path = _safe_path(repo_root, str(args.get("path") or ""))
    before = path.read_bytes()
    if playbook == "exact_text_replace":
        _exact_text_replace(path, args)
    elif playbook == "json_set":
        _json_set(path, args)
    after = path.read_bytes()
    if before == after:
        raise NativeExecutionError("native playbook produced no change")
    result = {
        "task_id": task_id,
        "execution_mode": "github_native",
        "native_playbook": playbook,
        "changed_paths": [path.relative_to(repo_root.resolve()).as_posix()],
        "paid_provider_calls": 0,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--board", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--result", default="/tmp/owner-native-result.json")
    ns = parser.parse_args()
    result = execute(Path(ns.repo_root), Path(ns.board), ns.task_id)
    Path(ns.result).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
