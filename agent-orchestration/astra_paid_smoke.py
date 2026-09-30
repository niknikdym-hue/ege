#!/usr/bin/env python3
"""One bounded paid API smoke for the Eksamio Astra brain.

The script sends no repository content and never prints the API key.  Its JSON
artifact contains only provider metadata, token usage, and the fixed sentinel
returned by the model.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_MODEL = "gpt-6-astra"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
EXPECTED_OUTPUT = "ASTRA_API_OK"


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
    return "".join(chunks).strip()


def _safe_error(raw: bytes) -> dict[str, Any]:
    try:
        body = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"type": "non_json_error", "message": "OpenAI returned a non-JSON error response"}
    error = body.get("error") if isinstance(body, dict) else None
    if not isinstance(error, dict):
        return {"type": "unknown_api_error", "message": "OpenAI returned an unrecognized error response"}
    return {
        "type": str(error.get("type") or "api_error")[:120],
        "code": str(error.get("code") or "")[:120],
        "message": str(error.get("message") or "")[:800],
    }


def _write(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(*, output_path: Path) -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        result = {"status": "FAILED", "error": {"type": "missing_key", "message": "OPENAI_API_KEY is absent"}}
        _write(output_path, result)
        print(json.dumps(result, ensure_ascii=False))
        return 2

    model = os.getenv("OPENAI_ASTRA_MODEL", DEFAULT_MODEL)
    base_url = os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    payload = {
        "model": model,
        "instructions": "This is a bounded provider-connectivity test. Follow the requested output exactly.",
        "input": "Reply with exactly ASTRA_API_OK and nothing else.",
        "reasoning": {"effort": "low"},
        "text": {"verbosity": "low"},
        "max_output_tokens": 128,
        "store": False,
    }
    request = urllib.request.Request(
        f"{base_url}/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "eksamio-astra-paid-smoke/0.1",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        result = {
            "status": "FAILED",
            "http_status": exc.code,
            "requested_model": model,
            "error": _safe_error(exc.read()),
        }
        _write(output_path, result)
        print(json.dumps(result, ensure_ascii=False))
        return 2
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        result = {
            "status": "FAILED",
            "requested_model": model,
            "error": {"type": "transport_or_decode_error", "message": str(exc)[:800]},
        }
        _write(output_path, result)
        print(json.dumps(result, ensure_ascii=False))
        return 2

    output_text = _output_text(body)
    passed = body.get("status") == "completed" and output_text == EXPECTED_OUTPUT
    result = {
        "status": "PASS" if passed else "FAILED",
        "requested_model": model,
        "returned_model": body.get("model"),
        "response_id": body.get("id"),
        "provider_status": body.get("status"),
        "output": output_text,
        "usage": body.get("usage") or {},
        "store": False,
        "repository_content_sent": False,
    }
    _write(output_path, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if passed else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one bounded paid GPT-6 Astra API smoke")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    return run(output_path=args.output)


if __name__ == "__main__":
    raise SystemExit(main())
