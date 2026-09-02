#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
MANIFEST = HERE / "PR139-LEARNER-CONTENT-SALVAGE-v0.1.json"

EXPECTED_MODULES = {
    "RU-PROG-01", "RU-PROG-02", "RU-PROG-03", "RU-PROG-04", "RU-PROG-05",
    "RU-PROG-06", "RU-PROG-07", "RU-PROG-11", "RU-PROG-12", "RU-PROG-15",
}
REQUIRED_UNIT_FIELDS = {
    "proposed_semantic_id", "title_ru", "canonical_explanation",
    "decision_algorithm", "worked_examples", "misconceptions",
    "guided_practice", "independent_practice", "mixed_transfer_practice",
    "retention_items", "independent_verification", "peis_evidence",
    "tutor_grounding",
}
ITEM_FIELDS = (
    "guided_practice", "independent_practice", "mixed_transfer_practice",
    "retention_items", "independent_verification",
)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def canonical_sha(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    manifest = load_json(MANIFEST)
    if manifest.get("status") != "CENTRAL_BRAIN_PR139_CONTENT_SALVAGE_CANDIDATE":
        raise AssertionError("PR139 salvage manifest status drift")
    if manifest.get("source_pr") != 139 or manifest.get("source_head") != "f16884ec4f8992ee9ad01c2930c42349f579bc70":
        raise AssertionError("PR139 salvage source authority drift")

    policy = manifest.get("salvage_policy") or {}
    required_true = {
        "copy_only_exact_pinned_json_blobs",
        "current_branch_subject_acceptance_required",
    }
    for key in required_true:
        if policy.get(key) is not True:
            raise AssertionError(f"PR139 salvage policy weakened: {key}")
    for key in (
        "source_pr_merge_allowed", "oge_local_import_allowed",
        "mp3_or_transcript_asset_salvage_allowed", "semantic_self_admission_allowed",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"PR139 salvage hard stop weakened: {key}")
    if policy.get("rights_blocked_task1_asset_bytes_copied") != 0:
        raise AssertionError("PR139 Task1 rights-blocked bytes copied")

    rows = manifest.get("files")
    if not isinstance(rows, list) or len(rows) != 10:
        raise AssertionError("PR139 salvage must pin exactly ten files")
    modules = {str(row.get("module_id")) for row in rows if isinstance(row, dict)}
    if modules != EXPECTED_MODULES:
        raise AssertionError(f"PR139 salvage module set drift: {sorted(modules)}")
    paths = [str(row.get("path", "")) for row in rows]
    if len(paths) != len(set(paths)):
        raise AssertionError("PR139 salvage file path duplication")
    if any(not path.startswith("russian-program/production-learning-content/RU-PROG-") or not path.endswith(".json") for path in paths):
        raise AssertionError("PR139 salvage contains a non-content JSON path")
    if any("oge-local-import" in path or path.endswith((".mp3", ".txt")) for path in paths):
        raise AssertionError("PR139 salvage contains rights/local-import asset path")

    semantic_ids: list[str] = []
    learner_item_ids: list[str] = []
    file_digests: list[str] = []
    observed_modules: set[str] = set()
    observed_blob_map: dict[str, str] = {}

    for row in rows:
        path = ENGINE / str(row["path"])
        raw = path.read_bytes()
        actual_blob = git_blob_sha(raw)
        expected_blob = str(row["source_blob_sha"])
        if actual_blob != expected_blob:
            raise AssertionError(f"PR139 pinned blob mismatch: {path.name}: {actual_blob} != {expected_blob}")
        observed_blob_map[str(row["path"])] = actual_blob
        data = json.loads(raw.decode("utf-8"))
        file_digests.append(f"{path.name}:{canonical_sha(data)}")

        if data.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
            raise AssertionError(f"salvaged content self-admitted: {path.name}")
        if data.get("subject") != "russian" or data.get("module_id") != row["module_id"]:
            raise AssertionError(f"salvaged content module/subject drift: {path.name}")
        observed_modules.add(str(data["module_id"]))

        guard = data.get("copyright_guard") or {}
        copied = guard.get("source_passages_copied", guard.get("official_source_passages_copied"))
        if copied != 0:
            raise AssertionError(f"salvaged content copied source passages: {path.name}")
        if guard.get("commercial_source_bytes_in_git", 0) != 0:
            raise AssertionError(f"salvaged content contains commercial source bytes: {path.name}")
        provenance = data.get("source_provenance")
        if not isinstance(provenance, list) or not any(isinstance(src, dict) and src.get("kind") == "official_program" for src in provenance):
            raise AssertionError(f"salvaged content lacks official-program provenance: {path.name}")

        units = data.get("units")
        if not isinstance(units, list) or not units:
            raise AssertionError(f"salvaged content has no learner units: {path.name}")
        for unit in units:
            if not isinstance(unit, dict):
                raise AssertionError(f"invalid learner unit: {path.name}")
            missing = REQUIRED_UNIT_FIELDS - set(unit)
            if missing:
                raise AssertionError(f"{path.name}:{unit.get('proposed_semantic_id')}: missing {sorted(missing)}")
            sid = str(unit.get("proposed_semantic_id", ""))
            if not sid.startswith("ru-"):
                raise AssertionError(f"invalid proposed semantic id: {sid}")
            semantic_ids.append(sid)

            explanation = unit.get("canonical_explanation") or {}
            if not isinstance(explanation.get("short"), str) or not explanation["short"].strip():
                raise AssertionError(f"missing canonical explanation: {sid}")
            boundaries = explanation.get("boundaries")
            if not isinstance(boundaries, list) or not boundaries:
                raise AssertionError(f"missing learner boundaries: {sid}")
            for field in ("decision_algorithm", "worked_examples", "misconceptions"):
                if not isinstance(unit.get(field), list) or not unit[field]:
                    raise AssertionError(f"missing {field}: {sid}")
            for field in ITEM_FIELDS:
                items = unit.get(field)
                if not isinstance(items, list) or not items:
                    raise AssertionError(f"missing {field}: {sid}")
                for item in items:
                    if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
                        raise AssertionError(f"invalid learner item id: {sid}/{field}")
                    learner_item_ids.append(item["id"])

            peis = unit.get("peis_evidence") or {}
            if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
                raise AssertionError(f"salvaged semantic self-admitted in PEIS: {sid}")
            if peis.get("independent_verification_required") is not True:
                raise AssertionError(f"PEIS independent verification guard missing: {sid}")
            tutor = unit.get("tutor_grounding")
            if not isinstance(tutor, dict) or not tutor:
                raise AssertionError(f"Tutor grounding missing: {sid}")
            if not isinstance(tutor.get("allowed"), list) or not tutor["allowed"]:
                raise AssertionError(f"Tutor allowed grounding missing: {sid}")
            if not isinstance(tutor.get("forbidden"), list) or not tutor["forbidden"]:
                raise AssertionError(f"Tutor forbidden grounding missing: {sid}")

    if observed_modules != EXPECTED_MODULES:
        raise AssertionError("observed PR139 salvage modules drift")
    if len(semantic_ids) != 29 or len(set(semantic_ids)) != 29:
        raise AssertionError(f"expected 29 globally unique proposed semantics, got {len(semantic_ids)}/{len(set(semantic_ids))}")
    if len(learner_item_ids) != 290 or len(set(learner_item_ids)) != 290:
        raise AssertionError(f"expected 290 globally unique learner items, got {len(learner_item_ids)}/{len(set(learner_item_ids))}")

    morphemics = load_json(ENGINE / "russian-program/production-learning-content/RU-PROG-04-MORPHEMICS-WAVE-001-v0.1.json")
    alternation = next(unit for unit in morphemics["units"] if unit["proposed_semantic_id"] == "ru-morphemics-alternation-and-full-analysis")
    item = next(item for item in alternation["guided_practice"] if item["id"] == "p04-u3-g1")
    if "рук-/руч-" not in item["prompt"] or "ру-/руч-" in item["prompt"] or "к/ч" not in item["expected"]:
        raise AssertionError("RU04 рук-/руч- bounded repair regressed")

    oge = load_json(ENGINE / "russian-program/production-learning-content/RU-PROG-15-OGE-COMPRESSED-EXPOSITION-WAVE-001-v0.1.json")
    scoring = oge.get("official_exam_scoring_overlay_2026") or {}
    if (scoring.get("IK1_content") or {}).get("max_points") != 2:
        raise AssertionError("OGE IK1 scoring drift")
    if (scoring.get("IK2_compression") or {}).get("max_points") != 2:
        raise AssertionError("OGE IK2 scoring drift")
    if (scoring.get("IK3_logic") or {}).get("max_points") != 2 or scoring.get("max_points_ik1_ik3") != 6:
        raise AssertionError("OGE IK3/total scoring drift")

    expected = manifest.get("expected") or {}
    if expected != {
        "modules": 10,
        "learner_units": 29,
        "proposed_semantic_ids": 29,
        "learner_items": 290,
        "rights_blocked_task1_asset_bytes_copied": 0,
        "new_school_canonical_identities": 0,
    }:
        raise AssertionError("PR139 salvage expected denominator drift")

    wave_sha = hashlib.sha256("\n".join(sorted(file_digests)).encode("utf-8")).hexdigest()
    evidence = {
        "source_pr": 139,
        "source_head": manifest["source_head"],
        "modules": sorted(observed_modules),
        "learner_units": len(semantic_ids),
        "proposed_semantic_ids": len(set(semantic_ids)),
        "learner_items": len(set(learner_item_ids)),
        "blob_map": dict(sorted(observed_blob_map.items())),
        "wave_sha256": wave_sha,
        "rights_blocked_task1_asset_bytes_copied": 0,
    }
    evidence_sha = canonical_sha(evidence)
    print("PR139_LEARNER_CONTENT_SALVAGE=PASS")
    print("MODULES=10")
    print("LEARNER_UNITS=29")
    print("PROPOSED_SEMANTIC_IDS=29")
    print("LEARNER_ITEMS=290")
    print("RIGHTS_BLOCKED_TASK1_ASSET_BYTES_COPIED=0")
    print("RU04_RUK_RUCH_REPAIR=PASS")
    print("OGE_IK1_IK3_MAX=6")
    print(f"WAVE_SHA256={wave_sha}")
    print(f"EVIDENCE_SHA256={evidence_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
