#!/usr/bin/env python3
"""Official openai-codex SDK boundary for Eksamio.

The SDK import is intentionally delayed until a non-dry-run execution so normal
PR CI stays network-free and does not need Codex authentication or packages.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Iterable

from eksamio_agent_runner import (
    PermissionGate,
    ProviderError,
    canonical_json,
    sha256_json,
    validate_task_plan,
)


class CodexSdkExecutorAdapter:
    """Execute one validated task in an exact local Git checkout via openai-codex."""

    def __init__(
        self,
        *,
        repo_root: Path,
        api_key: str | None = None,
        model: str | None = None,
        owner_authorized_actions: Iterable[str] = (),
    ):
        self.repo_root = repo_root.resolve()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("EKSAMIO_CODEX_MODEL")
        self.permission_gate = PermissionGate(frozenset(owner_authorized_actions))

    def _git(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(self.repo_root), *args],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        if completed.returncode != 0:
            raise ProviderError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")
        return completed.stdout.strip()

    def assert_exact_checkout(self, task: dict[str, Any]) -> None:
        validate_task_plan(task)
        actual_root = Path(self._git("rev-parse", "--show-toplevel")).resolve()
        if actual_root != self.repo_root:
            raise ProviderError(f"repo_root mismatch: expected {self.repo_root}, git reports {actual_root}")
        actual_sha = self._git("rev-parse", "HEAD")
        if actual_sha != task["base_sha"]:
            raise ProviderError(f"branch moved: task base {task['base_sha']} != checkout HEAD {actual_sha}")
        actual_branch = self._git("branch", "--show-current")
        if actual_branch != task["target_branch"]:
            raise ProviderError(
                f"target branch mismatch: task {task['target_branch']} != checkout {actual_branch or '<detached>'}"
            )

    @staticmethod
    def _prompt(task: dict[str, Any]) -> str:
        return (
            "Execute exactly this bounded Eksamio implementation task. GitHub/task authority follows as JSON.\n"
            "Hard rules: do not merge, deploy, publish, pay/refund, mutate production learner data, send email/SMS, "
            "rotate/expose secrets, or call live external providers unless that exact action is present in requested_actions "
            "and separately authorized by the controller. Do not broaden scope. Preserve false_exact_mastery=0. "
            "Do not claim GitHub CI PASS; report only work actually performed in this checkout.\n\n"
            + canonical_json(task)
        )

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [CodexSdkExecutorAdapter._json_safe(x) for x in value]
        if isinstance(value, dict):
            return {str(k): CodexSdkExecutorAdapter._json_safe(v) for k, v in value.items()}
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if hasattr(value, "__dict__"):
            return {
                k: CodexSdkExecutorAdapter._json_safe(v)
                for k, v in vars(value).items()
                if not k.startswith("_")
            }
        return str(value)

    def execute(self, task: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
        validate_task_plan(task)
        self.permission_gate.assert_allowed(task["requested_actions"])
        self.assert_exact_checkout(task)

        if dry_run:
            return {
                "status": "DRY_RUN",
                "executor": "openai-codex",
                "task_hash": sha256_json(task),
                "repo_root": str(self.repo_root),
                "requested_model": self.model,
            }

        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY is required for API-key Codex SDK execution")

        try:
            from openai_codex import Codex, Sandbox
        except ImportError as exc:
            raise ProviderError("openai-codex is required for live Codex SDK execution") from exc

        try:
            with Codex() as codex:
                codex.login_api_key(self.api_key)
                thread_kwargs: dict[str, Any] = {
                    "cwd": str(self.repo_root),
                    "sandbox": Sandbox.workspace_write,
                    "developer_instructions": (
                        "You are the bounded Eksamio execution engineer. Obey task scope and stop conditions. "
                        "Never perform merge/deploy/publication/payment/production writes/live-provider actions unless "
                        "the task explicitly requests them and the controller has already authorized them."
                    ),
                }
                if self.model:
                    thread_kwargs["model"] = self.model
                thread = codex.thread_start(**thread_kwargs)
                result = thread.run(
                    self._prompt(task),
                    cwd=str(self.repo_root),
                    sandbox=Sandbox.workspace_write,
                )
        except Exception as exc:
            raise ProviderError(f"Codex SDK execution failed: {exc}") from exc

        error = getattr(result, "error", None)
        if error is not None:
            raise ProviderError(f"Codex turn returned an error: {error}")

        return {
            "status": str(getattr(result, "status", "UNKNOWN")),
            "executor": "openai-codex",
            "turn_id": getattr(result, "id", None),
            "final_response": getattr(result, "final_response", None),
            "duration_ms": getattr(result, "duration_ms", None),
            "usage": self._json_safe(getattr(result, "usage", None)),
            "task_hash": sha256_json(task),
            "base_sha": task["base_sha"],
            "target_branch": task["target_branch"],
            "requested_model": self.model,
        }
