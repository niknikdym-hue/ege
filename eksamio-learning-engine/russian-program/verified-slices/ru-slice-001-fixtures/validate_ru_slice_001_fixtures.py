#!/usr/bin/env python3
import json
import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(os.environ.get("EKSAMIO_ENGINE_ROOT", str(HERE.parents[2]))).resolve()

A = "school-verb-personal-ending-conjugation-base"
B = "school-participle-vowel-suffix-conjugation-base"
GOAL = "present-tense participle suffix selection"

ITEM_BANK = HERE / "RU-SLICE-001-ITEM-BANK-v0.1.json"
EVIDENCE = HERE / "RU-SLICE-001-EVIDENCE-FIXTURES-v0.1.json"
EDGE = HERE / "RU-SLICE-001-PREREQUISITE-EDGE-v0.1.json"
GOLDEN = HERE / "RU-SLICE-001-GOLDEN-SCENARIOS-v0.1.json"
EVENT_SCHEMA = ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json"
PREREQ_SCHEMA = ENGINE / "283-EKSAMIO-PREREQUISITE-READINESS-CONTRACT-v0.1.json"

FORBIDDEN_RECURSIVE_FIELDS = {
    "effective_weight", "mastery_weight", "semantic_contribution_percentage",
    "canonical_mastery", "mastery_estimate",
}

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def fail(msg):
    raise SystemExit("FAIL: " + msg)

def require(cond, msg):
    if not cond:
        fail(msg)

def walk_keys(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from walk_keys(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk_keys(v)

def validate_jsonschema(events, edges):
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        fail("jsonschema library is required for shared-contract validation: " + str(exc))
    event_schema = load(EVENT_SCHEMA)
    event_validator = Draft202012Validator(event_schema, format_checker=FormatChecker())
    event_errors = []
    for event in events:
        errs = sorted(event_validator.iter_errors(event), key=lambda e: list(e.path))
        if errs:
            event_errors.append((event["event_id"], errs[0].message))
    require(not event_errors, "EvidenceEvent schema errors: " + repr(event_errors))
    prereq_contract = load(PREREQ_SCHEMA)
    edge_wrapper_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": prereq_contract["$defs"],
        "$ref": "#/$defs/edge_schema",
    }
    edge_validator = Draft202012Validator(edge_wrapper_schema, format_checker=FormatChecker())
    edge_errors = []
    for edge in edges:
        errs = sorted(edge_validator.iter_errors(edge), key=lambda e: list(e.path))
        if errs:
            edge_errors.append((edge.get("source_semantic_id"), errs[0].message))
    require(not edge_errors, "Prerequisite edge schema errors: " + repr(edge_errors))

def main():
    bank = load(ITEM_BANK)
    evidence = load(EVIDENCE)
    edge_doc = load(EDGE)
    golden = load(GOLDEN)

    events = []
    part_event_count = 0
    for part in evidence.get("parts", []):
        part_doc = load(HERE / part["file"])
        require(part_doc.get("event_count") == len(part_doc.get("events", [])),
                f"evidence part count mismatch: {part['file']}")
        require(part.get("events") == len(part_doc["events"]),
                f"evidence manifest part count mismatch: {part['file']}")
        events.extend(part_doc["events"])
        part_event_count += len(part_doc["events"])
    require(part_event_count == evidence.get("event_count"), "evidence manifest total count mismatch")

    items = bank["items"]
    require(len(items) == 12, f"item count {len(items)} != 12")
    ids = [x["item_id"] for x in items]
    require(len(ids) == len(set(ids)), "duplicate item_id")
    roles = Counter(x["item_role"] for x in items)
    require(roles == Counter({"PREREQUISITE_DIAGNOSTIC":4,"TARGET_DIAGNOSTIC":4,"INDEPENDENT_VERIFICATION":4}),
            f"unexpected item-role counts: {roles}")

    allowed_ids = {A, B}
    for item in items:
        target = item.get("semantic_target") or {}
        require(target.get("semantic_id") in allowed_ids, f"unknown semantic target in {item['item_id']}")
        require(target.get("mapping_resolution") == "EXACT", f"non-exact item target in {item['item_id']}")
        require(item.get("deterministic_check", {}).get("type") == "NORMALIZED_EXACT", f"non-deterministic checker in {item['item_id']}")
        require(item.get("deterministic_check", {}).get("accepted_answers"), f"missing accepted answer in {item['item_id']}")
        require(item.get("source_rule_refs"), f"missing provenance in {item['item_id']}")
        require(item.get("original_eksamio_content") is True, f"item not marked original in {item['item_id']}")
        if target["semantic_id"] == B:
            require(item.get("goal_context") == GOAL, f"wrong target goal in {item['item_id']}")
            require(A in item.get("prerequisite_refs", []), f"missing prerequisite ref in {item['item_id']}")
        if item["item_role"] == "INDEPENDENT_VERIFICATION":
            require(item.get("assistance_policy") == "UNASSISTED_ONLY", f"verification allows assistance in {item['item_id']}")

    blocked_answers = set(bank["independence_guard"]["known_worked_example_forms_not_allowed_as_verification"])
    verification_answers = {x["deterministic_check"]["accepted_answers"][0].lower() for x in items if x["item_role"] == "INDEPENDENT_VERIFICATION"}
    require(not (blocked_answers & verification_answers), "verification reuses source worked-example answer(s): " + repr(blocked_answers & verification_answers))
    diagnostic_answers = {x["deterministic_check"]["accepted_answers"][0].lower() for x in items if x["item_role"] != "INDEPENDENT_VERIFICATION"}
    require(not (diagnostic_answers & verification_answers), "verification reuses a diagnostic answer/context")

    require(evidence.get("event_count") == len(events), "event_count mismatch")
    event_ids = [e["event_id"] for e in events]
    require(len(event_ids) == len(set(event_ids)), "duplicate event_id")
    item_map = {x["item_id"]: x for x in items}
    composite_count = 0
    exact_fail_count = 0
    for event in events:
        forbidden = FORBIDDEN_RECURSIVE_FIELDS.intersection(walk_keys(event))
        require(not forbidden, f"forbidden client mastery field(s) in {event['event_id']}: {forbidden}")
        targets = event["semantic_targets"]
        if event["source"]["object_id"] == "ege-ru-12-2026-12-01":
            composite_count += 1
            require({x["semantic_id"] for x in targets} == {A, B}, f"composite target set wrong in {event['event_id']}")
            require(all(x["mapping_resolution"] == "COMPOSITE" for x in targets), f"composite mapping incorrectly resolved in {event['event_id']}")
            for obs in event["error_observations"]:
                require(obs["semantic_id"] is None, f"composite event assigns exact semantic error in {event['event_id']}")
                require(obs["observation_type"] == "UNKNOWN_OR_INSUFFICIENT_PRECISION", f"composite event has over-precise error type in {event['event_id']}")
                require(obs["precision"] == "UNKNOWN", f"composite event has over-precise error precision in {event['event_id']}")
        else:
            require(len(targets) == 1, f"exact item event has !=1 target in {event['event_id']}")
            require(targets[0]["mapping_resolution"] == "EXACT", f"exact item event not EXACT in {event['event_id']}")
            item_id = event["source"]["object_id"]
            require(item_id in item_map, f"event references unknown item {item_id}")
            require(targets[0]["semantic_id"] == item_map[item_id]["semantic_target"]["semantic_id"], f"event semantic target mismatch for {item_id}")
            if event["result"]["correctness"] is False:
                exact_fail_count += 1
                require(any(o["observation_type"] == "EXACT_RULE_ERROR" and o["semantic_id"] == targets[0]["semantic_id"] and o["precision"] == "EXACT" for o in event["error_observations"]), f"exact failure lacks exact error observation in {event['event_id']}")
            if item_map[item_id]["item_role"] == "INDEPENDENT_VERIFICATION":
                require(event["assistance"]["level"] == "UNASSISTED", f"verification event assisted in {event['event_id']}")
                require(event["transfer_context"]["kind"] == "SAME_SESSION_VERIFICATION", f"verification transfer context wrong in {event['event_id']}")

    require(composite_count >= 1, "missing composite EGE-12 fixture")
    require(exact_fail_count >= 4, "not enough exact failure fixtures")
    roles_text = " ".join(e["subject_extension"]["subject_payload"].get("fixture_role", "") for e in events)
    for required in ["PREREQUISITE_DIAGNOSTIC_FAILURE","PREREQUISITE_DIAGNOSTIC_SUCCESS","TARGET_DIAGNOSTIC_FAILURE","TARGET_DIAGNOSTIC_SUCCESS","ASSISTED_PREREQUISITE_PRACTICE","INDEPENDENT_PREREQUISITE_VERIFICATION_SUCCESS","INDEPENDENT_PREREQUISITE_VERIFICATION_FAILURE","INDEPENDENT_TARGET_VERIFICATION_SUCCESS","INDEPENDENT_TARGET_VERIFICATION_FAILURE"]:
        require(required in roles_text, "missing required evidence fixture role: " + required)

    edges = edge_doc["edges"]
    require(len(edges) == 1 and edge_doc.get("edge_count") == 1, "edge fixture must contain exactly one edge")
    edge = edges[0]
    require(edge["source_semantic_id"] == A, "wrong prerequisite edge source")
    require(edge["target_semantic_id"] == B, "wrong prerequisite edge target")
    require(edge["relation_type"] == "REQUIRED", "edge is not REQUIRED")
    require(edge["review_status"] == "SOURCE_VERIFIED", "edge not source verified")
    require(edge["admission_scope"] == "CANONICAL_GRAPH", "edge not canonical graph candidate")
    require(edge["conditional_scope"]["subject_id"] == "russian", "edge subject scope wrong")
    require(edge["conditional_scope"]["goal_context"] == GOAL, "edge goal scope wrong")
    require(edge_doc.get("canonical_contract_mutated") is False, "fixture claims immutable contract mutation")
    require(len(edge["provenance"]) >= 3, "edge provenance insufficient")

    scenarios = golden["scenarios"]
    require({s["scenario_id"] for s in scenarios} == {"ru001-s01-prerequisite-gap-confirmed","ru001-s02-prerequisite-already-met"}, "golden scenario set mismatch")
    valid_event_ids = set(event_ids)
    for scenario in scenarios:
        for step in scenario["steps"]:
            require(step["consume_event"] in valid_event_ids, f"golden scenario references unknown event {step['consume_event']}")
    require("threshold" in golden["no_invented_threshold_policy"].lower(), "missing no-invented-threshold assertion")

    validate_jsonschema(events, edges)
    print("RU-SLICE-001 FIXTURE VALIDATION: PASS")
    print("ITEMS: 12 (4 prerequisite diagnostic / 4 target diagnostic / 4 independent verification)")
    print(f"EVIDENCE_EVENTS: {len(events)} / JSONSCHEMA PASS")
    print("COMPOSITE EGE-12 SAFETY: PASS")
    print("CONDITIONAL REQUIRED EDGE: PASS / JSONSCHEMA PASS")
    print("GOLDEN SCENARIOS: 2 / PASS")
    print("RUSSIAN-SPECIFIC MASTERY/READINESS/NBA FIELDS: NONE")
    print("PRODUCTION/RUNTIME MUTATION: OUTSIDE FIXTURE PACKAGE / FORBIDDEN BY SCOPE")

if __name__ == "__main__":
    main()
