#!/usr/bin/env python3
"""Offline acceptance for four-brain human-test launch surfaces."""
from __future__ import annotations

import stat
from pathlib import Path

HERE = Path(__file__).resolve().parent

COMMANDS = {
    "config": HERE / "configure_private_provider_config.command",
    "preflight": HERE / "launch_tutor_provider_preflight.command",
    "smoke": HERE / "launch_brain_provider_smoke.command",
    "text": HERE / "launch_four_brain_text_test.command",
    "voice": HERE / "launch_four_brain_voice_test.command",
    "failover": HERE / "launch_four_brain_failover_test.command",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


def read(name: str) -> str:
    path = COMMANDS[name]
    require(bool(path.stat().st_mode & stat.S_IXUSR), f"{name} launcher is owner-executable")
    text = path.read_text(encoding="utf-8")
    require(text.startswith("#!/bin/zsh\n") and "set -euo pipefail" in text, f"{name} launcher fails closed under zsh")
    return text


def main() -> int:
    texts = {name: read(name) for name in COMMANDS}

    require("provider_live_preflight.py" in texts["preflight"], "zero-call preflight launcher runs local readiness check")
    require("owner-authorized" not in texts["preflight"], "zero-call preflight does not grant provider execution")
    require("API-вызовов и расходов" in texts["preflight"], "preflight explicitly discloses zero API spend")

    require("configure_private_provider_config.py" in texts["config"], "config launcher writes only the non-secret config surface")
    require("НЕСЕКРЕТНЫЙ" in texts["config"], "config launcher labels values as non-secret")

    require("--owner-authorized --provider all" in texts["smoke"], "smoke launcher owner-authorizes exactly the bounded provider smoke")
    require("ровно три" in texts["smoke"] and "Qwen, DeepSeek и Alice AI" in texts["smoke"], "smoke launcher discloses three real provider calls")

    require("--owner-authorized --max-turns 20" in texts["text"], "text launcher preserves 20-turn owner gate")
    require("--enable-speech" not in texts["text"], "text comparison cannot accidentally enable speech")

    require("--owner-authorized --enable-speech --max-turns 20" in texts["voice"], "voice comparison explicitly enables speech after owner gate")
    require("Yandex SpeechKit STT + Lera TTS" in texts["voice"], "voice launcher discloses the fixed Yandex speech layer")
    require("Аудио не сохраняется" in texts["voice"], "voice launcher discloses transient audio")

    require("--default-provider auto --lock-provider" in texts["failover"], "failover launcher locks AUTO mode")
    require("--simulate-unavailable \"$SIMULATED\"" in texts["failover"], "failover launcher uses deterministic local outage injection")
    require("Отключённые backend'ы НЕ вызываются по сети" in texts["failover"], "failover launcher discloses no network call to simulated failures")

    forbidden = (
        "--api-key",
        "--secret",
        "OPENAI_API_KEY=",
        "QWEN_API_KEY=",
        "DASHSCOPE_API_KEY=",
        "DEEPSEEK_API_KEY=",
        "YANDEX_AI_STUDIO_API_KEY=",
        "YANDEX_SPEECHKIT_API_KEY=",
    )
    for name, text in texts.items():
        for fragment in forbidden:
            require(fragment not in text, f"{name} launcher contains no secret CLI/env assignment: {fragment}")

    print("FOUR_BRAIN_TEST_PREP_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
