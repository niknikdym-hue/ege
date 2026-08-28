# Russian official source knowledge — Sep-1 launch lane

This directory is the deterministic **official-source requirement layer** for `Eksamio Pro — Русский`.

Authority boundary:
- launch source truth: EDSOO Russian 5–9 (2025), EDSOO Russian 10–11 basic (2025), FIPI OGE Russian 2026 final, FIPI EGE Russian 2026 final;
- `FIPI-OGE-RU-2027-PROJECT` is explicitly forbidden as Sep-1 launch truth;
- verified Source Archive PDF bytes stay outside Git; Git stores fingerprints, locators and normalized Eksamio-owned requirement meaning only;
- commercial textbook bytes are not ingested into this package;
- this layer does **not** admit learner content or `ru-*` semantic identities.

Artifacts:
- `RUSSIAN-OFFICIAL-SOURCE-MANIFEST-v1.0.json` — 8 concrete source documents and exact SHA-256 fingerprints;
- `RUSSIAN-OFFICIAL-REQUIREMENTS-INDEX-v1.0.json` + `requirements/*.json` — 1400 normalized official requirement records across all 16 `RU-PROG` modules;
- `build_source_semantic_crosswalk.py` — executable fail-closed requirement → current/proposed content classification;
- `RUSSIAN-SOURCE-SEMANTIC-CROSSWALK-INDEX-v1.0.json` — exact current-main/PR #139 reference boundary;
- `validate_russian_source_knowledge.py` — deterministic validator and negative guards.

A `READY` source-knowledge preflight gate means only that official source requirements are deterministically accounted for. It does not mean Russian learner content is subject-accepted or launch-ready.
