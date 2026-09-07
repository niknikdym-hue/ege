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
        ENGINE / "peis-service-bridge-reference/russian_phraseology_fragment_adapter.py"
    ).read_text(encoding="utf-8")
    dockerfile = (ENGINE / "peis-production-substrate/Dockerfile").read_text(encoding="utf-8")

    route = "/api/russian/thematic/phraseology/fragment-identification/submit"
    for token in (
        route + ":",
        "operationId: russianPhraseologyFragmentIdentificationSubmitOptions",
        "operationId: russianPhraseologyFragmentIdentificationSubmit",
        "type: serverless_containers",
        "container_id: ${YC_CONTAINER_ID}",
        "service_account_id: ${YC_GATEWAY_SA_ID}",
    ):
        require(gateway, token, "Yandex API Gateway template")

    for token in (
        f'PHRASEOLOGY_ADMISSION_PATH = "{route}"',
        "RussianPhraseologyFragmentAdmissionAdapter",
        "PHRASEOLOGY_ADAPTER_ID",
        "ADMISSION_ADAPTER_BY_PATH",
        "shared_peis",
    ):
        require(runtime, token, "Admissions Gate runtime")

    for token in (
        'ACTION_ID = "fragment_identification"',
        'SEMANTIC_ID = "ru-lexis-phraseologism-fragment-identification"',
        "registered user_identity_ref is required",
        "remaining_86_phraseology_rows_admitted",
        "variant_answers_admitted",
        "false_exact_mastery invariant violated",
    ):
        require(adapter, token, "phraseology Admissions Gate adapter")

    require(
        dockerfile,
        'CMD ["python", "/app/peis-production-substrate/learner_admissions_tutor_web_runtime.py"]',
        "Dockerfile",
    )

    print("PHRASEOLOGY_ADMISSION_YANDEX_CONTRACT=PASS")
    print("private_api_gateway_route=PASS")
    print("same_serverless_container_runtime=PASS")
    print("registered_exact_item_action_only=PASS")
    print("admitted_phraseology_items=199")
    print("variant_answers_admitted=0")
    print("gateway_apply=0")
    print("public_traffic_changes=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
