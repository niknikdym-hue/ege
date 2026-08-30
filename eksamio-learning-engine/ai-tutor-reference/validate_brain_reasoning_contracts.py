#!/usr/bin/env python3
"""Offline provider-specific reasoning-contract acceptance for Tutor tests."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from deepseek_live_adapter import DeepSeekTextProvider, DeepSeekTutorConfig  # noqa: E402
from qwen_live_adapter import QwenTextProvider, QwenTutorConfig  # noqa: E402
from tutor_boundary import ProviderRequest  # noqa: E402

QWEN_BASE = "https://test-workspace.us-east-1.maas.aliyuncs.com/compatible-mode/v1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


class NoCallTransport:
    def post_json(self, **kwargs: Any) -> Mapping[str, Any]:
        raise AssertionError("reasoning contract validator must not execute a provider call")


def request() -> ProviderRequest:
    return ProviderRequest(
        contract_version="eksamio.tutor.provider-request.v1",
        correlation_ref="reasoning-contract-turn",
        subject_id="russian",
        learning_goal="Explain a verified Russian-language concept pedagogically.",
        policy_instruction="Use only verified context. Do not invent facts.",
        verified_source_refs=("source:fixture-reasoning-contract",),
        verified_excerpts=("Проверенный контекст: тестовая учебная опора.",),
        peis_learning_summary="fixture learner summary",
        target_refs=("fixture-target",),
        history=(),
        learner_text="Объясни правило простыми словами.",
        allowed_tool_names=(),
    )


def main() -> int:
    qwen = QwenTextProvider(
        config=QwenTutorConfig(
            base_url=QWEN_BASE,
            thinking_enabled=True,
            preserve_thinking=False,
            max_completion_tokens=4096,
            execution_enabled=False,
        ),
        transport=NoCallTransport(),
    )
    qwen_body = qwen._request_body(request())
    require(qwen_body["model"] == "qwen3.8-max", "Qwen quality test uses qwen3.8-max")
    require(qwen_body["enable_thinking"] is True, "Qwen thinking is explicitly enabled")
    require(qwen_body["preserve_thinking"] is False, "Qwen hidden reasoning is explicitly not carried across Tutor turns")
    require(qwen_body["max_completion_tokens"] == 4096, "Qwen thinking+answer budget is explicitly bounded at 4096 tokens")
    require("max_tokens" not in qwen_body, "Qwen thinking contract uses max_completion_tokens instead of legacy max_tokens")

    deepseek = DeepSeekTextProvider(
        config=DeepSeekTutorConfig(
            thinking_enabled=True,
            reasoning_effort="high",
            max_output_tokens=4096,
            execution_enabled=False,
        ),
        transport=NoCallTransport(),
    )
    deepseek_body = deepseek._request_body(request())
    require(deepseek_body["model"] == "deepseek-v4-pro", "DeepSeek quality test uses V4 Pro")
    require(deepseek_body["thinking"] == {"type": "enabled"}, "DeepSeek thinking is explicitly enabled")
    require(deepseek_body["reasoning_effort"] == "high", "DeepSeek reasoning effort is explicitly high")
    require(deepseek_body["max_tokens"] == 4096, "DeepSeek generated-output budget is explicitly bounded at 4096 tokens")
    require("temperature" not in deepseek_body, "DeepSeek thinking request omits provider-ignored temperature")

    print("BRAIN_REASONING_CONTRACTS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
