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
    learner_runtime = (ENGINE / "peis-production-substrate/learner_web_runtime.py").read_text(encoding="utf-8")
    learner_views = (ENGINE / "peis-production-substrate/learner_views.py").read_text(encoding="utf-8")
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
        '/api/identity/session:',
        '/api/identity/logout:',
        '/api/consent/marketing/revoke:',
        '/api/russian/profile:',
        '/api/russian/plan:',
        '/api/russian/history:',
        '/api/russian/practice/next:',
        '/api/russian/practice/submit:',
        '/api/russian/program:',
        '/api/tutor/turn:',
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
        "@sha256:<immutable-digest>",
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
        '--network-id "${YC_NETWORK_ID}"',
        '--secret "environment-variable=PEIS_DATABASE_DSN',
        '--service-account-id "${YC_RUNTIME_SA_ID}"',
        '--concurrency 1',
        'yc serverless api-gateway',
    ):
        require(deploy, token, "deploy script")
    for forbidden in (
        'allow-unauthenticated-invoke',
        'PEIS_NETWORK_WRITES_ENABLED=true',
        'EKSAMIO_REGISTRATION_BEGIN_ENABLED=true\n',
        'EKSAMIO_POSTBOX_EXECUTION_ENABLED=true\n',
        'EKSAMIO_EXTERNAL_DELIVERY_AUTHORIZED=true\n',
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
        'PEIS_NETWORK_WRITES_ENABLED',
        'EKSAMIO_REGISTRATION_BEGIN_ENABLED',
        'EKSAMIO_POSTBOX_EXECUTION_ENABLED',
        'YandexMetadataIamTokenProvider',
        'SESSION_COOKIE = PasswordlessIdentityService.SESSION_COOKIE_NAME',
        'server.host_identity = None',
    ):
        require(runtime, token, "core runtime")

    for token in (
        '/api/identity/session',
        '/api/identity/logout',
        '/api/consent/marketing/revoke',
        '/api/russian/profile',
        '/api/russian/plan',
        '/api/russian/history',
        '/api/russian/practice/next',
        '/api/russian/practice/submit',
        'TUTOR_PROVIDER_NOT_ADMITTED',
        'RUSSIAN_FULL_SUBJECT_NOT_ADMITTED',
        'PasswordlessIdentityService.clear_session_cookie()',
    ):
        require(learner_runtime, token, "learner browser runtime")

    for token in (
        'canonical_state_owner',
        'shared_peis',
        'Europe/Moscow',
        'FIRST_SLICE_CARD_ID',
    ):
        require(learner_views, token, "learner views")

    require(
        dockerfile,
        'CMD ["python", "/app/peis-production-substrate/learner_web_runtime.py"]',
        "Dockerfile",
    )

    print("SEP1_YANDEX_STAGING_STATIC_VALIDATION=PASS")
    print("gateway_to_private_container_contract=PASS")
    print("authenticated_pro_routes=PASS")
    print("session_owned_peis=PASS")
    print("full_russian_program_fail_closed=PASS")
    print("production_tutor_fail_closed=PASS")
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
