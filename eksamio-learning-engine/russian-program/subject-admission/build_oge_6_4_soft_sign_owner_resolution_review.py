#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
OGE_OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
IDENTITY_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
EXACT_AUTHORITY = HERE / "RUSSIAN-OGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

TARGET_CODE = "6.4"
TARGET_TOPIC = "Ъ and Ь including separating signs"
UNRESOLVED_OWNER = "other active lexical/form soft-sign owners where applicable"
EXPECTED_EXPLICIT_REFS = [
    "school-separating-hard-soft-sign-boundary",
    "school-verb-soft-sign-forms",
]
FIPI_NAVIGATOR_URL = "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf"
FIPI_NAVIGATOR_EVIDENCE = {
    "document": "ФИПИ. Навигатор самостоятельной подготовки к ОГЭ-2026. Русский язык. Орфография",
    "url": FIPI_NAVIGATOR_URL,
    "retrieved_for_review": "2026-08-31",
    "content_code_6_4": "Правописание ъ и ь",
    "source_attested_soft_sign_paragraphs": [
        "5 класс, ч. 1, §12: Разделительные Ъ и Ь",
        "5 класс, ч. 2, §117: Правописание мягкого знака в глаголах во 2-м лице единственного числа",
        "6 класс, ч. 2, §72: Мягкий знак на конце и в середине числительных",
        "7 класс, ч. 1, §46: Мягкий знак после шипящих на конце наречий",
    ],
    "adjacent_codifier_boundaries": {
        "6.6": "suffix spelling across parts of speech, explicitly including -чик-/-щик- and -к-/-ск- families",
        "6.7": "endings across parts of speech, explicitly including noun endings",
    },
    "evidence_policy": "The navigator is used to narrow the owner frontier. A cited textbook paragraph is not by itself an exact component admission; adjacent-code ownership is used only to prevent false 6.4 admission.",
}
REVIEW_ONLY_CANDIDATES = [
    {
        "canonical_ref": "school-adverb-final-soft-sign-after-sibilant-base",
        "review_reason": "Active canonical identity directly decides final Ь after sibilants in adverbs. The FIPI OGE-2026 orthography navigator separately lists the matching soft-sign paragraph while code 6.6 lists adverb suffix-vowel rules, not this Ь decision.",
        "provenance": "253-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-C-O26-O35-v0.1.json",
        "source_bound_disposition": "FIPI_NAVIGATOR_SUPPORTS_6_4_OWNER_CANDIDATE",
        "official_source_evidence": "7 класс, ч. 1, §46: Мягкий знак после шипящих на конце наречий",
    },
    {
        "canonical_ref": "school-adjective-soft-sign-before-sk-base",
        "review_reason": "The identity contains a soft-sign decision, but it belongs to the adjective -К-/-СК- suffix family. FIPI code 6.6 explicitly owns the -к-/-ск- suffix family, so name overlap must not create a 6.4 admission.",
        "provenance": "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25-v0.1.json",
        "source_bound_disposition": "ADJACENT_CODE_6_6_SUFFIX_OWNER_NOT_6_4_ADMITTED",
        "official_source_evidence": "6.6 explicitly includes adjective suffixes -к- and -ск-; navigator example §68 covers the -К-/-СК- distinction",
    },
    {
        "canonical_ref": "school-noun-agent-suffix-chik-shchik-soft-sign",
        "review_reason": "The identity contains Ь before -ЩИК-, but FIPI code 6.6 explicitly owns noun suffixes -чик-/-щик-. It must not be moved into 6.4 merely because the canonical label contains soft-sign wording.",
        "provenance": "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25-v0.1.json",
        "source_bound_disposition": "ADJACENT_CODE_6_6_SUFFIX_OWNER_NOT_6_4_ADMITTED",
        "official_source_evidence": "6.6 explicitly includes noun suffixes -чик- and -щик-; navigator example §52 covers this family",
    },
    {
        "canonical_ref": "school-numeral-orthography-base",
        "review_reason": "The active numeral orthography identity includes the internal-soft-sign branch for 50–80 and 500–900. The FIPI navigator explicitly lists a paragraph on final/internal numeral Ь; code 6.8 separately owns solid/hyphen/separate numeral spelling and code 6.7 owns numeral endings.",
        "provenance": "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25-v0.1.json",
        "source_bound_disposition": "FIPI_NAVIGATOR_SUPPORTS_6_4_OWNER_CANDIDATE",
        "official_source_evidence": "6 класс, ч. 2, §72: Мягкий знак на конце и в середине числительных",
    },
    {
        "canonical_ref": "school-noun-genitive-plural-ending-system",
        "review_reason": "The canonical label includes final Ь in special genitive-plural groups, but this is an inflectional ending system. FIPI code 6.7 explicitly owns noun endings; therefore this overlap must not be silently admitted to 6.4.",
        "provenance": "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25-v0.1.json",
        "source_bound_disposition": "ADJACENT_CODE_6_7_ENDING_OWNER_NOT_6_4_ADMITTED",
        "official_source_evidence": "6.7 explicitly includes unstressed noun endings; canonical source O17 defines this identity as a noun-ending family",
    },
    {
        "canonical_ref": "school-verbal-noun-nie-nye-semantic-boundary",
        "review_reason": "The canonical identity directly contrasts -НИЕ/-НЬЕ, so it is a real sign-presence overlap that the earlier four-row frontier omitted. Current FIPI navigator evidence does not explicitly map this lexical/stylistic suffix boundary to 6.4 or another OGE code; exact ownership therefore remains unresolved.",
        "provenance": "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25-v0.1.json",
        "source_bound_disposition": "SOURCE_BOUNDARY_UNRESOLVED_NO_6_4_ADMISSION",
        "official_source_evidence": "No explicit -НИЕ/-НЬЕ paragraph is named in the current FIPI OGE-2026 orthography navigator examples; absence is not treated as proof of exclusion",
    },
]


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def build_review() -> dict[str, Any]:
    overlay = load_json(OGE_OVERLAY)
    inventory = load_json(IDENTITY_INVENTORY)
    exact = load_json(EXACT_AUTHORITY)

    rows = [
        row
        for row in overlay.get("orthography_codifier_overlay") or []
        if isinstance(row, dict) and str(row.get("position")) == TARGET_CODE
    ]
    if len(rows) != 1:
        raise ValueError("OGE 6.4 overlay row must exist exactly once")
    row = rows[0]
    if row.get("topic") != TARGET_TOPIC:
        raise ValueError("OGE 6.4 topic drift")
    if row.get("classification") != "SCHOOL_IDENTITY_ROUTE":
        raise ValueError("OGE 6.4 classification drift")

    owners = [str(value) for value in row.get("owners") or []]
    if owners != EXPECTED_EXPLICIT_REFS + [UNRESOLVED_OWNER]:
        raise ValueError("OGE 6.4 owner frontier changed; re-adjudication required")
    if UNRESOLVED_OWNER not in owners:
        raise ValueError("OGE 6.4 unresolved owner placeholder unexpectedly disappeared")

    decisions = [item for item in exact.get("decisions") or [] if isinstance(item, dict)]
    accepted_6_4 = [item for item in decisions if str(item.get("content_code")) == TARGET_CODE]
    if accepted_6_4:
        raise ValueError("OGE 6.4 cannot be exact-accepted while its overlay retains an unresolved owner placeholder")

    objects = [item for item in inventory.get("objects") or [] if isinstance(item, dict)]
    inventory_rows = [item for item in objects if item.get("source_id") == "oge-2026-orthography-6-4"]
    if len(inventory_rows) != 1:
        raise ValueError("OGE 6.4 identity-inventory source row must exist exactly once")
    inventory_row = inventory_rows[0]
    if inventory_row.get("review_status") != "reviewed":
        raise ValueError("OGE 6.4 inventory source row is not reviewed")
    if inventory_row.get("audit_classification") != "EXAM_ROUTE_ONLY":
        raise ValueError("OGE 6.4 inventory classification drift")
    inventory_refs = sorted(str(ref) for ref in inventory_row.get("current_semantic_refs") or [])
    if inventory_refs != sorted(EXPECTED_EXPLICIT_REFS):
        raise ValueError("OGE 6.4 identity-inventory refs drifted from the explicit overlay refs")

    known_refs: set[str] = set()
    for item in objects:
        source_id = str(item.get("source_id") or "")
        if source_id.startswith("school-"):
            known_refs.add(source_id)
        known_refs.update(str(ref) for ref in item.get("current_semantic_refs") or [] if str(ref).startswith("school-"))

    missing = [
        item["canonical_ref"]
        for item in REVIEW_ONLY_CANDIDATES
        if item["canonical_ref"] not in known_refs
    ]
    if missing:
        raise ValueError("review-only canonical refs missing from current inventory: " + ",".join(missing))

    candidate_rows = []
    for item in REVIEW_ONLY_CANDIDATES:
        candidate_rows.append(
            {
                **item,
                "review_disposition": "REVIEW_ONLY_NOT_OGE_6_4_OWNER_ADMITTED",
                "exact_oge_6_4_owner_proven": False,
                "admission_effect": "NONE",
            }
        )

    supported = [
        row for row in candidate_rows if row["source_bound_disposition"] == "FIPI_NAVIGATOR_SUPPORTS_6_4_OWNER_CANDIDATE"
    ]
    adjacent_nonowners = [
        row for row in candidate_rows if row["source_bound_disposition"].startswith("ADJACENT_CODE_")
    ]
    unresolved = [
        row for row in candidate_rows if row["source_bound_disposition"] == "SOURCE_BOUNDARY_UNRESOLVED_NO_6_4_ADMISSION"
    ]

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_REVIEW_REQUIRED",
        "authority_issue": 161,
        "scope": "OGE_2026_ORTHOGRAPHY_CODE_6_4_SOFT_SIGN_OWNER_RESOLUTION",
        "target": {
            "document_id": "OGE_COD",
            "content_code": TARGET_CODE,
            "topic": TARGET_TOPIC,
            "classification": str(row["classification"]),
        },
        "official_source_review": FIPI_NAVIGATOR_EVIDENCE,
        "current_overlay_truth": {
            "explicit_canonical_refs": EXPECTED_EXPLICIT_REFS,
            "unresolved_owner_placeholder": UNRESOLVED_OWNER,
            "unresolved_placeholder_present": True,
            "overlay_is_complete_exact_owner_list": False,
        },
        "identity_inventory_truth": {
            "source_id": str(inventory_row["source_id"]),
            "review_status": str(inventory_row["review_status"]),
            "audit_classification": str(inventory_row["audit_classification"]),
            "current_semantic_refs": inventory_refs,
            "inventory_refs_prove_overlay_completeness": False,
        },
        "exact_acceptance_truth": {
            "current_exact_acceptance_for_6_4": False,
            "accepted_oge_orthography_codes": sorted(str(item.get("content_code")) for item in decisions),
            "exact_acceptance_requires_complete_placeholder_free_owner_list": True,
        },
        "review_only_overlap_candidates": candidate_rows,
        "source_bound_frontier": {
            "fipi_supported_6_4_owner_candidates_not_yet_admitted": [row["canonical_ref"] for row in supported],
            "adjacent_code_nonowner_candidates": [row["canonical_ref"] for row in adjacent_nonowners],
            "still_unresolved_candidates": [row["canonical_ref"] for row in unresolved],
            "frontier_complete_for_exact_acceptance": False,
        },
        "summary": {
            "explicit_overlay_canonical_refs": len(EXPECTED_EXPLICIT_REFS),
            "unresolved_owner_placeholders": 1,
            "review_only_overlap_candidates": len(candidate_rows),
            "fipi_supported_6_4_owner_candidates_not_yet_admitted": len(supported),
            "adjacent_code_nonowner_candidates": len(adjacent_nonowners),
            "still_unresolved_candidates": len(unresolved),
            "semantic_admissions": 0,
            "object_level_closures": 0,
            "false_exact_mastery_admissions": 0,
        },
        "policy": {
            "reuse_first": True,
            "review_only_candidate_is_exact_owner": False,
            "keyword_or_name_overlap_is_exact_binding": False,
            "inventory_route_refs_are_complete_owner_proof": False,
            "official_navigator_paragraph_is_exact_component_admission": False,
            "adjacent_codifier_boundary_prevents_false_6_4_admission": True,
            "placeholder_may_be_silently_dropped": False,
            "exact_acceptance_allowed_while_placeholder_remains": False,
            "semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
        },
        "admission_effect": "NONE",
        "next_safe_step": "Resolve school-verbal-noun-nie-nye-semantic-boundary against exact official OGE scope, then independently prove whether the two FIPI-supported candidates belong in the complete 6.4 owner list. Do not remove the placeholder or exact-accept 6.4 before that proof is complete.",
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
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
        print("OGE_6_4_SOFT_SIGN_OWNER_RESOLUTION_REVIEW=PASS")
        for key, value in result["summary"].items():
            print(f"{key}={value}")
        print(f"normalized_sha256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
