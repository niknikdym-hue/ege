#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from sep1_production_preflight import (
    EXTERNAL_REQUIREMENTS,
    KILL_SWITCHES,
    evaluate,
    legal_artifact_fingerprints,
)

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


def legal_gate(result: dict[str, object]) -> dict[str, object]:
    return next(row for row in result["gates"] if row["id"] == "legal_privacy_operational")


def main() -> int:
    capabilities = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
    gates = capabilities.get("gates", [])
    ids = [row.get("id") for row in gates]
    if ids != EXPECTED_GATES:
        raise AssertionError(f"Sep-1 gate order/coverage drift: {ids}")
    if len(set(ids)) != len(ids):
        raise AssertionError("duplicate Sep-1 production gate")
    if capabilities.get("launch_status") != "NOT_READY":
        raise AssertionError("current capability truth must not claim launch ready")

    allowed = {"READY", "BLOCKED_CODE", "BLOCKED_EXTERNAL", "BLOCKED_SUBJECT", "BLOCKED_DEPENDENCY"}
    for row in gates:
        if row.get("status") not in allowed:
            raise AssertionError(f"unsupported gate status: {row}")
        if row.get("status") == "READY" and not row.get("evidence"):
            raise AssertionError(f"READY gate lacks durable evidence: {row['id']}")
        if not isinstance(row.get("blocker"), str) or not row["blocker"].strip():
            raise AssertionError(f"gate lacks exact blocker text: {row['id']}")

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
    if empty["overall"] != "NOT_READY":
        raise AssertionError("empty environment must be NOT_READY")
    if empty["kill_switch_failures"]:
        raise AssertionError("unset kill switches must default fail-closed/off")
    if empty["secret_values_emitted"] is not False or empty["owner_go_live_approved"] is not False:
        raise AssertionError("preflight output boundary drift")

    empty_statuses = {row["id"]: row["status"] for row in empty["gates"]}
    for external_gate in (
        "payments",
        "identity",
        "tutor",
        "yandex_private_staging",
        "pro_client_real_backend",
        "legal_privacy_operational",
    ):
        if empty_statuses.get(external_gate) != "BLOCKED_EXTERNAL":
            raise AssertionError(f"{external_gate} should be code-ready and external-blocked")

    bare = fully_populated_env()
    bare_legal = legal_gate(evaluate(bare))
    bare_missing = set(bare_legal["missing_external_fields"])
    if bare_legal["code_status"] != "READY" or bare_legal["status"] != "BLOCKED_EXTERNAL":
        raise AssertionError("legal code-ready/external-blocked boundary drift")
    if not any(name.endswith("_ACCEPTED_VERSION") for name in bare_missing):
        raise AssertionError("bare legal acceptance illegally bypassed artifact version binding")
    if not any(name.endswith("_ACCEPTED_SHA256") for name in bare_missing):
        raise AssertionError("bare legal acceptance illegally bypassed artifact fingerprint binding")

    mismatch = fully_populated_env()
    for row in legal_artifact_fingerprints():
        mismatch[str(row["accepted_env"])] = "true"
        mismatch[str(row["accepted_version_env"])] = str(row["version"])
        mismatch[str(row["accepted_sha256_env"])] = "0" * 64
    mismatch_missing = set(legal_gate(evaluate(mismatch))["missing_external_fields"])
    expected_sha_fields = {str(row["accepted_sha256_env"]) for row in legal_artifact_fingerprints()}
    if not expected_sha_fields.issubset(mismatch_missing):
        raise AssertionError("mismatched legal artifact SHA was not rejected")

    populated_env = fully_populated_env()
    bind_exact_legal_artifacts(populated_env)
    populated = evaluate(populated_env)
    if populated["overall"] != "NOT_READY":
        raise AssertionError("external values must not override remaining source/content/legal/e2e blockers")
    statuses = {row["id"]: row["status"] for row in populated["gates"]}

    for gate_id in ("payments", "identity", "tutor", "yandex_private_staging", "pro_client_real_backend"):
        if statuses.get(gate_id) != "READY":
            raise AssertionError(f"fully populated external fixture should make {gate_id} READY: {statuses.get(gate_id)}")

    for gate_id, expected in {
        "russian_source_knowledge": "BLOCKED_CODE",
        "russian_content": "BLOCKED_SUBJECT",
        "legal_privacy_operational": "BLOCKED_EXTERNAL",
        "production_e2e": "BLOCKED_DEPENDENCY",
    }.items():
        if statuses.get(gate_id) != expected:
            raise AssertionError(f"external fixture illegally overrode {gate_id}: {statuses.get(gate_id)}")

    resolved_missing = set(legal_gate(populated)["missing_external_fields"])
    expected_resolution = {
        f"LEGAL_ARTIFACT_CONTENT_RESOLUTION_REQUIRED:{row['id']}"
        for row in legal_artifact_fingerprints()
        if row["has_unresolved_markers"]
    }
    if not expected_resolution or not expected_resolution.issubset(resolved_missing):
        raise AssertionError("unresolved legal artifact markers must remain explicit external blockers")

    serialized = json.dumps(populated, ensure_ascii=False)
    secret_fixture = "S" * 40
    if secret_fixture in serialized:
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
    print("gate_count=9")
    print("provider_code_ready_gates=5")
    print("legal_code_ready_external_blocked=PASS")
    print("legal_bare_boolean_guard=PASS")
    print("legal_version_sha_binding=PASS")
    print("legal_unresolved_content_guard=PASS")
    print("remaining_source_content_legal_e2e_blockers=PASS")
    print("unsafe_activation_guard=PASS")
    print("secret_output_guard=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
