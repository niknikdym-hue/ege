#!/usr/bin/env python3
"""Owner-gated live smoke controller for Eksamio development agents.

This module prepares the first bounded live loop:
Astra plan -> Codex SDK execution -> deterministic checks -> Astra review.

It is intentionally fail-closed. A live provider cannot be reached unless the
caller supplies the explicit owner flag *and* credentials. Dangerous product or
production actions remain forbidden even when live-provider use is authorized.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from codex_sdk_executor import CodexSdkExecutorAdapter
from eksamio_agent_runner import (
    AstraResponsesAdapter,
    ContractError,
    PermissionDenied,
    PermissionGate,
    ProviderError,
    canonical_json,
    sha256_json,
    validate_review_decision,
    validate_task_plan,
)

CONTEXT_SCHEMA_VERSION = "0.1"
MAX_REVIEW_DIFF_BYTES = 120_000


class LiveSmokeError(RuntimeError):
    pass


def _require_exact_keys(value: dict[str, Any], required: set[str]) -> None:
    missing = required - set(value)
    unknown = set(value) - required
    if missing:
        raise LiveSmokeError(f"repository context missing fields: {sorted(missing)}")
    if unknown:
        raise LiveSmokeError(f"repository context unknown fields: {sorted(unknown)}")


def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(c in "0123456789abcdef" for c in value)


def _string_list(value: Any, field: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise LiveSmokeError(f"{field} must be a list of non-empty strings")
    if nonempty and not value:
        raise LiveSmokeError(f"{field} must not be empty")
    return list(value)


def validate_repository_context(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LiveSmokeError("repository context must be an object")
    required = {
        "schema_version",
        "repository",
        "base_sha",
        "target_branch",
        "task_brief",
        "evidence",
        "max_allowed_scope",
        "allowed_acceptance_checks",
    }
    _require_exact_keys(value, required)
    if value["schema_version"] != CONTEXT_SCHEMA_VERSION:
        raise LiveSmokeError("unsupported repository context schema_version")
    if value["repository"] != "niknikdym-hue/ege":
        raise LiveSmokeError("repository must be niknikdym-hue/ege")
    if not _valid_sha(value["base_sha"]):
        raise LiveSmokeError("base_sha must be a lowercase 40-character git SHA")
    for field in ("target_branch", "task_brief"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise LiveSmokeError(f"{field} must be non-empty")
    _string_list(value["evidence"], "evidence")
    _string_list(value["max_allowed_scope"], "max_allowed_scope", nonempty=True)
    _string_list(value["allowed_acceptance_checks"], "allowed_acceptance_checks", nonempty=True)
    return value


class GitWorkspace:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def git(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(self.root), *args],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        if completed.returncode != 0:
            raise LiveSmokeError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")
        return completed.stdout.strip()

    def assert_exact_context(self, context: dict[str, Any]) -> None:
        actual_root = Path(self.git("rev-parse", "--show-toplevel")).resolve()
        if actual_root != self.root:
            raise LiveSmokeError(f"repo root mismatch: configured {self.root}, git reports {actual_root}")
        if self.git("rev-parse", "HEAD") != context["base_sha"]:
            raise LiveSmokeError("checkout HEAD does not match repository context base_sha")
        branch = self.git("branch", "--show-current")
        if branch != context["target_branch"]:
            raise LiveSmokeError(
                f"checkout branch {branch or '<detached>'} does not match {context['target_branch']}"
            )
        if self.changed_paths():
            raise LiveSmokeError("live smoke requires a clean Git workspace before Codex execution")

    def changed_paths(self) -> list[str]:
        tracked = self.git("diff", "--name-only", "HEAD").splitlines()
        untracked = self.git("ls-files", "--others", "--exclude-standard").splitlines()
        return sorted({path for path in tracked + untracked if path})

    def diff_text(self) -> str:
        tracked = self.git("diff", "--no-ext-diff", "--binary", "HEAD")
        untracked_chunks: list[str] = []
        for path in self.git("ls-files", "--others", "--exclude-standard").splitlines():
            if not path:
                continue
            target = (self.root / path).resolve()
            try:
                target.relative_to(self.root)
            except ValueError as exc:
                raise LiveSmokeError(f"untracked path escaped repository: {path}") from exc
            if target.is_symlink():
                untracked_chunks.append(f"UNTRACKED SYMLINK {path} -> {os.readlink(target)}\n")
                continue
            if not target.is_file():
                untracked_chunks.append(f"UNTRACKED NON-FILE {path}\n")
                continue
            raw = target.read_bytes()
            if b"\x00" in raw:
                untracked_chunks.append(f"UNTRACKED BINARY {path} sha256={hashlib.sha256(raw).hexdigest()}\n")
            else:
                text = raw.decode("utf-8", errors="replace")
                untracked_chunks.append(f"--- /dev/null\n+++ {path}\n{text}\n")
        return tracked + "".join(untracked_chunks)


class AcceptanceRunner:
    def __init__(self, repo_root: Path, allowlist: list[str]):
        self.repo_root = repo_root.resolve()
        self.allowlist = frozenset(allowlist)

    def run_all(self, checks: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for check in checks:
            if check not in self.allowlist:
                raise LiveSmokeError(f"Astra requested an acceptance check outside owner allowlist: {check}")
            args = shlex.split(check)
            if not args:
                raise LiveSmokeError("acceptance check resolved to an empty command")
            started = time.monotonic()
            completed = subprocess.run(
                args,
                cwd=self.repo_root,
                text=True,
                capture_output=True,
                check=False,
                timeout=600,
            )
            result = {
                "command": check,
                "returncode": completed.returncode,
                "duration_ms": int((time.monotonic() - started) * 1000),
                "stdout_tail": completed.stdout[-4000:],
                "stderr_tail": completed.stderr[-4000:],
            }
            results.append(result)
            if completed.returncode != 0:
                raise LiveSmokeError(f"acceptance check failed: {check}")
        return results


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _ensure_task_matches_context(task: dict[str, Any], context: dict[str, Any]) -> None:
    validate_task_plan(task)
    for field in ("repository", "base_sha", "target_branch"):
        if task[field] != context[field]:
            raise LiveSmokeError(f"Astra task changed owner-controlled {field}")
    # Provider authorization does not grant product/production actions.
    PermissionGate().assert_allowed(task["requested_actions"])
    for check in task["acceptance_checks"]:
        if check not in context["allowed_acceptance_checks"]:
            raise LiveSmokeError(f"task acceptance check is outside owner allowlist: {check}")


def _assert_change_scope(paths: list[str], task: dict[str, Any], context: dict[str, Any]) -> None:
    for path in paths:
        if not _matches_any(path, task["allowed_scope"]):
            raise LiveSmokeError(f"Codex changed path outside Astra task scope: {path}")
        if not _matches_any(path, context["max_allowed_scope"]):
            raise LiveSmokeError(f"Codex changed path outside owner maximum scope: {path}")


class LiveSmokeHarness:
    def __init__(
        self,
        *,
        repo_root: Path,
        astra: Any | None = None,
        codex: Any | None = None,
    ):
        self.repo_root = repo_root.resolve()
        self.astra = astra or AstraResponsesAdapter()
        self.codex = codex or CodexSdkExecutorAdapter(repo_root=self.repo_root)
        self.workspace = GitWorkspace(self.repo_root)

    def run(self, context: dict[str, Any], *, owner_authorize_live_provider: bool) -> dict[str, Any]:
        context = validate_repository_context(context)

        grants = frozenset({"live_provider_call"}) if owner_authorize_live_provider else frozenset()
        # This happens before Astra.plan(), so a missing owner flag physically blocks network access.
        PermissionGate(grants).assert_allowed(["live_provider_call"])

        self.workspace.assert_exact_context(context)

        plan_result = self.astra.plan(
            {
                "repository_context": context,
                "controller_rules": {
                    "one_bounded_task_only": True,
                    "dangerous_actions_forbidden": True,
                    "max_allowed_scope": context["max_allowed_scope"],
                    "allowed_acceptance_checks": context["allowed_acceptance_checks"],
                },
            }
        )
        task = plan_result.get("output")
        if not isinstance(task, dict):
            raise LiveSmokeError("Astra plan did not return an object")
        _ensure_task_matches_context(task, context)

        codex_result = self.codex.execute(task, dry_run=False)

        # First live smoke is deliberately no-commit/no-push: exact HEAD must remain pinned.
        if self.workspace.git("rev-parse", "HEAD") != context["base_sha"]:
            raise LiveSmokeError("Codex moved Git HEAD; first live smoke forbids commit/push")

        changed_paths = self.workspace.changed_paths()
        _assert_change_scope(changed_paths, task, context)

        acceptance = AcceptanceRunner(self.repo_root, context["allowed_acceptance_checks"]).run_all(
            task["acceptance_checks"]
        )

        diff = self.workspace.diff_text()
        diff_bytes = diff.encode("utf-8")
        if len(diff_bytes) > MAX_REVIEW_DIFF_BYTES:
            raise LiveSmokeError(
                f"review diff is {len(diff_bytes)} bytes; exceeds fail-closed limit {MAX_REVIEW_DIFF_BYTES}"
            )

        diff_sha256 = hashlib.sha256(diff_bytes).hexdigest()
        review_context = {
            "repository": context["repository"],
            "reviewed_sha": context["base_sha"],
            "target_branch": context["target_branch"],
            "task": task,
            "codex_result": codex_result,
            "changed_paths": changed_paths,
            "diff_sha256": diff_sha256,
            "diff": diff,
            "acceptance": acceptance,
            "hard_rules": {
                "false_exact_mastery_zero": True,
                "server_owned_truth_required": True,
                "owner_gates_required": True,
                "no_merge_deploy_or_production_action": True,
            },
        }
        review_result = self.astra.review(review_context)
        decision = review_result.get("output")
        if not isinstance(decision, dict):
            raise LiveSmokeError("Astra review did not return an object")
        validate_review_decision(decision)
        if decision["reviewed_sha"] != context["base_sha"]:
            raise LiveSmokeError("Astra review changed reviewed_sha")

        return {
            "schema_version": "0.1",
            "status": "COMPLETED",
            "repository": context["repository"],
            "base_sha": context["base_sha"],
            "target_branch": context["target_branch"],
            "context_sha256": sha256_json(context),
            "task_sha256": sha256_json(task),
            "changed_paths": changed_paths,
            "diff_sha256": diff_sha256,
            "acceptance": acceptance,
            "astra_plan_metadata": plan_result.get("provider_metadata") or {},
            "codex": codex_result,
            "astra_review_metadata": review_result.get("provider_metadata") or {},
            "decision": decision,
            "created_at_unix": int(time.time()),
        }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LiveSmokeError(f"{path} must contain a JSON object")
    return value


def _write_artifact(path: Path, artifact: dict[str, Any], repo_root: Path) -> None:
    resolved = path.expanduser().resolve()
    root = repo_root.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        pass
    else:
        raise LiveSmokeError("live-smoke artifact must be written outside the mutable checkout")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Eksamio owner-gated live agent smoke")
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--context", required=True, type=Path)
    parser.add_argument("--artifact-out", required=True, type=Path)
    parser.add_argument("--owner-authorize-live-provider", action="store_true")
    args = parser.parse_args(argv)

    context = _load_json(args.context)
    artifact = LiveSmokeHarness(repo_root=args.repo_root).run(
        context,
        owner_authorize_live_provider=args.owner_authorize_live_provider,
    )
    _write_artifact(args.artifact_out, artifact, args.repo_root)
    print(json.dumps({"status": artifact["status"], "decision": artifact["decision"]["decision"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, PermissionDenied, ProviderError, LiveSmokeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
