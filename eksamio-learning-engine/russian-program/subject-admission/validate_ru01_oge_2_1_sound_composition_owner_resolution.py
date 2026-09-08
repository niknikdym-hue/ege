#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
SOURCE = PROGRAM / "source-knowledge"

CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v16.py"
BINDING_REVIEW = HERE / "build_ru01_phonetics_exact_object_binding_review.py"
AUTHORITY = HERE / "RU01-OGE-2-1-SOUND-COMPOSITION-OWNER-RESOLUTION-v0.1.json"
BASE_SEMANTICS = HERE / "RU01-PHONETICS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
TRANSCRIPTION = HERE / "RU01-PHONETIC-TRANSCRIPTION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
SOUND_CHANGES = HERE / "RU01-SOUND-CHANGES-IN-SPEECH-FLOW-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
SOURCE_INDEX = SOURCE / "RUSSIAN-OFFICIAL-REQUIREMENTS-INDEX-v1.0.json"
SOURCE_SHARD = SOURCE / "requirements" / "requirements-11.json"
SOURCE_MANIFEST = SOURCE / "RUSSIAN-OFFICIAL-SOURCE-MANIFEST-v1.0.json"

INPUT_HEAD = "5dad71b64577f0e51b94fc0191fb4b1c3b6fb543"
V16_SHA256 = "43ccb3968f98540d32e54ef99c1c73b864c55caea22289b9e2764d77e32fc147"
TARGET_UNIT = "RAU-b6f5dff93864358672bc"
TARGET_REQUIREMENT = "RSK-OGE_COD-2-1-P010"
GROUP = "RUS-SEM-REVIEW-001"
SOURCE_DOCUMENT_SHA256 = "2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a"
CANDIDATE = "ru-phonetics-sound-composition-determination"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    current = runpy.run_path(str(CURRENT))["build_progress"]()
    assert current["normalized_sha256"] == V16_SHA256
    assert current["status"] == "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_IN_PROGRESS"
    assert current["progress_summary"]["false_exact_mastery_admissions"] == 0

    groups = [row for row in current["semantic_review_groups"] if row.get("group_id") == GROUP]
    assert len(groups) == 1
    group = groups[0]
    assert TARGET_UNIT in group["admission_unit_ids"]
    assert TARGET_REQUIREMENT in {row["requirement_id"] for row in group["requirements"]}
    assert TARGET_REQUIREMENT not in {row["requirement_id"] for row in group["accepted_component_sets"]}

    review = runpy.run_path(str(BINDING_REVIEW))["build_review"]()
    records = [
        row for row in review["records"]
        if row.get("admission_unit_id") == TARGET_UNIT and row.get("requirement_id") == TARGET_REQUIREMENT
    ]
    assert len(records) == 1
    record = records[0]
    assert record["source_id"] == "FIPI-OGE-RU-2026-FINAL"
    assert record["document_id"] == "OGE_COD"
    assert record["page"] == 10 and record["code"] == "2.1"
    assert record["normalized_source_signature"] == "SOUND_IDENTIFICATION_FEATURES_COMPOSITION"
    assert record["review_classification"] == "COMPOSITE"
    assert record["accepted_semantic_refs"] == ["ru-phonetics-vowel-consonant-features"]
    assert record["blocker_or_reroute"] == "SOUND_COMPOSITION_FACET_UNBOUND"
    outcomes = [row for row in review["unit_outcomes"] if row.get("admission_unit_id") == TARGET_UNIT]
    assert len(outcomes) == 1 and outcomes[0]["unit_review_outcome"] == "PENDING_EXACT_DECOMPOSITION"

    index = json.loads(SOURCE_INDEX.read_text(encoding="utf-8"))
    docs = index["catalogs"]["documents"]
    oge_docs = [row for row in docs if row["document_id"] == "OGE_COD"]
    assert len(oge_docs) == 1
    assert oge_docs[0]["source_id"] == "FIPI-OGE-RU-2026-FINAL"
    assert oge_docs[0]["sha256"] == SOURCE_DOCUMENT_SHA256

    shard = json.loads(SOURCE_SHARD.read_text(encoding="utf-8"))
    columns = {name: pos for pos, name in enumerate(shard["columns"])}
    source_rows = [row for row in shard["records"] if row[columns["record_id"]] == TARGET_REQUIREMENT]
    assert len(source_rows) == 1
    source_row = source_rows[0]
    assert source_row[columns["page"]] == 10
    assert source_row[columns["code"]] == "2.1"
    assert source_row[columns["module_mask"]] == 1
    assert source_row[columns["meaning_ref"]] == 0
    assert index["catalogs"]["meanings"][0] == "Анализировать звуковую и буквенную форму языковых единиц."

    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    manifest_rows = [row for row in manifest["documents"] if row.get("document_id") == "OGE_COD"]
    assert len(manifest_rows) == 1
    manifest_row = manifest_rows[0]
    assert manifest_row["canonical_source_id"] == "FIPI-OGE-RU-2026-FINAL"
    assert manifest_row["sha256"] == SOURCE_DOCUMENT_SHA256
    assert manifest_row["final_status"] == "FINAL_FOR_2026"
    assert manifest_row["role"] == "codifier"

    base = json.loads(BASE_SEMANTICS.read_text(encoding="utf-8"))
    base_ids = {row["accepted_semantic_id"] for row in base["decisions"]}
    assert base_ids == {
        "ru-phonetics-sound-letter-relation",
        "ru-phonetics-vowel-consonant-features",
        "ru-phonetics-word-analysis-sequence",
    }
    transcription_text = json.dumps(json.loads(TRANSCRIPTION.read_text(encoding="utf-8")), ensure_ascii=False)
    sound_changes_text = json.dumps(json.loads(SOUND_CHANGES.read_text(encoding="utf-8")), ensure_ascii=False)
    assert "ru-phonetics-phonetic-transcription-elements" in transcription_text
    assert "ru-phonetics-sound-changes-in-speech-flow" in sound_changes_text

    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    asserted_sha = authority.pop("normalized_sha256")
    assert hashlib.sha256(canonical_json(authority)).hexdigest() == asserted_sha
    assert authority["russian_closure_input_head"] == INPUT_HEAD
    assert authority["current_launch_progress_v16_normalized_sha256"] == V16_SHA256
    assert authority["target_object"]["admission_unit_id"] == TARGET_UNIT
    assert authority["target_object"]["requirement_id"] == TARGET_REQUIREMENT
    assert authority["target_object"]["review_group_id"] == GROUP
    assert authority["exact_source_requirement"]["document_sha256"] == SOURCE_DOCUMENT_SHA256
    assert authority["exact_source_requirement"]["source_review_signature"] == record["normalized_source_signature"]
    assert authority["exact_source_requirement"]["source_review_classification"] == record["review_classification"]
    assert authority["exact_source_requirement"]["already_bound_component_ref"] == record["accepted_semantic_refs"][0]
    assert authority["exact_source_requirement"]["remaining_exact_blocker"] == record["blocker_or_reroute"]

    search = authority["existing_owner_search"]
    assert search["exact_current_sound_composition_owner_found"] is False
    assert search["resolution"] == "NO_EXACT_CURRENT_SOUND_COMPOSITION_OWNER"
    reviewed = {row["semantic_id"]: row["result"] for row in search["reviewed_current_phonetics_semantics"]}
    assert reviewed == {
        "ru-phonetics-sound-letter-relation": "NOT_EXACT_OWNER",
        "ru-phonetics-vowel-consonant-features": "PARTIAL_COMPONENT_ALREADY_BOUND",
        "ru-phonetics-word-analysis-sequence": "NOT_EXACT_OWNER_FOR_STANDALONE_FACET",
        "ru-phonetics-phonetic-transcription-elements": "NOT_EXACT_OWNER",
        "ru-phonetics-sound-changes-in-speech-flow": "NOT_EXACT_OWNER",
    }

    proposed = authority["proposed_owner"]
    assert proposed["semantic_id"] == CANDIDATE
    assert proposed["source_taxonomy_id"] == "sound_composition_determination"
    assert proposed["status"] == "PROPOSED_NOT_CANONICAL"

    boundary = authority["acceptance_boundary"]
    assert boundary["semantic_admission_effect"] == "NONE"
    assert boundary["object_closure_effect"] == "NONE"
    assert boundary["exact_mastery_effect"] == "NONE"
    assert boundary["candidate_owner_resolution_can_self_admit"] is False
    assert boundary["existing_partial_component_is_preserved"] is True
    assert boundary["route_or_task_name_can_admit_semantics"] is False
    assert boundary["keyword_fuzzy_or_embedding_inference_allowed"] is False
    assert boundary["component_specific_independent_learner_evidence_required"] is True
    assert boundary["false_exact_mastery"] == 0

    assert authority["next_required_gates"] == [
        "ORIGINAL_LEARNER_CONTENT",
        "INDEPENDENT_SOUND_COMPOSITION_SPECIFIC_EVIDENCE",
        "BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE",
        "EXACT_OBJECT_COMPONENT_SET_ACCEPTANCE_FOR_RAU-b6f5dff93864358672bc",
    ]

    print("RU01_OGE_2_1_SOUND_COMPOSITION_OWNER_RESOLUTION=PASS")
    print(f"input_head={INPUT_HEAD}")
    print(f"current_v16_sha256={V16_SHA256}")
    print(f"target={TARGET_UNIT}/{TARGET_REQUIREMENT}")
    print(f"candidate={CANDIDATE}")
    print(f"authority_normalized_sha256={asserted_sha}")
    print("false_exact_mastery=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
