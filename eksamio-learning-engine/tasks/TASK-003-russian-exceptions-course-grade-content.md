# TASK-003 — Russian Exceptions Trainer: course-grade content reaudit corrections

TASK_ID: TASK-003
STATUS: IN_REVIEW
MODE: IMPLEMENTATION / CONTENT_AUDIT

## Scope

Apply the completed 80/80 linguistic/content audit to the current Russian Exceptions Trainer source and practice layers, raising learner explanations to reusable future-course quality.

The method baseline is Drabkina/Subbotin:

`theory -> table/scheme -> algorithm -> application -> contrast -> trap -> independent check`.

Current academic/dictionary norm overrides outdated teaching simplifications.

## Inputs

- `128-RUSSIAN-EXCEPTIONS-CONTENT-AUDIT-RULES.txt`
- `129-NEW-CHAT-HANDOFF-RUSSIAN-EXCEPTIONS.txt`
- `130-RUSSIAN-EXCEPTIONS-80-CARD-DRABKINA-AUDIT-v0.1.txt`
- `131-RUSSIAN-EXCEPTIONS-COURSE-GRADE-CORRECTIONS-v0.1.json`
- `russkiy-knigi/` Drabkina 5–11 corpus
- current exceptions/practice manifests and builders

## Required content decisions

1. Keep exactly 80 active practice cards after replacements.
2. Apply every audited FIX, not just answer corrections.
3. Replace learner-unsafe `в конце концов = always non-introductory` with a context distinction.
4. Replace obsolete `зоревать` learner answer with current `заревать`.
5. Upgrade N/NN to course-grade branches, including:
   - кожаный and -АН-;
   - деревянный / оловянный / стеклянный;
   - ветреный / безветренный / ветряной;
   - кованый / кованный;
   - жёваный / жёванный;
   - раненый / раненный;
   - названый брат;
   - посажёный отец.
6. Use the fuller current `СКАК-/СКОК-/СКАЧ-/СКОЧ-` model.
7. Remove vague/false Rosenthal provenance for morphology, syntax and lexical norms.
8. Use Drabkina as a method source with accurate corpus mapping; never invent a page/PDF locator.
9. Humanize the standalone Exceptions Trainer intro copy approved by the user.

## Allowed paths

- `eksamio-learning-engine/32-RUSSIAN-EXPLANATION-BANK-v0.1.json`
- `eksamio-learning-engine/33-RUSSIAN-EXCEPTIONS-BANK-v0.1.json`
- `eksamio-learning-engine/48-RUSSIAN-EXCEPTIONS-WAVE2-NORMS-v0.1.json`
- `eksamio-learning-engine/87-RUSSIAN-EXCEPTIONS-MORPHOLOGY-TASK7-v0.1.json`
- `eksamio-learning-engine/88-RUSSIAN-EXCEPTIONS-SYNTAX-TASK8-v0.1.json`
- `eksamio-learning-engine/89-RUSSIAN-EXCEPTIONS-PARONYMS-HIGH-VALUE-v0.1.json`
- `eksamio-learning-engine/118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json`
- `eksamio-learning-engine/119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json`
- additive `13x-*` source/audit/method files
- `eksamio-learning-engine/build/build_russian_exceptions_bank_current_v2.py`
- additive practice builder under `eksamio-learning-engine/build/`
- `eksamio-learning-engine/standalone-exceptions-trainer/ui/rex-app.js`
- matching task/result/review/handoff records

## Forbidden changes

- no Tilda package publication;
- no live Tilda block replacement;
- no current EGE Russian trainer changes;
- no scoring/localStorage/attempt-contract changes;
- no answer synthesis without source support;
- no source-label leakage to learner runtime.

## Validation

Static gate in this task must confirm:
- audited scope = 80/80;
- audit disposition = 48 PASS / 30 FIX / 2 FAIL-REPLACE;
- current practice manifest raw count = 82, disabled = 2, expected active = 80;
- 131 overlay patch entries = 32 = 30 FIX + 2 replacements;
- `ex-practice-zorevat-001` inactive and replacement `ex-practice-zarevat-current-001` active;
- false universal current `в конце концов` correction inactive and context replacement active;
- source manifest disables `alt_root_zorevat` and maps to `alt_root_zarevat_current`;
- no production/Tilda path changed.

Machine canonical build, runtime package build and browser/Chromium gate remain mandatory before any Tilda package is issued.

## Stop condition

Stop after:
1. content/source corrections are committed on dedicated branch;
2. durable result record exists;
3. static gate is recorded;
4. draft PR is opened;
5. production remains HOLD until machine + browser validation.
