#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUTHORITY_SHA = "7edddb9f9764b5e8cdf7e2653c425e5f90c4ffe9"


class TextCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_json(path: str) -> dict:
    raw = subprocess.check_output(
        ["git", "show", f"{AUTHORITY_SHA}:{path}"], text=True, encoding="utf-8"
    )
    return json.loads(raw)


def live_text(url: str) -> tuple[str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "Eksamio-Issue-185-ReadOnly-Acceptance/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        assert response.status == 200, f"live page returned {response.status}: {url}"
    decoded = body.decode("utf-8")
    parser = TextCollector()
    parser.feed(decoded)
    visible = " ".join(html.unescape(" ".join(parser.parts)).split()).casefold()
    return visible, hashlib.sha256(body).hexdigest()


def require_marker(text: str, marker: str, label: str) -> None:
    normalized = " ".join(marker.split()).casefold()
    assert normalized in text, f"missing exact live action marker for {label}: {marker}"


def acceptance_decision(doc: dict, semantic_id: str) -> dict:
    matches = [d for d in doc["decisions"] if d["accepted_semantic_id"] == semantic_id]
    assert len(matches) == 1, f"expected one accepted decision for {semantic_id}"
    return matches[0]


def main() -> None:
    binding = load(ROOT / "THEMATIC-TRAINER-ACTION-SCOPED-SEMANTIC-BINDINGS-v0.1.json")
    paronym_source = load(ROOT / "LIVE-FIPI-PARONYM-CORRESPONDENCE-v0.1.json")
    phraseology_identity = load(ROOT / "LIVE-PHRASEOLOGY-EXACT-INVENTORY-v0.1.json")
    thematic_source = load(ROOT / "LIVE-FIPI-THEMATIC-CORRESPONDENCE-v0.1.json")
    rec = load(ROOT / "THEMATIC-TRAINER-CANONICAL-RECONCILIATION-v0.1.json")

    assert binding["issue"] == 185
    assert binding["status"] == "BOUNDED_ACTION_SCOPED_BINDING_ACCEPTED_NO_MASTERY_ADMISSION"
    assert binding["authority"]["russian_subject_head_sha"] == AUTHORITY_SHA

    paronym_auth = git_json(binding["authority"]["paronym_acceptance_path"])
    phraseology_auth = git_json(binding["authority"]["phraseology_acceptance_path"])
    assert paronym_auth["status"] == "CENTRAL_BRAIN_ACCEPTED_RU03_PARONYM_BOUNDED_SUBJECT_SEMANTIC"
    assert phraseology_auth["status"] == "CENTRAL_BRAIN_ACCEPTED_RU03_PHRASEOLOGISM_IDENTIFICATION_BOUNDED_SUBJECT_SEMANTIC"
    assert paronym_auth["policy"]["component_specific_independent_evidence_required"] is True
    assert phraseology_auth["policy"]["component_specific_independent_evidence_required"] is True
    assert paronym_auth["policy"]["content_presence_alone_is_semantic_admission"] is False
    assert phraseology_auth["policy"]["content_presence_alone_is_semantic_admission"] is False

    pb = binding["bindings"]["paronyms"]
    pd = acceptance_decision(paronym_auth, pb["accepted_action_component"]["accepted_semantic_id"])
    assert pd["accepted_semantic_id"] == "ru-lexis-paronym-collocation-choice"
    assert pd["object_binding_status"] == "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT"
    pi = paronym_source["inventory"]
    pp = paronym_source["textual_provenance_correspondence"]
    assert pi["full_live_group_count"] == pb["content_identity"]["group_count"] == 144
    assert pi["live_entry_count"] == pb["content_identity"]["entry_count"] == 334
    assert pi["ordered_group_id_sha256"] == pb["content_identity"]["ordered_group_id_sha256"]
    assert pi["ordered_entry_id_sha256"] == pb["content_identity"]["ordered_entry_id_sha256"]
    assert pp["exact_match_count"] == 144 and pp["mismatch_count"] == 0
    assert rec["assets"]["paronyms"]["semantic_binding_status"] == "BLOCKED_SEMANTIC_ACCEPTANCE_SEPARATE"
    assert pb["accepted_action_component"]["binding_status"] == "ACCEPTED_ACTION_SCOPED_COMPONENT_ONLY"
    assert pb["asset_wide_semantic_status"] == "BLOCKED_MULTI_ACTION_ASSET_NOT_ONE_SKILL"

    fb = binding["bindings"]["phraseology"]
    fd = acceptance_decision(phraseology_auth, fb["accepted_action_component"]["accepted_semantic_id"])
    assert fd["accepted_semantic_id"] == "ru-lexis-phraseologism-fragment-identification"
    assert fd["object_binding_status"] == "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT"
    assert phraseology_identity["live_row_count"] == fb["content_identity"]["row_count"] == 285
    assert phraseology_identity["unique_explicit_id_count"] == fb["content_identity"]["unique_id_count"] == 285
    assert phraseology_identity["ordered_id_sha256"] == fb["content_identity"]["ordered_id_sha256"]
    tf = thematic_source["phraseology"]
    assert tf["live_count"] == tf["fipi_count"] == tf["exact_primary_match_count"] == 285
    assert tf["exact_primary_mismatch_count"] == 0
    assert rec["assets"]["phraseology"]["semantic_binding_status"] == "BLOCKED_SEMANTIC_ACCEPTANCE_SEPARATE"
    assert fb["accepted_action_component"]["binding_status"] == "ACCEPTED_ACTION_SCOPED_COMPONENT_ONLY"
    assert fb["asset_wide_semantic_status"] == "BLOCKED_MULTI_ACTION_ASSET_NOT_ONE_SKILL"

    paronym_text, paronym_hash = live_text(pb["live_url"])
    phraseology_text, phraseology_hash = live_text(fb["live_url"])
    require_marker(paronym_text, pb["accepted_action_component"]["live_action_marker_ru"], "paronym accepted component")
    require_marker(paronym_text, pb["accepted_action_component"]["supporting_live_boundary_marker_ru"], "paronym collocation boundary")
    for marker in pb["explicitly_unbound_live_actions"]:
        require_marker(paronym_text, marker, "paronym excluded component")
    require_marker(phraseology_text, fb["accepted_action_component"]["live_action_marker_ru"], "phraseology accepted component")
    for marker in fb["explicitly_unbound_live_actions"]:
        require_marker(phraseology_text, marker, "phraseology excluded component")

    # Current page hashes are informational drift signals; semantic acceptance is anchored by exact action copy + pinned content identity/provenance.
    assert re.fullmatch(r"[0-9a-f]{64}", paronym_hash)
    assert re.fullmatch(r"[0-9a-f]{64}", phraseology_hash)

    boundary = binding["admission_boundary"]
    assert boundary["accepted_action_scoped_authority_reuses"] == 2
    for key in ("asset_wide_semantic_admissions", "production_event_semantic_admissions", "object_closures", "mastery_admissions", "false_exact_mastery"):
        assert boundary[key] == 0, f"{key} must remain fail-closed"
    assert boundary["registered_user_identity_ref_required_for_future_canonical_evidence"] is True
    assert boundary["browser_local_progress_can_emit_mastery"] is False
    assert boundary["generic_trainer_completion_can_emit_mastery"] is False
    assert "do not infer RU08 ownership" in binding["still_blocked"]["dictionary_words"]

    print("THEMATIC_ACTION_SCOPED_SEMANTIC_BINDINGS=PASS")
    print("paronym_action_binding=ru-lexis-paronym-collocation-choice")
    print("phraseology_action_binding=ru-lexis-phraseologism-fragment-identification")
    print("asset_wide_semantic_admissions=0")
    print("production_event_semantic_admissions=0")
    print("mastery_admissions=0")
    print("false_exact_mastery=0")
    print(f"live_paronym_html_sha256={paronym_hash}")
    print(f"live_phraseology_html_sha256={phraseology_hash}")


if __name__ == "__main__":
    main()
