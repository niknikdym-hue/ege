#!/usr/bin/env python3
"""Production browser surface on top of the authenticated PEIS runtime.

This adapter exposes the exact HTTP routes already consumed by the Eksamio Pro
client. It never creates a second learner model: identity comes from the
passwordless PostgreSQL session, learning comes from shared PEIS, and Pro access
is read from the accepted payment entitlement tables in the same PostgreSQL
substrate. Full Russian-program claims and production Tutor/payment execution
remain fail-closed.
"""
from __future__ import annotations

import json
import os
import sys
from http import cookies
from http.server import HTTPServer
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse

import runtime as core

PAYMENTS = core.ENGINE / "payments-reference"
if str(PAYMENTS) not in sys.path:
    sys.path.insert(0, str(PAYMENTS))

from entitlement_read import EntitlementReadError, ProEntitlementReader  # noqa: E402
from learner_views import RegisteredLearnerViews  # noqa: E402
from passwordless_identity import InvalidSession, PasswordlessIdentityService  # noqa: E402
from peis_service_bridge import ServiceRequestError  # noqa: E402
from registration_consent import RegistrationError  # noqa: E402
from russian_exceptions_practice_adapter import RussianExceptionsPracticeAdapter  # noqa: E402

SESSION_COOKIE = PasswordlessIdentityService.SESSION_COOKIE_NAME
READ_PATHS = {
    "/api/identity/session",
    "/api/payments/entitlement",
    "/api/russian/profile",
    "/api/russian/plan",
    "/api/russian/history",
    "/api/russian/practice/next",
    "/api/russian/program",
}
POST_PATHS = {
    "/api/identity/logout",
    "/api/consent/marketing/revoke",
    "/api/russian/practice/submit",
    "/api/tutor/turn",
}


def _session_token(cookie_header: str | None) -> str | None:
    jar = cookies.SimpleCookie()
    try:
        jar.load(cookie_header or "")
    except cookies.CookieError:
        return None
    morsel = jar.get(SESSION_COOKIE)
    return morsel.value if morsel and morsel.value else None


def make_handler(
    runtime: core.Runtime,
    views: RegisteredLearnerViews | None,
    entitlements: ProEntitlementReader | None = None,
):
    Base = core.make_handler(runtime)

    class Handler(Base):
        server_version = "EksamioLearnerWeb/0.2"

        def _cors(self) -> dict[str, str] | None:
            if not runtime.origin_allowed(self.request_headers()):
                self.send_json(403, {"error": "ORIGIN_NOT_ALLOWED"})
                return None
            return runtime.cors_headers()

        def _host(self, cors: Mapping[str, str]):
            try:
                return runtime.authenticated_host(self.headers.get("Cookie"))
            except InvalidSession:
                self.send_json(401, {"error": "AUTHENTICATION_REQUIRED"}, extra_headers=cors)
            except RuntimeError:
                self.send_json(503, {"error": "IDENTITY_UNAVAILABLE"}, extra_headers=cors)
            return None

        def _require_views(self, cors: Mapping[str, str]) -> RegisteredLearnerViews | None:
            if views is None:
                self.send_json(503, {"error": "LEARNER_STATE_UNAVAILABLE"}, extra_headers=cors)
                return None
            return views

        def do_OPTIONS(self):  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path not in READ_PATHS | POST_PATHS:
                super().do_OPTIONS()
                return
            cors = self._cors()
            if cors is None:
                return
            expected_method = "GET" if path in READ_PATHS else "POST"
            requested_method = self.headers.get("Access-Control-Request-Method")
            requested_headers = (self.headers.get("Access-Control-Request-Headers") or "").casefold()
            if requested_method != expected_method or any(
                item.strip() not in {"", "content-type"}
                for item in requested_headers.split(",")
            ):
                self.send_json(403, {"error": "PREFLIGHT_NOT_ALLOWED"}, extra_headers=cors)
                return
            self.send_response(204)
            for name, value in cors.items():
                self.send_header(name, value)
            self.send_header("Access-Control-Allow-Methods", f"{expected_method}, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self):  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            if path not in READ_PATHS:
                super().do_GET()
                return
            cors = self._cors()
            if cors is None:
                return

            if path == "/api/identity/session":
                try:
                    runtime.authenticated_host(self.headers.get("Cookie"))
                except InvalidSession:
                    self.send_json(200, {"authenticated": False}, extra_headers=cors)
                    return
                except RuntimeError:
                    self.send_json(503, {"error": "IDENTITY_UNAVAILABLE"}, extra_headers=cors)
                    return
                self.send_json(
                    200,
                    {"authenticated": True, "identity_owner": "server"},
                    extra_headers=cors,
                )
                return

            host = self._host(cors)
            if host is None:
                return

            if path == "/api/payments/entitlement":
                if entitlements is None:
                    self.send_json(503, {"error": "ENTITLEMENT_UNAVAILABLE"}, extra_headers=cors)
                    return
                try:
                    self.send_json(
                        200,
                        entitlements.status(host.learner_profile_id),
                        extra_headers=cors,
                    )
                except EntitlementReadError:
                    self.send_json(400, {"error": "INVALID_REQUEST"}, extra_headers=cors)
                except Exception:
                    self.send_json(503, {"error": "ENTITLEMENT_UNAVAILABLE"}, extra_headers=cors)
                return

            learner_views = self._require_views(cors)
            if learner_views is None:
                return

            if path == "/api/russian/program":
                self.send_json(
                    503,
                    {
                        "error": "RUSSIAN_FULL_SUBJECT_NOT_ADMITTED",
                        "detail": "Full Russian program remains fail-closed until subject acceptance.",
                    },
                    extra_headers=cors,
                )
                return

            query = parse_qs(parsed.query)
            try:
                grade = int(query.get("grade", ["10"])[0])
                route = str(query.get("route", ["ege"])[0])
                if path == "/api/russian/profile":
                    value: Any = learner_views.profile(
                        host.learner_profile_id,
                        grade=grade,
                        route=route,
                    )
                elif path == "/api/russian/plan":
                    value = learner_views.plan(
                        host.learner_profile_id,
                        grade=grade,
                        route=route,
                    )
                elif path == "/api/russian/history":
                    value = learner_views.history(host.learner_profile_id)
                else:
                    value = learner_views.practice_card(host.learner_profile_id)
                self.send_json(200, value, extra_headers=cors)
            except (ServiceRequestError, ValueError, TypeError):
                self.send_json(400, {"error": "INVALID_REQUEST"}, extra_headers=cors)
            except Exception:
                self.send_json(503, {"error": "LEARNER_STATE_UNAVAILABLE"}, extra_headers=cors)

        def do_POST(self):  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path not in POST_PATHS:
                super().do_POST()
                return
            cors = self._cors()
            if cors is None:
                return

            if path == "/api/identity/logout":
                token = _session_token(self.headers.get("Cookie"))
                status = "ALREADY_LOGGED_OUT"
                if token and runtime.identity_service is not None:
                    try:
                        status = runtime.identity_service.logout(token)
                    except InvalidSession:
                        status = "ALREADY_LOGGED_OUT"
                self.send_json(
                    200,
                    {"status": status},
                    extra_headers={
                        **cors,
                        "Set-Cookie": PasswordlessIdentityService.clear_session_cookie(),
                    },
                )
                return

            host = self._host(cors)
            if host is None:
                return
            token = _session_token(self.headers.get("Cookie"))
            if token is None:
                self.send_json(401, {"error": "AUTHENTICATION_REQUIRED"}, extra_headers=cors)
                return

            if path == "/api/tutor/turn":
                self.send_json(
                    503,
                    {"error": "TUTOR_PROVIDER_NOT_ADMITTED"},
                    extra_headers=cors,
                )
                return

            try:
                payload = self.read_json_object()
            except (ServiceRequestError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
                self.send_json(400, {"error": "INVALID_REQUEST"}, extra_headers=cors)
                return

            if path == "/api/consent/marketing/revoke":
                registration_service = (
                    runtime.registration_boundary.registration_service
                    if runtime.registration_boundary is not None
                    else None
                )
                if registration_service is None:
                    self.send_json(503, {"error": "IDENTITY_UNAVAILABLE"}, extra_headers=cors)
                    return
                if set(payload) != {"document_version", "text_version", "client_request_id"}:
                    self.send_json(400, {"error": "INVALID_REQUEST"}, extra_headers=cors)
                    return
                try:
                    result = registration_service.revoke_marketing(
                        session_token=token,
                        document_version=payload["document_version"],
                        text_version=payload["text_version"],
                        client_request_id=payload["client_request_id"],
                    )
                    self.send_json(200, result, extra_headers=cors)
                except (RegistrationError, ValueError, TypeError):
                    self.send_json(400, {"error": "INVALID_REQUEST"}, extra_headers=cors)
                except InvalidSession:
                    self.send_json(401, {"error": "AUTHENTICATION_REQUIRED"}, extra_headers=cors)
                except Exception:
                    self.send_json(503, {"error": "CONSENT_WRITE_UNAVAILABLE"}, extra_headers=cors)
                return

            learner_views = self._require_views(cors)
            if learner_views is None:
                return
            if not runtime.writes_enabled:
                self.send_json(503, {"error": "PEIS_WRITES_DISABLED"}, extra_headers=cors)
                return
            try:
                result = learner_views.submit_practice(host, payload)
                self.send_json(200, result, extra_headers=cors)
            except core.IntegrityConflict:
                self.send_json(409, {"error": "INTEGRITY_CONFLICT"}, extra_headers=cors)
            except (ServiceRequestError, ValueError, TypeError):
                self.send_json(400, {"error": "INVALID_REQUEST"}, extra_headers=cors)
            except Exception:
                self.send_json(503, {"error": "LEARNER_WRITE_UNAVAILABLE"}, extra_headers=cors)

    return Handler


def main() -> int:
    dsn = os.environ["PEIS_DATABASE_DSN"]
    evidence = json.loads(
        (core.ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text()
    )
    nba = json.loads(
        (core.ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text()
    )
    try:
        store: Any = core.PostgresPeisPersistenceStore(
            dsn,
            evidence_schema=evidence,
            nba_schema=nba,
        )
    except Exception:
        store = core.UnreadyStore()

    runtime = core.build_runtime_from_env(store)
    views: RegisteredLearnerViews | None = None
    entitlements: ProEntitlementReader | None = None
    if not isinstance(store, core.UnreadyStore):
        try:
            adapter = RussianExceptionsPracticeAdapter(core.ENGINE)
            views = RegisteredLearnerViews(
                store=store,
                bridge=runtime.bridge,
                adapter=adapter,
            )
            entitlements = ProEntitlementReader(store.connection)
        except Exception:
            views = None
            entitlements = None

    server = HTTPServer(
        (
            os.getenv("PEIS_BIND_HOST", "0.0.0.0"),
            int(os.getenv("PEIS_PORT", "8080")),
        ),
        make_handler(runtime, views, entitlements),
    )
    server.host_identity = None
    try:
        server.serve_forever()
    finally:
        server.server_close()
        close = getattr(store, "close", None)
        if callable(close):
            close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
