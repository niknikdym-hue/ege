#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
SKILL_GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
BOUNDARY_BUILDER = HERE / "build_ru02_orthoepy_candidate_boundary_review.py"

EXPECTED: dict[str, tuple[str, str, str]] = {
    "candidate-018": (
        "normative_stress_selection",
        "Определение нормативной позиции ударения",
        "confirmed",
    ),
    "candidate-019": (
        "stress_nouns",
        "Ударение в существительных и их формах",
        "partial",
    ),
    "candidate-020": (
        "stress_adjectival_forms",
        "Ударение в прилагательных, кратких формах и степенях сравнения",
        "partial",
    ),
    "candidate-021": (
        "stress_verbs",
        "Ударение в глаголах и личных/родовых формах",
        "partial",
    ),
    "candidate-022": (
        "stress_participles",
        "Ударение в причастиях и кратких причастиях",
        "partial",
    ),
    "candidate-023": (
        "stress_gerunds",
        "Ударение в деепричастиях",
        "partial",
    ),
    "candidate-024": (
        "stress_adverbs",
        "Ударение в наречиях",
        "partial",
    ),
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalized_meaning(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def build_resolution() -> dict[str, Any]:
    boundary = runpy.run_path(str(BOUNDARY_BUILDER))["build_review"]()
    if boundary.get("status") != "CENTRAL_BRAIN_RU02_ORTHOEPY_REUSE_FIRST_BOUNDARY_REVIEW_ACCEPTANCE_NOT_ADMITTED":
        raise ValueError("RU02 prerequisite boundary status drift")
    if set(boundary.get("program_candidate_refs") or []) != set(EXPECTED):
        raise ValueError("RU02 prerequisite candidate set drift")
    if int((boundary.get("summary") or {}).get("semantic_admissions", -1)) != 0:
        raise ValueError("RU02 prerequisite unexpectedly self-admitted semantics")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    graph = json.loads(SKILL_GRAPH.read_text(encoding="utf-8"))
    graph_rows = [row for row in graph.get("skills", []) if isinstance(row, dict)]

    resolutions: list[dict[str, Any]] = []
    for candidate_id, (taxonomy_ref, expected_label, expected_graph_evidence_status) in sorted(EXPECTED.items()):
        candidate_matches = [
            row
            for row in objects
            if row.get("source_system") == "semantic_candidate"
            and row.get("source_id") == candidate_id
            and row.get("authority_status") == "current"
        ]
        if len(candidate_matches) != 1:
            raise ValueError(f"RU02 candidate inventory mismatch: {candidate_id}")
        candidate = candidate_matches[0]
        if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
            raise ValueError(f"RU02 candidate classification drift: {candidate_id}")
        if candidate.get("candidate_canonical_owner") != candidate_id:
            raise ValueError(f"RU02 candidate owner drift: {candidate_id}")
        if candidate.get("review_status") not in {"draft", "needs_review"}:
            raise ValueError(f"RU02 candidate review state unsupported: {candidate_id}")
        if candidate.get("observed_label") != expected_label:
            raise ValueError(f"RU02 candidate label drift: {candidate_id}")
        refs = [str(ref) for ref in (candidate.get("current_semantic_refs") or [])]
        if refs != [taxonomy_ref]:
            raise ValueError(f"RU02 candidate taxonomy ref drift: {candidate_id}")

        backing_matches = [
            row
            for row in objects
            if row.get("source_system") == "ege_skill_graph"
            and row.get("source_id") == taxonomy_ref
            and row.get("authority_status") == "current"
            and row.get("candidate_canonical_owner") == candidate_id
        ]
        if len(backing_matches) != 1:
            raise ValueError(f"RU02 exact current taxonomy backing mismatch: {candidate_id}/{taxonomy_ref}")
        backing = backing_matches[0]
        if backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
            raise ValueError(f"RU02 taxonomy backing classification drift: {candidate_id}")
        if backing.get("review_status") != "source_verified":
            raise ValueError(f"RU02 taxonomy backing is not source-verified: {candidate_id}")
        if backing.get("observed_label") != expected_label:
            raise ValueError(f"RU02 taxonomy backing label drift: {candidate_id}")
        if normalized_meaning(backing.get("observed_meaning")) != normalized_meaning(candidate.get("observed_meaning")):
            raise ValueError(f"RU02 candidate/backing meaning mismatch: {candidate_id}")
        expected_provenance = f"03-RUSSIAN-SKILL-GRAPH.json#skills[{taxonomy_ref}]"
        provenance_refs = [str(ref) for ref in (backing.get("evidence_provenance_refs") or [])]
        if expected_provenance not in provenance_refs:
            raise ValueError(f"RU02 taxonomy provenance drift: {candidate_id}")

        graph_matches = [row for row in graph_rows if row.get("skill_id") == taxonomy_ref]
        if len(graph_matches) != 1:
            raise ValueError(f"RU02 skill-graph node mismatch: {taxonomy_ref}")
        graph_row = graph_matches[0]
        if graph_row.get("name_ru") != expected_label:
            raise ValueError(f"RU02 skill-graph label drift: {taxonomy_ref}")
        if normalized_meaning(graph_row.get("description")) != normalized_meaning(candidate.get("observed_meaning")):
            raise ValueError(f"RU02 skill-graph meaning drift: {taxonomy_ref}")
        if graph_row.get("parent_skill_id") != "orthoepic_norms":
            raise ValueError(f"RU02 skill-graph parent drift: {taxonomy_ref}")
        graph_evidence_status = str(graph_row.get("evidence_status") or "")
        if graph_evidence_status != expected_graph_evidence_status:
            raise ValueError(
                f"RU02 skill-graph evidence status drift: {taxonomy_ref}: "
                f"expected={expected_graph_evidence_status} actual={graph_evidence_status}"
            )
        if graph_row.get("exam_task_numbers") != [4]:
            raise ValueError(f"RU02 skill-graph task-route drift: {taxonomy_ref}")

        resolutions.append(
            {
                "candidate_ref": candidate_id,
                "candidate_review_status": str(candidate.get("review_status")),
                "source_taxonomy_id": taxonomy_ref,
                "label_ru": expected_label,
                "meaning_ru": normalized_meaning(candidate.get("observed_meaning")),
                "source_identity_resolution": "EXACT_CURRENT_SOURCE_VERIFIED_INVENTORY_BACKING_GRAPH_EVIDENCE_PRESERVED",
                "source_authority": "03-RUSSIAN-SKILL-GRAPH.json",
                "source_provenance_refs": provenance_refs,
                "inventory_source_review_status": "source_verified",
                "skill_graph_evidence_status": graph_evidence_status,
                "route_metadata": {"ege_task_numbers": [4]},
                "admission_effect": "NONE",
            }
        )

    confirmed_count = sum(row["skill_graph_evidence_status"] == "confirmed" for row in resolutions)
    partial_count = sum(row["skill_graph_evidence_status"] == "partial" for row in resolutions)
    if confirmed_count != 1 or partial_count != 6:
        raise ValueError("RU02 graph evidence distribution drift")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU02_SOURCE_IDENTITIES_RESOLVED_SUBJECT_ACCEPTANCE_NOT_ADMITTED",
        "authority_issue": 161,
        "module_id": "RU-PROG-02",
        "prerequisite_boundary_status": boundary["status"],
        "policy": {
            "source_identity_resolution_is_subject_semantic_admission": False,
            "ege_taxonomy_id_is_canonical_subject_semantic_id": False,
            "candidate_ref_is_canonical_subject_semantic_id": False,
            "task_number_is_semantic_identity": False,
            "exact_source_backing_required": True,
            "exact_label_and_meaning_match_required": True,
            "source_verified_inventory_backing_required": True,
            "skill_graph_evidence_status_must_be_preserved": True,
            "partial_skill_graph_evidence_may_be_promoted_by_resolution": False,
            "content_adequacy_review_still_required_before_gap_or_admission": True,
            "keyword_or_fuzzy_inference_allowed": False,
        },
        "resolutions": resolutions,
        "summary": {
            "candidate_records": len(EXPECTED),
            "exact_source_identity_resolutions": len(resolutions),
            "unresolved_source_identities": len(EXPECTED) - len(resolutions),
            "confirmed_skill_graph_evidence": confirmed_count,
            "partial_skill_graph_evidence": partial_count,
            "semantic_admissions": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "false_exact_mastery_admissions": 0,
        },
        "next_exact_work": {
            "draft_candidates_requiring_source_identity_resolution": 0,
            "candidates_with_partial_skill_graph_evidence_requiring_semantic_acceptance_review": partial_count,
            "content_units_requiring_exact_candidate_adequacy_review": 2,
            "candidate_level_content_gap_may_be_declared_without_separate_review": False,
            "subject_semantic_admission_may_be_inferred_from_source_resolution": False,
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
        print("RU02_ORTHOEPY_SOURCE_IDENTITY_RESOLUTION=PASS")
        print(f"EXACT_SOURCE_IDENTITY_RESOLUTIONS={result['summary']['exact_source_identity_resolutions']}")
        print(f"UNRESOLVED_SOURCE_IDENTITIES={result['summary']['unresolved_source_identities']}")
        print(f"CONFIRMED_SKILL_GRAPH_EVIDENCE={result['summary']['confirmed_skill_graph_evidence']}")
        print(f"PARTIAL_SKILL_GRAPH_EVIDENCE={result['summary']['partial_skill_graph_evidence']}")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_LEVEL_CLOSURES=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
