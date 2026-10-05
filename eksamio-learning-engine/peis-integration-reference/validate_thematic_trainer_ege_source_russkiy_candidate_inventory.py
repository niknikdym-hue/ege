#!/usr/bin/env python3
"""Audit named thematic source candidates in exact #164 ege-source-russkiy tree.

This is deliberately a filename/tree inventory. It does not parse the PDFs and
must not be used as proof that any candidate is the live trainer backing bank,
that its rows equal live item identities, or that it can create mastery.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

SOURCE_COMMIT = "7edddb9f9764b5e8cdf7e2653c425e5f90c4ffe9"
SOURCE_ROOT = "ege-source-russkiy"
SOURCE_TREE = "6af9dc79d6e9e4d86a035ea8484a450b8ea60e6f"
ARTIFACT_PATH = Path(__file__).with_name(
    "THEMATIC-TRAINER-EGE-SOURCE-RUSSKIY-CANDIDATE-INVENTORY-v0.1.json"
)

EXPECTED = {
    "orthoepy": [
        (2022, "ege-source-russkiy/source-russkiy-2022/Orthoepic dictionary-2022.pdf", "1b1199df871d868c1da36775d5efff32d41770b0", 202134),
        (2023, "ege-source-russkiy/source-russkiy-2023/Orthoepic dictionary-2023.pdf", "5155d5146c9a90e605a95c82b158f58722350b36", 165923),
        (2024, "ege-source-russkiy/source-russkiy-2024/Orthoepic dictionary-2024.pdf", "fdb28f6d9018768e051477acc11568bd10e6e941", 166401),
    ],
    "paronyms": [
        (2022, "ege-source-russkiy/source-russkiy-2022/Dictionary of paronyms-2022.pdf", "73aab7cae9417f1fc95dd6886a704f4dca95d22e", 102082),
        (2023, "ege-source-russkiy/source-russkiy-2023/Dictionary of paronyms-2023.pdf", "902f41e6f7e0e038b47121a43437cd9d3426f9a8", 83833),
        (2024, "ege-source-russkiy/source-russkiy-2024/Dictionary of paronyms-2024.pdf", "3804f784d8376ff1b7e174b916625104a7a2ade3", 83916),
    ],
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ls_tree_rows() -> list[tuple[str, str, int]]:
    raw = subprocess.check_output(
        ["git", "ls-tree", "-r", "-l", SOURCE_COMMIT, "--", SOURCE_ROOT],
        text=True,
    )
    rows: list[tuple[str, str, int]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        meta, path = line.split("\t", 1)
        _mode, obj_type, sha, size = meta.split()
        if obj_type != "blob":
            continue
        rows.append((path, sha, int(size)))
    return rows


def main() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    require(artifact["source_commit"] == SOURCE_COMMIT, "source commit drift")
    require(artifact["source_root"]["path"] == SOURCE_ROOT, "source root drift")
    require(artifact["source_root"]["git_tree_sha1"] == SOURCE_TREE, "artifact tree sha drift")

    actual_tree = subprocess.check_output(
        ["git", "rev-parse", f"{SOURCE_COMMIT}:{SOURCE_ROOT}"], text=True
    ).strip()
    require(actual_tree == SOURCE_TREE, f"exact source tree drift: {actual_tree}")

    rows = ls_tree_rows()
    row_map = {path: (sha, size) for path, sha, size in rows}

    observed = artifact["observed_source_candidates"]
    for family, expected_rows in EXPECTED.items():
        expected_paths = [path for _year, path, _sha, _size in expected_rows]
        if family == "orthoepy":
            discovered = sorted(path for path in row_map if path.rsplit("/", 1)[-1].startswith("Orthoepic dictionary-"))
        else:
            discovered = sorted(path for path in row_map if path.rsplit("/", 1)[-1].startswith("Dictionary of paronyms-"))
        require(discovered == expected_paths, f"{family} named source candidate set drift: {discovered!r}")

        artifact_rows = observed[family]
        require(len(artifact_rows) == len(expected_rows), f"{family} artifact count drift")
        for artifact_row, (year, path, sha, size) in zip(artifact_rows, expected_rows, strict=True):
            require(artifact_row == {"year": year, "path": path, "git_blob_sha1": sha, "byte_count": size}, f"{family} artifact row drift for {path}")
            require(row_map.get(path) == (sha, size), f"{family} exact git blob/size drift for {path}")

    lower_paths = [path.lower() for path in row_map]
    findings = artifact["bounded_filename_findings"]
    require(sum("orthoepic dictionary-2025" in path or "orthoepic dictionary-2026" in path for path in lower_paths) == findings["orthoepy_2025_2026_named_dictionary_candidates_in_scope"] == 0, "2025/2026 orthoepy filename finding drift")
    require(sum("dictionary of paronyms-2025" in path or "dictionary of paronyms-2026" in path for path in lower_paths) == findings["paronyms_2025_2026_named_dictionary_candidates_in_scope"] == 0, "2025/2026 paronym filename finding drift")
    require(sum("dictionary words" in path or "dictionary-words" in path for path in lower_paths) == findings["dictionary_words_named_dedicated_source_candidates_in_scope"] == 0, "dictionary-words filename finding drift")
    require(sum("phraseolog" in path for path in lower_paths) == findings["phraseology_named_dedicated_source_candidates_in_scope"] == 0, "phraseology filename finding drift")

    effect = artifact["reconciliation_effect"]
    require(all(str(effect[name]).startswith("UNKNOWN_BLOCKER") for name in ("orthoepy", "dictionary_words", "paronyms", "phraseology")), "all thematic trainers must remain fail-closed")
    require(effect["semantic_admissions"] == 0, "must not admit semantics")
    require(effect["object_closures"] == 0, "must not close objects")
    require(effect["mastery_admissions"] == 0, "must not admit mastery")
    require(effect["false_exact_mastery"] == 0, "false exact mastery must remain zero")

    print("THEMATIC_TRAINER_EGE_SOURCE_RUSSKIY_CANDIDATE_INVENTORY=PASS")
    print(f"source_commit={SOURCE_COMMIT}")
    print(f"source_tree={SOURCE_TREE}")
    print("orthoepy_named_pdf_candidates=3:2022,2023,2024")
    print("paronym_named_pdf_candidates=3:2022,2023,2024")
    print("orthoepy_2025_2026_named_candidates=0")
    print("paronyms_2025_2026_named_candidates=0")
    print("dictionary_words_named_candidates=0")
    print("phraseology_named_candidates=0")
    print("live_item_identity_binding=BLOCKED_NOT_PROVEN")
    print("false_exact_mastery=0")


if __name__ == "__main__":
    main()
