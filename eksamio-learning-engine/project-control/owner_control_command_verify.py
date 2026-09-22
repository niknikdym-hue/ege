from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import tempfile
import time
from decimal import Decimal
from pathlib import Path
from typing import Any


PINNED_PUBLIC_KEY_B64 = "__PENDING__"
SCHEMA_VERSION = "owner-control-command-v1"
REPOSITORY = "niknikdym-hue/ege"
PAYLOAD_KEYS = {
    "schema_version",
    "command_id",
    "repository",
    "issued_at",
    "expires_at",
    "approved_main_sha",
    "target_base_ref",
    "target_base_sha",
    "task_ids",
    "package_budget_usd",
    "tasks",
    "auto_retry",
    "auto_merge",
    "auto_deploy",
    "auto_ready",
}
TASK_KEYS = {
    "task_id",
    "execution_mode",
    "route_model",
    "astra_plan_required",
    "astra_acceptance_required",
    "allowed_paths",
}
SIG_KEYS = {"alg", "key_id", "value"}


class CommandVerificationError(ValueError):
    pass


def _b64u_decode(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise CommandVerificationError("invalid base64url value")
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except Exception as exc:
        raise CommandVerificationError("invalid base64url encoding") from exc


def canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _exact_keys(obj: dict[str, Any], expected: set[str], label: str) -> None:
    if set(obj) != expected:
        raise CommandVerificationError(
            f"{label} fields mismatch: missing={sorted(expected-set(obj))} unknown={sorted(set(obj)-expected)}"
        )


def _verify_ed25519(payload: dict[str, Any], signature: dict[str, Any], public_key_b64: str) -> None:
    if public_key_b64 == "__PENDING__":
        raise CommandVerificationError("bridge public key is not pinned")
    raw_public = _b64u_decode(public_key_b64)
    if len(raw_public) != 32:
        raise CommandVerificationError("Ed25519 public key must be 32 bytes")
    expected_key_id = hashlib.sha256(raw_public).hexdigest()[:16]
    if signature.get("key_id") != expected_key_id:
        raise CommandVerificationError("bridge signing key id mismatch")
    raw_sig = _b64u_decode(str(signature.get("value") or ""))
    if len(raw_sig) != 64:
        raise CommandVerificationError("Ed25519 signature must be 64 bytes")

    # SubjectPublicKeyInfo DER prefix for Ed25519 raw public keys.
    der = bytes.fromhex("302a300506032b6570032100") + raw_public
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pem_body = base64.b64encode(der).decode("ascii")
        pem = "-----BEGIN PUBLIC KEY-----\n" + "\n".join(
            pem_body[i:i+64] for i in range(0, len(pem_body), 64)
        ) + "\n-----END PUBLIC KEY-----\n"
        (root / "pub.pem").write_text(pem, encoding="ascii")
        (root / "payload.bin").write_bytes(canonical_payload(payload))
        (root / "sig.bin").write_bytes(raw_sig)
        result = subprocess.run(
            [
                "openssl", "pkeyutl", "-verify", "-pubin",
                "-inkey", str(root / "pub.pem"),
                "-rawin", "-in", str(root / "payload.bin"),
                "-sigfile", str(root / "sig.bin"),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise CommandVerificationError("Ed25519 command signature verification failed")


def verify_envelope(
    envelope: dict[str, Any],
    *,
    public_key_b64: str = PINNED_PUBLIC_KEY_B64,
    now: int | None = None,
) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        raise CommandVerificationError("command envelope must be an object")
    _exact_keys(envelope, {"payload", "signature"}, "envelope")
    payload = envelope["payload"]
    signature = envelope["signature"]
    if not isinstance(payload, dict) or not isinstance(signature, dict):
        raise CommandVerificationError("payload and signature must be objects")
    _exact_keys(payload, PAYLOAD_KEYS, "payload")
    _exact_keys(signature, SIG_KEYS, "signature")

    if payload["schema_version"] != SCHEMA_VERSION:
        raise CommandVerificationError("unsupported command schema")
    if payload["repository"] != REPOSITORY:
        raise CommandVerificationError("command repository mismatch")
    if signature["alg"] != "Ed25519":
        raise CommandVerificationError("unsupported signature algorithm")

    command_id = payload["command_id"]
    if not isinstance(command_id, str) or not re.fullmatch(r"[0-9a-f]{32}", command_id):
        raise CommandVerificationError("invalid command_id")

    issued_at = payload["issued_at"]
    expires_at = payload["expires_at"]
    if not isinstance(issued_at, int) or not isinstance(expires_at, int):
        raise CommandVerificationError("issued_at/expires_at must be integers")
    current = int(time.time()) if now is None else int(now)
    if issued_at > current + 30:
        raise CommandVerificationError("command issued in the future")
    if expires_at <= current:
        raise CommandVerificationError("command expired")
    if expires_at <= issued_at or expires_at - issued_at > 300:
        raise CommandVerificationError("command TTL exceeds policy")

    for field in ("approved_main_sha", "target_base_sha"):
        value = payload[field]
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
            raise CommandVerificationError(f"invalid {field}")

    base_ref = payload["target_base_ref"]
    if (
        not isinstance(base_ref, str)
        or not re.fullmatch(r"[A-Za-z0-9._/-]{1,180}", base_ref)
        or ".." in base_ref
        or base_ref.startswith("/")
        or base_ref.endswith("/")
    ):
        raise CommandVerificationError("invalid target_base_ref")

    task_ids = payload["task_ids"]
    tasks = payload["tasks"]
    if not isinstance(task_ids, list) or not 1 <= len(task_ids) <= 5:
        raise CommandVerificationError("task_ids must contain 1..5 tasks")
    if len(task_ids) != len(set(task_ids)):
        raise CommandVerificationError("duplicate task_id")
    if not isinstance(tasks, list) or len(tasks) != len(task_ids):
        raise CommandVerificationError("tasks/task_ids length mismatch")
    for task_id in task_ids:
        if not isinstance(task_id, str) or not re.fullmatch(r"[A-Z][A-Z0-9.-]{1,31}", task_id):
            raise CommandVerificationError("invalid task_id")

    seen: list[str] = []
    for task in tasks:
        if not isinstance(task, dict):
            raise CommandVerificationError("task route must be an object")
        _exact_keys(task, TASK_KEYS, "task")
        task_id = task["task_id"]
        if task_id not in task_ids:
            raise CommandVerificationError("task route id not in task_ids")
        seen.append(task_id)
        if task["execution_mode"] not in {"ai", "github_native"}:
            raise CommandVerificationError("invalid execution_mode")
        model = task["route_model"]
        if task["execution_mode"] == "ai":
            if model not in {"gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"}:
                raise CommandVerificationError("invalid AI route_model")
        elif model is not None:
            raise CommandVerificationError("github_native route must not declare a model")
        if not isinstance(task["astra_plan_required"], bool) or not isinstance(task["astra_acceptance_required"], bool):
            raise CommandVerificationError("Astra route flags must be booleans")
        allowed = task["allowed_paths"]
        if not isinstance(allowed, list) or any(not isinstance(p, str) or not p for p in allowed):
            raise CommandVerificationError("allowed_paths must be a string list")
    if seen != task_ids:
        raise CommandVerificationError("task route order mismatch")

    budget_raw = payload["package_budget_usd"]
    if not isinstance(budget_raw, str) or not re.fullmatch(r"\d+\.\d{2}", budget_raw):
        raise CommandVerificationError("package budget must be a fixed 2-decimal string")
    budget = Decimal(budget_raw)
    if not Decimal("0.00") <= budget <= Decimal("3.00"):
        raise CommandVerificationError("package budget outside hard policy")

    for flag in ("auto_retry", "auto_merge", "auto_deploy", "auto_ready"):
        if payload[flag] is not False:
            raise CommandVerificationError(f"{flag} must be false")

    _verify_ed25519(payload, signature, public_key_b64)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command_file")
    parser.add_argument("--public-key", default=PINNED_PUBLIC_KEY_B64)
    parser.add_argument("--now", type=int)
    args = parser.parse_args()
    envelope = json.loads(Path(args.command_file).read_text(encoding="utf-8"))
    payload = verify_envelope(envelope, public_key_b64=args.public_key, now=args.now)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
