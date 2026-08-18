# TASK-005 — Russian Exceptions Wave 6: слитно / раздельно through homonym contrasts

Date: 2026-08-12

## Goal

Build the next deliberate P2 expansion wave as a coherent future-course module, not as a random list of rare exceptions.

Theme:
**Одинаково/похоже звучит — разная часть речи, функция, значение и написание.**

Current reviewed 93-card bank must remain frozen while Wave 6 is developed and tested separately.

## Why this theme is next

The remaining uncovered P2 source bank contains many structurally related Task-14 contrasts. They reuse three strong explanation branches already present in the Learning Engine and map naturally to Drabkina/Subbotin-style tables and diagnostic algorithms:

1. цельный союз vs самостоятельные слова;
2. производный предлог vs существительное с предлогом;
3. наречие vs предложно-именное сочетание.

This is high-value course content because one verified table/algorithm can serve many practice cards and later expand directly into a Russian-course lesson.

## Target pairs — 14

### A. Союз vs самостоятельные слова

1. ЧТОБЫ / ЧТО БЫ
2. ТОЖЕ / ТО ЖЕ
3. ТАКЖЕ / ТАК ЖЕ
4. ПРИЧЁМ / ПРИ ЧЁМ
5. ПРИТОМ / ПРИ ТОМ
6. ЗАТО / ЗА ТО
7. ИТАК / И ТАК

### B. Производный предлог vs существительное с предлогом

8. ВВИДУ / В ВИДУ
9. ВСЛЕДСТВИЕ / В СЛЕДСТВИЕ
10. НАСЧЁТ / НА СЧЁТ
11. ВРОДЕ / В РОДЕ

### C. Наречие vs предложно-именное сочетание

12. ВНАЧАЛЕ / В НАЧАЛЕ
13. СНАЧАЛА / С НАЧАЛА
14. НАЗАВТРА / НА ЗАВТРА

## Card design

Every pair must be trained in **both directions**.

Planned Wave 6 size: 28 cards.

For each pair:

- card A requires the solid form in a natural context;
- card B requires the separate form in a different natural context;
- at least one of the two must be `independent_context` or `transfer`;
- feedback must state the diagnostic rule, apply it to the exact sentence, and contrast the other member of the pair;
- no learner card may teach a visual mnemonic as if it were the rule.

## Method baseline

Reuse and strengthen the existing explanation branches in:

- `38-RUSSIAN-EXPLANATION-ORTHOGRAPHY-13-14-v0.1.json`;
- `62-RUSSIAN-EXPLANATION-TASK14-WRITING-SPLITS-v0.1.json`.

Use the Drabkina/Subbotin corpus fully for school-facing method: tables, schemes, diagnostic questions, contrast examples and error logic.

Relevant project corpus includes the 7-class orthography practical workbook and the 10-class EGE orthography book. Do not fabricate page/section locators if they have not been independently established.

Normative source remains the verified source-bank chain (Rosenthal where exact orthographic rule is covered + current academic/dictionary cross-check when needed).

## Core teaching algorithm

The learner must not start with “слитно или раздельно?”. Start with:

1. What construction is this in the sentence?
2. Is it a service word with a whole meaning, or does the noun/pronoun/adverb retain its own meaning?
3. Which semantic/grammatical replacement is valid for this exact pair?
4. Is there a diagnostic dependent word / particle movement / pair continuation?
5. Only then choose spelling.

## Safety

- Do NOT add Wave 6 to manifest 119 during drafting.
- Do NOT alter the current 93-card runtime/package.
- Do NOT update Tilda.
- Do NOT merge PR #23 merely because Wave 6 candidate passes.
- Each of 28 cards must be manually reviewed before promotion.

## Acceptance

Before promotion:

- source audit PASS for 14/14 pairs;
- 28/28 candidate cards manually reviewed;
- every pair tested in both directions;
- no duplicate context_signature;
- candidate practice build PASS;
- current 93 still PASS independently;
- candidate coverage/build/runtime/T123/package PASS;
- Chromium preview PASS;
- final generated candidate payload manually inspected;
- no non-FIPI internal provenance leaks to learner runtime.
