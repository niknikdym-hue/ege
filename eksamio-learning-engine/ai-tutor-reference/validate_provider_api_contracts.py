#!/usr/bin/env python3
"""Offline contract pins for the live Tutor provider endpoints/models.

These assertions intentionally contain no provider secrets and perform no
network calls. They protect the live-test branch from silently drifting back to
obsolete endpoint/model URI shapes.
"""
from __future__ import annotations

from qwen_live_adapter import QwenTutorConfig, resolve_qwen_chat_endpoint
from yandex_alice_live_adapter import YandexAliceTutorConfig


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


def main() -> int:
    qwen = QwenTutorConfig(
        model="qwen3.8-max",
        base_url="https://fixture-workspace.us-east-1.maas.aliyuncs.com/compatible-mode/v1",
        execution_enabled=False,
    )
    require(qwen.model == "qwen3.8-max", "Qwen live-test model remains qwen3.8-max")
    require(
        resolve_qwen_chat_endpoint(qwen.base_url, execution_enabled=True)
        == "https://fixture-workspace.us-east-1.maas.aliyuncs.com/compatible-mode/v1/chat/completions",
        "Qwen workspace base resolves to the OpenAI-compatible chat-completions endpoint",
    )

    yandex = YandexAliceTutorConfig(
        folder_id="fixture-folder",
        model_id="aliceai-llm",
        execution_enabled=False,
    )
    require(
        yandex.endpoint == "https://ai.api.cloud.yandex.net/v1/chat/completions",
        "Yandex Alice uses the current OpenAI-compatible AI Studio chat endpoint",
    )
    require(
        yandex.model_uri == "gpt://fixture-folder/aliceai-llm/latest",
        "Yandex Alice model URI is explicitly pinned to /latest",
    )

    print("TUTOR_PROVIDER_API_CONTRACTS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
