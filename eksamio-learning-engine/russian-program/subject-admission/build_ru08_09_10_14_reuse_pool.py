#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
BUILD = ENGINE / "build"
sys.path.insert(0, str(BUILD))

import build_russian_exceptions_practice as base  # noqa: E402
import build_russian_exceptions_practice_course_grade as course  # noqa: E402

INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
RU1 = PROGRAM / "semantic-registry" / "RUSSIAN-RU1-121-CARD-ADMISSION-DECISION-v1.0.json"
PRACTICE_MANIFEST = ENGINE / "119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json"
CROSSWALK = PROGRAM / "RUSSIAN-FULL-SUBJECT-PRODUCT-CROSSWALK-v1.1.json"
TARGET_MODULES = ["RU-PROG-08", "RU-PROG-09", "RU-PROG-10", "RU-PROG-14"]
EXPLICIT_RU1_DOMAIN_TO_MODULE = {
    "orthography": "RU-PROG-08",
    "syntactic_norms": "RU-PROG-09",
    "punctuation": "RU-PROG-10",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_active_cards() -> tuple[list[dict[str, Any]], list[str], int]:
    manifest = base.load_json(PRACTICE_MANIFEST)
    items, source_files, expected_active = course.load_course_grade_practice_items(ENGINE, manifest)
    if len(items) != expected_active:
        raise ValueError("reviewed practice builder count drift")
    return items, source_files, expected_active


def main_payload() -> dict[str, Any]:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    school = []
    for row in inventory.get("objects", []):
        if not isinstance(row, dict) or row.get("source_system") != "school_canonical":
            continue
        school.append(
            {
                "semantic_id": str(row["source_id"]),
                "observed_label": str(row.get("observed_label") or ""),
                "observed_meaning": str(row.get("observed_meaning") or ""),
                "authority_status": str(row.get("authority_status") or ""),
                "review_status": str(row.get("review_status") or ""),
                "provenance_refs": list(row.get("evidence_provenance_refs") or []),
            }
        )
    school.sort(key=lambda row: row["semantic_id"])
    if len(school) != 185 or len({row["semantic_id"] for row in school}) != 185:
        raise ValueError(f"canonical school pool must contain exactly 185 identities, got {len(school)}")

    ru1 = json.loads(RU1.read_text(encoding="utf-8"))
    admitted = ru1.get("admitted_identities")
    if not isinstance(admitted, list) or len(admitted) != 12:
        raise ValueError("RU1 authority must contain exactly 12 admitted identities")
    admitted_rows = []
    explicit_target_counts = {module: 0 for module in TARGET_MODULES}
    for row in admitted:
        if not isinstance(row, dict):
            raise ValueError("invalid RU1 identity row")
        semantic_id = str(row["semantic_id"])
        domain = str(row["domain"])
        target_module = EXPLICIT_RU1_DOMAIN_TO_MODULE.get(domain)
        if target_module is not None:
            explicit_target_counts[target_module] += 1
        admitted_rows.append(
            {
                "semantic_id": semantic_id,
                "domain": domain,
                "canonical_label_ru": str(row["canonical_label_ru"]),
                "canonical_definition_ru": str(row["canonical_definition_ru"]),
                "includes": list(row.get("includes") or []),
                "excludes": list(row.get("excludes") or []),
                "source_provenance": list(row.get("source_provenance") or []),
                "explicit_target_module_from_domain_contract": target_module,
            }
        )
    admitted_rows.sort(key=lambda row: row["semantic_id"])

    crosswalk = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    practice_route = next(
        row
        for row in crosswalk["product_routes"]
        if row.get("product_family") == "exceptions_practice"
    )
    route_modules = list(practice_route["modules"])
    if route_modules != ["RU-PROG-07", "RU-PROG-08", "RU-PROG-09", "RU-PROG-10", "RU-PROG-14"]:
        raise ValueError("exceptions-practice routing authority drift")
    if "PRACTICE" not in str(practice_route.get("evidence_role", "")):
        raise ValueError("exceptions-practice evidence role drift")

    cards, source_files, expected_active = load_active_cards()
    if expected_active != 121 or len(cards) != 121:
        raise ValueError(f"reviewed active card count must be 121, got {len(cards)}")
    card_rows = []
    for item in cards:
        practice_id = str(item.get("practice_item_id") or "")
        if not practice_id:
            raise ValueError("active reviewed practice card lacks practice_item_id")
        card_rows.append(
            {
                "practice_item_id": practice_id,
                "exception_id": str(item.get("exception_id") or ""),
                "status": str(item.get("status") or ""),
                "source_practice_bank": str(item.get("source_practice_bank") or ""),
                "semantic_ref_if_present": item.get("semantic_id") or item.get("semantic_ref"),
            }
        )
    card_rows.sort(key=lambda row: row["practice_item_id"])
    if len({row["practice_item_id"] for row in card_rows}) != 121:
        raise ValueError("reviewed practice card IDs are not unique")

    payload: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "REUSE_POOL_READY_NOT_COVERAGE_AUTHORITY",
        "target_modules": TARGET_MODULES,
        "invariants": {
            "asset_presence_equals_requirement_coverage": False,
            "product_route_equals_semantic_mapping": False,
            "reviewed_card_equals_semantic_identity": False,
            "canonical_or_admitted_identity_requires_exact_object_mapping_for_coverage": True,
            "new_content_allowed_before_reuse_check": False,
        },
        "canonical_school_pool": {
            "count": len(school),
            "source": "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json#source_system=school_canonical",
            "identities": school,
        },
        "ru1_admitted_pool": {
            "count": len(admitted_rows),
            "source": "russian-program/semantic-registry/RUSSIAN-RU1-121-CARD-ADMISSION-DECISION-v1.0.json",
            "explicit_target_module_counts": explicit_target_counts,
            "identities": admitted_rows,
        },
        "reviewed_exception_practice_pool": {
            "count": len(card_rows),
            "source": "119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json",
            "route_modules": route_modules,
            "evidence_role": practice_route["evidence_role"],
            "source_files": source_files,
            "cards": card_rows,
        },
    }
    payload["normalized_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = main_payload()
    if args.output:
        Path(args.output).write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RU08_RU09_RU10_RU14_REUSE_POOL=PASS")
        print("canonical_school_identities=185")
        print("ru1_admitted_identities=12")
        print("reviewed_active_cards=121")
        for module, count in payload["ru1_admitted_pool"]["explicit_target_module_counts"].items():
            print(f"{module}.explicit_ru1_admitted={count}")
        print("asset_presence_equals_requirement_coverage=false")
        print("new_content_allowed_before_reuse_check=false")
        print(f"normalized_sha256={payload['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
