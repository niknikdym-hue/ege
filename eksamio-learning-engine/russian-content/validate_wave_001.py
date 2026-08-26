#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = Path(__file__).resolve().parent / "wave-001"
INVENTORY = ROOT / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

REQUIRED_TOP = {
    "schema_version",
    "status",
    "subject",
    "semantic_id",
    "title_ru",
    "grade_scope",
    "route_relevance",
    "source_provenance",
    "canonical_explanation",
    "worked_examples",
    "misconceptions",
    "guided_practice",
    "independent_practice",
    "mixed_transfer_practice",
    "retention_items",
    "independent_verification",
    "peis_evidence",
    "copyright_policy",
}
ID_LIST_FIELDS = (
    "misconceptions",
    "guided_practice",
    "independent_practice",
    "mixed_transfer_practice",
    "retention_items",
    "independent_verification",
)


def fail(message: str) -> None:
    raise SystemExit(f"RUSSIAN_CONTENT_WAVE_001_VALIDATION=FAIL: {message}")


def main() -> None:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    canonical_ids = {
        obj.get("source_id")
        for obj in inventory.get("objects", [])
        if obj.get("source_system") == "school_canonical"
        and obj.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
    }

    files = sorted(CONTENT_DIR.glob("*.json"))
    if not files:
        fail("no content bundles")

    semantic_ids: set[str] = set()
    normalized: list[dict] = []
    total_learning_items = 0

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        missing = sorted(REQUIRED_TOP - data.keys())
        if missing:
            fail(f"{path.name}: missing fields {missing}")
        sid = data["semantic_id"]
        if sid in semantic_ids:
            fail(f"duplicate semantic_id {sid}")
        semantic_ids.add(sid)
        if path.stem != sid:
            fail(f"{path.name}: filename != semantic_id")
        if sid not in canonical_ids:
            fail(f"{sid}: not a canonical school identity")
        if sid.startswith("candidate-"):
            fail(f"{sid}: candidate ref cannot be canonical")
        if data.get("subject") != "russian":
            fail(f"{sid}: wrong subject")
        if data.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
            fail(f"{sid}: unexpected status")

        provenance = data["source_provenance"]
        if not provenance or not any(p.get("kind") == "official_program" for p in provenance):
            fail(f"{sid}: no official-program provenance")
        if any(p.get("access") == "LICENSE_REQUIRED" for p in provenance):
            fail(f"{sid}: licensed source admitted into original-content wave")

        explanation = data["canonical_explanation"]
        if not explanation.get("short") or not explanation.get("decision_algorithm"):
            fail(f"{sid}: incomplete explanation")

        all_ids: list[str] = []
        for field in ID_LIST_FIELDS:
            rows = data[field]
            if not rows:
                fail(f"{sid}: empty {field}")
            total_learning_items += len(rows)
            for row in rows:
                rid = row.get("id")
                if not rid:
                    fail(f"{sid}: item without id in {field}")
                all_ids.append(rid)
                if field == "independent_verification" and row.get("type") == "single_choice":
                    options = row.get("options") or []
                    idx = row.get("correct_option_index")
                    if not isinstance(idx, int) or idx < 0 or idx >= len(options):
                        fail(f"{sid}/{rid}: invalid correct_option_index")
        if len(all_ids) != len(set(all_ids)):
            fail(f"{sid}: duplicate learning item ids")

        verification_ids = {row["id"] for row in data["independent_verification"]}
        peis = data["peis_evidence"]
        if peis.get("skill_ref") != sid:
            fail(f"{sid}: PEIS skill_ref mismatch")
        if set(peis.get("verification_item_ids", [])) - verification_ids:
            fail(f"{sid}: PEIS points to missing verification item")

        copyright_policy = data["copyright_policy"]
        if copyright_policy.get("content_origin") != "ORIGINAL_EKSAMIO":
            fail(f"{sid}: content is not marked original")
        if copyright_policy.get("commercial_textbook_bytes_used") is not False:
            fail(f"{sid}: commercial textbook bytes flag must be false")
        if copyright_policy.get("commercial_textbook_exercises_copied") is not False:
            fail(f"{sid}: copied textbook exercise flag must be false")

        normalized.append({
            "semantic_id": sid,
            "sources": sorted(
                (p.get("kind"), p.get("ref") or p.get("url") or p.get("title"))
                for p in provenance
            ),
            "item_ids": sorted(all_ids),
            "verification_ids": sorted(verification_ids),
        })

    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    print("RUSSIAN_CONTENT_WAVE_001_VALIDATION=PASS")
    print(f"bundles={len(files)}")
    print(f"canonical_semantic_ids={len(semantic_ids)}")
    print(f"learning_items={total_learning_items}")
    print(f"normalized_sha256={digest}")


if __name__ == "__main__":
    main()
