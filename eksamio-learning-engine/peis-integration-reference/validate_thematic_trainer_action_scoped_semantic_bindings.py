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
    raw = subprocess.check_output(["git", "show", f"{AUTHORITY_SHA}:{path}"], text=True, encoding="utf-8")
    return json.loads(raw)


def live_text(url: str) -> tuple[str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "Eksamio-Issue-185-ReadOnly-Acceptance/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        assert response.status == 200, f"live page returned {response.status}: {url}"
    parser = TextCollector()
    parser.feed(body.decode("utf-8"))
    visible = " ".join(html.unescape(" ".join(parser.parts)).split()).casefold()
    return visible, hashlib.sha256(body).hexdigest()


def require_marker(text: str, marker: str, label: str) -> None:
    assert " ".join(marker.split()).casefold() in text, f"missing exact live action marker for {label}: {marker}"


def acceptance_decision(doc: dict, semantic_id: str) -> dict:
    matches = [d for d in doc["decisions"] if d["accepted_semantic_id"] == semantic_id]
    assert len(matches) == 1, f"expected one accepted decision for {semantic_id}"
    return matches[0]


def inventory_object(doc: dict, object_key: str) -> dict:
    matches = [obj for obj in doc["objects"] if obj["object_key"] == object_key]
    assert len(matches) == 1, f"expected one semantic inventory object {object_key}"
    return matches[0]


def main() -> None:
    binding = load(ROOT / "THEMATIC-TRAINER-ACTION-SCOPED-SEMANTIC-BINDINGS-v0.1.json")
    rec = load(ROOT / "THEMATIC-TRAINER-CANONICAL-RECONCILIATION-v0.1.json")
    stress_source = load(ROOT / "LIVE-FIPI-ORTHOEPY-STRESS-CORRESPONDENCE-v0.1.json")
    paronym_source = load(ROOT / "LIVE-FIPI-PARONYM-CORRESPONDENCE-v0.1.json")
    phraseology_identity = load(ROOT / "LIVE-PHRASEOLOGY-EXACT-INVENTORY-v0.1.json")
    thematic_source = load(ROOT / "LIVE-FIPI-THEMATIC-CORRESPONDENCE-v0.1.json")

    assert binding["issue"] == 185
    assert binding["status"] == "BOUNDED_ACTION_SCOPED_BINDING_ACCEPTED_NO_MASTERY_ADMISSION"
    assert binding["authority"]["russian_subject_head_sha"] == AUTHORITY_SHA

    semantic_inventory = git_json(binding["authority"]["semantic_inventory_path"])
    stress_auth = git_json(binding["authority"]["orthoepy_stress_acceptance_path"])
    paronym_auth = git_json(binding["authority"]["paronym_acceptance_path"])
    phraseology_auth = git_json(binding["authority"]["phraseology_acceptance_path"])

    # Orthoepy: this live asset is stress-only. Exact 291/291 source provenance routes its exact stress action to the already accepted stress semantic.
    ob = binding["bindings"]["orthoepy"]
    od = acceptance_decision(stress_auth, ob["accepted_action_component"]["accepted_semantic_id"])
    assert stress_auth["status"] == "CENTRAL_BRAIN_ACCEPTED_RU02_NORMATIVE_STRESS_BOUNDED_SUBJECT_SEMANTIC"
    assert od["accepted_semantic_id"] == "ru-orthoepy-normative-stress-selection"
    assert od["object_binding_status"] == "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT"
    assert "without extending to non-stress orthoepic pronunciation rules" in od["boundary_guard"]
    assert stress_source["live"]["row_count"] == stress_source["live"]["unique_id_count"] == ob["content_identity"]["row_count"] == ob["content_identity"]["unique_id_count"] == 291
    assert stress_source["correspondence"]["exact_live_stressed_token_match_count"] == 291
    assert stress_source["correspondence"]["exact_live_stressed_token_mismatch_count"] == 0
    assert stress_source["correspondence"]["mismatches"] == []
    assert stress_source["fipi"]["pdf_sha256"] == "6e1b6dcaf835f6b7294c9426de406dea3614bb81d9d28e25fc423c9c8036f389"
    assert rec["assets"]["orthoepy"]["provenance_status"] == "EXACT_LIVE_STRESS_PROVENANCE_ACCEPTED_291_OF_291"
    assert rec["assets"]["orthoepy"]["semantic_binding_status"] == "ACCEPTED_ACTION_SCOPED_STRESS_SEMANTIC_ONLY_NO_PRODUCTION_EVENT_ADMISSION"
    assert rec["assets"]["orthoepy"]["nonstress_pronunciation_boundary"]["status"] == "SEPARATE_RU02_SUBJECT_BLOCKER_NOT_ISSUE_185_STRESS_ASSET_BLOCKER"

    # Dictionary: exact source-backed 308 bank reuses the existing canonical spelling owner only for the missing-root-vowel action.
    db = binding["bindings"]["dictionary_words"]
    skill = inventory_object(semantic_inventory, "ege_skill_graph::unchecked_root_vowels")
    canonical = inventory_object(semantic_inventory, "school_canonical::school-root-vowel-dictionary-unverifiable")
    assert skill["audit_classification"] == "SAME_MEANING_AS_EXISTING"
    assert skill["candidate_canonical_owner"] == db["accepted_content_owner"]["canonical_owner_id"] == "school-root-vowel-dictionary-unverifiable"
    assert canonical["audit_classification"] == "CANONICAL_SCHOOL_IDENTITY"
    assert canonical["review_status"] == "reviewed"
    rd = rec["assets"]["dictionary_words"]
    assert rd["live_item_identity"]["row_count"] == rd["live_item_identity"]["unique_id_count"] == db["content_identity"]["row_count"] == 308
    assert rd["fipi_2026_textual_provenance"]["source_backed_supported_count_total"] == 308
    assert rd["fipi_2026_textual_provenance"]["unresolved_count"] == 0
    assert rd["semantic_binding_status"] == "ACCEPTED_ACTION_SCOPED_COMPONENT_ONLY_NO_PRODUCTION_EVENT_ADMISSION"

    # Paronyms and phraseology: only the live actions that exactly match accepted bounded semantics are bound.
    pb = binding["bindings"]["paronyms"]
    pd = acceptance_decision(paronym_auth, pb["accepted_action_component"]["accepted_semantic_id"])
    assert pd["accepted_semantic_id"] == "ru-lexis-paronym-collocation-choice"
    assert pd["object_binding_status"] == "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT"
    pi = paronym_source["inventory"]
    pp = paronym_source["textual_provenance_correspondence"]
    assert pi["full_live_group_count"] == 144 and pi["live_entry_count"] == 334
    assert pp["exact_match_count"] == 144 and pp["mismatch_count"] == 0
    assert rec["assets"]["paronyms"]["semantic_binding_status"] == "ACCEPTED_ACTION_SCOPED_COMPONENT_ONLY_ASSET_WIDE_MULTI_ACTION_REMAINS_UNBOUND"
    assert pb["asset_wide_semantic_status"] == "BLOCKED_MULTI_ACTION_ASSET_NOT_ONE_SKILL"

    fb = binding["bindings"]["phraseology"]
    fd = acceptance_decision(phraseology_auth, fb["accepted_action_component"]["accepted_semantic_id"])
    assert fd["accepted_semantic_id"] == "ru-lexis-phraseologism-fragment-identification"
    assert fd["object_binding_status"] == "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT"
    assert phraseology_identity["live_row_count"] == phraseology_identity["unique_explicit_id_count"] == 285
    tf = thematic_source["phraseology"]
    assert tf["live_count"] == tf["fipi_count"] == tf["exact_primary_match_count"] == 285
    assert tf["exact_primary_mismatch_count"] == 0
    assert rec["assets"]["phraseology"]["semantic_binding_status"] == "ACCEPTED_ACTION_SCOPED_COMPONENT_ONLY_ASSET_WIDE_MULTI_ACTION_REMAINS_UNBOUND"
    assert fb["asset_wide_semantic_status"] == "BLOCKED_MULTI_ACTION_ASSET_NOT_ONE_SKILL"

    # Current live copy must still expose the exact action boundaries we bound; local progress remains non-authoritative.
    hashes = []
    for key in ("orthoepy", "dictionary_words", "paronyms", "phraseology"):
        text, page_hash = live_text(binding["bindings"][key]["live_url"])
        hashes.append(page_hash)
        component = binding["bindings"][key]["accepted_action_component"]
        require_marker(text, component["live_action_marker_ru"], f"{key} accepted component")
        if key == "orthoepy":
            require_marker(text, component["live_source_scope_marker_ru"], "orthoepy FIPI scope")
            for marker in binding["bindings"][key]["aggregate_modes_not_admitted_as_exact_mastery"]:
                require_marker(text, marker, "orthoepy non-admitted aggregate/local-status mode")
        elif key == "dictionary_words":
            require_marker(text, component["live_scope_marker_ru"], "dictionary canonical scope")
            for marker in binding["bindings"][key]["event_modes_not_admitted_yet"]:
                require_marker(text, marker, "dictionary non-admitted mode")
        elif key == "paronyms":
            require_marker(text, component["supporting_live_boundary_marker_ru"], "paronym collocation boundary")
            for marker in binding["bindings"][key]["explicitly_unbound_live_actions"]:
                require_marker(text, marker, "paronym excluded component")
        else:
            for marker in binding["bindings"][key]["explicitly_unbound_live_actions"]:
                require_marker(text, marker, "phraseology excluded component")
    assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes)

    boundary = binding["admission_boundary"]
    assert boundary["accepted_action_scoped_authority_reuses"] == 4
    assert boundary["accepted_existing_canonical_content_owner_bindings"] == 1
    for key in ("asset_wide_semantic_admissions", "production_event_semantic_admissions", "object_closures", "mastery_admissions", "false_exact_mastery"):
        assert boundary[key] == 0, f"{key} must remain fail-closed"
    assert boundary["registered_user_identity_ref_required_for_future_canonical_evidence"] is True
    assert boundary["browser_local_progress_can_emit_mastery"] is False
    assert boundary["generic_trainer_completion_can_emit_mastery"] is False
    assert set(binding["still_blocked"]) == {"production_event_admission_all_assets", "broader_ru02_nonstress_pronunciation"}

    print("THEMATIC_ACTION_SCOPED_SEMANTIC_BINDINGS=PASS")
    print("orthoepy_action_binding=ru-orthoepy-normative-stress-selection")
    print("dictionary_action_binding=school-root-vowel-dictionary-unverifiable")
    print("paronym_action_binding=ru-lexis-paronym-collocation-choice")
    print("phraseology_action_binding=ru-lexis-phraseologism-fragment-identification")
    print("production_event_semantic_admissions=0 mastery_admissions=0 false_exact_mastery=0")


if __name__ == "__main__":
    main()
