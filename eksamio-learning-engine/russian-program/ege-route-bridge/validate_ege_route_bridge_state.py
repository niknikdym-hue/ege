#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_ege_exact_route_bridge import build_bridge

HERE = Path(__file__).resolve().parent
STATE_PATH = HERE / "RUSSIAN-EGE-ROUTE-BRIDGE-STATE-v1.0.json"


def main() -> int:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    bridge = build_bridge()
    emitted = (json.dumps(bridge, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    emitted_sha = hashlib.sha256(emitted).hexdigest()

    summary = bridge["summary"]
    if state["status"] != "EGE_ROUTE_BRIDGE_BLOCKED_ON_OFFICIAL_TASK_TO_CODE_RELATION":
        raise AssertionError("pinned EGE bridge blocker status drift")
    if state["ege_admission_units"] != summary["ege_admission_units"] != 0:
        raise AssertionError("pinned EGE admission-unit count drift")
    if state["ege_requirements"] != summary["ege_requirements"]:
        raise AssertionError("pinned EGE requirement count drift")
    if state["candidate_classes"] != summary["candidate_classes"]:
        raise AssertionError("pinned EGE candidate-class drift")
    if state["candidate_classes"] != {"TASK_ID_NOT_PROVEN": 259}:
        raise AssertionError("EGE task-id blocker was weakened")
    if state["proven_tasks"] != sum(summary["proven_task_distribution"].values()) or state["proven_tasks"] != 0:
        raise AssertionError("EGE proven-task state drift")
    if state["semantic_admissions"] != summary["semantic_admissions"] or state["semantic_admissions"] != 0:
        raise AssertionError("EGE semantic-admission guard drift")
    if state["by_document"] != summary["by_document"]:
        raise AssertionError("EGE document accounting drift")

    if state["missing_authority_layer"] != "OFFICIAL_FIPI_EGE_2026_TASK_TO_REQUIREMENT_CONTENT_CODE_RELATION":
        raise AssertionError("exact missing EGE authority layer drift")
    if state["determinism"]["normalized_bridge_sha256"] != bridge["normalized_sha256"]:
        raise AssertionError("pinned normalized EGE bridge hash drift")
    if state["determinism"]["emitted_json_sha256"] != emitted_sha:
        raise AssertionError("pinned emitted EGE bridge hash drift")

    policy = bridge["matching_policy"]
    if policy["task_identity_source"] != "EXPLICIT_CODE_ONLY":
        raise AssertionError("EGE explicit-task-only matching policy drift")
    if policy["dotted_codifier_codes_are_task_ids"] is not False:
        raise AssertionError("dotted FIPI codes were promoted to task IDs")
    if policy["module_meaning_keyword_inference_allowed"] is not False:
        raise AssertionError("module/meaning/keyword inference was enabled")
    if policy["candidate_is_admission"] is not False:
        raise AssertionError("EGE candidate was promoted to admission")

    guards = state["guards"]
    for key in (
        "dotted_codifier_code_can_be_task_id",
        "module_meaning_keyword_inference_allowed",
        "candidate_is_admission",
        "russian_content_subject_accepted",
        "public_traffic_enabled",
        "production_charges_enabled",
        "peis_network_writes_enabled",
        "yandex_gateway_apply_enabled",
    ):
        if guards[key] is not False:
            raise AssertionError(f"fail-closed EGE bridge guard drift: {key}")

    print("RUSSIAN_EGE_ROUTE_BRIDGE_STATE=PASS")
    print(f"ege_admission_units={state['ege_admission_units']}")
    print(f"ege_requirements={state['ege_requirements']}")
    print("candidate[TASK_ID_NOT_PROVEN]=259")
    print("proven_tasks=0")
    print("semantic_admissions=0")
    print(f"normalized_bridge_sha256={bridge['normalized_sha256']}")
    print(f"emitted_json_sha256={emitted_sha}")
    print("missing_authority_layer=OFFICIAL_FIPI_EGE_2026_TASK_TO_REQUIREMENT_CONTENT_CODE_RELATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
