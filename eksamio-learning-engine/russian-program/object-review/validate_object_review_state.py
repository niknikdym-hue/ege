#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_object_level_review_queue import build_queue

HERE = Path(__file__).resolve().parent
STATE = json.loads((HERE / "RUSSIAN-OBJECT-REVIEW-STATE-v1.0.json").read_text(encoding="utf-8"))


def main() -> int:
    queue = build_queue()
    emitted = (json.dumps(queue, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    emitted_sha = hashlib.sha256(emitted).hexdigest()

    if STATE["requirements_total"] != queue["summary"]["requirements_total"] != 0:
        raise AssertionError("pinned requirement count drift")
    if STATE["review_batches"]["count"] != queue["summary"]["review_batches_total"]:
        raise AssertionError("pinned review-batch count drift")
    if STATE["review_batches"]["authority"] != "WORK_BATCH_ONLY_NOT_SEMANTIC_ADMISSION":
        raise AssertionError("review batch authority drift")
    if queue["review_batch_authority"] != "WORK_BATCH_ONLY_NOT_SEMANTIC_ADMISSION":
        raise AssertionError("runtime review batch authority drift")

    unit_state = STATE["admission_units"]
    for pinned, runtime_key in (
        ("count", "admission_units_total"),
        ("auto_resolved_canonical_units", "auto_resolved_canonical_units"),
        ("auto_resolved_canonical_requirements", "auto_resolved_canonical_requirements"),
        ("subject_review_required_units", "subject_review_required_units"),
        ("subject_review_required_requirements", "subject_review_required_requirements"),
    ):
        if unit_state[pinned] != queue["summary"][runtime_key]:
            raise AssertionError(f"pinned admission-unit state drift: {pinned}")
    if unit_state["authority"] != "OBJECT_LEVEL_DECISION_GRANULARITY":
        raise AssertionError("admission unit authority label drift")
    if unit_state["signature_fields"] != queue["admission_unit_signature_fields"]:
        raise AssertionError("admission unit signature fields drift")

    context = STATE["proposed_context"]
    if context["review_batches"] != queue["summary"]["proposed_context_batches"]:
        raise AssertionError("proposed-context batch count drift")
    if context["admission_units"] != queue["summary"]["proposed_context_units"]:
        raise AssertionError("proposed-context unit count drift")
    if context["requirements"] != queue["summary"]["proposed_context_requirements"]:
        raise AssertionError("proposed-context requirement count drift")
    if context["authority"] != "PR139_CONTEXT_ONLY_PROPOSED_NOT_CANONICAL":
        raise AssertionError("PR #139 context authority drift")

    if STATE["priority_routes"] != queue["by_priority_route"]:
        raise AssertionError("priority route accounting drift")
    if STATE["determinism"]["normalized_queue_sha256"] != queue["normalized_sha256"]:
        raise AssertionError("pinned normalized queue hash drift")
    if STATE["determinism"]["emitted_json_sha256"] != emitted_sha:
        raise AssertionError("pinned emitted queue hash drift")

    guards = STATE["guards"]
    if guards["module_or_keyword_auto_resolution_allowed"] is not False:
        raise AssertionError("module/keyword auto-resolution guard weakened")
    if queue["module_or_keyword_auto_resolution_allowed"] is not False:
        raise AssertionError("runtime module/keyword auto-resolution guard weakened")
    if guards["review_batch_is_admission_authority"] is not False:
        raise AssertionError("review batch admission guard weakened")
    if guards["pr139_proposed_identity_admission"] != 0:
        raise AssertionError("PR #139 proposed identity was admitted")
    if queue["summary"]["auto_resolved_canonical_units"] != 0:
        raise AssertionError("unexpected automatic canonical admission appeared")
    for key in (
        "russian_content_subject_accepted",
        "public_traffic_enabled",
        "production_charges_enabled",
        "peis_network_writes_enabled",
        "yandex_gateway_apply_enabled",
    ):
        if guards[key] is not False:
            raise AssertionError(f"fail-closed guard drift: {key}")

    print("RUSSIAN_OBJECT_REVIEW_STATE=PASS")
    print(f"review_batches={queue['summary']['review_batches_total']}")
    print(f"admission_units={queue['summary']['admission_units_total']}")
    print(f"requirements={queue['summary']['requirements_total']}")
    print(f"normalized_queue_sha256={queue['normalized_sha256']}")
    print(f"emitted_json_sha256={emitted_sha}")
    print("auto_resolved_canonical_units=0")
    print("review_batch_is_admission_authority=FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
