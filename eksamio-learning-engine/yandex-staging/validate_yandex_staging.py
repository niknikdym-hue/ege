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
    """Reject credential payloads while allowing Lockbox reference metadata.

    `YC_DB_SECRET_ID`, `YC_DB_SECRET_VERSION_ID`, and `YC_DB_SECRET_KEY=dsn`
    identify a Lockbox object/version/key; they are not secret values themselves.
    """
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
            raise AssertionError(f"staging env example contains a credential payload in {name.strip()}")


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
        '/v0/checked-card:',
    ):
        require(gateway, token, "gateway template")
    forbid(gateway.lower(), "tilda", "gateway template")
    forbid(gateway, "Access-Control-Allow-Origin: *", "gateway template")

    require(env_example, "PEIS_NETWORK_WRITES_ENABLED=false", "staging env")
    require(env_example, "YC_GATEWAY_APPLY=false", "staging env")
    require(env_example, "@sha256:<immutable-digest>", "staging env")
    assert_no_secret_payloads(env_example)

    for token in (
        'PEIS_NETWORK_WRITES_ENABLED:-false',
        'YC_GATEWAY_APPLY:-false',
        '@sha256:',
        '--network-id "${YC_NETWORK_ID}"',
        '--secret "environment-variable=PEIS_DATABASE_DSN',
        '--service-account-id "${YC_RUNTIME_SA_ID}"',
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

    require(runtime, 'PEIS_NETWORK_WRITES_ENABLED', "runtime")
    require(runtime, '"false"', "runtime")
    require(runtime, 'server.host_identity = None', "runtime")
    require(dockerfile, 'CMD ["python", "/app/peis-production-substrate/runtime.py"]', "Dockerfile")

    print("SEP1_YANDEX_STAGING_STATIC_VALIDATION=PASS")
    print("gateway_to_private_container_contract=PASS")
    print("immutable_image_required=PASS")
    print("lockbox_dsn_boundary=PASS")
    print("private_network_required=PASS")
    print("peis_writes_default_off=PASS")
    print("gateway_apply_default_off=PASS")
    print("rollback_command=PASS")
    print("secret_payloads_in_repo=0")
    print("live_yandex_execution=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
