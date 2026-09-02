#!/usr/bin/env python3
"""Fail-closed source-bound composite frontier for FIPI OGE 2026 codifier position 6.14.

OGE_COD 6.14 is an orthographic-analysis operation over already existing spelling
skills. It is not a new school semantic identity. This gate deliberately does not
invent a canonical owner set, admit semantics, materialize learner evidence, or
close the object. The exact applicable component set must be derived separately
from current accepted orthography authorities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"

OFFICIAL_SOURCE_SYSTEM = "OGE_COD"
OFFICIAL_CODE = "6.14"
OFFICIAL_LABEL = "Орфографический анализ"
EXPECTED_PLACEHOLDER = "all applicable active orthography identities"
EXPECTED_CLASSIFICATION = "EXAM_ONLY_COMPOSITE"
EXPECTED_NOTE = "Rule identification/application over existing skills; zero school-count effect."


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized_sha(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_review() -> dict[str, Any]:
    overlay = _load(OVERLAY)
    positions = [
        row
        for row in overlay.get("orthography_codifier_overlay", [])
        if str(row.get("position")) == OFFICIAL_CODE
    ]
    if len(positions) != 1:
        raise RuntimeError(f"expected exactly one historical overlay row for {OFFICIAL_CODE}, got {len(positions)}")

    row = positions[0]
    if row.get("classification") != EXPECTED_CLASSIFICATION:
        raise RuntimeError(
            f"6.14 classification drifted: expected={EXPECTED_CLASSIFICATION!r} actual={row.get('classification')!r}"
        )
    if row.get("topic") != "orthographic analysis":
        raise RuntimeError(f"6.14 topic drifted: {row.get('topic')!r}")
    if row.get("owners") != [EXPECTED_PLACEHOLDER]:
        raise RuntimeError(
            "6.14 overlay must remain a composite placeholder, not a fabricated canonical owner set: "
            f"actual={row.get('owners')!r}"
        )
    if row.get("note") != EXPECTED_NOTE:
        raise RuntimeError(f"6.14 note drifted: {row.get('note')!r}")
    if EXPECTED_PLACEHOLDER.startswith("school-"):
        raise RuntimeError("composite placeholder unexpectedly looks like a school canonical identity")

    task_rows = [
        item
        for item in overlay.get("exam_task_map", [])
        if str(item.get("tasks")) == "6-7"
    ]
    if len(task_rows) != 1:
        raise RuntimeError(f"expected exactly one OGE task 6-7 orthography composite row, got {len(task_rows)}")
    task_row = task_rows[0]
    if task_row.get("official_route") != "orthographic analysis":
        raise RuntimeError("OGE task 6-7 official route drifted")
    if task_row.get("classification") != EXPECTED_CLASSIFICATION:
        raise RuntimeError("OGE task 6-7 is no longer classified as an exam-only composite")
    if task_row.get("school_identity_families") != [
        "all applicable active orthography identities mapped below"
    ]:
        raise RuntimeError("OGE task 6-7 composite family placeholder drifted")

    second_pass = overlay.get("second_pass_result") or {}
    if second_pass.get("school_reopen_candidates") != 0:
        raise RuntimeError("historical FIPI backstop no longer proves zero school reopen candidates")
    if second_pass.get("unowned_official_school_orthography_topics") != 0:
        raise RuntimeError("historical FIPI backstop no longer proves zero unowned official orthography topics")
    if second_pass.get("school_count_effect") != 0:
        raise RuntimeError("historical 6.14 composite unexpectedly changes the school denominator")

    review: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "SOURCE_BOUND_COMPOSITE_FRONTIER_ONLY_COMPONENT_DERIVATION_REQUIRED",
        "official_source": {
            "source_system": OFFICIAL_SOURCE_SYSTEM,
            "cycle": 2026,
            "code": OFFICIAL_CODE,
            "label": OFFICIAL_LABEL,
            "explicit_subbranches": [],
            "fabricated_subcodes": 0,
        },
        "historical_overlay": {
            "file": OVERLAY.name,
            "classification": row.get("classification"),
            "topic": row.get("topic"),
            "placeholder_owner": EXPECTED_PLACEHOLDER,
            "placeholder_is_canonical_identity": False,
            "note": row.get("note"),
            "school_reopen_candidates": 0,
            "unowned_official_school_orthography_topics": 0,
            "school_count_effect": 0,
        },
        "composite_frontier": {
            "operation": "rule identification/application over existing active orthography identities",
            "new_canonical_identity_required": False,
            "exact_component_refs_accepted_now": [],
            "exact_component_acceptance_count": 0,
            "applicable_component_refs": [],
            "applicable_component_count": 0,
            "component_set_status": "UNRESOLVED_DETERMINISTIC_DERIVATION_REQUIRED",
            "policy": (
                "The overlay phrase 'all applicable active orthography identities' is a composite placeholder, "
                "not a canonical owner. The exact 6.14 component set must be derived deterministically from "
                "current accepted exact orthography authorities. Route membership, a manually broad list, "
                "keyword similarity, or every school-* identity is insufficient for exact component mastery."
            ),
        },
        "safety": {
            "semantic_admissions": 0,
            "object_closures": 0,
            "new_school_identities": 0,
            "school_reopen": 0,
            "false_exact_mastery_admissions": 0,
            "learner_audio_persistence": 0,
            "accepted_demo_or_scorer_change": False,
            "production_peis_write": False,
            "provider_execution": False,
            "public_traffic": False,
        },
        "next_gate": (
            "Derive the exact applicable 6.14 component set deterministically from current accepted orthography "
            "authorities, with no placeholder or manufactured owner admission; then run reuse-first independent "
            "learner-evidence audit before any separate object acceptance."
        ),
    }
    review["normalized_sha256"] = _normalized_sha(review)
    return review


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()

    review = build_review()
    if args.output:
        Path(args.output).write_text(
            json.dumps(review, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(review, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_OGE_6_14_SOURCE_BOUND_COMPOSITE_FRONTIER=PASS")
        print(f"official_code={review['official_source']['code']}")
        print(f"placeholder_is_canonical_identity={review['historical_overlay']['placeholder_is_canonical_identity']}")
        print(f"exact_component_acceptance_count={review['composite_frontier']['exact_component_acceptance_count']}")
        print(f"component_set_status={review['composite_frontier']['component_set_status']}")
        print(f"normalized_sha256={review['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
