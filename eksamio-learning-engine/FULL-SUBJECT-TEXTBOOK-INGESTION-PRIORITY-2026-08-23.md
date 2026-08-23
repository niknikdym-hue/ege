# Eksamio — Initial Full-Subject Textbook Ingestion Priority

**Status:** CURRENT OWNER-APPROVED / LAUNCH-BLOCKING INGESTION PRIORITY  
**Date:** 2026-08-23

## Launch-blocking rule

Full-subject source/textbook ingestion is not optional background research. It is a launch-blocking dependency for every subject that Eksamio claims or sells as a complete subject program.

A subject may not be called `FULL_SUBJECT_PROGRAM_READY` and may not be represented to learners as a complete school-subject system until its declared launch scope has passed the source-completeness gate defined by `FULL-SUBJECT-SOURCE-AND-TEXTBOOK-INGESTION-POLICY-v0.1.md`.

For the staged first paid launch, Russian is therefore the first mandatory subject-source gate. Mathematics and Physics do not block a Russian-only launch unless they are included in that launch offer, but each becomes launch-blocking before it is added as a complete paid subject.

Accepted demos do not satisfy this gate by themselves.

## Strict sequential subject order

Textbook/source-ingestion work is performed strictly in this order:

1. **Russian language**;
2. **Mathematics**;
3. **Physics**.

Do not run the acquisition/selection/download/ingestion waves for these subjects in parallel.

Do not start the Mathematics textbook wave until the Russian textbook/source wave reaches its subject-approved completion checkpoint.

Do not start the Physics textbook wave until the Mathematics textbook/source wave reaches its subject-approved completion checkpoint.

Central PEIS, infrastructure, Tutor and other non-conflicting platform work may continue in parallel; this sequential rule applies to full-subject source/textbook acquisition and ingestion.

Do not broaden textbook acquisition to other subjects until Central Brain explicitly opens the next wave.

## Per-subject execution gates

Each subject passes through the same ordered gates:

1. `OFFICIAL_SCOPE_LOCKED` — current official school-program scope and grade range identified and versioned;
2. `TEXTBOOK_SELECTION_MATRIX_APPROVED` — lines/authors/editions reviewed and every candidate has an explicit acquisition decision;
3. `SELECTED_SOURCE_FILES_ACQUIRED` — only approved `TAKE_*` sources acquired into approved external storage;
4. `SOURCE_CATALOG_HASHED` — metadata, provenance, storage ID and SHA-256 recorded in GitHub;
5. `TEXTBOOK_INGESTION_MAPPED` — structural/knowledge/pedagogy evidence extracted and mapped to existing/candidate semantic identities without auto-admission;
6. `CROSS_SOURCE_RECONCILIATION_COMPLETE` — important conflicts, duplication and granularity differences resolved or explicitly blocked;
7. `SCOPE_COVERAGE_LEDGER_COMPLETE` — every normative scope item mapped, explicitly excluded, or explicitly blocked;
8. `FULL_SUBJECT_SCOPE_SOURCE_COMPLETE` — subject/human acceptance of scope/source completeness.

Only after gate 8 may the subject-source lane move to the next subject in the sequence.

This gate is source/scope completeness only. The subject still requires prerequisites, original Eksamio content bundles, PEIS connection and end-to-end acceptance before `FULL_SUBJECT_PROGRAM_READY`.

## Current active subject

`ACTIVE_TEXTBOOK_INGESTION_SUBJECT=RUSSIAN`

Current active step:

`RUSSIAN_TEXTBOOK_SELECTION_MATRIX`

At this step:

- identify the official Russian school-program scope for the declared grades;
- identify current/relevant textbook lines and authors;
- verify continuity across grades and FPU/current-program relevance where applicable;
- compare the candidate lines with the discovery catalog `https://so.11klasov.net`;
- assign `TAKE_*`, `DO_NOT_TAKE_*` or `NEEDS_REVIEW`;
- do **not** batch-download PDFs yet.

Mathematics and Physics remain queued, not active.

## Scope by subject

- Russian language: build the full school-program coverage matrix across the applicable 1–11 grade scope.
- Mathematics: build the full school-program coverage matrix across 1–11, preserving one route-independent model with later BASE/PROFILE/OGE/EGE/VPR overlays.
- Physics: use the official current school-program grade scope as the authority; do not infer the full subject from EGE demos alone.

## Selection before download

Do not download every textbook from an available catalog. First build a selection matrix:

`subject -> grade -> official program scope -> textbook line/authors -> current/FPU relevance -> continuity across grades -> pedagogical value -> duplication status -> acquisition decision`

Preferred selection principle:

- prioritize textbook lines that are current/relevant to the Federal List of Textbooks or otherwise clearly tied to the current Russian school program;
- prefer coherent author/publisher lines spanning multiple grades over isolated one-off books where quality is comparable;
- keep more than one strong line only when it materially improves coverage, pedagogy, alternative explanations, or granularity review;
- exclude duplicate editions, workbooks, answer keys/GDZ, exam crammers and unrelated supplementary books unless a specific ingestion need is documented;
- older editions may be retained only when they add unique subject/pedagogical value and are clearly marked historical/non-current.

The site `https://so.11klasov.net` is treated as a discovery/acquisition catalog, not as curriculum authority and not as proof of redistribution rights.

## Storage boundary

Default binary-storage plan for selected source PDFs:

- source PDFs: external source storage, with Google Drive preferred for the initial bounded corpus;
- GitHub: catalog/metadata, source URL, authors, grade, edition/year, acquisition note, rights status if known, SHA-256, Drive/object identifier, ingestion status, mappings and derived reviewable artifacts;
- owner Mac: no persistent textbook/download folders unless explicitly requested by the owner for the current task.

Do not commit textbook PDFs to GitHub unless a separate explicit source/right/size decision authorizes it.

## Selection statuses

Every proposed acquisition must have one of:

- `TAKE_PRIMARY_LINE`;
- `TAKE_SECONDARY_LINE_FOR_COVERAGE_OR_PEDAGOGY`;
- `DO_NOT_TAKE_DUPLICATE`;
- `DO_NOT_TAKE_OUTDATED_OR_IRRELEVANT`;
- `NEEDS_REVIEW`.

Only `TAKE_*` rows are eligible for download.

## Stop conditions

Stop rather than silently weakening this plan if:

- the official normative school-program source for the active subject/grade scope is not verified;
- no defensible textbook-line selection can be made from current evidence;
- acquisition would require downloading all books indiscriminately;
- selected files would need to be stored persistently on the owner's Mac without explicit permission;
- rights status is being treated as redistribution permission merely because a PDF is downloadable;
- a textbook extraction is being auto-admitted as canonical semantic truth.

Use the applicable blocker, including `BLOCKED_FULL_SUBJECT_NORMATIVE_SCOPE_SOURCE_MISSING` or `BLOCKED_LOCAL_WORKSPACE_CREATION_REQUIRES_OWNER_PERMISSION`, instead of claiming completeness.

This document works together with `FULL-SUBJECT-SOURCE-AND-TEXTBOOK-INGESTION-POLICY-v0.1.md` and does not supersede its source hierarchy, copyright boundary or canonical-admission rules.
