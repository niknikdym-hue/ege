# Eksamio — Initial Full-Subject Textbook Ingestion Priority

**Status:** CURRENT OWNER-APPROVED INGESTION PRIORITY  
**Date:** 2026-08-23

## Initial subject wave

The first textbook/source-ingestion wave is limited to exactly these subjects:

1. Russian language;
2. Mathematics;
3. Physics.

Do not broaden textbook acquisition to other subjects until Central Brain explicitly opens the next wave.

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

## Required next artifact

Before any batch download, create a reviewable selection matrix for Russian, Mathematics and Physics. Every proposed acquisition must have one of:

- `TAKE_PRIMARY_LINE`;
- `TAKE_SECONDARY_LINE_FOR_COVERAGE_OR_PEDAGOGY`;
- `DO_NOT_TAKE_DUPLICATE`;
- `DO_NOT_TAKE_OUTDATED_OR_IRRELEVANT`;
- `NEEDS_REVIEW`.

Only `TAKE_*` rows are eligible for download.

This document works together with `FULL-SUBJECT-SOURCE-AND-TEXTBOOK-INGESTION-POLICY-v0.1.md` and does not supersede its source hierarchy, copyright boundary or canonical-admission rules.
