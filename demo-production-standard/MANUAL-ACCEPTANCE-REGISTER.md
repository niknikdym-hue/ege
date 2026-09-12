# EGE demo manual acceptance register

**Status:** DURABLE MANUAL OWNER / SUBJECT ACCEPTANCE RECORD  
**Recorded:** 2026-09-02  
**Baseline `main` at recording:** `85d2f2b3dd0cf56c428f57c8a5c7d1b636ecebbb`

This register records explicit manual owner/subject acceptance decisions for Eksamio EGE interactive demos. It does not replace `00-READ-FIRST-EGE-DEMOVERSII-MASTER.md`, `demo-production-standard/README.md`, subject/year evidence, CI, scorer evidence, or `PUBLISHED_SMOKE_PASS`.

A row marked `PASS / ACCEPTED` means the named demo has completed the owner's manual review and is accepted at that manual-review boundary. Do not return an accepted row to routine manual-review backlog without a concrete reopening trigger.

## Accepted demos

| Subject | Year | Manual owner / subject acceptance | Decision date | Reopen only if |
| --- | ---: | --- | --- | --- |
| Biology / Биология | 2026 | **PASS / ACCEPTED** | 2026-09-02 | official source/version changes; demo/runtime/scorer/assets change in a way that can affect acceptance; concrete regression; source contradiction |
| History / История | 2026 | **PASS / ACCEPTED** | 2026-09-02 | official source/version changes; demo/runtime/scorer/assets change in a way that can affect acceptance; concrete regression; source contradiction |
| Chemistry / Химия | 2026 | **PASS / ACCEPTED** | 2026-09-02 | official source/version changes; demo/runtime/scorer/assets change in a way that can affect acceptance; concrete regression; source contradiction |
| Social Studies / Обществознание | 2026 | **PASS / ACCEPTED** | 2026-09-02 | official source/version changes; demo/runtime/scorer/assets change in a way that can affect acceptance; concrete regression; source contradiction |

## Boundary of this record

- This is an acceptance/status record only; it does **not** mutate any demo content, answer keys, scorer, assets, T123 blocks, Tilda page, or runtime.
- Existing technical/source/browser/release evidence remains authoritative for its own gates and is not rewritten by this manual decision.
- Manual acceptance must not be downgraded merely because another unrelated project lane changes.
- If a reopening trigger occurs, re-check only the affected gate/scope unless the change invalidates broader evidence.
- A future subject/year can be added here only after an explicit manual owner/subject acceptance decision.
