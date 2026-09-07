#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE_PROBE = Path("live-thematic-exact-identity-probe.json")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_zero_admissions(doc: dict, label: str) -> None:
    for key in ("semantic_admissions", "object_closures", "mastery_admissions", "false_exact_mastery"):
        assert doc[key] == 0, f"{label}: {key} must remain 0"


def page_by_key(probe: dict, key: str) -> dict:
    matches = [page for page in probe["pages"] if page["key"] == key]
    assert len(matches) == 1, f"expected exactly one live probe page for {key}"
    return matches[0]


def main() -> None:
    rec = load(ROOT / "THEMATIC-TRAINER-CANONICAL-RECONCILIATION-v0.1.json")
    thematic = load(ROOT / "LIVE-FIPI-THEMATIC-CORRESPONDENCE-v0.1.json")
    paronyms = load(ROOT / "LIVE-FIPI-PARONYM-CORRESPONDENCE-v0.1.json")
    phraseology = load(ROOT / "LIVE-PHRASEOLOGY-EXACT-INVENTORY-v0.1.json")
    pronunciation = load(ROOT / "RU02-NORMATIVE-PRONUNCIATION-SOURCE-BACKED-CANDIDATE-RESOLUTION-v0.1.json")
    probe = load(LIVE_PROBE)

    assert rec["schema"] == "eksamio.thematic-trainer-canonical-reconciliation.v0.1"
    assert rec["issue"] == 185
    assert rec["learner_identity_policy"]["registered_user_identity_ref_required_for_future_canonical_evidence"] is True
    assert rec["learner_identity_policy"]["anonymous_or_device_only_canonical_state_allowed"] is False
    assert rec["learner_identity_policy"]["anon_to_account_continuity_allowed"] is False
    require_zero_admissions(rec, "reconciliation")
    require_zero_admissions(thematic, "thematic correspondence")
    require_zero_admissions(paronyms, "paronym correspondence")
    require_zero_admissions(phraseology, "phraseology inventory")
    require_zero_admissions(probe, "live identity probe")

    assets = rec["assets"]

    # Orthoepy: exact live identity is known, but provenance and pronunciation evidence are not admitted.
    ortho = page_by_key(probe, "orthoepy")
    ob = ortho["exact_live_backing_candidate"]
    ro = assets["orthoepy"]
    assert ortho["http_status"] == 200
    assert ob["variable"] == "RAW"
    assert ob["row_count"] == ro["live_item_identity"]["row_count"] == 291
    assert ob["live_candidate_key_count"] == ob["live_candidate_key_unique"] == ro["live_item_identity"]["unique_key_count"] == 291
    assert ob["live_candidate_keys"][0] == ro["live_item_identity"]["first_key"] == "w001"
    assert ob["live_candidate_keys"][-1] == ro["live_item_identity"]["last_key"] == "w291"
    assert ob["live_candidate_keys_sha256"] == ro["live_item_identity"]["ordered_key_sha256"]
    assert ro["provenance_status"].startswith("BLOCKED_")
    assert ro["semantic_binding_status"] == "BLOCKED"
    assert ro["pronunciation_component_evidence_status"] == "MISSING_BLOCKER"
    assert pronunciation["next_exact_work"]["pronunciation_component_specific_independent_evidence_status"] == "MISSING_BLOCKER"
    assert pronunciation["next_exact_work"]["object_acceptance_status"] == "BLOCKED"
    assert pronunciation["acceptance_boundary"]["false_exact_mastery"] == 0

    # Dictionary words: exact 308 live IDs are known; exact FIPI same-row support is 307/308 only.
    dictionary = page_by_key(probe, "dictionary_words")
    db = dictionary["exact_live_backing_candidate"]
    rd = assets["dictionary_words"]
    assert dictionary["http_status"] == 200
    assert db["variable"] == "WORDS"
    assert db["row_count"] == rd["live_item_identity"]["row_count"] == 308
    assert db["live_candidate_key_count"] == db["live_candidate_key_unique"] == rd["live_item_identity"]["unique_id_count"] == 308
    assert db["live_candidate_keys_sha256"] == rd["live_item_identity"]["ordered_id_sha256"]
    td = thematic["dictionary_words"]
    assert td["live_count"] == 308
    assert td["fipi_count"] == 308
    assert td["exact_same_row_supported_count"] == rd["fipi_2026_textual_provenance"]["same_row_supported_count"] == 307
    assert td["unresolved_count"] == rd["fipi_2026_textual_provenance"]["unresolved_count"] == 1
    assert len(td["unresolved"]) == 1
    unresolved = td["unresolved"][0]
    assert unresolved["live_id"] == rd["fipi_2026_textual_provenance"]["unresolved_live_id"] == "rovesnik"
    assert unresolved["live"] == rd["fipi_2026_textual_provenance"]["unresolved_live_form"] == "ровесник"
    assert unresolved["fipi_row"] == rd["fipi_2026_textual_provenance"]["exact_fipi_row"] == "ровесники"
    assert "NO_MORPHOLOGY_INFERRED" in rd["fipi_2026_textual_provenance"]["status"]
    assert rd["semantic_binding_status"] == "BLOCKED"

    # Paronyms: full 144-group live backing and exact FIPI textual provenance are now known.
    rp = assets["paronyms"]
    pi = paronyms["inventory"]
    pp = paronyms["textual_provenance_correspondence"]
    assert pi["full_live_group_count"] == pi["fipi_group_count"] == rp["full_thematic_identity"]["group_count"] == 144
    assert pi["unique_live_group_id_count"] == rp["full_thematic_identity"]["unique_group_id_count"] == 144
    assert pi["live_entry_count"] == rp["full_thematic_identity"]["entry_count"] == 334
    assert pi["unique_live_entry_id_count"] == rp["full_thematic_identity"]["unique_entry_id_count"] == 334
    assert pi["ordered_group_id_sha256"] == rp["full_thematic_identity"]["ordered_group_id_sha256"]
    assert pi["ordered_entry_id_sha256"] == rp["full_thematic_identity"]["ordered_entry_id_sha256"]
    assert pp["exact_match_count"] == rp["fipi_2026_textual_provenance"]["same_index_exact_match_count"] == 144
    assert pp["mismatch_count"] == rp["fipi_2026_textual_provenance"]["mismatch_count"] == 0
    assert pp["ordered_live_group_normalized_sha256"] == pp["ordered_fipi_group_normalized_sha256"] == rp["fipi_2026_textual_provenance"]["ordered_normalized_sha256"]
    assert paronyms["provenance_binding_status"] == rp["fipi_2026_textual_provenance"]["status"] == "EXACT_FULL_GROUP_TEXTUAL_CORRESPONDENCE"
    assert rp["semantic_binding_status"] == "BLOCKED_SEMANTIC_ACCEPTANCE_SEPARATE"

    # Phraseology: exact 285 live IDs and exact FIPI textual provenance are known; semantic acceptance remains separate.
    rf = assets["phraseology"]
    tf = thematic["phraseology"]
    assert phraseology["live_row_count"] == phraseology["unique_explicit_id_count"] == rf["live_item_identity"]["row_count"] == rf["live_item_identity"]["unique_id_count"] == 285
    assert phraseology["ordered_id_sha256"] == rf["live_item_identity"]["ordered_id_sha256"]
    assert phraseology["first_id"] == rf["live_item_identity"]["first_id"]
    assert phraseology["last_id"] == rf["live_item_identity"]["last_id"]
    assert tf["live_count"] == tf["fipi_count"] == 285
    assert tf["exact_primary_match_count"] == rf["fipi_2026_textual_provenance"]["same_index_exact_match_count"] == 285
    assert tf["exact_primary_mismatch_count"] == rf["fipi_2026_textual_provenance"]["mismatch_count"] == 0
    assert tf["live_ordered_normalized_sha256"] == tf["source_primary_ordered_normalized_sha256"] == rf["fipi_2026_textual_provenance"]["ordered_normalized_sha256"]
    assert tf["status"] == rf["fipi_2026_textual_provenance"]["status"] == "EXACT_PRIMARY_ROW_CORRESPONDENCE"
    assert rf["semantic_binding_status"] == "BLOCKED_SEMANTIC_ACCEPTANCE_SEPARATE"

    print("Thematic trainer canonical reconciliation PASS: exact identities/provenance pinned; semantic/mastery admission remains fail-closed")


if __name__ == "__main__":
    main()
