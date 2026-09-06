#!/usr/bin/env python3
"""Deterministic zero-live gate for the canonical four-brain TEXT benchmark."""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(HERE))

from four_brain_text_benchmark import (  # noqa: E402
    BENCHMARK_CARD_ID,
    BENCHMARK_SEMANTIC_ID,
    DEEPSEEK_BENCHMARK_MODEL,
    DEEPSEEK_RESPONSES_ENDPOINT,
    MAX_OUTPUT_TOKENS,
    OPENAI_BENCHMARK_MODEL,
    OPENAI_RESPONSES_ENDPOINT,
    QWEN_BENCHMARK_MODEL,
    FourBrainConfigurationError,
    FourBrainTextConfig,
    assemble_four_brain_text_tutor,
    open_four_brain_benchmark_session,
)

FIRST_PROMPT = "Я думаю, что правильно «сочитание», потому что в корнях -чет-/-чит- перед -а- обычно пишется И. Я прав?"
QWEN_FIXTURE_ENDPOINT = "https://fixture.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/responses"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)
    print(f"PASS: {message}")


@contextmanager
def fake_credentials():
    values = {
        "OPENAI_API_KEY": "fixture-openai-secret",
        "QWEN_API_KEY": "fixture-qwen-secret",
        "DEEPSEEK_API_KEY": "fixture-deepseek-secret",
        "YANDEX_AI_STUDIO_API_KEY": "fixture-yandex-secret",
        "YANDEX_FOLDER_ID": "fixture-folder",
        "EKSAMIO_YANDEX_ALICE_MODEL_ID": "aliceai-llm",
        "EKSAMIO_YANDEX_ALICE_FULL_SIZE_CONFIRMED": "1",
    }
    old = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class ScriptedTransport:
    def __init__(self, response: Mapping[str, Any]) -> None:
        self.response = response
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
        self.requests.append(
            {
                "url": url,
                "headers": dict(headers),
                "body": dict(body),
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.response


def config(mode: str) -> FourBrainTextConfig:
    return FourBrainTextConfig(
        brain_mode=mode,  # type: ignore[arg-type]
        owner_live_authorized=True,
        text_execution_enabled=True,
        qwen_responses_base_url=QWEN_FIXTURE_ENDPOINT,
        yandex_folder_id="fixture-folder",
        yandex_model_id="aliceai-llm",
        yandex_full_size_confirmed=True,
    )


def forced_provider_parity() -> None:
    payloads: dict[str, list[dict[str, Any]]] = {}
    exact_models: dict[str, str] = {}
    endpoints: dict[str, str] = {}
    with fake_credentials():
        for mode in ("openai", "qwen", "deepseek", "yandex"):
            response: Mapping[str, Any]
            if mode == "yandex":
                response = {"choices": [{"message": {"content": f"{mode.upper()}_OK"}}]}
            else:
                response = {"output_text": f"{mode.upper()}_OK"}
            transport = ScriptedTransport(response)
            assembly = assemble_four_brain_text_tutor(
                engine_root=ENGINE,
                config=config(mode),
                transport=transport,
                session_ref_factory=lambda mode=mode: f"tutor:four-brain-{mode}",
            )
            state = open_four_brain_benchmark_session(
                assembly,
                f"learner-four-brain-{mode}",
            )
            require(state.grounding.card_id == BENCHMARK_CARD_ID, f"{mode} uses reviewed card")
            require(state.grounding.semantic_id == BENCHMARK_SEMANTIC_ID, f"{mode} uses exact semantic")
            require(state.grounding.mapping_resolution == "EXACT", f"{mode} grounding remains EXACT")
            interaction = assembly.tutor.text_turn(state.session_ref, FIRST_PROMPT)
            require(f"{mode.upper()}_OK" in interaction.tutor_text, f"{mode} forced route succeeds")
            require(transport.calls == 1, f"{mode} uses exactly one scripted provider request")
            request = transport.requests[0]
            body = request["body"]
            require("temperature" not in body and "top_p" not in body, f"{mode} receives no custom sampling temperature")
            if mode == "yandex":
                require(body.get("max_tokens") == MAX_OUTPUT_TOKENS, "Yandex output cap matches benchmark")
                messages = body.get("messages")
            else:
                require(body.get("max_output_tokens") == MAX_OUTPUT_TOKENS, f"{mode} output cap matches benchmark")
                messages = body.get("input")
            require(isinstance(messages, list), f"{mode} receives projected message history")
            payloads[mode] = messages
            exact_models[mode] = assembly.exact_brain_model
            endpoints[mode] = str(request["url"])
            snapshot = assembly.safety_snapshot()
            require(snapshot["auto_or_fallback_enabled"] is False, f"{mode} has no AUTO/fallback")
            require(snapshot["voice_in_brain_ranking"] is False, f"{mode} brain ranking is TEXT-only")
            require(snapshot["production_peis_writes_enabled"] is False, f"{mode} PEIS writes stay off")
            require(snapshot["learner_audio_persisted_bytes"] == 0, f"{mode} audio persistence is zero")

    reference = payloads["openai"]
    for mode in ("qwen", "deepseek", "yandex"):
        require(payloads[mode] == reference, f"{mode} receives identical grounded prompt/history")
    require(exact_models["openai"] == OPENAI_BENCHMARK_MODEL, "OpenAI model is current benchmark identity")
    require(exact_models["qwen"] == QWEN_BENCHMARK_MODEL, "Qwen model identity is locked")
    require(exact_models["deepseek"] == DEEPSEEK_BENCHMARK_MODEL, "DeepSeek model identity is locked")
    require("/aliceai-llm/latest" in exact_models["yandex"], "offline Yandex fixture is explicit")
    require(endpoints["openai"] == OPENAI_RESPONSES_ENDPOINT, "OpenAI uses Responses endpoint")
    require(endpoints["qwen"] == QWEN_FIXTURE_ENDPOINT, "Qwen uses workspace-shaped Responses endpoint")
    require(endpoints["deepseek"] == DEEPSEEK_RESPONSES_ENDPOINT, "DeepSeek uses current Responses endpoint")


def fail_closed_contracts() -> None:
    try:
        FourBrainTextConfig(brain_mode="auto")  # type: ignore[arg-type]
    except FourBrainConfigurationError:
        pass
    else:
        raise AssertionError("AUTO benchmark mode was accepted")

    try:
        FourBrainTextConfig(
            brain_mode="qwen",
            owner_live_authorized=True,
            text_execution_enabled=True,
        )
    except FourBrainConfigurationError:
        pass
    else:
        raise AssertionError("Qwen live benchmark accepted a missing workspace endpoint")

    try:
        FourBrainTextConfig(
            brain_mode="qwen",
            owner_live_authorized=True,
            text_execution_enabled=True,
            qwen_responses_base_url="https://example.com/compatible-mode/v1/responses",
        )
    except FourBrainConfigurationError:
        pass
    else:
        raise AssertionError("Qwen benchmark accepted a non-Aliyun endpoint")

    try:
        FourBrainTextConfig(
            brain_mode="yandex",
            yandex_model_id="aliceai-llm-flash",
        )
    except FourBrainConfigurationError:
        pass
    else:
        raise AssertionError("Yandex Flash was admitted")

    try:
        FourBrainTextConfig(
            brain_mode="yandex",
            owner_live_authorized=True,
            text_execution_enabled=True,
            yandex_folder_id="fixture-folder",
            yandex_model_id="account-current-full-size-id",
            yandex_full_size_confirmed=False,
        )
    except FourBrainConfigurationError:
        pass
    else:
        raise AssertionError("unconfirmed Yandex full-size model was admitted")

    try:
        FourBrainTextConfig(brain_mode="openai", public_traffic_enabled=True)
    except FourBrainConfigurationError:
        pass
    else:
        raise AssertionError("public benchmark traffic was admitted")

    print("PASS: AUTO/fallback is fail-closed")
    print("PASS: Qwen workspace endpoint is fail-closed")
    print("PASS: Yandex Flash/unconfirmed full-size is fail-closed")
    print("PASS: public traffic is fail-closed")


def main() -> int:
    require(BENCHMARK_CARD_ID == "ex-practice-alt-sochetat-001", "canonical benchmark card is fixed")
    require(BENCHMARK_SEMANTIC_ID == "school-i-e-alternating-verb-roots-stressed-a", "canonical benchmark semantic is fixed")
    require(OPENAI_BENCHMARK_MODEL == "gpt-6-astra", "OpenAI benchmark uses GPT-6 Astra")
    require(QWEN_BENCHMARK_MODEL == "qwen3.8-max", "Qwen benchmark uses qwen3.8-max")
    require(DEEPSEEK_BENCHMARK_MODEL == "deepseek-v4-pro", "DeepSeek benchmark uses deepseek-v4-pro")
    forced_provider_parity()
    fail_closed_contracts()
    print("FOUR_BRAIN_TEXT_BENCHMARK=PASS")
    print("BRAIN_PROVIDERS=openai,qwen,deepseek,yandex")
    print("BENCHMARK_STEPS=10")
    print("CUSTOM_TEMPERATURE_SENT=0")
    print("VOICE_IN_BRAIN_RANKING=0")
    print("REAL_PROVIDER_REQUEST_COUNT=0")
    print("PAID_AI_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
