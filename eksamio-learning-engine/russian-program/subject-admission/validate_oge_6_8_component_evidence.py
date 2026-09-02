#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
CONTENT = ENGINE / "russian-program" / "production-learning-content" / "RU-PROG-08-OGE-6.8-COMPONENT-EVIDENCE-WAVE-001-v0.1.json"
ROUTE = ENGINE / "280-RUSSIAN-FIPI-2026-OGE-6.8-CURRENT-ROUTE-SUPERSESSION-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

EXPECTED_STATUS = "CURRENT_LAUNCH_OGE_6_8_COMPONENT_EVIDENCE_CANDIDATE_NO_OBJECT_ADMISSION"
EXPECTED_TARGET = {
    "source_id": "FIPI-OGE-RU-2026-FINAL",
    "document_id": "OGE_COD",
    "content_code": "6.8",
    "admission_unit_id": "RAU-201ed5b7e687237a0bae",
    "requirement_id": "RSK-OGE_COD-6-8-P025",
}
EXPECTED_OWNERS = {
    "school-adverb-solid-hyphen-separate-system",
    "school-compound-adjective-solid-hyphen-separate-system",
    "school-conjunction-solid-separate-spelling-base",
    "school-nonnegative-particle-separate-hyphen-spelling-base",
    "school-numeral-orthography-base",
    "school-pol-polu-writing-boundary",
    "school-preposition-solid-hyphen-separate-base",
}
EXPECTED_LABELS = {
    "school-adverb-solid-hyphen-separate-system": "Наречия и наречные сочетания: слитно, через дефис или раздельно",
    "school-compound-adjective-solid-hyphen-separate-system": "Сложные прилагательные и сочетания наречие + прилагательное: слитно, через дефис или раздельно",
    "school-conjunction-solid-separate-spelling-base": "Союзы и союзные сочетания: слитное или раздельное написание и омонимическая граница",
    "school-nonnegative-particle-separate-hyphen-spelling-base": "Неотрицательные частицы: раздельное и дефисное написание",
    "school-numeral-orthography-base": "Правописание количественных, порядковых и дробных числительных",
    "school-pol-polu-writing-boundary": "ПОЛ-/ПОЛУ-: слитно, дефис, раздельно и словарные случаи",
    "school-preposition-solid-hyphen-separate-base": "Предлоги: слитное, дефисное и раздельное написание; производный предлог vs свободное сочетание",
}
ABSORBED_HISTORICAL = "school-indefinite-pronouns-hyphen-koe-preposition-boundary"
FORBIDDEN_6_8_NONOWNERS = {
    "school-compound-noun-solid-hyphen-system",
    "school-negative-pronouns-ne-ni-stress-preposition-boundary",
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
        raise ValueError("OGE 6.8 evidence must stay in RU-PROG-08")
    if content.get("target") != EXPECTED_TARGET:
        raise ValueError("OGE 6.8 exact target identity drift")

    route_owners = [str(ref) for ref in route.get("exact_owner_refs") or []]
    if len(route_owners) != 7 or len(set(route_owners)) != 7 or set(route_owners) != EXPECTED_OWNERS:
        raise ValueError("route must expose exactly the seven proven 6.8 owners")
    account = route.get("owner_accounting") or {}
    if account.get("official_fipi_branches") != 9:
        raise ValueError("6.8 official branch count drift")
    if account.get("legacy_family_placeholders") != 0 or account.get("unresolved_owners") != 0:
        raise ValueError("6.8 route contains placeholder or unresolved owner")
    if account.get("newly_materialized_current_canonical") != 0 or account.get("school_reopen_required") != 0:
        raise ValueError("6.8 evidence must reuse current school identities")
    if account.get("absorbed_historical_refs_not_reopened") != [ABSORBED_HISTORICAL]:
        raise ValueError("absorbed pronoun lineage drift")
    if ABSORBED_HISTORICAL in route_owners:
        raise ValueError("absorbed historical pronoun identity reopened")
    if set(route_owners) & FORBIDDEN_6_8_NONOWNERS:
        raise ValueError("6.8 route imported a neighboring-code nonowner")

    mastery = route.get("mastery_boundary") or {}
    if mastery.get("route_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("route mastery boundary weakened")
    if mastery.get("component_specific_independent_evidence_required") is not True:
        raise ValueError("component-specific evidence requirement weakened")
    effect = route.get("admission_effect") or {}
    if effect.get("object_closures") != 0 or effect.get("false_exact_mastery_admissions") != 0:
        raise ValueError("route already claims forbidden acceptance")

    canonical_rows = {
        str(row.get("source_id")): row
        for row in inventory.get("objects") or []
        if isinstance(row, dict)
        and row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and row.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
        and row.get("review_status") == "reviewed"
    }
    for owner in route_owners:
        row = canonical_rows.get(owner)
        if row is None:
            raise ValueError(f"owner is not a current reviewed canonical identity: {owner}")
        if row.get("current_semantic_refs") != [owner]:
            raise ValueError(f"canonical self-ref drift: {owner}")
        if row.get("observed_label") != EXPECTED_LABELS[owner]:
            raise ValueError(f"canonical label drift: {owner}")

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
        "cross_route_reuse_used": False,
    }
    if policy != required_policy:
        raise ValueError("evidence policy drift")

    rows = content.get("owner_evidence") or []
    if len(rows) != 7:
        raise ValueError("evidence pack must contain exactly seven owner rows")
    refs = [str(row.get("canonical_ref")) for row in rows if isinstance(row, dict)]
    if len(refs) != 7 or len(set(refs)) != 7 or set(refs) != set(route_owners):
        raise ValueError("evidence owner set must equal route owner frontier exactly")
    if set(refs) & FORBIDDEN_6_8_NONOWNERS or ABSORBED_HISTORICAL in refs:
        raise ValueError("evidence owner set contains a forbidden or absorbed identity")

    item_ids: set[str] = set()
    per_owner: dict[str, int] = {}
    selected_total = 0
    constructed_total = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("owner row is not object")
        owner = str(row.get("canonical_ref"))
        if row.get("title_ru") != EXPECTED_LABELS[owner]:
            raise ValueError(f"owner title drift: {owner}")
        if row.get("evidence_status") != "CURRENT_LAUNCH_ORIGINAL_EKSAMIO_COMPONENT_EVIDENCE":
            raise ValueError(f"owner evidence status drift: {owner}")
        boundary = row.get("semantic_boundary")
        if not isinstance(boundary, str) or len(boundary.strip()) < 50:
            raise ValueError(f"owner boundary too weak: {owner}")

        guard = row.get("mastery_guard") or {}
        if guard != {
            "minimum_independent_items_required": 3,
            "component_specific_only": True,
            "generic_oge_route_result_can_emit_exact_mastery": False,
            "assisted_attempt_can_count_as_independent_evidence": False,
        }:
            raise ValueError(f"mastery guard drift: {owner}")

        evidence = row.get("independent_verification") or []
        if len(evidence) != 3:
            raise ValueError(f"expected exactly three independent items: {owner}")
        kinds = [str(item.get("type")) for item in evidence if isinstance(item, dict)]
        if kinds.count("single_choice") != 2 or kinds.count("constructed_response") != 1:
            raise ValueError(f"owner must have 2 selected + 1 constructed item: {owner}")

        for item in evidence:
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
            if not isinstance(prompt, str) or len(prompt.strip()) < 20:
                raise ValueError(f"weak prompt: {item_id}")
            kind = item.get("type")
            if kind == "single_choice":
                selected_total += 1
                options = item.get("options") or []
                idx = item.get("correct_option_index")
                if len(options) != 3 or not isinstance(idx, int) or not 0 <= idx < 3:
                    raise ValueError(f"invalid single-choice evidence: {item_id}")
                if len(set(str(v) for v in options)) != 3:
                    raise ValueError(f"duplicate choices: {item_id}")
                if not isinstance(item.get("feedback"), str) or len(item["feedback"].strip()) < 20:
                    raise ValueError(f"missing feedback: {item_id}")
            elif kind == "constructed_response":
                constructed_total += 1
                scoring = item.get("scoring") or {}
                if not isinstance(scoring.get("max_points"), int) or scoring["max_points"] < 2:
                    raise ValueError(f"constructed score too weak: {item_id}")
                criteria = scoring.get("criteria") or []
                if len(criteria) < 2 or any(not isinstance(c, str) or len(c.strip()) < 20 for c in criteria):
                    raise ValueError(f"constructed criteria too weak: {item_id}")
                if not isinstance(item.get("answer_outline"), str) or len(item["answer_outline"].strip()) < 30:
                    raise ValueError(f"constructed answer outline missing: {item_id}")
            else:
                raise ValueError(f"unsupported evidence type: {kind}")
        per_owner[owner] = len(evidence)

    if selected_total != 14 or constructed_total != 7 or len(item_ids) != 21:
        raise ValueError("6.8 evidence item arithmetic drift")

    guard = content.get("copyright_guard") or {}
    if guard.get("official_source_passages_copied") != 0:
        raise ValueError("official source exercise prose copied")
    if guard.get("commercial_textbook_bytes") != 0 or guard.get("commercial_textbook_prose_copied") != 0:
        raise ValueError("commercial textbook material present")
    if guard.get("learner_prompts_examples_feedback") != "ORIGINAL_EKSAMIO":
        raise ValueError("learner evidence is not declared original Eksamio")

    provenance = content.get("source_provenance") or []
    refs_seen = {str(row.get("ref")) for row in provenance if isinstance(row, dict)}
    if "../../280-RUSSIAN-FIPI-2026-OGE-6.8-CURRENT-ROUTE-SUPERSESSION-v0.1.json" not in refs_seen:
        raise ValueError("missing current 6.8 route provenance")
    if "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf" not in refs_seen:
        raise ValueError("missing official FIPI scope provenance")
    if "../../273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json" not in refs_seen:
        raise ValueError("missing canonical inventory provenance")

    summary = content.get("summary") or {}
    if summary != {
        "exact_owner_frontier": 7,
        "owners_with_materialized_component_evidence": 7,
        "independent_items_total": 21,
        "semantic_admissions": 0,
        "object_closures": 0,
        "requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise ValueError("evidence summary drift")

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
        raise ValueError("safety boundary drift")

    result = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_OGE_6_8_COMPONENT_EVIDENCE_MATERIALIZED_NO_OBJECT_ADMISSION",
        "target": EXPECTED_TARGET,
        "exact_owner_refs": route_owners,
        "summary": {
            "exact_owner_frontier": 7,
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
    print("OGE_6_8_COMPONENT_EVIDENCE=PASS")
    print(f"EXACT_OWNER_FRONTIER={s['exact_owner_frontier']}")
    print(f"OWNERS_WITH_VALID_COMPONENT_EVIDENCE={s['owners_with_valid_component_evidence']}")
    print(f"INDEPENDENT_ITEMS_TOTAL={s['independent_items_total']}")
    print(f"MINIMUM_ITEMS_PER_OWNER={s['minimum_items_per_owner']}")
    print(f"SELECTED_RESPONSE_ITEMS={s['selected_response_items']}")
    print(f"CONSTRUCTED_RESPONSE_ITEMS={s['constructed_response_items']}")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
