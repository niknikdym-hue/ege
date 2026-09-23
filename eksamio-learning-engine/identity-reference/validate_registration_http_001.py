#!/usr/bin/env python3
"""Deterministic gate for the authenticated registration HTTP boundary."""
from __future__ import annotations

from dataclasses import dataclass

from registration_http import RegistrationHttpBoundary


@dataclass(frozen=True)
class _Receipt:
    challenge_id: str = "ch:registration-http-001"
    expires_at_epoch: int = 2_000_000_000
    marketing_consent: bool = False


@dataclass(frozen=True)
class _Session:
    set_cookie: str = (
        "eksamio_pro_session=sid.test-registration-session-material-1234567890; "
        "Path=/; Max-Age=3600; HttpOnly; Secure; SameSite=Lax"
    )
    expires_at_epoch: int = 2_000_003_600
    token: str = "sid.must-never-appear-in-http-body"


class _Service:
    def __init__(self) -> None:
        self.begin_payload = None
        self.verify_payload = None
        self.begin_error = None
        self.verify_error = None

    def begin_registration(self, payload):
        self.begin_payload = dict(payload)
        if self.begin_error is not None:
            raise self.begin_error
        return _Receipt(marketing_consent=bool(payload["marketing_consent"]))

    def verify_registration(self, payload):
        self.verify_payload = dict(payload)
        if self.verify_error is not None:
            raise self.verify_error
        return _Session()


def _headers(origin="https://eksamio.ru", content_type="application/json"):
    return {"Origin": origin, "Content-Type": content_type}


def _begin_payload():
    return {
        "email": "student@example.test",
        "personal_data_consent": True,
        "marketing_consent": False,
        "personal_data_document_version": "pd-doc-v1",
        "personal_data_text_version": "pd-text-v1",
        "marketing_document_version": "marketing-doc-v1",
        "marketing_text_version": "marketing-text-v1",
        "client_request_id": "registration-http-request-001",
    }


def main() -> None:
    service = _Service()
    boundary = RegistrationHttpBoundary(
        registration_service=service,
        allowed_origin="https://eksamio.ru",
    )

    begin = boundary.handle(
        method="POST",
        path=boundary.BEGIN_PATH,
        headers=_headers(),
        payload=_begin_payload(),
    )
    assert begin.status_code == 202
    assert begin.body == {
        "ok": True,
        "status": "CHALLENGE_SENT",
        "challenge_id": "ch:registration-http-001",
        "expires_at_epoch": 2_000_000_000,
        "marketing_consent": False,
    }
    assert service.begin_payload == _begin_payload()
    assert begin.headers["Access-Control-Allow-Origin"] == "https://eksamio.ru"
    assert begin.headers["Access-Control-Allow-Credentials"] == "true"
    assert begin.headers["Cache-Control"] == "no-store"

    verify = boundary.handle(
        method="POST",
        path=boundary.VERIFY_PATH,
        headers=_headers(),
        payload={"challenge_id": "ch:registration-http-001", "code": "123456"},
    )
    assert verify.status_code == 200
    assert verify.body == {
        "ok": True,
        "status": "AUTHENTICATED",
        "expires_at_epoch": 2_000_003_600,
    }
    assert "Set-Cookie" in verify.headers
    assert "HttpOnly" in verify.headers["Set-Cookie"]
    assert "Secure" in verify.headers["Set-Cookie"]
    assert "SameSite=Lax" in verify.headers["Set-Cookie"]
    assert "sid.must-never-appear" not in repr(verify.body)
    assert "token" not in verify.body

    preflight = boundary.handle(
        method="OPTIONS",
        path=boundary.BEGIN_PATH,
        headers={
            "Origin": "https://eksamio.ru",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
        payload=None,
    )
    assert preflight.status_code == 204
    assert preflight.headers["Access-Control-Allow-Origin"] == "https://eksamio.ru"
    assert preflight.headers["Access-Control-Allow-Credentials"] == "true"
    assert preflight.headers["Access-Control-Allow-Headers"] == "Content-Type"

    hostile_origin = boundary.handle(
        method="POST",
        path=boundary.BEGIN_PATH,
        headers=_headers(origin="https://evil.example"),
        payload=_begin_payload(),
    )
    assert hostile_origin.status_code == 403
    assert hostile_origin.body["error"] == "ORIGIN_NOT_ALLOWED"
    assert "Access-Control-Allow-Origin" not in hostile_origin.headers

    wrong_type = boundary.handle(
        method="POST",
        path=boundary.BEGIN_PATH,
        headers=_headers(content_type="text/plain"),
        payload=_begin_payload(),
    )
    assert wrong_type.status_code == 415
    assert service.begin_payload == _begin_payload()  # call count does not matter; payload was not replaced

    unknown = boundary.handle(
        method="POST",
        path="/v1/registration/anything-else",
        headers=_headers(),
        payload={},
    )
    assert unknown.status_code == 404

    get_request = boundary.handle(
        method="GET",
        path=boundary.BEGIN_PATH,
        headers=_headers(),
        payload=None,
    )
    assert get_request.status_code == 405
    assert get_request.headers["Allow"] == "POST, OPTIONS"

    service.begin_error = ValueError("secret provider diagnostic must not leak")
    rejected = boundary.handle(
        method="POST",
        path=boundary.BEGIN_PATH,
        headers=_headers(),
        payload=_begin_payload(),
    )
    assert rejected.status_code == 400
    assert rejected.body == {"ok": False, "error": "REGISTRATION_REJECTED"}
    assert "secret provider diagnostic" not in repr(rejected.body)

    class _UnsafeSessionService(_Service):
        def verify_registration(self, payload):
            return type(
                "UnsafeSession",
                (),
                {
                    "set_cookie": "eksamio_pro_session=sid.bad; Path=/",
                    "expires_at_epoch": 2_000_000_100,
                    "token": "sid.bad",
                },
            )()

    unsafe_boundary = RegistrationHttpBoundary(
        registration_service=_UnsafeSessionService(),
        allowed_origin="https://eksamio.ru",
    )
    unsafe = unsafe_boundary.handle(
        method="POST",
        path=boundary.VERIFY_PATH,
        headers=_headers(),
        payload={"challenge_id": "ch:registration-http-001", "code": "123456"},
    )
    assert unsafe.status_code == 500
    assert unsafe.body == {"ok": False, "error": "REGISTRATION_UNAVAILABLE"}
    assert "sid.bad" not in repr(unsafe.body)

    try:
        RegistrationHttpBoundary(
            registration_service=service,
            allowed_origin="*",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("wildcard/non-https origin must be rejected")

    print("PASS: registration HTTP boundary keeps one authenticated server session contract")


if __name__ == "__main__":
    main()
