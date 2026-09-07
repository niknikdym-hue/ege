#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

ACCEPTANCE = HERE / "RU02-NORMATIVE-PRONUNCIATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
OWNER = HERE / "RU02-NORMATIVE-PRONUNCIATION-OWNER-RESOLUTION-v0.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-02-ORTHOEPY-NORMATIVE-PRONUNCIATION-WAVE-004-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

SEMANTIC = "ru-orthoepy-normative-pronunciation-selection"
TAXONOMY = "normative_pronunciation_selection"
LABEL = "Выбор нормативного литературного произношения"
OWNER_SHA = "61d57a8a19c24ebb87c9f975a8fb340b448e3878eb17dbc7e6c57172355296fa"
CONTENT_SHA = "f6587f11c3d9f8b515d795327253aa83ea21f14eb1e260279e75bc2ba2b8c557"
SOURCE_RECONCILIATION_HEAD = "c5592c212557b91578ed48e1bf778e30dd489dc7"

TARGET = {
    "admission_unit_id": "RAU-a8f2ad0b357c9e369c51",
    "requirement_id": "RSK-EDSOO1011-2-2-4-P074",
    "review_group_id": "RUS-SEM-REVIEW-047",
    "source_locator": "EDSOO1011 2.2.4 p.74",
    "module_id": "RU-PROG-02",
    "normalized_meaning": "Применять нормативное произношение и ударение.",
}

CATEGORIES = [
    "unstressed_vowel_pronunciation",
    "selected_consonant_pronunciation",
    "consonant_combination_pronunciation",
    "selected_grammatical_form_pronunciation",
    "loanword_pronunciation",
]
VERIFICATION_IDS = [f"p02-u4-v{i}" for i in range(1, 6)]
FACT_IDS = {
    "pron-vowel-moloko",
    "pron-consonant-dub",
    "pron-cluster-chto",
    "pron-form-ogo",
    "pron-loan-computer",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path.name}")
    return value


def normalized_sha(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def main() -> int:
    acceptance = load(ACCEPTANCE)
    owner = load(OWNER)
    content = load(CONTENT)
    inventory = load(INVENTORY)

    if normalized_sha(owner) != OWNER_SHA:
        raise AssertionError("pronunciation owner-resolution authority drift")
    if normalized_sha(content) != CONTENT_SHA:
        raise AssertionError("pronunciation learner-content authority drift")

    if owner.get("status") != "BOUNDED_SOURCE_BACKED_PRONUNCIATION_OWNER_RESOLUTION_NO_ADMISSION":
        raise AssertionError("pronunciation owner-resolution status drift")
    if owner.get("source_reconciliation_pr") != 187 or owner.get("source_reconciliation_head") != SOURCE_RECONCILIATION_HEAD:
        raise AssertionError("accepted #187 source-reconciliation pin drift")
    if owner.get("target_object") != TARGET:
        raise AssertionError("exact RU02 target identity drift")

    search = owner.get("existing_owner_search") or {}
    if search.get("exact_current_canonical_pronunciation_owner_found") is not False:
        raise AssertionError("existing canonical pronunciation owner unexpectedly appeared")
    if search.get("resolution") != "NO_EXACT_CURRENT_PRONUNCIATION_OWNER":
        raise AssertionError("pronunciation owner-search resolution drift")
    stress = search.get("normative_stress_owner") or {}
    if stress.get("semantic_id") != "ru-orthoepy-normative-stress-selection":
        raise AssertionError("accepted stress semantic ref drift")
    if stress.get("candidate_ref") != "candidate-018" or stress.get("may_cover_pronunciation_component") is not False:
        raise AssertionError("stress component illegally substitutes for pronunciation")
    source_check = search.get("source_check_nonowner") or {}
    if source_check.get("semantic_id") != "ru-orthoepy-norm-source-check" or source_check.get("may_cover_pronunciation_component") is not False:
        raise AssertionError("source-check nonowner boundary drift")

    proposed = owner.get("proposed_owner") or {}
    if proposed.get("semantic_id") != SEMANTIC or proposed.get("source_taxonomy_id") != TAXONOMY:
        raise AssertionError("proposed pronunciation identity drift")
    if proposed.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise AssertionError("owner-resolution file must remain pre-admission")
    if proposed.get("label_ru") != LABEL:
        raise AssertionError("pronunciation label drift")
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
        raise AssertionError("official FIPI pronunciation scope URL drift")
    if official.get("page") != 1 or official.get("codifier_position") != "3.2.3":
        raise AssertionError("official FIPI pronunciation locator drift")

    norm_facts = proposed.get("independent_norm_fact_sources")
    if not isinstance(norm_facts, list) or len(norm_facts) != 5:
        raise AssertionError("exactly five independent pronunciation norm facts required")
    if {str(row.get("fact_id")) for row in norm_facts if isinstance(row, dict)} != FACT_IDS:
        raise AssertionError("pronunciation norm-fact identity drift")
    for row in norm_facts:
        if not isinstance(row, dict) or not str(row.get("source_url", "")).startswith("https://gramota.ru/"):
            raise AssertionError("independent pronunciation norm source is not pinned to Gramota")

    owner_boundary = owner.get("acceptance_boundary") or {}
    if owner_boundary.get("semantic_admission_effect") != "NONE":
        raise AssertionError("owner-resolution file self-admitted semantics")
    if owner_boundary.get("object_closure_effect") != "NONE":
        raise AssertionError("owner-resolution file closed the object")
    if owner_boundary.get("exact_mastery_effect") != "NONE":
        raise AssertionError("owner-resolution file emitted exact mastery")
    if owner_boundary.get("component_specific_independent_learner_evidence_required") is not True:
        raise AssertionError("component-specific evidence requirement weakened")
    if owner_boundary.get("candidate_owner_resolution_can_self_admit") is not False:
        raise AssertionError("candidate owner resolution can self-admit")
    if owner_boundary.get("route_or_task_name_can_admit_semantics") is not False:
        raise AssertionError("route/task inference admitted semantics")
    if owner_boundary.get("false_exact_mastery") != 0:
        raise AssertionError("false exact mastery drift in owner resolution")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-02":
        raise AssertionError("pronunciation content status/module drift")
    identity = content.get("identity_boundary") or {}
    if identity.get("proposed_semantic_id") != SEMANTIC or identity.get("source_taxonomy_id") != TAXONOMY:
        raise AssertionError("pronunciation content identity drift")
    if identity.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError("content file must remain pre-admission")
    if identity.get("object_level_admission_effect") != "NONE_UNTIL_SEPARATE_EXACT_OBJECT_BINDING":
        raise AssertionError("pronunciation content changed object-level admission effect")
    if identity.get("generic_orthoepy_result_can_emit_exact_component_mastery") is not False:
        raise AssertionError("generic orthoepy result can emit exact pronunciation mastery")

    units = content.get("units")
    if not isinstance(units, list) or len(units) != 1:
        raise AssertionError("pronunciation content must contain exactly one bounded unit")
    unit = units[0]
    if unit.get("proposed_semantic_id") != SEMANTIC:
        raise AssertionError("pronunciation unit semantic drift")
    verification = unit.get("independent_verification")
    if not isinstance(verification, list) or len(verification) != 5:
        raise AssertionError("exactly five independent pronunciation verification items required")
    if [str(row.get("id")) for row in verification if isinstance(row, dict)] != VERIFICATION_IDS:
        raise AssertionError("pronunciation verification identity/order drift")
    if [str(row.get("category")) for row in verification if isinstance(row, dict)] != CATEGORIES:
        raise AssertionError("pronunciation verification category/order drift")
    if any(row.get("type") != "single_choice" for row in verification if isinstance(row, dict)):
        raise AssertionError("pronunciation verification mode drift")
    for row in verification:
        if not isinstance(row, dict):
            raise AssertionError("invalid pronunciation verification row")
        options = row.get("options")
        correct_index = row.get("correct_option_index")
        if not isinstance(options, list) or len(options) < 2 or not isinstance(correct_index, int) or not (0 <= correct_index < len(options)):
            raise AssertionError(f"invalid independent verification answer schema: {row.get('id')}")

    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError("pronunciation content PEIS self-admitted")
    if peis.get("component_specific_independent_evidence_required") is not True:
        raise AssertionError("component-specific pronunciation evidence no longer required")
    if peis.get("stress_mastery_can_substitute_for_pronunciation_mastery") is not False:
        raise AssertionError("stress mastery substitutes for pronunciation mastery")
    if peis.get("generic_orthoepy_score_can_emit_exact_mastery") is not False:
        raise AssertionError("generic orthoepy score can emit exact mastery")
    if peis.get("false_exact_mastery") != 0:
        raise AssertionError("pronunciation PEIS false exact mastery drift")

    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    collisions = [
        str(row.get("object_key"))
        for row in objects
        if row.get("authority_status") == "current"
        and SEMANTIC in {str(ref) for ref in (row.get("current_semantic_refs") or [])}
    ]
    if collisions:
        raise AssertionError(f"pronunciation semantic id already exists in current inventory: {collisions}")

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU02_NORMATIVE_PRONUNCIATION_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("pronunciation subject-acceptance status drift")
    if acceptance.get("authority_issue") != 161:
        raise AssertionError("pronunciation acceptance authority issue drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("pronunciation acceptance mutated school registry")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("pronunciation acceptance created a parallel registry")

    authority = acceptance.get("authority") or {}
    if authority.get("source_reconciliation_pr") != 187 or authority.get("source_reconciliation_head") != SOURCE_RECONCILIATION_HEAD:
        raise AssertionError("pronunciation acceptance source-reconciliation pin drift")
    if authority.get("owner_normalized_sha256") != OWNER_SHA or authority.get("content_normalized_sha256") != CONTENT_SHA:
        raise AssertionError("pronunciation acceptance normalized authority pins drift")

    policy = acceptance.get("policy") or {}
    expected_policy = {
        "exact_source_backed_owner_resolution_required": True,
        "official_fipi_scope_required": True,
        "independent_norm_fact_sources_required": True,
        "original_exact_learner_content_required": True,
        "stress_component_may_substitute_for_pronunciation": False,
        "route_or_task_name_can_admit_semantics": False,
        "canonical_school_registry_mutation_required": False,
        "parallel_registry_creation_forbidden": True,
        "content_or_evidence_presence_alone_is_semantic_admission": False,
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
        "generic_orthoepy_result_can_emit_exact_pronunciation_mastery": False,
        "generic_stress_result_can_emit_exact_pronunciation_mastery": False,
        "component_specific_independent_evidence_required": True,
        "exact_object_binding_requires_all_object_components": True,
    }
    for key, expected in expected_policy.items():
        if policy.get(key) is not expected:
            raise AssertionError(f"pronunciation acceptance policy drift: {key}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("pronunciation acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("pronunciation acceptance crosswalk drift")
    if decision.get("canonical_label_ru") != LABEL or decision.get("entity_type") != "PRONUNCIATION_SELECTION_SKILL":
        raise AssertionError("pronunciation acceptance label/entity drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("pronunciation semantic is not explicitly bounded-accepted")
    if decision.get("owner_search_result") != "NO_EXACT_CURRENT_PRONUNCIATION_OWNER":
        raise AssertionError("pronunciation owner-search result drift")
    if decision.get("source_evidence_status") != "confirmed":
        raise AssertionError("pronunciation source evidence not confirmed")
    if decision.get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise AssertionError("pronunciation accepted verification identity drift")
    if decision.get("pronunciation_categories") != CATEGORIES:
        raise AssertionError("pronunciation accepted category boundary drift")
    if decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("pronunciation acceptance improperly closes/binds the RU02 object")
    if "excludes normative stress selection" not in str(decision.get("boundary_guard", "")):
        raise AssertionError("pronunciation acceptance does not explicitly exclude stress substitution")

    summary = acceptance.get("summary") or {}
    expected_summary = {
        "accepted_bounded_subject_semantics": 1,
        "accepted_ru_subject_semantics": 1,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "exact_mastery_admissions": 0,
        "false_exact_mastery_admissions": 0,
    }
    if summary != expected_summary:
        raise AssertionError("pronunciation acceptance summary drift")

    other_semantic_acceptances = []
    for path in HERE.glob("*.json"):
        if path == ACCEPTANCE:
            continue
        try:
            value = load(path)
        except Exception:
            continue
        status = str(value.get("status") or "")
        if "ACCEPTED" not in status:
            continue
        decisions = value.get("decisions")
        if not isinstance(decisions, list):
            continue
        if any(
            isinstance(row, dict) and row.get("accepted_semantic_id") == SEMANTIC
            for row in decisions
        ):
            other_semantic_acceptances.append(path.name)
    if other_semantic_acceptances:
        raise AssertionError(
            f"pronunciation semantic already accepted by another subject-semantic authority: {other_semantic_acceptances}"
        )

    print("RU02_NORMATIVE_PRONUNCIATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print(f"TARGET_ADMISSION_UNIT={TARGET['admission_unit_id']}")
    print(f"TARGET_REQUIREMENT={TARGET['requirement_id']}")
    print(f"TARGET_REVIEW_GROUP={TARGET['review_group_id']}")
    print(f"PRONUNCIATION_CATEGORIES={len(CATEGORIES)}")
    print(f"INDEPENDENT_VERIFICATION_ITEMS={len(VERIFICATION_IDS)}")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("EXACT_MASTERY_ADMISSIONS=0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"ACCEPTANCE_NORMALIZED_SHA256={normalized_sha(acceptance)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
