#!/usr/bin/env python3
"""Offline provider-specific reasoning-contract acceptance for Tutor tests."""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from deepseek_live_adapter import DeepSeekTextProvider, DeepSeekTutorConfig  # noqa: E402
from qwen_live_adapter import QwenTextProvider, QwenTutorConfig  # noqa: E402
from reliability_gateway import ProviderAttempt  # noqa: E402
from tutor_boundary import ProviderRequest  # noqa: E402

QWEN_BASE = "https://test-workspace.us-east-1.maas.aliyuncs.com/compatible-mode/v1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


@contextmanager
def fake_credentials():
    names = {
        "QWEN_API_KEY": "fixture-qwen",
        "DEEPSEEK_API_KEY": "fixture-deepseek",
    }
    old = {name: os.environ.get(name) for name in names}
    os.environ.update(names)
    try:
        yield
    finally:
        for name, value in old.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


class CaptureTransport:
    def __init__(self, response: Mapping[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def post_json(self, *, url: str, headers: Mapping[str, str], body: Mapping[str, Any], timeout_seconds: float) -> Mapping[str, Any]:
        self.calls.append({"url": url, "headers": dict(headers), "body": dict(body)})
        return self.response


def request() -> ProviderRequest:
    return ProviderRequest(
        logical_turn_id="reasoning-contract-turn",
        session_ref="tutor:reasoning-contract",
        learner_message="Объясни правило простыми словами.",
        grounded_context="Проверенный контекст: тестовая учебная опора.",
        verified_source_refs=("fixture-source",),
        conversation_history=(),
    )


def attempt(provider_id: str) -> ProviderAttempt:
    return ProviderAttempt(
        logical_turn_id="reasoning-contract-turn",
        provider_id=provider_id,
        capability="text",
        attempt_number=1,
    )


def main() -> int:
    with fake_credentials():
        qwen_transport = CaptureTransport({"choices": [{"message": {"content": "QWEN_OK", "reasoning_content": "hidden"}}]})
        qwen = QwenTextProvider(
            config=QwenTutorConfig(
                base_url=QWEN_BASE,
                thinking_enabled=True,
                preserve_thinking=False,
                max_completion_tokens=4096,
                execution_enabled=True,
            ),
            transport=qwen_transport,
        )
        qwen.generate(request(), attempt(qwen.provider_id))
        qwen_body = qwen_transport.calls[0]["body"]
        require(qwen_body["model"] == "qwen3.8-max", "Qwen quality test uses qwen3.8-max")
        require(qwen_body["enable_thinking"] is True, "Qwen thinking is explicitly enabled")
        require(qwen_body["preserve_thinking"] is False, "Qwen hidden reasoning is explicitly not carried across Tutor turns")
        require(qwen_body["max_completion_tokens"] == 4096, "Qwen thinking+answer budget is explicitly bounded at 4096 tokens")
        require("max_tokens" not in qwen_body, "Qwen thinking contract uses max_completion_tokens instead of legacy max_tokens")

        deepseek_transport = CaptureTransport({"choices": [{"message": {"content": "DEEPSEEK_OK", "reasoning_content": "hidden"}}]})
        deepseek = DeepSeekTextProvider(
            config=DeepSeekTutorConfig(
                thinking_enabled=True,
                reasoning_effort="high",
                max_output_tokens=4096,
                execution_enabled=True,
            ),
            transport=deepseek_transport,
        )
        deepseek.generate(request(), attempt(deepseek.provider_id))
        deepseek_body = deepseek_transport.calls[0]["body"]
        require(deepseek_body["model"] == "deepseek-v4-pro", "DeepSeek quality test uses V4 Pro")
        require(deepseek_body["thinking"] == {"type": "enabled"}, "DeepSeek thinking is explicitly enabled")
        require(deepseek_body["reasoning_effort"] == "high", "DeepSeek reasoning effort is explicitly high")
        require(deepseek_body["max_tokens"] == 4096, "DeepSeek generated-output budget is explicitly bounded at 4096 tokens")
        require("temperature" not in deepseek_body, "DeepSeek thinking request omits provider-ignored temperature")

    print("BRAIN_REASONING_CONTRACTS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
