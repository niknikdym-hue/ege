#!/usr/bin/env python3
"""Canonical four-brain TEXT benchmark assembly for Eksamio Tutor.

This lane is intentionally separate from voice acceptance. It reuses the merged
reviewed 121-card grounding and provider-neutral Tutor orchestration, forces one
brain per run, forbids AUTO/fallback, and performs no production PEIS writes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from deepseek_secret_provider import DeepSeekSecretProvider
from four_brain_provider_adapters import (
    BenchmarkCredential,
    ChatBenchmarkConfig,
    ChatBenchmarkProvider,
    ResponsesBenchmarkConfig,
    ResponsesBenchmarkProvider,
)
from openai_secret_provider import OpenAISecretProvider
from qwen_secret_provider import QwenSecretProvider
from reliability_gateway import ProviderPath, ReliabilityGateway
from sep1_russian_tutor import (
    MockSpeechProvider,
    RussianTutorVerticalSlice,
    VoiceGateway,
)
from stdlib_json_transport import UrllibJsonTransport
from yandex_ai_secret_provider import YandexAISecretProvider

BrainMode = Literal["openai", "qwen", "deepseek", "yandex"]
BENCHMARK_CARD_ID = "ex-practice-alt-sochetat-001"
BENCHMARK_SEMANTIC_ID = "school-i-e-alternating-verb-roots-stressed-a"
OPENAI_BENCHMARK_MODEL = "gpt-6-astra"
QWEN_BENCHMARK_MODEL = "qwen3.8-max"
DEEPSEEK_BENCHMARK_MODEL = "deepseek-v4-pro"
OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"
DEEPSEEK_RESPONSES_ENDPOINT = "https://api.deepseek.com/responses"
YANDEX_CHAT_ENDPOINT = "https://ai.api.cloud.yandex.net/v1/chat/completions"
YANDEX_OFFLINE_FULL_SIZE_FIXTURE_ID = "aliceai-llm"
MAX_OUTPUT_TOKENS = 900


class FourBrainConfigurationError(ValueError):
    pass


def resolve_qwen_responses_endpoint(
    explicit_base_url: str | None = None,
    *,
    execution_enabled: bool,
) -> str:
    raw = (
        explicit_base_url
        or os.environ.get("QWEN_RESPONSES_BASE_URL")
        or os.environ.get("QWEN_BASE_URL")
        or os.environ.get("DASHSCOPE_BASE_URL")
        or ""
    ).strip().rstrip("/")
    if not raw:
        if execution_enabled:
            raise FourBrainConfigurationError(
                "Qwen live benchmark requires the account workspace Responses base URL"
            )
        return "https://disabled.invalid/responses"
    if raw.endswith("/responses"):
        endpoint = raw
    elif raw.endswith("/compatible-mode/v1"):
        endpoint = raw + "/responses"
    else:
        raise FourBrainConfigurationError(
            "Qwen endpoint must end with /compatible-mode/v1 or /responses"
        )
    parsed = urlparse(endpoint)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host.endswith("aliyuncs.com"):
        raise FourBrainConfigurationError(
            "Qwen benchmark requires an HTTPS Alibaba Model Studio aliyuncs.com endpoint"
        )
    if not endpoint.endswith("/compatible-mode/v1/responses"):
        raise FourBrainConfigurationError(
            "Qwen benchmark requires the current compatible-mode/v1/responses path"
        )
    return endpoint


@dataclass(frozen=True)
class FourBrainTextConfig:
    brain_mode: BrainMode
    owner_live_authorized: bool = False
    text_execution_enabled: bool = False
    public_traffic_enabled: bool = False
    openai_model: str = OPENAI_BENCHMARK_MODEL
    qwen_model: str = QWEN_BENCHMARK_MODEL
    deepseek_model: str = DEEPSEEK_BENCHMARK_MODEL
    qwen_responses_base_url: str | None = None
    yandex_folder_id: str | None = None
    yandex_model_id: str | None = None
    yandex_full_size_confirmed: bool = False

    def __post_init__(self) -> None:
        if self.brain_mode not in {"openai", "qwen", "deepseek", "yandex"}:
            raise FourBrainConfigurationError(
                "benchmark requires one forced openai/qwen/deepseek/yandex mode"
            )
        if self.public_traffic_enabled:
            raise FourBrainConfigurationError("four-brain benchmark is localhost/private only")
        if self.text_execution_enabled and not self.owner_live_authorized:
            raise FourBrainConfigurationError(
                "live provider execution requires explicit owner authorization"
            )
        if self.openai_model != OPENAI_BENCHMARK_MODEL:
            raise FourBrainConfigurationError(
                f"OpenAI benchmark model is locked to {OPENAI_BENCHMARK_MODEL}"
            )
        if self.qwen_model != QWEN_BENCHMARK_MODEL:
            raise FourBrainConfigurationError(
                f"Qwen benchmark model is locked to {QWEN_BENCHMARK_MODEL}"
            )
        if self.deepseek_model != DEEPSEEK_BENCHMARK_MODEL:
            raise FourBrainConfigurationError(
                f"DeepSeek benchmark model is locked to {DEEPSEEK_BENCHMARK_MODEL}"
            )
        if self.brain_mode == "qwen":
            resolve_qwen_responses_endpoint(
                self.qwen_responses_base_url,
                execution_enabled=self.text_execution_enabled,
            )
        if self.resolved_yandex_model_id and "flash" in self.resolved_yandex_model_id.lower():
            raise FourBrainConfigurationError(
                "Yandex Flash is forbidden; full-size Alice AI LLM is required"
            )
        if self.brain_mode == "yandex" and self.text_execution_enabled:
            if not self.resolved_yandex_folder_id:
                raise FourBrainConfigurationError(
                    "Yandex live benchmark requires YANDEX_FOLDER_ID"
                )
            if not self.resolved_yandex_model_id:
                raise FourBrainConfigurationError(
                    "Yandex live preflight must resolve the exact Alice AI model ID"
                )
            if not self.resolved_yandex_full_size_confirmed:
                raise FourBrainConfigurationError(
                    "Yandex live preflight must independently confirm full-size Alice AI LLM"
                )

    @property
    def resolved_yandex_folder_id(self) -> str | None:
        value = self.yandex_folder_id or os.environ.get("YANDEX_FOLDER_ID") or None
        return value.strip() if isinstance(value, str) and value.strip() else None

    @property
    def resolved_yandex_model_id(self) -> str | None:
        value = (
            self.yandex_model_id
            or os.environ.get("EKSAMIO_YANDEX_ALICE_MODEL_ID")
            or None
        )
        value = value.strip() if isinstance(value, str) and value.strip() else None
        if value and "flash" in value.lower():
            raise FourBrainConfigurationError(
                "Yandex Flash is forbidden; full-size Alice AI LLM is required"
            )
        return value

    @property
    def resolved_yandex_full_size_confirmed(self) -> bool:
        return self.yandex_full_size_confirmed or os.environ.get(
            "EKSAMIO_YANDEX_ALICE_FULL_SIZE_CONFIRMED",
            "",
        ).strip() == "1"

    @property
    def qwen_endpoint(self) -> str:
        return resolve_qwen_responses_endpoint(
            self.qwen_responses_base_url,
            execution_enabled=self.text_execution_enabled,
        )


@dataclass(frozen=True)
class FourBrainTextAssembly:
    tutor: RussianTutorVerticalSlice
    brain_provider: object
    config: FourBrainTextConfig

    @property
    def exact_brain_model(self) -> str:
        if self.config.brain_mode == "openai":
            return self.config.openai_model
        if self.config.brain_mode == "qwen":
            return self.config.qwen_model
        if self.config.brain_mode == "deepseek":
            return self.config.deepseek_model
        folder = self.config.resolved_yandex_folder_id or "unresolved-folder"
        model = self.config.resolved_yandex_model_id or "unresolved-full-size-alice-model"
        return f"gpt://{folder}/{model}/latest"

    def safety_snapshot(self) -> dict[str, object]:
        return {
            "brain_mode": self.config.brain_mode,
            "brain_provider_id": getattr(self.brain_provider, "provider_id", "unknown"),
            "exact_brain_model": self.exact_brain_model,
            "benchmark_card_id": BENCHMARK_CARD_ID,
            "benchmark_semantic_id": BENCHMARK_SEMANTIC_ID,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "custom_temperature_sent": False,
            "auto_or_fallback_enabled": False,
            "voice_in_brain_ranking": False,
            "public_traffic_enabled": False,
            "production_peis_writes_enabled": False,
            "persistent_evidence_enabled": False,
            "learner_audio_persisted_bytes": 0,
        }


def assemble_four_brain_text_tutor(
    *,
    engine_root: str | Path,
    config: FourBrainTextConfig,
    transport=None,
    session_ref_factory=None,
) -> FourBrainTextAssembly:
    json_transport = transport or UrllibJsonTransport()
    if config.brain_mode == "openai":
        provider = ResponsesBenchmarkProvider(
            config=ResponsesBenchmarkConfig(
                provider_id="openai-responses",
                credential=BenchmarkCredential(OpenAISecretProvider()),
                model=config.openai_model,
                endpoint=OPENAI_RESPONSES_ENDPOINT,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                execution_enabled=config.text_execution_enabled,
            ),
            transport=json_transport,
        )
    elif config.brain_mode == "qwen":
        provider = ResponsesBenchmarkProvider(
            config=ResponsesBenchmarkConfig(
                provider_id="qwen-responses",
                credential=BenchmarkCredential(QwenSecretProvider()),
                model=config.qwen_model,
                endpoint=config.qwen_endpoint,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                execution_enabled=config.text_execution_enabled,
            ),
            transport=json_transport,
        )
    elif config.brain_mode == "deepseek":
        provider = ResponsesBenchmarkProvider(
            config=ResponsesBenchmarkConfig(
                provider_id="deepseek-responses",
                credential=BenchmarkCredential(DeepSeekSecretProvider()),
                model=config.deepseek_model,
                endpoint=DEEPSEEK_RESPONSES_ENDPOINT,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                execution_enabled=config.text_execution_enabled,
            ),
            transport=json_transport,
        )
    else:
        folder = config.resolved_yandex_folder_id or "disabled-folder"
        model_id = config.resolved_yandex_model_id or YANDEX_OFFLINE_FULL_SIZE_FIXTURE_ID
        provider = ChatBenchmarkProvider(
            config=ChatBenchmarkConfig(
                provider_id="yandex-alice-ai",
                credential=BenchmarkCredential(
                    YandexAISecretProvider(),
                    authorization_scheme="Api-Key",
                ),
                model=f"gpt://{folder}/{model_id}/latest",
                endpoint=YANDEX_CHAT_ENDPOINT,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                execution_enabled=config.text_execution_enabled,
            ),
            transport=json_transport,
        )

    provider_id = getattr(provider, "provider_id")
    text_gateway = ReliabilityGateway(
        {
            (provider_id, "text"): ProviderPath(
                provider_id,
                "text",
                f"{config.brain_mode}-four-brain-text-v1",
                "PRIVATE_HUMAN_BENCHMARK_ONLY",
                1,
            )
        },
        {provider_id: provider},
    )
    no_voice = MockSpeechProvider(
        "four-brain-text-no-voice",
        transcript="voice is outside the brain ranking",
    )
    tutor = RussianTutorVerticalSlice(
        engine_root=engine_root,
        text_gateway=text_gateway,
        voice_gateway=VoiceGateway([no_voice]),
        session_ref_factory=session_ref_factory,
    )
    return FourBrainTextAssembly(tutor=tutor, brain_provider=provider, config=config)


def open_four_brain_benchmark_session(
    assembly: FourBrainTextAssembly,
    learner_profile_id: str,
):
    state = assembly.tutor.open_session(
        learner_profile_id=learner_profile_id,
        card_id=BENCHMARK_CARD_ID,
    )
    if state.grounding.semantic_id != BENCHMARK_SEMANTIC_ID:
        raise FourBrainConfigurationError("merged 121-card benchmark semantic drift")
    if state.grounding.mapping_resolution != "EXACT":
        raise FourBrainConfigurationError("benchmark card is no longer EXACT")
    return state
