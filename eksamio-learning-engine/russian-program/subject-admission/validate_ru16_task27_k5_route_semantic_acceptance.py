#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
ACCEPTANCE = HERE / "RU16-TASK27-K5-BOUNDED-ROUTE-SEMANTIC-ACCEPTANCE-v0.1.json"
RELATION = ENGINE / "russian-program/ege-task-code-relation/FIPI-EGE-2026-TASK-CODE-RELATION-v1.0.json"
CRITERIA = ENGINE / "53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
CONTENT = ENGINE / "russian-program/production-learning-content/RU-PROG-16-EGE-ESSAY-WAVE-001-v0.1.json"
SPEC_SHA = "3b71ec81f954bc32b574a0b3b997ee37bb3bc19ae8825f11217fd7149198b476"


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    relation = json.loads(RELATION.read_text(encoding="utf-8"))
    criteria = json.loads(CRITERIA.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU16_TASK27_K5_ROUTE_SEMANTIC":
        raise AssertionError("K5 acceptance status drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("K5 acceptance must remain an overlay")
    decision = acceptance.get("decision", {})
    if decision != {
        "candidate_ref": "candidate-052",
        "source_taxonomy_id": "essay_composition_coherence",
        "accepted_semantic_id": "ru-ege-essay-logical-composition-cohesion",
        "label_ru": "Логичная композиция, связность и последовательность сочинения",
        "criterion_route": "K5",
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_BOUNDED_ROUTE_SEMANTIC",
        "content_ref": "russian-program/production-learning-content/RU-PROG-16-EGE-ESSAY-WAVE-001-v0.1.json",
    }:
        raise AssertionError("K5 bounded decision drift")

    source = relation.get("source", {})
    task27 = next((row for row in relation.get("rows", []) if row.get("task") == 27), None)
    if source.get("source_id") != "FIPI-EGE-RU-2026-FINAL" or source.get("document_id") != "EGE_SPEC" or source.get("sha256") != SPEC_SHA:
        raise AssertionError("K5 Task27 Tier-A source drift")
    if not isinstance(task27, dict) or (task27.get("printed_page"), task27.get("pdf_page"), task27.get("panel"), task27.get("max_primary_score")) != (20, 10, "right", 22):
        raise AssertionError("K5 Task27 route locator/score drift")

    k5 = next((row for row in criteria.get("criteria", []) if row.get("id") == "K5"), None)
    if not isinstance(k5, dict) or k5.get("title") != "Логичность речи" or k5.get("max_points") != 2:
        raise AssertionError("official K5 criterion drift")
    checks = set(k5.get("learner_checks") or [])
    required_checks = {
        "Нет противоречий между частями рассуждения.",
        "Переходы между абзацами и тезисами понятны.",
        "Выводы следуют из приведённых доводов.",
    }
    if checks != required_checks:
        raise AssertionError("official K5 logicality boundary drift")

    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    candidate = [row for row in objects if row.get("object_key") == "semantic_candidate::candidate-052"]
    taxonomy = [row for row in objects if row.get("candidate_canonical_owner") == "candidate-052" and row.get("source_id") == "essay_composition_coherence" and row.get("audit_classification") == "EGE_TAXONOMY_NODE"]
    if len(candidate) != 1 or len(taxonomy) != 1:
        raise AssertionError("candidate-052 taxonomy evidence mismatch")
    if candidate[0].get("authority_status") != "current" or candidate[0].get("current_semantic_refs") != ["essay_composition_coherence"]:
        raise AssertionError("candidate-052 semantic candidate drift")
    if candidate[0].get("observed_label") != "Логичная композиция, связность и последовательность сочинения":
        raise AssertionError("candidate-052 exact label drift")
    if taxonomy[0].get("authority_status") != "current" or taxonomy[0].get("review_status") != "source_verified":
        raise AssertionError("candidate-052 taxonomy is not source-verified")
    if "03-RUSSIAN-SKILL-GRAPH.json#skills[essay_composition_coherence]" not in set(taxonomy[0].get("evidence_provenance_refs") or []):
        raise AssertionError("candidate-052 taxonomy provenance drift")

    bindings = [row for row in content.get("candidate_bindings", []) if row.get("candidate_ref") == "candidate-052"]
    units = [row for row in content.get("units", []) if row.get("proposed_semantic_id") == "ru-ege-essay-logical-composition-cohesion"]
    if len(bindings) != 1 or bindings[0].get("criterion_route") != "K5" or len(units) != 1:
        raise AssertionError("K5 learner-content binding drift")
    unit = units[0]
    text = json.dumps(unit, ensure_ascii=False).casefold()
    for stem in ("противореч", "переход", "вывод", "последователь"):
        if stem not in text:
            raise AssertionError(f"K5 learner content lacks logical-coherence boundary: {stem}")
    if not isinstance(unit.get("independent_verification"), list) or len(unit["independent_verification"]) < 2:
        raise AssertionError("K5 independent verification incomplete")

    mastery = acceptance.get("mastery_boundary", {})
    if mastery.get("k5_score_alone_implies_exact_semantic_mastery") is not False or mastery.get("component_specific_independent_evidence_required") is not True or mastery.get("generic_essay_attempt_can_emit_exact_component_mastery") is not False:
        raise AssertionError("K5 mastery boundary weakened")
    summary = acceptance.get("summary", {})
    if summary != {"accepted_route_semantics": 1, "accepted_ru_route_semantics": 1, "new_school_canonical_identities": 0, "object_level_admission_units_closed": 0, "false_exact_mastery_admissions": 0}:
        raise AssertionError("K5 acceptance summary drift")

    print("RU16_TASK27_K5_BOUNDED_ROUTE_SEMANTIC_ACCEPTANCE=PASS")
    print("ACCEPTED_ROUTE_SEMANTICS=1")
    print("ACCEPTED_SEMANTIC_ID=ru-ege-essay-logical-composition-cohesion")
    print("OBJECT_LEVEL_ADMISSION_UNITS_CLOSED=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
