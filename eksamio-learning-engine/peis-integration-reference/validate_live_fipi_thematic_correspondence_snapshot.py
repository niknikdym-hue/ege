#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "LIVE-FIPI-THEMATIC-CORRESPONDENCE-v0.1.json"
PRIMARY_OUT = Path("live-fipi-correspondence-snapshot-primary.json")
MEMBERSHIP_OUT = Path("live-fipi-correspondence-snapshot-membership.json")

snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

subprocess.run(
    [
        "node",
        str(ROOT / "probe_dictionary_same_row_family_membership.mjs"),
    ],
    check=True,
    env={
        **__import__("os").environ,
        "PROBE_OUT": str(MEMBERSHIP_OUT),
    },
)

# The membership probe intentionally writes its primary dependency to this fixed name.
primary_generated = Path("dictionary-same-row-family-membership-primary.json")
if not primary_generated.exists():
    raise SystemExit("primary correspondence output missing")
primary = json.loads(primary_generated.read_text(encoding="utf-8"))
membership = json.loads(MEMBERSHIP_OUT.read_text(encoding="utf-8"))
PRIMARY_OUT.write_text(json.dumps(primary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

expected_sources = snapshot["exact_sources"]
observed_sources = primary["exact_sources"]
source_key_map = {
    "dictionary_live": "dictionary_live",
    "phraseology_live": "phraseology_live",
    "orthography_fipi_2026": "orthography_fipi",
    "lexicon_phraseology_fipi_2026": "lexicon_fipi",
}
for expected_key, observed_key in source_key_map.items():
    expected = expected_sources[expected_key]
    observed = observed_sources[observed_key]
    assert observed["url"] == expected["url"], (expected_key, observed["url"], expected["url"])
    assert observed["byte_count"] == expected["byte_count"], (expected_key, observed["byte_count"], expected["byte_count"])
    assert observed["sha256"] == expected["sha256"], (expected_key, observed["sha256"], expected["sha256"])

phrase_expected = snapshot["phraseology"]
phrase = primary["phraseology"]
assert phrase["live_count"] == phrase_expected["live_count"] == 285
assert phrase["source_count"] == phrase_expected["fipi_count"] == 285
assert phrase["exact_primary_match_count"] == phrase_expected["exact_primary_match_count"] == 285
assert phrase["exact_primary_mismatch_count"] == phrase_expected["exact_primary_mismatch_count"] == 0
assert phrase["status"] == phrase_expected["status"] == "EXACT_PRIMARY_ROW_CORRESPONDENCE"
assert phrase["live_ordered_sha256"] == phrase_expected["live_ordered_normalized_sha256"]
assert phrase["source_primary_ordered_sha256"] == phrase_expected["source_primary_ordered_normalized_sha256"]

word_expected = snapshot["dictionary_words"]
assert membership["dictionary_total"] == word_expected["live_count"] == 308
assert membership["primary_exact_count"] == word_expected["primary_exact_match_count"] == 284
assert membership["additional_exact_same_row_member_count"] == word_expected["same_row_additional_exact_member_match_count"] == 23
assert membership["exact_same_row_supported_count"] == word_expected["exact_same_row_supported_count"] == 307
assert membership["unresolved_count"] == word_expected["unresolved_count"] == 1
assert len(membership["unresolved"]) == 1
unresolved = membership["unresolved"][0]
expected_unresolved = word_expected["unresolved"][0]
assert unresolved["index_1based"] == expected_unresolved["index_1based"] == 237
assert unresolved["live_id"] == expected_unresolved["live_id"] == "rovesnik"
assert unresolved["live"] == expected_unresolved["live"] == "ровесник"
assert unresolved["source_full_row"] == expected_unresolved["fipi_row"] == "ровесники"

for payload in (snapshot, primary, membership):
    assert payload["semantic_admissions"] == 0
    assert payload["object_closures"] == 0
    assert payload["mastery_admissions"] == 0
    assert payload["false_exact_mastery"] == 0
    assert payload["registered_user_identity_required_for_future_canonical_evidence"] is True

print("LIVE_FIPI_THEMATIC_CORRESPONDENCE_SNAPSHOT_PASS")
print("phraseology=285/285 exact primary rows")
print("dictionary=307/308 exact same-row supported; blocker=rovesnik:ровесник<>ровесники")
