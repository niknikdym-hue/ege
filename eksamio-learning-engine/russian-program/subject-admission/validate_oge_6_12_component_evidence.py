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
CONTENT = ENGINE / "russian-program" / "production-learning-content" / "RU-PROG-08-OGE-6.12-COMPONENT-EVIDENCE-WAVE-001-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
CAPITALIZATION = ENGINE / "250-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A4-CAPITALIZATION-v0.1.json"
ROUTE = ENGINE / "282-RUSSIAN-FIPI-2026-OGE-6.12-CURRENT-ROUTE-SUPERSESSION-v0.1.json"
OWNER_REVIEW = HERE / "build_oge_6_12_proper_names_exact_owner_resolution.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"

EXPECTED_STATUS = "CURRENT_LAUNCH_OGE_6_12_COMPONENT_EVIDENCE_CANDIDATE_NO_OBJECT_ADMISSION"
EXPECTED_TARGET = {
    "source_id": "FIPI-OGE-RU-2026-FINAL",
    "document_id": "OGE_COD",
    "content_code": "6.12",
}
EXPECTED_OWNERS = [
    "school-capitalization-astronomical-names",
    "school-capitalization-awards-orders-medals",
    "school-capitalization-documents-works-media-objects",
    "school-capitalization-geographic-administrative-names",
    "school-capitalization-historical-calendar-public-events",
    "school-capitalization-organizations-authorities-institutions",
    "school-capitalization-person-animal-name-and-derivatives",
    "school-capitalization-religious-names",
    "school-capitalization-trademarks-breeds-varieties-products",
]
REJECTED_NONOWNERS = {
    "school-capitalization-conditional-special-proper-names",
    "school-capitalization-positions-titles",
    "school-capitalization-sentence-text-start",
    "school-abbreviations-capitalization-formation",
}
EXPECTED_LABELS = {
    "school-capitalization-astronomical-names": "Астрономические названия: собственное имя или нарицательное/обычное употребление",
    "school-capitalization-awards-orders-medals": "Ордена, медали, награды, знаки отличия и премии: оформление компонентов названия",
    "school-capitalization-documents-works-media-objects": "Документы, памятники, предметы, произведения искусства, издания и информационные названия",
    "school-capitalization-geographic-administrative-names": "Географические и административно-территориальные названия и производные от них слова",
    "school-capitalization-historical-calendar-public-events": "Исторические эпохи и события, календарные периоды, праздники и общественные мероприятия",
    "school-capitalization-organizations-authorities-institutions": "Органы власти, учреждения, организации, общества, партии, предприятия: прописные по структуре официального названия",
    "school-capitalization-person-animal-name-and-derivatives": "Имена людей, клички животных, мифологические имена и производные от индивидуальных названий",
    "school-capitalization-religious-names": "Названия, связанные с религией: имена, священные тексты, праздники, учреждения и употребления",
    "school-capitalization-trademarks-breeds-varieties-products": "Товарные знаки, марки изделий, породы, виды и сорта: собственное название или нарицательное обозначение",
}


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object: {path}")
    return data


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
        raise ValueError(f"expected one exact OGE_COD 6.12 requirement, got {len(matches)}")
    group, requirement = matches[0]
    requirement_id = str(requirement.get("requirement_id") or "")
    if not requirement_id.startswith("RSK-"):
        raise ValueError("invalid resolved 6.12 requirement id")
    return {
        "requirement_id": requirement_id,
        "source_locator": str(requirement.get("source_locator") or ""),
        "packet_group": str(group.get("group_id") or ""),
    }


def validate() -> dict[str, Any]:
    content = load(CONTENT)
    inventory = load(INVENTORY)
    capitalization = load(CAPITALIZATION)
    route = load(ROUTE)
    resolution = runpy.run_path(str(OWNER_REVIEW))["build_resolution"]()
    source_target = prove_source_target()

    if content.get("schema_version") != "0.1.0":
        raise ValueError("unexpected 6.12 evidence schema")
    if content.get("status") != EXPECTED_STATUS:
        raise ValueError("6.12 evidence pack must remain no-object-admission candidate")
    if content.get("module_id") != "RU-PROG-08":
        raise ValueError("OGE 6.12 evidence must stay in RU-PROG-08")
    if content.get("target") != EXPECTED_TARGET:
        raise ValueError("OGE 6.12 source target drift")

    if resolution.get("status") != "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_ROUTE_SUPERSESSION_REQUIRED":
        raise ValueError("6.12 exact owner resolution status drift")
    owner_resolution = resolution.get("exact_owner_resolution") or {}
    if owner_resolution.get("exact_current_canonical_owners") != EXPECTED_OWNERS:
        raise ValueError("6.12 exact owner set drift")
    if owner_resolution.get("exact_owner_count") != 9:
        raise ValueError("6.12 exact owner count drift")
    if owner_resolution.get("rejected_frontier_candidate_count") != 2:
        raise ValueError("6.12 rejected frontier count drift")
    rejected_from_resolution = {
        str(row.get("candidate"))
        for row in owner_resolution.get("rejected_frontier_candidates") or []
        if isinstance(row, dict)
    }
    if rejected_from_resolution != {
        "school-capitalization-conditional-special-proper-names",
        "school-capitalization-positions-titles",
    }:
        raise ValueError("6.12 rejected exact-owner partition drift")
    if owner_resolution.get("unresolved_owner_candidates") != 0 or owner_resolution.get("unresolved_placeholders") != 0:
        raise ValueError("6.12 exact owner resolution still has unresolved truth")
    if owner_resolution.get("new_school_identities_required") != 0:
        raise ValueError("6.12 evidence must not create school identities")
    if owner_resolution.get("evidence_gate_required_before_object_acceptance") is not True:
        raise ValueError("6.12 evidence gate boundary weakened")

    if route.get("status") != "CURRENT_OGE_2026_6_12_ROUTE_SUPERSESSION_EXACT_OWNER_FRONTIER_NO_OBJECT_ADMISSION":
        raise ValueError("6.12 route supersession authority status drift")
    if route.get("position") != "6.12":
        raise ValueError("6.12 route position drift")
    if route.get("exact_owner_refs") != EXPECTED_OWNERS:
        raise ValueError("6.12 route exact owner set/order drift")
    account = route.get("owner_accounting") or {}
    if account.get("official_fipi_objects") != 1 or account.get("official_explicit_subbranches") != 0:
        raise ValueError("6.12 official object boundary drift")
    if account.get("owner_count") != 9 or account.get("rejected_frontier_candidates") != 2:
        raise ValueError("6.12 route owner accounting drift")
    if account.get("unresolved_owners") != 0 or account.get("newly_materialized_current_canonical") != 0:
        raise ValueError("6.12 route contains unresolved/new identity truth")
    mastery = route.get("mastery_boundary") or {}
    if mastery.get("route_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("6.12 generic route can emit exact mastery")
    if mastery.get("component_specific_independent_evidence_required") is not True:
        raise ValueError("6.12 component evidence requirement weakened")
    effect = route.get("admission_effect") or {}
    if effect.get("semantic_admissions") != 0 or effect.get("object_closures") != 0:
        raise ValueError("6.12 route already claims forbidden admission")
    if effect.get("false_exact_mastery_admissions") != 0:
        raise ValueError("6.12 route false exact mastery drift")

    units = {
        str(row.get("unit_id")): row
        for row in capitalization.get("canonical_units") or []
        if isinstance(row, dict) and row.get("unit_id")
    }
    if len(units) != 13:
        raise ValueError("capitalization canonical unit count drift")
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
        unit = units.get(owner)
        row = canonical_rows.get(owner)
        if unit is None or row is None:
            raise ValueError(f"6.12 owner lacks current canonical authority: {owner}")
        if unit.get("canonical_label") != EXPECTED_LABELS[owner]:
            raise ValueError(f"6.12 capitalization label drift: {owner}")
        if row.get("observed_label") != EXPECTED_LABELS[owner]:
            raise ValueError(f"6.12 inventory label drift: {owner}")
        if row.get("current_semantic_refs") != [owner]:
            raise ValueError(f"6.12 canonical self-ref drift: {owner}")

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
            "reuse-first violation: exact single-owner inventory evidence now exists; review it before duplicate 6.12 materialization: "
            + json.dumps(exact_inventory_items, ensure_ascii=False, sort_keys=True)
        )

    audit = content.get("reuse_audit") or {}
    if audit.get("source_systems_checked") != ["trainer_item", "practice_item"]:
        raise ValueError("6.12 reuse audit source systems drift")
    if audit.get("existing_exact_single_owner_items_total") != existing_exact_total:
        raise ValueError("6.12 reuse audit total does not match current inventory")
    audit_rows = audit.get("per_owner") or []
    if [str(row.get("canonical_ref")) for row in audit_rows if isinstance(row, dict)] != EXPECTED_OWNERS:
        raise ValueError("6.12 reuse audit owner order/set drift")
    for row in audit_rows:
        if not isinstance(row, dict):
            raise ValueError("6.12 reuse audit row must be object")
        owner = str(row.get("canonical_ref"))
        if row.get("existing_exact_item_refs") != exact_inventory_items[owner]:
            raise ValueError(f"6.12 reuse audit item refs drift: {owner}")
        if row.get("materialized_new_items") != 3:
            raise ValueError(f"6.12 materialized count drift: {owner}")

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
        raise ValueError("6.12 evidence policy drift")

    rows = content.get("owner_evidence") or []
    if len(rows) != 9:
        raise ValueError("6.12 evidence pack must contain exactly nine owner rows")
    refs = [str(row.get("canonical_ref")) for row in rows if isinstance(row, dict)]
    if refs != EXPECTED_OWNERS or len(set(refs)) != 9:
        raise ValueError("6.12 evidence owner order/set must equal exact owner frontier")
    if set(refs) & REJECTED_NONOWNERS:
        raise ValueError("6.12 evidence imported a rejected/nonowner identity")

    item_ids: set[str] = set()
    selected_total = 0
    constructed_total = 0
    per_owner: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("6.12 owner row is not object")
        owner = str(row.get("canonical_ref"))
        if row.get("title_ru") != EXPECTED_LABELS[owner]:
            raise ValueError(f"6.12 owner title drift: {owner}")
        if row.get("evidence_status") != "CURRENT_LAUNCH_ORIGINAL_EKSAMIO_COMPONENT_EVIDENCE":
            raise ValueError(f"6.12 owner evidence status drift: {owner}")
        boundary = row.get("semantic_boundary")
        if not isinstance(boundary, str) or len(boundary.strip()) < 80:
            raise ValueError(f"6.12 owner boundary too weak: {owner}")
        if row.get("mastery_guard") != {
            "minimum_independent_items_required": 3,
            "component_specific_only": True,
            "generic_oge_route_result_can_emit_exact_mastery": False,
            "assisted_attempt_can_count_as_independent_evidence": False,
        }:
            raise ValueError(f"6.12 mastery guard drift: {owner}")

        evidence = row.get("independent_verification") or []
        if len(evidence) != 3:
            raise ValueError(f"expected exactly three 6.12 independent items: {owner}")
        kinds = [str(item.get("type")) for item in evidence if isinstance(item, dict)]
        if kinds.count("single_choice") != 2 or kinds.count("constructed_response") != 1:
            raise ValueError(f"6.12 owner must have 2 selected + 1 constructed item: {owner}")

        for item in evidence:
            if not isinstance(item, dict):
                raise ValueError(f"non-object 6.12 evidence item: {owner}")
            item_id = str(item.get("id") or "")
            if not item_id or item_id in item_ids:
                raise ValueError(f"missing/duplicate 6.12 item id: {item_id}")
            item_ids.add(item_id)
            if item.get("evidence_mode") != "INDEPENDENT":
                raise ValueError(f"non-independent 6.12 evidence item: {item_id}")
            if item.get("school_semantic_refs") != [owner]:
                raise ValueError(f"mixed or wrong 6.12 semantic refs: {item_id}")
            prompt = item.get("prompt")
            if not isinstance(prompt, str) or len(prompt.strip()) < 20:
                raise ValueError(f"weak 6.12 prompt: {item_id}")
            kind = item.get("type")
            if kind == "single_choice":
                selected_total += 1
                options = item.get("options") or []
                idx = item.get("correct_option_index")
                if len(options) != 3 or not isinstance(idx, int) or not 0 <= idx < 3:
                    raise ValueError(f"invalid 6.12 single-choice evidence: {item_id}")
                if len(set(str(value) for value in options)) != 3:
                    raise ValueError(f"duplicate 6.12 choices: {item_id}")
                if not isinstance(item.get("feedback"), str) or len(item["feedback"].strip()) < 20:
                    raise ValueError(f"missing 6.12 feedback: {item_id}")
            elif kind == "constructed_response":
                constructed_total += 1
                scoring = item.get("scoring") or {}
                if not isinstance(scoring.get("max_points"), int) or scoring["max_points"] < 2:
                    raise ValueError(f"constructed 6.12 score too weak: {item_id}")
                criteria = scoring.get("criteria") or []
                if len(criteria) < 2 or any(not isinstance(c, str) or len(c.strip()) < 20 for c in criteria):
                    raise ValueError(f"constructed 6.12 criteria too weak: {item_id}")
                if not isinstance(item.get("answer_outline"), str) or len(item["answer_outline"].strip()) < 30:
                    raise ValueError(f"constructed 6.12 answer outline missing: {item_id}")
            else:
                raise ValueError(f"unsupported 6.12 evidence type: {kind}")
        per_owner[owner] = len(evidence)

    if selected_total != 18 or constructed_total != 9 or len(item_ids) != 27:
        raise ValueError("6.12 evidence item arithmetic drift")

    guard = content.get("copyright_guard") or {}
    if guard.get("official_source_passages_copied") != 0:
        raise ValueError("official source exercise prose copied into 6.12 evidence")
    if guard.get("commercial_textbook_bytes") != 0 or guard.get("commercial_textbook_prose_copied") != 0:
        raise ValueError("commercial textbook material present in 6.12 evidence")
    if guard.get("learner_prompts_examples_feedback") != "ORIGINAL_EKSAMIO":
        raise ValueError("6.12 learner evidence is not declared original Eksamio")

    provenance = content.get("source_provenance") or []
    refs_seen = {str(row.get("ref")) for row in provenance if isinstance(row, dict)}
    required_refs = {
        "../../250-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A4-CAPITALIZATION-v0.1.json",
        "../../282-RUSSIAN-FIPI-2026-OGE-6.12-CURRENT-ROUTE-SUPERSESSION-v0.1.json",
        "../subject-admission/build_oge_6_12_proper_names_exact_owner_resolution.py",
        "../../273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json",
        "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf",
    }
    if not required_refs.issubset(refs_seen):
        raise ValueError("6.12 evidence provenance incomplete")

    summary = content.get("summary") or {}
    if summary != {
        "exact_owner_frontier": 9,
        "owners_with_materialized_component_evidence": 9,
        "existing_exact_inventory_items_reused": 0,
        "materialized_new_items": 27,
        "independent_items_total": 27,
        "semantic_admissions": 0,
        "object_closures": 0,
        "requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise ValueError("6.12 evidence summary drift")

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
        raise ValueError("6.12 safety boundary drift")

    result = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_OGE_6_12_COMPONENT_EVIDENCE_MATERIALIZED_NO_OBJECT_ADMISSION",
        "target": EXPECTED_TARGET,
        "resolved_source_target": source_target,
        "exact_owner_refs": EXPECTED_OWNERS,
        "summary": {
            "exact_owner_frontier": 9,
            "owners_with_valid_component_evidence": len(per_owner),
            "existing_exact_inventory_items": existing_exact_total,
            "materialized_new_items": len(item_ids),
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
    print("OGE_6_12_COMPONENT_EVIDENCE=PASS")
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
    print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
