#!/usr/bin/env python3
"""Fail-closed source-bound frontier for FIPI OGE 2026 codifier position 6.13.

This is a candidate review only.  It deliberately does not admit semantic owners,
materialize learner evidence, mutate the school denominator, or close the object.
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
OFFICIAL_CODE = "6.13"
OFFICIAL_LABEL = "Правописание сложных и сложносокращённых слов"

# Candidate frontier already named by the reviewed FIPI 2026 OGE route overlay.
# These are candidates, not accepted exact owners.
EXPECTED_OVERLAY_CANDIDATES = (
    "school-compound-linking-vowel",
    "school-compound-first-part-without-linking-vowel-system",
    "school-compound-noun-solid-hyphen-system",
    "school-compound-adjective-solid-hyphen-separate-system",
    "school-abbreviations-capitalization-formation",
)

# Nearby spelling systems are explicitly outside this source-bound frontier unless
# a later exact-owner review proves an authority-grade 6.13 equivalence.
EXPLICIT_ADJACENT_EXCLUSIONS = (
    "school-pol-polu-writing-boundary",
    "school-adverb-solid-hyphen-separate-system",
    "school-preposition-solid-hyphen-separate-base",
    "school-conjunction-solid-separate-spelling-base",
    "school-nonnegative-particle-separate-hyphen-spelling-base",
    "school-numeral-orthography-base",
)


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
    candidates = tuple(row.get("owners") or ())
    if candidates != EXPECTED_OVERLAY_CANDIDATES:
        raise RuntimeError(
            "historical 6.13 overlay candidate frontier drifted: "
            f"expected={EXPECTED_OVERLAY_CANDIDATES!r} actual={candidates!r}"
        )
    if len(set(candidates)) != len(candidates):
        raise RuntimeError("duplicate 6.13 overlay candidate")
    if not all(candidate.startswith("school-") for candidate in candidates):
        raise RuntimeError("6.13 overlay candidate is not a school canonical identity reference")
    if set(candidates) & set(EXPLICIT_ADJACENT_EXCLUSIONS):
        raise RuntimeError("6.13 source frontier overlaps explicit adjacent exclusions")

    second_pass = overlay.get("second_pass_result") or {}
    if second_pass.get("school_reopen_candidates") != 0:
        raise RuntimeError("historical FIPI backstop no longer proves zero school reopen candidates")
    if second_pass.get("unowned_official_school_orthography_topics") != 0:
        raise RuntimeError("historical FIPI backstop no longer proves zero unowned official orthography topics")

    review: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "SOURCE_BOUND_FRONTIER_ONLY_EXACT_OWNER_REVIEW_REQUIRED",
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
            "candidate_count": len(candidates),
            "candidate_refs": list(candidates),
            "school_reopen_candidates": 0,
            "unowned_official_school_orthography_topics": 0,
        },
        "frontier": {
            "candidate_refs": list(candidates),
            "candidate_count": len(candidates),
            "exact_owner_refs_accepted_now": [],
            "exact_owner_acceptance_count": 0,
            "unresolved_candidate_count": len(candidates),
            "explicit_adjacent_exclusions": list(EXPLICIT_ADJACENT_EXCLUSIONS),
            "policy": (
                "Historical overlay membership is candidate evidence only. Exact owner admission requires "
                "a separate source/semantic proof against the whole OGE_COD 6.13 boundary; shared module, "
                "keyword similarity, nearby codifier position, or solid/hyphen/separate spelling alone is insufficient."
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
            "Resolve the five source-bound candidates one by one against exact OGE_COD 6.13 scope; "
            "only a separately proven exact-owner set may proceed to current-route supersession and "
            "component-specific learner-evidence audit."
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
        print("RUSSIAN_OGE_6_13_SOURCE_BOUND_FRONTIER=PASS")
        print(f"official_code={review['official_source']['code']}")
        print(f"candidate_count={review['frontier']['candidate_count']}")
        print(f"exact_owner_acceptance_count={review['frontier']['exact_owner_acceptance_count']}")
        print(f"unresolved_candidate_count={review['frontier']['unresolved_candidate_count']}")
        print(f"normalized_sha256={review['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
