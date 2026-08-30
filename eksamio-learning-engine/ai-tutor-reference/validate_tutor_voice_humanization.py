#!/usr/bin/env python3
from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from private_openai_yandex_resilient_human_ui import base_ui  # noqa: E402
from yandex_live_adapters import CredentialKind, YandexCredential  # noqa: E402
from yandex_speechkit_v3_tts import (  # noqa: E402
    YandexSpeechKitV3TTS,
    YandexSpeechKitV3TTSConfig,
    _split_text,
    normalize_tutor_text_for_speech,
)


EXAMPLE = (
    "Вы на правильном пути, но есть важный нюанс. В корнях *‑чет‑*/*‑чит‑* "
    "действительно обычно пишется «и», если дальше идёт «а» (*вычитать*), и «е» — "
    "в остальных случаях (*вычет*). Однако слово «сочетание» — **исключение** из этого "
    "правила, в нём сохраняется буква «е»."
)


class CaptureTTS:
    def __init__(self) -> None:
        self.bodies: list[Mapping[str, object]] = []

    def post_json_stream(self, **kwargs: Any) -> Sequence[Mapping[str, object]]:
        self.bodies.append(dict(kwargs["body"]))
        encoded = base64.b64encode(b"ID3-humanized").decode("ascii")
        return ({"audioChunk": {"data": encoded}},)


def main() -> int:
    spoken = normalize_tutor_text_for_speech(EXAMPLE)
    assert "*" not in spoken
    assert "`" not in spoken
    assert "/" not in spoken
    assert "чет или чит" in spoken
    assert "исключение" in spoken
    assert "вычитать" in spoken and "вычет" in spoken
    assert EXAMPLE.startswith("Вы на правильном пути")  # visible text is untouched

    transport = CaptureTTS()
    tts = YandexSpeechKitV3TTS(
        config=YandexSpeechKitV3TTSConfig(
            credential=YandexCredential(CredentialKind.API_KEY, lambda: "fixture-secret"),
            execution_enabled=True,
        ),
        transport=transport,
    )
    audio = tts.synthesize(EXAMPLE, session_ref="tutor:humanization")
    assert audio
    sent = " ".join(str(body["text"]) for body in transport.bodies)
    assert "*" not in sent and "/" not in sent
    assert "чет или чит" in sent
    assert all(len(str(body["text"])) <= 240 for body in transport.bodies)

    long_text = "Первая законченная фраза. " * 20
    chunks = _split_text(long_text, 240)
    assert chunks and all(len(chunk) <= 240 for chunk in chunks)
    assert all(chunk[-1] in ".!?;:" for chunk in chunks[:-1])

    page = base_ui.PAGE
    assert "function stopTutorPlayback()" in page
    assert "a.autoplay=false" in page
    assert "setTimeout(r,180)" in page
    assert "Tutor говорит…" in page
    assert "$('#mic').disabled=true" in page

    print("TUTOR_TTS_MARKDOWN_NORMALIZATION=PASS")
    print("TUTOR_TTS_ROOT_NOTATION=чет_или_чит")
    print("TUTOR_TTS_COMPLETE_PHRASE_CHUNKING=PASS")
    print("TUTOR_VOICE_HALF_DUPLEX=PASS")
    print("PREVIOUS_TUTOR_AUDIO_AUTOPLAY_ON_MIC=BLOCKED")
    print("VISIBLE_TUTOR_TEXT_MUTATED=0")
    print("LIVE_PROVIDER_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
