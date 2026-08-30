#!/usr/bin/env python3
"""Blind local human comparison for the four Eksamio Tutor brains.

The learner sees only A/B/C/D. The random alias mapping is stored locally with
0600 permissions and is never sent to the browser or printed to the terminal.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import threading
import webbrowser
from pathlib import Path
from typing import Any

import private_four_brain_tutor_test_ui as four
import private_multi_provider_tutor_test_ui as base_ui
from private_provider_config import load_private_provider_config

REAL_PROVIDERS = ("openai", "qwen", "deepseek", "yandex")
ALIASES = ("A", "B", "C", "D")
PROVIDER_ID_TO_NAME = {
    "openai-responses": "openai",
    "qwen-model-studio": "qwen",
    "deepseek-api": "deepseek",
    "yandex-alice-ai": "yandex",
}


def _candidate_sha() -> str | None:
    value = os.environ.get("EKSAMIO_TUTOR_CANDIDATE_SHA", "").strip().lower()
    if not value:
        return None
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError("invalid EKSAMIO_TUTOR_CANDIDATE_SHA")
    return value


def _mapping_dir() -> Path:
    root = Path.home() / "Library" / "Application Support" / "Eksamio" / "TutorBlindTests"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    return root


def _create_mapping() -> tuple[str, dict[str, str]]:
    providers = list(REAL_PROVIDERS)
    secrets.SystemRandom().shuffle(providers)
    mapping = dict(zip(ALIASES, providers, strict=True))
    test_id = "blind-" + secrets.token_hex(6)
    path = _mapping_dir() / f"{test_id}.json"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    payload = {
        "schema_version": "eksamio.tutor.blind-provider-map.v1",
        "test_id": test_id,
        "candidate_sha": _candidate_sha(),
        "mapping": mapping,
    }
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    return test_id, mapping


def _blind_page(*, speech_enabled: bool, test_id: str) -> str:
    page = base_ui.PAGE
    page = page.replace("трёх AI-мозгов", "четырёх скрытых AI-мозгов")
    page = page.replace("AI-мозг", "Вариант Тьютора")
    page = page.replace(
        '<option value="openai">OpenAI</option><option value="qwen">Qwen</option><option value="yandex">Яндекс</option><option value="auto">Авто: OpenAI → Qwen → Яндекс</option>',
        '<option value="A">Вариант A</option><option value="B">Вариант B</option><option value="C">Вариант C</option><option value="D">Вариант D</option>',
    )
    page = page.replace(
        "const labels={openai:'OpenAI',qwen:'Qwen',yandex:'Яндекс',auto:'Авто'};",
        "const labels={A:'Вариант A',B:'Вариант B',C:'Вариант C',D:'Вариант D'};",
    )
    page = page.replace(
        "for(const k of ['openai','qwen','yandex'])",
        "for(const k of ['A','B','C','D'])",
    )
    page = page.replace(
        "Один интерфейс для сравнения трёх AI-мозгов и проверки автоматического переключения. Учебный контекст у всех одинаковый.",
        "Слепое сравнение: названия AI скрыты до окончания оценки. Учебный контекст и интерфейс у всех вариантов одинаковые.",
    )
    page = page.replace(
        "При отказе одного AI система продолжит ход через следующий backend.",
        "Название AI скрыто. Оценивайте только качество обучения и удобство диалога.",
    )
    voice_note = " Голосовой слой у всех вариантов одинаков: Yandex SpeechKit STT + Lera TTS." if speech_enabled else ""
    page = page.replace(
        "Текст можно вставлять до 12 000 символов. Голос ответа — Yandex Lera / neutral / 1.04.",
        "Текст можно вставлять до 12 000 символов." + voice_note,
    )
    page = page.replace(
        '<div class="brand">Eksamio</div>',
        f'<div class="brand">Eksamio · слепой тест · {test_id}</div>',
    )
    return page


class BlindApp(four.FourBrainApp):
    def __init__(self, *, alias_to_provider: dict[str, str], **kwargs: Any) -> None:
        super().__init__(simulated_unavailable=set(), **kwargs)
        self.alias_to_provider = dict(alias_to_provider)
        self.provider_to_alias = {provider: alias for alias, provider in self.alias_to_provider.items()}

    def provider_status(self) -> dict[str, dict[str, object]]:
        real = super().provider_status()
        return {
            alias: {
                "ready": bool(real[provider]["ready"]),
                "detail": "готов к тесту" if real[provider]["ready"] else "локальная конфигурация не готова",
            }
            for alias, provider in self.alias_to_provider.items()
        }

    def start(self, provider: str, semantic_id: str) -> dict[str, object]:
        real_provider = self.alias_to_provider.get(provider)
        if real_provider is None:
            raise ValueError("неизвестный слепой вариант")
        result = super().start(real_provider, semantic_id)
        public_session = result.get("session")
        if isinstance(public_session, str):
            with self.lock:
                session = self.sessions.get(public_session)
                if session is not None:
                    session.provider_mode = provider
        return result

    def _accept(self, session: base_ui.LiveSession, interaction: Any) -> dict[str, object]:
        provider_id = base_ui._provider_used(interaction)
        real_name = PROVIDER_ID_TO_NAME.get(provider_id)
        alias = self.provider_to_alias.get(real_name or "", "?")
        with self.lock:
            session.successful_turns += 1
            session.provider_counts[alias] = session.provider_counts.get(alias, 0) + 1
            turns = session.successful_turns
        return {
            "text": interaction.tutor_text,
            "brain_provider": f"Вариант {alias}",
            "turns": turns,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Blind Eksamio four-brain Tutor comparison")
    parser.add_argument("--owner-authorized", action="store_true")
    parser.add_argument("--enable-speech", action="store_true")
    parser.add_argument("--max-turns", type=int, default=20)
    parser.add_argument("--port", type=int, default=base_ui.DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.owner_authorized:
        print("PRIVATE_BLIND_TUTOR_UI=BLOCKED_OWNER_AUTHORIZATION")
        return 2
    if not 1 <= args.max_turns <= 20:
        print("PRIVATE_BLIND_TUTOR_UI=BLOCKED_MAX_TURNS")
        return 2
    if not 1024 <= args.port <= 65535:
        print("PRIVATE_BLIND_TUTOR_UI=BLOCKED_INVALID_PORT")
        return 2
    if _candidate_sha() is None:
        print("PRIVATE_BLIND_TUTOR_UI=BLOCKED_EXACT_CANDIDATE_SHA")
        return 2

    local = load_private_provider_config()
    test_id, mapping = _create_mapping()
    app = BlindApp(
        alias_to_provider=mapping,
        max_turns=args.max_turns,
        speech_enabled=args.enable_speech,
        qwen_base_url=local.qwen_base_url,
        yandex_folder_id=local.yandex_folder_id,
    )
    base_ui.PAGE = _blind_page(speech_enabled=args.enable_speech, test_id=test_id)
    base_ui.Handler.app = app
    server = base_ui.ThreadingHTTPServer((base_ui.HOST, args.port), base_ui.Handler)
    url = f"http://{base_ui.HOST}:{args.port}/"
    print(f"PRIVATE_BLIND_TUTOR_UI=READY {url}")
    print(f"BLIND_TEST_ID={test_id}")
    print("PROVIDER_MAPPING_HIDDEN=1")
    print("PUBLIC_TRAFFIC_ENABLED=0")
    print(f"SPEECH_ENABLED={int(args.enable_speech)}")
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
