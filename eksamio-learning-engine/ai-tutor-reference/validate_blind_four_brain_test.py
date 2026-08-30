#!/usr/bin/env python3
"""Offline acceptance for blind A/B/C/D Tutor comparison."""
from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path

import private_four_brain_blind_test_ui as blind

HERE = Path(__file__).resolve().parent
FIXTURE_SHA = "1" * 40


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


def main() -> int:
    original_home = os.environ.get("HOME")
    original_sha = os.environ.get("EKSAMIO_TUTOR_CANDIDATE_SHA")
    try:
        with tempfile.TemporaryDirectory() as temp_home:
            os.environ["HOME"] = temp_home
            os.environ["EKSAMIO_TUTOR_CANDIDATE_SHA"] = FIXTURE_SHA
            test_id, mapping = blind._create_mapping()
            require(set(mapping) == {"A", "B", "C", "D"}, "blind mapping exposes exactly four aliases")
            require(set(mapping.values()) == {"openai", "qwen", "deepseek", "yandex"}, "blind mapping is a permutation of all four brains")
            mapping_file = Path(temp_home) / "Library" / "Application Support" / "Eksamio" / "TutorBlindTests" / f"{test_id}.json"
            require(mapping_file.exists(), "blind mapping is persisted locally for post-test reveal")
            require(stat.S_IMODE(mapping_file.stat().st_mode) == 0o600, "blind mapping file is owner-only 0600")
            require(stat.S_IMODE(mapping_file.parent.stat().st_mode) == 0o700, "blind mapping directory is owner-only 0700")
            payload = json.loads(mapping_file.read_text(encoding="utf-8"))
            require(payload.get("candidate_sha") == FIXTURE_SHA, "blind mapping is bound to exact candidate SHA")

            text_page = blind._blind_page(speech_enabled=False, test_id=test_id)
            voice_page = blind._blind_page(speech_enabled=True, test_id=test_id)
            for provider_name in ("OpenAI", "Qwen", "DeepSeek", "Alice AI"):
                require(provider_name not in text_page, f"blind text page hides brain name {provider_name}")
                require(provider_name not in voice_page, f"blind voice page hides brain name {provider_name}")
            require("Вариант A" in text_page and "Вариант D" in text_page, "blind page exposes A/B/C/D choices")
            require("Yandex SpeechKit STT + Lera TTS" in voice_page, "blind voice page discloses the common voice layer without revealing brain mapping")
    finally:
        if original_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = original_home
        if original_sha is None:
            os.environ.pop("EKSAMIO_TUTOR_CANDIDATE_SHA", None)
        else:
            os.environ["EKSAMIO_TUTOR_CANDIDATE_SHA"] = original_sha

    command_paths = {
        "blind_text": HERE / "launch_four_brain_blind_text_test.command",
        "blind_voice": HERE / "launch_four_brain_blind_voice_test.command",
        "reveal": HERE / "reveal_latest_blind_tutor_mapping.command",
    }
    for name, path in command_paths.items():
        require(bool(path.stat().st_mode & stat.S_IXUSR), f"{name} launcher is executable")
        text = path.read_text(encoding="utf-8")
        require("set -euo pipefail" in text, f"{name} launcher fails closed")
    require("private_tutor_runtime_gate.zsh" in command_paths["blind_text"].read_text(encoding="utf-8"), "blind text launcher requires exact-build runtime gate")
    require("private_tutor_runtime_gate.zsh" in command_paths["blind_voice"].read_text(encoding="utf-8"), "blind voice launcher requires exact-build runtime gate")
    require("--enable-speech" not in command_paths["blind_text"].read_text(encoding="utf-8"), "blind text launcher cannot enable speech")
    require("--enable-speech" in command_paths["blind_voice"].read_text(encoding="utf-8"), "blind voice launcher explicitly enables the common speech layer")
    reveal_text = command_paths["reveal"].read_text(encoding="utf-8")
    require("ПОСЛЕ" in reveal_text and "Раскрыть A/B/C/D" in reveal_text, "mapping reveal requires explicit post-evaluation confirmation")

    print("BLIND_FOUR_BRAIN_TEST_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
