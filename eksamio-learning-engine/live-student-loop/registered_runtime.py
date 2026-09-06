#!/usr/bin/env python3
"""Registered-only owner-test transport for the live student loop.

This file deliberately reuses the accepted PEIS/NBA/Tutor engine from runtime.py
but replaces its legacy anonymous HTTP admission. It is loopback-only and is NOT
the production registration transport: production registration/consent is owned by
registration_http.py from PR #186.
"""
from __future__ import annotations

import json
import mimetypes
import os
import sys
import time
from http.server import HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import runtime as legacy

REPORTING_TIMEZONE = ZoneInfo("Europe/Moscow")
# Keep the existing regression contract addressable through the reused runtime
# module while the registered-only path owns the corrected reporting behavior.
legacy.REPORTING_TIMEZONE = REPORTING_TIMEZONE


class RegisteredLiveStudentLoop(legacy.LiveStudentLoop):
    """Same learner engine, but owner-test login never receives an anonymous host."""

    def _create_loop_schema(self) -> None:
        super()._create_loop_schema()
        duplicate = self.store.connection.execute(
            """
            SELECT learner_profile_id, card_id, COUNT(*) AS n
            FROM tutor_contexts
            WHERE status = 'VERIFICATION_REQUIRED'
            GROUP BY learner_profile_id, card_id
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        ).fetchone()
        if duplicate is not None:
            raise RuntimeError("multiple pending Tutor contexts require explicit repair")
        with self.store.connection:
            self.store.connection.execute("DROP INDEX IF EXISTS idx_tutor_context_error")
            self.store.connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_tutor_context_pending_card
                ON tutor_contexts(learner_profile_id, card_id)
                WHERE status = 'VERIFICATION_REQUIRED'
                """
            )

    def owner_test_login(self) -> tuple[dict[str, Any], str]:
        if not self.owner_test:
            raise PermissionError("OWNER_MODE_DISABLED")
        receipt = self.identity.begin(
            {"channel": "email", "contact": "owner-test@learner.invalid"},
            anonymous_host_token=None,
        )
        auth = self.identity.verify(
            {"challenge_id": receipt.challenge_id, "code": self.delivery.code_for(receipt.challenge_id)}
        )
        return (
            {
                "authenticated": True,
                "display_label": "Тестовый зарегистрированный ученик",
                "identity_owner": "server",
                "owner_test": True,
            },
            legacy._loopback_cookie(legacy.SESSION_COOKIE, auth.token, max_age=30 * 24 * 60 * 60),
        )

    def tutor_turn(self, host: Any, message: str) -> dict[str, Any]:
        if not isinstance(message, str) or not message.strip():
            raise legacy.ServiceRequestError("Tutor message is required")

        events = self.store.list_events(
            host.learner_profile_id,
            "russian",
            semantic_id=legacy.EXACT_SEMANTIC_ID,
        )
        wrong = next(
            (
                event
                for event in reversed(events)
                if event["source"]["object_id"] == legacy.FIRST_SLICE_CARD_ID
                and event["result"]["outcome"] == "INCORRECT"
            ),
            None,
        )
        if wrong is None:
            raise legacy.ServiceRequestError("No exact accepted error is available for Tutor context")

        pending = self.pending_tutor_context(
            host.learner_profile_id,
            legacy.FIRST_SLICE_CARD_ID,
        )
        if pending is not None:
            context_id = str(pending["context_id"])
            pending_wrong = self.store.raw_event(str(pending["error_event_id"]))
            if pending_wrong is not None:
                wrong = pending_wrong
        else:
            row = self.store.connection.execute(
                """
                SELECT COUNT(*) AS n
                FROM tutor_contexts
                WHERE learner_profile_id = ? AND card_id = ?
                """,
                (host.learner_profile_id, legacy.FIRST_SLICE_CARD_ID),
            ).fetchone()
            lineage = int(row["n"]) + 1
            context_id = "tutorctx." + legacy._digest(
                host.learner_profile_id
                + "|"
                + wrong["event_id"]
                + "|lineage:"
                + str(lineage)
            )

        help_event_id = self._append_tutor_help(host, wrong, context_id)
        now_epoch = int(time.time())
        with self.store.connection:
            self.store.connection.execute(
                """
                INSERT INTO tutor_contexts(
                    context_id, learner_profile_id, card_id, error_event_id,
                    help_event_id, status, created_at, helped_at_epoch, verified_event_id
                ) VALUES (?, ?, ?, ?, ?, 'VERIFICATION_REQUIRED', ?, ?, NULL)
                ON CONFLICT(context_id) DO NOTHING
                """,
                (
                    context_id,
                    host.learner_profile_id,
                    legacy.FIRST_SLICE_CARD_ID,
                    wrong["event_id"],
                    help_event_id,
                    legacy._utc_now(),
                    now_epoch,
                ),
            )

        answer = wrong["result"].get("response_value")
        explanation = self.practice["feedback"]["why"]
        correct_answer = self.practice["answer"]["text"]
        return {
            "status": "TUTOR_ADVISORY_STAGING",
            "provider_mode": "DETERMINISTIC_STAGING_NO_AI",
            "context_id": context_id,
            "card_id": legacy.FIRST_SLICE_CARD_ID,
            "answer_received": answer,
            "error_event_id": wrong["event_id"],
            "accepted_source_refs": [
                f"source:russian-reviewed-card:{legacy.FIRST_SLICE_CARD_ID}"
            ],
            "verification_required": True,
            "text": (
                f"Вижу вашу ошибку в слове «{answer or '—'}». "
                f"{explanation} Проверочный ориентир — «{correct_answer}». "
                "Теперь выполните новое задание самостоятельно."
            ),
        }

    def profile(self, learner_profile_id: str, *, grade: int, route: str) -> dict[str, Any]:
        profile = super().profile(learner_profile_id, grade=grade, route=route)
        reporting_day = legacy.datetime.now(REPORTING_TIMEZONE).date()
        events = self.store.list_events(learner_profile_id, "russian")
        attempts = []

        for event in events:
            if event["result"]["outcome"] not in {"CORRECT", "INCORRECT", "PARTIAL"}:
                continue
            raw = event["timestamps"].get("received_at_server")
            if not isinstance(raw, str) or not raw:
                continue
            received = legacy.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if received.tzinfo is None:
                received = received.replace(tzinfo=legacy.timezone.utc)
            if received.astimezone(REPORTING_TIMEZONE).date() == reporting_day:
                attempts.append(event)

        correct = sum(
            event["result"]["outcome"] == "CORRECT"
            for event in attempts
        )
        errors = sum(
            event["result"]["outcome"] == "INCORRECT"
            for event in attempts
        )
        profile["today"] = {
            "solved": len(attempts),
            "correct": correct,
            "errors": errors,
            "review": errors,
        }
        profile["reporting_timezone"] = REPORTING_TIMEZONE.key
        return profile


class RegisteredLoopHandler(legacy.LiveLoopHandler):
    server_version = "EksamioRegisteredLiveStudentLoop/0.1"

    @property
    def app(self) -> RegisteredLiveStudentLoop:
        return self.server.app  # type: ignore[attr-defined]

    def _authenticated_host(self, *, required: bool) -> Any | None:
        session, _ignored_anonymous = self._cookies()
        if not session:
            if required:
                raise PermissionError("AUTHENTICATION_REQUIRED")
            return None
        try:
            return self.app.identity.resolve_session(session)
        except legacy.InvalidSession:
            if required:
                raise PermissionError("AUTHENTICATION_REQUIRED")
            return None

    def _serve_pro(self, relative: str) -> None:
        relative = relative or "index.html"
        if relative == "index.html":
            html = (legacy.PRO_CLIENT / "index.html").read_text(encoding="utf-8")
            config = (
                '<script>window.EKSAMIO_PRO_RUNTIME_CONFIG={'
                'mode:"http",baseUrl:"",ownerTest:true,'
                'registrationUrl:"/owner-test/registration"};</script>'
            )
            html = html.replace('<script src="adapters.js"></script>', config + '<script src="adapters.js"></script>')
            self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return
        path = (legacy.PRO_CLIENT / relative).resolve()
        if legacy.PRO_CLIENT.resolve() not in path.parents or not path.is_file():
            self._json(404, {"error": "NOT_FOUND"})
            return
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self._send(200, path.read_bytes(), mime)

    def _serve_trainer(self) -> None:
        config = (
            '<script>window.EKSAMIO_LEARNER_LOOP_CONFIG={'
            'enabled:true,baseUrl:"",proUrl:"/pro/?owner_test=1",'
            'registrationUrl:"/owner-test/registration",ownerTest:true};</script>'
        )
        blocks = []
        for number in legacy.TILDA_BLOCKS:
            path = legacy.TRAINER / f"ege-russkiy-trenazher-T123-{number}.txt"
            blocks.append(path.read_text(encoding="utf-8").strip())
        html = (
            '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Тренажёр ЕГЭ — registered owner test</title></head>'
            '<body style="margin:0">' + config + "\n".join(blocks) + "</body></html>"
        )
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def _serve_owner_test_registration(self) -> None:
        if not self.app.owner_test:
            raise PermissionError("OWNER_MODE_DISABLED")
        # Deliberately not a consent simulation. Real legal/registration UI is #186.
        html = """<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Eksamio owner-test login</title></head><body style="font-family:Arial,sans-serif;max-width:680px;margin:40px auto;padding:0 20px"><h1>OWNER TEST — зарегистрированный профиль</h1><p>Эта loopback-страница не имитирует юридические согласия и не является production-регистрацией. Она создаёт только тестовую server-owned сессию без anonymous continuity.</p><button id="login" style="padding:12px 18px">Создать тестовую сессию</button><p id="status"></p><script>document.getElementById('login').onclick=async()=>{const r=await fetch('/api/identity/owner-test-login',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:'{}'});document.getElementById('status').textContent=r.ok?'Сессия создана. Открываю Мой Eksamio…':'Ошибка owner-test login';if(r.ok)location.assign('/pro/#plan');};</script></body></html>"""
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def _do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/trainer", "/trainer/"}:
            self._serve_trainer()
            return
        if parsed.path.startswith("/pro/"):
            self._serve_pro(parsed.path.removeprefix("/pro/"))
            return
        if parsed.path in {"/owner-test/registration", "/owner-test/registration/"}:
            self._serve_owner_test_registration()
            return
        if parsed.path == "/healthz":
            self._json(200, {"status": "ok", "mode": "REGISTERED_STAGING_LOOPBACK_ONLY", "canonical_state_owner": "server", "anonymous_progress": False})
            return
        if parsed.path == "/api/identity/session":
            host = self._authenticated_host(required=False)
            self._json(200, {
                "authenticated": host is not None,
                "display_label": "Тестовый зарегистрированный ученик" if host is not None else "Вход не выполнен",
                "identity_owner": "server",
            })
            return
        if parsed.path == "/api/russian/program":
            self._send(200, (legacy.PRO_CLIENT / "program-catalog.json").read_bytes(), "application/json; charset=utf-8")
            return
        if parsed.path in {"/api/russian/profile", "/api/russian/plan", "/api/russian/history", "/api/owner/diagnostics", "/api/russian/practice/next", "/api/payments/entitlement"}:
            host = self._authenticated_host(required=True)
            query = parse_qs(parsed.query)
            grade = int(query.get("grade", ["10"])[0])
            route = query.get("route", ["ege"])[0]
            if parsed.path == "/api/russian/profile":
                value = self.app.profile(host.learner_profile_id, grade=grade, route=route)
            elif parsed.path == "/api/russian/plan":
                value = self.app.plan(host.learner_profile_id, grade=grade, route=route)
            elif parsed.path == "/api/russian/history":
                value = self.app.history(host.learner_profile_id)
            elif parsed.path == "/api/owner/diagnostics":
                if not self.app.owner_test:
                    raise PermissionError("OWNER_MODE_DISABLED")
                value = self.app.diagnostics(host.learner_profile_id)
            elif parsed.path == "/api/russian/practice/next":
                value = self.app.practice_card(host.learner_profile_id)
            else:
                value = {"active": True, "test_account": True, "commercial_entitlement": False, "state": "OWNER_TEST_ONLY"}
            self._json(200, value)
            return
        self._json(404, {"error": "NOT_FOUND"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._check_origin()
            parsed = urlparse(self.path)
            if parsed.path == "/api/identity/owner-test-login":
                value, session_cookie = self.app.owner_test_login()
                self._json(200, value, set_cookies=[session_cookie])
                return
            if parsed.path == "/api/identity/logout":
                session, _ = self._cookies()
                self.app.logout(session)
                self._json(200, {"status": "LOGGED_OUT"}, set_cookies=[legacy._loopback_cookie(legacy.SESSION_COOKIE, "", max_age=0)])
                return
            if parsed.path in {"/v0/checked-card", "/api/peis/checked-card"}:
                host = self._authenticated_host(required=True)
                self._json(200, self.app.submit_trainer(self._body(), host))
                return
            if parsed.path == "/api/russian/practice/submit":
                host = self._authenticated_host(required=True)
                self._json(200, self.app.submit_practice(host, self._body()))
                return
            if parsed.path == "/api/tutor/turn":
                host = self._authenticated_host(required=True)
                payload = self._body()
                if set(payload) != {"message", "card_id"} or payload.get("card_id") != legacy.FIRST_SLICE_CARD_ID:
                    raise legacy.ServiceRequestError("Tutor client may send only message and admitted card_id")
                self._json(200, self.app.tutor_turn(host, str(payload["message"])))
                return
            self._json(404, {"error": "NOT_FOUND"})
        except PermissionError as exc:
            self._json(401, {"error": str(exc)})
        except (legacy.ServiceRequestError, legacy.UnknownAdapter, ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._json(400, {"error": "INVALID_REQUEST", "detail": str(exc)})
        except legacy.IntegrityConflict:
            self._json(409, {"error": "INTEGRITY_CONFLICT"})
        except Exception:
            self._json(503, {"error": "PROGRESS_TEMPORARILY_NOT_SYNCED"})


class RegisteredLoopServer(HTTPServer):
    def __init__(self, address: tuple[str, int], app: RegisteredLiveStudentLoop):
        if address[0] not in {"127.0.0.1", "localhost"}:
            raise ValueError("owner-test server may bind only to loopback")
        super().__init__(address, RegisteredLoopHandler)
        self.app = app


def _staging_secret() -> bytes:
    value = os.environ.get("EKSAMIO_STAGING_HMAC_KEY", "")
    if not value and os.environ.get("EKSAMIO_STAGING_SECRET_STDIN") == "1":
        value = sys.stdin.readline().strip()
    return value.encode("utf-8")


def main() -> int:
    key = _staging_secret()
    database = os.environ.get("EKSAMIO_STAGING_DB", "")
    host = os.environ.get("EKSAMIO_STAGING_HOST", "127.0.0.1")
    if len(key) < 32 or not database:
        print("staging secret (32+ bytes) and EKSAMIO_STAGING_DB are required", file=sys.stderr)
        return 2
    if host not in {"127.0.0.1", "localhost"}:
        print("registered owner-test runtime is loopback-only", file=sys.stderr)
        return 2
    port = int(os.environ.get("EKSAMIO_STAGING_PORT", "8782"))
    app = RegisteredLiveStudentLoop(Path(database), key, owner_test=True)
    server = RegisteredLoopServer((host, port), app)
    print(f"EKSAMIO_REGISTERED_STUDENT_LOOP_STAGING=http://{host}:{port}/trainer/")
    try:
        server.serve_forever()
    finally:
        server.server_close()
        app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
