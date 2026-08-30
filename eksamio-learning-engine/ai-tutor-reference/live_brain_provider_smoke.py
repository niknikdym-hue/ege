#!/usr/bin/env python3
"""One-turn owner-gated live smoke for Qwen, DeepSeek and Alice AI brains.

No learner data is used. Provider response text is never printed or persisted.
This is infrastructure readiness, not pedagogical acceptance.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(HERE))

from private_provider_config import load_private_provider_config  # noqa: E402
from private_staging_four_brain_tutor import (  # noqa: E402
    PrivateFourBrainTutorConfig,
    assemble_private_four_brain_tutor,
)

SEMANTIC_ID = "ru-ege-essay-author-position"
SMOKE_MESSAGE = "Коротко подтверди, что готов продолжить учебный диалог по этой теме."
PROVIDERS = ("qwen", "deepseek", "yandex")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-authorized", action="store_true")
    parser.add_argument("--provider", choices=(*PROVIDERS, "all"), default="all")
    return parser.parse_args()


def smoke(provider: str) -> None:
    local = load_private_provider_config()
    config = PrivateFourBrainTutorConfig(
        text_provider_mode=provider,  # type: ignore[arg-type]
        qwen_base_url=local.qwen_base_url,
        yandex_folder_id=local.yandex_folder_id,
        owner_live_authorized=True,
        text_execution_enabled=True,
        speech_execution_enabled=False,
    )
    assembly = assemble_private_four_brain_tutor(engine_root=ENGINE, config=config)
    state = assembly.tutor.open_semantic_session(
        learner_profile_id=f"provider-smoke-{provider}",
        semantic_id=SEMANTIC_ID,
    )
    result = assembly.tutor.text_turn(state.session_ref, SMOKE_MESSAGE)
    if not isinstance(result.tutor_text, str) or not result.tutor_text.strip():
        raise RuntimeError(f"{provider} live smoke returned no Tutor text")
    if result.reliable_result.learner_quota_debit_count != 1:
        raise RuntimeError(f"{provider} live smoke violated exactly-once debit")
    print(f"LIVE_BRAIN_SMOKE_{provider.upper()}=PASS")


def main() -> int:
    args = parse_args()
    if not args.owner_authorized:
        print("LIVE_BRAIN_SMOKE=BLOCKED_OWNER_AUTHORIZATION")
        return 2
    selected = PROVIDERS if args.provider == "all" else (args.provider,)
    for provider in selected:
        smoke(provider)
    print(f"LIVE_BRAIN_SMOKE_CALLS={len(selected)}")
    print("PROVIDER_RESPONSE_TEXT_PERSISTED=0")
    print("PERSONAL_LEARNER_DATA_USED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
