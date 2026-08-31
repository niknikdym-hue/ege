#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
PACK = ENGINE / "russian-program" / "production-learning-content" / "RU-PROG-08-OGE-6.7-COMPONENT-EVIDENCE-WAVE-003-v0.1.json"
ROUTE = ENGINE / "279-RUSSIAN-FIPI-2026-OGE-6.7-CURRENT-ROUTE-SUPERSESSION-v0.1.json"
WAVE_B = ENGINE / "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25-v0.1.json"
FIPI_REOPEN = ENGINE / "263-RUSSIAN-SCHOOL-FIPI-REOPEN-MATERIALIZATION-v0.1.json"

EXPECTED_OWNERS = [
    "school-noun-case-ending-base",
    "school-noun-case-ending-special-paradigms",
    "school-noun-genitive-plural-ending-system",
    "school-noun-special-suffix-gender-endings",
    "school-proper-name-instrumental-ending-boundary",
]
EXPECTED_ITEM_IDS = {
    "school-noun-case-ending-base": ["oge67-nounbase-v1", "oge67-nounbase-v2", "oge67-nounbase-v3"],
    "school-noun-case-ending-special-paradigms": ["oge67-nounspecial-v1", "oge67-nounspecial-v2", "oge67-nounspecial-v3"],
    "school-noun-genitive-plural-ending-system": ["oge67-noungenpl-v1", "oge67-noungenpl-v2", "oge67-noungenpl-v3"],
    "school-noun-special-suffix-gender-endings": ["oge67-nounsuffixgender-v1", "oge67-nounsuffixgender-v2", "oge67-nounsuffixgender-v3"],
    "school-proper-name-instrumental-ending-boundary": ["oge67-properinstr-v1", "oge67-properinstr-v2", "oge67-properinstr-v3"],
}
EXPECTED_CORRECT_OPTIONS = {
    "oge67-nounbase-v1": "к деревне",
    "oge67-nounbase-v2": "о тетради",
    "oge67-nounspecial-v1": "к Марии",
    "oge67-nounspecial-v2": "в санатории",
    "oge67-noungenpl-v1": "нет сапог",
    "oge67-noungenpl-v2": "много ночей",
    "oge67-nounsuffixgender-v1": "домище",
    "oge67-nounsuffixgender-v2": "ручища",
    "oge67-properinstr-v1": "беседовать с Пушкиным",
    "oge67-properinstr-v2": "теория предложена Дарвином",
}
EXPECTED_CONSTRUCTED_TOKENS = {
    "oge67-nounbase-v3": ["в школе", "на площади", "1-му склонению", "3-му склонению"],
    "oge67-nounspecial-v3": ["мероприятии", "счастье", "-ие", "-ье"],
    "oge67-noungenpl-v3": ["вишен", "деревень", "мягкий знак"],
    "oge67-nounsuffixgender-v3": ["дедушка", "пёрышко", "запевала", "точило", "одушевл"],
    "oge67-properinstr-v3": ["Александровом", "Александровым", "Географическое", "фамилия"],
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def validate() -> dict[str, Any]:
    pack = load(PACK)
    route = load(ROUTE)
    wave_b = load(WAVE_B)
    reopen = load(FIPI_REOPEN)

    if pack.get("status") != "CURRENT_LAUNCH_OGE_6_7_COMPONENT_EVIDENCE_WAVE_003_NO_OBJECT_ADMISSION":
        raise ValueError("unexpected wave 003 status")
    if pack.get("subject") != "russian" or pack.get("module_id") != "RU-PROG-08":
        raise ValueError("unexpected subject/module")
    if pack.get("target") != {
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "document_id": "OGE_COD",
        "content_code": "6.7",
        "requirement_id": "RSK-OGE_COD-6-7-P025",
        "admission_unit_id": "RAU-2668e140328e4edee952",
    }:
        raise ValueError("wave 003 target drift")

    policy = pack.get("evidence_policy") or {}
    required_policy = {
        "reuse_first": True,
        "new_semantic_identity_created": False,
        "exact_owner_frontier_may_change_here": False,
        "each_item_must_reference_exactly_one_school_semantic": True,
        "component_specific_independent_evidence_required": True,
        "minimum_independent_items_per_owner": 3,
        "route_attempt_can_emit_exact_component_mastery": False,
        "evidence_readiness_is_object_acceptance": False,
        "route_scope": "OGE_2026_6_7_ENDINGS_ONLY",
    }
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            raise ValueError(f"wave 003 evidence policy drift: {key}")

    route_owners = [str(ref) for ref in route.get("exact_owner_refs") or []]
    if len(route_owners) != 12 or len(set(route_owners)) != 12:
        raise ValueError("OGE 6.7 exact owner frontier drift")
    if not set(EXPECTED_OWNERS) <= set(route_owners):
        raise ValueError("wave 003 owner escaped exact OGE 6.7 frontier")
    mastery = route.get("mastery_boundary") or {}
    if mastery.get("route_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("route exact-mastery guard weakened")
    if mastery.get("component_specific_independent_evidence_required") is not True:
        raise ValueError("route component-evidence guard weakened")

    o17 = wave_b.get("O17_noun_endings") or {}
    special_rows = {
        str(row.get("unit_id")): row
        for row in o17.get("new_units") or []
        if isinstance(row, dict)
    }
    for owner in EXPECTED_OWNERS[1:]:
        if owner not in special_rows:
            raise ValueError(f"file 252 O17 exact noun-ending owner missing: {owner}")
    if "-ий/-ие/-ия" not in str(special_rows["school-noun-case-ending-special-paradigms"].get("canonical_label") or ""):
        raise ValueError("special noun paradigm boundary drift")
    if "Родительный множественного" not in str(special_rows["school-noun-genitive-plural-ending-system"].get("canonical_label") or ""):
        raise ValueError("genitive-plural boundary drift")
    if "Творительный падеж" not in str(special_rows["school-proper-name-instrumental-ending-boundary"].get("canonical_label") or ""):
        raise ValueError("proper-name instrumental boundary drift")
    if "-ищ-" not in str(special_rows["school-noun-special-suffix-gender-endings"].get("canonical_label") or ""):
        raise ValueError("special suffix/gender ending boundary drift")

    reopen_units = {
        str(row.get("unit_id")): row
        for row in reopen.get("canonical_units") or []
        if isinstance(row, dict)
    }
    noun_base = reopen_units.get("school-noun-case-ending-base")
    if noun_base is None or "OGE-2026-orthography-6.7" not in (noun_base.get("fipi_routes") or []):
        raise ValueError("noun base OGE 6.7 binding missing")
    boundary = str(noun_base.get("decision_model") or "") + " " + str(noun_base.get("canonical_label") or "")
    for token in ("склонение", "падеж"):
        if token not in boundary:
            raise ValueError(f"noun base productive boundary token missing: {token}")

    rows = [row for row in pack.get("owner_evidence") or [] if isinstance(row, dict)]
    by_owner = {str(row.get("canonical_ref")): row for row in rows}
    if sorted(by_owner) != sorted(EXPECTED_OWNERS) or len(rows) != len(by_owner):
        raise ValueError("wave 003 owner set/uniqueness drift")

    seen_ids: set[str] = set()
    item_count = 0
    for owner in EXPECTED_OWNERS:
        row = by_owner[owner]
        if row.get("evidence_status") != "CURRENT_LAUNCH_ORIGINAL_EKSAMIO_COMPONENT_EVIDENCE":
            raise ValueError(f"unexpected owner evidence status: {owner}")
        guard = row.get("mastery_guard") or {}
        if guard != {
            "minimum_independent_items_required": 3,
            "component_specific_only": True,
            "assisted_attempt_can_count_as_independent_evidence": False,
            "generic_oge_route_result_can_emit_exact_mastery": False,
        }:
            raise ValueError(f"mastery guard drift: {owner}")
        items = [item for item in row.get("independent_verification") or [] if isinstance(item, dict)]
        if len(items) != 3:
            raise ValueError(f"owner must have exactly three independent items: {owner}")
        if [str(item.get("id")) for item in items] != EXPECTED_ITEM_IDS[owner]:
            raise ValueError(f"item identity/order drift: {owner}")
        for item in items:
            item_count += 1
            item_id = str(item.get("id"))
            if item_id in seen_ids:
                raise ValueError(f"duplicate evidence item id: {item_id}")
            seen_ids.add(item_id)
            if item.get("evidence_mode") != "INDEPENDENT" or item.get("school_semantic_refs") != [owner]:
                raise ValueError(f"item lost exact single-owner independence: {item_id}")
            if item.get("type") == "single_choice":
                options = item.get("options") or []
                idx = item.get("correct_option_index")
                if not isinstance(idx, int) or idx < 0 or idx >= len(options):
                    raise ValueError(f"invalid single-choice key: {item_id}")
                if options[idx] != EXPECTED_CORRECT_OPTIONS[item_id]:
                    raise ValueError(f"normative keyed form drift: {item_id}")
                if not str(item.get("feedback") or "").strip():
                    raise ValueError(f"missing learner feedback: {item_id}")
            elif item.get("type") == "constructed_response":
                scoring = item.get("scoring") or {}
                if scoring.get("max_points") != 2 or len(scoring.get("criteria") or []) != 2:
                    raise ValueError(f"constructed-response scoring drift: {item_id}")
                answer = str(item.get("answer_outline") or "")
                for token in EXPECTED_CONSTRUCTED_TOKENS[item_id]:
                    if token not in answer:
                        raise ValueError(f"constructed-response normative token missing: {item_id}: {token}")
            else:
                raise ValueError(f"unsupported evidence item type: {item_id}")

    if item_count != 15 or len(seen_ids) != 15:
        raise ValueError("wave 003 exact evidence item denominator drift")
    if pack.get("summary") != {
        "owners_with_new_evidence": 5,
        "new_independent_items": 15,
        "semantic_admissions": 0,
        "object_closures": 0,
        "requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise ValueError("wave 003 summary drift")

    copyright_guard = pack.get("copyright_guard") or {}
    if copyright_guard.get("official_source_passages_copied") != 0:
        raise ValueError("official source prose copied")
    if copyright_guard.get("commercial_textbook_bytes") != 0 or copyright_guard.get("commercial_textbook_prose_copied") != 0:
        raise ValueError("commercial textbook content copied")
    if copyright_guard.get("learner_prompts_examples_feedback") != "ORIGINAL_EKSAMIO":
        raise ValueError("learner originality guard missing")

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
    if pack.get("safety") != expected_safety:
        raise ValueError("production safety guard drift")

    result = {
        "status": "COMPLETE",
        "owners_completed_with_new_component_evidence": len(EXPECTED_OWNERS),
        "new_independent_items": item_count,
        "object_closures": 0,
        "false_exact_mastery_admissions": 0,
        "learner_audio_persistence": 0,
    }
    result["normalized_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def main() -> int:
    result = validate()
    print("OGE_6_7_COMPONENT_EVIDENCE_WAVE_003=PASS")
    print(f"OWNERS_COMPLETED={result['owners_completed_with_new_component_evidence']}")
    print(f"NEW_INDEPENDENT_ITEMS={result['new_independent_items']}")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
