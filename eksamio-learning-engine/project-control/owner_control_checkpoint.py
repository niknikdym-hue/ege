from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1"
RESUME_STAGES = {"executor", "acceptance"}
COMPLETED_BY_STAGE = {
    "executor": ["astra_plan"],
    "acceptance": ["astra_plan", "executor", "tests"],
}


def build_resume_manifest(request: dict[str, Any], source_run_id: str, resume_stage: str) -> dict[str, Any]:
    if resume_stage not in RESUME_STAGES:
        raise ValueError(f"unsupported resume stage: {resume_stage}")
    task = request.get("task") or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": request.get("repository"),
        "source_run_id": str(source_run_id),
        "task_id": task.get("task_id"),
        "base_ref": request.get("base_ref"),
        "base_sha": request.get("base_sha"),
        "owner": request.get("owner"),
        "resume_stage": resume_stage,
        "completed_paid_stages": COMPLETED_BY_STAGE[resume_stage],
        "no_auto_retry": True,
    }


def validate_resume_manifest(
    manifest: dict[str, Any],
    request: dict[str, Any],
    *,
    repository: str,
    source_run_id: str,
    task_id: str,
    base_ref: str,
    base_sha: str,
    owner: str,
) -> str:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("resume manifest schema mismatch")
    stage = manifest.get("resume_stage")
    if stage not in RESUME_STAGES:
        raise ValueError("resume manifest stage is not resumable")
    expected = {
        "repository": repository,
        "source_run_id": str(source_run_id),
        "task_id": task_id,
        "base_ref": base_ref,
        "base_sha": base_sha,
        "owner": owner,
        "no_auto_retry": True,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"resume manifest {key} mismatch")
    if manifest.get("completed_paid_stages") != COMPLETED_BY_STAGE[stage]:
        raise ValueError("resume manifest paid-stage history mismatch")
    if request.get("repository") != repository:
        raise ValueError("source request repository mismatch")
    if request.get("base_ref") != base_ref or request.get("base_sha") != base_sha:
        raise ValueError("source request base moved; paid resume refused")
    if request.get("owner") != owner:
        raise ValueError("source request owner mismatch")
    if (request.get("task") or {}).get("task_id") != task_id:
        raise ValueError("source request task mismatch")
    return stage


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())
