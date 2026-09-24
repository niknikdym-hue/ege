#!/usr/bin/env python3
"""Deterministic structural and scope validator for the candidate inventory."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MATERIALIZER = HERE / "materialize_mathematics_full_subject_candidate_inventory_v0_1.py"
OUTPUTS = [
    "MATHEMATICS-FULL-SUBJECT-CANDIDATE-INVENTORY-v0.1.json",
    "MATHEMATICS-FULL-SUBJECT-SOURCE-COVERAGE-v0.1.json",
    "MATHEMATICS-FULL-SUBJECT-DUPLICATE-GRANULARITY-REVIEW-v0.1.json",
    "MATHEMATICS-FULL-SUBJECT-CANDIDATE-INVENTORY-RESULT-v0.1.md",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition: bool, text: str) -> None:
    if not condition:
        raise AssertionError(text)


def main() -> None:
    inv = json.loads((HERE / OUTPUTS[0]).read_text(encoding="utf-8"))
    check(inv["baseline"]["current_main_sha"] == subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip(), "inventory records refreshed current main SHA")
    candidates = inv["candidates"]
    check(candidates, "inventory has candidates")
    ids = [x["candidate_id"] for x in candidates]
    check(len(ids) == len(set(ids)), "candidate IDs are unique")
    required = {"candidate_id", "label_ru", "capability", "domain", "scope_includes", "scope_excludes", "source_refs", "route_applicability", "year_task_mappings", "overlap_with_existing_canonical_ids", "possible_duplicate_candidate_ids", "granularity_status", "source_status", "admission_status"}
    for item in candidates:
        check(required <= set(item), f"required fields: {item.get('candidate_id')}")
        check(item["candidate_id"].startswith("math-candidate-"), f"semantic candidate prefix: {item['candidate_id']}")
        check(not any(ch.isdigit() for ch in item["candidate_id"].replace("v0", "")), f"task number leaked into candidate ID: {item['candidate_id']}")
        check(item["source_refs"], f"source refs: {item['candidate_id']}")
        check(item["route_applicability"] in {"BASE", "PROFILE", "BOTH"}, f"route applicability: {item['candidate_id']}")
        check(item["admission_status"] == "CANDIDATE_NOT_CANONICAL", f"not canonical: {item['candidate_id']}")
        check(item["source_status"] in {"SOURCE_BACKED", "NEEDS_SOURCE_REVIEW"}, f"source status: {item['candidate_id']}")
        check(item["granularity_status"] in {"CLEAR", "NEEDS_SUBJECT_REVIEW"}, f"granularity status: {item['candidate_id']}")
        for item_mapping in item["year_task_mappings"]:
            check(item_mapping["mapping_role"] == "ROUTE_METADATA_NOT_SEMANTIC_IDENTITY", f"mapping role: {item['candidate_id']}")
    check(inv["canonical_admission"]["performed"] is False, "canonical admission not performed")
    check(inv["route_model"]["BASE_and_PROFILE"] == "ROUTE_OVERLAYS_OF_ONE_MATHEMATICS_IDENTITY_MODEL", "shared route-overlay rule")
    registry = json.loads((ROOT / "eksamio-learning-engine/mathematics-identity/MATHEMATICS-SEMANTIC-REGISTRY-v0.1.json").read_text(encoding="utf-8"))
    check(registry["canonical_semantic_identity_count"] == 1, "canonical registry count preserved")
    check(registry["canonical_semantic_identities"][0]["semantic_id"] == "math-probability-classical-equally-likely", "canonical identity preserved")
    review = json.loads((HERE / OUTPUTS[2]).read_text(encoding="utf-8"))
    check(review["needs_subject_review"], "ambiguous granularity surfaced")
    check(review["canonical_comparison"], "existing canonical overlap surfaced")
    coverage = json.loads((HERE / OUTPUTS[1]).read_text(encoding="utf-8"))
    domains = {x["domain"] for x in coverage["domain_coverage"]}
    expected_domains = {"arithmetic_numbers", "algebraic_expressions", "equations_systems", "inequalities_systems", "functions_graphs", "calculus", "probability_statistics", "geometry", "applied_modeling", "advanced_algebra"}
    check(expected_domains <= domains, "major source-supported domains represented")
    check(coverage["explicitly_uncovered_or_needs_review"], "uncovered/needs-review scope explicit")
    # The task permits changes only under this new directory; ensure diff is add-only here.
    changed = subprocess.check_output(["git", "diff", "--name-only", "origin/main"], cwd=ROOT, text=True).splitlines()
    changed += subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
    allowed_prefix = "eksamio-learning-engine/mathematics-identity/full-subject-inventory/"
    check(all(p.startswith(allowed_prefix) for p in changed), f"forbidden changed path(s): {changed}")
    with tempfile.TemporaryDirectory() as tmp:
        temp_out = Path(tmp) / "full-subject-inventory"
        temp_out.mkdir()
        copied = MATERIALIZER.read_text(encoding="utf-8").replace('OUT = Path(__file__).resolve().parent', f'OUT = Path({str(temp_out)!r})')
        temp_script = temp_out / "materialize.py"
        temp_script.write_text(copied, encoding="utf-8")
        subprocess.run([sys.executable, str(temp_script)], check=True, cwd=ROOT)
        for name in OUTPUTS:
            check(digest(HERE / name) == digest(temp_out / name), f"deterministic regeneration: {name}")
    lines = [
        "STATUS=PASS",
        f"CANDIDATE_COUNT={len(candidates)}",
        f"SOURCE_BACKED_COUNT={sum(x['source_status'] == 'SOURCE_BACKED' for x in candidates)}",
        f"NEEDS_SOURCE_REVIEW_COUNT={sum(x['source_status'] == 'NEEDS_SOURCE_REVIEW' for x in candidates)}",
        f"NEEDS_GRANULARITY_REVIEW_COUNT={sum(x['granularity_status'] == 'NEEDS_SUBJECT_REVIEW' for x in candidates)}",
        "ACCEPTED_DEMO_FILES_CHANGED=0",
        "SOURCE_AUTHORITY_FILES_CHANGED=0",
        "SHARED_PEIS_CONTRACTS_CHANGED=0",
        "CANONICAL_IDS_AUTO_ADMITTED=0",
        "DETERMINISTIC_REGENERATION=PASS",
    ]
    (HERE / "MATHEMATICS-FULL-SUBJECT-CANDIDATE-INVENTORY-VALIDATION.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
