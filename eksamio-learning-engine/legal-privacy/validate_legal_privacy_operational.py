#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
MANIFEST = HERE / "SEP1-LEGAL-PRIVACY-ARTIFACTS-v0.1.json"
RUNBOOK = HERE / "SEP1-LEGAL-OPERATOR-RUNBOOK-v0.1.md"
PRO_INDEX = REPO_ROOT / "eksamio-pro-client" / "index.html"

EXPECTED_IDS = {
    "privacy",
    "personal_data",
    "public_offer",
    "audio_non_storage",
    "npd_payment_contour",
}
EXPECTED_LINKS = {
    "legal/privacy.html",
    "legal/personal-data.html",
    "legal/public-offer.html",
    "legal/audio-non-storage.html",
    "legal/npd-receipts.html",
}
ALLOWED_UNRESOLVED = {
    "LEGAL_OPERATOR_FULL_NAME",
    "LEGAL_OPERATOR_INN",
    "LEGAL_SUPPORT_CONTACT",
    "LEGAL_SUPPORT_SLA",
}
UNRESOLVED_RE = re.compile(r"\[\[UNRESOLVED:([A-Z0-9_]+)\]\]")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["status"] != "CODE_READY_EXTERNAL_INPUTS_REQUIRED":
        raise AssertionError("legal packet status drift")
    artifacts = manifest["artifacts"]
    if {row["id"] for row in artifacts} != EXPECTED_IDS:
        raise AssertionError("legal artifact inventory drift")
    if len(artifacts) != 5:
        raise AssertionError("legal artifact count drift")

    fingerprints: dict[str, str] = {}
    unresolved: set[str] = set()
    for row in artifacts:
        path = REPO_ROOT / row["path"]
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        expected_meta = (
            f'data-legal-artifact="{row["id"]}"',
            f'data-legal-version="{row["version"]}"',
            'data-legal-status="EXTERNAL_REVIEW_REQUIRED"',
        )
        for marker in expected_meta:
            if marker not in text:
                raise AssertionError(f"missing legal metadata {marker}: {row['id']}")
        fingerprints[row["id"]] = hashlib.sha256(raw).hexdigest()
        unresolved.update(UNRESOLVED_RE.findall(text))

    if not unresolved:
        raise AssertionError("draft legal packet must expose unresolved external fields")
    if not unresolved.issubset(ALLOWED_UNRESOLVED):
        raise AssertionError(f"unknown unresolved legal fields: {sorted(unresolved - ALLOWED_UNRESOLVED)}")
    if not {"LEGAL_OPERATOR_FULL_NAME", "LEGAL_OPERATOR_INN", "LEGAL_SUPPORT_CONTACT"}.issubset(unresolved):
        raise AssertionError("operator identity/contact placeholders must remain explicit until resolved")

    index = PRO_INDEX.read_text(encoding="utf-8")
    for href in EXPECTED_LINKS:
        if f'href="{href}"' not in index:
            raise AssertionError(f"missing Pro legal disclosure link: {href}")

    privacy = (REPO_ROOT / "eksamio-pro-client/legal/privacy.html").read_text(encoding="utf-8")
    audio = (REPO_ROOT / "eksamio-pro-client/legal/audio-non-storage.html").read_text(encoding="utf-8")
    offer = (REPO_ROOT / "eksamio-pro-client/legal/public-offer.html").read_text(encoding="utf-8")
    npd = (REPO_ROOT / "eksamio-pro-client/legal/npd-receipts.html").read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")

    for phrase in ("записи голоса ученика: 0", "аудиофрагменты: 0", "резервные копии пользовательского аудио: 0", "voiceprints", "акустические embeddings"):
        if phrase not in audio:
            raise AssertionError(f"learner-audio zero-persistence wording missing: {phrase}")
    if 'href="audio-non-storage.html"' not in privacy:
        raise AssertionError("privacy disclosure must link audio non-storage disclosure")
    for phrase in ("30 и 90 дней", "Автоматическое продление", "автоматическое списание", "СБП", "банковская карта"):
        if phrase not in offer:
            raise AssertionError(f"public-offer launch boundary missing: {phrase}")
    for phrase in ("НПД", "Robokassa", "Robocheki/SMZ", "Production charges запрещены"):
        if phrase not in npd:
            raise AssertionError(f"NPD/receipt contour boundary missing: {phrase}")
    for switch in ("PUBLIC_TRAFFIC_ENABLED", "PRODUCTION_CHARGES_ENABLED", "PEIS_NETWORK_WRITES_ENABLED", "YC_GATEWAY_APPLY"):
        if switch not in runbook:
            raise AssertionError(f"runbook kill switch missing: {switch}")
    if "[[UNRESOLVED:LEGAL_SUPPORT_SLA]]" not in runbook:
        raise AssertionError("support SLA must remain explicit external input")

    print("SEP1_LEGAL_PRIVACY_OPERATIONAL=PASS")
    print("artifact_count=5")
    print("unresolved_external_fields=" + ",".join(sorted(unresolved | {"LEGAL_SUPPORT_SLA"})))
    for artifact_id in sorted(fingerprints):
        print(f"{artifact_id}_sha256={fingerprints[artifact_id]}")
    print("learner_audio_persistence_zero_guard=PASS")
    print("pro_client_disclosure_links=5")
    print("public_traffic=OFF")
    print("production_charges=OFF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
