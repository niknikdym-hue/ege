#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise AssertionError(f"{label} missing required token: {token}")


def forbid(text: str, token: str, label: str) -> None:
    if token in text:
        raise AssertionError(f"{label} contains forbidden token: {token}")


def assert_no_secret_payloads(env_example: str) -> None:
    """Reject credential payloads while allowing Lockbox reference metadata."""
    dangerous_names = {
        "PASSWORD",
        "TOKEN",
        "API_KEY",
        "SECRET_VALUE",
        "PRIVATE_KEY",
        "ACCESS_KEY",
        "SECRET_ACCESS_KEY",
        "OAUTH_TOKEN",
        "IAM_TOKEN",
    }
    for raw in env_example.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip().upper() in dangerous_names and value.strip():
            raise AssertionError(
                f"staging env example contains a credential payload in {name.strip()}"
            )


def main() -> int:
    gateway = (HERE / "api-gateway.template.yaml").read_text(encoding="utf-8")
    env_example = (HERE / "staging.env.example").read_text(encoding="utf-8")
    deploy = (HERE / "deploy_staging.sh").read_text(encoding="utf-8")
    smoke = (HERE / "smoke_staging.sh").read_text(encoding="utf-8")
    rollback = (HERE / "rollback_staging.sh").read_text(encoding="utf-8")
    runtime = (ENGINE / "peis-production-substrate/runtime.py").read_text(encoding="utf-8")
    dockerfile = (ENGINE / "peis-production-substrate/Dockerfile").read_text(encoding="utf-8")

    for token in (
        'type: serverless_containers',
        'container_id: ${YC_CONTAINER_ID}',
        'service_account_id: ${YC_GATEWAY_SA_ID}',
        '/healthz:',
        '/readyz:',
        '/v1/registration/begin:',
        '/v1/registration/verify:',
        '/v1/session:',
        '/v0/checked-card:',
    ):
        require(gateway, token, "gateway template")
    forbid(gateway.lower(), "tilda", "gateway template")
    forbid(gateway, "Access-Control-Allow-Origin: *", "gateway template")

    for token in (
        "PEIS_NETWORK_WRITES_ENABLED=false",
        "EKSAMIO_WEB_IDENTITY_REQUIRED=false",
        "EKSAMIO_REGISTRATION_BEGIN_ENABLED=false",
        "EKSAMIO_POSTBOX_EXECUTION_ENABLED=false",
        "EKSAMIO_EXTERNAL_DELIVERY_AUTHORIZED=false",
        "YC_GATEWAY_APPLY=false",
        "EKSAMIO_ALLOWED_ORIGIN=https://eksamio.ru",
        "@sha256:<immutable-digest>",
        "YC_IDENTITY_SECRET_ID=",
        "YC_IDENTITY_SECRET_VERSION_ID=",
        "YC_IDENTITY_CONTACT_HMAC_KEY=contact_hmac",
        "YC_IDENTITY_VERIFICATION_HMAC_KEY=verification_hmac",
        "YC_IDENTITY_HOST_SIGNING_KEY=host_signing",
    ):
        require(env_example, token, "staging env")
    assert_no_secret_payloads(env_example)

    for token in (
        'PEIS_NETWORK_WRITES_ENABLED:-false',
        'EKSAMIO_WEB_IDENTITY_REQUIRED:-false',
        'EKSAMIO_REGISTRATION_BEGIN_ENABLED:-false',
        'EKSAMIO_POSTBOX_EXECUTION_ENABLED:-false',
        'EKSAMIO_EXTERNAL_DELIVERY_AUTHORIZED:-false',
        'YC_GATEWAY_APPLY:-false',
        '@sha256:',
        '--concurrency 1',
        '--network-id "${YC_NETWORK_ID}"',
        '--metadata-options "aws-v1-http-endpoint=disabled,gce-http-endpoint=enabled"',
        '--secret "environment-variable=PEIS_DATABASE_DSN',
        '--secret "environment-variable=EKSAMIO_CONTACT_HMAC_KEY',
        '--secret "environment-variable=EKSAMIO_VERIFICATION_HMAC_KEY',
        '--secret "environment-variable=EKSAMIO_HOST_SIGNING_KEY',
        '--service-account-id "${YC_RUNTIME_SA_ID}"',
        'real Postbox delivery requires explicit EKSAMIO_EXTERNAL_DELIVERY_AUTHORIZED=true',
        'yc serverless api-gateway',
    ):
        require(deploy, token, "deploy script")
    for forbidden in (
        'allow-unauthenticated-invoke',
        'PEIS_NETWORK_WRITES_ENABLED=true',
        'YC_GATEWAY_APPLY=true\n',
        'lockbox payload get',
    ):
        forbid(deploy, forbidden, "deploy script")

    for token in (
        'direct_container_unauthenticated=DENIED',
        'PEIS_WRITES_DISABLED',
        'public_product_traffic=OFF',
    ):
        require(smoke, token, "smoke script")
    require(rollback, 'yc serverless containers rollback', "rollback script")
    require(rollback, '--revision-id "${TARGET_REVISION_ID}"', "rollback script")

    for token in (
        'PasswordlessIdentityService',
        'RegistrationConsentStore',
        'RegistrationHttpBoundary',
        'YandexMetadataIamTokenProvider',
        'YANDEX_METADATA_IAM_URL',
        '"Metadata-Flavor": "Google"',
        'SESSION_COOKIE = PasswordlessIdentityService.SESSION_COOKIE_NAME',
        'path == "/v1/session"',
        'AUTHENTICATION_REQUIRED',
        'PEIS_NETWORK_WRITES_ENABLED',
        'EKSAMIO_REGISTRATION_BEGIN_ENABLED',
        'EKSAMIO_POSTBOX_EXECUTION_ENABLED',
        'HTTPServer',
        'server.host_identity = None',
    ):
        require(runtime, token, "runtime")
    forbid(runtime, 'ThreadingHTTPServer', "runtime")

    for token in (
        'COPY peis-trusted-host-reference /app/peis-trusted-host-reference',
        'COPY identity-reference /app/identity-reference',
        'CMD ["python", "/app/peis-production-substrate/runtime.py"]',
    ):
        require(dockerfile, token, "Dockerfile")

    print("SEP1_YANDEX_STAGING_STATIC_VALIDATION=PASS")
    print("gateway_to_private_container_contract=PASS")
    print("registration_gateway_routes=PASS")
    print("server_session_only_peis_identity=PASS")
    print("metadata_iam_path=PASS")
    print("identity_lockbox_refs=PASS")
    print("single_connection_concurrency_guard=PASS")
    print("immutable_image_required=PASS")
    print("lockbox_dsn_boundary=PASS")
    print("private_network_required=PASS")
    print("peis_writes_default_off=PASS")
    print("registration_delivery_default_off=PASS")
    print("gateway_apply_default_off=PASS")
    print("rollback_command=PASS")
    print("secret_payloads_in_repo=0")
    print("live_yandex_execution=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
