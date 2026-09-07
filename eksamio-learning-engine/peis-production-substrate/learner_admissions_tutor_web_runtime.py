#!/usr/bin/env python3
"""Authenticated learner runtime + Tutor + bounded exact-event Admissions Gate.

This is the production-shaped successor entrypoint to learner_tutor_web_runtime.
It preserves all accepted #186 registration/session/PEIS/Tutor boundaries and
adds one bounded registered-only admission route for the exact live orthoepy
stress action accepted by #185/#187. No live/GitHub lookup occurs at runtime.
"""
from __future__ import annotations

import json
import os
from http.server import HTTPServer
from typing import Any

import learner_tutor_web_runtime as tutor_web
import runtime as core
from entitlement_read import ProEntitlementReader
from peis_service_bridge import IntegrityConflict, ServiceRequestError, UnknownAdapter
from russian_exceptions_practice_adapter import RussianExceptionsPracticeAdapter
from russian_orthoepy_stress_adapter import ADAPTER_ID, RussianOrthoepyStressAdmissionAdapter
from tutor_lifecycle import FailClosedTutorProvider, PostgresTutorLifecycle, build_tutor_aware_bridge

ADMISSION_PATH = "/api/russian/thematic/orthoepy/stress/submit"


def make_handler(
    runtime: core.Runtime,
    views: tutor_web.TutorAwareRegisteredLearnerViews | None,
    entitlements: ProEntitlementReader | None,
    tutor: PostgresTutorLifecycle | None,
):
    Base = tutor_web.make_handler(runtime, views, entitlements, tutor)

    class Handler(Base):
        server_version = "EksamioLearnerAdmissionsTutorWeb/0.1"

        def do_OPTIONS(self):  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path != ADMISSION_PATH:
                super().do_OPTIONS()
                return
            cors = self._cors()
            if cors is None:
                return
            requested_method = self.headers.get("Access-Control-Request-Method")
            requested_headers = (self.headers.get("Access-Control-Request-Headers") or "").casefold()
            if requested_method != "POST" or any(
                item.strip() not in {"", "content-type"}
                for item in requested_headers.split(",")
            ):
                self.send_json(403, {"error": "PREFLIGHT_NOT_ALLOWED"}, extra_headers=cors)
                return
            self.send_response(204)
            for name, value in cors.items():
                self.send_header(name, value)
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_POST(self):  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path != ADMISSION_PATH:
                super().do_POST()
                return

            cors = self._cors()
            if cors is None:
                return
            host = self._host(cors)
            if host is None:
                return
            if not runtime.writes_enabled:
                self.send_json(503, {"error": "PEIS_WRITES_DISABLED"}, extra_headers=cors)
                return
            try:
                payload = self.read_json_object()
                result = runtime.bridge.submit_checked_card(
                    adapter_id=ADAPTER_ID,
                    payload=payload,
                    host_identity=host,
                )
                self.send_json(
                    200,
                    {
                        "status": result["status"],
                        "event_receipt": result["event_receipt"],
                        "directive": result["directive"],
                        "canonical_state_owner": "shared_peis",
                    },
                    extra_headers=cors,
                )
            except IntegrityConflict:
                self.send_json(409, {"error": "INTEGRITY_CONFLICT"}, extra_headers=cors)
            except UnknownAdapter:
                self.send_json(503, {"error": "ADMISSIONS_GATE_UNAVAILABLE"}, extra_headers=cors)
            except (
                ServiceRequestError,
                ValueError,
                TypeError,
                UnicodeDecodeError,
                json.JSONDecodeError,
            ):
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
    views: tutor_web.TutorAwareRegisteredLearnerViews | None = None
    entitlements: ProEntitlementReader | None = None
    tutor: PostgresTutorLifecycle | None = None
    if not isinstance(store, core.UnreadyStore):
        try:
            admission_adapter = RussianOrthoepyStressAdmissionAdapter(core.ENGINE)
            if ADAPTER_ID not in runtime.bridge.registry.adapter_ids():
                runtime.bridge.registry.register(admission_adapter)

            base_adapter = RussianExceptionsPracticeAdapter(core.ENGINE)
            tutor = PostgresTutorLifecycle(
                store=store,
                position_bridge=runtime.bridge,
                adapter=base_adapter,
                provider=FailClosedTutorProvider(),
            )
            tutor_bridge = build_tutor_aware_bridge(
                store=store,
                base_adapter=base_adapter,
                lifecycle=tutor,
            )
            views = tutor_web.TutorAwareRegisteredLearnerViews(
                store=store,
                bridge=tutor_bridge,
                adapter=base_adapter,
                tutor_lifecycle=tutor,
            )
            entitlements = ProEntitlementReader(store.connection)
        except Exception:
            views = None
            entitlements = None
            tutor = None

    server = HTTPServer(
        (
            os.getenv("PEIS_BIND_HOST", "0.0.0.0"),
            int(os.getenv("PEIS_PORT", "8080")),
        ),
        make_handler(runtime, views, entitlements, tutor),
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
