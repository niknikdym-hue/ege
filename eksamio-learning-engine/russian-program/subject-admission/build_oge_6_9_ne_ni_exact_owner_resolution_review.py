#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
CURRENT_SCHOOL = ENGINE / "277-RUSSIAN-SCHOOL-CURRENT-LAUNCH-REFREEZE-v1.1.json"
FRONTIER_BUILDER = HERE / "build_oge_6_9_ne_ni_source_bound_frontier_review.py"

TARGET_CODE = "6.9"
FIPI_NAVIGATOR_URL = "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf"

FIPI_BRANCH_SUPPORT = {
    "ne_with_nouns": {
        "fipi_wording": "слитное и раздельное написание не с именами существительными",
        "recommended_paragraphs": ["§51. НЕ с существительными"],
    },
    "ne_with_adjectives": {
        "fipi_wording": "слитное и раздельное написание не с именами прилагательными",
        "recommended_paragraphs": ["§65. НЕ с прилагательными"],
    },
    "ne_with_verbs": {
        "fipi_wording": "слитное и раздельное написание не с глаголами",
        "recommended_paragraphs": ["§105. НЕ с глаголами"],
    },
    "pronouns_with_ne_ni": {
        "fipi_wording": "правописание местоимений с не и ни",
        "recommended_paragraphs": [
            "§71. Отрицательные частицы НЕ и НИ",
            "§72. Различение частицы НЕ и приставки НЕ",
            "§73. Частица НИ, приставка НИ-, союз НИ... НИ",
        ],
    },
    "ne_with_participles": {
        "fipi_wording": "слитное и раздельное написание не с причастиями",
        "recommended_paragraphs": ["§26. Слитное и раздельное написание НЕ с причастиями"],
    },
    "ne_with_gerunds": {
        "fipi_wording": "слитное и раздельное написание не с деепричастиями",
        "recommended_paragraphs": ["§30. Раздельное написание НЕ с деепричастиями"],
    },
    "ne_with_adverbs": {
        "fipi_wording": "слитное и раздельное написание не с наречиями",
        "recommended_paragraphs": [
            "§38. Слитное и раздельное написание НЕ с наречиями на -О и -Е",
            "§39. Буквы Е и И в приставках НЕ- и НИ- отрицательных наречий",
        ],
    },
    "semantic_distinction_ne_ni": {
        "fipi_wording": "смысловые различия частиц не и ни",
        "recommended_paragraphs": [
            "§71. Отрицательные частицы НЕ и НИ",
            "§72. Различение частицы НЕ и приставки НЕ",
            "§73. Частица НИ, приставка НИ-, союз НИ... НИ",
        ],
    },
}

OWNER_BINDINGS = {
    "school-ne-noun-adjective-o-adverb-spelling-system": {
        "branches": ["ne_with_nouns", "ne_with_adjectives", "ne_with_adverbs"],
        "expected_label": "НЕ с существительными, прилагательными и наречиями на -о: слитно или раздельно по значению и контексту",
        "primary_provenance": "255-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-D-O36-O45-v0.1.json",
        "reason": "Current canonical identity directly owns the productive НЕ spelling system for nouns, adjectives and -о adverbs named by three explicit FIPI 6.9 branches.",
    },
    "school-ne-verb-gerund-spelling-base": {
        "branches": ["ne_with_verbs", "ne_with_gerunds"],
        "expected_label": "НЕ с глаголами и деепричастиями: раздельно, лексикализованные НЕ-/НЕДО- формы слитно",
        "primary_provenance": "255-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-D-O36-O45-v0.1.json",
        "reason": "Current canonical identity directly covers the two explicit FIPI 6.9 branches for verbs and gerunds, including the lexicalized НЕ-/НЕДО- boundary.",
    },
    "school-ne-numeral-pronoun-spelling-base": {
        "branches": ["pronouns_with_ne_ni"],
        "expected_label": "НЕ с числительными и местоименными словами: базовое раздельное написание и граница с отрицательными/неопределёнными формами",
        "primary_provenance": "255-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-D-O36-O45-v0.1.json",
        "reason": "Its pronoun-word component is a direct spelling owner for the explicit FIPI branch on pronouns with НЕ/НИ; the numeral portion is not used to widen 6.9.",
    },
    "school-negative-pronouns-ne-ni-stress-preposition-boundary": {
        "branches": ["pronouns_with_ne_ni", "semantic_distinction_ne_ni"],
        "expected_label": "НЕ/НИ в отрицательных местоимениях: ударение и предлог",
        "primary_provenance": "172-RUSSIAN-SCHOOL-CANONICAL-BANK-CHUNK04-ADVERBS-PRONOUNS-HYPHEN-v0.1.json",
        "reason": "Directly resolves НЕ/НИ choice and separate writing with a preposition in negative pronouns, within the pronoun branch and the НЕ/НИ distinction boundary.",
    },
    "school-ne-kto-inoy-vs-nikto-inoy": {
        "branches": ["pronouns_with_ne_ni", "semantic_distinction_ne_ni"],
        "expected_label": "НЕ КТО ИНОЙ, КАК / НЕ ЧТО ИНОЕ, КАК vs НИКТО ИНОЙ / НИЧТО ИНОЕ",
        "primary_provenance": "195-RUSSIAN-SCHOOL-CANONICAL-BANK-CHUNK18-GRADE10-NE-NI-CONTRASTS-v0.1.json",
        "reason": "A current canonical pronoun construction whose spelling and meaning turn on the НЕ/НИ contrast; no neighboring 6.8/6.11 semantics are imported.",
    },
    "school-ne-participle-dependent-short-opposition-boundary": {
        "branches": ["ne_with_participles"],
        "expected_label": "НЕ с причастиями: зависимое слово, краткая форма, противопоставление",
        "primary_provenance": "206-RUSSIAN-SCHOOL-CANONICAL-BANK-CHUNK29-GRADE7-NE-PARTICIPLES-v0.1.json",
        "reason": "Direct current canonical owner for the explicit FIPI branch on solid/separate НЕ with participles.",
    },
    "school-ne-non-o-adverb-predicative-separate-system": {
        "branches": ["ne_with_adverbs"],
        "expected_label": "НЕ с ненаречиями на -о, неизменяемыми словами и предикативами: базовое раздельное написание и функциональные исключения",
        "primary_provenance": "255-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-D-O36-O45-v0.1.json",
        "reason": "Covers the current canonical non--о/invariable/predicative boundary needed to prevent the -о adverb rule from being overgeneralized within the FIPI adverb branch.",
    },
    "school-negative-adverbs-ne-ni-spelling": {
        "branches": ["ne_with_adverbs", "semantic_distinction_ne_ni"],
        "expected_label": "НЕ- / НИ- в отрицательных наречиях и местоименных словах по ударению",
        "primary_provenance": "253-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-C-O26-O35-v0.1.json",
        "reason": "FIPI explicitly recommends the paragraph on НЕ-/НИ- in negative adverbs; this current identity owns that exact distinction without broadening to other orthography routes.",
    },
    "school-pri-chem-ni-pri-chem-nipochem": {
        "branches": ["ne_with_adverbs", "semantic_distinction_ne_ni"],
        "expected_label": "ПРИ ЧЁМ / НИ ПРИ ЧЁМ / НИПОЧЁМ",
        "primary_provenance": "185-RUSSIAN-SCHOOL-CANONICAL-BANK-CHUNK10-GRADE10-MIXED-SPECIALS-v0.1.json",
        "reason": "This bounded current identity distinguishes a separate НИ + preposition/pronoun construction from the lexicalized НИПОЧЁМ adverb; only that 6.9-relevant boundary is admitted.",
    },
    "school-ni-particle-vs-repeating-conjunction": {
        "branches": ["semantic_distinction_ne_ni"],
        "expected_label": "НИ: усилительная частица vs повторяющийся союз НИ… НИ",
        "primary_provenance": "209-RUSSIAN-SCHOOL-CANONICAL-BANK-CHUNK32-NI-PARTICLE-CONJUNCTION-v0.1.json",
        "reason": "FIPI explicitly points to the paragraph distinguishing particle НИ, prefix НИ- and conjunction НИ...НИ; this identity is therefore branch-bound evidence for the 6.9 functional/semantic distinction, not a generic 6.11 service-word admission.",
    },
    "school-ni-fixed-idioms": {
        "branches": ["semantic_distinction_ne_ni"],
        "expected_label": "Устойчивые сочетания с НИ",
        "primary_provenance": "245-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-SOURCE-ADMISSION-NI-FIXED-IDIOMS-v0.1.json",
        "reason": "Current source-admitted fixed НИ constructions are a bounded lexical exception inside the 6.9 НЕ/НИ choice surface; they are not generalized to arbitrary idioms.",
    },
    "school-ne-double-negation-affirmative-boundary": {
        "branches": ["semantic_distinction_ne_ni"],
        "expected_label": "НЕ МОГ НЕ...: двойное отрицание и утвердительный смысл",
        "primary_provenance": "207-RUSSIAN-SCHOOL-CANONICAL-BANK-CHUNK30-GRADE7-DOUBLE-NEGATION-v0.1.json",
        "reason": "Direct semantic НЕ/НИ choice boundary: the second particle is НЕ and the double negation yields affirmative/unavoidable meaning.",
    },
    "school-ne-ni-ni-odin-ne-odin-ni-razu-ne-raz": {
        "branches": ["semantic_distinction_ne_ni"],
        "expected_label": "НИ ОДИН / НЕ ОДИН; НИ РАЗУ / НЕ РАЗ",
        "primary_provenance": "195-RUSSIAN-SCHOOL-CANONICAL-BANK-CHUNK18-GRADE10-NE-NI-CONTRASTS-v0.1.json",
        "reason": "Direct minimal-pair semantic choice between НЕ and НИ, exactly within the explicit FIPI distinction branch.",
    },
    "school-ne-ni-pronominal-exclamatory-vs-concessive-boundary": {
        "branches": ["semantic_distinction_ne_ni"],
        "expected_label": "КУДА ТОЛЬКО НЕ... vs КУДА НИ...: восклицание и уступительно-обобщающее придаточное",
        "primary_provenance": "208-RUSSIAN-SCHOOL-CANONICAL-BANK-CHUNK31-GRADE7-NE-NI-CLAUSE-CONTRAST-v0.1.json",
        "reason": "Direct НЕ/НИ semantic contrast between affirmative interrogative/exclamatory and concessive-generalizing pronominal constructions.",
    },
}

EXPECTED_EXACT_OWNERS = sorted(OWNER_BINDINGS)
EXPECTED_FRONTIER_CANDIDATES = EXPECTED_EXACT_OWNERS
EXPECTED_CURRENT_ROUTE_REFS = ["school-ni-fixed-idioms"]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def normalized_sha(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_review() -> dict[str, Any]:
    inventory = load_json(INVENTORY)
    current_school = load_json(CURRENT_SCHOOL)
    frontier = runpy.run_path(str(FRONTIER_BUILDER))["build_review"]()

    if frontier.get("status") != "CENTRAL_BRAIN_SOURCE_BOUND_FRONTIER_PROVEN_NO_ADMISSION":
        raise ValueError("6.9 source-bound frontier is not accepted")
    source_frontier = frontier["source_bound_frontier"]
    if source_frontier["official_branch_count"] != len(FIPI_BRANCH_SUPPORT):
        raise ValueError("6.9 official branch count drift")
    if source_frontier["unique_owner_candidates"] != EXPECTED_FRONTIER_CANDIDATES:
        raise ValueError("6.9 source-bound candidate set drift")
    if source_frontier["current_route_refs"] != EXPECTED_CURRENT_ROUTE_REFS:
        raise ValueError("6.9 current route refs drift")
    if source_frontier["current_nonexact_route_refs"]:
        raise ValueError("6.9 source-bound frontier contains nonexact current route refs")
    if source_frontier["school_reopen_required"]:
        raise ValueError("6.9 unexpectedly requires school identity reopen")

    frontier_branches = {
        row["branch"]: {
            "fipi_wording": row["fipi_wording"],
            "candidate_owner_refs": sorted(row["candidate_owner_refs"]),
        }
        for row in frontier["official_source"]["branches"]
    }
    if set(frontier_branches) != set(FIPI_BRANCH_SUPPORT):
        raise ValueError("6.9 branch names drifted")
    for branch, support in FIPI_BRANCH_SUPPORT.items():
        if frontier_branches[branch]["fipi_wording"] != support["fipi_wording"]:
            raise ValueError(f"6.9 FIPI wording drift for {branch}")

    objects = [row for row in inventory.get("objects") or [] if isinstance(row, dict)]
    canonical_rows = {
        str(row.get("source_id")): row
        for row in objects
        if row.get("source_system") == "school_canonical"
        and str(row.get("source_id") or "").startswith("school-")
    }

    exact_owner_rows: list[dict[str, Any]] = []
    rejected_candidates: list[str] = []
    all_primary_authorities_present = True
    exact_owner_branch_pairs: set[tuple[str, str]] = set()

    for owner in EXPECTED_FRONTIER_CANDIDATES:
        binding = OWNER_BINDINGS.get(owner)
        if binding is None:
            rejected_candidates.append(owner)
            continue
        row = canonical_rows.get(owner)
        if row is None:
            raise ValueError(f"6.9 owner missing canonical inventory row: {owner}")
        if row.get("authority_status") != "current":
            raise ValueError(f"6.9 owner not current: {owner}")
        if row.get("review_status") != "reviewed":
            raise ValueError(f"6.9 owner not reviewed: {owner}")
        if row.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY":
            raise ValueError(f"6.9 owner not canonical school identity: {owner}")
        if row.get("current_semantic_refs") != [owner]:
            raise ValueError(f"6.9 owner self-ref drift: {owner}")
        if row.get("candidate_canonical_owner") != owner:
            raise ValueError(f"6.9 owner canonical-owner drift: {owner}")
        if row.get("observed_label") != binding["expected_label"]:
            raise ValueError(f"6.9 observed label drift: {owner}")

        branches = binding["branches"]
        if not branches or any(branch not in FIPI_BRANCH_SUPPORT for branch in branches):
            raise ValueError(f"6.9 owner branch binding invalid: {owner}")
        for branch in branches:
            if owner not in frontier_branches[branch]["candidate_owner_refs"]:
                raise ValueError(f"6.9 owner/branch binding not present in source frontier: {owner} -> {branch}")
            exact_owner_branch_pairs.add((branch, owner))

        provenance = [str(value) for value in row.get("evidence_provenance_refs") or []]
        primary = str(binding["primary_provenance"])
        if primary not in provenance:
            raise ValueError(f"6.9 primary provenance drift: {owner}")
        primary_exists = (ENGINE / primary).is_file()
        all_primary_authorities_present = all_primary_authorities_present and primary_exists
        if not primary_exists:
            raise ValueError(f"6.9 primary provenance authority file missing: {primary}")

        exact_owner_rows.append(
            {
                "owner_ref": owner,
                "branches": branches,
                "observed_label": str(row.get("observed_label")),
                "observed_meaning_sha256": hashlib.sha256(
                    str(row.get("observed_meaning") or "").encode("utf-8")
                ).hexdigest(),
                "primary_provenance": primary,
                "primary_provenance_present": primary_exists,
                "review_status": str(row.get("review_status")),
                "reason": str(binding["reason"]),
                "classification": "EXACT_BRANCH_OWNER",
            }
        )

    expected_pairs = {
        (branch, owner)
        for branch, row in frontier_branches.items()
        for owner in row["candidate_owner_refs"]
    }
    if exact_owner_branch_pairs != expected_pairs:
        missing = sorted(expected_pairs - exact_owner_branch_pairs)
        extra = sorted(exact_owner_branch_pairs - expected_pairs)
        raise ValueError(f"6.9 branch-owner resolution mismatch missing={missing} extra={extra}")

    exact_owner_refs = sorted(row["owner_ref"] for row in exact_owner_rows)
    if exact_owner_refs != EXPECTED_EXACT_OWNERS:
        raise ValueError("6.9 exact owner set drift")
    if rejected_candidates:
        raise ValueError(f"6.9 unresolved/rejected source-bound candidates: {rejected_candidates}")

    branch_resolution = []
    for branch in FIPI_BRANCH_SUPPORT:
        owner_refs = sorted(owner for pair_branch, owner in exact_owner_branch_pairs if pair_branch == branch)
        if not owner_refs:
            raise ValueError(f"6.9 official branch has no exact owner: {branch}")
        support = FIPI_BRANCH_SUPPORT[branch]
        branch_resolution.append(
            {
                "branch": branch,
                "fipi_wording": support["fipi_wording"],
                "recommended_paragraphs": support["recommended_paragraphs"],
                "exact_owner_refs": owner_refs,
                "exact_owner_count": len(owner_refs),
                "status": "EXACT_OWNER_SET_RESOLVED",
            }
        )

    if current_school.get("current_school_canonical_denominator") != 186:
        raise ValueError("current school denominator drift")

    missing_from_route = sorted(set(exact_owner_refs) - set(EXPECTED_CURRENT_ROUTE_REFS))
    if len(missing_from_route) != 13:
        raise ValueError("6.9 route supersession delta drift")

    result = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_OGE_6_9_EXACT_OWNER_RESOLUTION_ACCEPTED_NO_ROUTE_MUTATION",
        "authority_issue": 161,
        "scope": "OGE_2026_ORTHOGRAPHY_CODE_6_9_BRANCH_BOUND_EXACT_OWNER_RESOLUTION",
        "official_source": {
            "document": "ФИПИ. Навигатор самостоятельной подготовки к ОГЭ-2026. Русский язык. Орфография",
            "url": FIPI_NAVIGATOR_URL,
            "content_code": TARGET_CODE,
            "retrieved_for_review": "2026-09-01",
            "branch_count": len(FIPI_BRANCH_SUPPORT),
            "branch_resolution": branch_resolution,
            "support_boundary": (
                "The official 6.9 wording and FIPI-recommended paragraphs are used only to bind the "
                "eight explicit branches. Neighboring 6.8 solid/hyphen/separate spelling and 6.11 "
                "service-word spelling are not admitted as independent mastery surfaces."
            ),
        },
        "source_frontier_dependency": {
            "status": frontier["status"],
            "frontier_sha256": normalized_sha(frontier),
            "source_bound_candidate_count": len(EXPECTED_FRONTIER_CANDIDATES),
            "source_bound_candidate_refs": EXPECTED_FRONTIER_CANDIDATES,
            "legacy_placeholder_count": frontier["historical_overlay_truth"]["placeholder_count"],
        },
        "exact_owner_resolution": {
            "exact_owner_refs": exact_owner_refs,
            "exact_owner_count": len(exact_owner_refs),
            "exact_branch_owner_pair_count": len(exact_owner_branch_pairs),
            "rejected_source_bound_candidates": rejected_candidates,
            "unresolved_source_bound_candidates": [],
            "all_primary_authorities_present": all_primary_authorities_present,
            "owner_rows": exact_owner_rows,
            "school_reopen_required": False,
            "new_school_identities_required": 0,
            "route_supersession_ready": True,
            "object_acceptance_ready": False,
            "component_evidence_required_before_object_acceptance": True,
        },
        "current_route_truth": {
            "current_route_refs": EXPECTED_CURRENT_ROUTE_REFS,
            "current_route_ref_count": 1,
            "missing_exact_owner_refs": missing_from_route,
            "missing_exact_owner_ref_count": len(missing_from_route),
            "route_mutated_by_this_review": False,
        },
        "mastery_boundary": {
            "exact_owner_resolution_is_not_semantic_admission": True,
            "exact_owner_resolution_is_not_object_acceptance": True,
            "generic_route_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
        },
        "safety": {
            "semantic_admissions": 0,
            "object_closures": 0,
            "requirements_closed": 0,
            "new_school_identities": 0,
            "false_exact_mastery": 0,
            "learner_audio_persistence": 0,
            "accepted_demo_or_scorer_change": False,
            "tilda_change": False,
            "production_peis_write": False,
            "provider_execution": False,
            "public_traffic": False,
            "real_payment_or_refund": False,
            "real_message_delivery": False,
        },
        "next": (
            "If this review is green on the exact PR head, create a bounded current-route supersession "
            "using exactly these 14 current canonical owners and no others. Do not admit the 6.9 object "
            "until component-specific independent learner evidence has passed a separate fail-closed audit."
        ),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    review = build_review()
    emitted = json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(emitted, encoding="utf-8")
    digest = normalized_sha(review)

    resolution = review["exact_owner_resolution"]
    route = review["current_route_truth"]
    safety = review["safety"]

    print("OGE_6_9_NE_NI_EXACT_OWNER_RESOLUTION=PASS")
    print(f"OFFICIAL_BRANCHES={review['official_source']['branch_count']}")
    print(f"SOURCE_BOUND_CANDIDATES={review['source_frontier_dependency']['source_bound_candidate_count']}")
    print(f"EXACT_OWNERS={resolution['exact_owner_count']}")
    print(f"EXACT_BRANCH_OWNER_PAIRS={resolution['exact_branch_owner_pair_count']}")
    print(f"REJECTED_CANDIDATES={len(resolution['rejected_source_bound_candidates'])}")
    print(f"UNRESOLVED_CANDIDATES={len(resolution['unresolved_source_bound_candidates'])}")
    print(f"PRIMARY_AUTHORITIES_PRESENT={int(resolution['all_primary_authorities_present'])}")
    print(f"CURRENT_ROUTE_REFS={route['current_route_ref_count']}")
    print(f"MISSING_EXACT_OWNER_REFS={route['missing_exact_owner_ref_count']}")
    print(f"ROUTE_SUPERSESSION_READY={int(resolution['route_supersession_ready'])}")
    print(f"OBJECT_ACCEPTANCE_READY={int(resolution['object_acceptance_ready'])}")
    print(f"SEMANTIC_ADMISSIONS={safety['semantic_admissions']}")
    print(f"OBJECT_CLOSURES={safety['object_closures']}")
    print(f"NEW_SCHOOL_IDENTITIES={safety['new_school_identities']}")
    print(f"FALSE_EXACT_MASTERY={safety['false_exact_mastery']}")
    print(f"LEARNER_AUDIO_PERSISTENCE={safety['learner_audio_persistence']}")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
