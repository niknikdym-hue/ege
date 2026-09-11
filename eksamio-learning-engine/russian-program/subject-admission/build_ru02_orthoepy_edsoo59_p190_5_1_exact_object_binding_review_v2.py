#!/usr/bin/env python3
"""Compatibility-fixed exact object-binding review for EDSOO59 p.190 5.1 RU02 orthoepy.

The original bounded review expected stress evidence ids directly on the bounded
semantic acceptance artifact. That artifact intentionally records semantic
acceptance but not the later component-specific learner-evidence ids. The exact
accepted sibling authority for EDSOO59 p.187 4.1.6 is the current durable source
that pins those ids. This wrapper verifies that authority first, overlays only
that already-accepted evidence into a temporary in-memory/file view, and then
runs the original fail-closed review unchanged. No canonical authority file is
mutated and no sibling acceptance is inherited by the p.190 object.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import runpy
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CORE = HERE / "build_ru02_orthoepy_edsoo59_p190_5_1_exact_object_binding_review.py"
STRESS_ACCEPTANCE = HERE / "RU02-NORMATIVE-STRESS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
P187_ACCEPTANCE = HERE / "RU02-EDSOO59-P187-4-1-6-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

STRESS_REF = "ru-orthoepy-normative-stress-selection"
EXPECTED_STRESS_EVIDENCE = ["p02-u3-v1", "p02-u3-v2", "p02-u3-v3", "p02-u3-v4"]
EXPECTED_CORE_STATUS = (
    "CENTRAL_BRAIN_RU02_EDSOO59_P190_5_1_EXACT_OBJECT_BINDING_REVIEW_"
    "READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED"
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def exact_stress_evidence_from_accepted_sibling() -> list[str]:
    stress = load(STRESS_ACCEPTANCE)
    if stress.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU02_NORMATIVE_STRESS_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("stress bounded semantic acceptance status drift")
    decisions = [
        row
        for row in stress.get("decisions", [])
        if isinstance(row, dict) and row.get("accepted_semantic_id") == STRESS_REF
    ]
    if len(decisions) != 1:
        raise ValueError("stress bounded semantic decision missing or duplicated")
    decision = decisions[0]
    if decision.get("candidate_ref") != "candidate-018":
        raise ValueError("stress candidate identity drift")
    if decision.get("source_taxonomy_id") != "normative_stress_selection":
        raise ValueError("stress taxonomy drift")
    if decision.get("source_evidence_status") != "confirmed":
        raise ValueError("stress source evidence is not confirmed")
    if decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise ValueError("stress semantic boundary drift")
    if (stress.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("stress bounded semantic acceptance opened false exact mastery")

    p187 = load(P187_ACCEPTANCE)
    if p187.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_RU02_EDSOO59_P187_4_1_6_CANONICAL_COMPONENT_SET":
        raise ValueError("p187 exact accepted sibling status drift")
    p187_decision = p187.get("decision") or {}
    if p187_decision.get("admission_unit_id") != "RAU-da83bb720dea792b3afb":
        raise ValueError("p187 exact sibling admission-unit drift")
    if p187_decision.get("requirement_id") != "RSK-EDSOO59-4-1-6-P187":
        raise ValueError("p187 exact sibling requirement drift")
    evidence_map = p187_decision.get("component_specific_independent_evidence") or {}
    evidence = evidence_map.get(STRESS_REF)
    if evidence != EXPECTED_STRESS_EVIDENCE:
        raise ValueError("p187 accepted stress evidence drift")
    if p187_decision.get("independent_evidence_items") != 9:
        raise ValueError("p187 accepted sibling evidence count drift")
    if (p187.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("p187 exact sibling opened false exact mastery")
    return list(evidence)


def build_review() -> dict[str, Any]:
    exact_stress_evidence = exact_stress_evidence_from_accepted_sibling()
    stress = load(STRESS_ACCEPTANCE)
    overlay = copy.deepcopy(stress)
    decisions = [
        row
        for row in overlay.get("decisions", [])
        if isinstance(row, dict) and row.get("accepted_semantic_id") == STRESS_REF
    ]
    if len(decisions) != 1:
        raise ValueError("stress overlay decision missing or duplicated")
    if "independent_verification_item_ids" in decisions[0]:
        if decisions[0]["independent_verification_item_ids"] != exact_stress_evidence:
            raise ValueError("stress artifact gained conflicting evidence ids")
    else:
        decisions[0]["independent_verification_item_ids"] = exact_stress_evidence

    core = runpy.run_path(str(CORE), run_name="ru02_p190_review_core")
    core_build = core.get("build_review")
    if not callable(core_build):
        raise ValueError("core p190 review build_review missing")

    with tempfile.TemporaryDirectory(prefix="ru02-p190-review-") as tmpdir:
        overlay_path = Path(tmpdir) / STRESS_ACCEPTANCE.name
        overlay_path.write_text(
            json.dumps(overlay, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        core_build.__globals__["STRESS_ACCEPTANCE"] = overlay_path
        result = core_build()

    if result.get("status") != EXPECTED_CORE_STATUS:
        raise ValueError("core p190 review status drift")
    reuse = result.get("reuse_first_owner_resolution") or {}
    if reuse.get("canonical_component_refs") != [
        "ru-orthoepy-normative-pronunciation-selection",
        STRESS_REF,
    ]:
        raise ValueError("p190 review component refs drift")
    if reuse.get("independent_evidence_items") != 9:
        raise ValueError("p190 review evidence count drift")
    readiness = result.get("acceptance_readiness") or {}
    if readiness.get("object_accepted_by_this_review") is not False:
        raise ValueError("p190 review unexpectedly accepted object")
    policy = result.get("policy") or {}
    if policy.get("shared_sibling_evidence_can_auto_close_target") is not False:
        raise ValueError("p190 review weakened sibling fail-closed boundary")
    summary = result.get("summary") or {}
    for key in (
        "semantic_admissions",
        "object_level_admission_units_closed",
        "object_level_requirements_closed",
        "exact_mastery_admissions",
        "false_exact_mastery_admissions",
    ):
        if summary.get(key) != 0:
            raise ValueError(f"p190 review opened forbidden admission: {key}")

    result["validation_provenance"] = {
        "stress_bounded_semantic_artifact_is_component_evidence_registry": False,
        "stress_component_evidence_source": "accepted_exact_sibling_authority",
        "accepted_exact_sibling_requirement_id": "RSK-EDSOO59-4-1-6-P187",
        "accepted_exact_sibling_admission_unit_id": "RAU-da83bb720dea792b3afb",
        "stress_component_evidence_refs": exact_stress_evidence,
        "canonical_authority_file_mutated": False,
        "sibling_acceptance_inherited_by_target": False,
    }
    result.pop("normalized_sha256", None)
    result["normalized_sha256"] = hashlib.sha256(canonical_bytes(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_review()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        summary = result["summary"]
        print("RU02_EDSOO59_P190_5_1_EXACT_OBJECT_BINDING_REVIEW_V2=PASS")
        print("STRESS_EVIDENCE_SOURCE=ACCEPTED_EXACT_SIBLING_AUTHORITY")
        print("OBJECT_CLOSURES_BY_REVIEW=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print(f"CURRENT_SUBJECT_REVIEW_UNITS_REMAINING={summary['current_subject_review_units_remaining']}")
        print(f"CURRENT_SUBJECT_REVIEW_REQUIREMENTS_REMAINING={summary['current_subject_review_requirements_remaining']}")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
