#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(HERE))

from private_openai_yandex_121_tutor import assemble_fast_tutor, open_benchmark_session  # noqa: E402
from private_openai_voice_no_folder_ui import OpenAIVoiceConfig  # noqa: E402
from validate_private_openai_yandex_121_tutor import FakeSTT, FakeV3TTS, ScriptedJsonTransport  # noqa: E402


@contextmanager
def no_folder_credentials():
    names = ("OPENAI_API_KEY", "YANDEX_SPEECHKIT_API_KEY", "YANDEX_FOLDER_ID")
    old = {name: os.environ.get(name) for name in names}
    os.environ["OPENAI_API_KEY"] = "fixture-openai-secret"
    os.environ["YANDEX_SPEECHKIT_API_KEY"] = "fixture-yandex-speech-secret"
    os.environ.pop("YANDEX_FOLDER_ID", None)
    try:
        yield
    finally:
        for name, value in old.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def main() -> int:
    with no_folder_credentials():
        openai = ScriptedJsonTransport({"output_text": "OPENAI_VOICE_NO_FOLDER_OK"})
        stt = FakeSTT(transcript="Объясни слово сочетание")
        tts = FakeV3TTS()
        config = OpenAIVoiceConfig(
            brain_mode="openai",
            yandex_folder_id=None,
            owner_live_authorized=True,
            text_execution_enabled=True,
            speech_execution_enabled=True,
        )
        assert config.resolved_yandex_folder_id is None
        assembly = assemble_fast_tutor(
            engine_root=ENGINE,
            config=config,
            openai_transport=openai,
            stt_transport=stt,
            tts_v3_transport=tts,
        )
        state = open_benchmark_session(assembly, "learner-openai-voice-no-folder")
        result = assembly.tutor.voice_turn(state.session_ref, b"transient-pcm")
        assert "OPENAI_VOICE_NO_FOLDER_OK" in result.tutor_text
        assert result.asr_provider_id == "yandex-speechkit"
        assert result.tts_provider_id == "yandex-speechkit"
        assert openai.calls == 1
        assert assembly.speech_provider.raw_audio_persistence_count() == 0

    print("OPENAI_VOICE_WITHOUT_YANDEX_FOLDER=PASS")
    print("OPENAI_BRAIN=gpt-5.6-sol")
    print("SPEECHKIT_API_KEY_PATH=PASS")
    print("YANDEX_FOLDER_ID_REQUIRED=0")
    print("RAW_AUDIO_PERSISTED_BYTES=0")
    print("LIVE_PROVIDER_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
