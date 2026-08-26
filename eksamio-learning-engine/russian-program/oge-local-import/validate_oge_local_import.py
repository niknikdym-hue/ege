#!/usr/bin/env python3
"""Deterministic integrity validator for the owner-authored Russian OGE import."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ALLOWED_SCORING = {"exact_match", "self_check"}
ROOT = Path(__file__).resolve().parents[2]
IMPORT_ROOT = Path(__file__).resolve().parent


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> int:
    manifest_path = IMPORT_ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("items", [])
    actual = sorted((IMPORT_ROOT / "items").glob("*.json"))
    declared = sorted(ROOT / row["repository_path"] for row in rows)
    if actual != declared:
        fail("manifest item paths differ from actual item files")
    identities: set[str] = set()
    asset_refs: set[Path] = set()
    for row, path in zip(rows, declared):
        payload = json.loads(path.read_text(encoding="utf-8"))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != row.get("content_hash"):
            fail(f"content hash mismatch: {path}")
        if not row.get("has_answer") or not payload.get("answer"):
            fail(f"required answer absent: {path}")
        if payload["answer"].get("value", payload["answer"].get("sample")) in (None, "", []):
            fail(f"required answer empty: {path}")
        scoring = payload.get("scoring", {}).get("type")
        if scoring not in ALLOWED_SCORING or scoring != row.get("scoring_type"):
            fail(f"unsupported or inconsistent scoring: {path}")
        mapping = payload.get("ru_prog_mapping")
        if not mapping or mapping != row.get("ru_prog_mapping") or any(not x.startswith("RU-PROG-") for x in mapping):
            fail(f"missing or inconsistent RU-PROG mapping: {path}")
        identity = payload.get("semantic_identity", {}).get("id")
        if not identity or identity in identities:
            fail(f"missing or duplicate identity: {identity}")
        identities.add(identity)
        if payload.get("semantic_identity", {}).get("status") != "PROPOSED_NOT_CANONICAL":
            fail(f"unaccepted identity crossed admission boundary: {path}")
        for asset in payload.get("assets", []):
            asset_path = ROOT / asset
            if not asset_path.is_file():
                fail(f"broken asset: {asset}")
            asset_refs.add(asset_path)
        if payload["task_number"] != row["task_number"] or payload["variant"] != row["variant"]:
            fail(f"manifest metadata mismatch: {path}")
    actual_assets = set((IMPORT_ROOT / "assets").rglob("*"))
    actual_assets = {path for path in actual_assets if path.is_file()}
    if actual_assets != asset_refs:
        fail("manifest asset paths differ from actual asset files")
    if len(rows) != 40:
        fail(f"expected 40 imported items, found {len(rows)}")
    print(f"PASS: {len(rows)} items, {len(asset_refs)} assets, {len(identities)} unique proposed identities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
