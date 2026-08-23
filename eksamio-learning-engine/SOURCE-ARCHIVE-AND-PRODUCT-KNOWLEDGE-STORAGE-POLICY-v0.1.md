# Eksamio — Source Archive & Product Knowledge Storage Policy v0.1

**Status:** CURRENT OWNER-APPROVED STORAGE AUTHORITY  
**Date:** 2026-08-23  
**Scope:** textbook/source ingestion for Full Subject programs

## 1. Core rule

`SOURCE ARCHIVE != PRODUCT KNOWLEDGE STORE`.

An ingested textbook/source file is not automatically disposable after extraction, and it is not itself the production knowledge layer used by PEIS/Tutor.

Eksamio must preserve a clear separation between:

1. **Source Archive** — original selected source files retained for provenance, reprocessing, dispute resolution and audit;
2. **GitHub Source Catalog** — durable metadata, hashes, source locators, status and ingestion provenance;
3. **Eksamio Product Knowledge** — reviewed structured knowledge and original Eksamio learning artifacts suitable for runtime use;
4. **Tutor Context Projection** — only the bounded knowledge needed for the current learning turn, not whole textbooks by default.

## 2. Source Archive purpose

Selected original textbook/source files should normally be retained after ingestion when lawful and practical because they may be needed to:

- prove exactly which edition/source supported a claim;
- re-run ingestion with improved parsers/extractors;
- verify or correct an extraction error;
- resolve subject-source conflicts;
- audit canonical identity/prerequisite provenance;
- compare editions or curriculum changes over time;
- reproduce historical decisions.

Do not delete the only source copy merely because an AI/parser already extracted information from it.

## 3. Initial binary-storage location

For the bounded first corpus, the preferred Source Archive is external object/file storage, initially Google Drive when available and sufficient.

Default rules:

- textbook/source PDFs are not committed to GitHub;
- no persistent textbook/download folders are created on the owner's Mac unless explicitly requested;
- GitHub stores only catalog/provenance artifacts, not the full binary corpus;
- a later move from Google Drive to private Yandex Object Storage/cold storage is allowed when scale, automation, retention or operational needs justify it;
- do not build Yandex binary archival infrastructure early merely because it may be useful later.

Google Drive is a source archive, not a production dependency.

## 4. Runtime independence / Google outage rule

**Mandatory invariant:** normal Eksamio runtime in Yandex must continue to function when Google Drive is unreachable, disconnected, rate-limited, credentials expire, or the archive provider has a temporary outage.

Google Drive must never be on the hot path for:

- learner login/session;
- diagnostics;
- PEIS evidence/state/readiness/retention/NBA;
- trainers/homework;
- AI Tutor grounded help after the relevant knowledge has been admitted;
- independent verification;
- production scoring;
- normal subject-content delivery.

After ingestion and subject acceptance, all knowledge required for normal learner operation must already exist in the approved Eksamio Product Knowledge / PEIS-serving contour in Yandex or another production-admitted provider-neutral store.

Expected failure behavior when Google Drive is unavailable:

- `LEARNER_RUNTIME_CONTINUES=true`;
- `PEIS_CONTINUES=true`;
- `TUTOR_USES_ADMITTED_PRODUCT_KNOWLEDGE=true`;
- `SOURCE_REINGESTION_OR_DEEP_AUDIT_MAY_BE_DEFERRED=true`;
- no emergency direct textbook fetch is introduced into production runtime.

A Drive outage may block only operations that genuinely require the original binary, for example:

- first ingestion of a not-yet-ingested source;
- re-ingestion with a new extractor;
- page-level source dispute/audit;
- edition comparison requiring the original file.

Those operations must fail explicitly/defer safely; they must not degrade already-admitted learner-facing product knowledge.

If future operational requirements demand stronger source-archive continuity, add a secondary private archive/mirror (for example Yandex Object Storage/cold storage) through a separate bounded task. Do not create that infrastructure prematurely, but do not make Google Drive a single point of failure for production learning.

## 5. GitHub catalog requirements

For every archived source preserve, when available:

- stable `source_id`;
- subject;
- grade;
- title;
- authors;
- publisher;
- edition/year;
- source/acquisition URL or note;
- original filename;
- SHA-256 of the archived file;
- binary-storage provider;
- Drive/object identifier or stable storage reference;
- rights/retention status;
- ingestion status/version;
- exact page/section locators used by derived knowledge;
- superseded/replaced relationships for later editions.

The catalog is durable authority for provenance even if the physical storage provider changes later.

## 6. Rights / retention statuses

File possession or free download does not prove redistribution rights.

Use an explicit retention status, at minimum:

- `SOURCE_ARCHIVE_ALLOWED` — long-term internal source retention is accepted under the current source/right assessment;
- `TEMPORARY_INGESTION_ONLY` — source may be used for bounded analysis, but long-term retention is not yet admitted;
- `RIGHTS_NEEDS_REVIEW` — rights/retention status is unresolved; do not infer permission;
- `SOURCE_REMOVAL_APPROVED` — deletion from source archive has been explicitly approved after retention/right review.

These statuses concern source storage. They do not automatically authorize learner-facing reproduction.

## 7. Product Knowledge Store

After ingestion and subject review, Eksamio should store/use structured derived knowledge rather than whole source books in the production learning path.

Product knowledge may include, subject to the canonical-admission and originality policies:

- canonical semantic identities and boundaries;
- source-backed prerequisite relations;
- normalized concept/method/rule representations;
- misconception/error structures;
- grade/program applicability;
- source provenance and locators;
- scope coverage mappings;
- exam/diagnostic overlays;
- original Eksamio explanations;
- original worked examples;
- original guided/independent/mixed/retention/verification content.

Production PEIS/Yandex services may persist this reviewed structured layer according to the applicable production architecture.

Do not treat long copied textbook passages or copied exercise banks as Eksamio Product Knowledge unless separate reproduction authority exists.

## 8. Runtime / Tutor boundary

The Tutor and normal PEIS runtime should not repeatedly read whole textbook PDFs merely because they are archived.

Default runtime path:

`source archive -> ingestion/review -> canonical/structured Eksamio knowledge -> bounded context projection -> Tutor/learning flow`.

Tutor requests should receive only the smallest verified context needed for the learning objective.

Raw full-book retrieval is an exceptional review/re-ingestion operation, not the normal learner runtime path.

## 9. Deletion rule

Source deletion is never an automatic post-ingestion step.

A source may be removed only when:

1. retention/right policy allows or requires removal;
2. the removal is explicitly approved;
3. derived GitHub provenance remains sufficient to identify what source/version was used;
4. no unresolved audit/reprocessing dependency requires the binary;
5. deletion does not create a false claim that derived knowledge can still be independently reproduced from a missing source.

If removal is required for rights reasons, mark the catalog clearly rather than silently deleting provenance.

## 10. Integrity rule

Whenever a source is admitted to the archive, compute and persist its SHA-256.

If a file is later replaced by another edition/version, do not overwrite the historical identity silently. Create a new source/version record and mark the old one superseded/replaced where appropriate.

## 11. Relationship to Full Subject ingestion

This policy is mandatory together with:

- `FULL-SUBJECT-SOURCE-AND-TEXTBOOK-INGESTION-POLICY-v0.1.md`;
- `FULL-SUBJECT-TEXTBOOK-INGESTION-PRIORITY-2026-08-23.md`;
- `LOCAL-WORKSPACE-POLICY.md`.

For the current sequential wave:

`Russian -> Mathematics -> Physics`.

The current active step remains `RUSSIAN_TEXTBOOK_SELECTION_MATRIX`; no bulk Russian download is authorized before the matrix is reviewed.

## 12. Operational consequence

For every future download/ingestion task Codex/agents must answer separately:

- where the original binary will be archived;
- what GitHub catalog record will identify it;
- what retention/right status applies;
- what structured knowledge is allowed to move into Eksamio/Yandex;
- whether learner-facing reproduction rights exist;
- whether the raw source remains needed after ingestion;
- whether normal Yandex runtime remains fully functional with the source archive unavailable.

Never collapse these questions into a single vague status such as `IMPORTED`.
