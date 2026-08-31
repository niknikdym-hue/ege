#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

SKILL_GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
BOUNDARY = HERE / "RU03-LEXIS-CANDIDATE-BOUNDARY-REVIEW-v0.1.json"
REVIEW = HERE / "RU03-PHRASEOLOGISM-IDENTIFICATION-CONTENT-ADEQUACY-REVIEW-v0.1.json"
OLD_CONTENT = PROGRAM / "production-learning-content/RU-PROG-03-LEXIS-PARONYMS-PHRASEOLOGY-WAVE-002-v0.1.json"
NEW_CONTENT = PROGRAM / "production-learning-content/RU-PROG-03-PHRASEOLOGISM-IDENTIFICATION-WAVE-007-v0.1.json"

CANDIDATE = "candidate-014"
TAXONOMY = "phraseologism_identification"
SEMANTIC = "ru-lexis-phraseologism-fragment-identification"
OLD_SEMANTIC = "ru-lexis-phraseology-free-combination"
LABEL = "Поиск фразеологизма в заданном фрагменте текста"


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    graph = load(SKILL_GRAPH)
    inventory = load(INVENTORY)
    boundary = load(BOUNDARY)
    review = load(REVIEW)
    old_content = load(OLD_CONTENT)
    new_content = load(NEW_CONTENT)

    skill = one(
        [r for r in graph.get("skills", []) if isinstance(r, dict) and r.get("skill_id") == TAXONOMY],
        "phraseologism skill graph row",
    )
    if skill.get("name_ru") != LABEL or skill.get("description") != f"{LABEL}.":
        raise AssertionError("candidate-014 skill label/meaning drift")
    if skill.get("parent_skill_id") != "lexical_norms_and_semantics":
        raise AssertionError("candidate-014 skill parent drift")
    if skill.get("evidence_status") != "confirmed":
        raise AssertionError("candidate-014 source evidence is not confirmed")

    candidate = one(
        [
            r
            for r in inventory.get("objects", [])
            if isinstance(r, dict) and r.get("object_key") == f"semantic_candidate::{CANDIDATE}"
        ],
        "candidate-014 inventory row",
    )
    if candidate.get("source_system") != "semantic_candidate" or candidate.get("source_id") != CANDIDATE:
        raise AssertionError("candidate-014 inventory identity drift")
    if candidate.get("authority_status") != "current":
        raise AssertionError("candidate-014 inventory is not current")
    if candidate.get("observed_label") != LABEL or candidate.get("observed_meaning") != f"{LABEL}.":
        raise AssertionError("candidate-014 inventory meaning drift")
    if candidate.get("current_semantic_refs") != [TAXONOMY]:
        raise AssertionError("candidate-014 inventory source ref drift")
    if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
        raise AssertionError("candidate-014 is no longer a missing-subject candidate")
    if candidate.get("candidate_canonical_owner") != CANDIDATE:
        raise AssertionError("candidate-014 canonical owner drift")
    if candidate.get("needs_review_reason") is not None:
        raise AssertionError("candidate-014 unexpectedly needs source review")

    boundary_row = one(
        [r for r in boundary.get("candidate_review", []) if isinstance(r, dict) and r.get("candidate_ref") == CANDIDATE],
        "candidate-014 boundary row",
    )
    if boundary_row.get("source_taxonomy_id") != TAXONOMY:
        raise AssertionError("candidate-014 boundary taxonomy drift")
    if boundary_row.get("skill_graph_evidence_status") != "confirmed":
        raise AssertionError("candidate-014 boundary evidence drift")
    if boundary_row.get("learner_content_ref") != OLD_SEMANTIC:
        raise AssertionError("candidate-014 reuse-first old content ref drift")
    if boundary_row.get("content_boundary") != "BROADER_THAN_EXACT_CANDIDATE_TRAINS_PHRASEOLOGISM_VS_FREE_COMBINATION_NOT_ONLY_IDENTIFICATION_IN_FRAGMENT":
        raise AssertionError("candidate-014 broader-than-exact boundary drift")
    if boundary_row.get("disposition") != "REVIEWED_NOT_ADMITTED":
        raise AssertionError("candidate-014 boundary must remain non-admitting")

    old_unit = one(
        [r for r in old_content.get("units", []) if isinstance(r, dict) and r.get("proposed_semantic_id") == OLD_SEMANTIC],
        "existing broader phraseology unit",
    )
    if old_unit.get("title_ru") != "Фразеологизм и свободное сочетание":
        raise AssertionError("existing broader phraseology unit drift")

    if new_content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise AssertionError("new phraseologism content must remain subject-acceptance required")
    if new_content.get("subject") != "russian" or new_content.get("module_id") != "RU-PROG-03":
        raise AssertionError("new phraseologism content module drift")
    guard = new_content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes") != 0:
        raise AssertionError("candidate-014 content copied protected source bytes")
    if guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("candidate-014 learner examples are not marked original")

    units = [r for r in new_content.get("units", []) if isinstance(r, dict)]
    if len(units) != 1:
        raise AssertionError("candidate-014 content wave must contain exactly one bounded unit")
    unit = units[0]
    if unit.get("proposed_semantic_id") != SEMANTIC:
        raise AssertionError("candidate-014 proposed semantic drift")
    if unit.get("candidate_ref") != CANDIDATE or unit.get("source_taxonomy_id") != TAXONOMY:
        raise AssertionError("candidate-014 learner crosswalk drift")
    if unit.get("title_ru") != LABEL:
        raise AssertionError("candidate-014 learner title drift")
    if SEMANTIC == OLD_SEMANTIC:
        raise AssertionError("candidate-014 exact unit illegally reuses broader semantic id")

    explanation = unit.get("canonical_explanation") or {}
    short = str(explanation.get("short") or "").lower()
    boundaries = "\n".join(str(v).lower() for v in explanation.get("boundaries", []))
    for token in ("заданном фрагмент", "точную последовательность", "границ"):
        if token not in short + "\n" + boundaries:
            raise AssertionError(f"candidate-014 exact explanation missing token: {token}")
    for token in ("generic task-25", "contextual synonym", "свобод"):
        if token not in boundaries:
            raise AssertionError(f"candidate-014 exclusion boundary missing token: {token}")

    required_minimums = {
        "decision_algorithm": 5,
        "worked_examples": 4,
        "misconceptions": 4,
        "guided_practice": 2,
        "independent_practice": 4,
        "mixed_transfer_practice": 2,
        "retention_items": 2,
        "independent_verification": 2,
    }
    for key, minimum in required_minimums.items():
        value = unit.get(key)
        if not isinstance(value, list) or len(value) < minimum:
            raise AssertionError(f"candidate-014 learner content too thin: {key}")

    verification = unit["independent_verification"]
    ids = [row.get("id") for row in verification if isinstance(row, dict)]
    if len(ids) != len(set(ids)) or any(not value for value in ids):
        raise AssertionError("candidate-014 independent verification ids invalid")
    if {row.get("type") for row in verification} != {"single_choice", "constructed_response"}:
        raise AssertionError("candidate-014 independent verification modes drift")

    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError("candidate-014 content self-admitted semantic")
    if peis.get("independent_verification_required") is not True:
        raise AssertionError("candidate-014 independent verification not required")
    if peis.get("assistance_must_be_recorded") is not True:
        raise AssertionError("candidate-014 assistance recording weakened")
    if peis.get("generic_task_result_can_emit_exact_mastery") is not False:
        raise AssertionError("candidate-014 generic task mastery leakage")
    if peis.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("candidate-014 content object-binding drift")

    tutor = unit.get("tutor_grounding") or {}
    allowed = "\n".join(str(v).lower() for v in tutor.get("allowed", []))
    forbidden = "\n".join(str(v).lower() for v in tutor.get("forbidden", []))
    if "exact word boundaries" not in allowed or "supplied fragment" not in allowed:
        raise AssertionError("candidate-014 tutor grounding not exact enough")
    if "contextual_synonym_selection" not in forbidden or "generic task-25" not in forbidden:
        raise AssertionError("candidate-014 tutor exclusion drift")

    if review.get("status") != "CENTRAL_BRAIN_RU03_PHRASEOLOGISM_IDENTIFICATION_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("candidate-014 review status drift")
    if review.get("authority_issue") != 161:
        raise AssertionError("candidate-014 review authority issue drift")
    source = review.get("source_identity") or {}
    if (
        source.get("candidate_ref") != CANDIDATE
        or source.get("source_taxonomy_id") != TAXONOMY
        or source.get("label_ru") != LABEL
        or source.get("skill_graph_evidence_status") != "confirmed"
        or source.get("inventory_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE"
    ):
        raise AssertionError("candidate-014 review source truth drift")
    reuse = review.get("reuse_first_result") or {}
    if reuse.get("existing_content_reused_as_exact_candidate_unit") is not False:
        raise AssertionError("candidate-014 broader unit incorrectly reused as exact")
    if reuse.get("existing_content_boundary") != boundary_row.get("content_boundary"):
        raise AssertionError("candidate-014 reuse-first boundary mismatch")
    learner = review.get("learner_content") or {}
    if learner.get("proposed_semantic_id") != SEMANTIC:
        raise AssertionError("candidate-014 review learner semantic drift")
    if learner.get("independent_verification_present") is not True:
        raise AssertionError("candidate-014 review independent verification drift")
    if learner.get("assistance_recording_required") is not True or learner.get("tutor_grounding_bounded") is not True:
        raise AssertionError("candidate-014 review evidence controls drift")
    decision = review.get("review_decision") or {}
    if decision.get("content_exact_for_candidate_014") is not True:
        raise AssertionError("candidate-014 content not accepted as exact")
    if decision.get("content_duplicate_of_existing_ru03_unit") is not False:
        raise AssertionError("candidate-014 exact unit duplicate flag drift")
    if decision.get("exact_school_meaning_collision_observed") is not False:
        raise AssertionError("candidate-014 exact school meaning collision observed")
    if decision.get("semantic_admission_by_this_review") is not False:
        raise AssertionError("candidate-014 content review must not admit semantic")
    if decision.get("object_level_admission_units_closed") != 0 or decision.get("object_level_requirements_closed") != 0:
        raise AssertionError("candidate-014 content review falsely closed objects")
    if decision.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("candidate-014 content review false mastery")
    if decision.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise AssertionError("candidate-014 next status drift")

    digest = hashlib.sha256(
        json.dumps(review, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print("RU03_PHRASEOLOGISM_IDENTIFICATION_CONTENT_ADEQUACY=PASS")
    print(f"CANDIDATE={CANDIDATE}")
    print(f"PROPOSED_SEMANTIC={SEMANTIC}")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
