#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
OWNER = HERE / "RU02-NORMATIVE-PRONUNCIATION-OWNER-RESOLUTION-v0.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-02-ORTHOEPY-NORMATIVE-PRONUNCIATION-WAVE-004-v0.1.json"

TARGET = {
    "admission_unit_id": "RAU-a8f2ad0b357c9e369c51",
    "requirement_id": "RSK-EDSOO1011-2-2-4-P074",
    "review_group_id": "RUS-SEM-REVIEW-047",
    "source_locator": "EDSOO1011 2.2.4 p.74",
    "module_id": "RU-PROG-02",
    "normalized_meaning": "Применять нормативное произношение и ударение.",
}
SEMANTIC = "ru-orthoepy-normative-pronunciation-selection"
CATEGORIES = [
    "unstressed_vowel_pronunciation",
    "selected_consonant_pronunciation",
    "consonant_combination_pronunciation",
    "selected_grammatical_form_pronunciation",
    "loanword_pronunciation",
]
FACTS = {
    "pron-vowel-moloko": ("unstressed_vowel_pronunciation", "молоко", "[малако́]"),
    "pron-consonant-dub": ("selected_consonant_pronunciation", "дуб", "[дуп]"),
    "pron-cluster-chto": ("consonant_combination_pronunciation", "что", "[што]"),
    "pron-form-ogo": ("selected_grammatical_form_pronunciation", "доброго", "в окончании -ого буква г произносится как [в]"),
    "pron-loan-computer": ("loanword_pronunciation", "компьютер", "в сочетании те произносится твёрдый [т] перед [э]"),
}
VERIFICATION_IDS = [f"p02-u4-v{i}" for i in range(1, 6)]


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path.name}")
    return value


def assert_zero_admission(boundary: dict[str, Any]) -> None:
    if boundary.get("semantic_admission_effect") != "NONE":
        raise AssertionError("pronunciation owner resolution self-admitted semantics")
    if boundary.get("object_closure_effect") != "NONE":
        raise AssertionError("pronunciation owner resolution closed object")
    if boundary.get("exact_mastery_effect") != "NONE":
        raise AssertionError("pronunciation owner resolution emitted mastery")
    if boundary.get("component_specific_independent_learner_evidence_required") is not True:
        raise AssertionError("component-specific evidence requirement weakened")
    if boundary.get("candidate_owner_resolution_can_self_admit") is not False:
        raise AssertionError("candidate owner can self-admit")
    if boundary.get("route_or_task_name_can_admit_semantics") is not False:
        raise AssertionError("route/task inference admitted")
    if boundary.get("reference_reading_can_create_mastery") is not False:
        raise AssertionError("reference reading can create mastery")
    if boundary.get("false_exact_mastery") != 0:
        raise AssertionError("false exact mastery drift")


def main() -> int:
    owner = load(OWNER)
    content = load(CONTENT)

    if owner.get("status") != "BOUNDED_SOURCE_BACKED_PRONUNCIATION_OWNER_RESOLUTION_NO_ADMISSION":
        raise AssertionError("owner resolution status drift")
    if owner.get("source_reconciliation_pr") != 187:
        raise AssertionError("source reconciliation PR drift")
    if owner.get("source_reconciliation_head") != "c5592c212557b91578ed48e1bf778e30dd489dc7":
        raise AssertionError("accepted #187 authority head drift")
    if owner.get("target_object") != TARGET:
        raise AssertionError("exact RU02 target identity drift")

    search = owner.get("existing_owner_search") or {}
    if search.get("exact_current_canonical_pronunciation_owner_found") is not False:
        raise AssertionError("unexpected canonical pronunciation owner claim")
    stress = search.get("normative_stress_owner") or {}
    if stress.get("semantic_id") != "ru-orthoepy-normative-stress-selection" or stress.get("candidate_ref") != "candidate-018":
        raise AssertionError("stress owner boundary drift")
    if stress.get("may_cover_pronunciation_component") is not False:
        raise AssertionError("stress owner illegally covers pronunciation")
    source_check = search.get("source_check_nonowner") or {}
    if source_check.get("semantic_id") != "ru-orthoepy-norm-source-check" or source_check.get("may_cover_pronunciation_component") is not False:
        raise AssertionError("source-check nonowner boundary drift")
    if search.get("resolution") != "NO_EXACT_CURRENT_PRONUNCIATION_OWNER":
        raise AssertionError("owner-search resolution drift")

    proposed = owner.get("proposed_owner") or {}
    if proposed.get("semantic_id") != SEMANTIC or proposed.get("source_taxonomy_id") != "normative_pronunciation_selection":
        raise AssertionError("proposed pronunciation owner identity drift")
    if proposed.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise AssertionError("proposed pronunciation owner self-admitted")
    boundary = proposed.get("boundary") or {}
    if boundary.get("includes") != CATEGORIES:
        raise AssertionError("pronunciation category boundary drift")
    if set(boundary.get("excludes") or []) != {
        "normative_stress_selection",
        "spelling",
        "generic_phonetic_analysis",
        "source_lookup_without_independent_application",
    }:
        raise AssertionError("pronunciation exclusion boundary drift")

    official = proposed.get("official_scope_source") or {}
    if official.get("url") != "https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-1-fonetika.pdf":
        raise AssertionError("official FIPI pronunciation source drift")
    if official.get("page") != 1 or official.get("codifier_position") != "3.2.3":
        raise AssertionError("official FIPI locator drift")

    source_facts = proposed.get("independent_norm_fact_sources")
    if not isinstance(source_facts, list) or len(source_facts) != 5:
        raise AssertionError("exact five pronunciation norm facts required")
    by_id = {str(row.get("fact_id")): row for row in source_facts if isinstance(row, dict)}
    if set(by_id) != set(FACTS):
        raise AssertionError("pronunciation norm fact identity drift")
    for fact_id, (category, prompt_form, normative_fact) in FACTS.items():
        row = by_id[fact_id]
        if row.get("category") != category or row.get("prompt_form") != prompt_form or row.get("normative_fact") != normative_fact:
            raise AssertionError(f"pronunciation norm fact drift: {fact_id}")
        if not str(row.get("source_url", "")).startswith("https://gramota.ru/"):
            raise AssertionError(f"non-Gramota independent norm source: {fact_id}")
    assert_zero_admission(owner.get("acceptance_boundary") or {})

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-02":
        raise AssertionError("pronunciation content status/module drift")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes_in_git") != 0:
        raise AssertionError("pronunciation copyright boundary weakened")
    if guard.get("learner_explanations") != "ORIGINAL_EKSAMIO":
        raise AssertionError("pronunciation learner explanation provenance drift")

    identity = content.get("identity_boundary") or {}
    if identity.get("proposed_semantic_id") != SEMANTIC or identity.get("source_taxonomy_id") != "normative_pronunciation_selection":
        raise AssertionError("pronunciation content semantic identity drift")
    if identity.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError("pronunciation content self-admitted")
    if identity.get("generic_orthoepy_result_can_emit_exact_component_mastery") is not False:
        raise AssertionError("generic orthoepy result can emit exact pronunciation mastery")

    units = content.get("units")
    if not isinstance(units, list) or len(units) != 1:
        raise AssertionError("exact one pronunciation content unit required")
    unit = units[0]
    if unit.get("proposed_semantic_id") != SEMANTIC:
        raise AssertionError("pronunciation unit semantic identity drift")

    for key, exact_count in (
        ("worked_examples", 5),
        ("guided_practice", 5),
        ("independent_practice", 5),
        ("mixed_transfer_practice", 2),
        ("retention_items", 5),
        ("independent_verification", 5),
    ):
        rows = unit.get(key)
        if not isinstance(rows, list) or len(rows) != exact_count:
            raise AssertionError(f"pronunciation learner-content section drift: {key}")
    if not isinstance(unit.get("decision_algorithm"), list) or len(unit["decision_algorithm"]) != 5:
        raise AssertionError("pronunciation decision algorithm drift")
    if not isinstance(unit.get("misconceptions"), list) or len(unit["misconceptions"]) != 3:
        raise AssertionError("pronunciation misconceptions drift")

    verification = unit["independent_verification"]
    if [row.get("id") for row in verification] != VERIFICATION_IDS:
        raise AssertionError("pronunciation independent verification IDs drift")
    if [row.get("category") for row in verification] != CATEGORIES:
        raise AssertionError("one exact independent verification per pronunciation category required")
    if [row.get("source_fact_id") for row in verification] != list(FACTS):
        raise AssertionError("independent verification source-fact order drift")
    for row in verification:
        if row.get("type") != "single_choice":
            raise AssertionError("pronunciation verification must be deterministic single choice")
        options = row.get("options")
        index = row.get("correct_option_index")
        if not isinstance(options, list) or len(options) != 2 or not isinstance(index, int) or index not in (0, 1):
            raise AssertionError("pronunciation verification choice schema drift")

    scoring = unit.get("scoring") or {}
    if scoring.get("independent_verification_item_count") != 5:
        raise AssertionError("pronunciation verification denominator drift")
    if scoring.get("pass_rule") != "5/5 exact category-specific items correct in one unassisted attempt":
        raise AssertionError("pronunciation exact pass rule drift")
    if scoring.get("partial_credit_can_create_exact_component_mastery") is not False:
        raise AssertionError("partial credit can create exact pronunciation mastery")
    if scoring.get("cross_category_substitution_allowed") is not False:
        raise AssertionError("cross-category evidence substitution allowed")

    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError("pronunciation PEIS semantic ref self-admitted")
    if peis.get("component_specific_independent_evidence_required") is not True:
        raise AssertionError("pronunciation component-specific PEIS evidence weakened")
    if peis.get("stress_mastery_can_substitute_for_pronunciation_mastery") is not False:
        raise AssertionError("stress mastery substitutes for pronunciation mastery")
    if peis.get("generic_orthoepy_score_can_emit_exact_mastery") is not False:
        raise AssertionError("generic orthoepy score emits exact pronunciation mastery")
    if peis.get("false_exact_mastery") != 0:
        raise AssertionError("pronunciation false exact mastery drift")

    summary = content.get("summary") or {}
    expected_summary = {
        "production_content_units": 1,
        "pronunciation_categories_covered": 5,
        "independent_verification_items": 5,
        "semantic_admissions": 0,
        "object_level_closures": 0,
        "false_exact_mastery_admissions": 0,
    }
    if summary != expected_summary:
        raise AssertionError("pronunciation content summary drift")

    owner_sha = hashlib.sha256(canonical_json(owner)).hexdigest()
    content_sha = hashlib.sha256(canonical_json(content)).hexdigest()
    print("RU02_NORMATIVE_PRONUNCIATION_COMPONENT_EVIDENCE=PASS")
    print(f"TARGET_ADMISSION_UNIT={TARGET['admission_unit_id']}")
    print(f"TARGET_REQUIREMENT={TARGET['requirement_id']}")
    print(f"TARGET_REVIEW_GROUP={TARGET['review_group_id']}")
    print("PRONUNCIATION_CATEGORIES=5")
    print("INDEPENDENT_VERIFICATION_ITEMS=5")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"OWNER_NORMALIZED_SHA256={owner_sha}")
    print(f"CONTENT_NORMALIZED_SHA256={content_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
