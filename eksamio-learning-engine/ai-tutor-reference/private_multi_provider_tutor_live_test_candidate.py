#!/usr/bin/env python3
"""Private Tutor live-test candidate with metadata-only local evidence.

The base local UI stays unchanged. This wrapper replaces only its App class so
/api/finish writes an exact-build acceptance record without learner/Tutor text,
audio, session tokens, learner identifiers, or provider secrets.
"""
from __future__ import annotations

import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import private_multi_provider_tutor_test_ui as ui

EVIDENCE_SCHEMA = "eksamio.tutor.private-live-test-evidence.v1"
ALLOWED_EVIDENCE_KEYS = frozenset(
    {
        "schema_version",
        "evidence_id",
        "candidate_sha",
        "started_at_utc",
        "finished_at_utc",
        "semantic_id",
        "provider_mode",
        "successful_turns",
        "max_turns",
        "provider_counts",
        "speech_enabled",
        "local_only",
        "public_traffic_enabled",
        "production_peis_writes_enabled",
        "learner_text_persisted",
        "tutor_text_persisted",
        "raw_audio_persisted_bytes",
        "provider_secret_values_persisted",
    }
)
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _candidate_sha() -> str:
    value = os.environ.get("EKSAMIO_TUTOR_CANDIDATE_SHA", "").strip().lower()
    if not _SHA40.fullmatch(value):
        raise RuntimeError("private live-test candidate SHA is unavailable or invalid")
    return value


def _evidence_dir() -> Path:
    configured = os.environ.get("EKSAMIO_TUTOR_TEST_EVIDENCE_DIR", "").strip()
    root = Path(configured).expanduser() if configured else Path.home() / "Library" / "Application Support" / "Eksamio" / "TutorLiveTests"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    return root


def _write_evidence(payload: dict[str, Any]) -> Path:
    if set(payload) != ALLOWED_EVIDENCE_KEYS:
        raise RuntimeError("private live-test evidence field allowlist drift")
    root = _evidence_dir()
    path = root / f"{payload['evidence_id']}.json"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink(missing_ok=True)
        finally:
            raise
    return path


class EvidenceApp(ui.App):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._evidence_sessions: dict[str, tuple[str, str]] = {}

    def start(self, provider: str, semantic_id: str) -> dict[str, object]:
        result = super().start(provider, semantic_id)
        public_session = result.get("session")
        if not isinstance(public_session, str) or not public_session:
            raise RuntimeError("private live-test session identity missing")
        with self.lock:
            self._evidence_sessions[public_session] = (
                "tutor-live-" + secrets.token_hex(8),
                _utc_now(),
            )
        return result

    def finish(self, public_session: str) -> dict[str, object]:
        with self.lock:
            session = self.sessions.pop(public_session, None)
            evidence_state = self._evidence_sessions.pop(public_session, None)
        if session is None:
            raise ValueError("тестовая сессия не найдена")
        if evidence_state is None:
            raise RuntimeError("private live-test evidence identity missing")
        evidence_id, started_at = evidence_state
        provider_counts = dict(sorted(session.provider_counts.items()))
        payload: dict[str, Any] = {
            "schema_version": EVIDENCE_SCHEMA,
            "evidence_id": evidence_id,
            "candidate_sha": _candidate_sha(),
            "started_at_utc": started_at,
            "finished_at_utc": _utc_now(),
            "semantic_id": session.semantic_id,
            "provider_mode": session.provider_mode,
            "successful_turns": session.successful_turns,
            "max_turns": session.max_turns,
            "provider_counts": provider_counts,
            "speech_enabled": bool(self.speech_enabled),
            "local_only": True,
            "public_traffic_enabled": False,
            "production_peis_writes_enabled": False,
            "learner_text_persisted": False,
            "tutor_text_persisted": False,
            "raw_audio_persisted_bytes": 0,
            "provider_secret_values_persisted": False,
        }
        _write_evidence(payload)
        counts = ", ".join(f"{name}: {count}" for name, count in provider_counts.items()) or "ответов нет"
        return {
            "turns": session.successful_turns,
            "provider_counts_text": f"Backend: {counts}.",
            "evidence_saved": True,
            "evidence_id": evidence_id,
        }


def main() -> int:
    ui.App = EvidenceApp
    return ui.main()


if __name__ == "__main__":
    raise SystemExit(main())
