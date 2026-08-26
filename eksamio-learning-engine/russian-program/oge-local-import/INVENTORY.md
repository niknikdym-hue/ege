# Russian OGE local-source inventory

Inventory date: 2026-08-27  
Source boundary: `exam-platform-tilda/tilda-ready/pages/`  
Import boundary: Russian OGE only; all EGE directories excluded.

## Pages and files found

- 11 Russian OGE page directories, 44 files excluding `.DS_Store`.
- 8 executable task pages (`oge-russkiy-zadanie-1` through `oge-russkiy-zadanie-8`), 35 files.
- 3 navigation/topic pages (`oge-russkiy`, `oge-russkiy-konstruktor-variantov`, `oge-russkiy-zadanie-nn`), 9 files. They contain navigation/presentation, not additional task variants, so they were not imported as learner items.

## Executable task-bank inventory before import

| OGE task | Variants | Answer/self-check present | Scoring in local page | Required assets | RU program mapping |
|---|---:|---|---|---|---|
| 1 | 5 | sample answer, 3 microthemes per variant, compression notes, six-item learner self-check | self-check; no claim of official automated score | 5 MP3 + 5 transcript TXT | RU-PROG-15 |
| 2 | 5 | yes | exact match | none | RU-PROG-09 |
| 3 | 5 | yes | exact match | none | RU-PROG-09 |
| 4 | 5 | yes | exact match | none | RU-PROG-09 |
| 5 | 5 | yes; per-position punctuation explanations present | exact set match in page, represented as deterministic exact match | none | RU-PROG-10 |
| 6 | 5 | yes | exact match | none | RU-PROG-08 |
| 7 | 5 | yes; per-gap explanations present | exact match | none | RU-PROG-08 |
| 8 | 5 | yes; accepted answers, rule title, analysis and steps present | exact match | none | RU-PROG-07 |

Totals before import: 40 variants, 40 answer/reference-answer records, 40 scorers (35 exact-match and 5 self-check), 10 required runtime/source assets.

## Identity inventory

The current accepted RU1 semantic registry contains no accepted learner-item identity equal to any of the 40 local task/variant IDs. No duplicate learner-item identity was found elsewhere in the repository. The import therefore preserves the local IDs as identity proposals and marks every one `PROPOSED_NOT_CANONICAL` / `SUBJECT_ACCEPTANCE_REQUIRED`; it does not admit new canonical identities.

## Recorded source issue

The task-1 page loads MP3 files from an external GitHub Pages base URL although matching owner-local MP3 files are present. The imported items reference repository-relative copies only. No task wording, answer, scoring rule, microtheme, sample, explanation or source text was corrected or rewritten during import.
