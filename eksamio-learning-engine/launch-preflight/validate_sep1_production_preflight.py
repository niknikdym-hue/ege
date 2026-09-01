#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from sep1_production_preflight import (
    EXTERNAL_REQUIREMENTS,
    FINAL_E2E_REQUIRED_RESULTS,
    KILL_SWITCHES,
    evaluate,
    legal_artifact_fingerprints,
)

HERE = Path(__file__).resolve().parent
CAPABILITIES = HERE / "SEP1-PRODUCTION-CAPABILITIES-v0.1.json"
PREFLIGHT = HERE / "sep1_production_preflight.py"
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
    "production_e2e",
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
            elif requirement.kind == "sha256":
                env[requirement.name] = "b" * 64
            elif requirement.kind == "sha40":
                env[requirement.name] = "a" * 40
            elif requirement.kind == "path":
                env[requirement.name] = "/tmp/eksamio-e2e-nonexistent-fixture.json"
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


def exact_e2e_evidence(*, evidence_class: str, private_live: bool) -> dict[str, object]:
    legal = [
        {
            "id": str(row["id"]),
            "version": str(row["version"]),
            "sha256": str(row["sha256"]),
        }
        for row in legal_artifact_fingerprints()
    ]
    results = {key: True for key in FINAL_E2E_REQUIRED_RESULTS}
    results["private_staging_live_evidence"] = private_live
    return {
        "schema": "eksamio.sep1.production-e2e.v1",
        "evidence_class": evidence_class,
        "candidate": {
            "git_sha": "a" * 40,
            "config_fingerprint": "d" * 64,
            "preflight_fingerprint": hashlib.sha256(PREFLIGHT.read_bytes()).hexdigest(),
            "legal_artifacts": legal,
            "russian_content_authority": {
                "status": "READY",
                "fingerprint": "c" * 64,
            },
        },
        "results": results,
        "safety": {
            "learner_audio_persisted_bytes": 0,
            "public_traffic_enabled": False,
        },
    }


def bind_e2e_file(env: dict[str, str], path: Path, evidence: dict[str, object]) -> None:
    raw = json.dumps(
        evidence,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    path.write_bytes(raw)
    env["FINAL_PRODUCTION_E2E_EVIDENCE_PATH"] = str(path)
    env["FINAL_PRODUCTION_E2E_EVIDENCE_SHA256"] = hashlib.sha256(raw).hexdigest()
    env["FINAL_PRODUCTION_CANDIDATE_SHA"] = "a" * 40


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
    if statuses["production_e2e"] != "BLOCKED_EXTERNAL":
        raise AssertionError("final E2E must require an exact evidence artifact")

    unresolved = set(gate(populated, "legal_privacy_operational")["missing_external_fields"])
    expected_resolution = {
        f"LEGAL_ARTIFACT_CONTENT_RESOLUTION_REQUIRED:{row['id']}"
        for row in legal_artifact_fingerprints()
        if row["has_unresolved_markers"]
    }
    if not expected_resolution or not expected_resolution.issubset(unresolved):
        raise AssertionError("unresolved legal artifact markers must remain explicit")

    with tempfile.TemporaryDirectory(prefix="sep1-preflight-e2e-") as tmp:
        tmpdir = Path(tmp)

        # All legacy FINAL_* booleans plus exact simulated evidence still cannot
        # masquerade as private live production-candidate acceptance.
        simulated_env = fully_populated_env()
        bind_exact_legal_artifacts(simulated_env)
        bind_e2e_file(
            simulated_env,
            tmpdir / "simulated.json",
            exact_e2e_evidence(
                evidence_class="CI_SIMULATED_CONTRACT_EVIDENCE",
                private_live=False,
            ),
        )
        simulated_gate = gate(evaluate(simulated_env), "production_e2e")
        simulated_missing = set(simulated_gate["missing_external_fields"])
        if simulated_gate["status"] != "BLOCKED_EXTERNAL":
            raise AssertionError("simulated CI evidence illegally satisfied final production E2E")
        if "FINAL_PRODUCTION_E2E_LIVE_EVIDENCE_REQUIRED" not in simulated_missing:
            raise AssertionError("simulated-vs-live evidence distinction is not fail-closed")

        # An exact private-live shaped artifact can satisfy only the E2E gate.
        # Other subject/legal/provider gates still govern the overall launch.
        live_env = fully_populated_env()
        bind_exact_legal_artifacts(live_env)
        bind_e2e_file(
            live_env,
            tmpdir / "private-live.json",
            exact_e2e_evidence(
                evidence_class="PRIVATE_STAGING_LIVE_EVIDENCE",
                private_live=True,
            ),
        )
        live_result = evaluate(live_env)
        if gate(live_result, "production_e2e")["status"] != "READY":
            raise AssertionError("exact private-live E2E evidence did not satisfy the E2E code gate")
        if live_result["overall"] != "NOT_READY":
            raise AssertionError("E2E evidence illegally overrode Russian/legal launch blockers")

        # Candidate SHA binding is mandatory.
        wrong_sha_env = dict(live_env)
        wrong_sha_env["FINAL_PRODUCTION_CANDIDATE_SHA"] = "e" * 40
        wrong_sha_missing = set(gate(evaluate(wrong_sha_env), "production_e2e")["missing_external_fields"])
        if "FINAL_PRODUCTION_E2E_CANDIDATE_SHA_MISMATCH" not in wrong_sha_missing:
            raise AssertionError("stale/different candidate evidence was not rejected")

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
    print("production_e2e_code=READY")
    print("legal_code_ready_external_blocked=PASS")
    print("final_e2e_exact_live_evidence_guard=PASS")
    print("simulated_evidence_cannot_masquerade_as_live=PASS")
    print("candidate_sha_binding=PASS")
    print("unsafe_activation_guard=PASS")
    print("secret_output_guard=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
