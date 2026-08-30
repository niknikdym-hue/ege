#!/usr/bin/env python3
"""Unified local UI for OpenAI/Qwen/DeepSeek/Alice Tutor acceptance."""
from __future__ import annotations

import argparse
import secrets
import threading
import webbrowser
from http.server import ThreadingHTTPServer
from typing import Any, Mapping

import private_multi_provider_tutor_test_ui as base_ui
from deepseek_secret_provider import DeepSeekSecretProvider
from private_provider_config import load_private_provider_config
from private_staging_four_brain_tutor import (
    PrivateFourBrainTutorConfig,
    assemble_private_four_brain_tutor,
)

FOUR_PROVIDER_MODES = {"auto", "openai", "qwen", "deepseek", "yandex"}


class SimulatedUnavailableTransport:
    """Deterministic offline failure injection for an owner-authorized live route."""

    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name
        self.calls = 0

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, Any],
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        self.calls += 1
        raise TimeoutError(f"simulated {self.provider_name} outage")


def _four_brain_page(*, default_provider: str, lock_provider: bool) -> str:
    page = base_ui.PAGE
    page = page.replace("трёх AI-мозгов", "четырёх AI-мозгов")
    page = page.replace(
        '<option value="openai">OpenAI</option><option value="qwen">Qwen</option><option value="yandex">Яндекс</option><option value="auto">Авто: OpenAI → Qwen → Яндекс</option>',
        '<option value="openai">OpenAI</option><option value="qwen">Qwen</option><option value="deepseek">DeepSeek</option><option value="yandex">Яндекс (Alice AI)</option><option value="auto">Авто: OpenAI → Qwen → DeepSeek → Яндекс</option>',
    )
    page = page.replace(
        "const labels={openai:'OpenAI',qwen:'Qwen',yandex:'Яндекс',auto:'Авто'};",
        "const labels={openai:'OpenAI',qwen:'Qwen',deepseek:'DeepSeek',yandex:'Яндекс',auto:'Авто'};",
    )
    page = page.replace(
        "for(const k of ['openai','qwen','yandex'])",
        "for(const k of ['openai','qwen','deepseek','yandex'])",
    )
    labels = {
        "openai": "OpenAI",
        "qwen": "Qwen",
        "deepseek": "DeepSeek",
        "yandex": "Яндекс (Alice AI)",
        "auto": "Авто: OpenAI → Qwen → DeepSeek → Яндекс",
    }
    marker = f'<option value="{default_provider}">{labels[default_provider]}</option>'
    page = page.replace(marker, marker.replace(">", " selected>"), 1)
    if lock_provider:
        page = page.replace('<select id="provider">', '<select id="provider" disabled>', 1)
        page = page.replace(
            "При отказе одного AI система продолжит ход через следующий backend.",
            "Failover-тест: AUTO зафиксирован; недоступные backend'ы имитируются локально, следующий backend вызывается реально.",
        )
    return page


class FourBrainApp(base_ui.App):
    def __init__(self, *, simulated_unavailable: set[str], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.simulated_unavailable = set(simulated_unavailable)

    def provider_status(self) -> dict[str, dict[str, object]]:
        status = super().provider_status()
        deepseek_ready = base_ui._credential_ready(DeepSeekSecretProvider())
        status["deepseek"] = {
            "ready": deepseek_ready,
            "detail": "ключ не найден" if not deepseek_ready else "",
        }
        for name in self.simulated_unavailable:
            if name in status:
                status[name]["ready"] = False
                status[name]["detail"] = "намеренно отключён для failover-теста"
        return status

    def _transport(self, name: str):
        return SimulatedUnavailableTransport(name) if name in self.simulated_unavailable else None

    def start(self, provider: str, semantic_id: str) -> dict[str, object]:
        if provider not in FOUR_PROVIDER_MODES:
            raise ValueError("неизвестный AI-провайдер")
        topic = next((item for item in self.topics if item["id"] == semantic_id), None)
        if not topic:
            raise ValueError("тема не допущена к тестовому Tutor")
        config = PrivateFourBrainTutorConfig(
            text_provider_mode=provider,  # type: ignore[arg-type]
            qwen_base_url=self.qwen_base_url,
            yandex_folder_id=self.yandex_folder_id,
            owner_live_authorized=True,
            text_execution_enabled=True,
            speech_execution_enabled=self.speech_enabled,
        )
        assembly = assemble_private_four_brain_tutor(
            engine_root=base_ui.ENGINE,
            config=config,
            openai_transport=self._transport("openai"),
            qwen_transport=self._transport("qwen"),
            deepseek_transport=self._transport("deepseek"),
            yandex_text_transport=self._transport("yandex"),
        )
        tutor_state = assembly.tutor.open_semantic_session(
            learner_profile_id="private-test-" + secrets.token_hex(6),
            semantic_id=semantic_id,
        )
        public_session = secrets.token_urlsafe(24)
        with self.lock:
            self.sessions[public_session] = base_ui.LiveSession(
                assembly=assembly,  # type: ignore[arg-type]
                tutor_session_ref=tutor_state.session_ref,
                provider_mode=provider,
                semantic_id=semantic_id,
                max_turns=self.max_turns,
            )
        return {"session": public_session, "topic_title": topic["title"]}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local Eksamio four-brain Tutor user test")
    parser.add_argument("--owner-authorized", action="store_true")
    parser.add_argument("--enable-speech", action="store_true")
    parser.add_argument("--max-turns", type=int, default=base_ui.DEFAULT_MAX_TURNS)
    parser.add_argument("--port", type=int, default=base_ui.DEFAULT_PORT)
    parser.add_argument("--qwen-base-url", default=None)
    parser.add_argument("--yandex-folder-id", default=None)
    parser.add_argument("--default-provider", choices=sorted(FOUR_PROVIDER_MODES), default="openai")
    parser.add_argument("--lock-provider", action="store_true")
    parser.add_argument(
        "--simulate-unavailable",
        default="",
        help="comma-separated provider names; only injects deterministic transport failures",
    )
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.owner_authorized:
        print("PRIVATE_FOUR_BRAIN_TUTOR_UI=BLOCKED_OWNER_AUTHORIZATION")
        return 2
    if not 1 <= args.max_turns <= 20:
        print("PRIVATE_FOUR_BRAIN_TUTOR_UI=BLOCKED_MAX_TURNS_MUST_BE_1_TO_20")
        return 2
    if not 1024 <= args.port <= 65535:
        print("PRIVATE_FOUR_BRAIN_TUTOR_UI=BLOCKED_INVALID_PORT")
        return 2
    simulated = {item.strip() for item in args.simulate_unavailable.split(",") if item.strip()}
    if not simulated.issubset({"openai", "qwen", "deepseek", "yandex"}):
        print("PRIVATE_FOUR_BRAIN_TUTOR_UI=BLOCKED_INVALID_FAILOVER_PROVIDER")
        return 2
    if simulated and args.default_provider != "auto":
        print("PRIVATE_FOUR_BRAIN_TUTOR_UI=BLOCKED_FAILOVER_TEST_REQUIRES_AUTO")
        return 2

    local_config = load_private_provider_config()
    qwen_base_url = args.qwen_base_url or local_config.qwen_base_url
    yandex_folder_id = args.yandex_folder_id or local_config.yandex_folder_id

    app = FourBrainApp(
        max_turns=args.max_turns,
        speech_enabled=args.enable_speech,
        qwen_base_url=qwen_base_url,
        yandex_folder_id=yandex_folder_id,
        simulated_unavailable=simulated,
    )
    base_ui.PAGE = _four_brain_page(default_provider=args.default_provider, lock_provider=args.lock_provider)
    base_ui.Handler.app = app
    server = ThreadingHTTPServer((base_ui.HOST, args.port), base_ui.Handler)
    url = f"http://{base_ui.HOST}:{args.port}/"
    print(f"PRIVATE_FOUR_BRAIN_TUTOR_UI=READY {url}")
    print("PROVIDER_MODES=openai,qwen,deepseek,yandex,auto")
    print("DEFAULT_PROVIDER=" + args.default_provider)
    print(f"PROVIDER_SELECTION_LOCKED={int(args.lock_provider)}")
    print("AUTO_ORDER=PROVISIONAL_NOT_PRODUCT_RANKING")
    print("SIMULATED_UNAVAILABLE=" + (",".join(sorted(simulated)) if simulated else "none"))
    print("PUBLIC_TRAFFIC_ENABLED=0")
    print(f"MAX_SUCCESSFUL_LEARNER_TURNS={args.max_turns}")
    print(f"SPEECH_ENABLED={int(args.enable_speech)}")
    print("VOICE_LAYER=YANDEX_SPEECHKIT_STT_PLUS_LERA_TTS")
    print("SECRETS_IN_BROWSER=0")
    print("RAW_AUDIO_PERSISTED=0")
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
