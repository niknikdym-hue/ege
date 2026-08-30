#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

REVIEW = HERE / "RU11-SEMANTIC-RELATION-CONTENT-ADEQUACY-REVIEW-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
BROADER = PROGRAM / "production-learning-content/RU-PROG-11-TEXT-COHESION-WAVE-002-v0.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-11-SEMANTIC-RELATION-WAVE-005-v0.1.json"

CANDIDATE = "candidate-047"
TAXONOMY = "semantic_relation_between_sentences"
SEMANTIC = "ru-text-semantic-relation-between-sentences"
SOURCE_LABEL = "Определение причинных, следственных, пояснительных и противительных отношений между предложениями"


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def has_relation_family(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return any(token in text for token in ("причин", "следств", "поясн", "против"))


def main() -> int:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    broader = json.loads(BROADER.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if review.get("status") != "CENTRAL_BRAIN_RU11_SEMANTIC_RELATION_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("RU11 semantic-relation content-review status drift")
    if review.get("authority_issue") != 161:
        raise AssertionError("RU11 semantic-relation authority issue drift")

    source = review.get("source_identity") or {}
    if (
        source.get("candidate_ref") != CANDIDATE
        or source.get("source_taxonomy_id") != TAXONOMY
        or source.get("label_ru") != SOURCE_LABEL
        or source.get("inventory_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE"
        or source.get("inventory_review_status") != "draft"
        or source.get("skill_graph_evidence_status") != "confirmed"
        or source.get("taxonomy_backing_review_status") != "source_verified"
        or source.get("exam_task_numbers") != [24]
    ):
        raise AssertionError("RU11 semantic-relation review source truth drift")

    objects = [r for r in inventory.get("objects", []) if isinstance(r, dict)]
    candidate = one(
        [
            r
            for r in objects
            if r.get("source_system") == "semantic_candidate"
            and r.get("source_id") == CANDIDATE
            and r.get("authority_status") == "current"
        ],
        "RU11 candidate-047 current inventory",
    )
    if (
        candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE"
        or candidate.get("candidate_canonical_owner") != CANDIDATE
        or candidate.get("current_semantic_refs") != [TAXONOMY]
        or candidate.get("review_status") != "draft"
        or candidate.get("observed_label") != SOURCE_LABEL
    ):
        raise AssertionError("RU11 candidate-047 inventory ownership/review boundary drift")

    backing = one(
        [
            r
            for r in objects
            if r.get("source_system") == "ege_skill_graph"
            and r.get("source_id") == TAXONOMY
            and r.get("authority_status") == "current"
            and r.get("candidate_canonical_owner") == CANDIDATE
        ],
        "RU11 candidate-047 taxonomy backing",
    )
    if backing.get("review_status") != "source_verified" or backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise AssertionError("RU11 candidate-047 taxonomy backing not source-verified")
    if normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU11 candidate-047 inventory/backing meaning mismatch")

    skill = one(
        [r for r in graph.get("skills", []) if isinstance(r, dict) and r.get("skill_id") == TAXONOMY],
        "RU11 candidate-047 graph node",
    )
    if (
        skill.get("evidence_status") != "confirmed"
        or skill.get("parent_skill_id") != "speech_type_analysis"
        or skill.get("exam_task_numbers") != [24]
        or skill.get("name_ru") != SOURCE_LABEL
        or normalized(skill.get("description")) != normalized(candidate.get("observed_meaning"))
    ):
        raise AssertionError("RU11 candidate-047 confirmed Task-24 graph boundary drift")

    if any(
        SEMANTIC in {str(ref) for ref in (r.get("current_semantic_refs") or [])}
        for r in objects
        if r.get("authority_status") == "current"
    ):
        raise AssertionError("RU11 semantic-relation proposed semantic id collides with current inventory")
    if any(
        r.get("source_system") == "school_canonical"
        and r.get("authority_status") == "current"
        and normalized(r.get("observed_meaning")) == normalized(candidate.get("observed_meaning"))
        for r in objects
    ):
        raise AssertionError("RU11 candidate-047 exact school meaning already exists; reuse required")

    reuse = review.get("reuse_first_review") or {}
    if (
        reuse.get("existing_unit_reused_for_explanation_and_boundary") is not True
        or reuse.get("existing_unit_exact_candidate_047_mastery") is not False
        or reuse.get("direct_relation_bearing_independent_checks_observed") != 1
    ):
        raise AssertionError("RU11 candidate-047 reuse-first review drift")

    broad_unit = one(
        [
            r
            for r in broader.get("units", [])
            if isinstance(r, dict) and r.get("proposed_semantic_id") == "ru-text-cohesion-link-means"
        ],
        "RU11 broader cohesion learner unit",
    )
    broad_checks = broad_unit.get("independent_verification") or []
    direct_relation_checks = sum(1 for row in broad_checks if isinstance(row, dict) and has_relation_family(row))
    if direct_relation_checks != 1:
        raise AssertionError(f"RU11 broader relation-bearing direct checks drift: {direct_relation_checks}")
    broad_v1 = one([r for r in broad_checks if isinstance(r, dict) and r.get("id") == "p11-u2-v1"], "RU11 broader v1")
    if "средств" not in json.dumps(broad_v1, ensure_ascii=False).lower():
        raise AssertionError("RU11 broader relation check is no longer coupled to link-means evidence")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-11":
        raise AssertionError("RU11 semantic-relation content status/module drift")
    provenance = content.get("source_provenance") or []
    draft_source = one(
        [r for r in provenance if isinstance(r, dict) and r.get("kind") == "current_draft_subject_semantic_candidate"],
        "RU11 semantic-relation draft source provenance",
    )
    if draft_source.get("review_status") != "draft" or draft_source.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
        raise AssertionError("RU11 semantic-relation content falsely upgrades draft source candidate")
    confirmed_source = one(
        [r for r in provenance if isinstance(r, dict) and r.get("kind") == "confirmed_skill_graph"],
        "RU11 semantic-relation confirmed graph provenance",
    )
    if confirmed_source.get("evidence_status") != "confirmed":
        raise AssertionError("RU11 semantic-relation graph evidence status drift")

    guard = content.get("copyright_guard") or {}
    if (
        guard.get("source_passages_copied") != 0
        or guard.get("commercial_textbook_bytes") != 0
        or guard.get("learner_examples") != "ORIGINAL_EKSAMIO"
    ):
        raise AssertionError("RU11 semantic-relation provenance boundary weakened")

    unit = one(
        [r for r in content.get("units", []) if isinstance(r, dict) and r.get("proposed_semantic_id") == SEMANTIC],
        "RU11 semantic-relation learner unit",
    )
    if unit.get("title_ru") != "Причинные, следственные, пояснительные и противительные отношения между предложениями":
        raise AssertionError("RU11 semantic-relation learner title widened or drifted")

    for key, minimum in (
        ("decision_algorithm", 6),
        ("worked_examples", 4),
        ("misconceptions", 4),
        ("guided_practice", 3),
        ("independent_practice", 4),
        ("mixed_transfer_practice", 2),
        ("retention_items", 3),
        ("independent_verification", 4),
    ):
        value = unit.get(key)
        if not isinstance(value, list) or len(value) < minimum:
            raise AssertionError(f"RU11 semantic-relation learner section incomplete: {key}")

    serialized = json.dumps(unit, ensure_ascii=False).lower()
    for token in ("причин", "следств", "поясн", "против"):
        if token not in serialized:
            raise AssertionError(f"RU11 semantic-relation content missing source family: {token}")

    boundaries = " ".join((unit.get("canonical_explanation") or {}).get("boundaries") or []).lower()
    for token in ("добав", "последователь", "итог", "№24"):
        if token.lower() not in boundaries:
            raise AssertionError(f"RU11 semantic-relation exclusion missing: {token}")

    checks = unit.get("independent_verification") or []
    expected_ids = {"p11-rel-v1", "p11-rel-v2", "p11-rel-v3", "p11-rel-v4"}
    if {r.get("id") for r in checks if isinstance(r, dict)} != expected_ids:
        raise AssertionError("RU11 semantic-relation exact verification set drift")
    if any(r.get("type") != "constructed_response" for r in checks if isinstance(r, dict)):
        raise AssertionError("RU11 semantic-relation verification weakened from constructed response")
    family_checks = {
        "p11-rel-v1": "следств",
        "p11-rel-v2": "против",
        "p11-rel-v3": "причин",
        "p11-rel-v4": "поясн",
    }
    for row in checks:
        if not isinstance(row, dict):
            continue
        token = family_checks[row["id"]]
        if token not in json.dumps(row, ensure_ascii=False).lower():
            raise AssertionError(f"RU11 semantic-relation verification does not prove its family: {row['id']}")

    peis = unit.get("peis_evidence") or {}
    if (
        peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL"
        or peis.get("source_candidate_review_status") != "draft"
        or peis.get("independent_verification_required") is not True
        or peis.get("assistance_must_be_recorded") is not True
        or peis.get("generic_task24_result_can_emit_exact_component_mastery") is not False
        or peis.get("link_means_unit_result_can_emit_exact_component_mastery") is not False
        or peis.get("speech_type_result_can_emit_this_mastery") is not False
        or peis.get("out_of_scope_relation_result_can_emit_this_mastery") is not False
        or peis.get("object_closure_implied") is not False
    ):
        raise AssertionError("RU11 semantic-relation PEIS fail-closed boundary weakened")

    tutor = unit.get("tutor_grounding") or {}
    tutor_allowed = " ".join(tutor.get("allowed") or []).lower()
    tutor_forbidden = " ".join(tutor.get("forbidden") or []).lower()
    if "fail closed" not in tutor_allowed or "addition" not in tutor_forbidden or "generic task-24" not in tutor_forbidden:
        raise AssertionError("RU11 semantic-relation Tutor boundary incomplete")

    rd = review.get("review_decision") or {}
    if (
        rd.get("content_exact_for_current_candidate_047_source_meaning") is not True
        or rd.get("source_candidate_inventory_status_preserved_as_draft") is not True
        or rd.get("content_duplicate_of_existing_ru11_unit") is not False
        or rd.get("exact_school_meaning_collision_observed") is not False
        or rd.get("semantic_admission_by_this_review") is not False
        or rd.get("object_level_admission_units_closed") != 0
        or rd.get("object_level_requirements_closed") != 0
        or rd.get("false_exact_mastery_admissions") != 0
        or rd.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_WITH_DRAFT_CANDIDATE_GUARD"
    ):
        raise AssertionError("RU11 semantic-relation content review decision drift")

    digest = hashlib.sha256(
        json.dumps(review, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print("RU11_SEMANTIC_RELATION_CONTENT_ADEQUACY=PASS")
    print(f"SOURCE_CANDIDATE_REVIEW_STATUS={candidate.get('review_status')}")
    print(f"BROADER_DIRECT_RELATION_CHECKS={direct_relation_checks}")
    print(f"PROPOSED_SEMANTIC={SEMANTIC}")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
