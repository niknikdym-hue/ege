#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent.parent
OGE_OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
IDENTITY_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
EXACT_AUTHORITY = HERE / "RUSSIAN-OGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

TARGET_CODE = "6.4"
TARGET_TOPIC = "Ъ and Ь including separating signs"
UNRESOLVED_OWNER = "other active lexical/form soft-sign owners where applicable"
EXPECTED_EXPLICIT_REFS = [
    "school-separating-hard-soft-sign-boundary",
    "school-verb-soft-sign-forms",
]
REVIEW_ONLY_CANDIDATES = [
    {
        "canonical_ref": "school-adverb-final-soft-sign-after-sibilant-base",
        "review_reason": "Active canonical school identity has final-soft-sign scope; OGE 6.4 ownership is not proven by the current overlay placeholder.",
        "provenance": "253-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-C-O26-O35-v0.1.json",
    },
    {
        "canonical_ref": "school-adjective-soft-sign-before-sk-base",
        "review_reason": "Active canonical school identity has a soft-sign spelling boundary; exact OGE 6.4 ownership versus adjacent orthography codes requires source-bound adjudication.",
        "provenance": "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25-v0.1.json",
    },
    {
        "canonical_ref": "school-noun-agent-suffix-chik-shchik-soft-sign",
        "review_reason": "Active canonical school identity contains a soft-sign boundary but also belongs to suffix spelling; OGE 6.4 versus 6.6 ownership cannot be inferred from words alone.",
        "provenance": "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25-v0.1.json",
    },
    {
        "canonical_ref": "school-numeral-orthography-base",
        "review_reason": "Active canonical school identity includes numeral orthography with soft-sign behavior, but it is a broader spelling identity and exact OGE 6.4 ownership is not established.",
        "provenance": "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25-v0.1.json",
    },
]


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def build_review() -> dict[str, Any]:
    overlay = load_json(OGE_OVERLAY)
    inventory = load_json(IDENTITY_INVENTORY)
    exact = load_json(EXACT_AUTHORITY)

    rows = [
        row
        for row in overlay.get("orthography_codifier_overlay") or []
        if isinstance(row, dict) and str(row.get("position")) == TARGET_CODE
    ]
    if len(rows) != 1:
        raise ValueError("OGE 6.4 overlay row must exist exactly once")
    row = rows[0]
    if row.get("topic") != TARGET_TOPIC:
        raise ValueError("OGE 6.4 topic drift")
    if row.get("classification") != "SCHOOL_IDENTITY_ROUTE":
        raise ValueError("OGE 6.4 classification drift")

    owners = [str(value) for value in row.get("owners") or []]
    if owners != EXPECTED_EXPLICIT_REFS + [UNRESOLVED_OWNER]:
        raise ValueError("OGE 6.4 owner frontier changed; re-adjudication required")
    if UNRESOLVED_OWNER not in owners:
        raise ValueError("OGE 6.4 unresolved owner placeholder unexpectedly disappeared")

    decisions = [item for item in exact.get("decisions") or [] if isinstance(item, dict)]
    accepted_6_4 = [item for item in decisions if str(item.get("content_code")) == TARGET_CODE]
    if accepted_6_4:
        raise ValueError("OGE 6.4 cannot be exact-accepted while its overlay retains an unresolved owner placeholder")

    objects = [item for item in inventory.get("objects") or [] if isinstance(item, dict)]
    inventory_rows = [item for item in objects if item.get("source_id") == "oge-2026-orthography-6-4"]
    if len(inventory_rows) != 1:
        raise ValueError("OGE 6.4 identity-inventory source row must exist exactly once")
    inventory_row = inventory_rows[0]
    if inventory_row.get("review_status") != "reviewed":
        raise ValueError("OGE 6.4 inventory source row is not reviewed")
    if inventory_row.get("audit_classification") != "EXAM_ROUTE_ONLY":
        raise ValueError("OGE 6.4 inventory classification drift")
    inventory_refs = sorted(str(ref) for ref in inventory_row.get("current_semantic_refs") or [])
    if inventory_refs != sorted(EXPECTED_EXPLICIT_REFS):
        raise ValueError("OGE 6.4 identity-inventory refs drifted from the explicit overlay refs")

    known_refs: set[str] = set()
    for item in objects:
        source_id = str(item.get("source_id") or "")
        if source_id.startswith("school-"):
            known_refs.add(source_id)
        known_refs.update(str(ref) for ref in item.get("current_semantic_refs") or [] if str(ref).startswith("school-"))

    missing = [
        item["canonical_ref"]
        for item in REVIEW_ONLY_CANDIDATES
        if item["canonical_ref"] not in known_refs
    ]
    if missing:
        raise ValueError("review-only canonical refs missing from current inventory: " + ",".join(missing))

    candidate_rows = []
    for item in REVIEW_ONLY_CANDIDATES:
        candidate_rows.append(
            {
                **item,
                "review_disposition": "REVIEW_ONLY_NOT_OGE_6_4_OWNER_ADMITTED",
                "exact_oge_6_4_owner_proven": False,
                "admission_effect": "NONE",
            }
        )

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_REVIEW_REQUIRED",
        "authority_issue": 161,
        "scope": "OGE_2026_ORTHOGRAPHY_CODE_6_4_SOFT_SIGN_OWNER_RESOLUTION",
        "target": {
            "document_id": "OGE_COD",
            "content_code": TARGET_CODE,
            "topic": TARGET_TOPIC,
            "classification": str(row["classification"]),
        },
        "current_overlay_truth": {
            "explicit_canonical_refs": EXPECTED_EXPLICIT_REFS,
            "unresolved_owner_placeholder": UNRESOLVED_OWNER,
            "unresolved_placeholder_present": True,
            "overlay_is_complete_exact_owner_list": False,
        },
        "identity_inventory_truth": {
            "source_id": str(inventory_row["source_id"]),
            "review_status": str(inventory_row["review_status"]),
            "audit_classification": str(inventory_row["audit_classification"]),
            "current_semantic_refs": inventory_refs,
            "inventory_refs_prove_overlay_completeness": False,
        },
        "exact_acceptance_truth": {
            "current_exact_acceptance_for_6_4": False,
            "accepted_oge_orthography_codes": sorted(str(item.get("content_code")) for item in decisions),
            "exact_acceptance_requires_complete_placeholder_free_owner_list": True,
        },
        "review_only_overlap_candidates": candidate_rows,
        "summary": {
            "explicit_overlay_canonical_refs": len(EXPECTED_EXPLICIT_REFS),
            "unresolved_owner_placeholders": 1,
            "review_only_overlap_candidates": len(candidate_rows),
            "semantic_admissions": 0,
            "object_level_closures": 0,
            "false_exact_mastery_admissions": 0,
        },
        "policy": {
            "reuse_first": True,
            "review_only_candidate_is_exact_owner": False,
            "keyword_or_name_overlap_is_exact_binding": False,
            "inventory_route_refs_are_complete_owner_proof": False,
            "placeholder_may_be_silently_dropped": False,
            "exact_acceptance_allowed_while_placeholder_remains": False,
            "semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
        },
        "admission_effect": "NONE",
        "next_safe_step": "Adjudicate the unresolved OGE 6.4 owner placeholder owner-by-owner against exact official-source scope and canonical school identities; replace the placeholder only when the owner list is demonstrably complete, then run exact component acceptance separately.",
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_review()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("OGE_6_4_SOFT_SIGN_OWNER_RESOLUTION_REVIEW=PASS")
        for key, value in result["summary"].items():
            print(f"{key}={value}")
        print(f"normalized_sha256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
