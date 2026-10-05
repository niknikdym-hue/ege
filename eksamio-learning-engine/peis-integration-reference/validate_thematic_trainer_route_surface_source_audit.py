#!/usr/bin/env python3
"""Audit exact #164 trainer route-surface source directories.

This is intentionally bounded. It proves what the two public trainer-index
source directories contain at the immutable Russian closure commit and keeps
all thematic learner identity/mastery effects fail-closed. It does not claim
that live backing data or another canonical source cannot exist elsewhere.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

SOURCE_COMMIT = "7edddb9f9764b5e8cdf7e2653c425e5f90c4ffe9"
ARTIFACT_PATH = Path(__file__).with_name(
    "THEMATIC-TRAINER-ROUTE-SURFACE-SOURCE-AUDIT-v0.1.json"
)

EXPECTED_TREES = {
    "trenazhery-russkiy": "b2efaaa7946744d7da5229ab08a14f95710ce543",
    "trenazhery": "a126043f565fb2249da758c577f2c97a01ab4405",
}

EXPECTED_FILES = {
    "trenazhery-russkiy": {
        "trenazhery-russkiy/trenazhery-russkiy-HEAD.txt": (
            "7e3e14112bb69a6135e386e208c9d52f2b9863a6",
            3187,
        ),
        "trenazhery-russkiy/trenazhery-russkiy-SEO.txt": (
            "f445d4b11d0795701456b5ba5b0d9bf4f2d4d0a0",
            894,
        ),
        "trenazhery-russkiy/trenazhery-russkiy-T123.txt": (
            "512c01d4b902e59d8a3b516d835613b9e1b13e08",
            7083,
        ),
    },
    "trenazhery": {
        "trenazhery/trenazhery-HEAD.txt": (
            "d544e47cacdb403d02d46d53f277a6fc5dbd1ad8",
            2350,
        ),
        "trenazhery/trenazhery-SEO.txt": (
            "87d1ff247399d0dc2b5608a695f25119ead49950",
            824,
        ),
        "trenazhery/trenazhery-T123.txt": (
            "cf003b344ad2b2af33311f7969285ab1324e1378",
            6765,
        ),
    },
}

EXPECTED_ROUTES = [
    "/trenazhery/russkiy/orfoepiya/",
    "/trenazhery/russkiy/slovarnye-slova/",
    "/trenazhery/russkiy/paronimy/",
    "/trenazhery/russkiy/frazeologizmy/",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def git_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{path}"])


def main() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    require(artifact["source_commit"] == SOURCE_COMMIT, "source commit drift")

    for directory, expected_tree in EXPECTED_TREES.items():
        actual_tree = git_text("rev-parse", f"{SOURCE_COMMIT}:{directory}")
        require(actual_tree == expected_tree, f"{directory} tree drift: {actual_tree}")

        observed_paths = sorted(
            line
            for line in git_text(
                "ls-tree", "-r", "--name-only", SOURCE_COMMIT, "--", directory
            ).splitlines()
            if line
        )
        expected_paths = sorted(EXPECTED_FILES[directory])
        require(
            observed_paths == expected_paths,
            f"{directory} exact file set drift: {observed_paths!r}",
        )

        for path, (expected_blob, expected_size) in EXPECTED_FILES[directory].items():
            actual_blob = git_text("rev-parse", f"{SOURCE_COMMIT}:{path}")
            require(actual_blob == expected_blob, f"{path} blob drift: {actual_blob}")
            actual_size = int(git_text("cat-file", "-s", actual_blob))
            require(actual_size == expected_size, f"{path} byte count drift: {actual_size}")

    artifact_dirs = {row["path"]: row for row in artifact["directories"]}
    require(set(artifact_dirs) == set(EXPECTED_TREES), "artifact directory set drift")
    for directory, expected_tree in EXPECTED_TREES.items():
        require(
            artifact["root_discovery"][directory]["git_tree_sha1"] == expected_tree,
            f"artifact {directory} tree drift",
        )
        observed = {
            row["path"]: (row["git_blob_sha1"], row["byte_count"])
            for row in artifact_dirs[directory]["files"]
        }
        require(observed == EXPECTED_FILES[directory], f"artifact {directory} files drift")

    russian_index = git_bytes(
        "trenazhery-russkiy/trenazhery-russkiy-T123.txt"
    ).decode("utf-8")
    require(
        artifact["russian_index_exact_routes"] == EXPECTED_ROUTES,
        "artifact route list drift",
    )
    for route in EXPECTED_ROUTES:
        require(
            russian_index.count(f'href="{route}"') == 1,
            f"expected exactly one index link for {route}",
        )

    findings = artifact["bounded_findings"]
    require(findings["russian_index_source_proves_exact_four_route_links"] is True, "route-link finding drift")
    require(findings["these_two_directories_contain_per_theme_backing_payload"] is False, "surface directories must not be promoted to backing payload")
    require(findings["absence_of_backing_payload_elsewhere_in_repository_or_live_site_proven"] is False, "bounded audit must not overclaim global absence")
    require(findings["live_to_canonical_item_identity_proven"] is False, "live item identity must remain unproven")

    effect = artifact["reconciliation_effect"]
    for trainer in ("orthoepy", "dictionary_words", "paronyms", "phraseology"):
        require(str(effect[trainer]).startswith("UNKNOWN_BLOCKER"), f"{trainer} must remain fail-closed")
    require(effect["semantic_admissions"] == 0, "must not admit semantics")
    require(effect["object_closures"] == 0, "must not close objects")
    require(effect["mastery_admissions"] == 0, "must not admit mastery")
    require(effect["false_exact_mastery"] == 0, "false exact mastery must remain zero")

    print("THEMATIC_TRAINER_ROUTE_SURFACE_SOURCE_AUDIT=PASS")
    print(f"source_commit={SOURCE_COMMIT}")
    print("trainer_surface_directories=2")
    print("russian_index_exact_thematic_routes=4")
    print("per_theme_backing_payload_in_these_directories=NOT_FOUND")
    print("global_backing_absence=NOT_CLAIMED")
    print("live_to_canonical_item_identity=BLOCKED_NOT_PROVEN")
    print("false_exact_mastery=0")


if __name__ == "__main__":
    main()
