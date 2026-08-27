#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Mapping

from reliability_gateway import FailureClass, ProviderAttempt, ProviderFault
from sep1_russian_tutor import MockSpeechProvider, VoiceGateway
from tutor_boundary import ProviderRequest, ProviderResponse, TutorHistoryEntry
from yandex_live_adapters import (
    CredentialKind,
    YandexCredential,
    YandexSpeechConfig,
    YandexSpeechKitProvider,
    YandexTextConfig,
    YandexTextProvider,
)


class FakeJsonTransport:
    def __init__(self) -> None:
        self.calls = 0
        self.last = None
        self.timeout = False

    def post_json(self, *, url, headers, body, timeout_seconds):
        self.calls += 1
        self.last = (url, headers, body, timeout_seconds)
        if self.timeout:
            raise TimeoutError("fixture timeout")
        return {"choices": [{"message": {"content": "Проверенное объяснение по контексту."}}]}


class FakeBinaryTransport:
    def __init__(self) -> None:
        self.calls = 0
        self.last = None

    def post_binary(self, *, url, headers, params, body, timeout_seconds):
        self.calls += 1
        self.last = (url, headers, params, len(body), timeout_seconds)
        return {"result": "сочетание"}


class FakeFormBytesTransport:
    def __init__(self) -> None:
        self.calls = 0
        self.last = None

    def post_form_bytes(self, *, url, headers, fields, timeout_seconds):
        self.calls += 1
        self.last = (url, headers, fields, timeout_seconds)
        return b"OGG_FIXTURE_AUDIO"


def request() -> ProviderRequest:
    return ProviderRequest(
        contract_version="eksamio.tutor.provider-request.v1",
        correlation_ref="turn:fixture",
        subject_id="russian",
        learning_goal="Проверить написание сочетания",
        policy_instruction="Give advisory tutoring text; never claim canonical learning-state authority.",
        verified_source_refs=("source:russian-reviewed-card:ex-practice-alt-sochetat-001",),
        verified_excerpts=("Проверенный ответ: сочетание\nПроверенное объяснение: правило проверено.",),
        peis_learning_summary="нужна самостоятельная проверка",
        target_refs=("school-i-e-alternating-verb-roots-stressed-a",),
        history=(TutorHistoryEntry(role="learner", text="Не уверен в букве."),),
        learner_text="Объясни, как проверить.",
        allowed_tool_names=(),
    )


def attempt() -> ProviderAttempt:
    return ProviderAttempt(
        provider_attempt_id="attempt:yandex:1",
        episode_id="episode:fixture",
        turn_id="turn:fixture",
        provider_id="yandex-ai-studio",
        capability="TEXT_TUTOR",
        retry_index=0,
    )


def main() -> int:
    api_secret = "YANDEX_API_KEY_FIXTURE_MUST_NOT_LEAK"
    iam_secret = "YANDEX_IAM_FIXTURE_MUST_NOT_LEAK"

    json_transport = FakeJsonTransport()
    api_credential = YandexCredential(CredentialKind.API_KEY, lambda: api_secret)
    text_off = YandexTextProvider(
        config=YandexTextConfig(
            credential=api_credential,
            model_uri="gpt://folder-fixture/yandexgpt/latest",
            execution_enabled=False,
        ),
        transport=json_transport,
    )
    off = text_off.generate(request(), attempt())
    assert isinstance(off, ProviderFault)
    assert json_transport.calls == 0

    text_on = YandexTextProvider(
        config=YandexTextConfig(
            credential=api_credential,
            model_uri="gpt://folder-fixture/yandexgpt/latest",
            execution_enabled=True,
        ),
        transport=json_transport,
    )
    result = text_on.generate(request(), attempt())
    assert isinstance(result, ProviderResponse)
    assert result.source_refs == request().verified_source_refs
    assert result.text == "Проверенное объяснение по контексту."
    assert json_transport.last is not None
    text_url, text_headers, text_body, text_timeout = json_transport.last
    assert text_url == "https://ai.api.cloud.yandex.net/v1/chat/completions"
    assert text_headers["Authorization"] == f"Api-Key {api_secret}"
    assert text_body["model"] == "gpt://folder-fixture/yandexgpt/latest"
    system_content = text_body["messages"][0]["content"]
    assert request().verified_source_refs[0] in system_content
    assert request().verified_excerpts[0] in system_content
    assert text_timeout <= 60

    json_transport.timeout = True
    timeout_result = text_on.generate(request(), attempt())
    assert isinstance(timeout_result, ProviderFault)
    assert timeout_result.failure_class is FailureClass.TIMEOUT
    json_transport.timeout = False

    ungrounded = ProviderRequest(
        contract_version=request().contract_version,
        correlation_ref=request().correlation_ref,
        subject_id="russian",
        learning_goal="fixture",
        policy_instruction=request().policy_instruction,
        verified_source_refs=(),
        verified_excerpts=(),
        peis_learning_summary="fixture",
        target_refs=(),
        history=(),
        learner_text="fixture",
        allowed_tool_names=(),
    )
    before = json_transport.calls
    invalid = text_on.generate(ungrounded, attempt())
    assert isinstance(invalid, ProviderFault)
    assert invalid.failure_class is FailureClass.INVALID_PLATFORM_REQUEST
    assert json_transport.calls == before

    binary_transport = FakeBinaryTransport()
    form_transport = FakeFormBytesTransport()
    iam_credential = YandexCredential(CredentialKind.IAM_TOKEN, lambda: iam_secret)
    speech = YandexSpeechKitProvider(
        config=YandexSpeechConfig(
            credential=iam_credential,
            voice="jane",
            folder_id="folder-fixture",
            execution_enabled=True,
        ),
        stt_transport=binary_transport,
        tts_transport=form_transport,
    )
    transcript = speech.transcribe(b"TRANSIENT_OGG_AUDIO", session_ref="tutor:fixture")
    audio = speech.synthesize("Короткое объяснение.", session_ref="tutor:fixture")
    assert transcript == "сочетание"
    assert audio == b"OGG_FIXTURE_AUDIO"
    assert binary_transport.last is not None
    stt_url, stt_headers, stt_params, stt_size, stt_timeout = binary_transport.last
    assert stt_url == "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    assert stt_headers["Authorization"] == f"Bearer {iam_secret}"
    assert stt_params["folderId"] == "folder-fixture"
    assert stt_params["lang"] == "ru-RU"
    assert stt_size == len(b"TRANSIENT_OGG_AUDIO")
    assert stt_timeout <= 60
    assert form_transport.last is not None
    tts_url, tts_headers, tts_fields, tts_timeout = form_transport.last
    assert tts_url == "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
    assert tts_headers["Authorization"] == f"Bearer {iam_secret}"
    assert tts_fields["folderId"] == "folder-fixture"
    assert tts_fields["voice"] == "jane"
    assert tts_timeout <= 60
    assert speech.raw_audio_persistence_count() == 0
    assert not any(isinstance(value, bytes) for value in vars(speech).values())

    disabled_speech = YandexSpeechKitProvider(
        config=YandexSpeechConfig(
            credential=api_credential,
            voice="jane",
            execution_enabled=False,
        ),
        stt_transport=binary_transport,
        tts_transport=form_transport,
    )
    fallback = MockSpeechProvider("reserve-fixture", transcript="резерв")
    gateway = VoiceGateway([disabled_speech, fallback])
    routed = gateway.transcribe(b"TRANSIENT", session_ref="tutor:fixture")
    assert routed.provider_id == "reserve-fixture"
    assert routed.fallback_used is True
    gateway.set_disabled("yandex-speechkit", True)
    routed = gateway.synthesize("резерв", session_ref="tutor:fixture")
    assert routed.provider_id == "reserve-fixture"

    representations = "\n".join((
        repr(api_credential),
        repr(iam_credential),
        repr(text_on),
        repr(text_on.config),
        repr(speech),
        repr(speech.config),
    ))
    assert api_secret not in representations
    assert iam_secret not in representations
    assert b"TRANSIENT_OGG_AUDIO" not in repr(vars(speech)).encode("utf-8")

    print("SEP1_YANDEX_TUTOR_LIVE_ADAPTERS=PASS")
    print("yandex_text_grounding_preserved=PASS")
    print("api_key_auth_header=PASS")
    print("iam_speech_auth_header=PASS")
    print("speechkit_stt_tts_contract=PASS")
    print("voice_fallback_kill_switch=PASS")
    print("learner_audio_persistence=0")
    print("secret_redaction=PASS")
    print("live_provider_execution_in_ci=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
