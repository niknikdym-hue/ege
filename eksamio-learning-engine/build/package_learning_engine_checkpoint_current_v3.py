#!/usr/bin/env python3
"""Create checkpoint ZIP gated by current v3 aggregate validation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import package_learning_engine_checkpoint as base

CURRENT_SUMMARY = Path("audits/RUSSIAN-LEARNING-ENGINE-VALIDATION-CURRENT-V3-SUMMARY.txt")


def main() -> int:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=root_default)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    output_dir = (args.output_dir or root / base.CHECKPOINT_DIR_REL).resolve()
    base.SUMMARY_REL = CURRENT_SUMMARY

    try:
        zip_path, inventory_path = base.build_archive(root, output_dir, args.require_pass)
    except Exception as exc:
        print(f"PACKAGE ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"ZIP: {zip_path}")
    print(f"SHA256 INVENTORY: {inventory_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
