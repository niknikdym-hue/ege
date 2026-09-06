#!/usr/bin/env python3
"""Bounded browser HTTP contract for authenticated Eksamio registration.

This module is intentionally transport-thin. It exposes the existing
``RegistrationService`` to a browser/runtime adapter without creating a second
identity model. The registration verification response sets the server-owned
HttpOnly session cookie and never exposes the raw session token to JavaScript.

The boundary is cloud-agnostic so the same contract can sit behind a Yandex
runtime/API gateway without coupling product identity to a cloud provider.
Deployment-level throttling, bot protection and final legal URLs/text remain
separate launch gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from registration_consent import RegistrationError


@dataclass(frozen=True)
class HttpResult:
    status_code: int
    headers: Mapping[str, str]
    body: Mapping[str, Any]


class RegistrationHttpBoundary:
    """Exact-origin JSON boundary for registration begin/verify."""

    BEGIN_PATH = "/v1/registration/begin"
    VERIFY_PATH = "/v1/registration/verify"
    _KNOWN_PATHS = {BEGIN_PATH, VERIFY_PATH}

    def __init__(self, *, registration_service: Any, allowed_origin: str) -> None:
        if (
            not isinstance(allowed_origin, str)
            or not allowed_origin.startswith("https://")
            or allowed_origin.endswith("/")
        ):
            raise ValueError("allowed_origin must be one exact https origin")
        self.registration_service = registration_service
        self.allowed_origin = allowed_origin

    @staticmethod
    def _header(headers: Mapping[str, Any], name: str) -> str | None:
        if not isinstance(headers, Mapping):
            return None
        wanted = name.casefold()
        for key, value in headers.items():
            if isinstance(key, str) and key.casefold() == wanted and isinstance(value, str):
                return value
        return None

    def _cors_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json; charset=utf-8",
            "Cache-Control": "no-store",
            "Access-Control-Allow-Origin": self.allowed_origin,
            "Access-Control-Allow-Credentials": "true",
            "Vary": "Origin",
            "X-Content-Type-Options": "nosniff",
        }

    @staticmethod
    def _blocked(status_code: int, code: str) -> HttpResult:
        # Deliberately omit CORS headers for an untrusted origin.
        return HttpResult(
            status_code=status_code,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
            body={"ok": False, "error": code},
        )

    def _error(self, status_code: int, code: str) -> HttpResult:
        return HttpResult(
            status_code=status_code,
            headers=self._cors_headers(),
            body={"ok": False, "error": code},
        )

    def handle(
        self,
        *,
        method: str,
        path: str,
        headers: Mapping[str, Any],
        payload: Mapping[str, Any] | None,
    ) -> HttpResult:
        """Handle already-decoded JSON from a trusted runtime adapter.

        Raw HTTP/body decoding belongs to the runtime adapter. This keeps the
        security contract deterministic and directly testable.
        """
        if not isinstance(method, str) or not isinstance(path, str):
            return self._blocked(400, "INVALID_HTTP_REQUEST")

        origin = self._header(headers, "Origin")
        if origin != self.allowed_origin:
            return self._blocked(403, "ORIGIN_NOT_ALLOWED")

        if path not in self._KNOWN_PATHS:
            return self._error(404, "NOT_FOUND")

        method = method.upper()
        if method == "OPTIONS":
            request_method = self._header(headers, "Access-Control-Request-Method")
            request_headers = (self._header(headers, "Access-Control-Request-Headers") or "").casefold()
            if request_method != "POST" or any(
                item.strip() not in {"", "content-type"}
                for item in request_headers.split(",")
            ):
                return self._error(403, "PREFLIGHT_NOT_ALLOWED")
            response_headers = self._cors_headers()
            response_headers.update(
                {
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Max-Age": "600",
                }
            )
            return HttpResult(status_code=204, headers=response_headers, body={})

        if method != "POST":
            result = self._error(405, "METHOD_NOT_ALLOWED")
            return HttpResult(
                status_code=result.status_code,
                headers={**result.headers, "Allow": "POST, OPTIONS"},
                body=result.body,
            )

        content_type = self._header(headers, "Content-Type") or ""
        if content_type.split(";", 1)[0].strip().casefold() != "application/json":
            return self._error(415, "JSON_REQUIRED")
        if not isinstance(payload, Mapping):
            return self._error(400, "INVALID_JSON_OBJECT")

        try:
            if path == self.BEGIN_PATH:
                receipt = self.registration_service.begin_registration(payload)
                return HttpResult(
                    status_code=202,
                    headers=self._cors_headers(),
                    body={
                        "ok": True,
                        "status": "CHALLENGE_SENT",
                        "challenge_id": str(receipt.challenge_id),
                        "expires_at_epoch": int(receipt.expires_at_epoch),
                        "marketing_consent": bool(receipt.marketing_consent),
                    },
                )

            session = self.registration_service.verify_registration(payload)
            set_cookie = getattr(session, "set_cookie", None)
            expires_at_epoch = getattr(session, "expires_at_epoch", None)
            if (
                not isinstance(set_cookie, str)
                or not set_cookie.startswith("eksamio_pro_session=")
                or "HttpOnly" not in set_cookie
                or "Secure" not in set_cookie
                or "SameSite=Lax" not in set_cookie
                or not isinstance(expires_at_epoch, int)
            ):
                raise RuntimeError("identity service returned unsafe session material")
            return HttpResult(
                status_code=200,
                headers={**self._cors_headers(), "Set-Cookie": set_cookie},
                body={
                    "ok": True,
                    "status": "AUTHENTICATED",
                    "expires_at_epoch": expires_at_epoch,
                },
            )
        except RegistrationError:
            return self._error(400, "REGISTRATION_REJECTED")
        except ValueError:
            # Passwordless identity validation errors are intentionally reduced
            # to one public error class; raw internal exception text is never
            # returned to the browser.
            return self._error(400, "REGISTRATION_REJECTED")
        except Exception:
            return self._error(500, "REGISTRATION_UNAVAILABLE")
