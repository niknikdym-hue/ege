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
    rovesnik = load(ROOT / "DICTIONARY-ROVESNIK-SOURCE-BACKED-RESOLUTION-v0.1.json")
    stress = load(ROOT / "LIVE-FIPI-ORTHOEPY-STRESS-CORRESPONDENCE-v0.1.json")
    probe = load(LIVE_PROBE)

    assert rec["schema"] == "eksamio.thematic-trainer-canonical-reconciliation.v0.1"
    assert rec["issue"] == 185
    policy = rec["learner_identity_policy"]
    assert policy["registered_user_identity_ref_required_for_future_canonical_evidence"] is True
    assert policy["anonymous_or_device_only_canonical_state_allowed"] is False
    assert policy["anon_to_account_continuity_allowed"] is False
    require_zero_admissions(rec, "reconciliation")
    require_zero_admissions(thematic, "thematic correspondence")
    require_zero_admissions(paronyms, "paronym correspondence")
    require_zero_admissions(phraseology, "phraseology inventory")
    require_zero_admissions(probe, "live identity probe")

    # Orthoepy: exact live 291 identity + exact official stress provenance are closed for this stress-only asset.
    ortho = page_by_key(probe, "orthoepy")
    ob = ortho["exact_live_backing_candidate"]
    ro = rec["assets"]["orthoepy"]
    assert ortho["http_status"] == 200
    assert ob["variable"] == "RAW"
    assert ob["row_count"] == ro["live_item_identity"]["row_count"] == 291
    assert ob["live_candidate_key_count"] == ob["live_candidate_key_unique"] == ro["live_item_identity"]["unique_key_count"] == 291
    assert ob["live_candidate_keys"][0] == ro["live_item_identity"]["first_key"] == "w001"
    assert ob["live_candidate_keys"][-1] == ro["live_item_identity"]["last_key"] == "w291"
    assert ob["live_candidate_keys_sha256"] == ro["live_item_identity"]["ordered_key_sha256"]
    sp = ro["fipi_2026_stress_textual_provenance"]
    assert stress["live"]["row_count"] == stress["live"]["unique_id_count"] == 291
    assert stress["correspondence"]["exact_live_stressed_token_match_count"] == sp["exact_live_stressed_token_match_count"] == 291
    assert stress["correspondence"]["exact_live_stressed_token_mismatch_count"] == sp["exact_live_stressed_token_mismatch_count"] == 0
    assert stress["correspondence"]["mismatches"] == []
    assert stress["live"]["html_sha256"] == sp["live_html_sha256"]
    assert stress["live"]["raw_literal_sha256"] == sp["live_raw_literal_sha256"]
    assert stress["live"]["ordered_stressed_sha256"] == sp["live_ordered_stressed_sha256"]
    assert stress["fipi"]["pdf_sha256"] == sp["fipi_pdf_sha256"] == "6e1b6dcaf835f6b7294c9426de406dea3614bb81d9d28e25fc423c9c8036f389"
    assert ro["provenance_status"] == "EXACT_LIVE_STRESS_PROVENANCE_ACCEPTED_291_OF_291"
    assert ro["action_scoped_binding"]["accepted_semantic_id"] == "ru-orthoepy-normative-stress-selection"
    assert ro["action_scoped_binding"]["status"] == "ACCEPTED_ACTION_SCOPED_COMPONENT_ONLY"
    assert ro["semantic_binding_status"] == "ACCEPTED_ACTION_SCOPED_STRESS_SEMANTIC_ONLY_NO_PRODUCTION_EVENT_ADMISSION"
    assert ro["nonstress_pronunciation_boundary"]["status"] == "SEPARATE_RU02_SUBJECT_BLOCKER_NOT_ISSUE_185_STRESS_ASSET_BLOCKER"
    # Preserve the broader Russian-subject blocker without treating it as a blocker of this stress-only live asset.
    assert pronunciation["next_exact_work"]["pronunciation_component_specific_independent_evidence_status"] == "MISSING_BLOCKER"
    assert pronunciation["next_exact_work"]["object_acceptance_status"] == "BLOCKED"
    assert pronunciation["acceptance_boundary"]["false_exact_mastery"] == 0

    # Dictionary words: exact source-backed denominator and exact canonical owner/action are known; production evidence remains gated.
    dictionary = page_by_key(probe, "dictionary_words")
    db = dictionary["exact_live_backing_candidate"]
    rd = rec["assets"]["dictionary_words"]
    assert dictionary["http_status"] == 200
    assert db["variable"] == "WORDS"
    assert db["row_count"] == rd["live_item_identity"]["row_count"] == 308
    assert db["live_candidate_key_count"] == db["live_candidate_key_unique"] == rd["live_item_identity"]["unique_id_count"] == 308
    assert db["live_candidate_keys_sha256"] == rd["live_item_identity"]["ordered_id_sha256"]
    td = thematic["dictionary_words"]
    assert td["live_count"] == td["fipi_count"] == 308
    assert td["exact_same_row_supported_count"] == 307 and td["unresolved_count"] == 1
    unresolved = td["unresolved"][0]
    assert unresolved["live_id"] == "rovesnik" and unresolved["live"] == "ровесник" and unresolved["fipi_row"] == "ровесники"
    assert rovesnik["resolution"]["source_backed_supported_total"] == 308
    assert rovesnik["resolution"]["unresolved_count_after_resolution"] == 0
    assert rd["fipi_2026_textual_provenance"]["source_backed_supported_count_total"] == 308
    assert rd["fipi_2026_textual_provenance"]["unresolved_count"] == 0
    assert rd["canonical_content_owner_binding"]["canonical_owner_id"] == "school-root-vowel-dictionary-unverifiable"
    assert rd["action_scoped_binding"]["status"] == "ACCEPTED_ACTION_SCOPED_COMPONENT_ONLY"
    assert rd["semantic_binding_status"] == "ACCEPTED_ACTION_SCOPED_COMPONENT_ONLY_NO_PRODUCTION_EVENT_ADMISSION"

    # Paronyms: exact 144 groups / 334 entries, exact FIPI provenance, one action-scoped semantic only.
    rpa = rec["assets"]["paronyms"]
    pi = paronyms["inventory"]
    pp = paronyms["textual_provenance_correspondence"]
    assert pi["full_live_group_count"] == pi["fipi_group_count"] == rpa["full_thematic_identity"]["group_count"] == 144
    assert pi["live_entry_count"] == rpa["full_thematic_identity"]["entry_count"] == 334
    assert pp["exact_match_count"] == 144 and pp["mismatch_count"] == 0
    assert rpa["action_scoped_binding"]["accepted_semantic_id"] == "ru-lexis-paronym-collocation-choice"
    assert rpa["semantic_binding_status"] == "ACCEPTED_ACTION_SCOPED_COMPONENT_ONLY_ASSET_WIDE_MULTI_ACTION_REMAINS_UNBOUND"

    # Phraseology: exact 285 IDs/provenance, fragment-identification action only.
    rf = rec["assets"]["phraseology"]
    tf = thematic["phraseology"]
    assert phraseology["live_row_count"] == phraseology["unique_explicit_id_count"] == rf["live_item_identity"]["row_count"] == rf["live_item_identity"]["unique_id_count"] == 285
    assert tf["live_count"] == tf["fipi_count"] == tf["exact_primary_match_count"] == 285
    assert tf["exact_primary_mismatch_count"] == 0
    assert rf["action_scoped_binding"]["accepted_semantic_id"] == "ru-lexis-phraseologism-fragment-identification"
    assert rf["semantic_binding_status"] == "ACCEPTED_ACTION_SCOPED_COMPONENT_ONLY_ASSET_WIDE_MULTI_ACTION_REMAINS_UNBOUND"

    assert rec["accepted_content_owner_bindings"] == 1
    assert rec["accepted_action_scoped_authority_reuses"] == 4
    assert len(rec["remaining_exact_blockers"]) == 4
    assert all("registered" in blocker for blocker in rec["remaining_exact_blockers"])
    assert all("pronunciation" not in blocker.lower() for blocker in rec["remaining_exact_blockers"])
    assert len(rec["separate_subject_blockers_not_issue_185_asset_reconciliation"]) == 1
    print("Thematic trainer canonical reconciliation PASS: all four live thematic assets have exact bounded content/action mapping; production mastery remains fail-closed")


if __name__ == "__main__":
    main()
