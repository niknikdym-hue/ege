#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
CONTENT = ENGINE / "russian-program" / "production-learning-content" / "RU-PROG-08-OGE-6.6-COMPONENT-EVIDENCE-WAVE-001-v0.1.json"
ROUTE = ENGINE / "278-RUSSIAN-FIPI-2026-OGE-6.6-CURRENT-ROUTE-SUPERSESSION-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

EXPECTED_STATUS = "CURRENT_LAUNCH_OGE_6_6_COMPONENT_EVIDENCE_CANDIDATE_NO_OBJECT_ADMISSION"
EXPECTED_TARGET = {
    "source_id": "FIPI-OGE-RU-2026-FINAL",
    "document_id": "OGE_COD",
    "content_code": "6.6",
    "admission_unit_id": "RAU-9d61ef1d2fd678fc3fee",
    "requirement_id": "RSK-OGE_COD-6-6-P024",
}


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object: {path}")
    return data


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def validate() -> dict[str, Any]:
    content = load(CONTENT)
    route = load(ROUTE)
    inventory = load(INVENTORY)

    if content.get("schema_version") != "0.1.0":
        raise ValueError("unexpected evidence schema")
    if content.get("status") != EXPECTED_STATUS:
        raise ValueError("evidence pack must remain no-object-admission candidate")
    if content.get("module_id") != "RU-PROG-08":
        raise ValueError("OGE 6.6 evidence must stay in RU-PROG-08")
    if content.get("target") != EXPECTED_TARGET:
        raise ValueError("OGE 6.6 exact target identity drift")

    route_owners = [str(ref) for ref in route.get("exact_owner_refs") or []]
    if len(route_owners) != 10 or len(set(route_owners)) != 10:
        raise ValueError("route must expose exactly 10 unique owners")
    if route.get("mastery_boundary", {}).get("route_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("route mastery boundary weakened")

    canonical_rows = {
        str(row.get("source_id")): row
        for row in inventory.get("objects") or []
        if isinstance(row, dict)
        and row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and row.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
        and row.get("review_status") == "reviewed"
    }

    policy = content.get("evidence_policy") or {}
    required_policy = {
        "reuse_first": True,
        "new_semantic_identity_created": False,
        "exact_owner_frontier_may_change_here": False,
        "each_item_must_reference_exactly_one_school_semantic": True,
        "minimum_independent_items_per_owner": 3,
        "component_specific_independent_evidence_required": True,
        "route_attempt_can_emit_exact_component_mastery": False,
        "evidence_readiness_is_object_acceptance": False,
    }
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            raise ValueError(f"evidence policy drift: {key}")

    rows = content.get("owner_evidence") or []
    if len(rows) != 10:
        raise ValueError("evidence pack must contain exactly 10 owner rows")
    refs = [str(row.get("canonical_ref")) for row in rows if isinstance(row, dict)]
    if set(refs) != set(route_owners) or len(refs) != len(set(refs)):
        raise ValueError("evidence owner set must equal route owner frontier exactly")

    item_ids: set[str] = set()
    per_owner: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("owner row is not object")
        owner = str(row.get("canonical_ref"))
        canonical_row = canonical_rows.get(owner)
        if canonical_row is None:
            raise ValueError(f"owner is not a current reviewed school canonical identity: {owner}")
        if row.get("title_ru") != canonical_row.get("observed_label"):
            raise ValueError(f"owner title drift: {owner}")
        if row.get("evidence_status") != "CURRENT_LAUNCH_ORIGINAL_EKSAMIO_COMPONENT_EVIDENCE":
            raise ValueError(f"owner evidence status drift: {owner}")
        boundary = row.get("semantic_boundary")
        if not isinstance(boundary, str) or len(boundary.strip()) < 40:
            raise ValueError(f"owner boundary too weak: {owner}")

        guard = row.get("mastery_guard") or {}
        if guard != {
            "minimum_independent_items_required": 3,
            "component_specific_only": True,
            "generic_oge_route_result_can_emit_exact_mastery": False,
            "assisted_attempt_can_count_as_independent_evidence": False,
        }:
            raise ValueError(f"mastery guard drift: {owner}")

        items = row.get("independent_verification") or []
        if len(items) < 3:
            raise ValueError(f"insufficient independent items: {owner}")
        types = {str(item.get("type")) for item in items if isinstance(item, dict)}
        if "single_choice" not in types or "constructed_response" not in types:
            raise ValueError(f"owner needs both selected and constructed independent evidence: {owner}")

        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"non-object evidence item: {owner}")
            item_id = str(item.get("id") or "")
            if not item_id or item_id in item_ids:
                raise ValueError(f"missing/duplicate item id: {item_id}")
            item_ids.add(item_id)
            if item.get("evidence_mode") != "INDEPENDENT":
                raise ValueError(f"non-independent evidence item: {item_id}")
            if item.get("school_semantic_refs") != [owner]:
                raise ValueError(f"mixed or wrong semantic refs: {item_id}")
            prompt = item.get("prompt")
            if not isinstance(prompt, str) or len(prompt.strip()) < 15:
                raise ValueError(f"weak prompt: {item_id}")
            kind = item.get("type")
            if kind == "single_choice":
                options = item.get("options") or []
                idx = item.get("correct_option_index")
                if len(options) < 3 or not isinstance(idx, int) or not 0 <= idx < len(options):
                    raise ValueError(f"invalid single-choice evidence: {item_id}")
                if not isinstance(item.get("feedback"), str) or len(item["feedback"].strip()) < 15:
                    raise ValueError(f"missing feedback: {item_id}")
            elif kind == "constructed_response":
                scoring = item.get("scoring") or {}
                if not isinstance(scoring.get("max_points"), int) or scoring["max_points"] < 2:
                    raise ValueError(f"constructed score too weak: {item_id}")
                criteria = scoring.get("criteria") or []
                if len(criteria) < 2 or any(not isinstance(c, str) or len(c.strip()) < 15 for c in criteria):
                    raise ValueError(f"constructed criteria too weak: {item_id}")
                if not isinstance(item.get("answer_outline"), str) or len(item["answer_outline"].strip()) < 20:
                    raise ValueError(f"constructed answer outline missing: {item_id}")
            else:
                raise ValueError(f"unsupported evidence type: {kind}")
        per_owner[owner] = len(items)

    guard = content.get("copyright_guard") or {}
    if guard.get("official_source_passages_copied") != 0:
        raise ValueError("official source prose copied")
    if guard.get("commercial_textbook_bytes") != 0 or guard.get("commercial_textbook_prose_copied") != 0:
        raise ValueError("commercial textbook material present")
    if guard.get("learner_prompts_examples_feedback") != "ORIGINAL_EKSAMIO":
        raise ValueError("learner evidence is not declared original Eksamio")

    summary = content.get("summary") or {}
    if summary != {
        "exact_owner_frontier": 10,
        "owners_with_materialized_component_evidence": 10,
        "independent_items_total": len(item_ids),
        "semantic_admissions": 0,
        "object_closures": 0,
        "requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise ValueError("evidence summary drift")

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
        raise ValueError("safety boundary drift")

    result = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_OGE_6_6_COMPONENT_EVIDENCE_MATERIALIZED_NO_OBJECT_ADMISSION",
        "target": EXPECTED_TARGET,
        "exact_owner_refs": route_owners,
        "summary": {
            "exact_owner_frontier": len(route_owners),
            "owners_with_valid_component_evidence": len(per_owner),
            "independent_items_total": len(item_ids),
            "minimum_items_per_owner": min(per_owner.values()),
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
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    s = result["summary"]
    print("OGE_6_6_COMPONENT_EVIDENCE=PASS")
    print(f"EXACT_OWNER_FRONTIER={s['exact_owner_frontier']}")
    print(f"OWNERS_WITH_VALID_COMPONENT_EVIDENCE={s['owners_with_valid_component_evidence']}")
    print(f"INDEPENDENT_ITEMS_TOTAL={s['independent_items_total']}")
    print(f"MINIMUM_ITEMS_PER_OWNER={s['minimum_items_per_owner']}")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
