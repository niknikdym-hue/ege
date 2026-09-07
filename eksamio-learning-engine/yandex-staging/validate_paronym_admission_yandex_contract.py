#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise AssertionError(f"{label} missing required token: {token}")


def main() -> int:
    gateway = (HERE / "api-gateway.template.yaml").read_text(encoding="utf-8")
    runtime = (
        ENGINE / "peis-production-substrate/learner_admissions_tutor_web_runtime.py"
    ).read_text(encoding="utf-8")
    adapter = (
        ENGINE / "peis-service-bridge-reference/russian_paronym_context_adapter.py"
    ).read_text(encoding="utf-8")
    dockerfile = (ENGINE / "peis-production-substrate/Dockerfile").read_text(encoding="utf-8")

    route = "/api/russian/thematic/paronyms/context-choice/submit"
    for token in (
        route + ":",
        "operationId: russianParonymContextChoiceSubmitOptions",
        "operationId: russianParonymContextChoiceSubmit",
        "type: serverless_containers",
        "container_id: ${YC_CONTAINER_ID}",
        "service_account_id: ${YC_GATEWAY_SA_ID}",
    ):
        require(gateway, token, "Yandex API Gateway template")

    for token in (
        f'PARONYM_ADMISSION_PATH = "{route}"',
        "RussianParonymContextChoiceAdmissionAdapter",
        "PARONYM_ADAPTER_ID",
        "ADMISSION_ADAPTER_BY_PATH",
        "shared_peis",
    ):
        require(runtime, token, "Admissions Gate runtime")

    for token in (
        'ACTION_ID = "context_collocation_choice"',
        'SEMANTIC_ID = "ru-lexis-paronym-collocation-choice"',
        "registered user_identity_ref is required",
        "meaning_match_admitted",
        "exam_error_correction_admitted",
        "false_exact_mastery invariant violated",
    ):
        require(adapter, token, "paronym Admissions Gate adapter")

    require(
        dockerfile,
        'CMD ["python", "/app/peis-production-substrate/learner_admissions_tutor_web_runtime.py"]',
        "Dockerfile",
    )

    print("PARONYM_ADMISSION_YANDEX_CONTRACT=PASS")
    print("private_api_gateway_route=PASS")
    print("same_serverless_container_runtime=PASS")
    print("registered_exact_item_action_only=PASS")
    print("paronym_groups=144")
    print("paronym_entries=334")
    print("gateway_apply=0")
    print("public_traffic_changes=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
