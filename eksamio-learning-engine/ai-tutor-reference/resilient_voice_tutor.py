#!/usr/bin/env python3
"""Voice resilience overlay for the accepted-semantic Tutor.

STT must succeed before a logical Tutor turn begins. After the text brain has
succeeded, a TTS outage may degrade the turn to text but must never discard the
accepted Tutor response or trigger a second LLM charge.
"""
from __future__ import annotations

from accepted_russian_semantic_tutor import AcceptedSemanticRussianTutorVerticalSlice
from sep1_russian_tutor import TutorInteraction, TutorSliceError, VoiceProviderFailure


class ResilientAcceptedSemanticTutor(AcceptedSemanticRussianTutorVerticalSlice):
    def voice_turn(self, session_ref: str, audio: bytes) -> TutorInteraction:
        state = self._state(session_ref)
        if not isinstance(audio, bytes) or not audio:
            raise TutorSliceError("non-empty transient learner audio is required")

        # No LLM turn/quota is created until STT yields a usable transcript.
        try:
            asr = self.voice_gateway.transcribe(audio, session_ref=session_ref)
        except VoiceProviderFailure as exc:
            raise TutorSliceError("voice input unavailable; retry speech or use text") from exc
        transcript = str(asr.value).strip()
        if not transcript:
            raise TutorSliceError("voice input returned an empty transcript")
        state.raw_audio_inputs_seen += 1
        state.asr_provider_log.append(asr.provider_id)

        interaction = self._text_turn(state, transcript, modality="voice")

        # The logical paid turn is already accepted exactly once. If speech output
        # fails, preserve the text response instead of failing/reissuing the LLM turn.
        try:
            tts = self.voice_gateway.synthesize(interaction.tutor_text, session_ref=session_ref)
        except VoiceProviderFailure:
            return TutorInteraction(
                session_ref=interaction.session_ref,
                turn_id=interaction.turn_id,
                modality="voice-text-fallback",
                transcript=interaction.transcript,
                tutor_text=interaction.tutor_text,
                reliable_result=interaction.reliable_result,
                asr_provider_id=asr.provider_id,
                tts_provider_id=None,
                audio=None,
            )

        state.tts_provider_log.append(tts.provider_id)
        state.synthesized_audio_outputs_seen += 1
        if not isinstance(tts.value, bytes):
            return TutorInteraction(
                session_ref=interaction.session_ref,
                turn_id=interaction.turn_id,
                modality="voice-text-fallback",
                transcript=interaction.transcript,
                tutor_text=interaction.tutor_text,
                reliable_result=interaction.reliable_result,
                asr_provider_id=asr.provider_id,
                tts_provider_id=None,
                audio=None,
            )
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
