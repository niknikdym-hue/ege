#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CAPABILITIES_PATH = HERE / "SEP1-PRODUCTION-CAPABILITIES-v0.1.json"
LEGAL_MANIFEST_PATH = REPO_ROOT / "eksamio-learning-engine" / "legal-privacy" / "SEP1-LEGAL-PRIVACY-ARTIFACTS-v0.1.json"


@dataclass(frozen=True)
class Requirement:
    name: str
    secret: bool = False
    min_length: int = 1
    kind: str = "text"


EXTERNAL_REQUIREMENTS: dict[str, tuple[Requirement, ...]] = {
    "payments": (
        Requirement("ROBOKASSA_MERCHANT_LOGIN"),
        Requirement("ROBOKASSA_PROD_PASSWORD1", secret=True, min_length=8),
        Requirement("ROBOKASSA_PROD_PASSWORD2", secret=True, min_length=8),
        Requirement("ROBOKASSA_FISCAL_TAX"),
        Requirement("ROBOKASSA_FISCAL_PAYMENT_METHOD"),
        Requirement("ROBOKASSA_FISCAL_PAYMENT_OBJECT"),
        Requirement("ROBOKASSA_MERCHANT_TEST_ACCEPTED", kind="true"),
        Requirement("ROBOKASSA_PRODUCTION_SETTINGS_ACCEPTED", kind="true"),
        Requirement("NPD_ROBOCHEKI_RECEIPT_ACCEPTED", kind="true"),
    ),
    "identity": (
        Requirement("IDENTITY_CONTACT_HMAC_KEY", secret=True, min_length=32),
        Requirement("IDENTITY_VERIFICATION_HMAC_KEY", secret=True, min_length=32),
        Requirement("YANDEX_POSTBOX_SENDER_ADDRESS", kind="email"),
        Requirement("YANDEX_POSTBOX_RUNTIME_CREDENTIAL_READY", kind="true"),
        Requirement("YANDEX_POSTBOX_LIVE_ACCEPTED", kind="true"),
        Requirement("SMSRU_API_ID", secret=True, min_length=8),
        Requirement("SMSRU_LIVE_ACCEPTED", kind="true"),
        Requirement("IDENTITY_PRODUCTION_DELIVERY_ACCEPTED", kind="true"),
    ),
    "tutor": (
        Requirement("YANDEX_AI_STUDIO_CREDENTIAL", secret=True, min_length=8),
        Requirement("YANDEX_AI_STUDIO_MODEL_URI", kind="yandex_model_uri"),
        Requirement("YANDEX_SPEECHKIT_CREDENTIAL", secret=True, min_length=8),
        Requirement("YANDEX_SPEECHKIT_FOLDER_ID"),
        Requirement("YANDEX_SPEECHKIT_VOICE"),
        Requirement("TUTOR_LIVE_TEXT_ACCEPTED", kind="true"),
        Requirement("TUTOR_LIVE_VOICE_ACCEPTED", kind="true"),
        Requirement("TUTOR_SAME_SESSION_ACCEPTED", kind="true"),
        Requirement("LEARNER_AUDIO_PERSISTENCE_ZERO_ACCEPTED", kind="true"),
    ),
    "yandex_private_staging": (
        Requirement("YC_FOLDER_ID"),
        Requirement("YC_CONTAINER_ID"),
        Requirement("YC_RUNTIME_SA_ID"),
        Requirement("YC_GATEWAY_SA_ID"),
        Requirement("YC_NETWORK_ID"),
        Requirement("YC_IMAGE", kind="immutable_yandex_image"),
        Requirement("YC_DB_SECRET_ID"),
        Requirement("YC_DB_SECRET_VERSION_ID"),
        Requirement("YC_DB_SECRET_KEY"),
        Requirement("YANDEX_PRIVATE_STAGING_ACCEPTED", kind="true"),
    ),
    "pro_client_real_backend": (
        Requirement("PRO_BACKEND_BASE_URL", kind="https"),
        Requirement("PRO_PUBLIC_ORIGIN", kind="https"),
        Requirement("PRO_TLS_ACCEPTED", kind="true"),
        Requirement("PRO_COOKIE_SECURITY_ACCEPTED", kind="true"),
        Requirement("PRO_CORS_ACCEPTED", kind="true"),
        Requirement("PRO_REAL_ADAPTER_BROWSER_E2E_ACCEPTED", kind="true"),
    ),
    "legal_privacy_operational": (
        Requirement("LEGAL_PRIVACY_ACCEPTED", kind="true"),
        Requirement("LEGAL_PUBLIC_OFFER_ACCEPTED", kind="true"),
        Requirement("LEGAL_PERSONAL_DATA_ACCEPTED", kind="true"),
        Requirement("LEGAL_AUDIO_NON_STORAGE_DISCLOSURE_ACCEPTED", kind="true"),
        Requirement("LEGAL_NPD_PAYMENT_CONTOUR_ACCEPTED", kind="true"),
        Requirement("LEGAL_OPERATOR_FULL_NAME"),
        Requirement("LEGAL_OPERATOR_INN"),
        Requirement("LEGAL_SUPPORT_CONTACT"),
        Requirement("LEGAL_SUPPORT_SLA"),
    ),
    "production_e2e": (
        Requirement("FINAL_ANON_TO_ACCOUNT_ACCEPTED", kind="true"),
        Requirement("FINAL_PAYMENT_ENTITLEMENT_ACCEPTED", kind="true"),
        Requirement("FINAL_LEARNING_PEIS_TUTOR_ACCEPTED", kind="true"),
        Requirement("FINAL_REFUND_REVOKE_ACCEPTED", kind="true"),
        Requirement("FINAL_PRODUCTION_CANDIDATE_E2E_ACCEPTED", kind="true"),
    ),
}

KILL_SWITCHES = {
    "PUBLIC_TRAFFIC_ENABLED": False,
    "PRODUCTION_CHARGES_ENABLED": False,
    "PEIS_NETWORK_WRITES_ENABLED": False,
    "YC_GATEWAY_APPLY": False,
}

PLACEHOLDERS = {"changeme", "placeholder", "secret", "test", "todo", "xxx", "<secret>"}
IMAGE_RE = re.compile(r"^cr\.yandex/[^\s]+@sha256:[0-9a-f]{64}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _truth(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def _valid(requirement: Requirement, env: Mapping[str, str]) -> bool:
    value = env.get(requirement.name)
    if requirement.kind == "true":
        return _truth(value) is True
    if not isinstance(value, str) or not value.strip():
        return False
    stripped = value.strip()
    if requirement.secret:
        if len(stripped) < requirement.min_length or stripped.casefold() in PLACEHOLDERS:
            return False
    if requirement.kind == "https":
        return stripped.startswith("https://") and " " not in stripped
    if requirement.kind == "immutable_yandex_image":
        return bool(IMAGE_RE.fullmatch(stripped))
    if requirement.kind == "yandex_model_uri":
        return stripped.startswith("gpt://") and " " not in stripped
    if requirement.kind == "email":
        return bool(EMAIL_RE.fullmatch(stripped))
    return len(stripped) >= requirement.min_length


def legal_artifact_fingerprints() -> list[dict[str, str | bool]]:
    manifest = json.loads(LEGAL_MANIFEST_PATH.read_text(encoding="utf-8"))
    marker = str(manifest["unresolved_marker_prefix"])
    rows: list[dict[str, str | bool]] = []
    for artifact in manifest["artifacts"]:
        path = REPO_ROOT / str(artifact["path"])
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        rows.append(
            {
                "id": str(artifact["id"]),
                "version": str(artifact["version"]),
                "path": str(artifact["path"]),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "has_unresolved_markers": marker in text,
                "accepted_env": str(artifact["accepted_env"]),
                "accepted_version_env": str(artifact["accepted_version_env"]),
                "accepted_sha256_env": str(artifact["accepted_sha256_env"]),
            }
        )
    return rows


def _legal_missing(env: Mapping[str, str]) -> list[str]:
    missing: list[str] = []
    try:
        rows = legal_artifact_fingerprints()
    except (OSError, KeyError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return ["LEGAL_ARTIFACT_PACKET_INVALID"]

    for row in rows:
        if row["has_unresolved_markers"]:
            missing.append(f"LEGAL_ARTIFACT_CONTENT_RESOLUTION_REQUIRED:{row['id']}")
        if _truth(env.get(str(row["accepted_env"]))) is not True:
            missing.append(str(row["accepted_env"]))
        if env.get(str(row["accepted_version_env"]), "").strip() != row["version"]:
            missing.append(str(row["accepted_version_env"]))
        supplied_sha = env.get(str(row["accepted_sha256_env"]), "").strip().casefold()
        if not SHA256_RE.fullmatch(supplied_sha) or supplied_sha != row["sha256"]:
            missing.append(str(row["accepted_sha256_env"]))

    return list(dict.fromkeys(missing))


def evaluate(env: Mapping[str, str] | None = None) -> dict[str, object]:
    env = dict(os.environ if env is None else env)
    capabilities = json.loads(CAPABILITIES_PATH.read_text(encoding="utf-8"))

    kill_switch_failures: list[str] = []
    for name, expected in KILL_SWITCHES.items():
        actual = _truth(env.get(name))
        if actual is None:
            actual = False
        if actual is not expected:
            kill_switch_failures.append(name)

    gate_results: list[dict[str, object]] = []
    for gate in capabilities.get("gates", []):
        gate_id = str(gate["id"])
        code_status = str(gate["status"])
        missing = [
            requirement.name
            for requirement in EXTERNAL_REQUIREMENTS.get(gate_id, ())
            if not _valid(requirement, env)
        ]
        if gate_id == "legal_privacy_operational":
            missing.extend(_legal_missing(env))
            missing = list(dict.fromkeys(missing))
        if code_status != "READY":
            status = code_status
        elif missing:
            status = "BLOCKED_EXTERNAL"
        else:
            status = "READY"
        gate_results.append(
            {
                "id": gate_id,
                "status": status,
                "code_status": code_status,
                "missing_external_fields": missing,
                "blocker": gate.get("blocker"),
                "evidence": gate.get("evidence", []),
            }
        )

    if kill_switch_failures:
        overall = "FAIL_UNSAFE_ACTIVATION"
    elif all(row["status"] == "READY" for row in gate_results):
        overall = "READY_FOR_OWNER_GO_LIVE_DECISION"
    else:
        overall = "NOT_READY"

    return {
        "product": capabilities.get("product"),
        "deadline": capabilities.get("deadline"),
        "baseline_main": capabilities.get("baseline_main"),
        "overall": overall,
        "kill_switch_failures": kill_switch_failures,
        "gates": gate_results,
        "secret_values_emitted": False,
        "owner_go_live_approved": False,
    }


def main() -> int:
    result = evaluate()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["overall"] == "READY_FOR_OWNER_GO_LIVE_DECISION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
