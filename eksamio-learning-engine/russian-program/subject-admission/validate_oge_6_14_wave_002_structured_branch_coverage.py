#!/usr/bin/env python3
"""Fail-closed semantic branch-coverage gate for OGE 6.14 evidence wave 002.

The existing wave-002 gate proves item count and exact single-owner references. This
additional gate proves that structured/multi-branch canonical owners are not marked
evidence-ready from three items that exercise only a narrow sub-branch.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
PACK = ENGINE / "russian-program/production-learning-content/RU-PROG-08-OGE-6.14-GAP-EVIDENCE-WAVE-002-v0.1.json"
AUTH_248 = ENGINE / "248-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A2-ALTERNATING-ROOTS-NORMALIZATION-v0.1.json"
AUTH_249 = ENGINE / "249-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A3-E-E-Y-DOUBLE-CONSONANTS-v0.1.json"

DOUBLE_OWNER = "school-double-consonants-morpheme-junction"
IE_OWNER = "school-i-e-alternating-verb-roots-stressed-a"

DOUBLE_BRANCHES = {
    "prefix_root",
    "stem_suffix_oge_6_2_numeral",
    "compound_part_junction",
}
IE_BRANCHES = {
    "ber_bir",
    "der_dir",
    "mer_mir",
    "per_pir",
    "ter_tir",
    "blest_blist",
    "zheg_zhig",
    "stel_stil",
    "chet_chit",
    "sochetat_sochetanie_traditional_boundary",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected JSON object: {path}")
    return value


def one(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    matches = [row for row in rows if row.get(key) == value]
    assert len(matches) == 1, f"expected one {key}={value}, got {len(matches)}"
    return matches[0]


def validate_authorities() -> None:
    a248 = load(AUTH_248)
    a249 = load(AUTH_249)

    double = one(a249["resolution_O08"]["canonical_units"], "unit_id", DOUBLE_OWNER)
    assert double["unit_type"] == "productive_boundary_system"
    assert double["branches"] == [
        "prefix + root",
        "stem + suffix",
        "abbreviation/compound-part junction where identical consonants meet",
    ]

    ie = one(a248["new_canonical_units"], "unit_id", IE_OWNER)
    assert ie["unit_type"] == "structured_alternating_root_family"
    assert "последующем ударном -А-" in ie["canonical_label"]
    for token in [
        "БЕР/БИР",
        "ДЕР/ДИР",
        "МЕР/МИР",
        "ПЕР/ПИР",
        "ТЕР/ТИР",
        "БЛЕСТ/БЛИСТ",
        "ЖЕГ/ЖИГ",
        "СТЕЛ/СТИЛ",
        "ЧЕТ/ЧИТ",
    ]:
        assert token in ie["source_branch"], f"accepted I/E branch drift: {token}"
    assert ie["absorbs_semantic_id"] == "school-chet-chit-sochetat-sochetanie"
    assert "СОЧЕТАТЬ" in ie["absorbed_branch"] and "СОЧЕТАНИЕ" in ie["absorbed_branch"]


def validate_owner_branch_coverage(
    row: dict[str, Any], expected: set[str], *, require_boundary_tokens: tuple[str, ...] = ()
) -> None:
    required = row.get("required_branch_ids")
    assert isinstance(required, list), f"{row['canonical_ref']}: required_branch_ids missing"
    assert len(required) == len(set(required)), f"{row['canonical_ref']}: duplicate required_branch_ids"
    assert set(required) == expected, (
        f"{row['canonical_ref']}: required branch set drift; "
        f"missing={sorted(expected - set(required))} extra={sorted(set(required) - expected)}"
    )

    items = row.get("independent_verification")
    assert isinstance(items, list) and len(items) >= 3
    covered: set[str] = set()
    response_types = {str(item.get("type")) for item in items if isinstance(item, dict)}
    assert {"single_choice", "constructed_response"}.issubset(response_types)
    for item in items:
        assert isinstance(item, dict)
        assert item.get("evidence_mode") == "INDEPENDENT"
        assert item.get("school_semantic_refs") == [row["canonical_ref"]]
        branch_ids = item.get("covered_branch_ids")
        assert isinstance(branch_ids, list) and branch_ids, (
            f"{row['canonical_ref']}#{item.get('id')}: covered_branch_ids missing"
        )
        assert len(branch_ids) == len(set(branch_ids)), (
            f"{row['canonical_ref']}#{item.get('id')}: duplicate covered_branch_ids"
        )
        unknown = set(branch_ids) - expected
        assert not unknown, f"{row['canonical_ref']}#{item.get('id')}: unknown branches {sorted(unknown)}"
        covered.update(str(branch_id) for branch_id in branch_ids)

    assert covered == expected, (
        f"{row['canonical_ref']}: evidence does not cover full accepted semantic breadth; "
        f"missing={sorted(expected - covered)}"
    )
    boundary = str(row.get("semantic_boundary") or "").lower()
    for token in require_boundary_tokens:
        assert token.lower() in boundary, f"{row['canonical_ref']}: semantic boundary missing {token!r}"


def main() -> int:
    validate_authorities()
    pack = load(PACK)
    assert pack["status"] == "CURRENT_LAUNCH_OGE_6_14_GAP_EVIDENCE_WAVE_002_NO_OBJECT_ADMISSION"
    assert pack["evidence_policy"]["exact_owner_frontier_may_change_here"] is False
    assert pack["evidence_policy"]["route_attempt_can_emit_exact_component_mastery"] is False

    rows = [row for row in pack["owner_evidence"] if isinstance(row, dict)]
    double = one(rows, "canonical_ref", DOUBLE_OWNER)
    ie = one(rows, "canonical_ref", IE_OWNER)

    validate_owner_branch_coverage(double, DOUBLE_BRANCHES)
    assert "stem_suffix_oge_6_2_numeral" in {
        branch_id
        for item in double["independent_verification"]
        for branch_id in item["covered_branch_ids"]
    }

    validate_owner_branch_coverage(
        ie,
        IE_BRANCHES,
        require_boundary_tokens=("ударн", "сочет"),
    )

    summary = pack["summary"]
    assert summary["semantic_admissions"] == 0
    assert summary["object_closures"] == 0
    assert summary["false_exact_mastery_admissions"] == 0
    assert pack["safety"]["learner_audio_persistence"] == 0

    print("OGE_6_14_WAVE_002_STRUCTURED_OWNER_BRANCH_COVERAGE=PASS")
    print(f"DOUBLE_JUNCTION_BRANCHES_COVERED={len(DOUBLE_BRANCHES)}")
    print(f"IE_STRUCTURED_FAMILY_BRANCHES_COVERED={len(IE_BRANCHES)}")
    print("OGE_6_14_OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
