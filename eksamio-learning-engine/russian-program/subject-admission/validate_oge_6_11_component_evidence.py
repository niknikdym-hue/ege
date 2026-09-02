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
CONTENT = ENGINE / "russian-program" / "production-learning-content" / "RU-PROG-08-OGE-6.11-COMPONENT-EVIDENCE-WAVE-001-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
OWNER_REVIEW = HERE / "build_oge_6_11_service_words_exact_owner_resolution.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"

EXPECTED_STATUS = "CURRENT_LAUNCH_OGE_6_11_COMPONENT_EVIDENCE_CANDIDATE_NO_OBJECT_ADMISSION"
EXPECTED_TARGET = {
    "source_id": "FIPI-OGE-RU-2026-FINAL",
    "document_id": "OGE_COD",
    "content_code": "6.11",
}
EXPECTED_OWNERS = [
    "school-conjunction-solid-separate-spelling-base",
    "school-nonnegative-particle-separate-hyphen-spelling-base",
    "school-preposition-solid-hyphen-separate-base",
]
EXPECTED_LABELS = {
    "school-conjunction-solid-separate-spelling-base": "Союзы и союзные сочетания: слитное или раздельное написание и омонимическая граница",
    "school-nonnegative-particle-separate-hyphen-spelling-base": "Неотрицательные частицы: раздельное и дефисное написание",
    "school-preposition-solid-hyphen-separate-base": "Предлоги: слитное, дефисное и раздельное написание; производный предлог vs свободное сочетание",
}


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object: {path}")
    return data


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def resolve_target() -> dict[str, Any]:
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()

    packet_matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
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
                packet_matches.append((group, req))
    if len(packet_matches) != 1:
        raise ValueError(f"expected one exact OGE_COD 6.11 requirement, got {len(packet_matches)}")
    group, requirement = packet_matches[0]
    requirement_id = str(requirement.get("requirement_id") or "")
    if not requirement_id.startswith("RSK-"):
        raise ValueError("invalid resolved 6.11 requirement id")

    accounting_matches = [
        row
        for row in accounting.get("dispositions") or []
        if isinstance(row, dict)
        and any(
            isinstance(member, dict) and str(member.get("requirement_id")) == requirement_id
            for member in row.get("members") or []
        )
    ]
    if len(accounting_matches) != 1:
        raise ValueError("OGE 6.11 requirement must map to exactly one accounting unit")
    accounting_row = accounting_matches[0]
    if len(accounting_row.get("members") or []) != 1:
        raise ValueError("OGE 6.11 accounting unit must remain single-member before component acceptance")
    if accounting_row.get("disposition") != "PARTIAL_OR_COMPOSITE":
        raise ValueError("OGE 6.11 pre-acceptance disposition drift")
    if accounting_row.get("semantic_identity_ref") is not None:
        raise ValueError("OGE 6.11 must not already carry a singular semantic identity")
    admission_unit_id = str(accounting_row.get("admission_unit_id") or "")
    if not admission_unit_id.startswith("RAU-"):
        raise ValueError("invalid resolved 6.11 admission unit id")

    return {
        "requirement_id": requirement_id,
        "admission_unit_id": admission_unit_id,
        "source_locator": str(requirement.get("source_locator") or ""),
        "packet_group": str(group.get("group_id") or ""),
        "normalized_meaning": str(accounting_row.get("normalized_meaning") or ""),
        "modules": list(accounting_row.get("modules") or []),
        "routes": list(accounting_row.get("routes") or []),
        "current_disposition": str(accounting_row.get("disposition") or ""),
    }


def validate() -> dict[str, Any]:
    content = load(CONTENT)
    inventory = load(INVENTORY)
    resolution = runpy.run_path(str(OWNER_REVIEW))["build_resolution"]()
    resolved_target = resolve_target()

    if content.get("schema_version") != "0.1.0":
        raise ValueError("unexpected 6.11 evidence schema")
    if content.get("status") != EXPECTED_STATUS:
        raise ValueError("6.11 evidence pack must remain no-object-admission candidate")
    if content.get("module_id") != "RU-PROG-08":
        raise ValueError("OGE 6.11 evidence must stay in RU-PROG-08")
    if content.get("target") != EXPECTED_TARGET:
        raise ValueError("OGE 6.11 source target drift")

    if resolution.get("status") != "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_EVIDENCE_REQUIRED":
        raise ValueError("6.11 exact owner resolution is not accepted evidence-required frontier")
    owner_resolution = resolution.get("exact_owner_resolution") or {}
    if owner_resolution.get("exact_current_canonical_owners") != EXPECTED_OWNERS:
        raise ValueError("6.11 exact owner set drift")
    if owner_resolution.get("exact_owner_count") != 3:
        raise ValueError("6.11 exact owner count drift")
    if owner_resolution.get("unresolved_owner_candidates") != 0 or owner_resolution.get("unresolved_placeholders") != 0:
        raise ValueError("6.11 exact owner resolution still has unresolved truth")
    if owner_resolution.get("new_school_identities_required") != 0:
        raise ValueError("6.11 evidence must not create school identities")
    if owner_resolution.get("current_route_supersession_required") is not False:
        raise ValueError("6.11 route supersession must remain unnecessary")
    if owner_resolution.get("current_inventory_route_already_matches_exact_owner_set") is not True:
        raise ValueError("6.11 current route no longer matches exact owner set")
    if owner_resolution.get("evidence_gate_required_before_object_acceptance") is not True:
        raise ValueError("6.11 evidence gate boundary weakened")
    resolution_safety = resolution.get("safety") or {}
    if resolution_safety.get("semantic_admissions") != 0 or resolution_safety.get("object_closures") != 0:
        raise ValueError("6.11 owner resolution already claims forbidden admission")
    if resolution_safety.get("false_exact_mastery") != 0 or resolution_safety.get("learner_audio_persistence") != 0:
        raise ValueError("6.11 owner resolution safety drift")

    objects = [row for row in inventory.get("objects") or [] if isinstance(row, dict)]
    canonical_rows = {
        str(row.get("source_id")): row
        for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and row.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
        and row.get("review_status") == "reviewed"
    }
    for owner in EXPECTED_OWNERS:
        row = canonical_rows.get(owner)
        if row is None:
            raise ValueError(f"owner is not a current reviewed canonical identity: {owner}")
        if row.get("current_semantic_refs") != [owner]:
            raise ValueError(f"canonical self-ref drift: {owner}")
        if row.get("observed_label") != EXPECTED_LABELS[owner]:
            raise ValueError(f"canonical label drift: {owner}")

    exact_inventory_items: dict[str, list[str]] = {owner: [] for owner in EXPECTED_OWNERS}
    for row in objects:
        if row.get("source_system") not in {"trainer_item", "practice_item"}:
            continue
        if row.get("authority_status") != "current" or row.get("review_status") not in {"source_verified", "reviewed"}:
            continue
        refs = [str(ref) for ref in row.get("current_semantic_refs") or []]
        for owner in EXPECTED_OWNERS:
            if refs == [owner]:
                exact_inventory_items[owner].append(str(row.get("source_id") or ""))
    existing_exact_total = sum(len(ids) for ids in exact_inventory_items.values())
    if existing_exact_total != 0:
        raise ValueError(
            "reuse-first violation: current exact single-owner trainer/practice evidence now exists; review it before materializing duplicate 6.11 evidence: "
            + json.dumps(exact_inventory_items, ensure_ascii=False, sort_keys=True)
        )

    required_policy = {
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
    if content.get("evidence_policy") != required_policy:
        raise ValueError("6.11 evidence policy drift")

    rows = content.get("owner_evidence") or []
    if len(rows) != 3:
        raise ValueError("6.11 evidence pack must contain exactly three owner rows")
    refs = [str(row.get("canonical_ref")) for row in rows if isinstance(row, dict)]
    if refs != EXPECTED_OWNERS or len(set(refs)) != 3:
        raise ValueError("6.11 evidence owner order/set must equal exact owner frontier")

    item_ids: set[str] = set()
    selected_total = 0
    constructed_total = 0
    per_owner: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("6.11 owner row is not object")
        owner = str(row.get("canonical_ref"))
        if row.get("title_ru") != EXPECTED_LABELS[owner]:
            raise ValueError(f"6.11 owner title drift: {owner}")
        if row.get("evidence_status") != "CURRENT_LAUNCH_ORIGINAL_EKSAMIO_COMPONENT_EVIDENCE":
            raise ValueError(f"6.11 owner evidence status drift: {owner}")
        boundary = row.get("semantic_boundary")
        if not isinstance(boundary, str) or len(boundary.strip()) < 80:
            raise ValueError(f"6.11 owner boundary too weak: {owner}")
        if row.get("mastery_guard") != {
            "minimum_independent_items_required": 3,
            "component_specific_only": True,
            "generic_oge_route_result_can_emit_exact_mastery": False,
            "assisted_attempt_can_count_as_independent_evidence": False,
        }:
            raise ValueError(f"6.11 mastery guard drift: {owner}")

        evidence = row.get("independent_verification") or []
        if len(evidence) != 3:
            raise ValueError(f"expected exactly three 6.11 independent items: {owner}")
        kinds = [str(item.get("type")) for item in evidence if isinstance(item, dict)]
        if kinds.count("single_choice") != 2 or kinds.count("constructed_response") != 1:
            raise ValueError(f"6.11 owner must have 2 selected + 1 constructed item: {owner}")

        for item in evidence:
            if not isinstance(item, dict):
                raise ValueError(f"non-object 6.11 evidence item: {owner}")
            item_id = str(item.get("id") or "")
            if not item_id or item_id in item_ids:
                raise ValueError(f"missing/duplicate 6.11 item id: {item_id}")
            item_ids.add(item_id)
            if item.get("evidence_mode") != "INDEPENDENT":
                raise ValueError(f"non-independent 6.11 evidence item: {item_id}")
            if item.get("school_semantic_refs") != [owner]:
                raise ValueError(f"mixed or wrong 6.11 semantic refs: {item_id}")
            prompt = item.get("prompt")
            if not isinstance(prompt, str) or len(prompt.strip()) < 20:
                raise ValueError(f"weak 6.11 prompt: {item_id}")
            kind = item.get("type")
            if kind == "single_choice":
                selected_total += 1
                options = item.get("options") or []
                idx = item.get("correct_option_index")
                if len(options) != 3 or not isinstance(idx, int) or not 0 <= idx < 3:
                    raise ValueError(f"invalid 6.11 single-choice evidence: {item_id}")
                if len(set(str(v) for v in options)) != 3:
                    raise ValueError(f"duplicate 6.11 choices: {item_id}")
                if not isinstance(item.get("feedback"), str) or len(item["feedback"].strip()) < 20:
                    raise ValueError(f"missing 6.11 feedback: {item_id}")
            elif kind == "constructed_response":
                constructed_total += 1
                scoring = item.get("scoring") or {}
                if not isinstance(scoring.get("max_points"), int) or scoring["max_points"] < 2:
                    raise ValueError(f"constructed 6.11 score too weak: {item_id}")
                criteria = scoring.get("criteria") or []
                if len(criteria) < 2 or any(not isinstance(c, str) or len(c.strip()) < 20 for c in criteria):
                    raise ValueError(f"constructed 6.11 criteria too weak: {item_id}")
                if not isinstance(item.get("answer_outline"), str) or len(item["answer_outline"].strip()) < 30:
                    raise ValueError(f"constructed 6.11 answer outline missing: {item_id}")
            else:
                raise ValueError(f"unsupported 6.11 evidence type: {kind}")
        per_owner[owner] = len(evidence)

    if selected_total != 6 or constructed_total != 3 or len(item_ids) != 9:
        raise ValueError("6.11 evidence item arithmetic drift")

    guard = content.get("copyright_guard") or {}
    if guard.get("official_source_passages_copied") != 0:
        raise ValueError("official source exercise prose copied into 6.11 evidence")
    if guard.get("commercial_textbook_bytes") != 0 or guard.get("commercial_textbook_prose_copied") != 0:
        raise ValueError("commercial textbook material present in 6.11 evidence")
    if guard.get("learner_prompts_examples_feedback") != "ORIGINAL_EKSAMIO":
        raise ValueError("6.11 learner evidence is not declared original Eksamio")

    provenance = content.get("source_provenance") or []
    refs_seen = {str(row.get("ref")) for row in provenance if isinstance(row, dict)}
    required_refs = {
        "../../255-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-D-O36-O45-v0.1.json",
        "../subject-admission/build_oge_6_11_service_words_exact_owner_resolution.py",
        "../../273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json",
        "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf",
    }
    if not required_refs.issubset(refs_seen):
        raise ValueError("missing exact 6.11 evidence provenance")

    if content.get("summary") != {
        "exact_owner_frontier": 3,
        "owners_with_materialized_component_evidence": 3,
        "independent_items_total": 9,
        "semantic_admissions": 0,
        "object_closures": 0,
        "requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise ValueError("6.11 evidence summary drift")

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
    if content.get("safety") != expected_safety:
        raise ValueError("6.11 safety boundary drift")

    result = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_OGE_6_11_COMPONENT_EVIDENCE_MATERIALIZED_NO_OBJECT_ADMISSION",
        "target": {
            **EXPECTED_TARGET,
            **resolved_target,
        },
        "exact_owner_refs": EXPECTED_OWNERS,
        "reuse_first_inventory_audit": {
            "existing_exact_current_trainer_or_practice_items": 0,
            "mixed_or_route_scoped_items_counted": 0,
            "materialization_reason": "NO_CURRENT_SOURCE_VERIFIED_SINGLE_OWNER_TRAINER_OR_PRACTICE_EVIDENCE",
        },
        "summary": {
            "exact_owner_frontier": 3,
            "owners_with_valid_component_evidence": len(per_owner),
            "independent_items_total": len(item_ids),
            "minimum_items_per_owner": min(per_owner.values()),
            "selected_response_items": selected_total,
            "constructed_response_items": constructed_total,
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
    print("OGE_6_11_COMPONENT_EVIDENCE=PASS")
    print(f"REQUIREMENT_ID={result['target']['requirement_id']}")
    print(f"ADMISSION_UNIT_ID={result['target']['admission_unit_id']}")
    print(f"EXACT_OWNER_FRONTIER={s['exact_owner_frontier']}")
    print(f"OWNERS_WITH_VALID_COMPONENT_EVIDENCE={s['owners_with_valid_component_evidence']}")
    print(f"INDEPENDENT_ITEMS_TOTAL={s['independent_items_total']}")
    print(f"MINIMUM_ITEMS_PER_OWNER={s['minimum_items_per_owner']}")
    print(f"SELECTED_RESPONSE_ITEMS={s['selected_response_items']}")
    print(f"CONSTRUCTED_RESPONSE_ITEMS={s['constructed_response_items']}")
    print("EXISTING_EXACT_INVENTORY_ITEMS=0")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
