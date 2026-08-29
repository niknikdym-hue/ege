#!/usr/bin/env python3
from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BUILDER = HERE / "build_russian_subject_semantic_acceptance_packet.py"


def main() -> int:
    namespace = runpy.run_path(str(BUILDER))
    payload: dict[str, Any] = namespace["build_packet"]()
    if payload.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED":
        raise AssertionError("semantic packet status drift")
    summary = payload.get("summary", {})
    if summary.get("semantic_review_groups") != 74:
        raise AssertionError("semantic review group count drift")
    if summary.get("admission_units") != 1316 or summary.get("requirements") != 1391:
        raise AssertionError("semantic packet coverage drift")
    if summary.get("canonical_semantic_admissions") != 0 or summary.get("ru_proposal_admissions") != 0:
        raise AssertionError("semantic packet silently admitted identities")
    if summary.get("russian_content_ready") is not False:
        raise AssertionError("semantic packet falsely reports Russian content ready")
    explicit = int(summary.get("groups_with_explicit_candidate_evidence", -1))
    decomposition = int(summary.get("groups_requiring_exact_source_decomposition", -1))
    if explicit + decomposition != 74 or explicit < 1:
        raise AssertionError("semantic packet next-action partition drift")

    groups = payload.get("groups")
    if not isinstance(groups, list) or len(groups) != 74:
        raise AssertionError("semantic packet group array drift")
    ids = [str(group.get("group_id", "")) for group in groups]
    meanings = [str(group.get("normalized_meaning", "")) for group in groups]
    if len(ids) != len(set(ids)) or len(meanings) != len(set(meanings)):
        raise AssertionError("semantic packet duplicates group ids or meanings")
    if sum(int(group.get("admission_units", 0)) for group in groups) != 1316:
        raise AssertionError("semantic packet unit sum drift")
    if sum(int(group.get("requirements", 0)) for group in groups) != 1391:
        raise AssertionError("semantic packet requirement sum drift")

    allowed_status = {
        "CENTRAL_BRAIN_COMPONENT_ACCEPTANCE_REQUIRED",
        "EXACT_SOURCE_COMPONENT_DECOMPOSITION_REQUIRED",
    }
    for group in groups:
        if group.get("status") not in allowed_status:
            raise AssertionError("semantic packet contains an unsupported group status")
        if group.get("admission_effect") != "NONE_UNTIL_EXPLICIT_SUBJECT_ACCEPTANCE":
            raise AssertionError("semantic packet admission boundary weakened")
        refs = group.get("explicit_semantic_candidate_refs")
        if not isinstance(refs, list):
            raise AssertionError("semantic candidate refs must be explicit list")
        if group.get("status") == "CENTRAL_BRAIN_COMPONENT_ACCEPTANCE_REQUIRED" and not refs:
            raise AssertionError("component-acceptance group lacks explicit candidate evidence")
        if group.get("status") == "EXACT_SOURCE_COMPONENT_DECOMPOSITION_REQUIRED" and refs:
            raise AssertionError("source-decomposition group contains unreviewed semantic candidate refs")

    policy = payload.get("policy", {})
    if policy.get("semantic_auto_admission_allowed") is not False:
        raise AssertionError("semantic auto-admission was enabled")
    if policy.get("keyword_or_fuzzy_mapping_allowed") is not False:
        raise AssertionError("keyword/fuzzy semantic mapping was enabled")
    if policy.get("module_only_mapping_allowed") is not False:
        raise AssertionError("module-only semantic mapping was enabled")
    if policy.get("reuse_existing_semantics_first") is not True:
        raise AssertionError("reuse-first policy weakened")

    print("RUSSIAN_SUBJECT_SEMANTIC_ACCEPTANCE_PACKET=PASS")
    print("SEMANTIC_REVIEW_GROUPS=74")
    print(f"GROUPS_WITH_EXPLICIT_CANDIDATE_EVIDENCE={explicit}")
    print(f"GROUPS_REQUIRING_EXACT_SOURCE_DECOMPOSITION={decomposition}")
    print("CANONICAL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=0")
    print("RUSSIAN_CONTENT_READY=false")
    print(f"NORMALIZED_PACKET_SHA256={payload['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
