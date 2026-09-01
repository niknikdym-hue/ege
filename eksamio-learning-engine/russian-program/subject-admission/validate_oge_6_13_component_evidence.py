#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
CONTENT = ENGINE / "russian-program" / "production-learning-content" / "RU-PROG-08-OGE-6.13-COMPONENT-EVIDENCE-WAVE-001-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
OWNER_REVIEW = HERE / "build_oge_6_13_compound_words_exact_owner_resolution.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"

EXPECTED_STATUS = "CURRENT_LAUNCH_OGE_6_13_COMPONENT_EVIDENCE_CANDIDATE_NO_OBJECT_ADMISSION"
EXPECTED_TARGET = {
    "source_id": "FIPI-OGE-RU-2026-FINAL",
    "document_id": "OGE_COD",
    "content_code": "6.13",
}
EXPECTED_OWNERS = [
    "school-compound-linking-vowel",
    "school-compound-first-part-without-linking-vowel-system",
    "school-compound-noun-solid-hyphen-system",
    "school-compound-adjective-solid-hyphen-separate-system",
    "school-abbreviations-capitalization-formation",
]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def prove_source_target() -> dict[str, str]:
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for group in packet.get("semantic_review_groups") or []:
        if not isinstance(group, dict):
            continue
        for req in group.get("requirements") or []:
            if not isinstance(req, dict):
                continue
            if (
                req.get("source_id") == EXPECTED_TARGET["source_id"]
                and req.get("document_id") == EXPECTED_TARGET["document_id"]
                and str(req.get("code")) == EXPECTED_TARGET["content_code"]
            ):
                matches.append((group, req))
    if len(matches) != 1:
        raise ValueError(f"expected one exact OGE_COD 6.13 requirement, got {len(matches)}")
    group, req = matches[0]
    requirement_id = str(req.get("requirement_id") or "")
    locator = str(req.get("source_locator") or "")
    if not requirement_id.startswith("RSK-") or "6.13" not in locator:
        raise ValueError("invalid resolved OGE 6.13 source target")
    return {
        "requirement_id": requirement_id,
        "source_locator": locator,
        "packet_group": str(group.get("group_id") or ""),
    }


def validate() -> dict[str, Any]:
    content = load(CONTENT)
    inventory = load(INVENTORY)
    resolution = runpy.run_path(str(OWNER_REVIEW))["build_resolution"]()
    source_target = prove_source_target()

    if content.get("schema_version") != "0.1.0":
        raise ValueError("unexpected OGE 6.13 evidence schema")
    if content.get("status") != EXPECTED_STATUS:
        raise ValueError("OGE 6.13 evidence pack must remain no-object-admission candidate")
    if content.get("module_id") != "RU-PROG-08" or content.get("module_title_ru") != "Орфография":
        raise ValueError("OGE 6.13 evidence module boundary drift")
    if content.get("target") != EXPECTED_TARGET:
        raise ValueError("OGE 6.13 target drift")

    if resolution.get("status") != "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_EVIDENCE_AUDIT_REQUIRED":
        raise ValueError("OGE 6.13 exact-owner resolution state drift")
    r = resolution.get("exact_owner_resolution") or {}
    if r.get("exact_current_canonical_owners") != EXPECTED_OWNERS or r.get("exact_owner_count") != 5:
        raise ValueError("OGE 6.13 exact-owner set drift")
    if r.get("unresolved_owner_candidates") != 0 or r.get("new_school_identities_required") != 0:
        raise ValueError("OGE 6.13 owner frontier is not closed")
    if r.get("current_inventory_route_already_matches_exact_owner_set") is not True:
        raise ValueError("OGE 6.13 current route no longer equals exact-owner set")
    if r.get("current_route_supersession_required") is not False:
        raise ValueError("OGE 6.13 must not manufacture redundant route supersession")
    if r.get("evidence_gate_required_before_object_acceptance") is not True:
        raise ValueError("OGE 6.13 evidence gate weakened")

    objects = [row for row in inventory.get("objects") or [] if isinstance(row, dict)]
    canonical_rows = {
        str(row.get("source_id")): row
        for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
        and row.get("authority_status") == "current"
        and row.get("review_status") == "reviewed"
    }
    for owner in EXPECTED_OWNERS:
        row = canonical_rows.get(owner)
        if row is None:
            raise ValueError(f"missing current reviewed canonical owner: {owner}")
        if row.get("current_semantic_refs") != [owner] or row.get("candidate_canonical_owner") != owner:
            raise ValueError(f"canonical owner self-identity drift: {owner}")

    exact_inventory_items: dict[str, list[str]] = {owner: [] for owner in EXPECTED_OWNERS}
    for row in objects:
        if row.get("source_system") not in {"trainer_item", "practice_item"}:
            continue
        if row.get("authority_status") != "current" or row.get("review_status") not in {"source_verified", "reviewed"}:
            continue
        refs = [str(x) for x in row.get("current_semantic_refs") or []]
        for owner in EXPECTED_OWNERS:
            if refs == [owner]:
                exact_inventory_items[owner].append(str(row.get("source_id") or ""))
    existing_exact_total = sum(len(v) for v in exact_inventory_items.values())
    if existing_exact_total != 0:
        raise ValueError(
            "reuse-first truth changed: exact single-owner inventory evidence now exists; re-audit before keeping materialized evidence: "
            + json.dumps(exact_inventory_items, ensure_ascii=False, sort_keys=True)
        )

    policy = content.get("evidence_policy") or {}
    expected_policy = {
        "reuse_first": True,
        "existing_exact_inventory_evidence_must_be_audited": True,
        "new_semantic_identity_created": False,
        "exact_owner_frontier_may_change_here": False,
        "each_item_must_reference_exactly_one_school_semantic": True,
        "minimum_independent_items_per_owner": 3,
        "component_specific_independent_evidence_required": True,
        "route_attempt_can_emit_exact_component_mastery": False,
        "evidence_readiness_is_object_acceptance": False,
        "cross_route_reuse_used": False,
    }
    if policy != expected_policy:
        raise ValueError("OGE 6.13 evidence policy drift")

    audit = content.get("reuse_audit") or {}
    if audit.get("source_systems_checked") != ["trainer_item", "practice_item"]:
        raise ValueError("OGE 6.13 reuse audit source systems drift")
    if audit.get("existing_exact_single_owner_items_total") != 0:
        raise ValueError("OGE 6.13 reuse audit total drift")
    audit_rows = [row for row in audit.get("per_owner") or [] if isinstance(row, dict)]
    if [str(row.get("canonical_ref")) for row in audit_rows] != EXPECTED_OWNERS:
        raise ValueError("OGE 6.13 reuse-audit owner set/order drift")
    for row in audit_rows:
        if row.get("existing_exact_item_refs") != [] or row.get("materialized_new_items") != 3:
            raise ValueError(f"OGE 6.13 reuse-audit row drift: {row.get('canonical_ref')}")

    rows = [row for row in content.get("owner_evidence") or [] if isinstance(row, dict)]
    if len(rows) != 5 or [str(row.get("canonical_ref")) for row in rows] != EXPECTED_OWNERS:
        raise ValueError("OGE 6.13 evidence owner set/order drift")

    item_ids: set[str] = set()
    selected = 0
    constructed = 0
    per_owner: dict[str, int] = {}
    for row in rows:
        owner = str(row.get("canonical_ref"))
        boundary = row.get("semantic_boundary")
        if not isinstance(boundary, str) or len(boundary.strip()) < 80:
            raise ValueError(f"OGE 6.13 semantic boundary too weak: {owner}")
        if row.get("evidence_status") != "CURRENT_LAUNCH_ORIGINAL_EKSAMIO_COMPONENT_EVIDENCE":
            raise ValueError(f"OGE 6.13 evidence status drift: {owner}")
        if row.get("mastery_guard") != {
            "minimum_independent_items_required": 3,
            "component_specific_only": True,
            "generic_oge_route_result_can_emit_exact_mastery": False,
            "assisted_attempt_can_count_as_independent_evidence": False,
        }:
            raise ValueError(f"OGE 6.13 mastery guard drift: {owner}")

        evidence = [item for item in row.get("independent_verification") or [] if isinstance(item, dict)]
        if len(evidence) != 3:
            raise ValueError(f"OGE 6.13 requires exactly three independent items: {owner}")
        kinds = [str(item.get("type")) for item in evidence]
        if kinds.count("single_choice") != 2 or kinds.count("constructed_response") != 1:
            raise ValueError(f"OGE 6.13 item-type mix drift: {owner}")
        for item in evidence:
            item_id = str(item.get("id") or "")
            if not item_id or item_id in item_ids:
                raise ValueError(f"duplicate/empty OGE 6.13 item id: {item_id}")
            item_ids.add(item_id)
            if item.get("evidence_mode") != "INDEPENDENT" or item.get("school_semantic_refs") != [owner]:
                raise ValueError(f"OGE 6.13 item not exact single-owner independent evidence: {item_id}")
            prompt = item.get("prompt")
            if not isinstance(prompt, str) or len(prompt.strip()) < 20:
                raise ValueError(f"OGE 6.13 prompt too weak: {item_id}")
            if item.get("type") == "single_choice":
                options = item.get("options") or []
                idx = item.get("correct_option_index")
                if not isinstance(options, list) or len(options) < 3 or not isinstance(idx, int) or not 0 <= idx < len(options):
                    raise ValueError(f"OGE 6.13 single-choice scoring drift: {item_id}")
                feedback = item.get("feedback")
                if not isinstance(feedback, str) or len(feedback.strip()) < 20:
                    raise ValueError(f"OGE 6.13 feedback too weak: {item_id}")
                selected += 1
            else:
                outline = item.get("answer_outline")
                scoring = item.get("scoring") or {}
                criteria = scoring.get("criteria") or []
                if not isinstance(outline, str) or len(outline.strip()) < 40:
                    raise ValueError(f"OGE 6.13 constructed answer outline too weak: {item_id}")
                if not isinstance(scoring.get("max_points"), int) or scoring.get("max_points") < 2:
                    raise ValueError(f"OGE 6.13 constructed max points invalid: {item_id}")
                if not isinstance(criteria, list) or len(criteria) < 2 or any(not isinstance(x, str) or not x.strip() for x in criteria):
                    raise ValueError(f"OGE 6.13 constructed criteria invalid: {item_id}")
                constructed += 1
        per_owner[owner] = len(evidence)

    guard = content.get("copyright_guard") or {}
    if guard != {
        "official_source_passages_copied": 0,
        "commercial_textbook_bytes": 0,
        "commercial_textbook_prose_copied": 0,
        "learner_prompts_examples_feedback": "ORIGINAL_EKSAMIO",
    }:
        raise ValueError("OGE 6.13 copyright guard drift")

    provenance = [str(row.get("ref") or "") for row in content.get("source_provenance") or [] if isinstance(row, dict)]
    required_fragments = [
        "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25",
        "250-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A4-CAPITALIZATION",
        "build_oge_6_13_compound_words_exact_owner_resolution.py",
        "build_oge_6_13_object_evidence_audit.py",
        "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY",
        "doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf",
    ]
    for fragment in required_fragments:
        if not any(fragment in ref for ref in provenance):
            raise ValueError(f"OGE 6.13 provenance missing: {fragment}")

    summary = content.get("summary") or {}
    expected_summary = {
        "exact_owner_frontier": 5,
        "owners_with_materialized_component_evidence": 5,
        "existing_exact_inventory_items_reused": 0,
        "materialized_new_items": 15,
        "independent_items_total": 15,
        "semantic_admissions": 0,
        "object_closures": 0,
        "requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }
    if summary != expected_summary:
        raise ValueError("OGE 6.13 evidence summary drift")

    safety = content.get("safety") or {}
    expected_safety = {
        "accepted_demo_or_scorer_change": False,
        "tilda_change": False,
        "learner_audio_persistence": 0,
        "production_peis_write": False,
        "provider_execution": False,
        "public_traffic": False,
        "real_payment_or_refund": False,
        "real_message_delivery": False,
    }
    if safety != expected_safety:
        raise ValueError("OGE 6.13 safety boundary drift")

    content_sha = hashlib.sha256(canonical(content)).hexdigest()
    result = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_OGE_6_13_COMPONENT_EVIDENCE_MATERIALIZED_NO_OBJECT_ADMISSION",
        "target": {**EXPECTED_TARGET, **source_target},
        "exact_owner_refs": EXPECTED_OWNERS,
        "per_owner_independent_items": per_owner,
        "content_normalized_sha256": content_sha,
        "summary": {
            "exact_owner_frontier": 5,
            "owners_with_valid_component_evidence": 5,
            "independent_items_total": 15,
            "minimum_items_per_owner": 3,
            "selected_response_items": selected,
            "constructed_response_items": constructed,
            "existing_exact_inventory_items": 0,
            "materialized_new_items": 15,
            "semantic_admissions": 0,
            "object_closures": 0,
            "false_exact_mastery_admissions": 0,
        },
        "safety": expected_safety,
    }
    result["normalized_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    print("OGE_6_13_COMPONENT_EVIDENCE=PASS")
    print(f"REQUIREMENT_ID={result['target']['requirement_id']}")
    print(f"EXACT_OWNER_FRONTIER={s['exact_owner_frontier']}")
    print(f"OWNERS_WITH_VALID_COMPONENT_EVIDENCE={s['owners_with_valid_component_evidence']}")
    print(f"INDEPENDENT_ITEMS_TOTAL={s['independent_items_total']}")
    print(f"MINIMUM_ITEMS_PER_OWNER={s['minimum_items_per_owner']}")
    print(f"SELECTED_RESPONSE_ITEMS={s['selected_response_items']}")
    print(f"CONSTRUCTED_RESPONSE_ITEMS={s['constructed_response_items']}")
    print(f"EXISTING_EXACT_INVENTORY_ITEMS={s['existing_exact_inventory_items']}")
    print(f"MATERIALIZED_NEW_ITEMS={s['materialized_new_items']}")
    print(f"SEMANTIC_ADMISSIONS={s['semantic_admissions']}")
    print(f"OBJECT_CLOSURES={s['object_closures']}")
    print(f"FALSE_EXACT_MASTERY={s['false_exact_mastery_admissions']}")
    print(f"LEARNER_AUDIO_PERSISTENCE={result['safety']['learner_audio_persistence']}")
    print(f"CONTENT_NORMALIZED_SHA256={result['content_normalized_sha256']}")
    print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
