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
    "RU-PROG-15-OGE-COMPRESSED-EXPOSITION-WAVE-001-v0.1.json",
]
EXPECTED_MODULES = {"RU-PROG-01", "RU-PROG-04", "RU-PROG-05", "RU-PROG-15"}
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


def validate_file(path: Path) -> tuple[dict, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "SUBJECT_ACCEPTANCE_REQUIRED", path.name
    assert data["module_id"] in EXPECTED_MODULES, path.name
    assert data["subject"] == "russian", path.name
    assert data["copyright_guard"]["source_passages_copied"] == 0 if "source_passages_copied" in data["copyright_guard"] else data["copyright_guard"]["official_source_passages_copied"] == 0
    assert any(src.get("kind") == "official_program" for src in data["source_provenance"]), path.name
    assert data["units"], path.name

    all_ids: list[str] = []
    proposed_ids: set[str] = set()
    for unit in data["units"]:
        missing = REQUIRED_UNIT_FIELDS - set(unit)
        assert not missing, f"{path.name}:{unit.get('proposed_semantic_id')}: missing {sorted(missing)}"
        semantic_id = unit["proposed_semantic_id"]
        assert semantic_id.startswith("ru-"), semantic_id
        assert semantic_id not in proposed_ids, semantic_id
        proposed_ids.add(semantic_id)
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

    if len(all_ids) != len(set(all_ids)):
        duplicates = sorted({item_id for item_id in all_ids if all_ids.count(item_id) > 1})
        raise AssertionError(f"{path.name}: duplicate learner item ids: {duplicates}")

    digest = hashlib.sha256(canonical_bytes(data)).hexdigest()
    return data, digest


def main() -> None:
    modules: set[str] = set()
    unit_total = 0
    digests: list[str] = []
    for filename in FILES:
        path = ROOT / filename
        if not path.exists():
            raise AssertionError(f"missing content file: {filename}")
        data, digest = validate_file(path)
        modules.add(data["module_id"])
        unit_total += len(data["units"])
        digests.append(f"{filename}:{digest}")

    assert modules == EXPECTED_MODULES, (modules, EXPECTED_MODULES)

    oge = json.loads((ROOT / "RU-PROG-15-OGE-COMPRESSED-EXPOSITION-WAVE-001-v0.1.json").read_text(encoding="utf-8"))
    scoring = oge["official_exam_scoring_overlay_2026"]
    assert scoring["IK1_content"]["max_points"] == 2
    assert scoring["IK2_compression"]["max_points"] == 2
    assert scoring["IK3_logic"]["max_points"] == 2
    assert scoring["max_points_ik1_ik3"] == 6

    wave_hash = hashlib.sha256("\n".join(sorted(digests)).encode("utf-8")).hexdigest()
    print("RU_FULL_CONTENT_WAVE_001_VALIDATION=PASS")
    print(f"modules={len(modules)}")
    print(f"learner_units={unit_total}")
    print(f"wave_sha256={wave_hash}")


if __name__ == "__main__":
    main()
