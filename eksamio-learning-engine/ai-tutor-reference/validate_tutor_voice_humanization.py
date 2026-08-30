#!/usr/bin/env python3
from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from private_openai_yandex_resilient_human_ui import base_ui  # noqa: E402
from tutor_boundary import ProviderRequest  # noqa: E402
from tutor_provider_prompt import VERIFICATION_REMINDER, grounded_system_text  # noqa: E402
from yandex_live_adapters import CredentialKind, YandexCredential  # noqa: E402
from yandex_speechkit_v3_tts import (  # noqa: E402
    YandexSpeechKitV3TTS,
    YandexSpeechKitV3TTSConfig,
    _split_text,
    normalize_tutor_text_for_speech,
)


EXAMPLE = (
    "Вы почти правы, но здесь есть важный нюанс. Слово «сочетание» — исключение "
    "в группе корней ЧЕТ-/ЧИТ-: несмотря на наличие буквы «а» после корня, пишется «е». "
    "Попробуйте ещё раз: восстановите букву и запишите слово целиком — соч..тать."
)

RHYTHM_EXAMPLE = (
    "Обычно перед «а» пишется «и», но в словах «сочетать», «сочетание» сохраняется «е»."
)

PROSODY_CASES = (
    ("Сначала найдите корень. Затем проверьте исключение.", ". sil<[260]> Затем"),
    ("Правило такое: если после корня есть а, обычно пишется и.", ": <[small]> если"),
    ("Сравните два случая; затем сформулируйте вывод.", "; <[medium]> затем"),
    ("Ответ верный, однако объяснение неполное.", ", <[small]> однако"),
    ("Ответ почти верный, но правило применено слишком широко.", ", <[small]> но"),
)


class CaptureTTS:
    def __init__(self) -> None:
        self.bodies: list[Mapping[str, object]] = []

    def post_json_stream(self, **kwargs: Any) -> Sequence[Mapping[str, object]]:
        self.bodies.append(dict(kwargs["body"]))
        encoded = base64.b64encode(b"ID3-humanized").decode("ascii")
        return ({"audioChunk": {"data": encoded}},)


class HistoryEntry:
    def __init__(self, role: str, text: str) -> None:
        self.role = role
        self.text = text


def _request(history: tuple[HistoryEntry, ...] = ()) -> ProviderRequest:
    return ProviderRequest(
        contract_version="test",
        correlation_ref="turn:test",
        subject_id="russian",
        learning_goal="understand:test",
        policy_instruction="Stay in the current learning task.",
        verified_source_refs=("source:test",),
        verified_excerpts=("Проверенный контекст",),
        peis_learning_summary="test",
        target_refs=("test",),
        history=history,  # type: ignore[arg-type]
        learner_text="test",
        allowed_tool_names=(),
    )


def main() -> int:
    spoken = normalize_tutor_text_for_speech(EXAMPLE)
    assert "*" not in spoken
    assert "`" not in spoken
    assert "/" not in spoken
    assert "[[t͡ɕ ɛ t]] или [[t͡ɕ i t]]" in spoken
    assert "буквы а sil<[180]> после" in spoken
    assert ". sil<[260]> Слово" in spoken
    assert ". sil<[260]> Попробуйте" in spoken
    assert "сочетание" in spoken
    assert EXAMPLE.startswith("Вы почти правы")  # visible text is untouched

    rhythm = normalize_tutor_text_for_speech(RHYTHM_EXAMPLE)
    # Human-listening target: never pause before the named letter. The first
    # semantic pause belongs after the completed clause "пишется и".
    assert "перед а пишется и, <[small]> но" in rhythm
    # The examples form one spoken group, followed by a small pause before the
    # conclusion "сохраняется е".
    assert "в словах сочетать, сочетание <[small]> сохраняется е" in rhythm
    assert "перед <[" not in rhythm
    assert "перед sil<[" not in rhythm

    for source, marker in PROSODY_CASES:
        rendered = normalize_tutor_text_for_speech(source)
        assert marker in rendered, (source, rendered, marker)

    # Markdown and school notation are visual-only and must never leak to speech.
    markdown = normalize_tutor_text_for_speech(
        "В корнях *‑чет‑*/*‑чит‑* пишется **е**. Подробнее: https://example.invalid/rule"
    )
    assert "*" not in markdown and "/" not in markdown and "http" not in markdown
    assert "[[t͡ɕ ɛ t]] или [[t͡ɕ i t]]" in markdown

    transport = CaptureTTS()
    tts = YandexSpeechKitV3TTS(
        config=YandexSpeechKitV3TTSConfig(
            credential=YandexCredential(CredentialKind.API_KEY, lambda: "fixture-secret"),
            execution_enabled=True,
        ),
        transport=transport,
    )
    audio = tts.synthesize(RHYTHM_EXAMPLE, session_ref="tutor:humanization")
    assert audio
    sent = " ".join(str(body["text"]) for body in transport.bodies)
    assert "перед а пишется и, <[small]> но" in sent
    assert "сочетать, сочетание <[small]> сохраняется е" in sent
    assert all(len(str(body["text"])) <= 240 for body in transport.bodies)

    long_text = normalize_tutor_text_for_speech("Первая законченная фраза. " * 20)
    chunks = _split_text(long_text, 240)
    assert chunks and all(len(chunk) <= 240 for chunk in chunks)
    # TTS markup must remain attached to its phrase, never become a chunk by itself.
    assert all(not chunk.startswith(("sil<[", "<[")) for chunk in chunks)

    page = base_ui.PAGE
    assert "function stopTutorPlayback()" in page
    assert "a.autoplay=false" in page
    assert "setTimeout(r,180)" in page
    assert "Tutor говорит…" in page
    assert "$('#mic').disabled=true" in page

    first_prompt = grounded_system_text(_request()).lower()
    assert "не добавляй шаблонную фразу" in first_prompt
    assert "не более одного раза за всю сессию" in first_prompt
    assert "естественным русским учебным языком" in first_prompt
    assert "логичная пунктуация" in first_prompt
    repeated_prompt = grounded_system_text(
        _request((HistoryEntry("tutor", f"{VERIFICATION_REMINDER}."),))
    ).lower()
    assert "больше её не повторяй" in repeated_prompt

    print("RUSSIAN_PEDAGOGICAL_PROSODY=PASS")
    print("TUTOR_TTS_MARKDOWN_NORMALIZATION=PASS")
    print("TUTOR_TTS_ROOT_CHET_PHONEME=PASS")
    print("TUTOR_TTS_NO_PAUSE_BEFORE_NAMED_LETTER=PASS")
    print("TUTOR_TTS_CONTRASTIVE_CLAUSE_PAUSE=PASS")
    print("TUTOR_TTS_EXAMPLE_GROUP_PAUSE=PASS")
    print("TUTOR_TTS_SENTENCE_PAUSE=PASS")
    print("TUTOR_TTS_COLON_PAUSE=PASS")
    print("TUTOR_TTS_SEMICOLON_PAUSE=PASS")
    print("TUTOR_TTS_COMPLETE_PHRASE_CHUNKING=PASS")
    print("TUTOR_VERIFICATION_REMINDER_MAX_ONCE=PASS")
    print("TUTOR_VOICE_HALF_DUPLEX=PASS")
    print("PREVIOUS_TUTOR_AUDIO_AUTOPLAY_ON_MIC=BLOCKED")
    print("VISIBLE_TUTOR_TEXT_MUTATED=0")
    print("LIVE_PROVIDER_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
