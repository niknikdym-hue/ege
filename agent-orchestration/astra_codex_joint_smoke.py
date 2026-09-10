#!/usr/bin/env python3
"""Bounded paid Astra Brain -> Codex -> Astra review smoke controller."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ASTRA_MODEL = "gpt-6-astra"
BASE_URL = "https://api.openai.com/v1"
TARGET_FILE = "agent-orchestration/README.md"
EXPECTED_ARCHITECTURE = "GitHub truth -> Astra Senior Brain -> bounded Codex executor -> CI -> Astra review -> GitHub"


PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string", "const": "astra-codex-joint-smoke-v0.1"},
        "executor": {"type": "string", "const": "codex"},
        "mode": {"type": "string", "const": "read_only"},
        "target_file": {"type": "string", "const": TARGET_FILE},
        "instruction": {"type": "string", "minLength": 1},
        "expected_architecture": {"type": "string", "const": EXPECTED_ARCHITECTURE},
        "forbidden_actions": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 4,
        },
    },
    "required": [
        "task_id",
        "executor",
        "mode",
        "target_file",
        "instruction",
        "expected_architecture",
        "forbidden_actions",
    ],
    "additionalProperties": False,
}


REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": ["PASS", "BLOCKED"]},
        "codex_executed": {"type": "boolean"},
        "expected_architecture_verified": {"type": "boolean"},
        "read_only_preserved": {"type": "boolean"},
        "reason": {"type": "string", "minLength": 1},
    },
    "required": [
        "decision",
        "codex_executed",
        "expected_architecture_verified",
        "read_only_preserved",
        "reason",
    ],
    "additionalProperties": False,
}


class SmokeError(RuntimeError):
    pass


def _output_text(response: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if (
                isinstance(content, dict)
                and content.get("type") == "output_text"
                and isinstance(content.get("text"), str)
            ):
                chunks.append(content["text"])
    if not chunks:
        raise SmokeError("Astra response did not contain output_text")
    return "".join(chunks)


def _safe_api_error(raw: bytes) -> str:
    try:
        body = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return "OpenAI returned a non-JSON error"
    error = body.get("error") if isinstance(body, dict) else None
    if not isinstance(error, dict):
        return "OpenAI returned an unrecognized error"
    return json.dumps(
        {
            "type": str(error.get("type") or "api_error")[:120],
            "code": str(error.get("code") or "")[:120],
            "message": str(error.get("message") or "")[:800],
        },
        ensure_ascii=False,
    )


def _astra_structured(
    *,
    instructions: str,
    input_object: dict[str, Any],
    schema_name: str,
    schema: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SmokeError("OPENAI_API_KEY is absent")
    model = os.getenv("OPENAI_ASTRA_MODEL", ASTRA_MODEL)
    base_url = os.getenv("OPENAI_BASE_URL", BASE_URL).rstrip("/")
    payload = {
        "model": model,
        "instructions": instructions,
        "input": json.dumps(input_object, ensure_ascii=False, sort_keys=True),
        "reasoning": {"effort": "low"},
        "text": {
            "verbosity": "low",
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        },
        "max_output_tokens": 1024,
        "store": False,
    }
    request = urllib.request.Request(
        f"{base_url}/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "eksamio-astra-codex-joint-smoke/0.1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SmokeError(f"Astra HTTP {exc.code}: {_safe_api_error(exc.read())}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise SmokeError(f"Astra transport/decode failure: {exc}") from exc
    if body.get("status") != "completed":
        raise SmokeError(f"Astra response status is {body.get('status')!r}")
    try:
        output = json.loads(_output_text(body))
    except json.JSONDecodeError as exc:
        raise SmokeError("Astra output was not valid JSON") from exc
    if not isinstance(output, dict):
        raise SmokeError("Astra output was not an object")
    metadata = {
        "requested_model": model,
        "returned_model": body.get("model"),
        "response_id": body.get("id"),
        "usage": body.get("usage") or {},
        "store": False,
    }
    return output, metadata


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def plan(*, branch: str, head_sha: str, plan_path: Path, prompt_path: Path) -> int:
    plan_output, metadata = _astra_structured(
        instructions=(
            "You are Astra, the Eksamio Senior Brain. Produce one minimal read-only task for Codex. "
            "Codex must inspect only the supplied target file, verify the expected architecture statement, "
            "make no edits, and report evidence. Do not broaden scope."
        ),
        input_object={
            "repository": "niknikdym-hue/ege",
            "branch": branch,
            "head_sha": head_sha,
            "target_file": TARGET_FILE,
            "expected_architecture": EXPECTED_ARCHITECTURE,
            "hard_boundaries": ["no edits", "no commit", "no push", "no merge", "no deploy", "no network tools"],
        },
        schema_name="eksamio_astra_codex_joint_plan_v0_1",
        schema=PLAN_SCHEMA,
    )
    if (
        plan_output.get("task_id") != "astra-codex-joint-smoke-v0.1"
        or plan_output.get("executor") != "codex"
        or plan_output.get("mode") != "read_only"
        or plan_output.get("target_file") != TARGET_FILE
        or plan_output.get("expected_architecture") != EXPECTED_ARCHITECTURE
    ):
        raise SmokeError("Astra plan changed a controller-owned boundary")
    _write_json(plan_path, {"status": "PASS", "plan": plan_output, "astra": metadata})
    prompt_path.write_text(
        "You are the bounded Codex executor. Execute the Astra plan below.\n"
        "Use read-only inspection. Do not edit, commit, push, merge, deploy, or call network tools.\n"
        "Return concise JSON with keys status, target_file, observed_architecture, matches_expected, files_changed.\n\n"
        + json.dumps(plan_output, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "phase": "ASTRA_PLAN", "astra": metadata}, ensure_ascii=False))
    return 0


def review(*, plan_path: Path, codex_path: Path, checkout_clean: bool, result_path: Path) -> int:
    plan_record = json.loads(plan_path.read_text(encoding="utf-8"))
    codex_output = codex_path.read_text(encoding="utf-8", errors="replace")[:8000]
    decision, metadata = _astra_structured(
        instructions=(
            "You are Astra, the Eksamio Senior Brain reviewing the first Codex executor smoke. "
            "Return PASS only if Codex executed the supplied plan, verified the exact expected architecture, "
            "and the deterministic checkout_clean evidence is true. Otherwise return BLOCKED."
        ),
        input_object={
            "plan": plan_record.get("plan"),
            "codex_final_response": codex_output,
            "deterministic_evidence": {"checkout_clean": checkout_clean},
        },
        schema_name="eksamio_astra_codex_joint_review_v0_1",
        schema=REVIEW_SCHEMA,
    )
    passed = (
        decision.get("decision") == "PASS"
        and decision.get("codex_executed") is True
        and decision.get("expected_architecture_verified") is True
        and decision.get("read_only_preserved") is True
        and checkout_clean
    )
    result = {
        "status": "PASS" if passed else "BLOCKED",
        "plan": plan_record,
        "codex": {
            "runner": "openai/codex-action@v1",
            "model": "gpt-5.6-terra",
            "sandbox": "read-only",
            "final_response": codex_output,
        },
        "deterministic_evidence": {"checkout_clean": checkout_clean},
        "astra_review": {"decision": decision, "astra": metadata},
    }
    _write_json(result_path, result)
    print(json.dumps({"status": result["status"], "phase": "ASTRA_REVIEW", "astra": metadata}, ensure_ascii=False))
    return 0 if passed else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run bounded Astra/Codex joint smoke phases")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--branch", required=True)
    plan_parser.add_argument("--head-sha", required=True)
    plan_parser.add_argument("--plan-out", required=True, type=Path)
    plan_parser.add_argument("--prompt-out", required=True, type=Path)

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("--plan", required=True, type=Path)
    review_parser.add_argument("--codex-output", required=True, type=Path)
    review_parser.add_argument("--checkout-clean", choices=["true", "false"], required=True)
    review_parser.add_argument("--result-out", required=True, type=Path)

    args = parser.parse_args(argv)
    if args.command == "plan":
        return plan(branch=args.branch, head_sha=args.head_sha, plan_path=args.plan_out, prompt_path=args.prompt_out)
    return review(
        plan_path=args.plan,
        codex_path=args.codex_output,
        checkout_clean=args.checkout_clean == "true",
        result_path=args.result_out,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2)
