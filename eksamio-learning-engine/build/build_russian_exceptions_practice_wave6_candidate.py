#!/usr/bin/env python3
"""Build the reviewed 121-card Wave 6 candidate without changing current manifest 119.

Reuses the current audited course-grade loader, so the reviewed 93-card checkpoint
keeps all overlays and Wave 5 content, then adds the 28-card Wave 6 draft through
candidate manifest 143. Manual review overlay 145 converts exactly those 28 draft
items to schema-valid REVIEWED status and applies two explicit editorial fixes.
Output stays under build/candidate-wave6. Current 93 and Tilda are not mutated.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import build_russian_exceptions_practice as base
import build_russian_exceptions_practice_current_corrected_v2 as current
import build_russian_exceptions_practice_course_grade as course_grade

CURRENT_EXCEPTION_MANIFEST = "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json"
CANDIDATE_PRACTICE_MANIFEST = "143-RUSSIAN-EXCEPTIONS-PRACTICE-WAVE6-CANDIDATE-MANIFEST.json"
WAVE6_DRAFT = "142-RUSSIAN-EXCEPTIONS-PRACTICE-WAVE6-SOLID-SEPARATE-DRAFT-v0.1.json"
WAVE6_REVIEW_OVERLAY = "145-RUSSIAN-EXCEPTIONS-WAVE6-REVIEWED-OVERLAY-v0.1.json"


def _clone(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def load_reviewed_wave6_practice_items(
    root: Path, manifest: Any
) -> tuple[list[dict[str, Any]], list[str], int]:
    items, source_files, expected_active = course_grade.load_course_grade_practice_items(root, manifest)
    overlay = base.load_json(root / WAVE6_REVIEW_OVERLAY)
    if not isinstance(overlay, dict):
        raise base.BuildError(f"{WAVE6_REVIEW_OVERLAY} must be an object")

    reviewed_ids_raw = overlay.get("reviewed_practice_item_ids")
    if not isinstance(reviewed_ids_raw, list) or not reviewed_ids_raw or not all(isinstance(x, str) and x for x in reviewed_ids_raw):
        raise base.BuildError(f"{WAVE6_REVIEW_OVERLAY}: reviewed_practice_item_ids must be non-empty string array")
    if len(reviewed_ids_raw) != len(set(reviewed_ids_raw)):
        raise base.BuildError(f"{WAVE6_REVIEW_OVERLAY}: duplicate reviewed practice ID")
    reviewed_ids = set(reviewed_ids_raw)

    summary = overlay.get("review_summary")
    if not isinstance(summary, dict) or summary.get("reviewed_cards") != len(reviewed_ids):
        raise base.BuildError(f"{WAVE6_REVIEW_OVERLAY}: reviewed count mismatch")
    if len(reviewed_ids) != 28:
        raise base.BuildError(f"Wave 6 review must contain exactly 28 cards, got {len(reviewed_ids)}")

    reviewed_status = overlay.get("reviewed_status")
    if reviewed_status != "reviewed":
        raise base.BuildError(f"{WAVE6_REVIEW_OVERLAY}: reviewed_status must be 'reviewed'")

    by_id: dict[str, dict[str, Any]] = {}
    wave6_active_ids: set[str] = set()
    for item in items:
        pid = item.get("practice_item_id")
        if not isinstance(pid, str) or not pid:
            raise base.BuildError("active practice item missing practice_item_id")
        if pid in by_id:
            raise base.BuildError(f"duplicate active practice_item_id: {pid}")
        by_id[pid] = item
        if item.get("source_practice_bank") == WAVE6_DRAFT:
            wave6_active_ids.add(pid)

    if wave6_active_ids != reviewed_ids:
        missing_review = sorted(wave6_active_ids - reviewed_ids)
        missing_active = sorted(reviewed_ids - wave6_active_ids)
        raise base.BuildError(
            f"Wave 6 review/active mismatch: unreviewed_active={missing_review}, reviewed_not_active={missing_active}"
        )

    # Manual review changes only the 28 Wave 6 draft items. Current 93 remain byte-for-byte
    # equivalent at this loader stage except for ordinary clone serialization.
    for pid in reviewed_ids_raw:
        item = by_id[pid]
        if item.get("status") != "source_verified_draft":
            raise base.BuildError(
                f"{pid}: expected historical Wave 6 draft status 'source_verified_draft', got {item.get('status')!r}"
            )
        item["status"] = "reviewed"
        item["manual_review_overlay"] = WAVE6_REVIEW_OVERLAY

    patches = overlay.get("item_patches")
    if not isinstance(patches, list) or not all(isinstance(x, dict) for x in patches):
        raise base.BuildError(f"{WAVE6_REVIEW_OVERLAY}: item_patches must be object array")
    if summary.get("editorial_fixes") != len(patches):
        raise base.BuildError(f"{WAVE6_REVIEW_OVERLAY}: editorial fix count mismatch")
    if len(patches) != 2:
        raise base.BuildError(f"Wave 6 review overlay must contain exactly two editorial fixes, got {len(patches)}")

    patched_ids: set[str] = set()
    for patch in patches:
        pid = patch.get("practice_item_id")
        if not isinstance(pid, str) or pid not in reviewed_ids:
            raise base.BuildError(f"Wave 6 editorial patch targets non-reviewed item: {pid!r}")
        if pid in patched_ids:
            raise base.BuildError(f"duplicate Wave 6 editorial patch: {pid}")
        patched_ids.add(pid)
        item = by_id[pid]
        for field in ("prompt", "answer", "feedback", "context_signature"):
            if field not in patch:
                raise base.BuildError(f"{pid}: editorial patch missing {field}")
            item[field] = _clone(patch[field])

    expected_fix_ids = {
        "ex-practice-za-to-separate-w6-012",
        "ex-practice-v-rode-separate-w6-022",
    }
    if patched_ids != expected_fix_ids:
        raise base.BuildError(f"Wave 6 editorial patch IDs mismatch: {sorted(patched_ids)}")

    if len(items) != expected_active:
        raise base.BuildError(f"Wave 6 review overlay changed active count: expected={expected_active}, actual={len(items)}")

    source_files = list(source_files) + [WAVE6_REVIEW_OVERLAY]
    return [_clone(x) for x in items], source_files, expected_active


def main() -> int:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=root_default)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--audit", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output or root / "build" / "candidate-wave6" / "RUSSIAN-EXCEPTIONS-PRACTICE-WAVE6-CANDIDATE.json"
    audit = args.audit or root / "audits" / "candidate-wave6" / "RUSSIAN-EXCEPTIONS-PRACTICE-WAVE6-VALIDATION.txt"

    base.EXCEPTIONS_MANIFEST = CURRENT_EXCEPTION_MANIFEST
    base.PRACTICE_MANIFEST = CANDIDATE_PRACTICE_MANIFEST
    base.flatten_exceptions = current.active_exceptions
    base.load_practice_items = load_reviewed_wave6_practice_items

    try:
        return base.build(root, output, audit)
    except base.BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
