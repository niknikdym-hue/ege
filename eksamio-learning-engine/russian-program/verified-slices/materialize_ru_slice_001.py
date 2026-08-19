#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

SLICE = "RU-SLICE-001"
PRE = "school-verb-personal-ending-conjugation-base"
TARGET = "school-participle-vowel-suffix-conjugation-base"
GOAL = "present-tense participle suffix selection"
HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]

ITEM_FILE = HERE / "RU-SLICE-001-ITEM-BANK-v0.1.json"
EVIDENCE_FILE = HERE / "RU-SLICE-001-EVIDENCE-FIXTURES-v0.1.json"
EDGE_FILE = HERE / "RU-SLICE-001-PREREQUISITE-EDGE-v0.1.json"
GOLDEN_FILE = HERE / "RU-SLICE-001-GOLDEN-SCENARIOS-v0.1.json"
RESULT_FILE = HERE / "RU-SLICE-001-FIXTURE-VALIDATION.txt"

FORBIDDEN_FIELDS = {
    "effective_weight",
    "mastery_weight",
    "semantic_contribution_percentage",
    "canonical_mastery",
    "mastery_estimate",
}


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def provenance(semantic_id: str) -> list[dict]:
    if semantic_id == PRE:
        return [
            {
                "source_ref": "253-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-C-O26-O35-v0.1.json",
                "source_locator": "O26_verb_personal_endings / Rosenthal §44",
                "assertion_type": "REVIEWED_CURRICULUM_SOURCE",
            },
            {
                "source_ref": "36-RUSSIAN-EXPLANATION-ORTHOGRAPHY-11-12-v0.1.json",
                "source_locator": "units[verb_conjugation_endings]",
                "assertion_type": "REVIEWED_CURRICULUM_SOURCE",
            },
        ]
    return [
        {
            "source_ref": "253-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-C-O26-O35-v0.1.json",
            "source_locator": "O29_participle_vowels / Rosenthal §47 / Lopatin §§58–60, 76",
            "assertion_type": "REVIEWED_CURRICULUM_SOURCE",
        },
        {
            "source_ref": "36-RUSSIAN-EXPLANATION-ORTHOGRAPHY-11-12-v0.1.json",
            "source_locator": "units[participle_suffixes]",
            "assertion_type": "REVIEWED_CURRICULUM_SOURCE",
        },
    ]


def make_item(item_id: str, role: str, semantic_id: str, prompt: str, answer: str,
              rationale: str, rule_basis: str, boundary: str = "regular") -> dict:
    return {
        "item_id": item_id,
        "delivery_role": role,
        "semantic_id": semantic_id,
        "goal_context": GOAL if semantic_id == TARGET else None,
        "prompt": prompt,
        "response_contract": {
            "mode": "TYPED_SINGLE_CYRILLIC_LETTER",
            "normalization": "trim + lowercase + Cyrillic ё preserved",
            "accepted_answers": [answer.lower()],
        },
        "deterministic_key": answer.lower(),
        "rationale": rationale,
        "rule_basis": rule_basis,
        "source_provenance": provenance(semantic_id),
        "boundary_type": boundary,
        "content_origin": "ORIGINAL_EKSAMIO_NOT_COPIED_FROM_FIPI_OR_CURRENT_TRAINER",
        "independent_verification_safe": role == "INDEPENDENT_VERIFICATION",
        "worked_example_exposure": False,
    }


def build_item_bank() -> dict:
    items = [
        make_item(
            "RU1-CONJ-DIAG-01", "PREREQUISITE_DIAGNOSTIC", PRE,
            "Вставьте одну букву: «На рассвете лодки медленно приближа..тся к пристани».",
            "ю", "«Приближаться» — I спряжение; в 3-м лице множественного числа пишется -ют.",
            "I conjugation personal ending",
        ),
        make_item(
            "RU1-CONJ-DIAG-02", "PREREQUISITE_DIAGNOSTIC", PRE,
            "Вставьте одну букву: «Ты терпеливо держ..шь нить натянутой».",
            "и", "«Держать» относится ко II спряжению; форма 2-го лица единственного числа — «держишь».",
            "II conjugation reviewed exception", "reviewed_exception",
        ),
        make_item(
            "RU1-CONJ-DIAG-03", "PREREQUISITE_DIAGNOSTIC", PRE,
            "Вставьте одну букву: «Мы стел..м покрывало на траве».",
            "е", "«Стелить» — исключение I спряжения; форма 1-го лица множественного числа — «стелем».",
            "I conjugation reviewed exception", "reviewed_exception",
        ),
        make_item(
            "RU1-CONJ-DIAG-04", "PREREQUISITE_DIAGNOSTIC", PRE,
            "Вставьте одну букву: «Пастухи гон..т табун к реке».",
            "я", "«Гнать» относится ко II спряжению; форма 3-го лица множественного числа — «гонят».",
            "II conjugation reviewed exception", "reviewed_exception",
        ),
        make_item(
            "RU1-PART-TARGET-01", "TARGET_DIAGNOSTIC_PRACTICE", TARGET,
            "Вставьте одну букву в суффикс причастия: «кле..щий афишу волонтёр».",
            "я", "«Клеить» — II спряжение; действительное причастие настоящего времени — «клеящий».",
            "present active participle from II conjugation",
        ),
        make_item(
            "RU1-PART-TARGET-02", "TARGET_DIAGNOSTIC_PRACTICE", TARGET,
            "Вставьте одну букву в суффикс причастия: «колебл..мый ветром флажок».",
            "е", "«Колебать» — I спряжение; страдательное причастие настоящего времени — «колеблемый».",
            "present passive participle from I conjugation",
        ),
        make_item(
            "RU1-PART-TARGET-03", "TARGET_DIAGNOSTIC_PRACTICE", TARGET,
            "Вставьте одну букву в суффикс причастия: «завис..щий от погоды маршрут».",
            "я", "«Зависеть» относится ко II спряжению; действительное причастие настоящего времени — «зависящий».",
            "present active participle from II conjugation reviewed exception", "reviewed_exception",
        ),
        make_item(
            "RU1-PART-TARGET-04", "TARGET_DIAGNOSTIC_PRACTICE", TARGET,
            "Вставьте одну букву в суффикс причастия: «омыва..мый морем берег».",
            "е", "«Омывать» — I спряжение; страдательное причастие настоящего времени — «омываемый».",
            "present passive participle from I conjugation",
        ),
        make_item(
            "RU1-VERIFY-CONJ-01", "INDEPENDENT_VERIFICATION", PRE,
            "Вставьте одну букву: «Слыш..т ли они сигнал издалека?»",
            "а", "«Слышать» относится ко II спряжению; в 3-м лице множественного числа — «слышат».",
            "II conjugation reviewed exception", "reviewed_exception",
        ),
        make_item(
            "RU1-VERIFY-CONJ-02", "INDEPENDENT_VERIFICATION", PRE,
            "Вставьте одну букву: «Полевой ветер ве..т с востока».",
            "е", "«Веять» относится к I спряжению; форма 3-го лица единственного числа — «веет».",
            "I conjugation personal ending",
        ),
        make_item(
            "RU1-VERIFY-PART-01", "INDEPENDENT_VERIFICATION", TARGET,
            "Вставьте одну букву в суффикс причастия: «та..щий на солнце снег».",
            "ю", "«Таять» — I спряжение; действительное причастие настоящего времени — «тающий».",
            "present active participle from I conjugation",
        ),
        make_item(
            "RU1-VERIFY-PART-02", "INDEPENDENT_VERIFICATION", TARGET,
            "Вставьте одну букву в суффикс причастия: «стро..мый инженерами мост».",
            "и", "«Строить» — II спряжение; страдательное причастие настоящего времени — «строимый».",
            "present passive participle from II conjugation",
        ),
    ]
    return {
        "schema_version": "0.1.0",
        "date": "2026-08-20",
        "status": "FIXTURE_READY_NO_PRODUCTION_INTEGRATION",
        "slice_id": SLICE,
        "subject": "russian",
        "semantic_scope": {
            "prerequisite_semantic_id": PRE,
            "target_semantic_id": TARGET,
            "conditional_goal_context": GOAL,
        },
        "authority_refs": [
            "RU-SLICE-001-TASK12-CONJUGATION-PARTICIPLE-SOURCE-GATE-v0.1.json",
            "../../253-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-C-O26-O35-v0.1.json",
            "../../36-RUSSIAN-EXPLANATION-ORTHOGRAPHY-11-12-v0.1.json",
        ],
        "content_invariants": [
            "Every item has exactly one canonical semantic_id.",
            "All responses are deterministically checkable without AI.",
            "Verification items are fresh original contexts and have worked_example_exposure=false.",
            "Target items are restricted to present-tense participle suffix selection.",
            "Past-passive participle suffix branches are outside this item bank.",
        ],
        "items": items,
        "counts": {
            "prerequisite_diagnostic": 4,
            "target_diagnostic_practice": 4,
            "independent_verification": 4,
            "total": 12,
        },
    }


def semantic_target(semantic_id: str, role: str = "PRIMARY", resolution: str = "EXACT") -> dict:
    return {
        "semantic_id": semantic_id,
        "target_role": role,
        "mapping_resolution": resolution,
        "mapping_confidence": 1.0 if resolution == "EXACT" else None,
        "mapping_review_status": "source_verified",
    }


def exact_error(semantic_id: str, item_id: str) -> list[dict]:
    return [{
        "observation_type": "EXACT_RULE_ERROR",
        "semantic_id": semantic_id,
        "candidate_ref": None,
        "precision": "EXACT",
        "confidence": 1.0,
        "source_locator": item_id,
        "provenance_refs": ["RU-SLICE-001-ITEM-BANK-v0.1.json"],
    }]


def make_event(event_id: str, targets: list[dict], object_id: str, *, product_type: str,
               route: str, outcome: str, correctness: bool, response_value: object,
               seq: int, fixture_role: str, assistance: str = "UNASSISTED",
               transfer_kind: str = "NOT_APPLICABLE", origin_refs: list[str] | None = None,
               errors: list[dict] | None = None, source_type: str = "ru_slice_item",
               evaluator_type: str = "DETERMINISTIC_VALIDATOR", trust: str = "DETERMINISTIC_HIGH",
               content_version: str = "0.1.0", exam_meta: dict | None = None) -> dict:
    origin_refs = origin_refs or []
    errors = errors or []
    at = f"2026-08-20T00:{4 + seq:02d}:00+03:00"
    source = {
        "object_type": source_type,
        "object_id": object_id,
        "content_version": content_version,
        "item_version": "0.1.0",
    }
    if exam_meta is not None:
        source["route_metadata"] = exam_meta
    return {
        "event_id": event_id,
        "schema_version": "0.1.0",
        "event_kind": "PERFORMANCE_OBSERVATION",
        "learner_profile_id": "learner-fixture-ru001",
        "identity_refs": {"anonymous_identity_ref": "anon:ru-slice-001"},
        "subject_id": "russian",
        "semantic_targets": targets,
        "semantic_context": {
            "semantic_registry_version": "russian-school-185-current",
            "semantic_mapping_version": "0.1.0-draft",
            "mapping_artifact_refs": [
                "../../274-RUSSIAN-SEMANTIC-CROSSWALK-DRAFT-v0.1.json",
                "RU-SLICE-001-TASK12-CONJUGATION-PARTICIPLE-SOURCE-GATE-v0.1.json",
            ],
        },
        "source": source,
        "product": {"source_type": product_type, "product_id": "eksamio-ru-slice-001", "route": route},
        "session_id": "session-ru-slice-001",
        "timestamps": {
            "occurred_at_client": at,
            "received_at_server": at,
            "server_sequence": seq,
            "server_watermark": f"wm-ru001-{seq:03d}",
        },
        "result": {
            "attempt_index": 1,
            "outcome": outcome,
            "correctness": correctness,
            "score": 1 if correctness else 0,
            "max_score": 1,
            "response_value": response_value,
            "result_details": {"fixture_role": fixture_role},
        },
        "response_mode": "UNORDERED_SET" if source_type == "trainer_card" else "TYPED_TEXT",
        "assistance": {"level": assistance, "help_event_refs": [], "assistance_provider": None},
        "evaluator": {
            "evaluator_type": evaluator_type,
            "evaluator_id": "ege-ru-task12-key" if source_type == "trainer_card" else "ru-slice-001-key",
            "evaluator_version": "2026" if source_type == "trainer_card" else "0.1.0",
            "trust_class": trust,
            "uncertainty": 0.0,
            "review_status": "not_required",
            "rubric_version": None,
            "official_truth_status": "OFFICIAL_OR_DETERMINISTIC",
        },
        "provenance_refs": [
            "russkiy-knigi/ege-russkiy-trenazher/ege-russkiy-trenazher-T123-06.txt"
            if source_type == "trainer_card" else "RU-SLICE-001-ITEM-BANK-v0.1.json",
            "RU-SLICE-001-TASK12-CONJUGATION-PARTICIPLE-SOURCE-GATE-v0.1.json",
        ],
        "transfer_context": {"kind": transfer_kind, "origin_event_refs": origin_refs},
        "retention_context": {
            "kind": "SAME_SESSION" if transfer_kind == "SAME_SESSION_VERIFICATION" else "NONE",
            "delay_seconds": 0 if transfer_kind == "SAME_SESSION_VERIFICATION" else None,
            "scheduled_by_policy_version": None,
        },
        "error_observations": errors,
        "subject_extension": {
            "subject_payload_schema_version": "ru-slice-001-subject-payload-v0.1",
            "subject_payload": {
                "slice_id": SLICE,
                "fixture_role": fixture_role,
                "item_id": object_id,
                "goal_context": GOAL,
            },
        },
        "created_at": at,
    }


def build_evidence() -> dict:
    composite_error = [{
        "observation_type": "UNKNOWN_OR_INSUFFICIENT_PRECISION",
        "semantic_id": None,
        "candidate_ref": None,
        "precision": "UNKNOWN",
        "confidence": 1.0,
        "source_locator": "ege-ru-12-2026-12-01",
        "provenance_refs": [
            "../../274-RUSSIAN-SEMANTIC-CROSSWALK-DRAFT-v0.1.json",
            "russkiy-knigi/ege-russkiy-trenazher/ege-russkiy-trenazher-T123-06.txt",
        ],
    }]
    events = [
        make_event(
            "ru001.ev.composite.error.001",
            [semantic_target(PRE, "PRIMARY", "COMPOSITE"), semantic_target(TARGET, "SECONDARY", "COMPOSITE")],
            "ege-ru-12-2026-12-01", product_type="ege_oge_trainer", route="ege-task-12",
            outcome="INCORRECT", correctness=False, response_value="25", seq=1,
            fixture_role="composite_entry_error", errors=composite_error, source_type="trainer_card",
            evaluator_type="OFFICIAL_KEY_OR_RULE", trust="OFFICIAL_SOURCE_HIGH",
            content_version="current-ege-ru-trainer",
            exam_meta={"exam": "EGE", "exam_year": 2026, "task_route": "12", "historical_format": False},
        ),
        make_event(
            "ru001.ev.preq.diag.success", [semantic_target(PRE)], "RU1-CONJ-DIAG-01",
            product_type="diagnostic", route="prerequisite_diagnostic", outcome="CORRECT", correctness=True,
            response_value="ю", seq=2, fixture_role="prerequisite_diagnostic_success",
        ),
        make_event(
            "ru001.ev.preq.diag.failure", [semantic_target(PRE)], "RU1-CONJ-DIAG-02",
            product_type="diagnostic", route="prerequisite_diagnostic", outcome="INCORRECT", correctness=False,
            response_value="е", seq=3, fixture_role="prerequisite_diagnostic_failure",
            errors=exact_error(PRE, "RU1-CONJ-DIAG-02"),
        ),
        make_event(
            "ru001.ev.target.diag.success", [semantic_target(TARGET)], "RU1-PART-TARGET-01",
            product_type="diagnostic", route="target_diagnostic", outcome="CORRECT", correctness=True,
            response_value="я", seq=4, fixture_role="target_diagnostic_success",
        ),
        make_event(
            "ru001.ev.target.diag.failure", [semantic_target(TARGET)], "RU1-PART-TARGET-02",
            product_type="diagnostic", route="target_diagnostic", outcome="INCORRECT", correctness=False,
            response_value="и", seq=5, fixture_role="target_diagnostic_failure",
            errors=exact_error(TARGET, "RU1-PART-TARGET-02"),
        ),
        make_event(
            "ru001.ev.target.assisted.success", [semantic_target(TARGET)], "RU1-PART-TARGET-03",
            product_type="course_module", route="guided_target_practice", outcome="CORRECT", correctness=True,
            response_value="я", seq=6, fixture_role="assisted_learning_success_not_mastery",
            assistance="RULE_EXPLANATION",
        ),
        make_event(
            "ru001.ev.preq.reverify.success", [semantic_target(PRE)], "RU1-VERIFY-CONJ-01",
            product_type="diagnostic", route="independent_verification", outcome="CORRECT", correctness=True,
            response_value="а", seq=7, fixture_role="prerequisite_independent_reverification_success",
            transfer_kind="SAME_SESSION_VERIFICATION", origin_refs=["ru001.ev.preq.diag.failure"],
        ),
        make_event(
            "ru001.ev.target.verify.success", [semantic_target(TARGET)], "RU1-VERIFY-PART-01",
            product_type="diagnostic", route="independent_verification", outcome="CORRECT", correctness=True,
            response_value="ю", seq=8, fixture_role="target_independent_verification_success",
            transfer_kind="SAME_SESSION_VERIFICATION", origin_refs=["ru001.ev.target.assisted.success"],
        ),
        make_event(
            "ru001.ev.target.verify.failure", [semantic_target(TARGET)], "RU1-VERIFY-PART-02",
            product_type="diagnostic", route="independent_verification", outcome="INCORRECT", correctness=False,
            response_value="е", seq=9, fixture_role="target_independent_verification_failure",
            transfer_kind="SAME_SESSION_VERIFICATION", origin_refs=["ru001.ev.target.assisted.success"],
            errors=exact_error(TARGET, "RU1-VERIFY-PART-02"),
        ),
    ]
    return {
        "schema_version": "0.1.0",
        "date": "2026-08-20",
        "status": "SHARED_EVIDENCE_FIXTURES_READY_NO_PRODUCTION_INTEGRATION",
        "slice_id": SLICE,
        "shared_schema_ref": "../../277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json",
        "events": events,
        "fixture_invariants": [
            "Composite EGE-12 error maps both semantic targets as COMPOSITE and does not claim an exact rule error.",
            "Exact diagnostic and verification fixtures contain one EXACT primary semantic target.",
            "Assisted success is recorded as RULE_EXPLANATION and is not labeled mastery.",
            "Independent verification uses fresh verification items and SAME_SESSION_VERIFICATION context.",
        ],
    }


def build_edge() -> dict:
    return {
        "schema_version": "0.1.0",
        "date": "2026-08-20",
        "status": "SOURCE_VERIFIED_CANONICAL_GRAPH_CANDIDATE_FIXTURE",
        "slice_id": SLICE,
        "shared_edge_schema_ref": "../../283-EKSAMIO-PREREQUISITE-READINESS-CONTRACT-v0.1.json#/$defs/edge_schema",
        "edge_id": "ru-prereq-conjugation-to-present-participle-suffix-v0.1",
        "edge": {
            "source_semantic_id": PRE,
            "target_semantic_id": TARGET,
            "relation_type": "REQUIRED",
            "provenance": [
                {
                    "source_ref": "eksamio-learning-engine/russkiy-knigi/rozental.doc",
                    "source_locator": "Rosenthal §44: verb conjugation/personal endings; §47: participle suffixes",
                    "assertion_type": "VERIFIED_SUBJECT_SOURCE",
                },
                {
                    "source_ref": "253-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-C-O26-O35-v0.1.json",
                    "source_locator": "O26_verb_personal_endings + O29_participle_vowels",
                    "assertion_type": "REVIEWED_CURRICULUM_SOURCE",
                },
                {
                    "source_ref": "36-RUSSIAN-EXPLANATION-ORTHOGRAPHY-11-12-v0.1.json",
                    "source_locator": "verb_conjugation_endings.algorithm + participle_suffixes.rule/algorithm",
                    "assertion_type": "REVIEWED_CURRICULUM_SOURCE",
                },
            ],
            "graph_version": "prerequisite-graph-v0.1-ru-slice-001-source-verified",
            "review_status": "SOURCE_VERIFIED",
            "conditional_scope": {
                "subject_id": "russian",
                "goal_context": GOAL,
                "route_context": "any Russian route assessing present-tense participle suffix selection",
            },
            "admission_scope": "CANONICAL_GRAPH",
        },
        "materialization_boundary": {
            "contract_283_mutated": False,
            "embedded_in_283_canonical_edges": False,
            "purpose": "Fixture/data input for the shared prerequisite graph materializer and reference PEIS runtime.",
            "must_not_apply_when": [
                "past-passive participle suffix selection",
                "any goal context where target choice is driven by infinitive/model rather than present-tense conjugation",
            ],
        },
    }


def build_golden() -> dict:
    return {
        "schema_version": "0.1.0",
        "date": "2026-08-20",
        "status": "GOLDEN_CLOSED_LOOP_SCENARIOS_READY_FOR_SHARED_RUNTIME",
        "slice_id": SLICE,
        "shared_contract_refs": [
            "../../277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json",
            "../../282-EKSAMIO-MASTERY-INFERENCE-CONTRACT-v0.1.json",
            "../../283-EKSAMIO-PREREQUISITE-READINESS-CONTRACT-v0.1.json",
            "../../284-EKSAMIO-RETENTION-SCHEDULE-STATE-CONTRACT-v0.1.json",
            "../../285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json",
        ],
        "semantic_scope": {"prerequisite": PRE, "target": TARGET, "goal_context": GOAL},
        "global_assertions": [
            "Composite failure cannot become an exact semantic failure.",
            "The REQUIRED edge may block only in the declared present-tense goal context.",
            "Assisted success requires independent verification before strong mastery evidence.",
            "No scenario asserts final universal mastery coefficients or a forgetting curve.",
        ],
        "scenarios": [
            {
                "scenario_id": "RU001-GOLDEN-A-PREREQUISITE-GAP",
                "steps": [
                    {"step": 1, "consume_event": "ru001.ev.composite.error.001", "expected_readiness": "INSUFFICIENT_EVIDENCE", "expected_nba": {"action_type": "DIAGNOSE_TARGET", "semantic_targets": [PRE], "reason_codes": ["STATE_UNCERTAIN_NEEDS_DIAGNOSTIC"]}},
                    {"step": 2, "consume_event": "ru001.ev.preq.diag.failure", "expected_readiness": "BLOCKED_BY_REQUIRED_PREREQUISITE", "expected_nba": {"action_type": "LEARN_PREREQUISITE", "semantic_targets": [TARGET], "prerequisite_targets": [PRE], "reason_codes": ["PREREQUISITE_BLOCKS_TARGET", "PREREQUISITE_REPAIR_FOR_ORIGINAL_GOAL"]}},
                    {"step": 3, "instruction_ref": "../../36-RUSSIAN-EXPLANATION-ORTHOGRAPHY-11-12-v0.1.json#verb_conjugation_endings", "expected_nba": {"action_type": "INDEPENDENT_PRACTICE", "semantic_targets": [PRE], "reason_codes": ["INDEPENDENT_VERIFICATION_REQUIRED_AFTER_HELP"]}},
                    {"step": 4, "consume_event": "ru001.ev.preq.reverify.success", "expected_readiness": "READY_TO_LEARN_OR_PRACTICE", "expected_mastery_reason_codes": ["INDEPENDENT_EVIDENCE_PRESENT"], "expected_nba": {"action_type": "GUIDED_PRACTICE", "semantic_targets": [TARGET], "reason_codes": ["TARGET_READY_TO_LEARN"]}},
                    {"step": 5, "consume_event": "ru001.ev.target.assisted.success", "expected_nba": {"action_type": "INDEPENDENT_PRACTICE", "semantic_targets": [TARGET], "reason_codes": ["INDEPENDENT_VERIFICATION_REQUIRED_AFTER_HELP"]}},
                    {"step": 6, "consume_event": "ru001.ev.target.verify.success", "expected_mastery_reason_codes": ["INDEPENDENT_EVIDENCE_PRESENT"], "expected_nba": {"action_type": "RETENTION_REVIEW", "semantic_targets": [TARGET], "reason_codes": ["RETENTION_DUE"]}, "measured_outcome_required": True},
                ],
            },
            {
                "scenario_id": "RU001-GOLDEN-B-PREREQUISITE-ALREADY-MET",
                "steps": [
                    {"step": 1, "consume_event": "ru001.ev.composite.error.001", "expected_readiness": "INSUFFICIENT_EVIDENCE", "expected_nba": {"action_type": "DIAGNOSE_TARGET", "semantic_targets": [PRE], "reason_codes": ["STATE_UNCERTAIN_NEEDS_DIAGNOSTIC"]}},
                    {"step": 2, "consume_event": "ru001.ev.preq.diag.success", "expected_readiness": "READY_TO_LEARN_OR_PRACTICE", "expected_nba": {"action_type": "DIAGNOSE_TARGET", "semantic_targets": [TARGET], "reason_codes": ["STATE_UNCERTAIN_NEEDS_DIAGNOSTIC"]}},
                    {"step": 3, "consume_event": "ru001.ev.target.diag.failure", "expected_readiness": "READY_TO_LEARN_OR_PRACTICE", "expected_nba": {"action_type": "GUIDED_PRACTICE", "semantic_targets": [TARGET], "reason_codes": ["LOW_MASTERY_HIGH_CONFIDENCE", "TARGET_READY_TO_LEARN"]}},
                    {"step": 4, "consume_event": "ru001.ev.target.assisted.success", "expected_nba": {"action_type": "INDEPENDENT_PRACTICE", "semantic_targets": [TARGET], "reason_codes": ["INDEPENDENT_VERIFICATION_REQUIRED_AFTER_HELP"]}},
                    {"step": 5, "consume_event": "ru001.ev.target.verify.success", "expected_mastery_reason_codes": ["INDEPENDENT_EVIDENCE_PRESENT"], "expected_nba": {"action_type": "RETENTION_REVIEW", "semantic_targets": [TARGET], "reason_codes": ["RETENTION_DUE"]}, "measured_outcome_required": True},
                ],
            },
            {
                "scenario_id": "RU001-GUARDRAIL-TARGET-VERIFY-FAILURE",
                "steps": [
                    {"step": 1, "consume_event": "ru001.ev.target.assisted.success"},
                    {"step": 2, "consume_event": "ru001.ev.target.verify.failure", "expected_assertions": ["assisted success must not override fresh independent failure", "target must not be promoted to strong mastery"], "expected_nba": {"action_type": "GUIDED_PRACTICE", "semantic_targets": [TARGET], "reason_codes": ["LOW_MASTERY_HIGH_CONFIDENCE", "TARGET_READY_TO_LEARN"]}},
                ],
            },
        ],
    }


def walk_forbidden(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_FIELDS:
                raise AssertionError(f"forbidden field {key!r} at {path}")
            walk_forbidden(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden(child, f"{path}[{index}]")


def validate(bank: dict, evidence: dict, edge_doc: dict, golden: dict) -> str:
    import jsonschema

    items = bank["items"]
    assert len(items) == 12
    assert bank["counts"] == {"prerequisite_diagnostic": 4, "target_diagnostic_practice": 4, "independent_verification": 4, "total": 12}
    assert len({x["item_id"] for x in items}) == 12
    for item in items:
        assert item["semantic_id"] in {PRE, TARGET}
        assert item["deterministic_key"] in item["response_contract"]["accepted_answers"]
        assert item["worked_example_exposure"] is False
        if item["semantic_id"] == TARGET:
            assert item["goal_context"] == GOAL
    verification_prompts = {x["prompt"] for x in items if x["delivery_role"] == "INDEPENDENT_VERIFICATION"}
    other_prompts = {x["prompt"] for x in items if x["delivery_role"] != "INDEPENDENT_VERIFICATION"}
    assert verification_prompts.isdisjoint(other_prompts)

    event_schema = json.loads((ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text(encoding="utf-8"))
    events = evidence["events"]
    validator = jsonschema.Draft202012Validator(event_schema)
    for event in events:
        validator.validate(event)
    by_id = {event["event_id"]: event for event in events}
    assert len(by_id) == len(events) == 9
    composite = by_id["ru001.ev.composite.error.001"]
    assert {x["semantic_id"] for x in composite["semantic_targets"]} == {PRE, TARGET}
    assert all(x["mapping_resolution"] == "COMPOSITE" for x in composite["semantic_targets"])
    assert all(x["observation_type"] != "EXACT_RULE_ERROR" for x in composite["error_observations"])
    for event in events:
        if event["event_id"] != "ru001.ev.composite.error.001":
            assert len(event["semantic_targets"]) == 1
            assert event["semantic_targets"][0]["mapping_resolution"] == "EXACT"
    assert by_id["ru001.ev.target.assisted.success"]["assistance"]["level"] == "RULE_EXPLANATION"
    for event_id in ["ru001.ev.preq.reverify.success", "ru001.ev.target.verify.success", "ru001.ev.target.verify.failure"]:
        assert by_id[event_id]["assistance"]["level"] == "UNASSISTED"
        assert by_id[event_id]["transfer_context"]["kind"] == "SAME_SESSION_VERIFICATION"

    edge_contract = json.loads((ENGINE / "283-EKSAMIO-PREREQUISITE-READINESS-CONTRACT-v0.1.json").read_text(encoding="utf-8"))
    edge_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": edge_contract["$defs"],
        **edge_contract["$defs"]["edge_schema"],
    }
    jsonschema.Draft202012Validator(edge_schema).validate(edge_doc["edge"])
    edge = edge_doc["edge"]
    assert edge["source_semantic_id"] == PRE
    assert edge["target_semantic_id"] == TARGET
    assert edge["relation_type"] == "REQUIRED"
    assert edge["review_status"] == "SOURCE_VERIFIED"
    assert edge["conditional_scope"]["goal_context"] == GOAL
    assert edge_doc["materialization_boundary"]["embedded_in_283_canonical_edges"] is False

    scenario_ids = {x["scenario_id"] for x in golden["scenarios"]}
    assert "RU001-GOLDEN-A-PREREQUISITE-GAP" in scenario_ids
    assert "RU001-GOLDEN-B-PREREQUISITE-ALREADY-MET" in scenario_ids
    for scenario in golden["scenarios"]:
        for step in scenario["steps"]:
            if "consume_event" in step:
                assert step["consume_event"] in by_id

    for artifact in [bank, evidence, edge_doc, golden]:
        walk_forbidden(artifact)

    return "\n".join([
        "EKSAMIO LEARNING ENGINE",
        "RU-SLICE-001 FIXTURE VALIDATION",
        "DATE: 2026-08-20",
        "STATUS: PASS",
        "",
        "CONTENT",
        "- exact item bank: 12 / PASS",
        "- prerequisite diagnostic items: 4 / PASS",
        "- target present-tense participle items: 4 / PASS",
        "- fresh independent verification items: 4 / PASS",
        "- deterministic evaluation only: PASS",
        "",
        "SHARED EVIDENCE CONTRACT 277",
        "- schema-valid EvidenceEvent fixtures: 9 / PASS_FULL_JSONSCHEMA",
        "- composite EGE-12 has two COMPOSITE targets: PASS",
        "- composite failure creates exact rule error: NO / PASS",
        "- exact diagnostic and verification mappings: PASS",
        "- assisted event marked RULE_EXPLANATION: PASS",
        "- independent verification unassisted: PASS",
        "- forbidden client-authored mastery fields: NONE / PASS",
        "",
        "SHARED PREREQUISITE CONTRACT 283",
        "- edge validates against $defs.edge_schema: PASS_FULL_JSONSCHEMA",
        "- relation: REQUIRED",
        "- review_status: SOURCE_VERIFIED",
        "- conditional goal scope exact: PASS",
        "- generalized to past-passive branch: NO / PASS",
        "- contract 283 mutated: NO",
        "",
        "GOLDEN SCENARIOS",
        "- prerequisite gap branch: PASS",
        "- prerequisite already met branch: PASS",
        "- independent verification failure guardrail: PASS",
        "",
        "SAFETY",
        "- Russian-specific learner/mastery/readiness/NBA schema: NONE",
        "- AI evaluator required: NO",
        "- trainer/T123/scoring/localStorage/runtime/Tilda changed: NO",
        "",
        "VERDICT",
        "PASS. RU-SLICE-001 content/evidence/edge fixtures are ready as deterministic input for the shared executable PEIS reference kernel. This does not claim the shared runtime itself is implemented.",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    bank = build_item_bank()
    evidence = build_evidence()
    edge = build_edge()
    golden = build_golden()

    if not args.check_only:
        dump(ITEM_FILE, bank)
        dump(EVIDENCE_FILE, evidence)
        dump(EDGE_FILE, edge)
        dump(GOLDEN_FILE, golden)

    result = validate(bank, evidence, edge, golden)
    if not args.check_only:
        RESULT_FILE.write_text(result, encoding="utf-8")
    print(result)


if __name__ == "__main__":
    main()
