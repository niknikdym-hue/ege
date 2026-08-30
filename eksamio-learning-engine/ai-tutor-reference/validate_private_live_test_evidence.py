#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import stat
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

import private_multi_provider_tutor_live_test_candidate as candidate
import private_multi_provider_tutor_test_ui as ui


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    app = object.__new__(candidate.EvidenceApp)
    app.max_turns = 20
    app.speech_enabled = False
    app.qwen_base_url = None
    app.yandex_folder_id = None
    app.sessions = {}
    app.lock = threading.Lock()
    app.topics = []
    app._evidence_sessions = {}

    public_session = "PUBLIC_SESSION_MUST_NOT_PERSIST"
    tutor_session_ref = "tutor:TUTOR_SESSION_MUST_NOT_PERSIST"
    evidence_id = "tutor-live-evidence-fixture"
    app.sessions[public_session] = ui.LiveSession(
        assembly=None,  # type: ignore[arg-type]
        tutor_session_ref=tutor_session_ref,
        provider_mode="auto",
        semantic_id="ru-expressive-epithet",
        max_turns=20,
        successful_turns=4,
        provider_counts={"openai": 3, "qwen": 1},
    )
    app._evidence_sessions[public_session] = (evidence_id, "2026-08-30T00:00:00Z")

    with tempfile.TemporaryDirectory() as tmp:
        evidence_dir = Path(tmp) / "TutorLiveTests"
        with patch.dict(
            os.environ,
            {
                "EKSAMIO_TUTOR_TEST_EVIDENCE_DIR": str(evidence_dir),
                "EKSAMIO_TUTOR_CANDIDATE_SHA": "a" * 40,
            },
            clear=False,
        ):
            result = app.finish(public_session)

        require(result["turns"] == 4, "finish turn count drift")
        require(result["evidence_saved"] is True, "finish must report evidence saved")
        require(result["evidence_id"] == evidence_id, "evidence identity drift")
        files = list(evidence_dir.glob("*.json"))
        require(len(files) == 1, "exactly one evidence record expected")
        path = files[0]
        payload = json.loads(path.read_text(encoding="utf-8"))

        require(set(payload) == candidate.ALLOWED_EVIDENCE_KEYS, "evidence keys escaped allowlist")
        require(payload["schema_version"] == candidate.EVIDENCE_SCHEMA, "evidence schema drift")
        require(payload["candidate_sha"] == "a" * 40, "candidate SHA missing")
        require(payload["semantic_id"] == "ru-expressive-epithet", "semantic identity missing")
        require(payload["provider_mode"] == "auto", "provider mode missing")
        require(payload["successful_turns"] == 4 and payload["max_turns"] == 20, "turn evidence drift")
        require(payload["provider_counts"] == {"openai": 3, "qwen": 1}, "provider count evidence drift")
        require(payload["speech_enabled"] is False, "first evidence fixture must remain text-only")
        require(payload["local_only"] is True, "local-only boundary missing")
        require(payload["public_traffic_enabled"] is False, "public traffic boundary drift")
        require(payload["production_peis_writes_enabled"] is False, "production PEIS boundary drift")
        require(payload["learner_text_persisted"] is False, "learner text persistence boundary drift")
        require(payload["tutor_text_persisted"] is False, "Tutor text persistence boundary drift")
        require(payload["raw_audio_persisted_bytes"] == 0, "raw audio persistence boundary drift")
        require(payload["provider_secret_values_persisted"] is False, "secret persistence boundary drift")

        serialized = json.dumps(payload, ensure_ascii=False)
        for forbidden in (public_session, tutor_session_ref, "learner_profile", "api_key", "audio_b64"):
            require(forbidden not in serialized, f"forbidden private material persisted: {forbidden}")

        require(stat.S_IMODE(evidence_dir.stat().st_mode) == 0o700, "evidence directory must be mode 0700")
        require(stat.S_IMODE(path.stat().st_mode) == 0o600, "evidence file must be mode 0600")

        try:
            candidate._candidate_sha()
        except RuntimeError:
            pass
        else:
            raise AssertionError("invalid candidate SHA must fail closed")

    print("PRIVATE_LIVE_TEST_EVIDENCE=PASS")
    print("EVIDENCE_METADATA_ONLY=PASS")
    print("EVIDENCE_BUILD_SHA_REQUIRED=PASS")
    print("LEARNER_TEXT_PERSISTED=0")
    print("TUTOR_TEXT_PERSISTED=0")
    print("RAW_AUDIO_PERSISTED_BYTES=0")
    print("PROVIDER_SECRET_VALUES_PERSISTED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
