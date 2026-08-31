#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
CONTENT_DIR = PROGRAM / "production-learning-content"
BOUNDARY_BUILDER_OUTPUT = HERE / "RU09-SYNTAX-REUSE-FIRST-BOUNDARY-REVIEW.json"

EXPECTED_CANDIDATES = {
    "candidate-028",
    "candidate-029",
    "candidate-030",
    "candidate-031",
    "candidate-032",
}
SUPPORT_SYSTEMS = {"exception_item", "practice_item", "trainer_item"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main_payload() -> dict[str, Any]:
    if not BOUNDARY_BUILDER_OUTPUT.exists():
        raise ValueError("RU09 boundary review must be materialized before content-gap review")
    boundary = json.loads(BOUNDARY_BUILDER_OUTPUT.read_text(encoding="utf-8"))
    if boundary.get("status") != "CENTRAL_BRAIN_RU09_SYNTAX_REUSE_FIRST_BOUNDARY_REVIEW_IN_PROGRESS_NO_NEW_ADMISSION":
        raise ValueError("RU09 boundary review status drift")
    candidate_rows = boundary.get("candidate_boundary")
    if not isinstance(candidate_rows, list) or {row.get("candidate_ref") for row in candidate_rows if isinstance(row, dict)} != EXPECTED_CANDIDATES:
        raise ValueError("RU09 candidate boundary mismatch")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    content_files = sorted(CONTENT_DIR.glob("*.json"))
    content_text = {path: path.read_text(encoding="utf-8") for path in content_files}

    rows: list[dict[str, Any]] = []
    for candidate in sorted(candidate_rows, key=lambda row: str(row.get("candidate_ref"))):
        candidate_ref = str(candidate["candidate_ref"])
        taxonomy_ref = str(candidate["taxonomy_ref"])
        meaning = str(candidate["meaning_ru"])
        if candidate.get("candidate_review_status") != "draft":
            raise ValueError(f"RU09 candidate is no longer draft: {candidate_ref}")
        if candidate.get("taxonomy_source_status") != "current_source_verified":
            raise ValueError(f"RU09 taxonomy backing not source-verified: {candidate_ref}")

        support: list[dict[str, str]] = []
        for obj in objects:
            if obj.get("source_system") not in SUPPORT_SYSTEMS or obj.get("authority_status") != "current":
                continue
            refs = {str(ref) for ref in (obj.get("current_semantic_refs") or [])}
            if taxonomy_ref not in refs:
                continue
            support.append(
                {
                    "source_system": str(obj.get("source_system")),
                    "source_id": str(obj.get("source_id")),
                    "observed_label": str(obj.get("observed_label") or ""),
                    "review_status": str(obj.get("review_status") or ""),
                }
            )
        support.sort(key=lambda row: (row["source_system"], row["source_id"]))

        bundle_refs: list[str] = []
        for path, text in content_text.items():
            # Exact refs only. This is a content-presence probe, not a semantic similarity test.
            if taxonomy_ref in text or candidate_ref in text:
                bundle_refs.append(str(path.relative_to(PROGRAM)))

        rows.append(
            {
                "candidate_ref": candidate_ref,
                "taxonomy_ref": taxonomy_ref,
                "meaning_ru": meaning,
                "candidate_status": "draft_not_admitted",
                "exact_school_meaning_matches": list(candidate.get("exact_school_meaning_matches") or []),
                "supporting_current_assets": support,
                "support_counts": {
                    "exception_items": sum(row["source_system"] == "exception_item" for row in support),
                    "practice_items": sum(row["source_system"] == "practice_item" for row in support),
                    "trainer_items": sum(row["source_system"] == "trainer_item" for row in support),
                },
                "production_learning_bundle_refs": bundle_refs,
                "content_gap_status": (
                    "PRODUCTION_LEARNER_CONTENT_PRESENT_REQUIRES_EXACT_SCOPE_REVIEW"
                    if bundle_refs
                    else "CONTENT_GAP_CONFIRMED_NO_PRODUCTION_LEARNER_CONTENT_BUNDLE"
                ),
                "admission_effect": "NONE",
            }
        )

    gaps = [row for row in rows if row["content_gap_status"] == "CONTENT_GAP_CONFIRMED_NO_PRODUCTION_LEARNER_CONTENT_BUNDLE"]
    payload: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU09_CONTENT_GAP_REVIEW_COMPLETE_NO_ADMISSION",
        "module_id": "RU-PROG-09",
        "policy": {
            "reuse_check_precedes_new_content": True,
            "supporting_exception_or_practice_item_is_full_production_bundle": False,
            "trainer_item_semantic_ref_is_subject_admission": False,
            "content_presence_is_semantic_admission": False,
            "content_gap_proves_semantic_uniqueness": False,
            "new_content_may_self_admit_candidate": False,
            "keyword_or_fuzzy_semantic_inference_allowed": False,
        },
        "summary": {
            "draft_candidates_reviewed": len(rows),
            "candidates_with_source_verified_taxonomy_backing": len(rows),
            "candidates_with_existing_production_bundle": len(rows) - len(gaps),
            "confirmed_production_content_gaps": len(gaps),
            "candidates_with_supporting_current_exception_practice_or_trainer_assets": sum(bool(row["supporting_current_assets"]) for row in rows),
            "new_semantic_admissions": 0,
            "new_object_level_closures": 0,
            "false_exact_mastery_admissions": 0,
        },
        "candidates": rows,
        "next_safe_content_action": (
            "MATERIALIZE_ORIGINAL_EKSAMIO_BOUNDED_LEARNER_CONTENT_FOR_CONFIRMED_GAPS_AS_SUBJECT_ACCEPTANCE_REQUIRED_ONLY"
            if gaps
            else "REVIEW_EXISTING_BUNDLE_SCOPE_BEFORE_ANY_ADMISSION"
        ),
    }
    payload["normalized_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
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
        print("RU09_CANDIDATE_CONTENT_GAP_REVIEW=PASS")
        for key, value in payload["summary"].items():
            print(f"{key}={value}")
        for row in payload["candidates"]:
            counts = row["support_counts"]
            print(
                f"{row['candidate_ref']}={row['content_gap_status']}|"
                f"exception={counts['exception_items']}|practice={counts['practice_items']}|trainer={counts['trainer_items']}"
            )
        print(f"normalized_sha256={payload['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
