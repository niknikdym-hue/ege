#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_ege_exact_route_bridge import build_bridge

HERE = Path(__file__).resolve().parent
LEGACY_STATE_PATH = HERE / "RUSSIAN-EGE-ROUTE-BRIDGE-STATE-v1.0.json"
STATE_PATH = HERE / "RUSSIAN-EGE-ROUTE-BRIDGE-STATE-v2.0.json"

EXPECTED_CANDIDATE_CLASSES = {
    "EXACT_MULTI_TASK_CANONICAL_CANDIDATE_SET": 10,
    "EXACT_MULTI_TASK_ROUTE_WITHOUT_CANONICAL_TARGET": 10,
    "EXACT_SINGLE_TASK_COMPOSITE_CANONICAL_SET": 16,
    "EXACT_SINGLE_TASK_ROUTE_WITHOUT_CANONICAL_TARGET": 27,
    "TASK_ID_NOT_PROVEN": 196,
}


def main() -> int:
    legacy = json.loads(LEGACY_STATE_PATH.read_text(encoding="utf-8"))
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    bridge = build_bridge()
    emitted = (json.dumps(bridge, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    emitted_sha = hashlib.sha256(emitted).hexdigest()
    summary = bridge["summary"]

    if legacy.get("status") != "SUPERSEDED" or legacy.get("superseded_by") != STATE_PATH.name:
        raise AssertionError("legacy EGE route bridge state must explicitly point to v2")
    if legacy.get("authority_rule") != "Consumers must use v2.0 for current launch truth; v1.0 must never be interpreted as the current blocker state.":
        raise AssertionError("legacy EGE bridge consumer boundary drift")

    if state["schema_version"] != "2.0.0":
        raise AssertionError("current EGE bridge state schema drift")
    if state["status"] != "EGE_OFFICIAL_TASK_CODE_RELATION_BRIDGE_CANDIDATES_READY_FOR_SUBJECT_REVIEW":
        raise AssertionError("current EGE bridge status drift")

    pinned = state["bridge"]
    for key in (
        "ege_admission_units",
        "ege_requirements",
        "task_proven_units",
        "task_proven_requirements",
        "task_unproven_units",
        "task_unproven_requirements",
        "semantic_admissions",
    ):
        if pinned[key] != summary[key]:
            raise AssertionError(f"pinned EGE bridge summary drift: {key}")
    if pinned["candidate_classes"] != summary["candidate_classes"] != EXPECTED_CANDIDATE_CLASSES:
        raise AssertionError("pinned EGE candidate-class drift")
    if pinned["candidate_classes"] != EXPECTED_CANDIDATE_CLASSES:
        raise AssertionError("unexpected EGE candidate-class truth")
    if pinned["by_document"] != summary["by_document"]:
        raise AssertionError("EGE document accounting drift")
    if pinned["semantic_admissions"] != 0:
        raise AssertionError("EGE bridge must not admit semantics")

    relation = state["source_relation"]
    bridge_relation = bridge["task_code_relation"]
    if relation["source_id"] != "FIPI-EGE-RU-2026-FINAL" or relation["document_id"] != "EGE_SPEC":
        raise AssertionError("pinned FIPI EGE relation authority drift")
    if relation["normalized_relation_sha256"] != bridge_relation["normalized_sha256"]:
        raise AssertionError("pinned FIPI task-code relation hash drift")
    if relation["task_rows"] != 27 or relation["basic_tasks"] != 24 or relation["advanced_tasks"] != 3:
        raise AssertionError("pinned FIPI task-table accounting drift")
    if relation["max_primary_score_total"] != 50:
        raise AssertionError("pinned FIPI EGE score total drift")

    if state["determinism"]["normalized_bridge_sha256"] != bridge["normalized_sha256"]:
        raise AssertionError("pinned normalized EGE bridge hash drift")
    if state["determinism"]["emitted_json_sha256"] != emitted_sha:
        raise AssertionError("pinned emitted EGE bridge hash drift")

    policy = bridge["matching_policy"]
    if policy["task_identity_source"] != "EXPLICIT_FIPI_EGE_2026_TASK_CODE_TABLE":
        raise AssertionError("official task-code relation is not bridge authority")
    if policy["codifier_section_and_exact_code_required"] is not True:
        raise AssertionError("exact section+code matching boundary weakened")
    if policy["dotted_codifier_code_is_not_itself_a_task_id"] is not True:
        raise AssertionError("dotted codifier code was promoted to task ID")
    if policy["module_meaning_keyword_inference_allowed"] is not False:
        raise AssertionError("module/meaning/keyword inference was enabled")
    if policy["candidate_is_admission"] is not False:
        raise AssertionError("EGE candidate was promoted to admission")

    boundary = state["subject_boundary"]
    if boundary["all_candidates_require_subject_review"] is not True:
        raise AssertionError("EGE candidates bypassed subject review")
    if boundary["semantic_admissions"] != 0 or boundary["russian_content_subject_accepted"] is not False:
        raise AssertionError("EGE subject acceptance was falsely claimed")

    guards = state["guards"]
    for key in (
        "dotted_codifier_code_is_task_number",
        "module_meaning_keyword_inference_allowed",
        "candidate_is_admission",
        "public_traffic_enabled",
        "production_charges_enabled",
        "peis_network_writes_enabled",
        "yandex_gateway_apply_enabled",
    ):
        if guards[key] is not False:
            raise AssertionError(f"fail-closed EGE bridge guard drift: {key}")

    print("RUSSIAN_EGE_ROUTE_BRIDGE_STATE_V2=PASS")
    print(f"ege_admission_units={pinned['ege_admission_units']}")
    print(f"ege_requirements={pinned['ege_requirements']}")
    print(f"task_proven_units={pinned['task_proven_units']}")
    print(f"task_proven_requirements={pinned['task_proven_requirements']}")
    print(f"task_unproven_units={pinned['task_unproven_units']}")
    print(f"task_unproven_requirements={pinned['task_unproven_requirements']}")
    print("semantic_admissions=0")
    print(f"normalized_bridge_sha256={bridge['normalized_sha256']}")
    print(f"emitted_json_sha256={emitted_sha}")
    print("legacy_v1_superseded=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
