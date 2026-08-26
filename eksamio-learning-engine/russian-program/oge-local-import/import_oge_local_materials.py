#!/usr/bin/env python3
"""Deterministically import the owner-authored local Russian OGE task bank."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


TASK_MODULES = {
    1: ["RU-PROG-15"],
    2: ["RU-PROG-09"],
    3: ["RU-PROG-09"],
    4: ["RU-PROG-09"],
    5: ["RU-PROG-10"],
    6: ["RU-PROG-08"],
    7: ["RU-PROG-08"],
    8: ["RU-PROG-07"],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_json_cards(source: Path) -> list[dict]:
    text = source.read_text(encoding="utf-8")
    match = re.search(r"var\s+cards\s*=\s*", text)
    if not match:
        raise ValueError(f"cards bank not found: {source}")
    return json.JSONDecoder().raw_decode(text[match.end() :])[0]


def extract_task1_variants(source: Path) -> dict[str, dict]:
    node = r'''
const fs=require("fs"),vm=require("vm");
const s=fs.readFileSync(process.argv[1],"utf8");
const a=s.indexOf("var variants =")+4,b=s.indexOf("var LAST_KEY",a);
if(a<4||b<0) throw new Error("variants bank not found");
const c={};vm.createContext(c);vm.runInContext(s.slice(a,b),c);
process.stdout.write(JSON.stringify(c.variants));
'''
    result = subprocess.run(
        ["node", "-e", node, str(source)], check=True, capture_output=True, text=True
    )
    return json.loads(result.stdout)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    source_root = args.source.resolve()
    import_root = args.repo_root.resolve() / "russian-program" / "oge-local-import"
    items_root = import_root / "items"
    assets_root = import_root / "assets" / "task-01"
    items_root.mkdir(parents=True, exist_ok=True)
    assets_root.mkdir(parents=True, exist_ok=True)

    manifest_items: list[dict] = []
    task1_source = source_root / "oge-russkiy-zadanie-1" / "oge-russkiy-zadanie-1-T123.txt"
    for variant_id, original in extract_task1_variants(task1_source).items():
        item_id = f"oge-ru-01-{variant_id.lower()}"
        audio_name = original["audio"]
        transcript_name = audio_name.removesuffix(".mp3") + ".txt"
        asset_paths = []
        for name in (audio_name, transcript_name):
            src = task1_source.parent / name
            dst = assets_root / name
            shutil.copyfile(src, dst)
            asset_paths.append(dst.relative_to(args.repo_root.resolve()).as_posix())
        payload = {
            "schema_version": "1.0.0",
            "status": "SUBJECT_ACCEPTANCE_REQUIRED",
            "subject": "russian",
            "exam": "OGE",
            "task_number": 1,
            "variant": variant_id,
            "item_id": item_id,
            "semantic_identity": {"id": item_id, "status": "PROPOSED_NOT_CANONICAL"},
            "ru_prog_mapping": TASK_MODULES[1],
            "scoring": {"type": "self_check", "required_checks": 6},
            "answer": {"type": "reference_answer", "sample": original["sample"]},
            "content": original,
            "assets": asset_paths,
            "provenance": {
                "authorship": "OWNER_AUTHORED_LOCAL_MATERIAL",
                "source": "exam-platform-tilda/tilda-ready/pages/oge-russkiy-zadanie-1/oge-russkiy-zadanie-1-T123.txt",
                "adaptation": "mechanical extraction only; wording unchanged",
            },
        }
        dest = items_root / f"{item_id}.json"
        write_json(dest, payload)
        manifest_items.append(manifest_row(args.repo_root.resolve(), source_root, task1_source, dest, payload))

    for task_number in range(2, 9):
        source_file = source_root / f"oge-russkiy-zadanie-{task_number}" / f"oge-russkiy-zadanie-{task_number}-T123.txt"
        for index, original in enumerate(extract_json_cards(source_file), start=1):
            item_id = original["id"]
            answer = original.get("answer", original.get("correctAnswer"))
            payload = {
                "schema_version": "1.0.0",
                "status": "SUBJECT_ACCEPTANCE_REQUIRED",
                "subject": "russian",
                "exam": "OGE",
                "task_number": task_number,
                "variant": index,
                "item_id": item_id,
                "semantic_identity": {"id": item_id, "status": "PROPOSED_NOT_CANONICAL"},
                "ru_prog_mapping": TASK_MODULES[task_number],
                "scoring": {"type": "exact_match"},
                "answer": {"type": "exact", "value": answer},
                "content": original,
                "assets": [],
                "provenance": {
                    "authorship": "OWNER_AUTHORED_LOCAL_MATERIAL",
                    "source": f"exam-platform-tilda/tilda-ready/pages/{source_file.parent.name}/{source_file.name}",
                    "adaptation": "mechanical extraction only; wording unchanged",
                },
            }
            dest = items_root / f"{item_id}.json"
            write_json(dest, payload)
            manifest_items.append(manifest_row(args.repo_root.resolve(), source_root, source_file, dest, payload))

    manifest = {
        "schema_version": "1.0.0",
        "import_id": "russian-oge-owner-local-pages-2026-08-27",
        "status": "SUBJECT_ACCEPTANCE_REQUIRED",
        "source_scope": "exam-platform-tilda/tilda-ready/pages; Russian OGE only; EGE excluded",
        "inventory": {"task_numbers": list(range(1, 9)), "variants_per_task": 5, "items": 40},
        "items": sorted(manifest_items, key=lambda row: (row["task_number"], str(row["variant"]))),
    }
    write_json(import_root / "manifest.json", manifest)
    return 0


def manifest_row(repo_root: Path, source_root: Path, source_file: Path, dest: Path, payload: dict) -> dict:
    return {
        "local_source": source_file.relative_to(source_root).as_posix(),
        "repository_path": dest.relative_to(repo_root).as_posix(),
        "task_number": payload["task_number"],
        "variant": payload["variant"],
        "has_answer": True,
        "scoring_type": payload["scoring"]["type"],
        "ru_prog_mapping": payload["ru_prog_mapping"],
        "semantic_identity": payload["semantic_identity"],
        "assets": payload["assets"],
        "provenance": payload["provenance"],
        "content_hash": sha256(dest),
    }


if __name__ == "__main__":
    raise SystemExit(main())
