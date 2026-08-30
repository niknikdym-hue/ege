#!/usr/bin/env python3
"""Offline acceptance for OpenAI/Qwen/DeepSeek/Alice Tutor brains."""
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

from private_staging_four_brain_tutor import (  # noqa: E402
    PrivateFourBrainTutorConfig,
    assemble_private_four_brain_tutor,
)

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
        "DEEPSEEK_API_KEY": "test-deepseek-secret",
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

    def post_json(self, *, url: str, headers: Mapping[str, str], body: Mapping[str, Any], timeout_seconds: float) -> Mapping[str, Any]:
        self.calls += 1
        self.requests.append({"url": url, "headers": dict(headers), "body": dict(body)})
        if not self.outcomes:
            raise AssertionError("unexpected provider call")
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class FakeSTT:
    def __init__(self) -> None:
        self.calls = 0

    def post_binary(self, **kwargs: Any) -> Mapping[str, Any]:
        self.calls += 1
        return {"result": "Объясни правило ещё раз."}


class FakeV3TTS:
    def __init__(self) -> None:
        self.calls = 0
        self.requests: list[dict[str, Any]] = []

    def post_json_stream(self, **kwargs: Any) -> Sequence[Mapping[str, object]]:
        self.calls += 1
        self.requests.append({"body": dict(kwargs["body"])})
        data = base64.b64encode(b"ID3-four-brain-fixture").decode("ascii")
        return ({"audioChunk": {"data": data}},)


def config(mode: str, *, speech: bool = False) -> PrivateFourBrainTutorConfig:
    return PrivateFourBrainTutorConfig(
        text_provider_mode=mode,  # type: ignore[arg-type]
        qwen_base_url=QWEN_BASE,
        yandex_folder_id="fixture-folder",
        owner_live_authorized=True,
        text_execution_enabled=True,
        speech_execution_enabled=speech,
    )


def open_session(assembly, suffix: str) -> str:
    state = assembly.tutor.open_semantic_session(
        learner_profile_id=f"learner-{suffix}",
        semantic_id=SEMANTIC_ID,
    )
    return state.session_ref


def openai_success(text: str) -> Mapping[str, Any]:
    return {"output_text": text}


def chat_success(text: str) -> Mapping[str, Any]:
    return {"choices": [{"message": {"content": text}}]}


def assemble(mode: str, *, speech: bool = False, transports: dict[str, ScriptedJsonTransport] | None = None, stt=None, tts=None):
    transports = transports or {}
    return assemble_private_four_brain_tutor(
        engine_root=ENGINE,
        config=config(mode, speech=speech),
        openai_transport=transports.get("openai"),
        qwen_transport=transports.get("qwen"),
        deepseek_transport=transports.get("deepseek"),
        yandex_text_transport=transports.get("yandex"),
        stt_transport=stt,
        tts_v3_transport=tts,
    )


def forced_text_and_prompt_parity() -> None:
    request_bodies: dict[str, Mapping[str, Any]] = {}
    with fake_credentials():
        cases = {
            "openai": (openai_success("OPENAI_OK"), "OPENAI_OK"),
            "qwen": (chat_success("QWEN_OK"), "QWEN_OK"),
            "deepseek": (chat_success("DEEPSEEK_OK"), "DEEPSEEK_OK"),
            "yandex": (chat_success("YANDEX_OK"), "YANDEX_OK"),
        }
        for name, (response, marker) in cases.items():
            transport = ScriptedJsonTransport([response])
            assembly = assemble(name, transports={name: transport})
            result = assembly.tutor.text_turn(open_session(assembly, f"text-{name}"), "Объясни тему кратко.")
            require(marker in result.tutor_text and transport.calls == 1, f"forced {name} text route works")
            request_bodies[name] = transport.requests[0]["body"]

    openai_messages = request_bodies["openai"]["input"]
    require(openai_messages == request_bodies["qwen"]["messages"], "OpenAI and Qwen receive identical grounded messages")
    require(openai_messages == request_bodies["deepseek"]["messages"], "OpenAI and DeepSeek receive identical grounded messages")
    require(openai_messages == request_bodies["yandex"]["messages"], "OpenAI and Alice receive identical grounded messages")
    require(request_bodies["deepseek"]["model"] == "deepseek-v4-pro", "DeepSeek test uses V4 Pro")
    require(request_bodies["deepseek"]["thinking"] == {"type": "enabled"}, "DeepSeek quality test explicitly enables thinking")
    require(request_bodies["deepseek"]["reasoning_effort"] == "high", "DeepSeek quality test uses high reasoning effort")


def failover_checks() -> None:
    with fake_credentials():
        openai = ScriptedJsonTransport([PermissionError("fixture credential unavailable")])
        qwen = ScriptedJsonTransport([RuntimeError("provider HTTP error 500"), RuntimeError("provider HTTP error 500")])
        deepseek = ScriptedJsonTransport([chat_success("DEEPSEEK_FALLBACK_OK")])
        yandex = ScriptedJsonTransport([chat_success("YANDEX_SHOULD_NOT_RUN")])
        assembly = assemble(
            "auto",
            transports={"openai": openai, "qwen": qwen, "deepseek": deepseek, "yandex": yandex},
        )
        result = assembly.tutor.text_turn(open_session(assembly, "fallback-deepseek"), "Продолжим урок.")
        require("DEEPSEEK_FALLBACK_OK" in result.tutor_text, "OpenAI/Qwen outage falls through to DeepSeek")
        require(openai.calls == 1 and qwen.calls == 2 and deepseek.calls == 1 and yandex.calls == 0, "DeepSeek accepts before Alice is attempted")
        require(result.reliable_result.learner_quota_debit_count == 1, "DeepSeek fallback debits learner quota exactly once")

        openai = ScriptedJsonTransport([PermissionError("fixture rejected")])
        qwen = ScriptedJsonTransport([RuntimeError("provider HTTP error 429")])
        deepseek = ScriptedJsonTransport([RuntimeError("provider HTTP error 429")])
        yandex = ScriptedJsonTransport([chat_success("ALICE_LAST_RESORT_OK")])
        assembly = assemble(
            "auto",
            transports={"openai": openai, "qwen": qwen, "deepseek": deepseek, "yandex": yandex},
        )
        result = assembly.tutor.text_turn(open_session(assembly, "fallback-alice"), "Не прерывай урок.")
        require("ALICE_LAST_RESORT_OK" in result.tutor_text, "four-brain route retains Alice as last technical fallback")
        require(openai.calls == 1 and qwen.calls == 1 and deepseek.calls == 1 and yandex.calls == 1, "rate limits fall through without blind retry")
        require(result.reliable_result.learner_quota_debit_count == 1, "fourth-brain fallback still debits once")


def voice_checks_for_every_brain() -> None:
    with fake_credentials():
        responses = {
            "openai": openai_success("VOICE_OPENAI_OK"),
            "qwen": chat_success("VOICE_QWEN_OK"),
            "deepseek": chat_success("VOICE_DEEPSEEK_OK"),
            "yandex": chat_success("VOICE_YANDEX_OK"),
        }
        for name, response in responses.items():
            llm = ScriptedJsonTransport([response])
            stt = FakeSTT()
            tts = FakeV3TTS()
            assembly = assemble(name, speech=True, transports={name: llm}, stt=stt, tts=tts)
            result = assembly.tutor.voice_turn(open_session(assembly, f"voice-{name}"), b"fake-transient-pcm")
            require(result.audio is not None, f"{name} brain completes a voice Tutor turn")
            require(result.asr_provider_id == "yandex-speechkit", f"{name} voice input uses Yandex SpeechKit STT")
            require(result.tts_provider_id == "yandex-speechkit", f"{name} voice output uses Yandex SpeechKit Lera TTS")
            require(llm.calls == 1 and stt.calls == 1 and tts.calls == 1, f"{name} voice turn calls STT/brain/TTS exactly once")
            hints = tts.requests[0]["body"]["hints"]
            require({"voice": "lera"} in hints and {"role": "neutral"} in hints and {"speed": "1.04"} in hints, f"{name} voice response keeps Lera profile")


def safety_checks() -> None:
    assembly = assemble_private_four_brain_tutor(
        engine_root=ENGINE,
        config=PrivateFourBrainTutorConfig(),
    )
    snapshot = assembly.safety_snapshot()
    require(snapshot["public_traffic_enabled"] is False, "four-brain test keeps public traffic off")
    require(snapshot["text_provider_order"] == ["openai-responses", "qwen-model-studio", "deepseek-api", "yandex-alice-ai"], "provisional AUTO route includes DeepSeek before Alice")
    require(snapshot["auto_order_is_provisional"] is True, "AUTO order cannot be mistaken for final human ranking")
    require(snapshot["stt_provider"] == "yandex-speechkit" and snapshot["tts_provider"] == "yandex-speechkit", "all brains share Yandex SpeechKit voice")
    require(snapshot["tts_voice"] == "lera" and snapshot["tts_role"] == "neutral" and snapshot["tts_speed"] == 1.04, "voice profile remains Lera / neutral / 1.04")
    require(snapshot["learner_audio_persisted_bytes"] == 0, "four-brain assembly persists zero learner audio")


def main() -> int:
    safety_checks()
    forced_text_and_prompt_parity()
    failover_checks()
    voice_checks_for_every_brain()
    print("FOUR_BRAIN_TUTOR_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
