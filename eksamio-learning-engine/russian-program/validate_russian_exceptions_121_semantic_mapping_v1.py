#!/usr/bin/env python3
"""Materialize and validate the bounded RU-1 121-card semantic mapping."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROGRAM = ROOT / "eksamio-learning-engine" / "russian-program"
DECISION = PROGRAM / "semantic-registry" / "RUSSIAN-RU1-121-CARD-ADMISSION-DECISION-v1.0.json"
REGISTRY = PROGRAM / "semantic-registry" / "RUSSIAN-SEMANTIC-REGISTRY-RU1-v1.0.json"
MAPPING = PROGRAM / "RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json"
LEDGER_REV = "6211b3f80f75d8c26c25ca8578f883d861ac254d"
LEDGER_PATH = "eksamio-learning-engine/russian-program/RUSSIAN-EXCEPTIONS-121-PEIS-INTEGRATION-LEDGER-v0.1.json"
BASELINE = "f7107e1eacce9ac21ce92fcf2778bcaeb649d069"
ALLOWED = {
    "eksamio-learning-engine/russian-program/semantic-registry/RUSSIAN-SEMANTIC-REGISTRY-RU1-v1.0.json",
    "eksamio-learning-engine/russian-program/RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json",
    "eksamio-learning-engine/russian-program/validate_russian_exceptions_121_semantic_mapping_v1.py",
    "eksamio-learning-engine/russian-program/RUSSIAN-RU1-121-MAPPING-VALIDATION-v1.0.json",
}


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_bytes(value))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def historical_ledger() -> dict:
    result = subprocess.run(
        ["git", "show", f"{LEDGER_REV}:{LEDGER_PATH}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def materialize() -> None:
    decision = read_json(DECISION)
    ledger = historical_ledger()
    admitted = decision["admitted_identities"]
    admitted_ids = {item["semantic_id"] for item in admitted}
    resolved = {row[0]: row[2] for row in decision["resolved_rows"]}
    partial = {row[0]: row[1] for row in decision["partial_composite_rows_preserved"]}
    codebook = ledger["semantic_codebook"]
    output_rows = []

    for practice_item_id, exception_id, class_code, semantic_codes, candidate_codes, gap_code in ledger["rows"]:
        if practice_item_id in resolved:
            resolution = "EXACT"
            target_ids = [resolved[practice_item_id]]
        elif class_code == "E":
            resolution = "EXACT"
            target_ids = [codebook[code] for code in semantic_codes]
        elif class_code == "P":
            resolution = "PARTIAL_COMPOSITE"
            target_ids = [codebook[code] for code in semantic_codes]
        else:
            raise ValueError(f"unresolved non-RU1 row: {practice_item_id}")
        output_rows.append({
            "practice_item_id": practice_item_id,
            "exception_id": exception_id,
            "mapping_resolution": resolution,
            "semantic_target_ids": target_ids,
            "integration_ready": True,
            "live_connected": False,
        })

    if {row["practice_item_id"] for row in output_rows if row["mapping_resolution"] == "PARTIAL_COMPOSITE"} != set(partial):
        raise ValueError("historical partial-row set differs from Central Brain decision")
    for row in output_rows:
        if row["practice_item_id"] in partial and row["semantic_target_ids"] != partial[row["practice_item_id"]]:
            raise ValueError(f"partial target mutation: {row['practice_item_id']}")
    if not all(target in admitted_ids for target in resolved.values()):
        raise ValueError("decision resolves a row to a non-admitted RU identity")

    registry = {
        "schema_version": "1.0.0",
        "registry_version": "RUSSIAN-SEMANTIC-REGISTRY-RU1-v1.0",
        "status": "CANONICAL_RU1_MATERIALIZED",
        "subject_id": "russian",
        "admission_decision_ref": "RUSSIAN-RU1-121-CARD-ADMISSION-DECISION-v1.0.json",
        "preserved_school_identity_count": 185,
        "canonical_new_ru_identity_count": len(admitted),
        "identities": [{
            "semantic_id": item["semantic_id"],
            "entity_type": item["entity_type"],
            "domain": item["domain"],
            "canonical_label_ru": item["canonical_label_ru"],
            "canonical_definition_ru": item["canonical_definition_ru"],
            "includes": item["includes"],
            "excludes": item["excludes"],
            "parent_ids": [],
            "prerequisite_ids": [],
            "status": "CANONICAL_ADMITTED_RU1",
            "admission_basis": item["proposal_basis"],
            "source_provenance_refs": item["source_provenance"],
        } for item in admitted],
    }
    mapping = {
        "schema_version": "1.0.0",
        "mapping_version": "RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0",
        "status": "RUSSIAN_RU1_121_MAPPING_READY_FOR_SERVICE_CONNECTION",
        "subject_id": "russian",
        "admission_decision_ref": "semantic-registry/RUSSIAN-RU1-121-CARD-ADMISSION-DECISION-v1.0.json",
        "historical_evidence": {
            "ledger_pr_head": LEDGER_REV,
            "ledger_path": LEDGER_PATH,
            "ledger_sha256": hashlib.sha256(canonical_bytes(ledger)).hexdigest(),
            "pr57_head": "572a3764ff9d5b99b8d1d61aec64d89eb079e013",
            "pr23_head": "2215e47b5c211cbff7e12d5b823a0a835adb7480",
        },
        "counts": {
            "active_cards": len(output_rows),
            "represented_exception_ids": len({row["exception_id"] for row in output_rows}),
            "exact": sum(row["mapping_resolution"] == "EXACT" for row in output_rows),
            "partial_composite": sum(row["mapping_resolution"] == "PARTIAL_COMPOSITE" for row in output_rows),
            "blocked": 0,
            "integration_ready": sum(row["integration_ready"] for row in output_rows),
            "live_connected": sum(row["live_connected"] for row in output_rows),
            "canonical_ru_ids_admitted": len(admitted),
            "canonical_school_ids": 185,
        },
        "rows": output_rows,
    }
    write_json(REGISTRY, registry)
    write_json(MAPPING, mapping)


def validate() -> dict:
    decision, registry, mapping = read_json(DECISION), read_json(REGISTRY), read_json(MAPPING)
    expected_ru = {item["semantic_id"] for item in decision["admitted_identities"]}
    registry_ru = {item["semantic_id"] for item in registry["identities"]}
    rows = mapping["rows"]
    assert len(rows) == 121
    assert len({row["practice_item_id"] for row in rows}) == 121
    assert len({row["exception_id"] for row in rows}) == 88
    resolutions = Counter(row["mapping_resolution"] for row in rows)
    assert resolutions == Counter({"EXACT": 116, "PARTIAL_COMPOSITE": 5})
    assert all(row["integration_ready"] and not row["live_connected"] for row in rows)
    assert registry_ru == expected_ru and len(registry_ru) == 12
    assert all(item["parent_ids"] == [] and item["prerequisite_ids"] == [] for item in registry["identities"])
    targets = {target for row in rows for target in row["semantic_target_ids"]}
    assert not any(target.startswith("candidate-") for target in targets)
    assert {target for target in targets if target.startswith("ru-")} == expected_ru
    assert not {"candidate-015", "candidate-053", "candidate-025", "candidate-018"} & targets
    resolved = {row[0]: row[2] for row in decision["resolved_rows"]}
    row_by_id = {row["practice_item_id"]: row for row in rows}
    for practice_item_id, target in resolved.items():
        assert row_by_id[practice_item_id]["mapping_resolution"] == "EXACT"
        assert row_by_id[practice_item_id]["semantic_target_ids"] == [target]
    partial = {row[0]: row[1] for row in decision["partial_composite_rows_preserved"]}
    for practice_item_id, expected_targets in partial.items():
        assert row_by_id[practice_item_id]["mapping_resolution"] == "PARTIAL_COMPOSITE"
        assert row_by_id[practice_item_id]["semantic_target_ids"] == expected_targets
    school_denominator = read_json(ROOT / "eksamio-learning-engine" / "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json")
    assert school_denominator["final_school_canonical_denominator"] == 185
    changed = subprocess.run(["git", "diff", "--name-only", BASELINE, "--"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    assert set(changed) <= ALLOWED, f"out-of-scope changed paths: {sorted(set(changed) - ALLOWED)}"
    assert mapping["counts"] == {
        "active_cards": 121, "represented_exception_ids": 88, "exact": 116,
        "partial_composite": 5, "blocked": 0, "integration_ready": 121,
        "live_connected": 0, "canonical_ru_ids_admitted": 12,
        "canonical_school_ids": 185,
    }
    return {
        "status": mapping["status"],
        "ACTIVE_ROWS": 121,
        "UNIQUE_PRACTICE_ITEM_IDS": 121,
        "EXCEPTION_IDS": 88,
        "EXACT": 116,
        "PARTIAL_COMPOSITE": 5,
        "BLOCKED": 0,
        "INTEGRATION_READY": 121,
        "LIVE_CONNECTED": 0,
        "CANONICAL_RU_IDS_ADMITTED": 12,
        "CANONICAL_SCHOOL_IDS": 185,
        "SCHOOL_IDS_CHANGED": 0,
        "CANDIDATE_REFS_AS_MASTERY_KEYS": 0,
        "PARTIAL_COMPOSITE_ROWS_PRESERVED": "5/5",
        "RUSSIAN_DEMOS_CHANGED": 0,
        "TILDA_CHANGED": 0,
        "SHARED_PEIS_CONTRACTS_CHANGED": 0,
        "PRODUCTION_CONNECTION_CHANGED": 0,
        "REGISTRY_SHA256": sha256(REGISTRY),
        "MAPPING_SHA256": sha256(MAPPING),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--materialize", action="store_true")
    parser.add_argument("--write-validation", action="store_true")
    args = parser.parse_args()
    if args.materialize:
        materialize()
    result = validate()
    if args.write_validation:
        write_json(PROGRAM / "RUSSIAN-RU1-121-MAPPING-VALIDATION-v1.0.json", result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
