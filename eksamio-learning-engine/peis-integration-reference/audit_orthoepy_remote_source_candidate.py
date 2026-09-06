#!/usr/bin/env python3
"""Audit the exact remote RU02 stress-bank candidate without promoting it to live mastery.

This is intentionally a source-candidate audit only.  It proves what the exact
remote #164 bytes contain and preserves the accepted semantic boundary:
normative stress selection is not normative pronunciation, and no live thematic
trainer item is admitted until its live item identity is independently sealed.
"""
from __future__ import annotations

import hashlib
import json
import subprocess

SOURCE_COMMIT = "7edddb9f9764b5e8cdf7e2653c425e5f90c4ffe9"
BANK_PATH = "eksamio-learning-engine/russkiy-knigi/ege-russkiy-trenazher/ORTHOEPIC-TRAINER-BANK.json"
BANK_BLOB = "3595d4e36cc2d78596ff05451ce42faadb3b1aed"
ACCEPTANCE_PATH = "eksamio-learning-engine/russian-program/subject-admission/RU02-NORMATIVE-STRESS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
ACCEPTANCE_BLOB = "bf18638c8222c3be605f1f06046545be2f8f62dc"


def git_show(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{path}"])


def git_blob_sha(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    bank_raw = git_show(BANK_PATH)
    acceptance_raw = git_show(ACCEPTANCE_PATH)
    require(git_blob_sha(bank_raw) == BANK_BLOB, "exact #164 orthoepic bank blob drift")
    require(git_blob_sha(acceptance_raw) == ACCEPTANCE_BLOB, "exact #164 RU02 acceptance blob drift")

    bank = json.loads(bank_raw.decode("utf-8"))
    acceptance = json.loads(acceptance_raw.decode("utf-8"))

    require(bank["schemaVersion"] == 1, "orthoepic bank schema drift")
    require(bank["source"] == "Орфоэпический список 2026", "orthoepic bank source label drift")
    entries = bank["entries"]
    ids = [str(row["id"]) for row in entries]
    require(len(entries) == 96, "exact remote candidate bank entry denominator must remain 96")
    require(len(ids) == len(set(ids)), "exact remote candidate bank item IDs must be unique")
    require(bank["cardCount"] == 36, "declared cardCount changed; re-audit before reconciliation")
    require(bank["cardCount"] != len(entries), "known 36-vs-96 metadata mismatch unexpectedly disappeared")
    require(all(row.get("correct") and row.get("wrong") for row in entries), "every stress-bank item needs exact correct/wrong forms")

    require(acceptance["status"] == "CENTRAL_BRAIN_ACCEPTED_RU02_NORMATIVE_STRESS_BOUNDED_SUBJECT_SEMANTIC", "RU02 acceptance status drift")
    require(len(acceptance["decisions"]) == 1, "RU02 bounded acceptance must remain one decision")
    decision = acceptance["decisions"][0]
    require(decision["candidate_ref"] == "candidate-018", "unexpected RU02 candidate")
    require(decision["source_taxonomy_id"] == "normative_stress_selection", "candidate-018 taxonomy drift")
    require(decision["accepted_semantic_id"] == "ru-orthoepy-normative-stress-selection", "candidate-018 semantic identity drift")
    require("without extending to non-stress orthoepic pronunciation rules" in decision["boundary_guard"], "normative pronunciation must remain outside candidate-018")
    require(decision["object_binding_status"] == "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT", "candidate-018 must not close an object by itself")
    require(acceptance["summary"]["false_exact_mastery_admissions"] == 0, "false exact mastery must remain zero")

    print("ORTHOEPY_REMOTE_SOURCE_CANDIDATE_AUDIT=PASS")
    print(f"source_commit={SOURCE_COMMIT}")
    print(f"bank_blob={BANK_BLOB}")
    print(f"declared_cardCount={bank['cardCount']}")
    print(f"actual_unique_entries={len(entries)}")
    print("live_item_identity_binding=BLOCKED_NOT_PROVEN")
    print("normative_pronunciation_owner=NOT_SUPPLIED_BY_CANDIDATE_018")
    print("false_exact_mastery=0")


if __name__ == "__main__":
    main()
