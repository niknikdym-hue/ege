#!/usr/bin/env python3
"""Authenticated page gate for the registered-only owner staging runtime."""
from __future__ import annotations

import json
import os
import sys
from http.server import HTTPServer
from pathlib import Path
from urllib.parse import urlparse

import registered_runtime as registered


class GatedRegisteredLoopHandler(registered.RegisteredLoopHandler):
    server_version = "EksamioGatedRegisteredLiveStudentLoop/0.1"

    def _serve_registration_required(self) -> None:
        html = """<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Eksamio — требуется вход</title></head><body style="font-family:Arial,sans-serif;max-width:680px;margin:40px auto;padding:0 20px"><h1>Войдите, чтобы начать учебную работу</h1><p>До входа тренажёр не создаёт учебные попытки, PEIS-события или прогресс. После входа все действия относятся к одному server-owned профилю ученика.</p><a id="registered-entry" href="/owner-test/registration" style="display:inline-block;padding:12px 18px;border-radius:10px;background:#2F80FF;color:#fff;text-decoration:none;font-weight:700">Войти в Мой Eksamio</a></body></html>"""
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def _serve_trainer(self) -> None:
        if self._authenticated_host(required=False) is None:
            self._serve_registration_required()
            return
        super()._serve_trainer()

    def _serve_owner_test_registration(self) -> None:
        if not self.app.owner_test:
            raise PermissionError("OWNER_MODE_DISABLED")
        html = """<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Eksamio owner-test login</title></head><body style="font-family:Arial,sans-serif;max-width:680px;margin:40px auto;padding:0 20px"><h1>OWNER TEST — зарегистрированный профиль</h1><p>Эта loopback-страница не является production-регистрацией и не имитирует юридические согласия. Production registration/consent authority — registration_http.py из PR #186.</p><button id="login" style="padding:12px 18px">Создать тестовую сессию</button><p id="status"></p><script>document.getElementById('login').onclick=async()=>{const r=await fetch('/api/identity/owner-test-login',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:'{}'});document.getElementById('status').textContent=r.ok?'Сессия создана. Открываю тренажёр…':'Ошибка owner-test login';if(r.ok)location.assign('/trainer/');};</script></body></html>"""
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def _do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            self._json(200, {
                "status": "ok",
                "mode": "REGISTERED_GATED_STAGING_LOOPBACK_ONLY",
                "canonical_state_owner": "server",
                "anonymous_progress": False,
                "learning_requires_authentication": True,
            })
            return
        super()._do_GET()


class GatedRegisteredLoopServer(HTTPServer):
    def __init__(self, address: tuple[str, int], app: registered.RegisteredLiveStudentLoop):
        if address[0] not in {"127.0.0.1", "localhost"}:
            raise ValueError("owner-test server may bind only to loopback")
        super().__init__(address, GatedRegisteredLoopHandler)
        self.app = app


def main() -> int:
    key = registered._staging_secret()
    database = os.environ.get("EKSAMIO_STAGING_DB", "")
    host = os.environ.get("EKSAMIO_STAGING_HOST", "127.0.0.1")
    if len(key) < 32 or not database:
        print("staging secret (32+ bytes) and EKSAMIO_STAGING_DB are required", file=sys.stderr)
        return 2
    if host not in {"127.0.0.1", "localhost"}:
        print("registered owner-test runtime is loopback-only", file=sys.stderr)
        return 2
    port = int(os.environ.get("EKSAMIO_STAGING_PORT", "8782"))
    app = registered.RegisteredLiveStudentLoop(Path(database), key, owner_test=True)
    server = GatedRegisteredLoopServer((host, port), app)
    print(f"EKSAMIO_REGISTERED_GATED_STUDENT_LOOP_STAGING=http://{host}:{port}/trainer/")
    try:
        server.serve_forever()
    finally:
        server.server_close()
        app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
