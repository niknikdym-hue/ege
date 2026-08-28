#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_source_semantic_crosswalk import build as build_crosswalk
from validate_russian_source_knowledge import load_rows, normalized_rows_hash

HERE = Path(__file__).resolve().parent
STATE = json.loads((HERE / "RUSSIAN-SOURCE-KNOWLEDGE-STATE-v1.0.json").read_text(encoding="utf-8"))
INDEX = json.loads((HERE / "RUSSIAN-OFFICIAL-REQUIREMENTS-INDEX-v1.0.json").read_text(encoding="utf-8"))


def main() -> int:
    rows = load_rows(INDEX)
    requirement_hash = normalized_rows_hash(rows)
    crosswalk = build_crosswalk()
    emitted = (json.dumps(crosswalk, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    emitted_hash = hashlib.sha256(emitted).hexdigest()

    req_state = STATE["requirements"]
    cross_state = STATE["crosswalk"]
    if req_state["count"] != len(rows) != 0:
        raise AssertionError("pinned requirement count drift")
    if req_state["runtime_normalized_rows_sha256"] != requirement_hash:
        raise AssertionError("pinned requirement normalized hash drift")
    if req_state["declared_extraction_sha256"] != INDEX["normalized_content_sha256"]:
        raise AssertionError("pinned declared extraction hash drift")
    if cross_state["record_count"] != crosswalk["record_count"]:
        raise AssertionError("pinned crosswalk count drift")
    if cross_state["normalized_rows_sha256"] != crosswalk["normalized_sha256"]:
        raise AssertionError("pinned crosswalk normalized hash drift")
    if cross_state["emitted_json_sha256"] != emitted_hash:
        raise AssertionError("pinned crosswalk emitted hash drift")
    if cross_state["counts"] != crosswalk["counts"]:
        raise AssertionError("pinned crosswalk status counts drift")
    if sum(cross_state["counts"].values()) != 1400:
        raise AssertionError("pinned crosswalk accounting incomplete")

    guards = STATE["guards"]
    if guards["commercial_textbook_bytes_ingested"] != 0:
        raise AssertionError("textbook ingestion guard drift")
    if guards["canonical_semantic_ids_admitted"] != 0:
        raise AssertionError("semantic admission guard drift")
    for key in (
        "fipi_oge_2027_project_allowed_as_launch_truth",
        "russian_content_subject_accepted",
        "public_traffic_enabled",
        "production_charges_enabled",
        "peis_network_writes_enabled",
        "yandex_gateway_apply_enabled",
    ):
        if guards[key] is not False:
            raise AssertionError(f"fail-closed state guard drift: {key}")

    print("RUSSIAN_SOURCE_KNOWLEDGE_STATE=PASS")
    print(f"runtime_requirement_package_sha256={requirement_hash}")
    print(f"crosswalk_normalized_sha256={crosswalk['normalized_sha256']}")
    print(f"crosswalk_emitted_sha256={emitted_hash}")
    for status, count in sorted(crosswalk["counts"].items()):
        print(f"crosswalk[{status}]={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
