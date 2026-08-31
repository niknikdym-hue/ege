#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
ROUTE = ENGINE / "279-RUSSIAN-FIPI-2026-OGE-6.7-CURRENT-ROUTE-SUPERSESSION-v0.1.json"
PACK = (
    ENGINE
    / "russian-program"
    / "production-learning-content"
    / "RU-PROG-08-OGE-6.7-COMPONENT-EVIDENCE-WAVE-001-v0.1.json"
)
REUSE_PACK = (
    ENGINE
    / "russian-program"
    / "production-learning-content"
    / "RU-PROG-08-OGE-6.6-COMPONENT-EVIDENCE-WAVE-001-v0.1.json"
)
REUSE_VALIDATOR = HERE / "validate_oge_6_6_component_evidence.py"

OWNER = "school-o-e-after-sibilants-suffix-ending"
REQUIRED_REUSE_IDS = ["oge66-shib-v1", "oge66-shib-v2"]
EXCLUDED_REUSE_IDS = ["oge66-shib-v3"]
NEW_ITEM_ID = "oge67-shib-end-v3"
EXPECTED_PROMPT = (
    "Почему в творительном падеже пишется «плащом», но «овощем»? "
    "Объясни выбор О/Е после шипящей именно в окончании."
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def validate() -> dict[str, Any]:
    route = load(ROUTE)
    pack = load(PACK)
    reuse_pack = load(REUSE_PACK)
    reuse_validation = runpy.run_path(str(REUSE_VALIDATOR))["validate"]()

    if OWNER not in (route.get("exact_owner_refs") or []):
        raise ValueError("wave owner is not in exact OGE 6.7 route frontier")
    if (route.get("mastery_boundary") or {}).get("route_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("route mastery guard weakened")

    if pack.get("status") != "CURRENT_LAUNCH_OGE_6_7_COMPONENT_EVIDENCE_WAVE_001_NO_OBJECT_ADMISSION":
        raise ValueError("unexpected evidence-wave status")
    if pack.get("subject") != "russian" or pack.get("module_id") != "RU-PROG-08":
        raise ValueError("unexpected subject/module")
    target = pack.get("target") or {}
    if target != {
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "document_id": "OGE_COD",
        "content_code": "6.7",
        "requirement_id": "RSK-OGE_COD-6-7-P025",
        "admission_unit_id": "RAU-2668e140328e4edee952",
    }:
        raise ValueError("OGE 6.7 evidence target drift")

    policy = pack.get("evidence_policy") or {}
    required_policy = {
        "reuse_first": True,
        "new_semantic_identity_created": False,
        "exact_owner_frontier_may_change_here": False,
        "each_item_must_reference_exactly_one_school_semantic": True,
        "component_specific_independent_evidence_required": True,
        "route_attempt_can_emit_exact_component_mastery": False,
        "evidence_readiness_is_object_acceptance": False,
        "cross_route_reuse_may_complete_an_owner_only_when_route_scoped": True,
    }
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            raise ValueError(f"evidence policy drift: {key}")

    reuse_summary = reuse_validation.get("summary") or {}
    if reuse_summary.get("owners_with_valid_component_evidence") != 10:
        raise ValueError("validated OGE 6.6 reuse pack is incomplete")
    if reuse_summary.get("object_closures") != 0 or reuse_summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("reuse pack admission boundary weakened")
    reuse_rows = {
        str(row.get("canonical_ref")): row
        for row in reuse_pack.get("owner_evidence") or []
        if isinstance(row, dict)
    }
    reuse_owner = reuse_rows.get(OWNER)
    if reuse_owner is None:
        raise ValueError("reuse owner missing")
    reuse_items = {
        str(item.get("id")): item
        for item in reuse_owner.get("independent_verification") or []
        if isinstance(item, dict)
    }
    for item_id in REQUIRED_REUSE_IDS:
        item = reuse_items.get(item_id)
        if item is None or item.get("evidence_mode") != "INDEPENDENT" or item.get("school_semantic_refs") != [OWNER]:
            raise ValueError(f"required ending-specific reuse item invalid: {item_id}")
    if reuse_items["oge66-shib-v1"].get("feedback") != "В ударном окончании после ч пишется о: врачом.":
        raise ValueError("stressed ending reuse content drift")
    if reuse_items["oge66-shib-v2"].get("feedback") != "В безударном окончании после щ пишется е: товарищем.":
        raise ValueError("unstressed ending reuse content drift")
    for item_id in EXCLUDED_REUSE_IDS:
        if item_id not in reuse_items:
            raise ValueError(f"expected excluded same-owner item missing: {item_id}")

    rows = [row for row in pack.get("owner_evidence") or [] if isinstance(row, dict)]
    if len(rows) != 1 or rows[0].get("canonical_ref") != OWNER:
        raise ValueError("wave must contain exactly one owner")
    row = rows[0]
    dependency = row.get("reuse_dependency") or {}
    if dependency.get("required_route_scoped_item_ids") != REQUIRED_REUSE_IDS:
        raise ValueError("route-scoped reuse dependency drift")
    if dependency.get("excluded_same_owner_item_ids") != EXCLUDED_REUSE_IDS:
        raise ValueError("excluded suffix-only reuse dependency drift")

    items = [item for item in row.get("independent_verification") or [] if isinstance(item, dict)]
    if len(items) != 1:
        raise ValueError("wave 001 must contribute exactly one new independent item")
    item = items[0]
    if item.get("id") != NEW_ITEM_ID or item.get("type") != "constructed_response":
        raise ValueError("unexpected completion item identity/type")
    if item.get("evidence_mode") != "INDEPENDENT" or item.get("school_semantic_refs") != [OWNER]:
        raise ValueError("completion item is not exact single-owner independent evidence")
    if item.get("prompt") != EXPECTED_PROMPT:
        raise ValueError("completion item prompt drift")
    scoring = item.get("scoring") or {}
    if scoring.get("max_points") != 2 or len(scoring.get("criteria") or []) != 2:
        raise ValueError("constructed-response scoring must remain two substantive points")
    answer = str(item.get("answer_outline") or "")
    if "ударением" not in answer or "без ударения" not in answer or "оконч" not in answer:
        raise ValueError("completion answer lost ending/stress boundary")

    summary = pack.get("summary") or {}
    if summary != {
        "owners_with_new_evidence": 1,
        "new_independent_items": 1,
        "owner_completed_only_with_validated_route_scoped_reuse": True,
        "semantic_admissions": 0,
        "object_closures": 0,
        "requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise ValueError("evidence-wave summary drift")

    copyright_guard = pack.get("copyright_guard") or {}
    if copyright_guard.get("official_source_passages_copied") != 0:
        raise ValueError("official source prose copied")
    if copyright_guard.get("commercial_textbook_bytes") != 0 or copyright_guard.get("commercial_textbook_prose_copied") != 0:
        raise ValueError("commercial textbook content copied")
    if copyright_guard.get("learner_prompts_examples_feedback") != "ORIGINAL_EKSAMIO":
        raise ValueError("learner-facing originality guard missing")

    safety = pack.get("safety") or {}
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
        raise ValueError("production safety guard drift")

    result = {
        "status": "COMPLETE",
        "owner": OWNER,
        "validated_reused_route_scoped_items": 2,
        "validated_new_route_scoped_items": 1,
        "combined_exact_items_for_owner": 3,
        "object_closures": 0,
        "false_exact_mastery_admissions": 0,
        "learner_audio_persistence": 0,
    }
    result["normalized_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def main() -> int:
    result = validate()
    print("OGE_6_7_COMPONENT_EVIDENCE_WAVE_001=PASS")
    print(f"OWNER={result['owner']}")
    print(f"VALIDATED_REUSED_ROUTE_SCOPED_ITEMS={result['validated_reused_route_scoped_items']}")
    print(f"VALIDATED_NEW_ROUTE_SCOPED_ITEMS={result['validated_new_route_scoped_items']}")
    print(f"COMBINED_EXACT_ITEMS_FOR_OWNER={result['combined_exact_items_for_owner']}")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
