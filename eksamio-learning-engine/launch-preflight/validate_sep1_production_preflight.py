#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from sep1_production_preflight import EXTERNAL_REQUIREMENTS, KILL_SWITCHES, evaluate, legal_artifact_fingerprints

HERE = Path(__file__).resolve().parent
CAPABILITIES = HERE / "SEP1-PRODUCTION-CAPABILITIES-v0.1.json"
EXPECTED_GATES = [
    "russian_source_knowledge",
    "russian_content",
    "payments",
    "identity",
    "tutor",
    "yandex_private_staging",
    "pro_client_real_backend",
    "legal_privacy_operational",
    "production_e2e",
]
EXTERNAL_CODE_READY = (
    "payments",
    "identity",
    "tutor",
    "yandex_private_staging",
    "pro_client_real_backend",
    "legal_privacy_operational",
)


def fully_populated_env() -> dict[str, str]:
    env: dict[str, str] = {
        "PUBLIC_TRAFFIC_ENABLED": "false",
        "PRODUCTION_CHARGES_ENABLED": "false",
        "PEIS_NETWORK_WRITES_ENABLED": "false",
        "YC_GATEWAY_APPLY": "false",
    }
    for requirements in EXTERNAL_REQUIREMENTS.values():
        for requirement in requirements:
            if requirement.kind == "true":
                env[requirement.name] = "true"
            elif requirement.kind == "https":
                env[requirement.name] = "https://example.invalid"
            elif requirement.kind == "immutable_yandex_image":
                env[requirement.name] = "cr.yandex/example/eksamio@sha256:" + "a" * 64
            elif requirement.kind == "yandex_model_uri":
                env[requirement.name] = "gpt://folder-fixture/yandexgpt/latest"
            elif requirement.kind == "email":
                env[requirement.name] = "login@eksamio.example"
            elif requirement.secret:
                env[requirement.name] = "S" * max(40, requirement.min_length)
            else:
                env[requirement.name] = "fixture-value"
    return env


def bind_exact_legal_artifacts(env: dict[str, str]) -> None:
    for row in legal_artifact_fingerprints():
        env[str(row["accepted_env"])] = "true"
        env[str(row["accepted_version_env"])] = str(row["version"])
        env[str(row["accepted_sha256_env"])] = str(row["sha256"])


def gate(result: dict[str, object], gate_id: str) -> dict[str, object]:
    return next(row for row in result["gates"] if row["id"] == gate_id)


def main() -> int:
    capabilities = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
    gates = capabilities.get("gates", [])
    ids = [row.get("id") for row in gates]
    if ids != EXPECTED_GATES or len(set(ids)) != len(ids):
        raise AssertionError(f"Sep-1 gate order/coverage drift: {ids}")
    if capabilities.get("launch_status") != "NOT_READY":
        raise AssertionError("capability truth must remain NOT_READY")

    allowed = {"READY", "BLOCKED_CODE", "BLOCKED_EXTERNAL", "BLOCKED_SUBJECT", "BLOCKED_DEPENDENCY"}
    for row in gates:
        if row.get("status") not in allowed:
            raise AssertionError(f"unsupported gate status: {row}")
        if row.get("status") == "READY" and not row.get("evidence"):
            raise AssertionError(f"READY gate lacks evidence: {row['id']}")
        if not isinstance(row.get("blocker"), str) or not row["blocker"].strip():
            raise AssertionError(f"gate lacks blocker text: {row['id']}")

    activation = capabilities.get("activation_invariants", {})
    for key in (
        "public_traffic_enabled",
        "production_charges_enabled",
        "peis_network_writes_enabled",
        "yandex_gateway_apply_enabled",
        "owner_go_live_approved",
    ):
        if activation.get(key) is not False:
            raise AssertionError(f"preflight must remain fail-closed: {key}")

    empty = evaluate({})
    if empty["overall"] != "NOT_READY" or empty["kill_switch_failures"]:
        raise AssertionError("empty environment must be safely NOT_READY")
    empty_status = {row["id"]: row["status"] for row in empty["gates"]}
    if empty_status["russian_source_knowledge"] != "READY":
        raise AssertionError("validated source-knowledge code gate must remain READY")
    if empty_status["russian_content"] != "BLOCKED_SUBJECT":
        raise AssertionError("source readiness must not self-accept Russian content")
    if empty_status["production_e2e"] != "BLOCKED_DEPENDENCY":
        raise AssertionError("final E2E must remain dependency-blocked")
    for gate_id in EXTERNAL_CODE_READY:
        if empty_status[gate_id] != "BLOCKED_EXTERNAL":
            raise AssertionError(f"{gate_id} should be external-blocked with empty env")

    bare = fully_populated_env()
    bare_legal = gate(evaluate(bare), "legal_privacy_operational")
    bare_missing = set(bare_legal["missing_external_fields"])
    if bare_legal["code_status"] != "READY" or bare_legal["status"] != "BLOCKED_EXTERNAL":
        raise AssertionError("legal code-ready/external-blocked boundary drift")
    if not any(name.endswith("_ACCEPTED_VERSION") for name in bare_missing):
        raise AssertionError("bare legal acceptance bypassed artifact version binding")
    if not any(name.endswith("_ACCEPTED_SHA256") for name in bare_missing):
        raise AssertionError("bare legal acceptance bypassed artifact SHA binding")

    mismatch = fully_populated_env()
    for row in legal_artifact_fingerprints():
        mismatch[str(row["accepted_env"])] = "true"
        mismatch[str(row["accepted_version_env"])] = str(row["version"])
        mismatch[str(row["accepted_sha256_env"])] = "0" * 64
    mismatch_missing = set(gate(evaluate(mismatch), "legal_privacy_operational")["missing_external_fields"])
    expected_sha_fields = {str(row["accepted_sha256_env"]) for row in legal_artifact_fingerprints()}
    if not expected_sha_fields.issubset(mismatch_missing):
        raise AssertionError("mismatched legal artifact SHA was not rejected")

    populated_env = fully_populated_env()
    bind_exact_legal_artifacts(populated_env)
    populated = evaluate(populated_env)
    if populated["overall"] != "NOT_READY":
        raise AssertionError("external values must not override subject/legal/E2E blockers")
    statuses = {row["id"]: row["status"] for row in populated["gates"]}
    if statuses["russian_source_knowledge"] != "READY":
        raise AssertionError("source gate regressed under populated fixture")
    if statuses["russian_content"] != "BLOCKED_SUBJECT":
        raise AssertionError("external values illegally overrode subject acceptance")
    for gate_id in ("payments", "identity", "tutor", "yandex_private_staging", "pro_client_real_backend"):
        if statuses[gate_id] != "READY":
            raise AssertionError(f"fully populated fixture should make {gate_id} READY")
    if statuses["legal_privacy_operational"] != "BLOCKED_EXTERNAL":
        raise AssertionError("unresolved legal content must remain external-blocked")
    if statuses["production_e2e"] != "BLOCKED_DEPENDENCY":
        raise AssertionError("final E2E must remain dependency-blocked")

    unresolved = set(gate(populated, "legal_privacy_operational")["missing_external_fields"])
    expected_resolution = {
        f"LEGAL_ARTIFACT_CONTENT_RESOLUTION_REQUIRED:{row['id']}"
        for row in legal_artifact_fingerprints()
        if row["has_unresolved_markers"]
    }
    if not expected_resolution or not expected_resolution.issubset(unresolved):
        raise AssertionError("unresolved legal artifact markers must remain explicit")

    serialized = json.dumps(populated, ensure_ascii=False)
    if "S" * 40 in serialized:
        raise AssertionError("secret value leaked into preflight output")

    unsafe_env = fully_populated_env()
    bind_exact_legal_artifacts(unsafe_env)
    unsafe_env["PRODUCTION_CHARGES_ENABLED"] = "true"
    unsafe = evaluate(unsafe_env)
    if unsafe["overall"] != "FAIL_UNSAFE_ACTIVATION" or "PRODUCTION_CHARGES_ENABLED" not in unsafe["kill_switch_failures"]:
        raise AssertionError("unsafe production activation must hard-fail")

    if set(KILL_SWITCHES) != {
        "PUBLIC_TRAFFIC_ENABLED",
        "PRODUCTION_CHARGES_ENABLED",
        "PEIS_NETWORK_WRITES_ENABLED",
        "YC_GATEWAY_APPLY",
    }:
        raise AssertionError("kill-switch inventory drift")

    print("SEP1_PRODUCTION_PREFLIGHT=PASS")
    print("current_overall=NOT_READY")
    print("russian_source_knowledge=READY")
    print("russian_content=BLOCKED_SUBJECT")
    print("legal_code_ready_external_blocked=PASS")
    print("final_e2e_dependency_guard=PASS")
    print("unsafe_activation_guard=PASS")
    print("secret_output_guard=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
