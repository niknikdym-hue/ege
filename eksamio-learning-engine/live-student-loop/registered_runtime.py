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
from http.server import HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import runtime as legacy


class RegisteredLiveStudentLoop(legacy.LiveStudentLoop):
    """Same learner engine, but owner-test login never receives an anonymous host."""

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
