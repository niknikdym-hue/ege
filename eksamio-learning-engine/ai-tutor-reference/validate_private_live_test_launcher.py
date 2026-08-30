#!/usr/bin/env python3
"""Offline acceptance checks for the macOS private Tutor live-test launcher."""
from __future__ import annotations

import stat
from pathlib import Path


HERE = Path(__file__).resolve().parent
LAUNCHER = HERE / "launch_private_tutor_live_test.command"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    mode = LAUNCHER.stat().st_mode
    text = LAUNCHER.read_text(encoding="utf-8")

    require(bool(mode & stat.S_IXUSR), "launcher must retain executable owner bit")
    require(text.startswith("#!/bin/zsh\n"), "launcher must use zsh shebang")
    require("set -euo pipefail" in text, "launcher must fail closed")
    require("python3.12" in text and "sys.version_info >= (3, 12)" in text, "launcher must require Python 3.12+")
    require("git -C \"$REPO_ROOT\" rev-parse HEAD" in text, "launcher must resolve exact local candidate SHA")
    require("EKSAMIO_TUTOR_CANDIDATE_SHA" in text, "launcher must pass candidate SHA to evidence wrapper")
    require("osascript" in text, "launcher must use local macOS owner confirmation")
    require("Разрешаю тест" in text and "Отмена" in text, "launcher must present explicit owner allow/cancel controls")
    require("API-расходы" in text, "launcher confirmation must disclose possible provider spend")
    require("production PEIS" in text and "голос остаются выключены" in text, "launcher must disclose disabled production/voice boundaries")
    require("защищённого хранилища" in text, "launcher must state secure automatic credential resolution")
    require("private_multi_provider_tutor_live_test_candidate.py" in text, "launcher must start the evidence-bound private Tutor candidate")
    require("--owner-authorized" in text, "launcher must pass owner authorization only after confirmation")
    require("--max-turns 20" in text, "launcher must retain the bounded 20-turn ceiling")
    require("--enable-speech" not in text, "first private live test must remain text-only")
    require("PYTHONDONTWRITEBYTECODE=1" in text, "launcher must avoid local bytecode residue")

    forbidden_fragments = (
        "--api-key",
        "--secret",
        "OPENAI_API_KEY=",
        "QWEN_API_KEY=",
        "DASHSCOPE_API_KEY=",
        "YANDEX_AI_STUDIO_API_KEY=",
        "YANDEX_SPEECHKIT_API_KEY=",
    )
    for fragment in forbidden_fragments:
        require(fragment not in text, f"launcher must not embed/pass provider secret material: {fragment}")

    print("PRIVATE_LIVE_TEST_LAUNCHER=PASS")
    print("LAUNCHER_EXECUTABLE=PASS")
    print("EXACT_CANDIDATE_SHA_BINDING=PASS")
    print("OWNER_CONFIRMATION=PASS")
    print("TEXT_ONLY_FIRST_TEST=PASS")
    print("MAX_SUCCESSFUL_TURNS=20")
    print("PROVIDER_SECRET_VALUES_IN_LAUNCHER=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
