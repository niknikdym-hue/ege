#!/usr/bin/env python3
"""Build the audited 80-card Russian Exceptions Practice Bank.

Historical wave files remain immutable checkpoints. Current card selection is
controlled by manifest 119. Audited fixes are applied from overlay 131 and a
separate post-audit learner-feedback polish is applied from overlay 136.
The builder fails closed if an audited FIX target disappears, a FAIL/REPLACE item
remains active, or any quality-polish target is missing.

Data-only: does not publish or modify Tilda/current EGE trainer files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import build_russian_exceptions_practice as base
import build_russian_exceptions_practice_current_corrected_v2 as current

CURRENT_EXCEPTION_MANIFEST = "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json"
CURRENT_PRACTICE_MANIFEST = "119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json"
COURSE_GRADE_OVERLAY = "131-RUSSIAN-EXCEPTIONS-COURSE-GRADE-CORRECTIONS-v0.1.json"
LEARNER_FEEDBACK_POLISH = "136-RUSSIAN-EXCEPTIONS-LEARNER-FEEDBACK-POLISH-v0.1.json"

FEEDBACK_ACTIONS = {"replace_feedback", "replace_feedback_and_provenance"}
VALID_ACTIONS = FEEDBACK_ACTIONS | {"provenance_fix", "disable_and_replace"}


def _clone(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _load_patch_list(root: Path, rel: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    overlay = base.load_json(root / rel)
    if not isinstance(overlay, dict):
        raise base.BuildError(f"{rel} must be an object")
    patches = overlay.get("item_patches")
    if not isinstance(patches, list) or not all(isinstance(x, dict) for x in patches):
        raise base.BuildError(f"{rel}: item_patches must be object array")
    patch_summary = overlay.get("patch_summary", {})
    expected_patches = patch_summary.get("patch_entries") if isinstance(patch_summary, dict) else None
    if not isinstance(expected_patches, int) or expected_patches != len(patches):
        raise base.BuildError(
            f"{rel}: patch count mismatch: summary={expected_patches!r}, actual={len(patches)}"
        )
    return overlay, patches


def load_course_grade_practice_items(
    root: Path, manifest: Any
) -> tuple[list[dict[str, Any]], list[str], int]:
    items, source_files, expected_active = current.load_active_practice_items(root, manifest)

    by_id: dict[str, dict[str, Any]] = {}
    for item in items:
        pid = item.get("practice_item_id")
        if not isinstance(pid, str) or not pid:
            raise base.BuildError("active practice item missing practice_item_id")
        if pid in by_id:
            raise base.BuildError(f"duplicate active practice_item_id before overlay: {pid}")
        by_id[pid] = item

    # 1) Audited 80/80 correction overlay.
    overlay, patches = _load_patch_list(root, COURSE_GRADE_OVERLAY)
    patch_summary = overlay.get("patch_summary", {})
    seen_patch_ids: set[str] = set()
    feedback_applied = 0
    provenance_reviewed = 0
    replacement_validated = 0

    for patch in patches:
        pid = patch.get("practice_item_id")
        action = patch.get("action")
        if not isinstance(pid, str) or not pid:
            raise base.BuildError(f"{COURSE_GRADE_OVERLAY}: patch missing practice_item_id")
        if pid in seen_patch_ids:
            raise base.BuildError(f"{COURSE_GRADE_OVERLAY}: duplicate patch for {pid}")
        seen_patch_ids.add(pid)
        if action not in VALID_ACTIONS:
            raise base.BuildError(f"{COURSE_GRADE_OVERLAY}: unsupported action {action!r} for {pid}")

        if action in FEEDBACK_ACTIONS:
            item = by_id.get(pid)
            if item is None:
                raise base.BuildError(f"audited feedback target is not active: {pid}")
            why = patch.get("feedback_why")
            if not isinstance(why, str) or not why.strip():
                raise base.BuildError(f"{pid}: {action} requires non-empty feedback_why")
            feedback = item.get("feedback")
            if not isinstance(feedback, dict):
                raise base.BuildError(f"{pid}: active item has no feedback object")
            feedback["why"] = why.strip()
            item["content_audit_overlay"] = COURSE_GRADE_OVERLAY
            feedback_applied += 1
            if action == "replace_feedback_and_provenance":
                provenance_reviewed += 1
            continue

        if action == "provenance_fix":
            if pid not in by_id:
                raise base.BuildError(f"audited provenance target is not active: {pid}")
            # Practice payload has no source_refs. Provenance is corrected in the
            # linked Exceptions source bank; here we only assert that the audited
            # learner card is still active and traceable.
            by_id[pid]["content_audit_overlay"] = COURSE_GRADE_OVERLAY
            provenance_reviewed += 1
            continue

        replacement = patch.get("replacement")
        if not isinstance(replacement, dict):
            raise base.BuildError(f"{pid}: disable_and_replace requires replacement object")
        replacement_id = replacement.get("practice_item_id")
        if not isinstance(replacement_id, str) or not replacement_id:
            raise base.BuildError(f"{pid}: replacement missing practice_item_id")
        if pid in by_id:
            raise base.BuildError(f"FAIL/REPLACE item is still active: {pid}")
        active_replacement = by_id.get(replacement_id)
        if active_replacement is None:
            raise base.BuildError(f"replacement is not active: {pid} -> {replacement_id}")
        replacement_exception = replacement.get("exception_id")
        if replacement_exception != active_replacement.get("exception_id"):
            raise base.BuildError(
                f"replacement exception mismatch for {replacement_id}: overlay={replacement_exception!r}, active={active_replacement.get('exception_id')!r}"
            )
        active_replacement["content_audit_overlay"] = COURSE_GRADE_OVERLAY
        replacement_validated += 1

    expected_fix = patch_summary.get("audit_fix_items") if isinstance(patch_summary, dict) else None
    expected_replace = patch_summary.get("audit_fail_replace_items") if isinstance(patch_summary, dict) else None
    if not isinstance(expected_fix, int) or expected_fix != len(patches) - replacement_validated:
        raise base.BuildError(
            f"overlay FIX count mismatch: summary={expected_fix!r}, validated={len(patches)-replacement_validated}"
        )
    if not isinstance(expected_replace, int) or expected_replace != replacement_validated:
        raise base.BuildError(
            f"overlay replacement count mismatch: summary={expected_replace!r}, validated={replacement_validated}"
        )

    # 2) Human-review polish: safe cards whose feedback was still too terse for
    # course-grade teaching. This does not change answers, prompts or card count.
    polish, polish_patches = _load_patch_list(root, LEARNER_FEEDBACK_POLISH)
    polish_summary = polish.get("patch_summary", {})
    expected_polish = polish_summary.get("quality_polish_items") if isinstance(polish_summary, dict) else None
    if not isinstance(expected_polish, int) or expected_polish != len(polish_patches):
        raise base.BuildError(
            f"{LEARNER_FEEDBACK_POLISH}: quality count mismatch: summary={expected_polish!r}, actual={len(polish_patches)}"
        )
    polish_seen: set[str] = set()
    for patch in polish_patches:
        pid = patch.get("practice_item_id")
        action = patch.get("action")
        if not isinstance(pid, str) or not pid:
            raise base.BuildError(f"{LEARNER_FEEDBACK_POLISH}: patch missing practice_item_id")
        if pid in polish_seen:
            raise base.BuildError(f"{LEARNER_FEEDBACK_POLISH}: duplicate patch for {pid}")
        polish_seen.add(pid)
        if action != "replace_feedback":
            raise base.BuildError(f"{LEARNER_FEEDBACK_POLISH}: only replace_feedback is allowed, got {action!r} for {pid}")
        item = by_id.get(pid)
        if item is None:
            raise base.BuildError(f"quality-polish feedback target is not active: {pid}")
        why = patch.get("feedback_why")
        if not isinstance(why, str) or not why.strip():
            raise base.BuildError(f"{pid}: quality polish requires non-empty feedback_why")
        feedback = item.get("feedback")
        if not isinstance(feedback, dict):
            raise base.BuildError(f"{pid}: active item has no feedback object")
        feedback["why"] = why.strip()
        item["learner_feedback_polish"] = LEARNER_FEEDBACK_POLISH

    if len(items) != expected_active:
        raise base.BuildError(f"overlays changed active item count: expected={expected_active}, actual={len(items)}")

    source_files = list(source_files) + [COURSE_GRADE_OVERLAY, LEARNER_FEEDBACK_POLISH]
    return [_clone(x) for x in items], source_files, expected_active


def main() -> int:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=root_default)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--audit", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output or root / "build" / "RUSSIAN-EXCEPTIONS-PRACTICE-CANONICAL.json"
    audit = args.audit or root / "audits" / "RUSSIAN-EXCEPTIONS-PRACTICE-VALIDATION.txt"

    base.EXCEPTIONS_MANIFEST = CURRENT_EXCEPTION_MANIFEST
    base.PRACTICE_MANIFEST = CURRENT_PRACTICE_MANIFEST
    base.flatten_exceptions = current.active_exceptions
    base.load_practice_items = load_course_grade_practice_items

    try:
        return base.build(root, output, audit)
    except base.BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
