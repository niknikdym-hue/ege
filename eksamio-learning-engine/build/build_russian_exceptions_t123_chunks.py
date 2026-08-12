#!/usr/bin/env python3
"""Build deterministic data-only T123 chunks for the standalone Russian Exceptions Trainer.

Input is the already validated learner-safe Exceptions Runtime. The builder groups each
exception together with all of its practice cards, emits valid JSON envelopes wrapped in
application/json <script> tags, verifies a conservative raw-byte ceiling, and writes a
manifest with SHA-256 digests. No production/Tilda mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

DEFAULT_MAX_BLOCK_BYTES = 35_000
PLACEHOLDER_CHUNK_COUNT = 999


class BuildError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BuildError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(f"Invalid JSON in {path}: {exc}") from exc


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def envelope(runtime: dict[str, Any], exceptions: dict[str, Any], practice_items: dict[str, Any], index: int, count: int) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "product_id": runtime["product_id"],
        "content_version": runtime["content_version"],
        "chunk_index": index,
        "chunk_count": count,
        "topics": runtime["topics"] if index == 1 else [],
        "exceptions": exceptions,
        "practice_items": practice_items,
    }


def wrapper_text(payload: dict[str, Any]) -> str:
    version = payload["content_version"]
    index = payload["chunk_index"]
    count = payload["chunk_count"]
    body = compact_json(payload).replace("</script", "<\\/script")
    return (
        f'<script type="application/json" class="rex-runtime-chunk" '
        f'data-version="{version}" data-index="{index}" data-count="{count}">'
        f'{body}</script>\n'
    )


def bundle_for(runtime: dict[str, Any], exception_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    exc = runtime["exceptions"][exception_id]
    practice_ids = exc.get("practice_item_ids")
    if not isinstance(practice_ids, list) or not practice_ids:
        raise BuildError(f"{exception_id}: no practice_item_ids")
    practice: dict[str, Any] = {}
    for pid in practice_ids:
        if pid not in runtime["practice_items"]:
            raise BuildError(f"{exception_id}: missing practice item {pid}")
        practice[pid] = runtime["practice_items"][pid]
    return {exception_id: exc}, practice


def build_chunks(runtime: dict[str, Any], max_block_bytes: int) -> list[dict[str, Any]]:
    required = ("product_id", "content_version", "topics", "exceptions", "practice_items")
    for key in required:
        if key not in runtime:
            raise BuildError(f"Runtime missing {key}")
    if runtime["product_id"] != "russian_exceptions":
        raise BuildError(f"Unexpected product_id: {runtime['product_id']!r}")
    if not isinstance(runtime["exceptions"], dict) or not isinstance(runtime["practice_items"], dict):
        raise BuildError("Runtime exceptions/practice_items must be objects")

    ordered_ids = sorted(
        runtime["exceptions"],
        key=lambda eid: (
            runtime["exceptions"][eid].get("topic_id") or "",
            runtime["exceptions"][eid].get("launch_priority") or "P9",
            eid,
        ),
    )

    groups: list[tuple[dict[str, Any], dict[str, Any]]] = []
    current_exc: dict[str, Any] = {}
    current_pr: dict[str, Any] = {}

    def size_if(exc: dict[str, Any], pr: dict[str, Any], index: int) -> int:
        probe = envelope(runtime, exc, pr, index, PLACEHOLDER_CHUNK_COUNT)
        return len(wrapper_text(probe).encode("utf-8"))

    for eid in ordered_ids:
        bexc, bpr = bundle_for(runtime, eid)
        candidate_exc = {**current_exc, **bexc}
        candidate_pr = {**current_pr, **bpr}
        index = len(groups) + 1
        if current_exc and size_if(candidate_exc, candidate_pr, index) > max_block_bytes:
            groups.append((current_exc, current_pr))
            current_exc, current_pr = bexc, bpr
            if size_if(current_exc, current_pr, len(groups) + 1) > max_block_bytes:
                raise BuildError(f"Single exception bundle exceeds max block bytes: {eid}")
        else:
            current_exc, current_pr = candidate_exc, candidate_pr
    if current_exc:
        groups.append((current_exc, current_pr))

    count = len(groups)
    chunks: list[dict[str, Any]] = []
    for idx, (exc, pr) in enumerate(groups, start=1):
        payload = envelope(runtime, exc, pr, idx, count)
        raw = wrapper_text(payload).encode("utf-8")
        if len(raw) > max_block_bytes:
            raise BuildError(f"Final chunk {idx} exceeds max block bytes: {len(raw)} > {max_block_bytes}")
        chunks.append(payload)
    return chunks


def reconstruct(chunks: list[dict[str, Any]], runtime: dict[str, Any]) -> dict[str, Any]:
    if not chunks:
        raise BuildError("No chunks")
    version = runtime["content_version"]
    if any(c.get("content_version") != version for c in chunks):
        raise BuildError("Mixed content versions")
    expected = len(chunks)
    indices = [c.get("chunk_index") for c in chunks]
    if indices != list(range(1, expected + 1)):
        raise BuildError(f"Non-contiguous chunk indices: {indices}")
    if any(c.get("chunk_count") != expected for c in chunks):
        raise BuildError("chunk_count mismatch")

    exceptions: dict[str, Any] = {}
    practice: dict[str, Any] = {}
    topics: list[Any] = []
    for c in chunks:
        if c.get("topics"):
            if topics:
                raise BuildError("Topics repeated in more than one chunk")
            topics = c["topics"]
        for key, value in c.get("exceptions", {}).items():
            if key in exceptions:
                raise BuildError(f"Duplicate exception across chunks: {key}")
            exceptions[key] = value
        for key, value in c.get("practice_items", {}).items():
            if key in practice:
                raise BuildError(f"Duplicate practice item across chunks: {key}")
            practice[key] = value

    if exceptions != runtime["exceptions"]:
        raise BuildError("Reconstructed exceptions differ from runtime")
    if practice != runtime["practice_items"]:
        raise BuildError("Reconstructed practice_items differ from runtime")
    if topics != runtime["topics"]:
        raise BuildError("Reconstructed topics differ from runtime")
    return {"topics": topics, "exceptions": exceptions, "practice_items": practice}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, default=root / "build" / "RUSSIAN-EXCEPTIONS-RUNTIME.json")
    parser.add_argument("--output-dir", type=Path, default=root / "build" / "t123-exceptions-runtime")
    parser.add_argument("--manifest", type=Path, default=root / "build" / "RUSSIAN-EXCEPTIONS-T123-CHUNKS-MANIFEST.json")
    parser.add_argument("--max-block-bytes", type=int, default=DEFAULT_MAX_BLOCK_BYTES)
    args = parser.parse_args()

    try:
        if args.max_block_bytes < 5_000:
            raise BuildError("max-block-bytes is unrealistically small")
        runtime = load_json(args.runtime)
        chunks = build_chunks(runtime, args.max_block_bytes)
        reconstruct(chunks, runtime)
        if args.output_dir.exists():
            shutil.rmtree(args.output_dir)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        rows = []
        for chunk in chunks:
            idx = int(chunk["chunk_index"])
            name = f"trenazhery-russkiy-isklyucheniya-RUNTIME-{idx:02d}.txt"
            path = args.output_dir / name
            raw = wrapper_text(chunk).encode("utf-8")
            path.write_bytes(raw)
            rows.append({
                "chunk_index": idx,
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "bytes": len(raw),
                "sha256": sha256_hex(raw),
                "exceptions": len(chunk["exceptions"]),
                "practice_items": len(chunk["practice_items"]),
            })

        runtime_compact = compact_json({
            "topics": runtime["topics"],
            "exceptions": runtime["exceptions"],
            "practice_items": runtime["practice_items"],
        }).encode("utf-8")
        manifest = {
            "schema_version": "1.0.0",
            "product_id": runtime["product_id"],
            "content_version": runtime["content_version"],
            "chunk_count": len(chunks),
            "max_block_bytes": args.max_block_bytes,
            "runtime_content_sha256": sha256_hex(runtime_compact),
            "exceptions_total": len(runtime["exceptions"]),
            "practice_items_total": len(runtime["practice_items"]),
            "chunks": rows,
            "production_integration": "not_connected",
        }
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"PASS: chunks={len(chunks)}, max_bytes={max(row['bytes'] for row in rows)}, version={runtime['content_version']}, practice={len(runtime['practice_items'])}")
        print(f"Manifest: {args.manifest}")
        return 0
    except BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
