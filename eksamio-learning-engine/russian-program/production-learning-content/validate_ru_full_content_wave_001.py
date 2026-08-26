#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = [
    "RU-PROG-01-PHONETICS-GRAPHICS-WAVE-001-v0.1.json",
    "RU-PROG-04-MORPHEMICS-WAVE-001-v0.1.json",
    "RU-PROG-05-WORD-FORMATION-WAVE-001-v0.1.json",
    "RU-PROG-06-MORPHOLOGY-WAVE-002-v0.1.json",
    "RU-PROG-11-TEXT-COHESION-WAVE-002-v0.1.json",
    "RU-PROG-12-STYLES-GENRES-WAVE-002-v0.1.json",
    "RU-PROG-15-OGE-COMPRESSED-EXPOSITION-WAVE-001-v0.1.json",
]
EXPECTED_MODULES = {
    "RU-PROG-01",
    "RU-PROG-04",
    "RU-PROG-05",
    "RU-PROG-06",
    "RU-PROG-11",
    "RU-PROG-12",
    "RU-PROG-15",
}
REQUIRED_UNIT_FIELDS = {
    "proposed_semantic_id",
    "title_ru",
    "canonical_explanation",
    "decision_algorithm",
    "worked_examples",
    "misconceptions",
    "guided_practice",
    "independent_practice",
    "mixed_transfer_practice",
    "retention_items",
    "independent_verification",
    "peis_evidence",
    "tutor_grounding",
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def collect_item_ids(unit: dict) -> list[str]:
    ids: list[str] = []
    for field in (
        "guided_practice",
        "independent_practice",
        "mixed_transfer_practice",
        "retention_items",
        "independent_verification",
    ):
        for item in unit[field]:
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id:
                raise AssertionError(f"{unit['proposed_semantic_id']}: {field} item without id")
            ids.append(item_id)
    return ids


def validate_file(path: Path) -> tuple[dict, str, list[str], list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "SUBJECT_ACCEPTANCE_REQUIRED", path.name
    assert data["module_id"] in EXPECTED_MODULES, path.name
    assert data["subject"] == "russian", path.name
    guard = data["copyright_guard"]
    copied = guard.get("source_passages_copied", guard.get("official_source_passages_copied"))
    assert copied == 0, path.name
    assert any(src.get("kind") == "official_program" for src in data["source_provenance"]), path.name
    assert data["units"], path.name

    all_ids: list[str] = []
    semantic_ids: list[str] = []
    for unit in data["units"]:
        missing = REQUIRED_UNIT_FIELDS - set(unit)
        assert not missing, f"{path.name}:{unit.get('proposed_semantic_id')}: missing {sorted(missing)}"
        semantic_id = unit["proposed_semantic_id"]
        assert semantic_id.startswith("ru-"), semantic_id
        semantic_ids.append(semantic_id)
        assert unit["canonical_explanation"].get("short"), semantic_id
        assert unit["decision_algorithm"], semantic_id
        assert unit["worked_examples"], semantic_id
        assert unit["misconceptions"], semantic_id
        assert unit["guided_practice"], semantic_id
        assert unit["independent_practice"], semantic_id
        assert unit["mixed_transfer_practice"], semantic_id
        assert unit["retention_items"], semantic_id
        assert unit["independent_verification"], semantic_id
        assert unit["peis_evidence"]["semantic_ref_status"] == "PROPOSED_NOT_CANONICAL", semantic_id
        assert unit["peis_evidence"]["independent_verification_required"] is True, semantic_id
        all_ids.extend(collect_item_ids(unit))

    assert len(semantic_ids) == len(set(semantic_ids)), f"{path.name}: duplicate semantic ids"
    assert len(all_ids) == len(set(all_ids)), f"{path.name}: duplicate learner item ids"
    digest = hashlib.sha256(canonical_bytes(data)).hexdigest()
    return data, digest, all_ids, semantic_ids


def assert_global_unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        duplicates = sorted({value for value in values if values.count(value) > 1})
        raise AssertionError(f"duplicate {label}: {duplicates}")


def main() -> None:
    modules: set[str] = set()
    unit_total = 0
    digests: list[str] = []
    learner_item_ids: list[str] = []
    semantic_ids: list[str] = []
    for filename in FILES:
        path = ROOT / filename
        if not path.exists():
            raise AssertionError(f"missing content file: {filename}")
        data, digest, item_ids, file_semantic_ids = validate_file(path)
        modules.add(data["module_id"])
        unit_total += len(data["units"])
        digests.append(f"{filename}:{digest}")
        learner_item_ids.extend(item_ids)
        semantic_ids.extend(file_semantic_ids)

    assert modules == EXPECTED_MODULES, (modules, EXPECTED_MODULES)
    assert_global_unique(learner_item_ids, "learner item ids across content waves")
    assert_global_unique(semantic_ids, "proposed semantic ids across content waves")

    oge = json.loads((ROOT / "RU-PROG-15-OGE-COMPRESSED-EXPOSITION-WAVE-001-v0.1.json").read_text(encoding="utf-8"))
    scoring = oge["official_exam_scoring_overlay_2026"]
    assert scoring["IK1_content"]["max_points"] == 2
    assert scoring["IK2_compression"]["max_points"] == 2
    assert scoring["IK3_logic"]["max_points"] == 2
    assert scoring["max_points_ik1_ik3"] == 6

    wave_hash = hashlib.sha256("\n".join(sorted(digests)).encode("utf-8")).hexdigest()
    print("RU_FULL_CONTENT_WAVES_001_002_VALIDATION=PASS")
    print(f"modules={len(modules)}")
    print(f"learner_units={unit_total}")
    print(f"learner_items={len(learner_item_ids)}")
    print(f"proposed_semantic_ids={len(semantic_ids)}")
    print(f"wave_sha256={wave_hash}")


if __name__ == "__main__":
    main()
