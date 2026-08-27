#!/usr/bin/env python3
"""Sep-1 grounded Russian Tutor vertical slice.

This module is deliberately a thin orchestration layer over the already merged
provider-neutral Tutor boundary and reliability gateway. Russian truth is loaded
from the reviewed repository content/mapping, not authored by a provider. Voice
is provider-neutral with Yandex-preferred routing and a reserve path. Raw learner
audio is transient and is never stored in Tutor session state.
"""
from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from reliability_gateway import (
    EpisodeProjection,
    FailureClass,
    ProviderAttempt,
    ProviderFault,
    ProviderOutcome,
    ReliabilityGateway,
    ReliableTurnResult,
)
from tutor_boundary import (
    PeisContextProjection,
    ProviderRequest,
    ProviderResponse,
    ServerTutorTurn,
    SystemPolicy,
    TutorHistoryEntry,
    VerifiedSubjectContext,
)


class TutorSliceError(ValueError):
    pass


class GroundingError(TutorSliceError):
    pass


class UnknownTutorSession(TutorSliceError):
    pass


class VoiceProviderFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class GroundedRussianCard:
    card_id: str
    semantic_id: str
    prompt: str
    correct_answer: str
    explanation: str
    rule_ref: str
    source_ref: str
    mapping_resolution: str

    @property
    def verified_excerpt(self) -> str:
        return (
            f"Задание: {self.prompt}\n"
            f"Проверенный ответ: {self.correct_answer}\n"
            f"Проверенное объяснение: {self.explanation}"
        )


class RussianGroundingLoader:
    """Load a reviewed card and its admitted semantic mapping from current repo data."""

    def __init__(self, engine_root: str | Path) -> None:
        root = Path(engine_root)
        practice_path = root / "92-RUSSIAN-EXCEPTIONS-PRACTICE-PILOT-v0.1.json"
        mapping_path = root / "russian-program/RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json"
        practice = json.loads(practice_path.read_text(encoding="utf-8"))
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
        self._items = {item.get("practice_item_id"): item for item in practice.get("items", [])}
        self._mapping = {row.get("practice_item_id"): row for row in mapping.get("rows", [])}

    def load(self, card_id: str) -> GroundedRussianCard:
        item = self._items.get(card_id)
        row = self._mapping.get(card_id)
        if not isinstance(item, dict) or not isinstance(row, dict):
            raise GroundingError("Tutor may ground only in a reviewed item with an admitted mapping")
        if item.get("status") not in {"source_verified", "reviewed"}:
            raise GroundingError("Tutor grounding item is not reviewed/source-verified")
        if row.get("integration_ready") is not True:
            raise GroundingError("Tutor grounding mapping is not integration-ready")
        semantic_ids = row.get("semantic_target_ids")
        if row.get("mapping_resolution") != "EXACT" or not isinstance(semantic_ids, list) or len(semantic_ids) != 1:
            raise GroundingError("launch Tutor slice requires one EXACT admitted semantic target")
        prompt = item.get("prompt", {}).get("text")
        answer = item.get("answer", {}).get("text")
        feedback = item.get("feedback", {})
        explanation = feedback.get("why")
        rule_ref = feedback.get("rule_ref")
        if not all(isinstance(value, str) and value for value in (prompt, answer, explanation, rule_ref)):
            raise GroundingError("launch Tutor slice requires reviewed text prompt/answer/explanation")
        return GroundedRussianCard(
            card_id=card_id,
            semantic_id=str(semantic_ids[0]),
            prompt=prompt,
            correct_answer=answer,
            explanation=explanation,
            rule_ref=rule_ref,
            source_ref=f"source:russian-reviewed-card:{card_id}",
            mapping_resolution="EXACT",
        )


class GroundedTextProvider:
    """Deterministic provider fixture that can only answer from verified context."""

    def __init__(self, provider_id: str, *, fail_once: FailureClass | None = None) -> None:
        self.provider_id = provider_id
        self.fail_once = fail_once
        self.calls = 0

    def generate(self, request: ProviderRequest, attempt: ProviderAttempt) -> ProviderOutcome:
        self.calls += 1
        if self.fail_once is not None and self.calls == 1:
            return ProviderFault(self.fail_once, "deterministic launch-slice fixture")
        if len(request.verified_source_refs) != 1 or len(request.verified_excerpts) != 1:
            return ProviderFault(FailureClass.INVALID_PLATFORM_REQUEST, "grounding must be singular and verified")
        source_ref = request.verified_source_refs[0]
        excerpt = request.verified_excerpts[0]
        if not source_ref.startswith("source:russian-reviewed-card:"):
            return ProviderFault(FailureClass.INVALID_PLATFORM_REQUEST, "unverified Russian source ref")
        if "Проверенный ответ:" not in excerpt or "Проверенное объяснение:" not in excerpt:
            return ProviderFault(FailureClass.INVALID_PLATFORM_REQUEST, "verified excerpt lacks answer/explanation")
        explanation = excerpt.split("Проверенное объяснение:", 1)[1].strip()
        answer_line = excerpt.split("Проверенный ответ:", 1)[1].splitlines()[0].strip()
        text = (
            f"Опираемся на проверенный материал Eksamio: {explanation} "
            f"Для самопроверки ориентир — «{answer_line}». Затем ответь самостоятельно без подсказки."
        )
        return ProviderResponse(text=text, source_refs=(source_ref,))


class MockSpeechProvider:
    """Deterministic ASR/TTS fixture; accepts bytes transiently but stores none."""

    def __init__(
        self,
        provider_id: str,
        *,
        transcript: str,
        fail_asr_once: bool = False,
        fail_tts_once: bool = False,
    ) -> None:
        self.provider_id = provider_id
        self.transcript = transcript
        self.fail_asr_once = fail_asr_once
        self.fail_tts_once = fail_tts_once
        self.asr_calls = 0
        self.tts_calls = 0

    def transcribe(self, audio: bytes, *, session_ref: str) -> str:
        self.asr_calls += 1
        if self.fail_asr_once and self.asr_calls == 1:
            raise VoiceProviderFailure(f"{self.provider_id}: deterministic ASR failure")
        if not isinstance(audio, bytes) or not audio:
            raise VoiceProviderFailure("empty audio")
        if not session_ref.startswith("tutor:"):
            raise VoiceProviderFailure("invalid Tutor session")
        return self.transcript

    def synthesize(self, text: str, *, session_ref: str) -> bytes:
        self.tts_calls += 1
        if self.fail_tts_once and self.tts_calls == 1:
            raise VoiceProviderFailure(f"{self.provider_id}: deterministic TTS failure")
        if not text or not session_ref.startswith("tutor:"):
            raise VoiceProviderFailure("invalid TTS input")
        return f"MOCK_AUDIO|{self.provider_id}|{session_ref}|{text}".encode("utf-8")


@dataclass(frozen=True)
class VoiceRouteResult:
    value: str | bytes
    provider_id: str
    fallback_used: bool


class VoiceGateway:
    """Yandex-preferred provider-neutral ASR/TTS router with a kill switch."""

    def __init__(self, providers: list[MockSpeechProvider]) -> None:
        if not providers:
            raise ValueError("at least one voice provider is required")
        self.providers = list(providers)
        self.disabled: set[str] = set()

    def set_disabled(self, provider_id: str, disabled: bool) -> None:
        if disabled:
            self.disabled.add(provider_id)
        else:
            self.disabled.discard(provider_id)

    def transcribe(self, audio: bytes, *, session_ref: str) -> VoiceRouteResult:
        attempted = 0
        for provider in self.providers:
            if provider.provider_id in self.disabled:
                continue
            attempted += 1
            try:
                value = provider.transcribe(audio, session_ref=session_ref)
                return VoiceRouteResult(value=value, provider_id=provider.provider_id, fallback_used=attempted > 1)
            except VoiceProviderFailure:
                continue
        raise VoiceProviderFailure("all admitted ASR providers unavailable")

    def synthesize(self, text: str, *, session_ref: str) -> VoiceRouteResult:
        attempted = 0
        for provider in self.providers:
            if provider.provider_id in self.disabled:
                continue
            attempted += 1
            try:
                value = provider.synthesize(text, session_ref=session_ref)
                return VoiceRouteResult(value=value, provider_id=provider.provider_id, fallback_used=attempted > 1)
            except VoiceProviderFailure:
                continue
        raise VoiceProviderFailure("all admitted TTS providers unavailable")


@dataclass
class TutorSessionState:
    session_ref: str
    learner_profile_id: str
    grounding: GroundedRussianCard
    history: list[TutorHistoryEntry] = field(default_factory=list)
    turn_count: int = 0
    modality_log: list[str] = field(default_factory=list)
    asr_provider_log: list[str] = field(default_factory=list)
    tts_provider_log: list[str] = field(default_factory=list)
    raw_audio_inputs_seen: int = 0
    synthesized_audio_outputs_seen: int = 0

    def raw_audio_persistence_count(self) -> int:
        # State contains counters/metadata only. A bytes object anywhere is a hard failure.
        for value in vars(self).values():
            if isinstance(value, bytes):
                return 1
            if isinstance(value, list) and any(isinstance(item, bytes) for item in value):
                return 1
        return 0


@dataclass(frozen=True)
class TutorInteraction:
    session_ref: str
    turn_id: str
    modality: str
    transcript: str
    tutor_text: str
    reliable_result: ReliableTurnResult
    asr_provider_id: str | None = None
    tts_provider_id: str | None = None
    audio: bytes | None = None


class RussianTutorVerticalSlice:
    """One logical Tutor session across text and voice modalities."""

    def __init__(
        self,
        *,
        engine_root: str | Path,
        text_gateway: ReliabilityGateway,
        voice_gateway: VoiceGateway,
        session_ref_factory: Callable[[], str] | None = None,
    ) -> None:
        self.grounding_loader = RussianGroundingLoader(engine_root)
        self.text_gateway = text_gateway
        self.voice_gateway = voice_gateway
        self.session_ref_factory = session_ref_factory or (lambda: "tutor:" + secrets.token_urlsafe(18))
        self.sessions: dict[str, TutorSessionState] = {}

    def open_session(self, *, learner_profile_id: str, card_id: str) -> TutorSessionState:
        if not isinstance(learner_profile_id, str) or len(learner_profile_id) < 3:
            raise TutorSliceError("server-owned learner profile is required")
        grounding = self.grounding_loader.load(card_id)
        session_ref = self.session_ref_factory()
        if not session_ref.startswith("tutor:") or session_ref in self.sessions:
            raise TutorSliceError("invalid/duplicate server Tutor session ref")
        state = TutorSessionState(session_ref, learner_profile_id, grounding)
        self.sessions[session_ref] = state
        return state

    def _state(self, session_ref: str) -> TutorSessionState:
        try:
            return self.sessions[session_ref]
        except KeyError as exc:
            raise UnknownTutorSession("unknown Tutor session") from exc

    def _text_turn(self, state: TutorSessionState, learner_text: str, *, modality: str) -> TutorInteraction:
        if not isinstance(learner_text, str) or not learner_text.strip():
            raise TutorSliceError("learner text/transcript is required")
        state.turn_count += 1
        turn_id = f"turn-{state.turn_count:03d}"
        grounding = state.grounding
        history = tuple(state.history)
        learning_goal = f"understand:{grounding.semantic_id}"
        turn = ServerTutorTurn(
            tutor_session_ref=state.session_ref,
            subject_id="russian",
            learning_goal=learning_goal,
            policy=SystemPolicy(verification_required=True, allowed_tool_names=()),
            verified_subject=VerifiedSubjectContext(
                source_refs=(grounding.source_ref,),
                excerpts=(grounding.verified_excerpt,),
            ),
            peis_projection=PeisContextProjection(
                projection_version="sep1-russian-tutor-v1",
                learning_summary="Use reviewed Russian evidence; Tutor assistance is not independent verification.",
                target_refs=(grounding.semantic_id,),
                projection_ref=f"server-projection:{state.learner_profile_id}:{grounding.semantic_id}",
            ),
            history=history,
            learner_text=learner_text.strip(),
            help_state="GUIDED_HELP",
            continuation_marker=state.session_ref,
        )
        episode = EpisodeProjection(
            episode_id=state.session_ref,
            turn_id=turn_id,
            learning_goal=learning_goal,
            semantic_targets=(grounding.semantic_id,),
            verified_context_refs=(grounding.source_ref,),
            peis_projection_version=turn.peis_projection.projection_version,
            peis_projection_ref=turn.peis_projection.projection_ref,
            help_state=turn.help_state,
            verification_required=True,
            structured_history_summary=tuple(f"{entry.role}:{entry.text}" for entry in history),
            continuation_marker=state.session_ref,
        )
        reliable = self.text_gateway.handle_turn(episode, turn, capability="text")
        if reliable.status != "TUTOR_ADVISORY" or reliable.tutor_result is None or not reliable.tutor_result.text:
            raise TutorSliceError("grounded Tutor text path unavailable")
        tutor_text = reliable.tutor_result.text
        state.history.extend(
            [TutorHistoryEntry("learner", learner_text.strip()), TutorHistoryEntry("tutor", tutor_text)]
        )
        state.modality_log.append(modality)
        return TutorInteraction(
            session_ref=state.session_ref,
            turn_id=turn_id,
            modality=modality,
            transcript=learner_text.strip(),
            tutor_text=tutor_text,
            reliable_result=reliable,
        )

    def text_turn(self, session_ref: str, learner_text: str) -> TutorInteraction:
        return self._text_turn(self._state(session_ref), learner_text, modality="text")

    def voice_turn(self, session_ref: str, audio: bytes) -> TutorInteraction:
        state = self._state(session_ref)
        if not isinstance(audio, bytes) or not audio:
            raise TutorSliceError("non-empty transient learner audio is required")
        state.raw_audio_inputs_seen += 1
        asr = self.voice_gateway.transcribe(audio, session_ref=session_ref)
        state.asr_provider_log.append(asr.provider_id)
        interaction = self._text_turn(state, str(asr.value), modality="voice")
        tts = self.voice_gateway.synthesize(interaction.tutor_text, session_ref=session_ref)
        state.tts_provider_log.append(tts.provider_id)
        state.synthesized_audio_outputs_seen += 1
        if not isinstance(tts.value, bytes):
            raise TutorSliceError("TTS provider returned a non-audio payload")
        # Raw learner audio and generated audio are returned/transient only; neither is placed in state/history.
        return TutorInteraction(
            session_ref=interaction.session_ref,
            turn_id=interaction.turn_id,
            modality="voice",
            transcript=interaction.transcript,
            tutor_text=interaction.tutor_text,
            reliable_result=interaction.reliable_result,
            asr_provider_id=asr.provider_id,
            tts_provider_id=tts.provider_id,
            audio=tts.value,
        )
