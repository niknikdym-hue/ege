#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
REPO_ROOT = ENGINE.parent
MANIFEST = HERE / "LEGAL-PRODUCTION-ARTIFACT-SET-v0.1.json"
PRO_CLIENT = REPO_ROOT / "eksamio-pro-client" / "index.html"


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def artifact_set_fingerprint() -> tuple[str, list[dict[str, str]]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    for artifact in manifest["artifacts"]:
        path = ENGINE / artifact["path"]
        if not path.is_file():
            raise AssertionError(f"missing legal artifact: {artifact['path']}")
        rows.append(
            {
                "id": artifact["id"],
                "version": artifact["version"],
                "path": artifact["path"],
                "git_blob_sha1": git_blob_sha1(path),
            }
        )
    canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest(), rows


def validate() -> dict[str, object]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["status"] == "CODE_READY_EXTERNAL_ACCEPTANCE_REQUIRED"
    assert manifest["not_legal_advice"] is True
    assert manifest["launch_invariants"] == {
        "learner_audio_persisted": 0,
        "saved_card": False,
        "auto_renew": False,
        "public_traffic_enabled": False,
        "production_charges_enabled": False,
    }

    fingerprint, rows = artifact_set_fingerprint()
    ids = {row["id"] for row in rows}
    assert ids == {
        "privacy_policy",
        "public_offer",
        "learner_audio_non_storage",
        "npd_payment_receipt",
        "operator_runbook",
        "legal_readiness",
    }

    privacy = (HERE / "PUBLIC-PRIVACY-POLICY-DRAFT-v0.1.md").read_text(encoding="utf-8")
    offer = (HERE / "PUBLIC-OFFER-DRAFT-v0.1.md").read_text(encoding="utf-8")
    audio = (HERE / "LEARNER-AUDIO-NON-STORAGE-DISCLOSURE-v0.1.md").read_text(encoding="utf-8")
    payment = (HERE / "NPD-PAYMENT-RECEIPT-DISCLOSURE-v0.1.md").read_text(encoding="utf-8")
    runbook = (HERE / "OPERATOR-RUNBOOK-v0.1.md").read_text(encoding="utf-8")
    index = PRO_CLIENT.read_text(encoding="utf-8")

    # Fail closed: unresolved legal/operator facts must never masquerade as accepted publication.
    assert "NOT FOR PUBLICATION" in privacy
    assert "BLOCKED_EXTERNAL" in offer and "NOT FOR PUBLICATION" in offer
    assert "BLOCKED_EXTERNAL" in audio
    assert "BLOCKED_EXTERNAL" in payment
    assert "[OPERATOR_LEGAL_NAME_OR_FIO]" in privacy
    assert "[OPERATOR_LEGAL_NAME_OR_FIO]" in offer
    assert "[SUPPORT_CONTACT]" in offer

    # Product/legal invariants that must not drift during external review.
    combined_audio = privacy + "\n" + audio
    for phrase in ("аудиозапись ученика не сохраняется", "voiceprint", "embeddings"):
        assert phrase.casefold() in combined_audio.casefold(), phrase
    assert "автопродлен" in offer.casefold() or "автоматического продления" in offer.casefold()
    assert "СБП" in offer and "банковск" in offer.casefold()
    assert "Robokassa" in payment and "Robocheki" in payment
    for switch in (
        "PUBLIC_TRAFFIC_ENABLED=false",
        "PRODUCTION_CHARGES_ENABLED=false",
    ):
        assert switch in runbook, switch

    # The launch surface must expose stable disclosure routes even while publication is externally blocked.
    for route in manifest["required_client_routes"]:
        href = route["href"]
        marker = f'data-legal-link="{route["id"]}"'
        assert href in index, href
        assert marker in index, marker

    fields = manifest["external_acceptance_fields"]
    assert "LEGAL_ARTIFACT_SET_ACCEPTED_FINGERPRINT" in fields
    assert len(fields) == len(set(fields))

    return {
        "status": "PASS_CODE_READY_EXTERNAL_ACCEPTANCE_REQUIRED",
        "artifact_set_fingerprint": fingerprint,
        "artifact_count": len(rows),
        "required_client_routes": len(manifest["required_client_routes"]),
        "missing_external_fields": fields,
    }


def main() -> int:
    result = validate()
    print("SEP1_LEGAL_LAUNCH_VALIDATION=PASS")
    print(f"artifact_set_fingerprint={result['artifact_set_fingerprint']}")
    print(f"artifact_count={result['artifact_count']}")
    print(f"required_client_routes={result['required_client_routes']}")
    print("external_acceptance_required=" + ",".join(result["missing_external_fields"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
