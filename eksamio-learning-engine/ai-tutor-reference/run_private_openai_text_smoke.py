#!/usr/bin/env python3
"""Owner-gated live OpenAI text smoke for the accepted-semantic Russian Tutor.

This script never accepts or prints an API key. It auto-resolves the existing
credential through ``OpenAISecretProvider``. Public traffic and SpeechKit remain
OFF in this smoke. Running it incurs a bounded real OpenAI API request.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(HERE))

from private_staging_openai_yandex_tutor import (  # noqa: E402
    PrivateOpenAIYandexTutorConfig,
    assemble_private_openai_yandex_tutor,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-authorized", action="store_true")
    parser.add_argument("--semantic-id", default="ru-ege-essay-author-position")
    parser.add_argument(
        "--learner-text",
        default="Объясни эту тему коротко и задай мне один проверочный вопрос.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("EKSAMIO_OPENAI_TUTOR_MODEL", "gpt-5.6-terra"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.owner_authorized:
        print("PRIVATE_OPENAI_TEXT_SMOKE=BLOCKED_OWNER_AUTHORIZATION")
        return 2

    config = PrivateOpenAIYandexTutorConfig(
        yandex_voice="text-smoke-inert",
        openai_model=args.model,
        private_staging=True,
        public_traffic_enabled=False,
        owner_live_authorized=True,
        text_execution_enabled=True,
        speech_execution_enabled=False,
    )
    assembly = assemble_private_openai_yandex_tutor(engine_root=ENGINE, config=config)
    state = assembly.tutor.open_semantic_session(
        learner_profile_id="learner:private-openai-smoke",
        semantic_id=args.semantic_id,
    )
    interaction = assembly.tutor.text_turn(state.session_ref, args.learner_text)

    print("PRIVATE_OPENAI_TEXT_SMOKE=PASS")
    print(f"MODEL={args.model}")
    print(f"SEMANTIC_ID={args.semantic_id}")
    print("PUBLIC_TRAFFIC=OFF")
    print("SPEECH_EXECUTION=OFF")
    print("LEARNER_AUDIO_PERSISTED_BYTES=0")
    print("TUTOR_RESPONSE_BEGIN")
    print(interaction.tutor_text)
    print("TUTOR_RESPONSE_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
