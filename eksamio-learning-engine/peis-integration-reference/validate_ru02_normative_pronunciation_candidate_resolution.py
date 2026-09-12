#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE / "RU02-NORMATIVE-PRONUNCIATION-SOURCE-BACKED-CANDIDATE-RESOLUTION-v0.1.json"
EXPECTED_RU164 = "7edddb9f9764b5e8cdf7e2653c425e5f90c4ffe9"
EXPECTED_MEANING = "Применять нормативное произношение и ударение."
EXPECTED_STRESS_CANDIDATES = {f"candidate-{number:03d}" for number in range(18, 25)}


def run_json(script: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["python3", str(script), "--emit"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ru164-root", required=True)
    args = parser.parse_args()

    ru164 = Path(args.ru164_root).resolve()
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    assert artifact["status"] == "BOUNDED_SOURCE_BACKED_CANDIDATE_OWNER_RESOLUTION_NO_ADMISSION"
    assert artifact["russian_closure_commit"] == EXPECTED_RU164
    target = artifact["target_object"]
    assert target == {
        "admission_unit_id": "RAU-a8f2ad0b357c9e369c51",
        "requirement_id": "RSK-EDSOO1011-2-2-4-P074",
        "review_group_id": "RUS-SEM-REVIEW-047",
        "source_locator": "EDSOO1011 2.2.4 p.74",
        "module_id": "RU-PROG-02",
        "normalized_meaning": EXPECTED_MEANING,
    }

    admission_dir = ru164 / "eksamio-learning-engine/russian-program/subject-admission"
    engine = ru164 / "eksamio-learning-engine"

    source_resolution = run_json(admission_dir / "build_ru02_orthoepy_source_identity_resolution.py")
    resolutions = source_resolution["resolutions"]
    assert {row["candidate_ref"] for row in resolutions} == EXPECTED_STRESS_CANDIDATES
    assert len(resolutions) == 7
    for row in resolutions:
        assert "stress" in row["source_taxonomy_id"]
        assert "произнош" not in (row["label_ru"] + " " + row["meaning_ru"]).lower()
        assert row["admission_effect"] == "NONE"

    content_review = run_json(admission_dir / "build_ru02_orthoepy_content_adequacy_review.py")
    source_check_rows = [
        row
        for row in content_review["content_adequacy_decisions"]
        if row["content_semantic_id"] == "ru-orthoepy-norm-source-check"
    ]
    assert len(source_check_rows) == 1
    source_check = source_check_rows[0]
    assert source_check["adequacy_class"] == "NORMATIVE_SOURCE_CHECK_META_PROCEDURE_NOT_EXACT_CANDIDATE_CONTENT"
    assert source_check["exact_candidate_owner"] is None
    assert source_check["admission_effect"] == "NONE"

    inventory = json.loads((engine / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json").read_text(encoding="utf-8"))
    pronunciation_candidates = []
    for row in inventory["objects"]:
        if row.get("source_system") != "semantic_candidate" or row.get("authority_status") != "current":
            continue
        text = f"{row.get('observed_label', '')} {row.get('observed_meaning', '')}".lower()
        if "произнош" in text:
            pronunciation_candidates.append(row.get("source_id"))
    assert pronunciation_candidates == [], pronunciation_candidates

    remaining = json.loads(
        (admission_dir / "RUSSIAN-SUBJECT-REVIEWED-REMAINING-DOMAIN-MEANINGS-v0.1.json").read_text(encoding="utf-8")
    )
    assert EXPECTED_MEANING in remaining["exact_normalized_meanings"]
    assert remaining["policy"]["component_mastery_requires_component_specific_independent_evidence"] is True
    assert remaining["policy"]["keyword_or_fuzzy_inference_allowed"] is False

    existing = artifact["existing_owner_search"]
    assert existing["exact_pronunciation_owner_found"] is False
    assert existing["resolution"] == "NO_EXACT_CURRENT_PRONUNCIATION_OWNER"
    assert set(existing["stress_family_candidates"]) == EXPECTED_STRESS_CANDIDATES
    assert existing["normative_stress_owner"]["candidate_ref"] == "candidate-018"
    assert existing["normative_stress_owner"]["may_cover_pronunciation_component"] is False
    assert existing["source_check_unit"]["exact_candidate_owner"] is None

    candidate = artifact["source_backed_candidate"]
    assert candidate["proposed_semantic_id"] == "ru-orthoepy-normative-pronunciation-selection"
    assert candidate["owner_status"] == "PROPOSED_SOURCE_BACKED_NOT_CANONICAL"
    assert candidate["official_source"]["publisher"] == "FGBNU FIPI"
    assert candidate["official_source"]["codifier_position"] == "3.2.3"
    assert candidate["official_source"]["page"] == 1
    assert candidate["official_source"]["url"] == "https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-1-fonetika.pdf"
    assert candidate["official_source"]["byte_identity_status"] == "PUBLIC_OFFICIAL_SOURCE_LOCATOR_ONLY_BYTES_NOT_VENDORED"
    assert set(candidate["boundary"]["includes"]) == {
        "pronunciation of unstressed vowel sounds",
        "pronunciation of selected consonant sounds",
        "pronunciation of selected consonant combinations",
        "pronunciation of selected grammatical forms",
        "pronunciation features of loanwords",
    }
    assert "stress-position selection" in candidate["boundary"]["excludes"]

    acceptance = artifact["acceptance_boundary"]
    assert acceptance["semantic_admission_effect"] == "NONE"
    assert acceptance["object_closure_effect"] == "NONE"
    assert acceptance["exact_mastery_effect"] == "NONE"
    assert acceptance["false_exact_mastery"] == 0
    assert acceptance["component_specific_independent_learner_evidence_required"] is True
    assert acceptance["candidate_owner_resolution_alone_can_close_object"] is False

    next_work = artifact["next_exact_work"]
    assert next_work["pronunciation_owner_search_complete"] is True
    assert next_work["pronunciation_candidate_owner_resolution_complete"] is True
    assert next_work["pronunciation_component_specific_independent_evidence_status"] == "MISSING_BLOCKER"
    assert next_work["object_acceptance_status"] == "BLOCKED"
    assert next_work["mastery_status"] == "INELIGIBLE"

    print("RU02_NORMATIVE_PRONUNCIATION_CANDIDATE_RESOLUTION=PASS")
    print("EXACT_CURRENT_PRONUNCIATION_OWNER=NONE")
    print("PROPOSED_SOURCE_BACKED_OWNER=ru-orthoepy-normative-pronunciation-selection")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print("COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE=MISSING_BLOCKER")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
