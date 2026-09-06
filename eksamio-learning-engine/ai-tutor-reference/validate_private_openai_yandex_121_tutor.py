#!/usr/bin/env python3
from __future__ import annotations

import base64
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(HERE))

from private_openai_yandex_121_tutor import (  # noqa: E402
    BENCHMARK_CARD_ID,
    BENCHMARK_SEMANTIC_ID,
    FastTutorConfig,
    assemble_fast_tutor,
    open_benchmark_session,
)
from sep1_russian_tutor import TutorSliceError  # noqa: E402


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)
    print(f"PASS: {message}")


@contextmanager
def fake_credentials():
    values = {
        "OPENAI_API_KEY": "fixture-openai-secret",
        "YANDEX_AI_STUDIO_API_KEY": "fixture-yandex-ai-secret",
        "YANDEX_SPEECHKIT_API_KEY": "fixture-yandex-speech-secret",
        "YANDEX_FOLDER_ID": "fixture-folder",
    }
    old = {name: os.environ.get(name) for name in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for name, value in old.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


class ScriptedJsonTransport:
    def __init__(self, response: Mapping[str, Any]) -> None:
        self.response = response
        self.calls = 0
        self.requests: list[dict[str, Any]] = []

    def post_json(self, *, url: str, headers: Mapping[str, str], body: Mapping[str, Any], timeout_seconds: float):
        self.calls += 1
        self.requests.append({"url": url, "headers": dict(headers), "body": dict(body)})
        return self.response


class FakeSTT:
    def __init__(self, transcript: str = "Почему в слове сочетание пишется е?", fail: bool = False) -> None:
        self.transcript = transcript
        self.fail = fail
        self.calls = 0
        self.params: list[dict[str, str]] = []

    def post_binary(self, **kwargs: Any) -> Mapping[str, Any]:
        self.calls += 1
        self.params.append(dict(kwargs.get("params") or {}))
        if self.fail:
            raise TimeoutError("fixture SpeechKit STT failure")
        return {"result": self.transcript}


class FakeV3TTS:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0
        self.requests: list[dict[str, Any]] = []

    def post_json_stream(self, **kwargs: Any) -> Sequence[Mapping[str, object]]:
        self.calls += 1
        self.requests.append({"url": kwargs["url"], "body": dict(kwargs["body"]), "headers": dict(kwargs["headers"])})
        if self.fail:
            raise TimeoutError("fixture SpeechKit TTS failure")
        encoded = base64.b64encode(b"ID3-fast-benchmark-mp3").decode("ascii")
        return ({"audioChunk": {"data": encoded}},)


def cfg(provider: str, *, speech: bool = False) -> FastTutorConfig:
    return FastTutorConfig(
        brain_mode=provider,  # type: ignore[arg-type]
        yandex_folder_id="fixture-folder",
        owner_live_authorized=True,
        text_execution_enabled=True,
        speech_execution_enabled=speech,
    )


def session(assembly, suffix: str) -> str:
    state = open_benchmark_session(assembly, f"learner-fast-{suffix}")
    require(state.grounding.card_id == BENCHMARK_CARD_ID, "benchmark uses merged reviewed card")
    require(state.grounding.semantic_id == BENCHMARK_SEMANTIC_ID, "benchmark semantic is exact merged school semantic")
    require(state.grounding.mapping_resolution == "EXACT", "benchmark mapping remains EXACT")
    return state.session_ref


def forced_prompt_parity() -> None:
    with fake_credentials():
        openai_transport = ScriptedJsonTransport({"output_text": "OPENAI_OK"})
        openai = assemble_fast_tutor(
            engine_root=ENGINE,
            config=cfg("openai"),
            openai_transport=openai_transport,
        )
        out = openai.tutor.text_turn(session(openai, "openai"), "Не давай ответ сразу, помоги понять правило.")
        require("OPENAI_OK" in out.tutor_text and openai_transport.calls == 1, "forced OpenAI route works")
        require(openai.safety_snapshot()["exact_brain_model"] == "gpt-5.6-sol", "OpenAI human benchmark model is gpt-5.6-sol")

        yandex_transport = ScriptedJsonTransport({"choices": [{"message": {"content": "YANDEX_OK"}}]})
        yandex = assemble_fast_tutor(
            engine_root=ENGINE,
            config=cfg("yandex"),
            yandex_text_transport=yandex_transport,
        )
        out = yandex.tutor.text_turn(session(yandex, "yandex"), "Не давай ответ сразу, помоги понять правило.")
        require("YANDEX_OK" in out.tutor_text and yandex_transport.calls == 1, "forced Yandex Alice route works")
        require("/aliceai-llm/latest" in str(yandex.safety_snapshot()["exact_brain_model"]), "Yandex human benchmark uses full-size Alice AI LLM URI")

        openai_messages = openai_transport.requests[0]["body"]["input"]
        yandex_messages = yandex_transport.requests[0]["body"]["messages"]
        require(openai_messages == yandex_messages, "OpenAI and Yandex receive identical grounded prompt/history")
        serialized = repr(openai_messages)
        require("Проверенный контекст" in serialized and "Не выдумывай" in serialized, "provider prompt preserves Eksamio source-truth guard")


def voice_parity_and_failure_guards() -> None:
    with fake_credentials():
        for provider in ("openai", "yandex"):
            text_transport = ScriptedJsonTransport(
                {"output_text": f"{provider.upper()}_VOICE_OK"}
                if provider == "openai"
                else {"choices": [{"message": {"content": "YANDEX_VOICE_OK"}}]}
            )
            stt = FakeSTT()
            tts = FakeV3TTS()
            kwargs = {"openai_transport": text_transport} if provider == "openai" else {"yandex_text_transport": text_transport}
            assembly = assemble_fast_tutor(
                engine_root=ENGINE,
                config=cfg(provider, speech=True),
                stt_transport=stt,
                tts_v3_transport=tts,
                **kwargs,
            )
            result = assembly.tutor.voice_turn(session(assembly, f"voice-{provider}"), b"fixture-transient-lpcm")
            require(result.asr_provider_id == "yandex-speechkit", f"{provider} voice run uses Yandex STT")
            require(result.tts_provider_id == "yandex-speechkit" and isinstance(result.audio, bytes), f"{provider} voice run uses Yandex Lera TTS")
            require(stt.params[0].get("format") == "lpcm" and stt.params[0].get("sampleRateHertz") == "16000", f"{provider} fast voice benchmark uses bounded LPCM 16k STT")
            hints = tts.requests[0]["body"]["hints"]
            require({"voice": "lera"} in hints and {"role": "neutral"} in hints and {"speed": "1.04"} in hints, f"{provider} voice output is Lera neutral 1.04")
            require(assembly.speech_provider.raw_audio_persistence_count() == 0, f"{provider} speech provider retains zero learner audio bytes")

        untouched = ScriptedJsonTransport({"output_text": "MUST_NOT_RUN"})
        broken = assemble_fast_tutor(
            engine_root=ENGINE,
            config=cfg("openai", speech=True),
            openai_transport=untouched,
            stt_transport=FakeSTT(fail=True),
            tts_v3_transport=FakeV3TTS(),
        )
        try:
            broken.tutor.voice_turn(session(broken, "stt-failure"), b"fixture-transient-lpcm")
        except TutorSliceError:
            pass
        else:
            raise AssertionError("STT failure unexpectedly created Tutor turn")
        require(untouched.calls == 0, "STT failure creates zero LLM calls")

        text_transport = ScriptedJsonTransport({"output_text": "TEXT_SURVIVES_TTS"})
        tts_down = assemble_fast_tutor(
            engine_root=ENGINE,
            config=cfg("openai", speech=True),
            openai_transport=text_transport,
            stt_transport=FakeSTT(),
            tts_v3_transport=FakeV3TTS(fail=True),
        )
        result = tts_down.tutor.voice_turn(session(tts_down, "tts-failure"), b"fixture-transient-lpcm")
        require(result.modality == "voice-text-fallback" and result.audio is None, "TTS failure preserves accepted text answer")
        require(text_transport.calls == 1 and result.reliable_result.learner_quota_debit_count == 1, "TTS failure does not trigger second LLM request/quota debit")


def safety_contract() -> None:
    for provider in ("openai", "yandex"):
        assembly = assemble_fast_tutor(engine_root=ENGINE, config=FastTutorConfig(brain_mode=provider))  # type: ignore[arg-type]
        snapshot = assembly.safety_snapshot()
        require(snapshot["public_traffic_enabled"] is False, f"{provider} public traffic stays off")
        require(snapshot["production_peis_writes_enabled"] is False, f"{provider} production PEIS writes stay off")
        require(snapshot["learner_audio_persisted_bytes"] == 0, f"{provider} learner audio persistence contract is zero")
        require(snapshot["benchmark_stt_contract"] == "speechkit-v1-bounded-rest", f"{provider} fast benchmark STT is explicitly not mislabeled as production streaming")
        require(snapshot["production_stt_target"] == "speechkit-v3-grpc-streaming", f"{provider} production STT target remains v3 streaming")


def main() -> int:
    safety_contract()
    forced_prompt_parity()
    voice_parity_and_failure_guards()
    print("FAST_OPENAI_YANDEX_121_TUTOR=PASS")
    print("BRAIN_PROVIDERS=openai,yandex")
    print(f"BENCHMARK_CARD={BENCHMARK_CARD_ID}")
    print(f"BENCHMARK_SEMANTIC={BENCHMARK_SEMANTIC_ID}")
    print("PROMPT_PARITY=PASS")
    print("FORCED_PROVIDER_ROUTING=PASS")
    print("Yandex_SHARED_VOICE=PASS")
    print("RAW_AUDIO_PERSISTED_BYTES=0")
    print("LIVE_PROVIDER_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
