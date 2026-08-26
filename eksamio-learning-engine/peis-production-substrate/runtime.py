"""Minimal private HTTP envelope for the existing subject-neutral PEIS bridge."""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path[:0] = [
    str(HERE),
    str(ENGINE / "peis-persistence-reference"),
    str(ENGINE / "peis-service-bridge-reference"),
    str(ENGINE / "peis-reference-kernel"),
]

from peis_service_bridge import (  # noqa: E402
    AdapterRegistry,
    HostIdentity,
    IntegrityConflict,
    MissingHostIdentity,
    PeisServiceBridge,
    ServiceRequestError,
    UnknownAdapter,
)
from peis_reference_kernel import snapshot as kernel_snapshot  # noqa: E402
from peis_postgres import PostgresPeisPersistenceStore  # noqa: E402
from russian_exceptions_practice_adapter import RussianExceptionsPracticeAdapter  # noqa: E402

MAX_BODY_BYTES = 262144


class Runtime:
    def __init__(self, bridge: PeisServiceBridge, writes_enabled: bool):
        self.bridge = bridge
        self.writes_enabled = writes_enabled

    def ready(self) -> bool:
        return bool(getattr(self.bridge.store, "readiness", lambda: False)())


class UnreadyStore:
    """Fail closed during dependency outage while keeping process health observable."""

    def readiness(self) -> bool:
        return False


def make_registry(engine_root: Path = ENGINE) -> AdapterRegistry:
    """Register only server-owned, current-main-admitted product adapters."""
    registry = AdapterRegistry()
    registry.register(RussianExceptionsPracticeAdapter(engine_root))
    return registry


def make_handler(runtime: Runtime) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "EksamioPEIS/0.1"

        def log_message(self, format: str, *args: Any):  # noqa: A003
            return

        def send_json(self, code: int, value: dict[str, Any]):
            body = json.dumps(value, separators=(",", ":")).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path == "/healthz":
                self.send_json(200, {"status": "ok"})
                return
            if self.path == "/readyz":
                ready = runtime.ready()
                self.send_json(200 if ready else 503, {"status": "ready" if ready else "not_ready"})
                return
            self.send_json(404, {"error": "NOT_FOUND"})

        def do_POST(self):  # noqa: N802
            if self.path != "/v0/checked-card":
                self.send_json(404, {"error": "NOT_FOUND"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_json(400, {"error": "INVALID_REQUEST"})
                return
            if length <= 0 or length > MAX_BODY_BYTES:
                self.send_json(413, {"error": "REQUEST_TOO_LARGE"})
                return
            if not runtime.writes_enabled:
                self.send_json(503, {"error": "PEIS_WRITES_DISABLED"})
                return
            try:
                request = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(request, dict) or set(request) != {"adapter_id", "payload"}:
                    raise ServiceRequestError("invalid request envelope")
                # Production identity is injected by the private trusted host, never browser-owned.
                identity = getattr(self.server, "host_identity", None)
                if not isinstance(identity, HostIdentity):
                    raise MissingHostIdentity("private trusted host identity is required")
                self.send_json(
                    200,
                    runtime.bridge.submit_checked_card(
                        adapter_id=request["adapter_id"],
                        payload=request["payload"],
                        host_identity=identity,
                    ),
                )
            except MissingHostIdentity:
                self.send_json(401, {"error": "HOST_IDENTITY_REQUIRED"})
            except UnknownAdapter:
                self.send_json(404, {"error": "UNKNOWN_ADAPTER"})
            except IntegrityConflict:
                self.send_json(409, {"error": "INTEGRITY_CONFLICT"})
            except (ServiceRequestError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
                self.send_json(400, {"error": "INVALID_REQUEST"})
            except Exception:
                self.send_json(500, {"error": "SERVICE_UNAVAILABLE"})

    return Handler


def main() -> int:
    dsn = os.environ["PEIS_DATABASE_DSN"]
    evidence = json.loads((ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text())
    nba = json.loads((ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text())
    try:
        store = PostgresPeisPersistenceStore(dsn, evidence_schema=evidence, nba_schema=nba)
    except Exception:
        store = UnreadyStore()
    bridge = PeisServiceBridge(store=store, registry=make_registry(), kernel_snapshot=kernel_snapshot)
    server = ThreadingHTTPServer(
        (os.getenv("PEIS_BIND_HOST", "0.0.0.0"), int(os.getenv("PEIS_PORT", "8080"))),
        make_handler(Runtime(bridge, os.getenv("PEIS_NETWORK_WRITES_ENABLED", "false").lower() == "true")),
    )
    # No browser-supplied or placeholder identity is accepted by this container.
    server.host_identity = None
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
