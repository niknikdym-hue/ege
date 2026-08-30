#!/usr/bin/env python3
"""Static acceptance for exact-build binding of all real provider launchers."""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = HERE / "private_tutor_runtime_gate.zsh"
LIVE_LAUNCHERS = (
    "launch_brain_provider_smoke.command",
    "launch_four_brain_text_test.command",
    "launch_four_brain_voice_test.command",
    "launch_four_brain_failover_test.command",
    "launch_four_brain_blind_text_test.command",
    "launch_four_brain_blind_voice_test.command",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


def main() -> int:
    gate = GATE.read_text(encoding="utf-8")
    require("git -C \"$SCRIPT_DIR\" rev-parse --show-toplevel" in gate, "runtime gate requires a Git checkout")
    require("git -C \"$REPO_ROOT\" diff --quiet" in gate, "runtime gate rejects dirty tracked worktree")
    require("git -C \"$REPO_ROOT\" diff --cached --quiet" in gate, "runtime gate rejects staged uncommitted changes")
    require("rev-parse --verify HEAD" in gate, "runtime gate binds the exact HEAD")
    require("export EKSAMIO_TUTOR_CANDIDATE_SHA" in gate, "runtime gate exports exact candidate SHA to test process")
    require("OPENAI_API_KEY" not in gate and "QWEN_API_KEY" not in gate and "DEEPSEEK_API_KEY" not in gate, "runtime gate never handles provider secrets")

    for filename in LIVE_LAUNCHERS:
        text = (HERE / filename).read_text(encoding="utf-8")
        require('source "$SCRIPT_DIR/private_tutor_runtime_gate.zsh"' in text, f"{filename} requires exact-build runtime gate")
        require(text.index("private_tutor_runtime_gate.zsh") < text.index("--owner-authorized"), f"{filename} binds build before granting live provider execution")

    print("PRIVATE_TUTOR_RUNTIME_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
