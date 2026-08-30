#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
SKILL_GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
WAVE2 = ENGINE / "48-RUSSIAN-EXCEPTIONS-WAVE2-NORMS-v0.1.json"

CANDIDATE = "candidate-015"
TAXONOMY = "contextual_synonym_selection"
LABEL = "Подбор контекстного синонима к слову исходного текста"
MEANING = "Подбор контекстного синонима к слову исходного текста."
OFFICIAL_URL = "https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-2-leksika-i-frazeologija.pdf"
OFFICIAL_LOCATOR = "Навигатор самостоятельной подготовки к ЕГЭ 2026 — Русский язык — Лексика и фразеология, p.12 (PDF page index 11)"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def norm(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise ValueError(f"{label}: expected exactly one row, got {len(rows)}")
    return rows[0]


def build_resolution() -> dict[str, Any]:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(SKILL_GRAPH.read_text(encoding="utf-8"))
    wave2 = json.loads(WAVE2.read_text(encoding="utf-8"))

    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    skills = [row for row in graph.get("skills", []) if isinstance(row, dict)]
    items = [row for row in wave2.get("items", []) if isinstance(row, dict)]

    candidate = one(
        [
            row for row in objects
            if row.get("source_system") == "semantic_candidate"
            and row.get("source_id") == CANDIDATE
            and row.get("authority_status") == "current"
        ],
        "candidate-015 current inventory",
    )
    if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
        raise ValueError("candidate-015 is no longer a missing subject semantic candidate")
    if candidate.get("candidate_canonical_owner") != CANDIDATE:
        raise ValueError("candidate-015 owner drift")
    if candidate.get("current_semantic_refs") != [TAXONOMY]:
        raise ValueError("candidate-015 taxonomy ref drift")
    if candidate.get("observed_label") != LABEL or norm(candidate.get("observed_meaning")) != norm(MEANING):
        raise ValueError("candidate-015 label/meaning drift")
    if candidate.get("review_status") != "needs_review":
        raise ValueError("candidate-015 prerequisite needs_review state drift")

    backing = one(
        [
            row for row in objects
            if row.get("source_system") == "ege_skill_graph"
            and row.get("source_id") == TAXONOMY
            and row.get("authority_status") == "current"
            and row.get("candidate_canonical_owner") == CANDIDATE
        ],
        "candidate-015 skill-graph inventory backing",
    )
    if backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise ValueError("candidate-015 backing classification drift")
    if backing.get("review_status") != "needs_review":
        raise ValueError("candidate-015 backing prerequisite review state drift")
    if norm(backing.get("observed_meaning")) != norm(MEANING):
        raise ValueError("candidate-015 backing meaning drift")

    skill = one([row for row in skills if row.get("skill_id") == TAXONOMY], "contextual synonym skill node")
    if skill.get("name_ru") != LABEL or norm(skill.get("description")) != norm(MEANING):
        raise ValueError("contextual synonym skill label/meaning drift")
    if skill.get("parent_skill_id") != "lexical_norms_and_semantics":
        raise ValueError("contextual synonym parent drift")
    if skill.get("exam_task_numbers") != [25]:
        raise ValueError("contextual synonym Task-25 route drift")
    if skill.get("evidence_status") != "needs_review":
        raise ValueError("contextual synonym prerequisite evidence state drift")

    historical = one(
        [row for row in items if row.get("exception_id") == "task25_historical_synonym_not_current_phraseology"],
        "historical Task-25 synonym exception",
    )
    if historical.get("status") != "source_verified":
        raise ValueError("historical Task-25 exception source status drift")
    if TAXONOMY not in set(historical.get("subskill_ids") or []):
        raise ValueError("historical Task-25 exception taxonomy drift")

    exact_school_meaning = [
        row for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and norm(row.get("observed_meaning")) == norm(MEANING)
    ]
    if exact_school_meaning:
        raise ValueError("exact school-canonical contextual-synonym meaning already exists; reuse required")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU03_CONTEXTUAL_SYNONYM_CURRENT_2026_SOURCE_IDENTITY_RESOLVED_NO_ADMISSION",
        "authority_issue": 161,
        "module_id": "RU-PROG-03",
        "candidate_ref": CANDIDATE,
        "source_taxonomy_id": TAXONOMY,
        "label_ru": LABEL,
        "meaning_ru": MEANING,
        "repository_prerequisite_truth": {
            "candidate_review_status": "needs_review",
            "skill_graph_evidence_status": "needs_review",
            "historical_exception_id": "task25_historical_synonym_not_current_phraseology",
            "historical_exception_disposition": "PRESERVED_AS_HISTORICAL_PRODUCT_EVIDENCE_NOT_USED_AS_CURRENT_2026_NEGATIVE_AUTHORITY",
            "base_graph_or_inventory_mutated": False,
        },
        "current_official_source_resolution": {
            "authority": "FGBNU FIPI",
            "document": "Navigator samostoyatelnoy podgotovki k EGE 2026 — Russkiy yazyk — Leksika i frazeologiya",
            "url": OFFICIAL_URL,
            "locator": OFFICIAL_LOCATOR,
            "checked_on": "2026-08-30",
            "verification_mode": "CENTRAL_BRAIN_VISUAL_AND_TEXT_CHECK_OF_CURRENT_OFFICIAL_FIPI_PDF",
            "evidence": [
                "The current 2026 FIPI navigator explicitly defines contextual synonyms and antonyms as relations valid only inside the supplied text.",
                "The same current 2026 FIPI navigator explicitly states a Task-25 distinction between contextual and language-only synonyms/antonyms depending on whether the wording contains the contextual qualifier.",
                "Therefore contextual synonym selection is current Task-25 source scope in 2026 and is not limited to a historical-only exam format.",
            ],
            "source_identity_evidence_status": "confirmed",
        },
        "resolution": {
            "source_identity_status": "EXACT_CURRENT_2026_OFFICIAL_SOURCE_CONFIRMED",
            "prior_needs_review_state": "RESOLVED_BY_NEWER_EXPLICIT_CURRENT_OFFICIAL_FIPI_AUTHORITY",
            "historical_only_negative_inference": "SUPERSEDED_FOR_CURRENT_2026_SCOPE_ONLY",
            "taxonomy_identity_preserved": True,
            "candidate_identity_preserved": True,
            "task_number_is_semantic_identity": False,
            "semantic_admission_effect": "NONE",
            "object_binding_effect": "NONE",
        },
        "policy": {
            "source_resolution_is_subject_semantic_admission": False,
            "content_presence_alone_is_semantic_admission": False,
            "exact_original_learner_content_required_before_semantic_acceptance": True,
            "exact_school_meaning_collision_forbidden": True,
            "generic_task25_result_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
            "accepted_demos_or_scorers_may_change": False,
            "keyword_or_fuzzy_inference_allowed": False,
        },
        "summary": {
            "candidate_records_resolved": 1,
            "current_official_source_identities_confirmed": 1,
            "remaining_ru03_source_identity_needs_review_candidates": 0,
            "semantic_admissions": 0,
            "new_school_canonical_identities": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "false_exact_mastery_admissions": 0,
        },
        "next_exact_work": {
            "candidate_ref": CANDIDATE,
            "required_step": "EXACT_CONTENT_ADEQUACY_REVIEW_THEN_ORIGINAL_LEARNER_CONTENT_IF_GAP_THEN_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE",
            "semantic_admission_allowed_from_this_resolution_alone": False,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()

    result = build_resolution()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RU03_CONTEXTUAL_SYNONYM_SOURCE_IDENTITY_RESOLUTION=PASS")
        print("CURRENT_2026_OFFICIAL_SOURCE_IDENTITIES_CONFIRMED=1")
        print("REMAINING_RU03_SOURCE_IDENTITY_NEEDS_REVIEW_CANDIDATES=0")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_CLOSURES=0/0")
        print("FALSE_EXACT_MASTERY=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
