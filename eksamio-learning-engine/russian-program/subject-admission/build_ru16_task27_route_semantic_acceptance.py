#!/usr/bin/env python3
"""Build the first bounded RU16 Task-27 route-semantic acceptance slice.

This does not mutate the frozen 185-school canonical registry. It admits only
four EGE Task-27 route semantics (K1, the two independently assessable K2
components, and K3) where all of the following agree:
- final FIPI 2026 Task-27 route authority;
- official FIPI 2026 criteria within that route;
- current source-verified EGE taxonomy nodes / draft subject candidates;
- the already materialized original Eksamio learner-content bundle.

K4 remains unaccepted because candidate-054 still has an explicit granularity
review flag. K5/K6 and K7-K10 remain separate later decisions. Tier-B criterion
detail refines the already proven Task-27 route scope and may not expand it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
TASK_RELATION = ENGINE / "russian-program/ege-task-code-relation/FIPI-EGE-2026-TASK-CODE-RELATION-v1.0.json"
CRITERIA = ENGINE / "53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
CONTENT = ENGINE / "russian-program/production-learning-content/RU-PROG-16-EGE-ESSAY-WAVE-001-v0.1.json"

EXPECTED_SPEC_SHA = "3b71ec81f954bc32b574a0b3b997ee37bb3bc19ae8825f11217fd7149198b476"
ACCEPTED = {
    "candidate-048": {
        "source_id": "author_position_formulation",
        "semantic_id": "ru-ege-essay-author-position",
        "criterion": "K1",
        "label": "Формулирование позиции автора по проблеме исходного текста",
    },
    "candidate-049": {
        "source_id": "textual_comment_examples",
        "semantic_id": "ru-ege-essay-source-examples-explanation",
        "criterion": "K2",
        "label": "Выбор и пояснение двух примеров-иллюстраций из исходного текста",
    },
    "candidate-050": {
        "source_id": "example_relation_explanation",
        "semantic_id": "ru-ege-essay-example-semantic-relation",
        "criterion": "K2",
        "label": "Определение и пояснение смысловой связи между примерами",
    },
    "candidate-051": {
        "source_id": "own_position_argumentation",
        "semantic_id": "ru-ege-essay-own-relation-justification",
        "criterion": "K3",
        "label": "Формулирование и обоснование собственного отношения к позиции автора",
    },
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _objects(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    rows = inventory.get("objects")
    if not isinstance(rows, list):
        raise ValueError("semantic inventory objects missing")
    return [row for row in rows if isinstance(row, dict)]


def _task_locator(task27: dict[str, Any]) -> str:
    return (
        f"printed_page={task27['printed_page']};pdf_page={task27['pdf_page']};"
        f"panel={task27['panel']};task={task27['task']}"
    )


def build_acceptance() -> dict[str, Any]:
    relation = json.loads(TASK_RELATION.read_text(encoding="utf-8"))
    criteria = json.loads(CRITERIA.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    objects = _objects(inventory)

    if relation.get("status") != "OFFICIAL_FIPI_EGE_2026_TASK_TO_CODE_RELATION":
        raise ValueError("official Task-27 route authority is not current")
    if relation.get("relation_policy", {}).get("semantic_admission_implied") is not False:
        raise ValueError("task-code relation must not self-admit semantics")
    source = relation.get("source")
    if not isinstance(source, dict) or source.get("source_id") != "FIPI-EGE-RU-2026-FINAL" or source.get("document_id") != "EGE_SPEC":
        raise ValueError("official Task-27 source identity drift")
    if source.get("sha256") != EXPECTED_SPEC_SHA:
        raise ValueError("Task-27 FIPI specification fingerprint drift")
    task_rows = [row for row in relation.get("rows", []) if row.get("task") == 27]
    if len(task_rows) != 1:
        raise ValueError("Task 27 must have exactly one official relation row")
    task27 = task_rows[0]
    if (
        task27.get("printed_page") != 20
        or task27.get("pdf_page") != 10
        or task27.get("panel") != "right"
        or task27.get("max_primary_score") != 22
    ):
        raise ValueError("Task-27 page/panel/score authority drift")
    if set(task27.get("content_code_expressions") or []) != {"1.4", "1.5"}:
        raise ValueError("Task-27 content-code scope drift")
    if set(task27.get("requirement_code_expressions") or []) != {"1.5", "1.7"}:
        raise ValueError("Task-27 requirement-code scope drift")
    locator = _task_locator(task27)

    if criteria.get("task_number") != 27 or criteria.get("criteria_year") != 2026 or criteria.get("max_score") != 22:
        raise ValueError("official Task-27 criteria route drift")
    official_source = criteria.get("official_source")
    if not isinstance(official_source, dict) or official_source.get("publisher") != "ФГБНУ ФИПИ":
        raise ValueError("Task-27 criteria source is not FIPI")
    criterion_rows = {str(row.get("id")): row for row in criteria.get("criteria", []) if isinstance(row, dict)}
    if set(criterion_rows) != {f"K{i}" for i in range(1, 11)}:
        raise ValueError("Task-27 criteria must remain K1..K10")
    if sum(int(row.get("max_points", 0)) for row in criterion_rows.values()) != 22:
        raise ValueError("Task-27 criterion maxima no longer sum to 22")

    k1 = criterion_rows["K1"]
    k2 = criterion_rows["K2"]
    k3 = criterion_rows["K3"]
    if k1.get("title") != "Отражение позиции автора (рассказчика) по указанной проблеме":
        raise ValueError("K1 official meaning drift")
    if k3.get("title") != "Собственное отношение к позиции автора (рассказчика) и его обоснование":
        raise ValueError("K3 official meaning drift")
    if k2.get("title") != "Комментарий к позиции автора (рассказчика)":
        raise ValueError("K2 official meaning drift")
    top_k2 = next((row for row in k2.get("scale", []) if row.get("points") == 3), None)
    condition = str((top_k2 or {}).get("condition", ""))
    if "2 relevant text examples" not in condition or "semantic relation named and explained" not in condition:
        raise ValueError("K2 no longer proves both independently assessed components")

    candidate_bindings = {
        str(row.get("candidate_ref")): row
        for row in content.get("candidate_bindings", [])
        if isinstance(row, dict)
    }
    units = {
        str(row.get("proposed_semantic_id")): row
        for row in content.get("units", [])
        if isinstance(row, dict)
    }
    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("RU16 learner content must remain fail-closed before this overlay")

    decisions: list[dict[str, Any]] = []
    for candidate_ref, expected in ACCEPTED.items():
        semantic_id = str(expected["semantic_id"])
        source_id = str(expected["source_id"])
        criterion = str(expected["criterion"])
        label = str(expected["label"])

        candidate_rows = [row for row in objects if row.get("object_key") == f"semantic_candidate::{candidate_ref}"]
        if len(candidate_rows) != 1:
            raise ValueError(f"candidate object mismatch: {candidate_ref}")
        candidate = candidate_rows[0]
        if candidate.get("authority_status") != "current":
            raise ValueError(f"candidate not current: {candidate_ref}")
        if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
            raise ValueError(f"candidate classification drift: {candidate_ref}")
        if candidate.get("observed_label") != label:
            raise ValueError(f"candidate exact label drift: {candidate_ref}")
        if candidate.get("current_semantic_refs") != [source_id]:
            raise ValueError(f"candidate semantic-ref drift: {candidate_ref}")

        taxonomy_rows = [
            row for row in objects
            if row.get("candidate_canonical_owner") == candidate_ref
            and row.get("source_id") == source_id
            and row.get("audit_classification") == "EGE_TAXONOMY_NODE"
        ]
        if len(taxonomy_rows) != 1:
            raise ValueError(f"source-verified taxonomy node mismatch: {candidate_ref}")
        taxonomy = taxonomy_rows[0]
        if taxonomy.get("authority_status") != "current" or taxonomy.get("review_status") != "source_verified":
            raise ValueError(f"taxonomy evidence not current/source-verified: {candidate_ref}")
        provenance = f"03-RUSSIAN-SKILL-GRAPH.json#skills[{source_id}]"
        if provenance not in set(taxonomy.get("evidence_provenance_refs") or []):
            raise ValueError(f"taxonomy provenance drift: {candidate_ref}")

        binding = candidate_bindings.get(candidate_ref)
        if not isinstance(binding, dict) or binding.get("proposed_semantic_id") != semantic_id:
            raise ValueError(f"learner-content candidate binding drift: {candidate_ref}")
        expected_route = "K2_COMPONENT" if criterion == "K2" else criterion
        if binding.get("criterion_route") != expected_route:
            raise ValueError(f"criterion binding drift: {candidate_ref}")
        unit = units.get(semantic_id)
        if not isinstance(unit, dict) or unit.get("candidate_ref") != candidate_ref:
            raise ValueError(f"learner-content unit missing: {semantic_id}")
        if not isinstance(unit.get("independent_verification"), list) or len(unit["independent_verification"]) < 2:
            raise ValueError(f"independent verification incomplete: {semantic_id}")

        decisions.append(
            {
                "candidate_ref": candidate_ref,
                "source_taxonomy_id": source_id,
                "accepted_semantic_id": semantic_id,
                "label_ru": label,
                "route": "EGE_2026_TASK_27",
                "criterion_route": criterion,
                "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_BOUNDED_ROUTE_SEMANTIC",
                "content_ref": "russian-program/production-learning-content/RU-PROG-16-EGE-ESSAY-WAVE-001-v0.1.json",
                "authority": {
                    "tier_a_route_scope": "FIPI-EGE-2026-TASK-CODE-RELATION-v1.0.json#task=27",
                    "tier_a_source_sha256": EXPECTED_SPEC_SHA,
                    "tier_a_source_locator": locator,
                    "tier_a_content_codes": list(task27["content_code_expressions"]),
                    "tier_a_requirement_codes": list(task27["requirement_code_expressions"]),
                    "tier_b_component_boundary": f"53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json#criteria[{criterion}]",
                    "source_verified_taxonomy": provenance,
                },
                "acceptance_reason": "The component is inside the final FIPI Task-27 route scope, the official 2026 criterion describes the same bounded learner operation, the current EGE taxonomy node is source-verified, and an original Eksamio learner unit with independent verification exists. Tier-B detail refines but does not expand the Tier-A Task-27 scope.",
                "mastery_boundary": {
                    "generic_essay_attempt_can_emit_exact_component_mastery": False,
                    "component_specific_independent_evidence_required": True,
                    "criterion_score_is_route_evidence_not_semantic_mastery": True,
                },
            }
        )

    if {row["accepted_semantic_id"] for row in decisions} != {str(row["semantic_id"]) for row in ACCEPTED.values()}:
        raise ValueError("accepted RU16 semantic set drift")
    if len(decisions) != 4:
        raise ValueError("first RU16 bounded acceptance slice must contain exactly four semantics")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_ACCEPTED_RU16_TASK27_K1_K3_ROUTE_SEMANTICS",
        "scope": "EGE_2026_TASK_27_K1_K3_WITH_K2_DECOMPOSED",
        "canonical_school_registry_mutated": False,
        "new_parallel_registry_created": False,
        "policy": {
            "tier_a_route_scope_required": True,
            "tier_b_may_refine_but_not_expand_tier_a": True,
            "source_verified_taxonomy_required": True,
            "production_learner_content_required": True,
            "k2_components_remain_separate": True,
            "criterion_score_implies_semantic_mastery": False,
            "k4_k6_admitted_by_this_slice": False,
            "k7_k10_admitted_by_this_slice": False,
            "candidate_053_general_essay_role": False,
        },
        "summary": {
            "accepted_route_semantics": 4,
            "accepted_criteria_routes": 3,
            "k2_semantic_components": 2,
            "new_school_canonical_identities": 0,
            "accepted_ru_route_semantics": 4,
            "k4_k6_acceptances": 0,
            "k7_k10_acceptances": 0,
            "false_exact_mastery_admissions": 0,
        },
        "decisions": sorted(decisions, key=lambda row: row["candidate_ref"]),
        "remaining_ru16_subject_decisions": [
            "candidate-054 / K4 factual accuracy: granularity remains needs_review",
            "candidate-052 / K5 logic-composition-cohesion: bounded acceptance remains pending",
            "candidate-055 / K6 ethical norm: bounded acceptance remains pending",
            "K7 orthography: bind exact accepted RU-PROG-08 components",
            "K8 punctuation: bind exact accepted RU-PROG-10 components",
            "K9 grammar: bind exact accepted RU-PROG-07/RU-PROG-09 components; candidate-053 is not a general owner",
            "K10 speech norms: bind exact accepted RU-PROG-14 components",
        ],
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_acceptance()
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RU16_TASK27_BOUNDED_ROUTE_SEMANTIC_ACCEPTANCE=PASS")
        for key, value in result["summary"].items():
            print(f"{key}={value}")
        print("accepted_semantic_ids=" + ",".join(row["accepted_semantic_id"] for row in result["decisions"]))
        print(f"NORMALIZED_ACCEPTANCE_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
