#!/usr/bin/env python3
"""Immediate private OpenAI VOICE benchmark without a Yandex folder-id dependency.

The selected brain is OpenAI only. Speech remains Yandex SpeechKit with the
existing service-account API-key resolver. Current Yandex SpeechKit guidance
allows service-account API-key authentication without a caller-supplied folder
ID for this path; Alice AI remains separately blocked until a folder ID exists.
"""
from __future__ import annotations

import secrets
import threading
import webbrowser
from http.server import ThreadingHTTPServer

import private_openai_yandex_121_tutor_ui as base_ui
from private_openai_yandex_121_tutor import (
    OPENAI_BENCHMARK_MODEL,
    YANDEX_BENCHMARK_MODEL_ID,
    FastTutorConfig,
    FastTutorConfigurationError,
    assemble_fast_tutor,
    open_benchmark_session,
)


class OpenAIVoiceConfig(FastTutorConfig):
    """FastTutorConfig variant: folder ID is not required for SpeechKit API-key voice."""

    def __post_init__(self) -> None:
        if self.brain_mode != "openai":
            raise FastTutorConfigurationError("this immediate runner is OpenAI VOICE only")
        if self.openai_model != OPENAI_BENCHMARK_MODEL:
            raise FastTutorConfigurationError("OpenAI model must remain gpt-5.6-sol")
        if self.yandex_model_id != YANDEX_BENCHMARK_MODEL_ID:
            raise FastTutorConfigurationError("Yandex model lock drift")
        if self.public_traffic_enabled:
            raise FastTutorConfigurationError("private benchmark must stay localhost-only")
        if (self.text_execution_enabled or self.speech_execution_enabled) and not self.owner_live_authorized:
            raise FastTutorConfigurationError("live provider execution requires owner authorization")
        if self.yandex_voice != "lera" or self.yandex_voice_role != "neutral" or abs(self.yandex_voice_speed - 1.04) > 0.0001:
            raise FastTutorConfigurationError("voice benchmark must remain Lera / neutral / 1.04")


class OpenAIVoiceApp(base_ui.App):
    def status(self) -> dict[str, object]:
        status = super().status()
        providers = status.get("providers")
        if isinstance(providers, dict):
            openai = providers.get("openai")
            status["openai_voice_ready"] = bool(
                isinstance(openai, dict) and openai.get("ready") and status.get("speech_ready")
            )
        return status

    def start(self, provider: str, mode: str) -> dict[str, object]:
        if provider != "openai" or mode != "voice":
            raise ValueError("this immediate runner is locked to Tutor A — OpenAI / VOICE")
        status = self.status()
        providers = status.get("providers")
        if not isinstance(providers, dict) or not isinstance(providers.get("openai"), dict) or not providers["openai"].get("ready"):
            raise ValueError("OpenAI credential preflight BLOCKED")
        if not status.get("speech_ready"):
            raise ValueError("Yandex SpeechKit credential preflight BLOCKED")

        config = OpenAIVoiceConfig(
            brain_mode="openai",
            yandex_folder_id=None,
            owner_live_authorized=True,
            text_execution_enabled=True,
            speech_execution_enabled=True,
        )
        assembly = assemble_fast_tutor(engine_root=base_ui.ENGINE, config=config)
        learner_profile_id = "private-openai-voice-" + secrets.token_hex(6)
        tutor_state = open_benchmark_session(assembly, learner_profile_id)
        public_session = secrets.token_urlsafe(24)
        with self.lock:
            self.sessions[public_session] = base_ui.LiveSession(
                assembly=assembly,
                tutor_session_ref=tutor_state.session_ref,
                provider="openai",
                run_mode="voice",
                model=assembly.exact_brain_model,
            )
        return {
            "session": public_session,
            "provider": "openai",
            "mode": "voice",
            "model": assembly.exact_brain_model,
            "semantic_id": tutor_state.grounding.semantic_id,
        }


def main() -> int:
    args = base_ui.parse_args()
    if not args.owner_authorized:
        print("OPENAI_VOICE_UI=BLOCKED_OWNER_AUTHORIZATION")
        return 2
    if not 1024 <= args.port <= 65535:
        print("OPENAI_VOICE_UI=BLOCKED_INVALID_PORT")
        return 2

    app = OpenAIVoiceApp(yandex_folder_id=None)
    base_ui.Handler.app = app
    server = ThreadingHTTPServer((base_ui.HOST, args.port), base_ui.Handler)
    url = f"http://{base_ui.HOST}:{args.port}/"
    print(f"OPENAI_VOICE_UI=READY {url}")
    print("BRAIN_PROVIDER=openai")
    print("SPEECH_PROVIDER=yandex-speechkit")
    print("YANDEX_FOLDER_ID_REQUIRED_FOR_THIS_RUN=0")
    print("PUBLIC_TRAFFIC_ENABLED=0")
    print("PRODUCTION_PEIS_WRITES_ENABLED=0")
    print("RAW_AUDIO_PERSISTED_BYTES=0")
    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
