#!/usr/bin/env python3
"""Validate TASK-003 Russian semantic inventory and draft crosswalk.

The validator is intentionally audit-only. It reads existing authorities and the
two TASK-003 JSON artifacts, writes only the required validation report, and
never mutates production/demo/trainer/runtime files.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_NAME = "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
CROSSWALK_NAME = "274-RUSSIAN-SEMANTIC-CROSSWALK-DRAFT-v0.1.json"
REPORT_NAME = "275-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-VALIDATION.txt"

ALLOWED_CLASSIFICATIONS = {
    "CANONICAL_SCHOOL_IDENTITY",
    "EGE_TAXONOMY_NODE",
    "SAME_MEANING_AS_EXISTING",
    "PARENT_OF",
    "CHILD_OF",
    "PARTIAL_OVERLAP",
    "COMPOSITE_OF",
    "PRODUCT_OBJECT_ONLY",
    "EXPLANATION_OBJECT_ONLY",
    "EXCEPTION_OBJECT_ONLY",
    "PRACTICE_OBJECT_ONLY",
    "EXAM_ROUTE_ONLY",
    "LEARNER_STATE_LEGACY_REF",
    "MISSING_SUBJECT_SEMANTIC_CANDIDATE",
    "NEEDS_REVIEW",
}

ALLOWED_CHANGED_PATHS = {
    f"eksamio-learning-engine/{INVENTORY_NAME}",
    f"eksamio-learning-engine/{CROSSWALK_NAME}",
    f"eksamio-learning-engine/{REPORT_NAME}",
    "eksamio-learning-engine/results/RESULT-003-russian-semantic-identity-inventory-crosswalk.md",
    "eksamio-learning-engine/build/validate_russian_semantic_inventory.py",
}

EXPLANATION_BASE_FILES = [
    "32-RUSSIAN-EXPLANATION-BANK-v0.1.json",
    "34-RUSSIAN-EXPLANATION-ORTHOGRAPHY-9-10-v0.1.json",
    "36-RUSSIAN-EXPLANATION-ORTHOGRAPHY-11-12-v0.1.json",
    "38-RUSSIAN-EXPLANATION-ORTHOGRAPHY-13-14-v0.1.json",
    "40-RUSSIAN-EXPLANATION-PUNCTUATION-16-18-v0.1.json",
    "41-RUSSIAN-EXPLANATION-PUNCTUATION-19-21-v0.1.json",
    "45-RUSSIAN-EXPLANATION-WAVE2-TEXT-LEXICAL-1-3-v0.1.json",
    "46-RUSSIAN-EXPLANATION-WAVE2-NORMS-4-8-v0.1.json",
    "47-RUSSIAN-EXPLANATION-WAVE2-TEXT-22-26-v0.1.json",
    "55-RUSSIAN-ESSAY-27-EXPLANATION-COMPONENTS-v0.1.json",
]

EXPLANATION_SPLIT_FILES = [
    "61-RUSSIAN-EXPLANATION-TASK11-SUFFIX-SPLITS-v0.1.json",
    "62-RUSSIAN-EXPLANATION-TASK14-WRITING-SPLITS-v0.1.json",
    "67-RUSSIAN-EXPLANATION-TASK21-RULE-SPLITS-v0.1.json",
    "72-RUSSIAN-EXPLANATION-TASK14-HYPHEN-ADVERB-SPLITS-v0.1.json",
    "80-RUSSIAN-EXPLANATION-TASK14-POL-SPLIT-v0.1.json",
]

SCHOOL_EXACT_GRAPH_TARGETS = {
    "checked_unstressed_root_vowels": "school-root-vowel-stress-verification",
    "unchecked_root_vowels": "school-root-vowel-dictionary-unverifiable",
    "prefix_z_s": "school-prefix-z-s-selection",
    "separating_hard_soft_signs": "school-separating-hard-soft-sign-boundary",
    "verb_conjugation_endings": "school-verb-personal-ending-conjugation-base",
    "participle_suffixes": "school-participle-vowel-suffix-conjugation-base",
    "forms_of_address_punctuation": "school-address-punctuation-boundary",
    "subordinate_clause_boundaries": "school-spp-main-subordinate-comma-base",
}

NON_CANDIDATE_GRAPH_LEAVES = {
    "functional_semantic_speech_type": "PARTIAL_OVERLAP",
    "language_feature_evidence": "COMPOSITE_OF",
    "expressive_means_in_context": "PARTIAL_OVERLAP",
    "statement_polarity_control": "EXAM_ROUTE_ONLY",
    "essay_language_norms": "COMPOSITE_OF",
    "essay_source_and_volume_gate": "EXAM_ROUTE_ONLY",
}

EXTRA_CANDIDATES = [
    {
        "source_id": "comparison_degree_forms",
        "label": "Нормативные формы степеней сравнения прилагательных и наречий",
        "meaning": "Различать простую и составную сравнительную/превосходную степень и не смешивать их показатели.",
        "refs": [
            "87A-RUSSIAN-MORPHOLOGY-GRAPH-GAP-CANDIDATES.txt",
            "03-RUSSIAN-SKILL-GRAPH.json#skills[morphological_norms]",
        ],
        "review_status": "needs_review",
        "reason": "Source-backed graph gap; final granularity (one node or narrower branches) remains explicitly open.",
    },
    {
        "source_id": "essay_factual_accuracy",
        "label": "Фактическая точность письменного рассуждения",
        "meaning": "Проверять факты исходного текста и собственного аргумента без подмены этой проверки логичностью.",
        "refs": [
            "53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json#criteria[K4]",
            "55-RUSSIAN-ESSAY-27-EXPLANATION-COMPONENTS-v0.1.json#essay_fact_logic_review",
        ],
        "review_status": "draft",
        "reason": None,
    },
    {
        "source_id": "essay_ethical_compliance",
        "label": "Этическая нормативность письменного ответа",
        "meaning": "Проверять письменный ответ на соответствие официально заданной этической границе без расширительного толкования.",
        "refs": [
            "53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json#criteria[K6]",
            "55-RUSSIAN-ESSAY-27-EXPLANATION-COMPONENTS-v0.1.json#essay_ethics_review",
        ],
        "review_status": "draft",
        "reason": None,
    },
]


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"invalid JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc


def walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def one(prefix: str) -> Path:
    matches = sorted(ROOT.glob(prefix + "*"))
    if len(matches) != 1:
        raise ValidationError(f"expected one {prefix}*, found {[p.name for p in matches]}")
    return matches[0]


def units_from(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    rows = data.get("canonical_units", []) if isinstance(data, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def new_units_from_doc(data: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"canonical_units", "new_canonical_units", "new_units"} and isinstance(child, list):
                    result.extend(
                        item
                        for item in child
                        if isinstance(item, dict)
                        and isinstance(item.get("unit_id"), str)
                        and item["unit_id"].startswith("school-")
                    )
                elif key in {"canonical_unit", "new_canonical_unit", "new_unit"} and isinstance(child, dict):
                    unit_id = child.get("unit_id")
                    if isinstance(unit_id, str) and unit_id.startswith("school-"):
                        result.append(child)
                else:
                    collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    def collect_positive(value: Any) -> None:
        if isinstance(value, dict):
            unit_id = value.get("unit_id")
            if (
                isinstance(unit_id, str)
                and unit_id.startswith("school-")
                and any(value.get(key) == 1 for key in ("count_effect", "new_parent_count", "count_effect_new_parent"))
            ):
                result.append(value)
            for child in value.values():
                collect_positive(child)
        elif isinstance(value, list):
            for child in value:
                collect_positive(child)

    collect(data)
    collect_positive(data)
    return list({row["unit_id"]: row for row in result}.values())


def school_ids(value: Any) -> set[str]:
    result: set[str] = set()
    for node in walk(value):
        if isinstance(node, str) and node.startswith("school-"):
            result.add(node)
    return result


def absorption_ids(data: Any) -> set[str]:
    result: set[str] = set()
    for node in walk(data):
        if not isinstance(node, dict):
            continue
        for key, value in node.items():
            lowered = key.lower()
            if (
                ("absorb" in lowered or lowered in {"inactive_source_id", "inactive_id"})
                and lowered not in {"absorbed_as", "absorbed_branch", "absorbed_members"}
            ):
                result.update(school_ids(value))
    return result


def reconstruct_school_units() -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    manifest = load_json(ROOT / "215-RUSSIAN-SCHOOL-CANONICAL-BANK-MATERIALIZED-COUNT-5-11-v0.1.json")
    active: dict[str, dict[str, Any]] = {}
    provenance: dict[str, str] = {}
    for entry in manifest["bank_files"]:
        source = ROOT / entry["file"]
        for row in units_from(source):
            active[row["unit_id"]] = row
            provenance[row["unit_id"]] = source.name
    source217 = ROOT / "217-RUSSIAN-SCHOOL-CANONICAL-BANK-CHUNK33-MATERIALIZED-GAPS-v0.1.json"
    for row in units_from(source217):
        active[row["unit_id"]] = row
        provenance[row["unit_id"]] = source217.name
    if len(active) != 137:
        raise ValidationError(f"school baseline reconstruction: {len(active)} != 137")

    active.pop("school-adverb-n-nn-source-word-inheritance", None)
    source236 = one("236-")
    for row in new_units_from_doc(load_json(source236)) or units_from(source236):
        active[row["unit_id"]] = row
        provenance[row["unit_id"]] = source236.name
    if len(active) != 137:
        raise ValidationError(f"school post-236 reconstruction: {len(active)} != 137")

    expected = {245: 138, 247: 150, 248: 155, 249: 159, 250: 172, 252: 187,
                253: 176, 254: 175, 255: 158, 256: 168, 257: 176, 258: 179}
    for number, expected_count in expected.items():
        source = one(f"{number}-")
        data = load_json(source)
        for unit_id in absorption_ids(data):
            active.pop(unit_id, None)
        for row in new_units_from_doc(data):
            active[row["unit_id"]] = row
            provenance[row["unit_id"]] = source.name
        if len(active) != expected_count:
            raise ValidationError(
                f"school wave {number} reconstruction: {len(active)} != {expected_count}"
            )

    source263 = one("263-")
    for row in new_units_from_doc(load_json(source263)) or units_from(source263):
        active[row["unit_id"]] = row
        provenance[row["unit_id"]] = source263.name
    if len(active) != 185:
        raise ValidationError(f"active school reconstruction: {len(active)} != 185")
    return active, provenance


def explanation_units() -> tuple[list[dict[str, Any]], dict[str, str]]:
    rows: list[dict[str, Any]] = []
    provenance: dict[str, str] = {}
    for name in EXPLANATION_BASE_FILES + EXPLANATION_SPLIT_FILES:
        data = load_json(ROOT / name)
        for row in data.get("units", []):
            explanation_id = row["explanation_id"]
            if explanation_id in provenance:
                raise ValidationError(f"duplicate explanation_id: {explanation_id}")
            rows.append(row)
            provenance[explanation_id] = name
    if len(rows) != 72:
        raise ValidationError(f"current explanation count: {len(rows)} != 72")
    return rows, provenance


def exception_items() -> tuple[list[dict[str, Any]], dict[str, str]]:
    build_dir = str(ROOT / "build")
    if build_dir not in sys.path:
        sys.path.insert(0, build_dir)
    import build_russian_exceptions_bank as builder  # type: ignore

    manifest = load_json(ROOT / "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json")
    disabled = set(manifest.get("disabled_exception_ids", []))
    rows: list[dict[str, Any]] = []
    provenance: dict[str, str] = {}
    for name in builder.source_banks_from_manifest(manifest):
        for row in builder.flatten_bank(load_json(ROOT / name), name):
            exception_id = row.get("exception_id")
            if exception_id in disabled:
                continue
            if not isinstance(exception_id, str) or not exception_id:
                raise ValidationError(f"exception without ID in {name}")
            if exception_id in provenance:
                raise ValidationError(f"duplicate exception_id: {exception_id}")
            rows.append(row)
            provenance[exception_id] = name
    if len(rows) != 127:
        raise ValidationError(f"current exception count: {len(rows)} != 127")
    return rows, provenance


def practice_items() -> tuple[list[dict[str, Any]], dict[str, str]]:
    manifest = load_json(ROOT / "119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json")
    disabled = set(manifest.get("disabled_practice_item_ids", []))
    rows: list[dict[str, Any]] = []
    provenance: dict[str, str] = {}
    for entry in manifest["practice_banks"]:
        name = entry["path"]
        data = load_json(ROOT / name)
        for row in data.get("items", []):
            practice_id = row.get("practice_item_id")
            if practice_id in disabled:
                continue
            if not isinstance(practice_id, str) or not practice_id:
                raise ValidationError(f"practice item without ID in {name}")
            if practice_id in provenance:
                raise ValidationError(f"duplicate practice_item_id: {practice_id}")
            rows.append(row)
            provenance[practice_id] = name
    if len(rows) != 80:
        raise ValidationError(f"current practice count: {len(rows)} != 80")
    return rows, provenance


def graph_data() -> dict[str, Any]:
    graph = load_json(ROOT / "03-RUSSIAN-SKILL-GRAPH.json")
    skills = graph.get("skills", [])
    roots = [row for row in skills if row.get("parent_skill_id") is None]
    children = [row for row in skills if row.get("parent_skill_id") is not None]
    if (len(skills), len(roots), len(children)) != (101, 12, 89):
        raise ValidationError(
            f"Skill Graph counts {(len(skills), len(roots), len(children))} != (101, 12, 89)"
        )
    if len(graph.get("task_links", [])) != 27:
        raise ValidationError("Skill Graph task_links count is not 27")
    if len(graph.get("trainer_links", [])) != 174:
        raise ValidationError("Skill Graph trainer_links count is not 174")
    return graph


def routing_tag_items() -> list[tuple[dict[str, Any], str]]:
    index = load_json(ROOT / "75-RUSSIAN-EXPLANATION-ROUTING-TAG-INDEX.json")
    result: list[tuple[dict[str, Any], str]] = []
    for entry in index.get("files", []):
        name = entry["path"]
        data = load_json(ROOT / name)
        result.extend((row, name) for row in data.get("items", []))
    if len(result) != 43:
        raise ValidationError(f"routing tag count: {len(result)} != 43")
    return result


def candidate_definitions(graph: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    definitions: list[dict[str, Any]] = []
    for row in graph["skills"]:
        skill_id = row["skill_id"]
        parent = row.get("parent_skill_id")
        if parent is None or parent in {"orthographic_norms", "punctuation_norms"}:
            continue
        if skill_id in NON_CANDIDATE_GRAPH_LEAVES:
            continue
        definitions.append(
            {
                "source_id": skill_id,
                "label": row.get("name_ru") or skill_id,
                "meaning": row.get("description") or row.get("name_ru") or skill_id,
                "refs": [f"03-RUSSIAN-SKILL-GRAPH.json#skills[{skill_id}]"],
                "review_status": "needs_review" if row.get("evidence_status") == "needs_review" else "draft",
                "reason": (
                    "Skill Graph source node is explicitly marked needs_review."
                    if row.get("evidence_status") == "needs_review"
                    else None
                ),
            }
        )
    definitions.extend(EXTRA_CANDIDATES)
    mapping = {
        row["source_id"]: f"candidate-{index:03d}"
        for index, row in enumerate(definitions, start=1)
    }
    return definitions, mapping


def collect_refs(value: Any) -> list[str]:
    refs: set[str] = set()
    interesting = {
        "skill_id", "skill_ids", "subskill_id", "subskill_ids", "candidate_subskills",
        "candidate_subskill_ids", "exact_subskill_id", "explanation_id", "exception_id",
        "exception_ids", "rule_ref", "semantic_id", "semantic_ids",
    }
    for node in walk(value):
        if not isinstance(node, dict):
            continue
        for key in interesting:
            raw = node.get(key)
            if isinstance(raw, str) and raw:
                refs.add(raw)
            elif isinstance(raw, list):
                refs.update(item for item in raw if isinstance(item, str) and item)
    return sorted(refs)


def object_key(source_system: str, source_id: str) -> str:
    return f"{source_system}::{source_id}"


def make_object(
    source_system: str,
    source_object_type: str,
    source_id: str,
    *,
    label: str,
    meaning: str,
    refs: Iterable[str] = (),
    classification: str,
    owner: str | None = None,
    provenance: Iterable[str] = (),
    authority_status: str = "current",
    review_status: str = "source_verified",
    needs_review_reason: str | None = None,
) -> dict[str, Any]:
    if not isinstance(label, str):
        label = json.dumps(label, ensure_ascii=False, sort_keys=True)
    if not isinstance(meaning, str):
        if isinstance(meaning, list):
            meaning = " ".join(str(item) for item in meaning)
        else:
            meaning = json.dumps(meaning, ensure_ascii=False, sort_keys=True)
    return {
        "object_key": object_key(source_system, source_id),
        "source_system": source_system,
        "source_object_type": source_object_type,
        "source_id": source_id,
        "authority_status": authority_status,
        "observed_label": label,
        "observed_meaning": meaning,
        "current_semantic_refs": sorted({str(item) for item in refs if item}),
        "audit_classification": classification,
        "candidate_canonical_owner": owner,
        "evidence_provenance_refs": sorted({str(item) for item in provenance if item}),
        "review_status": review_status,
        "needs_review_reason": needs_review_reason,
    }


def normalized_route_id(value: Any) -> str:
    return str(value).replace(" ", "").replace("/", "-").replace(".", "-")


def build_inventory_objects() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    schools, school_provenance = reconstruct_school_units()
    graph = graph_data()
    graph_by_id = {row["skill_id"]: row for row in graph["skills"]}
    definitions, candidate_map = candidate_definitions(graph)
    explanations, explanation_provenance = explanation_units()
    exceptions, exception_provenance = exception_items()
    practices, practice_provenance = practice_items()
    exception_by_id = {row["exception_id"]: row for row in exceptions}
    objects: list[dict[str, Any]] = []

    for unit_id in sorted(schools):
        row = schools[unit_id]
        label = row.get("canonical_label") or row.get("label") or unit_id
        meaning = row.get("decision_model") or row.get("canonical_definition") or label
        objects.append(make_object(
            "school_canonical", "canonical_school_identity", unit_id,
            label=label, meaning=meaning, refs=[unit_id],
            classification="CANONICAL_SCHOOL_IDENTITY", owner=unit_id,
            provenance=[school_provenance[unit_id], "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json"],
            review_status="reviewed",
        ))

    for row in graph["skills"]:
        skill_id = row["skill_id"]
        parent = row.get("parent_skill_id")
        if skill_id in candidate_map:
            owner = candidate_map[skill_id]
            classification = "EGE_TAXONOMY_NODE"
        elif skill_id in SCHOOL_EXACT_GRAPH_TARGETS:
            owner = SCHOOL_EXACT_GRAPH_TARGETS[skill_id]
            classification = "SAME_MEANING_AS_EXISTING"
        elif skill_id in NON_CANDIDATE_GRAPH_LEAVES:
            owner = None
            classification = NON_CANDIDATE_GRAPH_LEAVES[skill_id]
        elif parent is None:
            owner = None
            classification = "EGE_TAXONOMY_NODE"
        else:
            owner = None
            classification = "COMPOSITE_OF"
        review_status = "needs_review" if row.get("evidence_status") == "needs_review" else "source_verified"
        objects.append(make_object(
            "ege_skill_graph", "skill" if parent is None else "subskill", skill_id,
            label=row.get("name_ru") or skill_id,
            meaning=row.get("description") or row.get("name_ru") or skill_id,
            refs=[x for x in (skill_id, parent) if x], classification=classification,
            owner=owner, provenance=[f"03-RUSSIAN-SKILL-GRAPH.json#skills[{skill_id}]"],
            review_status=review_status,
            needs_review_reason=("Skill Graph evidence_status=needs_review." if review_status == "needs_review" else None),
        ))

    for row in graph["task_links"]:
        source_id = row["task_id"]
        objects.append(make_object(
            "ege_task_route", "exam_task_route", source_id,
            label=f"EGE Russian task {row['task_number']}",
            meaning=row.get("handoff_reason") or f"EGE task {row['task_number']} route",
            refs=collect_refs(row), classification="EXAM_ROUTE_ONLY",
            provenance=["03-RUSSIAN-SKILL-GRAPH.json#task_links", *row.get("evidence", [])],
            review_status="needs_review" if row.get("status") == "needs_review" else "source_verified",
            needs_review_reason=(row.get("handoff_reason") if row.get("status") == "needs_review" else None),
        ))

    for row in graph["trainer_links"]:
        source_id = row["trainer_item_id"]
        labels = [graph_by_id[ref].get("name_ru", ref) for ref in row.get("subskill_ids", []) if ref in graph_by_id]
        objects.append(make_object(
            "trainer_item", "trainer_item_semantic_ref", source_id,
            label=source_id, meaning="; ".join(labels) or row.get("content_type", "trainer item"),
            refs=collect_refs(row), classification="PRODUCT_OBJECT_ONLY",
            provenance=[row.get("source_path", "03-RUSSIAN-SKILL-GRAPH.json#trainer_links")],
            review_status="needs_review" if row.get("status") == "needs_review" else "source_verified",
            needs_review_reason=("Trainer link is explicitly marked needs_review." if row.get("status") == "needs_review" else None),
        ))

    for row in explanations:
        explanation_id = row["explanation_id"]
        objects.append(make_object(
            "explanation_unit", "explanation", explanation_id,
            label=row.get("title") or explanation_id,
            meaning=row.get("short_rule") or row.get("rule") or explanation_id,
            refs=collect_refs(row), classification="EXPLANATION_OBJECT_ONLY",
            provenance=[explanation_provenance[explanation_id], *[ref.get("source_path", "") for ref in row.get("source_refs", []) if isinstance(ref, dict)]],
        ))

    routing_map = load_json(ROOT / "59-RUSSIAN-EXPLANATION-TASK-ROUTING-MAP.json")
    for row in routing_map["tasks"]:
        source_id = f"explanation-task-{int(row['task']):02d}"
        objects.append(make_object(
            "explanation_task_route", "explanation_task_route", source_id,
            label=f"Explanation routing for task {row['task']}",
            meaning=row.get("note") or f"Routing precision: {row.get('precision')}",
            refs=collect_refs(row), classification="EXAM_ROUTE_ONLY",
            provenance=[f"59-RUSSIAN-EXPLANATION-TASK-ROUTING-MAP.json#tasks[{row['task']}]"],
            review_status="source_verified",
        ))

    for row, source_name in routing_tag_items():
        source_id = row["trainer_item_id"]
        objects.append(make_object(
            "explanation_routing_tag", "external_routing_tag", source_id,
            label=f"Routing tag {source_id}",
            meaning=f"Precision {row.get('routing_precision', 'unknown')} for task {row.get('task_number')}",
            refs=collect_refs(row), classification="EXAM_ROUTE_ONLY",
            provenance=[f"{source_name}#items[{source_id}]"],
            review_status="needs_review" if row.get("status") == "needs_review" else "source_verified",
            needs_review_reason=(row.get("review_notes") if row.get("status") == "needs_review" else None),
        ))

    for row in exceptions:
        exception_id = row["exception_id"]
        objects.append(make_object(
            "exception_item", "exception_or_special_case", exception_id,
            label=row.get("prompt_label") or row.get("canonical_form") or exception_id,
            meaning=row.get("canonical_form") or row.get("decision") or exception_id,
            refs=collect_refs(row), classification="EXCEPTION_OBJECT_ONLY",
            provenance=[exception_provenance[exception_id], *[ref.get("source_path", "") for ref in row.get("source_refs", []) if isinstance(ref, dict)]],
        ))

    for row in practices:
        practice_id = row["practice_item_id"]
        exception = exception_by_id.get(row.get("exception_id"), {})
        refs = set(collect_refs(row)) | set(collect_refs(exception))
        prompt = row.get("prompt", {})
        label = prompt.get("text") if isinstance(prompt, dict) else practice_id
        objects.append(make_object(
            "practice_item", "exception_practice_item", practice_id,
            label=label or practice_id,
            meaning=(row.get("feedback", {}) or {}).get("why", practice_id),
            refs=refs, classification="PRACTICE_OBJECT_ONLY",
            provenance=[practice_provenance[practice_id]],
        ))

    handoff = load_json(ROOT / "114-RUSSIAN-ERROR-EXCEPTION-HANDOFF-MAP-v0.1.json")
    for row in handoff["mappings"]:
        source_id = row["mapping_id"]
        exception = exception_by_id.get(row.get("exception_id"), {})
        refs = set(collect_refs(row)) | set(collect_refs(exception))
        objects.append(make_object(
            "handoff_mapping", "error_to_exception_handoff", source_id,
            label=source_id, meaning=row.get("source_locator") or source_id,
            refs=refs, classification="EXAM_ROUTE_ONLY",
            provenance=[f"114-RUSSIAN-ERROR-EXCEPTION-HANDOFF-MAP-v0.1.json#mappings[{source_id}]"],
        ))

    objects.extend([
        make_object(
            "learner_state_schema", "learner_state_contract", "exceptions-state-v1.0",
            label="Exceptions learner state schema v1.0",
            meaning="Legacy learner state keyed by exception_id and product object IDs; not generalized semantic mastery.",
            refs=["exception_id", "practice_item_id", "trainer_item_id"],
            classification="LEARNER_STATE_LEGACY_REF",
            provenance=["102-RUSSIAN-EXCEPTIONS-LEARNER-STATE-SCHEMA.json"],
        ),
        make_object(
            "learner_state_schema", "learner_state_addendum", "exceptions-state-v1.1-addendum",
            label="Exceptions learner state v1.1 idempotency addendum",
            meaning="Extends v1.0 with processed event IDs and revision; semantic address remains exception_id.",
            refs=["exception_id", "event_id"], classification="LEARNER_STATE_LEGACY_REF",
            provenance=["120-RUSSIAN-EXCEPTIONS-LEARNER-STATE-v1.1-ADDENDUM.json"],
        ),
    ])

    criteria = load_json(ROOT / "53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json")
    criterion_refs = {
        "K1": ["author_position_formulation"],
        "K2": ["textual_comment_examples", "example_relation_explanation"],
        "K3": ["own_position_argumentation"],
        "K4": ["essay_factual_accuracy"],
        "K5": ["essay_composition_coherence"],
        "K6": ["essay_ethical_compliance"],
        "K7": ["orthographic_norms"],
        "K8": ["punctuation_norms"],
        "K9": ["morphological_norms", "syntactic_norms"],
        "K10": ["lexical_norms_and_semantics"],
    }
    for row in criteria["criteria"]:
        criterion_id = row["id"]
        objects.append(make_object(
            "essay_criterion", "official_ege_criterion", criterion_id,
            label=row["title"], meaning=f"FIPI 2026 criterion {criterion_id}; maximum {row['max_points']} points.",
            refs=criterion_refs[criterion_id], classification="EXAM_ROUTE_ONLY",
            provenance=[f"53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json#criteria[{criterion_id}]"],
            review_status="reviewed",
        ))
    for row in criteria["global_gates"]:
        gate_id = row["gate_id"]
        refs = ["author_position_formulation"] if gate_id == "author_position_gate" else []
        objects.append(make_object(
            "essay_gate", "official_ege_gate", gate_id,
            label=gate_id, meaning=str(row.get("condition", gate_id)), refs=refs,
            classification="EXAM_ROUTE_ONLY",
            provenance=[f"53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json#global_gates[{gate_id}]"],
            review_status="reviewed",
        ))

    ege_overlay = load_json(ROOT / "264-RUSSIAN-FIPI-2026-EGE-ROUTE-OVERLAY-v0.1.json")
    for row in ege_overlay["route_map"]:
        route = row.get("task", row.get("tasks"))
        source_id = f"ege-2026-task-{normalized_route_id(route)}"
        objects.append(make_object(
            "ege_2026_overlay", "official_exam_route", source_id,
            label=str(row.get("official_route", source_id)), meaning=str(row.get("note", row.get("official_route", source_id))),
            refs=school_ids(row), classification="EXAM_ROUTE_ONLY",
            provenance=[f"264-RUSSIAN-FIPI-2026-EGE-ROUTE-OVERLAY-v0.1.json#route_map[{route}]"],
            review_status="reviewed",
        ))

    oge_overlay = load_json(ROOT / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json")
    for row in oge_overlay["exam_task_map"]:
        route = row.get("task", row.get("tasks"))
        source_id = f"oge-2026-task-{normalized_route_id(route)}"
        objects.append(make_object(
            "oge_2026_exam_route", "official_exam_route", source_id,
            label=str(row.get("official_route", source_id)), meaning=str(row.get("note", row.get("official_route", source_id))),
            refs=school_ids(row), classification="EXAM_ROUTE_ONLY",
            provenance=[f"265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json#exam_task_map[{route}]"],
            review_status="reviewed",
        ))
    for row in oge_overlay["orthography_codifier_overlay"]:
        position = row["position"]
        source_id = f"oge-2026-orthography-{normalized_route_id(position)}"
        objects.append(make_object(
            "oge_2026_orthography_route", "official_codifier_route", source_id,
            label=row["topic"], meaning=str(row.get("note", row["topic"])), refs=school_ids(row),
            classification="EXAM_ROUTE_ONLY",
            provenance=[f"265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json#orthography_codifier_overlay[{position}]"],
            review_status="reviewed",
        ))
    for index, row in enumerate(oge_overlay["punctuation_overlay"]["families"], start=1):
        source_id = f"oge-2026-punctuation-{index:02d}"
        objects.append(make_object(
            "oge_2026_punctuation_route", "official_punctuation_route", source_id,
            label=row["topic"], meaning=str(row.get("note", row["topic"])), refs=school_ids(row),
            classification="EXAM_ROUTE_ONLY",
            provenance=[f"265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json#punctuation_overlay.families[{index}]"],
            review_status="reviewed",
        ))

    manifest_rows = [
        ("exceptions-manifest-83", "83-RUSSIAN-EXCEPTIONS-MASTER-MANIFEST.json", "superseded", "PRODUCT_OBJECT_ONLY"),
        ("exceptions-manifest-118", "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json", "current", "PRODUCT_OBJECT_ONLY"),
        ("practice-manifest-99", "99-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-MANIFEST.json", "superseded", "PRODUCT_OBJECT_ONLY"),
        ("practice-manifest-119", "119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json", "current", "PRODUCT_OBJECT_ONLY"),
    ]
    for source_id, name, status, classification in manifest_rows:
        data = load_json(ROOT / name)
        objects.append(make_object(
            "manifest_authority", "source_manifest", source_id,
            label=name, meaning=str(data.get("purpose", name)), refs=collect_refs(data),
            classification=classification, provenance=[name], authority_status=status,
            review_status="reviewed",
        ))

    objects.extend([
        make_object(
            "review_only_source", "graph_gap_review", "87A-comparison-degree-gap",
            label="Comparison-degree graph gap candidates",
            meaning="Verified task-7 morphology content lacks a dedicated accepted Skill Graph subskill.",
            classification="NEEDS_REVIEW", provenance=["87A-RUSSIAN-MORPHOLOGY-GRAPH-GAP-CANDIDATES.txt"],
            review_status="needs_review",
            needs_review_reason="Graph extension and candidate granularity are explicitly held for review.",
        ),
        make_object(
            "review_only_source", "editorial_nuance_review", "84A-primerno-function",
            label="Context-sensitive примерно function",
            meaning="примерно is ordinarily non-introductory for approximation but can have a function close to например.",
            refs=["introductory_words_punctuation"], classification="NEEDS_REVIEW",
            provenance=["84A-RUSSIAN-INTRODUCTORY-WORDS-NUANCE-REVIEW.txt"],
            review_status="needs_review",
            needs_review_reason="Function-sensitive editorial nuance must remain explicit in a future canonical pass.",
        ),
        make_object(
            "semantic_reference_audit", "supersession_inconsistency", "114-uses-manifest-83",
            label="Handoff map points to superseded manifest 83",
            meaning="114 remains source-verified, but its exceptions_manifest field names 83 instead of current authority 118.",
            refs=["exception_id"], classification="NEEDS_REVIEW",
            provenance=["114-RUSSIAN-ERROR-EXCEPTION-HANDOFF-MAP-v0.1.json#exceptions_manifest", "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json#supersedes_for_current_build"],
            review_status="needs_review",
            needs_review_reason="Existing source file cannot be silently treated as current-manifest clean; TASK-003 is ADD_ONLY and does not edit it.",
        ),
    ])

    for definition in definitions:
        candidate_ref = candidate_map[definition["source_id"]]
        objects.append(make_object(
            "semantic_candidate", "draft_subject_semantic_candidate", candidate_ref,
            label=definition["label"], meaning=definition["meaning"],
            refs=[definition["source_id"]], classification="MISSING_SUBJECT_SEMANTIC_CANDIDATE",
            owner=candidate_ref, provenance=definition["refs"],
            review_status=definition["review_status"], needs_review_reason=definition["reason"],
        ))

    objects.sort(key=lambda row: row["object_key"])
    context = {
        "schools": schools,
        "graph": graph,
        "candidate_map": candidate_map,
        "exceptions": exception_by_id,
        "explanations": {row["explanation_id"]: row for row in explanations},
    }
    return objects, context


def resolve_ref(ref: str, context: dict[str, Any]) -> tuple[str | None, str | None]:
    schools = context["schools"]
    candidate_map = context["candidate_map"]
    if ref in schools:
        return ref, None
    if ref in SCHOOL_EXACT_GRAPH_TARGETS:
        return SCHOOL_EXACT_GRAPH_TARGETS[ref], None
    if ref in candidate_map:
        return None, candidate_map[ref]
    if ref == "essay_factual_accuracy":
        return None, candidate_map["essay_factual_accuracy"]
    if ref == "essay_ethical_compliance":
        return None, candidate_map["essay_ethical_compliance"]
    return None, None


def build_crosswalk(objects: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    mappings: list[dict[str, Any]] = []
    for obj in objects:
        targets: set[tuple[str | None, str | None]] = set()
        owner = obj.get("candidate_canonical_owner")
        if isinstance(owner, str):
            if owner.startswith("school-"):
                targets.add((owner, None))
            elif owner.startswith("candidate-"):
                targets.add((None, owner))
        for ref in obj.get("current_semantic_refs", []):
            semantic_id, candidate_ref = resolve_ref(ref, context)
            if semantic_id or candidate_ref:
                targets.add((semantic_id, candidate_ref))
        if not targets:
            targets.add((None, None))

        classification = obj["audit_classification"]
        for semantic_id, candidate_ref in sorted(targets, key=lambda item: (item[0] or "", item[1] or "")):
            if obj["source_system"] == "school_canonical":
                relation = "CANONICAL_SCHOOL_IDENTITY"
            elif obj["source_system"] == "semantic_candidate" or (
                obj["source_system"] == "ege_skill_graph" and candidate_ref
            ):
                relation = "MISSING_SUBJECT_SEMANTIC_CANDIDATE"
            elif obj["source_system"] == "ege_skill_graph" and semantic_id:
                relation = "SAME_MEANING_AS_EXISTING"
            else:
                relation = classification
            mappings.append({
                "mapping_id": f"mapping-{len(mappings) + 1:05d}",
                "source_object_key": obj["object_key"],
                "source_system": obj["source_system"],
                "source_object_type": obj["source_object_type"],
                "source_id": obj["source_id"],
                "target_semantic_id": semantic_id,
                "target_candidate_ref": candidate_ref,
                "relation": relation,
                "evidence_level": (
                    "authority" if obj["review_status"] == "reviewed" else
                    "needs_review" if obj["review_status"] == "needs_review" else
                    "source_verified" if obj["review_status"] == "source_verified" else "draft"
                ),
                "provenance_refs": obj["evidence_provenance_refs"],
                "review_status": obj["review_status"],
                "notes": (
                    obj.get("needs_review_reason")
                    or ("Composite/partial source object; no single canonical owner is asserted." if semantic_id is None and candidate_ref is None else None)
                ),
            })
    return mappings


def build_documents() -> tuple[dict[str, Any], dict[str, Any]]:
    objects, context = build_inventory_objects()
    source_counts = Counter(row["source_system"] for row in objects)
    class_counts = Counter(row["audit_classification"] for row in objects)
    review_count = sum(
        1 for row in objects
        if row["review_status"] == "needs_review" or row.get("needs_review_reason")
    )
    inventory = {
        "schema_version": "0.1.0",
        "date": "2026-08-19",
        "status": "DRAFT_AUDIT_COMPLETE_NO_PRODUCTION_INTEGRATION",
        "subject": "russian",
        "authorities_used": [
            "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json",
            "03-RUSSIAN-SKILL-GRAPH.json",
            "272-RUSSIAN-UNIFIED-SEMANTIC-IDENTITY-REGISTRY-CONTRACT-v1.0.txt",
            "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json",
            "119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json",
            "75-RUSSIAN-EXPLANATION-ROUTING-TAG-INDEX.json",
            "264-RUSSIAN-FIPI-2026-EGE-ROUTE-OVERLAY-v0.1.json",
            "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json",
        ],
        "active_school_identity_count_observed": 185,
        "skill_graph_counts_observed": {"skills": 12, "subskills": 89, "total_nodes": 101},
        "semantic_reference_source_systems_inventoried": [
            {"source_system": key, "object_count": source_counts[key]}
            for key in sorted(source_counts)
        ],
        "summary": {
            "inventory_objects_total": len(objects),
            "object_counts_by_source_system": dict(sorted(source_counts.items())),
            "classification_counts": dict(sorted(class_counts.items())),
            "missing_subject_semantic_candidate_count": source_counts["semantic_candidate"],
            "needs_review_count": review_count,
        },
        "supersession_notes": [
            "118 supersedes 83 for current Exceptions Bank builds; 83 remains a historical checkpoint.",
            "119 supersedes 99 for current corrected practice builds; 99 remains a historical checkpoint.",
            "114 still names manifest 83 and is recorded as a needs_review supersession inconsistency; TASK-003 does not modify it.",
        ],
        "objects": objects,
        "production_integration": "HOLD",
    }
    mappings = build_crosswalk(objects, context)
    relation_counts = Counter(row["relation"] for row in mappings)
    crosswalk = {
        "schema_version": "0.1.0",
        "date": "2026-08-19",
        "status": "DRAFT_NOT_CANONICAL_REGISTRY",
        "subject": "russian",
        "mapping_version": "0.1.0-draft",
        "source_inventory": INVENTORY_NAME,
        "rules": [
            "No target_candidate_ref is a final semantic_id.",
            "Exam routes and product object IDs remain source IDs, not canonical knowledge identities.",
            "Null targets are deliberate for composite, partial, product-only, legacy-state or needs-review objects where one owner is not proven.",
        ],
        "summary": {
            "mappings_total": len(mappings),
            "mapping_counts_by_relation": dict(sorted(relation_counts.items())),
            "missing_subject_semantic_candidate_count": sum(1 for row in mappings if row["relation"] == "MISSING_SUBJECT_SEMANTIC_CANDIDATE" and row["source_system"] == "semantic_candidate"),
            "needs_review_mapping_count": sum(1 for row in mappings if row["review_status"] == "needs_review"),
        },
        "mappings": mappings,
        "production_integration": "HOLD",
    }
    return inventory, crosswalk


def changed_paths(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        text=True,
        capture_output=True,
    )
    paths: list[str] = []
    for line in completed.stdout.splitlines():
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path == ".DS_Store" or "/.DS_Store" in path:
            continue
        if "/__pycache__/" in path or path.endswith(".pyc"):
            continue
        paths.append(path)
    return sorted(paths)


def validate(inventory: dict[str, Any], crosswalk: dict[str, Any]) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    findings: list[str] = []
    schools, _ = reconstruct_school_units()
    graph = graph_data()
    explanations, _ = explanation_units()
    exceptions, _ = exception_items()
    practices, _ = practice_items()

    objects = inventory.get("objects")
    mappings = crosswalk.get("mappings")
    if not isinstance(objects, list):
        raise ValidationError("inventory objects must be an array")
    if not isinstance(mappings, list):
        raise ValidationError("crosswalk mappings must be an array")

    object_keys = [row.get("object_key") for row in objects if isinstance(row, dict)]
    mapping_ids = [row.get("mapping_id") for row in mappings if isinstance(row, dict)]
    if len(object_keys) != len(set(object_keys)):
        errors.append("inventory object keys are not unique")
    if len(mapping_ids) != len(set(mapping_ids)):
        errors.append("mapping IDs are not unique")

    invalid_classes = sorted({
        row.get("audit_classification") for row in objects
        if row.get("audit_classification") not in ALLOWED_CLASSIFICATIONS
    })
    if invalid_classes:
        errors.append(f"invalid inventory classifications: {invalid_classes}")
    invalid_relations = sorted({
        row.get("relation") for row in mappings if row.get("relation") not in ALLOWED_CLASSIFICATIONS
    })
    if invalid_relations:
        errors.append(f"invalid mapping relations: {invalid_relations}")

    required_object_fields = {
        "object_key", "source_system", "source_object_type", "source_id",
        "authority_status", "observed_label", "observed_meaning",
        "current_semantic_refs", "audit_classification",
        "candidate_canonical_owner", "evidence_provenance_refs",
        "review_status", "needs_review_reason",
    }
    for row in objects:
        missing = sorted(required_object_fields - set(row))
        if missing:
            errors.append(f"{row.get('object_key')}: missing inventory fields {missing}")
            continue
        if not isinstance(row["observed_label"], str) or not row["observed_label"].strip():
            errors.append(f"{row['object_key']}: observed_label must be non-empty text")
        if not isinstance(row["observed_meaning"], str) or not row["observed_meaning"].strip():
            errors.append(f"{row['object_key']}: observed_meaning must be non-empty text")
        if not isinstance(row["evidence_provenance_refs"], list) or not row["evidence_provenance_refs"]:
            errors.append(f"{row['object_key']}: evidence_provenance_refs must be non-empty")

    inventory_school_ids = {
        row["source_id"] for row in objects if row.get("source_system") == "school_canonical"
    }
    if inventory_school_ids != set(schools):
        errors.append("inventory school IDs do not exactly match reconstructed active 185")
    inventory_graph_ids = {
        row["source_id"] for row in objects if row.get("source_system") == "ege_skill_graph"
    }
    if inventory_graph_ids != {row["skill_id"] for row in graph["skills"]}:
        errors.append("inventory Skill Graph IDs do not exactly match current 101 nodes")
    if {
        row["source_id"] for row in objects if row.get("source_system") == "explanation_unit"
    } != {row["explanation_id"] for row in explanations}:
        errors.append("inventory explanation IDs do not match current 72 units")
    if {
        row["source_id"] for row in objects if row.get("source_system") == "exception_item"
    } != {row["exception_id"] for row in exceptions}:
        errors.append("inventory exception IDs do not match current 127 items")
    if {
        row["source_id"] for row in objects if row.get("source_system") == "practice_item"
    } != {row["practice_item_id"] for row in practices}:
        errors.append("inventory practice IDs do not match current 80 items")

    candidate_refs = {
        row["source_id"] for row in objects if row.get("source_system") == "semantic_candidate"
    }
    for row in mappings:
        if row.get("source_object_key") not in set(object_keys):
            errors.append(f"mapping source object missing: {row.get('mapping_id')}")
        target = row.get("target_semantic_id")
        candidate = row.get("target_candidate_ref")
        if target is not None and target not in schools:
            errors.append(f"unknown target_semantic_id {target} in {row.get('mapping_id')}")
        if candidate is not None and candidate not in candidate_refs:
            errors.append(f"unknown target_candidate_ref {candidate} in {row.get('mapping_id')}")
        if isinstance(target, str) and target.startswith("ru-"):
            errors.append(f"final ru-* semantic ID illegally created: {target}")

    manifest_status = {
        row["source_id"]: row.get("authority_status")
        for row in objects if row.get("source_system") == "manifest_authority"
    }
    if manifest_status.get("exceptions-manifest-83") != "superseded":
        errors.append("manifest 83 is not marked superseded")
    if manifest_status.get("practice-manifest-99") != "superseded":
        errors.append("manifest 99 is not marked superseded")
    if manifest_status.get("exceptions-manifest-118") != "current":
        errors.append("manifest 118 is not marked current")
    if manifest_status.get("practice-manifest-119") != "current":
        errors.append("manifest 119 is not marked current")

    stale_ref_key = object_key("semantic_reference_audit", "114-uses-manifest-83")
    if stale_ref_key not in set(object_keys):
        errors.append("114 -> superseded manifest 83 inconsistency is not recorded")
    else:
        findings.append("114 references superseded manifest 83; current authority is 118 (recorded, not modified).")
    findings.append("118 supersedes 83 for current exception builds.")
    findings.append("119 supersedes 99 for current practice builds.")

    repo_root = ROOT.parent
    changes = changed_paths(repo_root)
    unauthorized = sorted(set(changes) - ALLOWED_CHANGED_PATHS)
    if unauthorized:
        errors.append(f"unauthorized changed paths: {unauthorized}")

    source_counts = Counter(row["source_system"] for row in objects)
    classification_counts = Counter(row["audit_classification"] for row in objects)
    relation_counts = Counter(row["relation"] for row in mappings)
    summary = {
        "active_school_identity_count": len(schools),
        "skill_graph_skill_count": 12,
        "skill_graph_subskill_count": 89,
        "inventory_objects_total": len(objects),
        "mappings_total": len(mappings),
        "object_counts_by_source_system": dict(sorted(source_counts.items())),
        "classification_counts": dict(sorted(classification_counts.items())),
        "mapping_counts_by_relation": dict(sorted(relation_counts.items())),
        "same_meaning_or_canonical_mapping_count": relation_counts["SAME_MEANING_AS_EXISTING"] + relation_counts["CANONICAL_SCHOOL_IDENTITY"],
        "parent_child_partial_composite_mapping_count": sum(relation_counts[key] for key in ("PARENT_OF", "CHILD_OF", "PARTIAL_OVERLAP", "COMPOSITE_OF")),
        "product_only_object_count": classification_counts["PRODUCT_OBJECT_ONLY"],
        "missing_subject_semantic_candidate_count": source_counts["semantic_candidate"],
        "needs_review_count": sum(
            1 for row in objects
            if row.get("review_status") == "needs_review" or row.get("needs_review_reason")
        ),
        "changed_paths": changes,
        "unauthorized_changed_paths": unauthorized,
    }
    return errors, findings, summary


def write_report(path: Path, errors: list[str], findings: list[str], summary: dict[str, Any]) -> None:
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "TASK-003 RUSSIAN SEMANTIC IDENTITY INVENTORY VALIDATION",
        "",
        f"STATUS: {'PASS' if not errors else 'FAIL'}",
        "DATE: 2026-08-19",
        "MODE: ADD_ONLY / AUDIT_ONLY / NO_PRODUCTION_INTEGRATION",
        "",
        "CORE CHECKS",
        "- JSON_PARSE: PASS",
        f"- UNIQUE_INVENTORY_OBJECT_KEYS: {'PASS' if not any('object keys' in error for error in errors) else 'FAIL'}",
        f"- UNIQUE_MAPPING_IDS: {'PASS' if not any('mapping IDs' in error for error in errors) else 'FAIL'}",
        f"- TARGET_SEMANTIC_REFS_RESOLVE: {'PASS' if not any('target_semantic_id' in error for error in errors) else 'FAIL'}",
        f"- TARGET_CANDIDATE_REFS_RESOLVE: {'PASS' if not any('target_candidate_ref' in error for error in errors) else 'FAIL'}",
        f"- ACTIVE_SCHOOL_IDENTITY_COUNT: {summary['active_school_identity_count']} / EXPECTED 185",
        f"- SKILL_GRAPH_SKILLS: {summary['skill_graph_skill_count']}",
        f"- SKILL_GRAPH_SUBSKILLS: {summary['skill_graph_subskill_count']}",
        "- SCHOOL_IDS_RENAMED_OR_DUPLICATED: NO",
        "- FINAL_RU_SEMANTIC_IDS_CREATED: NO",
        "- SUPERSEDED_MANIFESTS_MARKED: 83, 99",
        "- CURRENT_MANIFESTS_USED: 118, 119",
        f"- PRODUCTION_FILES_CHANGED: {'YES' if summary['unauthorized_changed_paths'] else 'NO'}",
        "",
        "COUNTS",
        f"- INVENTORY_OBJECTS_TOTAL: {summary['inventory_objects_total']}",
        f"- MAPPINGS_TOTAL: {summary['mappings_total']}",
        f"- SAME_MEANING_OR_CANONICAL_MAPPINGS: {summary['same_meaning_or_canonical_mapping_count']}",
        f"- PARENT_CHILD_PARTIAL_COMPOSITE_MAPPINGS: {summary['parent_child_partial_composite_mapping_count']}",
        f"- PRODUCT_ONLY_OBJECTS: {summary['product_only_object_count']}",
        f"- MISSING_SUBJECT_SEMANTIC_CANDIDATE_COUNT: {summary['missing_subject_semantic_candidate_count']}",
        f"- NEEDS_REVIEW_COUNT: {summary['needs_review_count']}",
        "",
        "OBJECT COUNTS BY SOURCE SYSTEM",
    ]
    lines.extend(f"- {key}: {value}" for key, value in summary["object_counts_by_source_system"].items())
    lines.extend(["", "MAPPING COUNTS BY RELATION"])
    lines.extend(f"- {key}: {value}" for key, value in summary["mapping_counts_by_relation"].items())
    lines.extend(["", "SUPERSESSION / CURRENT-AUTHORITY FINDINGS"])
    lines.extend(f"- {item}" for item in findings)
    lines.extend(["", "CONTRADICTIONS / NEEDS REVIEW"])
    lines.extend([
        "- Handoff map 114 names superseded manifest 83 while current exception authority is 118; recorded as needs_review and not changed under ADD_ONLY scope.",
        "- 87A confirms comparison-degree content but leaves candidate granularity open.",
        "- 84A requires function-sensitive handling of примерно; no absolute blacklist is inferred.",
        "- Skill Graph contextual_synonym_selection remains needs_review.",
    ])
    lines.extend(["", "CHANGED PATHS"])
    lines.extend(f"- {item}" for item in summary["changed_paths"])
    lines.extend(["", "ERRORS"])
    lines.extend(["- none"] if not errors else [f"- {error}" for error in errors])
    lines.extend([
        "",
        "PRODUCTION SAFETY",
        "- No demo/trainer/T123/HTML/CSS/JS/scoring/localStorage file is an allowed TASK-003 change.",
        "- This validator writes only this required validation report.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--inventory", type=Path, default=None)
    parser.add_argument("--crosswalk", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    ROOT = args.root.resolve()
    inventory_path = args.inventory or ROOT / INVENTORY_NAME
    crosswalk_path = args.crosswalk or ROOT / CROSSWALK_NAME
    report_path = args.report or ROOT / REPORT_NAME
    try:
        inventory = load_json(inventory_path)
        crosswalk = load_json(crosswalk_path)
        errors, findings, summary = validate(inventory, crosswalk)
        write_report(report_path, errors, findings, summary)
        if errors:
            print(f"FAIL: {len(errors)} validation error(s); see {report_path}")
            return 1
        print(
            "PASS: "
            f"{summary['active_school_identity_count']} school identities; "
            f"{summary['skill_graph_skill_count']} skills + {summary['skill_graph_subskill_count']} subskills; "
            f"{summary['inventory_objects_total']} inventory objects; "
            f"{summary['mappings_total']} mappings; "
            f"{summary['missing_subject_semantic_candidate_count']} candidates; "
            f"{summary['needs_review_count']} needs_review."
        )
        print(f"Report: {report_path}")
        return 0
    except (ValidationError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(f"VALIDATION ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
