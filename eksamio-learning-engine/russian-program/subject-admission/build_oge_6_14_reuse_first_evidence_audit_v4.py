#!/usr/bin/env python3
"""OGE 6.14 evidence audit v4 with structured-owner branch-complete repair.

v3 proved the 83-owner denominator and the 48-item final evidence floor, but its
item-count rule could mark a structured canonical owner ready from evidence that
covered only a narrow sub-branch. v4 keeps the exact 83-owner frontier immutable,
replaces exactly six wave-002 items for two structured owners, proves their full
accepted branch coverage, and makes no OGE 6.14 object admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
BASE_V3 = HERE / "build_oge_6_14_reuse_first_evidence_audit_v3.py"
REPAIR = ENGINE / "russian-program/production-learning-content/RU-PROG-08-OGE-6.14-GAP-EVIDENCE-WAVE-002-STRUCTURED-REPAIR-v0.1.json"
AUTH_248 = ENGINE / "248-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A2-ALTERNATING-ROOTS-NORMALIZATION-v0.1.json"
AUTH_249 = ENGINE / "249-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A3-E-E-Y-DOUBLE-CONSONANTS-v0.1.json"
REPAIR_VALIDATOR = "russian-program/subject-admission/validate_oge_6_14_wave_002_structured_repair.py"

DOUBLE_OWNER = "school-double-consonants-morpheme-junction"
IE_OWNER = "school-i-e-alternating-verb-roots-stressed-a"
EXPECTED_OWNERS = [DOUBLE_OWNER, IE_OWNER]
EXPECTED_OLD_IDS = {
    DOUBLE_OWNER: ["oge614-w2-junction-v1", "oge614-w2-junction-v2", "oge614-w2-junction-v3"],
    IE_OWNER: ["oge614-w2-ie-v1", "oge614-w2-ie-v2", "oge614-w2-ie-v3"],
}
EXPECTED_BRANCHES = {
    DOUBLE_OWNER: {
        "prefix_root",
        "stem_suffix_oge_6_2_numeral",
        "compound_part_junction",
    },
    IE_OWNER: {
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
    },
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalized_sha(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def one(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    matches = [row for row in rows if row.get(key) == value]
    if len(matches) != 1:
        raise ValueError(f"expected one {key}={value}, got {len(matches)}")
    return matches[0]


def validate_canonical_authorities() -> None:
    a248 = load(AUTH_248)
    a249 = load(AUTH_249)

    double = one(a249["resolution_O08"]["canonical_units"], "unit_id", DOUBLE_OWNER)
    if double.get("unit_type") != "productive_boundary_system":
        raise ValueError("double-consonant owner type drift")
    if double.get("branches") != [
        "prefix + root",
        "stem + suffix",
        "abbreviation/compound-part junction where identical consonants meet",
    ]:
        raise ValueError("double-consonant accepted branch set drift")

    ie = one(a248["new_canonical_units"], "unit_id", IE_OWNER)
    if ie.get("unit_type") != "structured_alternating_root_family":
        raise ValueError("I/E owner type drift")
    if "последующем ударном -А-" not in str(ie.get("canonical_label") or ""):
        raise ValueError("I/E current canonical formulation drift")
    for token in [
        "БЕР/БИР", "ДЕР/ДИР", "МЕР/МИР", "ПЕР/ПИР", "ТЕР/ТИР",
        "БЛЕСТ/БЛИСТ", "ЖЕГ/ЖИГ", "СТЕЛ/СТИЛ", "ЧЕТ/ЧИТ",
    ]:
        if token not in str(ie.get("source_branch") or ""):
            raise ValueError(f"I/E accepted branch missing: {token}")
    if ie.get("absorbs_semantic_id") != "school-chet-chit-sochetat-sochetanie":
        raise ValueError("I/E absorbed semantic boundary drift")
    absorbed = str(ie.get("absorbed_branch") or "")
    if "СОЧЕТАТЬ" not in absorbed or "СОЧЕТАНИЕ" not in absorbed:
        raise ValueError("I/E traditional сочетать/сочетание boundary drift")


def validate_repair_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    owner = str(row.get("canonical_ref") or "")
    if owner not in EXPECTED_BRANCHES:
        raise ValueError(f"unexpected repair owner: {owner}")
    if row.get("source_oge_code") != "6.2":
        raise ValueError(f"repair owner is not bound to OGE 6.2: {owner}")
    if row.get("replaces_item_ids") != EXPECTED_OLD_IDS[owner]:
        raise ValueError(f"replacement item identity drift: {owner}")

    required = row.get("required_branch_ids")
    if not isinstance(required, list) or len(required) != len(set(required)):
        raise ValueError(f"invalid required branch list: {owner}")
    if set(str(branch) for branch in required) != EXPECTED_BRANCHES[owner]:
        raise ValueError(f"required branch set drift: {owner}")

    items = [item for item in row.get("independent_verification") or [] if isinstance(item, dict)]
    if len(items) != 3:
        raise ValueError(f"repair must replace exactly three items: {owner}")
    if {str(item.get("type")) for item in items} != {"single_choice", "constructed_response"}:
        raise ValueError(f"repair must contain selected + constructed response: {owner}")

    covered: set[str] = set()
    ids: list[str] = []
    for item in items:
        item_id = str(item.get("id") or "")
        ids.append(item_id)
        if item.get("evidence_mode") != "INDEPENDENT":
            raise ValueError(f"non-independent repair item: {item_id}")
        if item.get("school_semantic_refs") != [owner]:
            raise ValueError(f"mixed/wrong repair item: {item_id}")
        branch_ids = item.get("covered_branch_ids")
        if not isinstance(branch_ids, list) or not branch_ids or len(branch_ids) != len(set(branch_ids)):
            raise ValueError(f"invalid covered branches: {item_id}")
        unknown = {str(branch) for branch in branch_ids} - EXPECTED_BRANCHES[owner]
        if unknown:
            raise ValueError(f"unknown repair branches for {item_id}: {sorted(unknown)}")
        covered.update(str(branch) for branch in branch_ids)
        if len(str(item.get("prompt") or "").strip()) < 15:
            raise ValueError(f"repair prompt too short: {item_id}")
        if item.get("type") == "single_choice":
            options = item.get("options")
            index = item.get("correct_option_index")
            if not isinstance(options, list) or len(options) != 3 or len(set(str(x) for x in options)) != 3:
                raise ValueError(f"invalid repair options: {item_id}")
            if not isinstance(index, int) or not 0 <= index < 3:
                raise ValueError(f"invalid repair answer index: {item_id}")
            if len(str(item.get("feedback") or "").strip()) < 20:
                raise ValueError(f"repair feedback too short: {item_id}")
        elif item.get("type") == "constructed_response":
            if len(str(item.get("answer_outline") or "").strip()) < 40:
                raise ValueError(f"repair outline too short: {item_id}")
            scoring = item.get("scoring") or {}
            if scoring.get("max_points") != 2:
                raise ValueError(f"repair scoring max drift: {item_id}")
            criteria = scoring.get("criteria") or []
            if len(criteria) != 2 or any(len(str(c).strip()) < 25 for c in criteria):
                raise ValueError(f"repair scoring criteria invalid: {item_id}")
        else:
            raise ValueError(f"unsupported repair item type: {item_id}")

    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate repair item ids: {owner}")
    if covered != EXPECTED_BRANCHES[owner]:
        raise ValueError(f"full accepted branch coverage not proven for {owner}; missing={sorted(EXPECTED_BRANCHES[owner] - covered)}")

    boundary = str(row.get("semantic_boundary") or "").lower()
    if owner == DOUBLE_OWNER:
        for token in ["пристав", "суффикс", "сложн", "одиннадцать"]:
            if token not in boundary:
                raise ValueError(f"double owner boundary missing {token!r}")
    if owner == IE_OWNER:
        for token in ["ударн", "сочет", "чет/чит"]:
            if token not in boundary:
                raise ValueError(f"I/E owner boundary missing {token!r}")
    return items


def build_audit_v4() -> dict[str, Any]:
    validate_canonical_authorities()
    base = runpy.run_path(str(BASE_V3))["build_audit_v3"]()
    if base.get("status") != "CENTRAL_BRAIN_OGE_6_14_COMPONENT_EVIDENCE_COMPLETE_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE_NOT_ACCEPTED":
        raise ValueError("v3 base status drift")
    summary = base.get("summary") or {}
    if summary.get("exact_owner_frontier") != 83:
        raise ValueError("v3 exact owner frontier drift")
    if summary.get("owners_with_explicit_component_specific_independent_evidence") != 83:
        raise ValueError("v3 evidence-ready owner count drift")
    if summary.get("exact_independent_items_reused") != 262:
        raise ValueError("v3 exact item denominator drift")
    if base.get("missing_owner_refs") != []:
        raise ValueError("v3 unexpectedly has missing owners")

    repair = load(REPAIR)
    if repair.get("status") != "CURRENT_LAUNCH_OGE_6_14_WAVE_002_STRUCTURED_OWNER_REPLACEMENT_EVIDENCE_NO_OBJECT_ADMISSION":
        raise ValueError("structured repair status drift")
    policy = repair.get("repair_policy") or {}
    if policy.get("replacement_owner_count") != 2 or policy.get("replacement_item_count") != 6:
        raise ValueError("structured repair denominator drift")
    if policy.get("additional_effective_item_count") != 0:
        raise ValueError("structured repair must be replacement-only")
    if policy.get("effective_wave_owner_count") != 16 or policy.get("effective_wave_item_count") != 48:
        raise ValueError("effective wave denominator drift")
    if policy.get("exact_owner_frontier") != 83 or policy.get("exact_owner_frontier_may_change_here") is not False:
        raise ValueError("repair changed exact owner frontier policy")
    if policy.get("new_semantic_identity_created") is not False:
        raise ValueError("repair may not create semantics")
    if policy.get("route_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("repair weakened route mastery boundary")

    rows = [row for row in repair.get("owner_replacements") or [] if isinstance(row, dict)]
    if [str(row.get("canonical_ref") or "") for row in rows] != EXPECTED_OWNERS:
        raise ValueError("structured repair owner order/set drift")

    result = json.loads(json.dumps(base, ensure_ascii=False))
    reviews = {str(row.get("canonical_ref") or ""): row for row in result.get("owner_reviews") or [] if isinstance(row, dict)}
    all_old_ids: list[str] = []
    all_new_ids: list[str] = []

    for repair_row in rows:
        owner = str(repair_row["canonical_ref"])
        items = validate_repair_row(repair_row)
        review = reviews.get(owner)
        if review is None:
            raise ValueError(f"v3 owner review absent: {owner}")
        old_evidence = [item for item in review.get("exact_component_independent_items") or [] if isinstance(item, dict)]
        old_ids = [str(item.get("source_id") or "") for item in old_evidence]
        if old_ids != EXPECTED_OLD_IDS[owner]:
            raise ValueError(f"v3 old evidence identity drift: {owner}: {old_ids}")
        if int(review.get("exact_component_independent_item_count") or 0) != 3:
            raise ValueError(f"v3 old structured owner count drift: {owner}")

        replacement_evidence: list[dict[str, Any]] = []
        for item in items:
            replacement_evidence.append({
                "source_kind": "VALIDATED_OGE_6_14_WAVE_002_STRUCTURED_REPLACEMENT_EVIDENCE",
                "source_system": "current_launch_original_eksamio_component_evidence",
                "source_id": str(item["id"]),
                "review_status": "validated_structured_branch_complete_replacement_evidence",
                "school_semantic_refs": [owner],
                "covered_branch_ids": list(item["covered_branch_ids"]),
                "evidence_provenance_refs": [str(REPAIR.relative_to(ENGINE)), REPAIR_VALIDATOR],
                "source_oge_code": "6.2",
            })
        review["evidence_status"] = "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT_STRUCTURED_BRANCH_COMPLETE"
        review["exact_component_independent_item_count"] = 3
        review["exact_component_independent_items"] = replacement_evidence
        review["required_branch_ids"] = list(repair_row["required_branch_ids"])
        review["covered_branch_ids"] = sorted({
            str(branch)
            for item in items
            for branch in item["covered_branch_ids"]
        })
        review["structured_repair_superseded_source_ids"] = old_ids
        all_old_ids.extend(old_ids)
        all_new_ids.extend(str(item["id"]) for item in items)

    if len(all_old_ids) != 6 or len(set(all_old_ids)) != 6:
        raise ValueError("superseded structured evidence count drift")
    if len(all_new_ids) != 6 or len(set(all_new_ids)) != 6:
        raise ValueError("replacement structured evidence count drift")

    exact_total = sum(int(row.get("exact_component_independent_item_count") or 0) for row in reviews.values())
    if exact_total != 262:
        raise ValueError(f"effective exact evidence denominator drift: {exact_total}")
    if len(result.get("exact_owner_refs") or []) != 83 or result.get("missing_owner_refs") != []:
        raise ValueError("effective 83-owner frontier changed")

    for source in result.get("validated_existing_evidence_sources") or []:
        if isinstance(source, dict) and source.get("content_code") == "6.14-gap-wave-002":
            source["structured_owner_source_ids_superseded_by_v4"] = all_old_ids
            source["effective_item_count_after_replacement"] = 48
    result.setdefault("validated_existing_evidence_sources", []).append({
        "content_code": "6.14-gap-wave-002-structured-repair",
        "pack": str(REPAIR.relative_to(ENGINE)),
        "validator": REPAIR_VALIDATOR,
        "replacement_owner_count": 2,
        "replacement_item_count": 6,
        "additional_effective_item_count": 0,
        "superseded_source_ids": all_old_ids,
        "replacement_source_ids": all_new_ids,
    })

    result["status"] = "CENTRAL_BRAIN_OGE_6_14_COMPONENT_EVIDENCE_COMPLETE_STRUCTURED_BRANCH_COVERAGE_PROVEN_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE_NOT_ACCEPTED"
    result["scope"] = "OGE_2026_CONTENT_CODE_6_14_REUSE_FIRST_EXACT_COMPONENT_EVIDENCE_AUDIT_V4_STRUCTURED_REPAIR"
    result["summary"] = {
        **summary,
        "exact_owner_frontier": 83,
        "owners_with_explicit_component_specific_independent_evidence": 83,
        "owners_with_no_independent_evidence": 0,
        "exact_independent_items_reused": 262,
        "effective_wave_002_owner_count": 16,
        "effective_wave_002_independent_items": 48,
        "structured_repair_owner_count": 2,
        "structured_repair_replaced_item_count": 6,
        "structured_repair_additional_item_count": 0,
        "structured_branch_coverage_complete": True,
        "ready_for_separate_exact_object_acceptance": True,
        "semantic_admissions": 0,
        "object_closures": 0,
        "false_exact_mastery_admissions": 0,
    }
    result["next_gate"] = (
        "Create a separate OGE 6.14 exact object acceptance bound to the unchanged 83-owner frontier "
        "and this v4 structured-branch-complete evidence fingerprint. Before aggregate integration, "
        "compare against historical accepted object identity to prevent double counting."
    )
    result.pop("normalized_sha256", None)
    result["normalized_sha256"] = normalized_sha(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_audit_v4()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        s = result["summary"]
        print("OGE_6_14_REUSE_FIRST_EVIDENCE_AUDIT_V4=PASS")
        print(f"EXACT_OWNER_FRONTIER={s['exact_owner_frontier']}")
        print(f"OWNERS_WITH_EXACT_COMPONENT_EVIDENCE={s['owners_with_explicit_component_specific_independent_evidence']}")
        print(f"EXACT_INDEPENDENT_ITEMS={s['exact_independent_items_reused']}")
        print(f"EFFECTIVE_WAVE_002_ITEMS={s['effective_wave_002_independent_items']}")
        print(f"STRUCTURED_REPAIR_REPLACED_ITEMS={s['structured_repair_replaced_item_count']}")
        print("STRUCTURED_BRANCH_COVERAGE_COMPLETE=1")
        print("READY_FOR_SEPARATE_EXACT_OBJECT_ACCEPTANCE=1")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_CLOSURES=0")
        print("FALSE_EXACT_MASTERY=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
