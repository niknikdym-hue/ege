"""Private Yandex web runtime: registration -> session -> authenticated PEIS."""
from __future__ import annotations

import json
import os
import sys
from http import cookies
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib import request as urllib_request

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path[:0] = [
    str(HERE),
    str(ENGINE / "peis-persistence-reference"),
    str(ENGINE / "peis-service-bridge-reference"),
    str(ENGINE / "peis-reference-kernel"),
    str(ENGINE / "peis-trusted-host-reference"),
    str(ENGINE / "identity-reference"),
]

from passwordless_identity import (  # noqa: E402
    IdentityAuthStore,
    InvalidSession,
    PasswordlessIdentityService,
)
from peis_service_bridge import (  # noqa: E402
    AdapterRegistry,
    IntegrityConflict,
    PeisServiceBridge,
    ServiceRequestError,
    UnknownAdapter,
)
from peis_reference_kernel import snapshot as kernel_snapshot  # noqa: E402
from peis_postgres import PostgresPeisPersistenceStore  # noqa: E402
from peis_trusted_host import TrustedHostIdentityResolver  # noqa: E402
from production_delivery import (  # noqa: E402
    DeliveryExecutionDisabled,
    DeliveryProviderFailure,
    YandexPostboxDeliveryProvider,
    YandexPostboxRuntimeConfig,
)
from registration_consent import RegistrationConsentStore, RegistrationService  # noqa: E402
from registration_http import HttpResult, RegistrationHttpBoundary  # noqa: E402
from russian_exceptions_practice_adapter import RussianExceptionsPracticeAdapter  # noqa: E402

MAX_BODY_BYTES = 262144
SESSION_COOKIE = PasswordlessIdentityService.SESSION_COOKIE_NAME
YANDEX_METADATA_IAM_URL = (
    "http://169.254.169.254/computeMetadata/v1/"
    "instance/service-accounts/default/token"
)


class UrlLibJsonPostTransport:
    """Minimal stdlib HTTPS transport for the already-reviewed Postbox adapter."""

    def __init__(self, *, opener: Any = urllib_request.urlopen):
        self.opener = opener

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, Any],
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        if not url.startswith("https://"):
            raise DeliveryProviderFailure("JSON transport requires HTTPS")
        request = urllib_request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            headers=dict(headers),
            method="POST",
        )
        with self.opener(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, Mapping):
            raise DeliveryProviderFailure("JSON transport returned a non-object response")
        return payload


class YandexMetadataIamTokenProvider:
    """Fetch short-lived IAM material from the attached container service account."""

    def __init__(self, *, opener: Any = urllib_request.urlopen):
        self.opener = opener

    def __call__(self) -> str:
        request = urllib_request.Request(
            YANDEX_METADATA_IAM_URL,
            headers={"Metadata-Flavor": "Google"},
            method="GET",
        )
        try:
            with self.opener(request, timeout=2.0) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise DeliveryProviderFailure("Yandex metadata IAM token unavailable") from exc
        token = payload.get("access_token") if isinstance(payload, Mapping) else None
        if not isinstance(token, str) or not token:
            raise DeliveryProviderFailure("Yandex metadata IAM response lacks access_token")
        return token


class DisabledDeliveryProvider:
    """No network fallback: begin is blocked before this provider can be called."""

    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        raise DeliveryExecutionDisabled("production registration delivery is disabled")


class Runtime:
    def __init__(
        self,
        *,
        bridge: PeisServiceBridge,
        identity_service: PasswordlessIdentityService | None,
        registration_boundary: RegistrationHttpBoundary | None,
        allowed_origin: str | None,
        writes_enabled: bool,
        registration_begin_enabled: bool,
        identity_required_for_ready: bool = False,
    ):
        self.bridge = bridge
        self.identity_service = identity_service
        self.registration_boundary = registration_boundary
        self.allowed_origin = allowed_origin
        self.writes_enabled = bool(writes_enabled)
        self.registration_begin_enabled = bool(registration_begin_enabled)
        self.identity_required_for_ready = bool(identity_required_for_ready)

    def ready(self) -> bool:
        store_ready = bool(getattr(self.bridge.store, "readiness", lambda: False)())
        if not store_ready:
            return False
        if self.identity_required_for_ready and (
            self.identity_service is None or self.registration_boundary is None
        ):
            return False
        return True

    def cors_headers(self) -> dict[str, str]:
        if not self.allowed_origin:
            return {}
        return {
            "Access-Control-Allow-Origin": self.allowed_origin,
            "Access-Control-Allow-Credentials": "true",
            "Vary": "Origin",
        }

    def origin_allowed(self, headers: Mapping[str, Any]) -> bool:
        if not self.allowed_origin:
            return False
        origin = None
        for key, value in headers.items():
            if isinstance(key, str) and key.casefold() == "origin" and isinstance(value, str):
                origin = value
                break
        return origin == self.allowed_origin

    def registration_result(
        self,
        *,
        method: str,
        path: str,
        headers: Mapping[str, Any],
        payload: Mapping[str, Any] | None,
    ) -> HttpResult:
        if self.registration_boundary is None:
            return HttpResult(
                status_code=503,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Cache-Control": "no-store",
                    "X-Content-Type-Options": "nosniff",
                },
                body={"ok": False, "error": "REGISTRATION_UNAVAILABLE"},
            )
        if (
            path == RegistrationHttpBoundary.BEGIN_PATH
            and method.upper() == "POST"
            and not self.registration_begin_enabled
        ):
            if not self.origin_allowed(headers):
                return self.registration_boundary._blocked(403, "ORIGIN_NOT_ALLOWED")
            return self.registration_boundary._error(503, "REGISTRATION_DELIVERY_DISABLED")
        return self.registration_boundary.handle(
            method=method,
            path=path,
            headers=headers,
            payload=payload,
        )

    def authenticated_host(self, cookie_header: str | None):
        if self.identity_service is None:
            raise RuntimeError("identity runtime unavailable")
        jar = cookies.SimpleCookie()
        try:
            jar.load(cookie_header or "")
        except cookies.CookieError as exc:
            raise InvalidSession("invalid session cookie") from exc
        morsel = jar.get(SESSION_COOKIE)
        if morsel is None or not morsel.value:
            raise InvalidSession("session cookie required")
        return self.identity_service.resolve_session(morsel.value)


class UnreadyStore:
    """Fail closed during dependency outage while keeping process health observable."""

    def readiness(self) -> bool:
        return False


def make_registry(engine_root: Path = ENGINE) -> AdapterRegistry:
    """Register only server-owned, current-main-admitted product adapters."""
    registry = AdapterRegistry()
    registry.register(RussianExceptionsPracticeAdapter(engine_root))
    return registry


def build_runtime(
    store: Any,
    *,
    writes_enabled: bool,
    allowed_origin: str,
    contact_hmac_key: bytes,
    verification_hmac_key: bytes,
    host_signing_key: bytes,
    delivery_provider: Any,
    registration_begin_enabled: bool,
    identity_required_for_ready: bool = True,
) -> Runtime:
    bridge = PeisServiceBridge(
        store=store,
        registry=make_registry(),
        kernel_snapshot=kernel_snapshot,
    )
    trusted_host = TrustedHostIdentityResolver(
        store=store,
        signing_keys={"web-v1": host_signing_key},
        active_key_id="web-v1",
    )
    identity = PasswordlessIdentityService(
        peis_store=store,
        trusted_host_resolver=trusted_host,
        auth_store=IdentityAuthStore(store.connection),
        delivery_provider=delivery_provider,
        contact_hmac_key=contact_hmac_key,
        verification_hmac_key=verification_hmac_key,
    )
    registration = RegistrationService(
        identity_service=identity,
        consent_store=RegistrationConsentStore(store.connection),
    )
    boundary = RegistrationHttpBoundary(
        registration_service=registration,
        allowed_origin=allowed_origin,
    )
    return Runtime(
        bridge=bridge,
        identity_service=identity,
        registration_boundary=boundary,
        allowed_origin=allowed_origin,
        writes_enabled=writes_enabled,
        registration_begin_enabled=registration_begin_enabled,
        identity_required_for_ready=identity_required_for_ready,
    )


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def make_handler(runtime: Runtime) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "EksamioPEISWeb/0.2"

        def log_message(self, format: str, *args: Any):  # noqa: A003
            return

        def send_json(
            self,
            code: int,
            value: Mapping[str, Any],
            *,
            extra_headers: Mapping[str, str] | None = None,
        ):
            body = _json_bytes(value)
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            for name, header_value in (extra_headers or {}).items():
                if name.casefold() not in {"content-type", "content-length"}:
                    self.send_header(name, header_value)
            self.end_headers()
            self.wfile.write(body)

        def send_http_result(self, result: HttpResult):
            body = b"" if result.status_code == 204 else _json_bytes(result.body)
            self.send_response(result.status_code)
            seen_content_type = False
            for name, header_value in result.headers.items():
                if name.casefold() == "content-length":
                    continue
                if name.casefold() == "content-type":
                    seen_content_type = True
                self.send_header(name, header_value)
            if body and not seen_content_type:
                self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body:
                self.wfile.write(body)

        def request_headers(self) -> dict[str, str]:
            return {str(key): str(value) for key, value in self.headers.items()}

        def read_json_object(self) -> dict[str, Any]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise ServiceRequestError("invalid request body length") from exc
            if length <= 0 or length > MAX_BODY_BYTES:
                raise ServiceRequestError("invalid request body length")
            value = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(value, dict):
                raise ServiceRequestError("JSON object required")
            return value

        def checked_card_cors(self) -> dict[str, str]:
            return runtime.cors_headers() if runtime.origin_allowed(self.request_headers()) else {}

        def do_OPTIONS(self):  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path in {
                RegistrationHttpBoundary.BEGIN_PATH,
                RegistrationHttpBoundary.VERIFY_PATH,
            }:
                result = runtime.registration_result(
                    method="OPTIONS",
                    path=path,
                    headers=self.request_headers(),
                    payload=None,
                )
                self.send_http_result(result)
                return
            if path == "/v0/checked-card":
                if not runtime.origin_allowed(self.request_headers()):
                    self.send_json(403, {"error": "ORIGIN_NOT_ALLOWED"})
                    return
                requested_method = self.headers.get("Access-Control-Request-Method")
                requested_headers = (self.headers.get("Access-Control-Request-Headers") or "").casefold()
                if requested_method != "POST" or any(
                    item.strip() not in {"", "content-type"}
                    for item in requested_headers.split(",")
                ):
                    self.send_json(
                        403,
                        {"error": "PREFLIGHT_NOT_ALLOWED"},
                        extra_headers=runtime.cors_headers(),
                    )
                    return
                self.send_response(204)
                for name, value in runtime.cors_headers().items():
                    self.send_header(name, value)
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.send_header("Access-Control-Max-Age", "600")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_json(404, {"error": "NOT_FOUND"})

        def do_GET(self):  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path == "/healthz":
                self.send_json(200, {"status": "ok"})
                return
            if path == "/readyz":
                ready = runtime.ready()
                self.send_json(
                    200 if ready else 503,
                    {
                        "status": "ready" if ready else "not_ready",
                        "identity_runtime": runtime.identity_service is not None,
                        "registration_begin_enabled": runtime.registration_begin_enabled,
                        "peis_network_writes_enabled": runtime.writes_enabled,
                    },
                )
                return
            if path == "/v1/session":
                if not runtime.origin_allowed(self.request_headers()):
                    self.send_json(403, {"error": "ORIGIN_NOT_ALLOWED"})
                    return
                try:
                    runtime.authenticated_host(self.headers.get("Cookie"))
                except InvalidSession:
                    self.send_json(
                        200,
                        {"authenticated": False},
                        extra_headers=runtime.cors_headers(),
                    )
                    return
                except RuntimeError:
                    self.send_json(
                        503,
                        {"error": "IDENTITY_UNAVAILABLE"},
                        extra_headers=runtime.cors_headers(),
                    )
                    return
                self.send_json(
                    200,
                    {"authenticated": True, "identity_owner": "server"},
                    extra_headers=runtime.cors_headers(),
                )
                return
            self.send_json(404, {"error": "NOT_FOUND"})

        def do_POST(self):  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path in {
                RegistrationHttpBoundary.BEGIN_PATH,
                RegistrationHttpBoundary.VERIFY_PATH,
            }:
                if not runtime.origin_allowed(self.request_headers()):
                    self.send_json(403, {"ok": False, "error": "ORIGIN_NOT_ALLOWED"})
                    return
                try:
                    payload = self.read_json_object()
                except (ServiceRequestError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
                    self.send_json(
                        400,
                        {"ok": False, "error": "INVALID_JSON_OBJECT"},
                        extra_headers=runtime.cors_headers(),
                    )
                    return
                result = runtime.registration_result(
                    method="POST",
                    path=path,
                    headers=self.request_headers(),
                    payload=payload,
                )
                self.send_http_result(result)
                return

            if path != "/v0/checked-card":
                self.send_json(404, {"error": "NOT_FOUND"})
                return
            cors = self.checked_card_cors()
            if not cors:
                self.send_json(403, {"error": "ORIGIN_NOT_ALLOWED"})
                return
            if not runtime.writes_enabled:
                self.send_json(503, {"error": "PEIS_WRITES_DISABLED"}, extra_headers=cors)
                return
            try:
                host = runtime.authenticated_host(self.headers.get("Cookie"))
                request = self.read_json_object()
                if set(request) != {"adapter_id", "payload"}:
                    raise ServiceRequestError("invalid request envelope")
                result = runtime.bridge.submit_checked_card(
                    adapter_id=request["adapter_id"],
                    payload=request["payload"],
                    host_identity=host,
                )
                self.send_json(200, result, extra_headers=cors)
            except InvalidSession:
                self.send_json(401, {"error": "AUTHENTICATION_REQUIRED"}, extra_headers=cors)
            except RuntimeError:
                self.send_json(503, {"error": "IDENTITY_UNAVAILABLE"}, extra_headers=cors)
            except UnknownAdapter:
                self.send_json(404, {"error": "UNKNOWN_ADAPTER"}, extra_headers=cors)
            except IntegrityConflict:
                self.send_json(409, {"error": "INTEGRITY_CONFLICT"}, extra_headers=cors)
            except (ServiceRequestError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
                self.send_json(400, {"error": "INVALID_REQUEST"}, extra_headers=cors)
            except Exception:
                self.send_json(500, {"error": "SERVICE_UNAVAILABLE"}, extra_headers=cors)

    return Handler


def _env_key(name: str) -> bytes:
    value = os.getenv(name, "")
    raw = value.encode("utf-8")
    if len(raw) < 32:
        raise ValueError(f"{name} must contain at least 32 bytes")
    return raw


def _build_delivery_from_env() -> tuple[Any, bool]:
    sender = os.getenv("EKSAMIO_POSTBOX_SENDER", "")
    execution_enabled = os.getenv(
        "EKSAMIO_POSTBOX_EXECUTION_ENABLED", "false"
    ).lower() == "true"
    if not sender:
        return DisabledDeliveryProvider(), False
    provider = YandexPostboxDeliveryProvider(
        config=YandexPostboxRuntimeConfig(
            sender_address=sender,
            iam_token_provider=YandexMetadataIamTokenProvider(),
            execution_enabled=execution_enabled,
        ),
        transport=UrlLibJsonPostTransport(),
    )
    return provider, execution_enabled


def build_runtime_from_env(store: Any) -> Runtime:
    allowed_origin = os.getenv("EKSAMIO_ALLOWED_ORIGIN", "")
    identity_required = os.getenv(
        "EKSAMIO_WEB_IDENTITY_REQUIRED", "false"
    ).lower() == "true"
    writes_enabled = os.getenv(
        "PEIS_NETWORK_WRITES_ENABLED", "false"
    ).lower() == "true"
    begin_requested = os.getenv(
        "EKSAMIO_REGISTRATION_BEGIN_ENABLED", "false"
    ).lower() == "true"

    try:
        delivery, delivery_enabled = _build_delivery_from_env()
        return build_runtime(
            store,
            writes_enabled=writes_enabled,
            allowed_origin=allowed_origin,
            contact_hmac_key=_env_key("EKSAMIO_CONTACT_HMAC_KEY"),
            verification_hmac_key=_env_key("EKSAMIO_VERIFICATION_HMAC_KEY"),
            host_signing_key=_env_key("EKSAMIO_HOST_SIGNING_KEY"),
            delivery_provider=delivery,
            registration_begin_enabled=begin_requested and delivery_enabled,
            identity_required_for_ready=identity_required,
        )
    except Exception:
        bridge = PeisServiceBridge(
            store=store,
            registry=make_registry(),
            kernel_snapshot=kernel_snapshot,
        )
        return Runtime(
            bridge=bridge,
            identity_service=None,
            registration_boundary=None,
            allowed_origin=allowed_origin or None,
            writes_enabled=writes_enabled,
            registration_begin_enabled=False,
            identity_required_for_ready=identity_required,
        )


def main() -> int:
    dsn = os.environ["PEIS_DATABASE_DSN"]
    evidence = json.loads(
        (ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text()
    )
    nba = json.loads(
        (ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text()
    )
    try:
        store = PostgresPeisPersistenceStore(
            dsn,
            evidence_schema=evidence,
            nba_schema=nba,
        )
    except Exception:
        store = UnreadyStore()

    runtime = build_runtime_from_env(store)
    server = HTTPServer(
        (
            os.getenv("PEIS_BIND_HOST", "0.0.0.0"),
            int(os.getenv("PEIS_PORT", "8080")),
        ),
        make_handler(runtime),
    )
    # Legacy private-host injection stays explicitly absent; browser writes use
    # only the server-owned passwordless session resolved from PostgreSQL.
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
