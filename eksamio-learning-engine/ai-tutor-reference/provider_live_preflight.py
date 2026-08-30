#!/usr/bin/env python3
"""Non-billing local preflight for Tutor provider human tests.

This script resolves only local configuration/Keychain presence. It performs no
network request and therefore cannot prove account scope, billing or provider
availability. Secret values are never printed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from deepseek_secret_provider import DeepSeekSecretProvider  # noqa: E402
from openai_secret_provider import OpenAISecretProvider  # noqa: E402
from private_provider_config import load_private_provider_config  # noqa: E402
from qwen_live_adapter import resolve_qwen_chat_endpoint  # noqa: E402
from qwen_secret_provider import QwenSecretProvider  # noqa: E402
from yandex_ai_secret_provider import YandexAISecretProvider  # noqa: E402
from yandex_speech_secret_provider import YandexSpeechSecretProvider  # noqa: E402


def credential_present(provider: Callable[[], str]) -> bool:
    try:
        value = provider()
    except Exception:
        return False
    return isinstance(value, str) and bool(value.strip())


def qwen_endpoint_state(raw: str | None) -> tuple[bool, str]:
    if not isinstance(raw, str) or not raw.strip():
        return False, "missing Qwen base URL in env/private provider config"
    try:
        endpoint = resolve_qwen_chat_endpoint(raw, execution_enabled=True)
    except Exception as exc:
        return False, f"invalid base URL: {exc}"
    host = endpoint.split("/", 3)[2]
    return True, f"configured host={host}"


def main() -> int:
    local_config = load_private_provider_config()
    qwen_endpoint_ok, qwen_endpoint_detail = qwen_endpoint_state(local_config.qwen_base_url)
    folder_present = bool(local_config.yandex_folder_id)
    states = {
        "openai_credential_present": credential_present(OpenAISecretProvider()),
        "qwen_credential_present": credential_present(QwenSecretProvider()),
        "qwen_endpoint_valid": qwen_endpoint_ok,
        "qwen_endpoint_detail": qwen_endpoint_detail,
        "deepseek_credential_present": credential_present(DeepSeekSecretProvider()),
        "yandex_ai_credential_present": credential_present(YandexAISecretProvider()),
        "yandex_speechkit_credential_present": credential_present(YandexSpeechSecretProvider()),
        "yandex_folder_id_present": folder_present,
        "network_calls": 0,
        "provider_secret_values_printed": 0,
    }
    states["qwen_human_test_local_ready"] = bool(states["qwen_credential_present"] and qwen_endpoint_ok)
    states["deepseek_human_test_local_ready"] = bool(states["deepseek_credential_present"])
    states["yandex_brain_human_test_local_ready"] = bool(states["yandex_ai_credential_present"] and folder_present)
    states["yandex_voice_human_test_local_ready"] = bool(states["yandex_speechkit_credential_present"] and folder_present)

    print(json.dumps(states, ensure_ascii=False, indent=2, sort_keys=True))
    print("NOTE=credential presence does not prove scope/billing/provider availability; owner-authorized live smoke is still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
