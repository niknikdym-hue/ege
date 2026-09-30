#!/usr/bin/env python3
"""Audit dedicated thematic-bank filenames in exact remote Russian closure bytes.

Bounded claim only: this scans the exact #164 full-trainer directory for files
whose basename ends with ``-TRAINER-BANK.json``.  It does not claim that live
Tilda backing data or canonical sources elsewhere do not exist.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

SOURCE_COMMIT = "7edddb9f9764b5e8cdf7e2653c425e5f90c4ffe9"
SOURCE_DIR = "eksamio-learning-engine/russkiy-knigi/ege-russkiy-trenazher"
ORTHO_PATH = f"{SOURCE_DIR}/ORTHOEPIC-TRAINER-BANK.json"
ORTHO_BLOB = "3595d4e36cc2d78596ff05451ce42faadb3b1aed"
ARTIFACT_PATH = Path(__file__).with_name("THEMATIC-TRAINER-REMOTE-SOURCE-INVENTORY-v0.1.json")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_show(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{path}"])


def git_blob_sha(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def main() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    require(artifact["source_commit"] == SOURCE_COMMIT, "source commit drift")
    require(artifact["search_scope"]["directory"] == SOURCE_DIR, "bounded search directory drift")

    names_raw = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", SOURCE_COMMIT, "--", SOURCE_DIR],
        text=True,
    )
    dedicated = sorted(
        line.strip()
        for line in names_raw.splitlines()
        if line.strip().rsplit("/", 1)[-1].endswith("-TRAINER-BANK.json")
    )
    require(dedicated == [ORTHO_PATH], f"dedicated thematic-bank filename set drift: {dedicated!r}")

    ortho_raw = git_show(ORTHO_PATH)
    require(len(ortho_raw) == 7734, "exact orthoepy bank byte count drift")
    require(git_blob_sha(ortho_raw) == ORTHO_BLOB, "exact orthoepy bank blob drift")
    ortho = json.loads(ortho_raw.decode("utf-8"))
    ids = [str(row["id"]) for row in ortho["entries"]]
    require(ortho["cardCount"] == 36, "declared orthoepy cardCount drift")
    require(len(ids) == 96 and len(set(ids)) == 96, "orthoepy exact unique-entry denominator drift")

    observed = artifact["observed_dedicated_bank_files"]
    require(len(observed) == 1 and observed[0]["path"] == ORTHO_PATH, "artifact dedicated-bank list drift")
    require(observed[0]["git_blob_sha1"] == ORTHO_BLOB, "artifact orthoepy blob drift")
    require(observed[0]["byte_count"] == len(ortho_raw), "artifact orthoepy byte count drift")
    require(observed[0]["declared_card_count"] == 36, "artifact declared card count drift")
    require(observed[0]["actual_unique_entry_ids"] == 96, "artifact unique entry count drift")
    require(observed[0]["live_bank_identity_proven"] is False, "live identity must remain unproven")

    negatives = {row["trainer"]: row["dedicated_bank_filename_in_scope"] for row in artifact["bounded_negative_findings"]}
    require(
        negatives == {"dictionary_words": False, "paronyms": False, "phraseology": False},
        "bounded negative findings drift",
    )

    effect = artifact["reconciliation_effect"]
    require(effect["semantic_admissions"] == 0, "must not admit semantics")
    require(effect["object_closures"] == 0, "must not close objects")
    require(effect["mastery_admissions"] == 0, "must not admit mastery")
    require(effect["false_exact_mastery"] == 0, "false exact mastery must remain zero")
    require(all(str(effect[name]).startswith("UNKNOWN_BLOCKER") for name in ("orthoepy", "dictionary_words", "paronyms", "phraseology")), "all thematic trainers must remain fail-closed")

    print("THEMATIC_TRAINER_REMOTE_SOURCE_INVENTORY=PASS")
    print(f"source_commit={SOURCE_COMMIT}")
    print(f"bounded_directory={SOURCE_DIR}")
    print("dedicated_bank_files=1")
    print(f"orthoepy_blob={ORTHO_BLOB}")
    print("orthoepy_declared_cardCount=36")
    print("orthoepy_actual_unique_entries=96")
    print("dictionary_words_dedicated_bank_in_scope=NOT_FOUND")
    print("paronyms_dedicated_bank_in_scope=NOT_FOUND")
    print("phraseology_dedicated_bank_in_scope=NOT_FOUND")
    print("live_item_identity_binding=BLOCKED_NOT_PROVEN")
    print("false_exact_mastery=0")


if __name__ == "__main__":
    main()
