#!/usr/bin/env python3
"""Deterministic integrity and rights validator for the Russian OGE import."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ALLOWED_SCORING = {"exact_match", "self_check"}
ROOT = Path(__file__).resolve().parents[2]
IMPORT_ROOT = Path(__file__).resolve().parent
TASK1_RIGHTS_GATE = IMPORT_ROOT / "TASK1-RIGHTS-GATE-v1.0.json"
RIGHTS_BLOCKED = "RIGHTS_BLOCKED"
EXCLUDED_RIGHTS_BLOCKED = "EXCLUDED_RIGHTS_BLOCKED"
NOT_PROVEN = "NOT_PROVEN"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def validate_task1_rights(
    payload: dict,
    row: dict,
    path: Path,
    gate_entry: dict,
) -> set[Path]:
    provenance = payload.get("provenance", {})
    if provenance.get("authorship") != NOT_PROVEN:
        fail(f"Task 1 authorship must be NOT_PROVEN: {path}")
    if provenance.get("rights_status") != RIGHTS_BLOCKED:
        fail(f"Task 1 provenance must be RIGHTS_BLOCKED: {path}")
    if provenance.get("production_admission") != EXCLUDED_RIGHTS_BLOCKED:
        fail(f"Task 1 content crossed rights admission boundary: {path}")
    if provenance.get("rights_authority") is not None:
        fail(f"Task 1 has unsupported rights authority: {path}")
    if "OWNER_AUTHORED_LOCAL_MATERIAL" in json.dumps(payload, ensure_ascii=False):
        fail(f"Task 1 still asserts owner authorship: {path}")

    rights = payload.get("rights", {})
    required = {
        "content_status": RIGHTS_BLOCKED,
        "production_admission": EXCLUDED_RIGHTS_BLOCKED,
        "authorship": NOT_PROVEN,
        "rights_authority": None,
    }
    for key, expected in required.items():
        if rights.get(key) != expected:
            fail(f"Task 1 rights.{key} mismatch: {path}")

    assets = payload.get("assets", [])
    if len(assets) != 2:
        fail(f"Task 1 must preserve exactly MP3+transcript refs: {path}")
    rights_assets = rights.get("assets", [])
    if {entry.get("path") for entry in rights_assets} != set(assets):
        fail(f"Task 1 rights asset set mismatch: {path}")
    for asset in rights_assets:
        if asset.get("rights_status") != RIGHTS_BLOCKED:
            fail(f"Task 1 asset not rights-blocked: {path}")
        if asset.get("production_admission") != EXCLUDED_RIGHTS_BLOCKED:
            fail(f"Task 1 asset crossed production admission boundary: {path}")
        if asset.get("authorship") != NOT_PROVEN:
            fail(f"Task 1 asset asserts unsupported authorship: {path}")
        if asset.get("rights_authority") is not None:
            fail(f"Task 1 asset asserts unsupported rights authority: {path}")

    if gate_entry.get("item_id") != payload.get("item_id"):
        fail(f"Task 1 rights-gate item mismatch: {path}")
    if set(gate_entry.get("assets", [])) != set(assets):
        fail(f"Task 1 rights-gate asset mismatch: {path}")
    actual_blob = git_blob_sha1(path)
    if gate_entry.get("git_blob_sha1") != actual_blob:
        fail(f"Task 1 rights-gate blob fingerprint mismatch: {path}")

    # The pre-repair manifest row contains a SHA-256 of the former item bytes and
    # an inferred provenance claim. For Task 1 only, the versioned rights gate
    # explicitly supersedes those two manifest fields. All other manifest fields
    # remain validated below; Tasks 2-8 retain normal manifest SHA-256 checking.
    if row.get("task_number") != 1:
        fail(f"internal Task 1 validation misuse: {path}")

    return {ROOT / asset for asset in assets}


def main() -> int:
    manifest_path = IMPORT_ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("items", [])
    actual = sorted((IMPORT_ROOT / "items").glob("*.json"))
    declared = sorted(ROOT / row["repository_path"] for row in rows)
    if actual != declared:
        fail("manifest item paths differ from actual item files")

    gate = json.loads(TASK1_RIGHTS_GATE.read_text(encoding="utf-8"))
    if gate.get("status") != RIGHTS_BLOCKED:
        fail("Task 1 rights gate is not RIGHTS_BLOCKED")
    if gate.get("production_admission") != EXCLUDED_RIGHTS_BLOCKED:
        fail("Task 1 rights gate is not excluded from production")
    if gate.get("authorship") != NOT_PROVEN or gate.get("rights_authority") is not None:
        fail("Task 1 rights gate asserts unsupported authority")
    if gate.get("supersedes_manifest_task1_provenance") is not True:
        fail("Task 1 rights gate does not explicitly supersede stale manifest provenance")
    gate_entries = {entry["item_id"]: entry for entry in gate.get("variants", [])}
    if len(gate_entries) != gate.get("expected_variant_count") or len(gate_entries) != 5:
        fail("Task 1 rights gate must contain exactly five variants")

    identities: set[str] = set()
    asset_refs: set[Path] = set()
    task1_variants = 0
    task1_assets: set[Path] = set()

    for row, path in zip(rows, declared):
        payload = json.loads(path.read_text(encoding="utf-8"))
        task_number = payload.get("task_number")
        if task_number == 1:
            item_id = payload.get("item_id")
            if item_id not in gate_entries:
                fail(f"Task 1 item missing from rights gate: {path}")
            blocked_assets = validate_task1_rights(payload, row, path, gate_entries[item_id])
            task1_variants += 1
            task1_assets.update(blocked_assets)
        else:
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
        if task_number != row["task_number"] or payload["variant"] != row["variant"]:
            fail(f"manifest metadata mismatch: {path}")

    actual_assets = {path for path in (IMPORT_ROOT / "assets").rglob("*") if path.is_file()}
    if actual_assets != asset_refs:
        fail("manifest asset paths differ from actual asset files")
    if len(rows) != 40:
        fail(f"expected 40 imported items, found {len(rows)}")
    if task1_variants != 5:
        fail(f"expected 5 rights-blocked Task 1 variants, found {task1_variants}")
    if len(task1_assets) != 10 or len(task1_assets) != gate.get("expected_asset_count"):
        fail(f"expected 10 rights-blocked Task 1 assets, found {len(task1_assets)}")

    print(
        "PASS: "
        f"{len(rows)} items, {len(asset_refs)} assets, {len(identities)} unique proposed identities, "
        f"{task1_variants} Task-1 variants rights-blocked, {len(task1_assets)} Task-1 assets rights-blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
