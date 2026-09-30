#!/usr/bin/env python3
"""Minimal fail-closed Eksamio Astra -> Codex orchestration boundary.

v0.1 deliberately does not merge, deploy, publish, pay, send messages, mutate
production learner data, or invoke providers unless a later owner-controlled
layer explicitly grants that authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "0.1"
DEFAULT_ASTRA_MODEL = "gpt-6-astra"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
MODULE_ROOT = Path(__file__).resolve().parent

DANGEROUS_ACTIONS = frozenset(
    {
        "merge",
        "deploy",
        "public_publish",
        "public_traffic_change",
        "payment",
        "refund",
        "production_write",
        "production_migration",
        "live_provider_call",
        "send_email",
        "send_sms",
        "secret_create",
        "secret_rotate",
        "secret_expose",
        "destructive_repo_action",
        "destructive_cloud_action",
    }
)


class ContractError(ValueError):
    pass


class PermissionDenied(RuntimeError):
    pass


class ProviderError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require_exact_keys(value: dict[str, Any], required: set[str], optional: set[str]) -> None:
    missing = required - set(value)
    unknown = set(value) - required - optional
    if missing:
        raise ContractError(f"missing fields: {sorted(missing)}")
    if unknown:
        raise ContractError(f"unknown fields: {sorted(unknown)}")


def _require_sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise ContractError(f"{field} must be a lowercase 40-character git SHA")
    return value


def _require_string_list(value: Any, field: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ContractError(f"{field} must be a list of non-empty strings")
    if nonempty and not value:
        raise ContractError(f"{field} must not be empty")
    return list(value)


def validate_task_plan(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("task plan must be an object")
    required = {
        "schema_version",
        "repository",
        "base_sha",
        "target_branch",
        "goal",
        "allowed_scope",
        "non_goals",
        "acceptance_checks",
        "requested_actions",
    }
    _require_exact_keys(value, required, {"stop_conditions"})
    if value["schema_version"] != SCHEMA_VERSION:
        raise ContractError("unsupported task schema_version")
    if value["repository"] != "niknikdym-hue/ege":
        raise ContractError("task repository must be niknikdym-hue/ege")
    _require_sha(value["base_sha"], "base_sha")
    if not isinstance(value["target_branch"], str) or not value["target_branch"].strip():
        raise ContractError("target_branch must be non-empty")
    if not isinstance(value["goal"], str) or not value["goal"].strip():
        raise ContractError("goal must be non-empty")
    _require_string_list(value["allowed_scope"], "allowed_scope", nonempty=True)
    _require_string_list(value["non_goals"], "non_goals")
    _require_string_list(value["acceptance_checks"], "acceptance_checks", nonempty=True)
    _require_string_list(value["requested_actions"], "requested_actions")
    if "stop_conditions" in value:
        _require_string_list(value["stop_conditions"], "stop_conditions")
    return value


def validate_review_decision(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("review decision must be an object")
    required = {"schema_version", "decision", "reviewed_sha", "invariants", "evidence", "reason", "next_action"}
    _require_exact_keys(value, required, set())
    if value["schema_version"] != SCHEMA_VERSION:
        raise ContractError("unsupported review schema_version")
    if value["decision"] not in {"PASS", "REWORK", "BLOCKED"}:
        raise ContractError("decision must be PASS, REWORK or BLOCKED")
    _require_sha(value["reviewed_sha"], "reviewed_sha")
    invariants = value["invariants"]
    if not isinstance(invariants, dict):
        raise ContractError("invariants must be an object")
    invariant_keys = {"false_exact_mastery_zero", "server_owned_truth_preserved", "owner_gates_preserved"}
    _require_exact_keys(invariants, invariant_keys, set())
    if any(not isinstance(invariants[k], bool) for k in invariant_keys):
        raise ContractError("all invariant values must be booleans")
    _require_string_list(value["evidence"], "evidence")
    for field in ("reason", "next_action"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ContractError(f"{field} must be non-empty")
    if value["decision"] == "PASS" and not all(invariants.values()):
        raise ContractError("PASS is forbidden when any hard invariant is false")
    return value


@dataclass(frozen=True)
class PermissionGate:
    owner_authorized_actions: frozenset[str] = frozenset()

    def assert_allowed(self, requested_actions: Iterable[str]) -> None:
        requested = set(requested_actions)
        unknown_owner_grants = self.owner_authorized_actions - DANGEROUS_ACTIONS
        if unknown_owner_grants:
            raise PermissionDenied(f"invalid owner authorization names: {sorted(unknown_owner_grants)}")
        forbidden = (requested & DANGEROUS_ACTIONS) - self.owner_authorized_actions
        if forbidden:
            raise PermissionDenied(f"owner authorization required: {sorted(forbidden)}")


class AstraResponsesAdapter:
    """Small Responses API adapter. Network use is opt-in; tests never call it."""

    def __init__(self, *, api_key: str | None = None, model: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_ASTRA_MODEL", DEFAULT_ASTRA_MODEL)
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL)).rstrip("/")

    @staticmethod
    def _extract_output_text(response: dict[str, Any]) -> str:
        chunks: list[str] = []
        for item in response.get("output", []):
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    chunks.append(content["text"])
        if not chunks:
            raise ProviderError("Astra response did not contain output_text")
        return "".join(chunks)

    def structured(self, *, instructions: str, input_text: str, schema_name: str, schema: dict[str, Any], reasoning_effort: str = "high") -> dict[str, Any]:
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY is required for a live Astra call")
        payload = {
            "model": self.model,
            "instructions": instructions,
            "input": input_text,
            "reasoning": {"effort": reasoning_effort},
            "text": {"format": {"type": "json_schema", "name": schema_name, "strict": True, "schema": schema}},
            "store": False,
        }
        request = urllib.request.Request(
            f"{self.base_url}/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ProviderError(f"Astra Responses API call failed: {exc}") from exc
        if body.get("status") != "completed":
            raise ProviderError(f"Astra response status is not completed: {body.get('status')}")
        try:
            structured_output = json.loads(self._extract_output_text(body))
        except json.JSONDecodeError as exc:
            raise ProviderError("Astra Structured Output was not valid JSON") from exc
        return {
            "output": structured_output,
            "provider_metadata": {
                "requested_model": self.model,
                "returned_model": body.get("model"),
                "response_id": body.get("id"),
                "usage": body.get("usage") or {},
            },
        }

    def plan(self, repository_context: dict[str, Any]) -> dict[str, Any]:
        schema = _load_json(MODULE_ROOT / "schemas" / "task-plan-v0.1.schema.json")
        result = self.structured(
            instructions=(
                "You are Eksamio Senior Brain. Use only the supplied GitHub evidence. "
                "Return one bounded implementation task. Preserve false_exact_mastery=0 and owner gates. "
                "Never infer PASS from missing evidence."
            ),
            input_text=canonical_json(repository_context),
            schema_name="eksamio_task_plan_v0_1",
            schema=schema,
            reasoning_effort="high",
        )
        validate_task_plan(result["output"])
        return result

    def review(self, review_context: dict[str, Any]) -> dict[str, Any]:
        schema = _load_json(MODULE_ROOT / "schemas" / "review-decision-v0.1.schema.json")
        result = self.structured(
            instructions=(
                "You are Eksamio Senior Brain reviewing an exact GitHub head and CI evidence. "
                "Return PASS, REWORK, or BLOCKED. PASS is forbidden unless every hard invariant is true "
                "and the supplied exact-head evidence proves the bounded task."
            ),
            input_text=canonical_json(review_context),
            schema_name="eksamio_review_decision_v0_1",
            schema=schema,
            reasoning_effort="high",
        )
        validate_review_decision(result["output"])
        return result


class CodexExecutorAdapter:
    """Fail-closed executor boundary.

    v0.1 does not embed a shell command into the task contract. A trusted local/CI
    integration supplies EKSAMIO_CODEX_COMMAND. JSON is passed on stdin, and
    shell=True is never used. This boundary can be replaced by the Codex SDK
    without changing the Astra task contract.
    """

    def __init__(self, command: str | None = None):
        self.command = command or os.getenv("EKSAMIO_CODEX_COMMAND")

    def execute(self, task: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
        validate_task_plan(task)
        if dry_run:
            return {"status": "DRY_RUN", "task_hash": sha256_json(task), "command_configured": bool(self.command)}
        if not self.command:
            raise ProviderError("EKSAMIO_CODEX_COMMAND is required for non-dry-run Codex execution")
        args = shlex.split(self.command)
        if not args:
            raise ProviderError("EKSAMIO_CODEX_COMMAND resolved to an empty command")
        completed = subprocess.run(
            args,
            input=canonical_json(task),
            text=True,
            capture_output=True,
            check=False,
            timeout=3600,
        )
        if completed.returncode != 0:
            raise ProviderError(f"Codex executor failed with exit {completed.returncode}: {completed.stderr[-2000:]}")
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ProviderError("Codex executor stdout must be one JSON object") from exc
        if not isinstance(result, dict):
            raise ProviderError("Codex executor result must be an object")
        return result


def build_run_record(*, phase: str, git_sha: str, input_object: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    _require_sha(git_sha, "git_sha")
    return {
        "schema_version": SCHEMA_VERSION,
        "phase": phase,
        "git_sha": git_sha,
        "input_sha256": sha256_json(input_object),
        "result": result,
        "created_at_unix": int(time.time()),
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError(f"{path} must contain a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Eksamio agent orchestration v0.1")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_task = sub.add_parser("validate-task")
    validate_task.add_argument("path", type=Path)

    validate_review = sub.add_parser("validate-review")
    validate_review.add_argument("path", type=Path)

    dry_run = sub.add_parser("dry-run")
    dry_run.add_argument("path", type=Path)
    dry_run.add_argument("--git-sha", required=True)

    args = parser.parse_args(argv)
    if args.command == "validate-task":
        validate_task_plan(_load_json(args.path))
        print("PASS")
        return 0
    if args.command == "validate-review":
        validate_review_decision(_load_json(args.path))
        print("PASS")
        return 0
    if args.command == "dry-run":
        task = validate_task_plan(_load_json(args.path))
        PermissionGate().assert_allowed(task["requested_actions"])
        result = CodexExecutorAdapter().execute(task, dry_run=True)
        print(json.dumps(build_run_record(phase="CODEX_DRY_RUN", git_sha=args.git_sha, input_object=task, result=result), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, PermissionDenied, ProviderError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
