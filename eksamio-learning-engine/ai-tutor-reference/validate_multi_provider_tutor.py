#!/usr/bin/env python3
"""Offline acceptance validator for OpenAI -> Qwen -> Yandex Tutor routing."""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(HERE))

from private_staging_multi_provider_tutor import (  # noqa: E402
    PrivateMultiProviderTutorConfig,
    assemble_private_multi_provider_tutor,
)
from sep1_russian_tutor import TutorSliceError  # noqa: E402


SEMANTIC_ID = "ru-ege-essay-author-position"
QWEN_BASE = "https://test-workspace.us-east-1.maas.aliyuncs.com/compatible-mode/v1"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


@contextmanager
def fake_credentials():
    names = {
        "OPENAI_API_KEY": "test-openai-secret",
        "QWEN_API_KEY": "test-qwen-secret",
        "YANDEX_AI_STUDIO_API_KEY": "test-yandex-ai-secret",
        "YANDEX_SPEECHKIT_API_KEY": "test-yandex-speech-secret",
    }
    old = {name: os.environ.get(name) for name in names}
    os.environ.update(names)
    try:
        yield
    finally:
        for name, value in old.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


class ScriptedJsonTransport:
    def __init__(self, outcomes: list[Any]) -> None:
        self.outcomes = list(outcomes)
        self.calls = 0
        self.requests: list[dict[str, Any]] = []

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, Any],
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        self.calls += 1
        self.requests.append({"url": url, "headers": dict(headers), "body": dict(body)})
        if not self.outcomes:
            raise AssertionError("unexpected JSON provider call")
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class FakeSTT:
    def __init__(self, *, transcript: str = "Объясни правило ещё раз.", fail: bool = False) -> None:
        self.transcript = transcript
        self.fail = fail
        self.calls = 0

    def post_binary(self, **kwargs: Any) -> Mapping[str, Any]:
        self.calls += 1
        if self.fail:
            raise TimeoutError("fixture STT timeout")
        return {"result": self.transcript}


class FakeTTS:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def post_form_bytes(self, **kwargs: Any) -> bytes:
        self.calls += 1
        if self.fail:
            raise TimeoutError("fixture TTS timeout")
        return b"OggS-fake-yandex-speechkit-audio"


def config(mode: str, *, speech: bool = False) -> PrivateMultiProviderTutorConfig:
    return PrivateMultiProviderTutorConfig(
        yandex_voice="fixture-voice",
        text_provider_mode=mode,  # type: ignore[arg-type]
        qwen_base_url=QWEN_BASE,
        yandex_folder_id="fixture-folder",
        owner_live_authorized=True,
        text_execution_enabled=True,
        speech_execution_enabled=speech,
    )


def open_session(assembly, suffix: str):
    state = assembly.tutor.open_semantic_session(
        learner_profile_id=f"learner-{suffix}",
        semantic_id=SEMANTIC_ID,
    )
    return state.session_ref


def openai_success(text: str) -> Mapping[str, Any]:
    return {"output_text": text}


def chat_success(text: str) -> Mapping[str, Any]:
    return {"choices": [{"message": {"content": text}}]}


def forced_provider_checks() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    captured: dict[str, dict[str, Any]] = {}
    with fake_credentials():
        openai = ScriptedJsonTransport([openai_success("OPENAI_OK")])
        assembly = assemble_private_multi_provider_tutor(
            engine_root=ENGINE,
            config=config("openai"),
            openai_transport=openai,
        )
        result = assembly.tutor.text_turn(open_session(assembly, "openai"), "Объясни тему кратко.")
        require("OPENAI_OK" in result.tutor_text and openai.calls == 1, "forced OpenAI Tutor route works")
        captured["openai"] = openai.requests[0]

        qwen = ScriptedJsonTransport([chat_success("QWEN_OK")])
        assembly = assemble_private_multi_provider_tutor(
            engine_root=ENGINE,
            config=config("qwen"),
            qwen_transport=qwen,
        )
        result = assembly.tutor.text_turn(open_session(assembly, "qwen"), "Объясни тему кратко.")
        require("QWEN_OK" in result.tutor_text and qwen.calls == 1, "forced Qwen Tutor route works")
        captured["qwen"] = qwen.requests[0]

        yandex = ScriptedJsonTransport([chat_success("YANDEX_OK")])
        assembly = assemble_private_multi_provider_tutor(
            engine_root=ENGINE,
            config=config("yandex"),
            yandex_text_transport=yandex,
        )
        result = assembly.tutor.text_turn(open_session(assembly, "yandex"), "Объясни тему кратко.")
        require("YANDEX_OK" in result.tutor_text and yandex.calls == 1, "forced Yandex Alice Tutor route works")
        captured["yandex"] = yandex.requests[0]

    return captured["openai"], captured["qwen"], captured["yandex"]


def prompt_parity_check(openai_req: dict[str, Any], qwen_req: dict[str, Any], yandex_req: dict[str, Any]) -> None:
    openai_messages = openai_req["body"]["input"]
    qwen_messages = qwen_req["body"]["messages"]
    yandex_messages = yandex_req["body"]["messages"]
    require(openai_messages == qwen_messages == yandex_messages, "all three brains receive identical grounded messages/history")
    serialized = repr(openai_messages)
    require("Проверенный контекст" in serialized and "Не выдумывай" in serialized, "shared provider prompt preserves Eksamio grounding guard")


def failover_checks() -> None:
    with fake_credentials():
        openai = ScriptedJsonTransport([RuntimeError("provider HTTP error 429")])
        qwen = ScriptedJsonTransport([chat_success("QWEN_FALLBACK_OK")])
        yandex = ScriptedJsonTransport([chat_success("YANDEX_SHOULD_NOT_RUN")])
        assembly = assemble_private_multi_provider_tutor(
            engine_root=ENGINE,
            config=config("auto"),
            openai_transport=openai,
            qwen_transport=qwen,
            yandex_text_transport=yandex,
        )
        result = assembly.tutor.text_turn(open_session(assembly, "fallback-qwen"), "Помоги разобраться.")
        require("QWEN_FALLBACK_OK" in result.tutor_text, "OpenAI rate limit falls through to Qwen")
        require(openai.calls == 1 and qwen.calls == 1 and yandex.calls == 0, "rate-limited OpenAI is not blindly retried")
        require(result.reliable_result.learner_quota_debit_count == 1, "fallback turn debits learner quota exactly once")

        openai = ScriptedJsonTransport([PermissionError("fixture rejected")])
        qwen = ScriptedJsonTransport([RuntimeError("provider HTTP error 500"), RuntimeError("provider HTTP error 500")])
        yandex = ScriptedJsonTransport([chat_success("YANDEX_FALLBACK_OK")])
        assembly = assemble_private_multi_provider_tutor(
            engine_root=ENGINE,
            config=config("auto"),
            openai_transport=openai,
            qwen_transport=qwen,
            yandex_text_transport=yandex,
        )
        result = assembly.tutor.text_turn(open_session(assembly, "fallback-yandex"), "Продолжим урок.")
        require("YANDEX_FALLBACK_OK" in result.tutor_text, "OpenAI credential failure plus Qwen outage falls through to Yandex")
        require(openai.calls == 1 and qwen.calls == 2 and yandex.calls == 1, "bounded provider attempts preserve third-provider availability")
        require(result.reliable_result.learner_quota_debit_count == 1, "third-provider fallback still debits once")


def voice_checks() -> None:
    with fake_credentials():
        openai = ScriptedJsonTransport([openai_success("VOICE_TEXT_OK")])
        stt = FakeSTT()
        tts = FakeTTS()
        assembly = assemble_private_multi_provider_tutor(
            engine_root=ENGINE,
            config=config("openai", speech=True),
            openai_transport=openai,
            stt_transport=stt,
            tts_transport=tts,
        )
        result = assembly.tutor.voice_turn(open_session(assembly, "voice-ok"), b"fake-transient-pcm")
        require(result.audio is not None and result.tts_provider_id == "yandex-speechkit", "voice Tutor uses Yandex SpeechKit TTS")
        require(result.asr_provider_id == "yandex-speechkit" and result.modality == "voice", "voice Tutor uses Yandex SpeechKit STT")

        openai = ScriptedJsonTransport([openai_success("TEXT_SURVIVES_TTS")])
        assembly = assemble_private_multi_provider_tutor(
            engine_root=ENGINE,
            config=config("openai", speech=True),
            openai_transport=openai,
            stt_transport=FakeSTT(),
            tts_transport=FakeTTS(fail=True),
        )
        result = assembly.tutor.voice_turn(open_session(assembly, "tts-down"), b"fake-transient-pcm")
        require(result.audio is None and result.modality == "voice-text-fallback", "TTS outage degrades to text instead of losing Tutor answer")
        require("TEXT_SURVIVES_TTS" in result.tutor_text and result.reliable_result.learner_quota_debit_count == 1, "accepted paid text turn is preserved exactly once during TTS outage")

        untouched_llm = ScriptedJsonTransport([openai_success("SHOULD_NOT_RUN")])
        assembly = assemble_private_multi_provider_tutor(
            engine_root=ENGINE,
            config=config("openai", speech=True),
            openai_transport=untouched_llm,
            stt_transport=FakeSTT(fail=True),
            tts_transport=FakeTTS(),
        )
        try:
            assembly.tutor.voice_turn(open_session(assembly, "stt-down"), b"fake-transient-pcm")
        except TutorSliceError:
            pass
        else:
            raise AssertionError("STT failure unexpectedly created a Tutor turn")
        require(untouched_llm.calls == 0, "STT failure causes zero LLM calls and therefore zero paid text turn")


def safety_checks() -> None:
    # Execution OFF must construct without reading any provider credential or requiring live endpoint/folder config.
    assembly = assemble_private_multi_provider_tutor(
        engine_root=ENGINE,
        config=PrivateMultiProviderTutorConfig(yandex_voice="fixture-voice"),
    )
    snapshot = assembly.safety_snapshot()
    require(snapshot["public_traffic_enabled"] is False, "multi-provider test assembly keeps public traffic off")
    require(snapshot["text_provider_order"] == ["openai-responses", "qwen-model-studio", "yandex-alice-ai"], "AUTO priority is OpenAI -> Qwen -> Yandex")
    require(snapshot["tts_provider"] == "yandex-speechkit" and snapshot["stt_provider"] == "yandex-speechkit", "Russian voice path is Yandex SpeechKit only")
    require(snapshot["learner_audio_persisted_bytes"] == 0, "Tutor assembly persists zero learner audio bytes")


def main() -> int:
    safety_checks()
    openai_req, qwen_req, yandex_req = forced_provider_checks()
    prompt_parity_check(openai_req, qwen_req, yandex_req)
    failover_checks()
    voice_checks()
    print("MULTI_PROVIDER_TUTOR_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
