# RESULT-005 — Russian Exceptions Wave 6: solid/separate course-grade checkpoint

Date: 2026-08-12

## Decision

**PASS as the current non-production 121-card checkpoint.**

Tilda/publication remains **HOLD** until the user explicitly moves to the Tilda preview/publication step.

## Starting point

Before Wave 6, the current reviewed practice bank contained 93 active learner cards and had complete P0/P1 coverage.

The next expansion was deliberately chosen from lower-priority P2 source material by pedagogical value, not raw count.

Theme:

**Слитно / раздельно: одинаково или похоже звучит — разная часть речи, функция, значение и написание.**

## Wave 6 source gate

Source audit:
`141-RUSSIAN-EXCEPTIONS-WAVE6-SOLID-SEPARATE-SOURCE-AUDIT.txt`

Result: **PASS 14/14 pairs**.

Pairs:

1. ЧТОБЫ / ЧТО БЫ
2. ТОЖЕ / ТО ЖЕ
3. ТАКЖЕ / ТАК ЖЕ
4. ПРИЧЁМ / ПРИ ЧЁМ
5. ПРИТОМ / ПРИ ТОМ
6. ЗАТО / ЗА ТО
7. ИТАК / И ТАК
8. ВВИДУ / В ВИДУ
9. ВСЛЕДСТВИЕ / В СЛЕДСТВИЕ
10. НАСЧЁТ / НА СЧЁТ
11. ВРОДЕ / В РОДЕ
12. ВНАЧАЛЕ / В НАЧАЛЕ
13. СНАЧАЛА / С НАЧАЛА
14. НАЗАВТРА / НА ЗАВТРА

The teaching model is not «remember where the space goes». It is:

construction type -> grammatical/semantic diagnosis -> pair-specific replacement/question -> spelling -> contrast.

Drabkina/Subbotin remains the school-facing method baseline for tables, diagnostic schemes and error logic; current academic/dictionary norm controls the final boundary.

## Practice design

Historical draft:
`142-RUSSIAN-EXCEPTIONS-PRACTICE-WAVE6-SOLID-SEPARATE-DRAFT-v0.1.json`

Wave size: **28 cards**.

Every one of 14 pairs is trained in both directions:

- solid form;
- separate form.

Every pair has independent-context/transfer evidence.

## Manual review

Manual review:
`144-RUSSIAN-EXCEPTIONS-WAVE6-MANUAL-CONTENT-REVIEW.txt`

Review overlay:
`145-RUSSIAN-EXCEPTIONS-WAVE6-REVIEWED-OVERLAY-v0.1.json`

Result: **28/28 REVIEWED PASS** after three explicit editorial fixes.

Editorial fixes:

1. `ЗА ТО`
   - replaced a less-natural example with:
     `Я проголосовал за то предложение, которое поддержала группа.`

2. `В РОДЕ`
   - replaced an artificial family-line example with:
     `Ошибка была в роде существительного: к слову подобрали неверную форму согласования.`

3. reverse `ВРОДЕ` feedback
   - generated-artifact inspection caught a stale reference to the discarded old `В РОДЕ` example;
   - feedback now contrasts with the clean grammatical-noun example `ошибка в роде существительного`.

This third fix is important: machine/Chromium PASS alone did not detect weak learner wording. Generated-payload inspection remained mandatory.

## Candidate gate before promotion

Wave 6 was first validated separately from current 93.

Successful isolated candidate:

- practice total: 121;
- Wave 6 cards: 28;
- 14 target pairs x exactly 2 cards;
- both answer directions per pair;
- unique context signatures;
- all reviewed statuses applied;
- coverage audit PASS;
- learner-safe runtime PASS;
- forbidden-source leak check PASS;
- T123 chunk build PASS;
- standalone package PASS;
- Chromium preview PASS.

Candidate generated artifact was manually opened and inspected before promotion.

## Promotion into current

Current practice manifest:
`119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json`

Current registered/raw practice items: **123**.

Disabled historical items: **2**.

Current active learner cards: **121**.

Current course-grade builder:
`build/build_russian_exceptions_practice_course_grade.py`

The builder now centrally applies Wave 6 review overlay 145 only if Wave 6 draft bank 142 is active. It fails closed unless:

- active Wave 6 IDs exactly match all 28 reviewed IDs;
- all 28 historical draft statuses are transformed to schema-valid `reviewed`;
- exactly the three approved editorial patches are applied;
- active-card count remains equal to the manifest contract.

The historical isolated candidate wrapper now reuses this same central review logic, avoiding divergent implementations.

## Final current-121 gate

The old duplicate Wave 6 CI job was removed after promotion. Wave 6 invariants are now part of the single main current gate.

Successful final main-only GitHub Actions run:
`31628404036`

Gated head:
`8b73620bb63e533c3f05a6814f488833c0bb1677`

Result: **PASS**.

Passed:

- current canonical source build;
- current course-grade practice build;
- launch-priority build;
- practice coverage audit;
- explicit 121-card count check;
- explicit 28-card Wave 6 / 14-pair bidirectional structure check;
- explicit reviewed-status and unique-context checks;
- explicit absence of rejected learner wording;
- runtime build;
- learner-source leakage gate;
- aggregate Learning Engine validation;
- browser core evaluator/state/selector tests;
- standalone package build;
- Chromium preview smoke;
- runtime size audit.

## Final generated artifact inspection

The final artifact from run `31628404036` was downloaded and inspected after CI PASS.

Confirmed:

- practice cards: **121**;
- runtime practice cards: **121**;
- Wave 6 cards: **28**;
- Wave 6 target exception IDs: **14**;
- all canonical Wave 6 statuses: `reviewed`;
- runtime exception items represented: **88**;
- topics: 6;
- `за то предложение` present;
- `ошибка в роде существительного` present;
- `в роде существительного` present;
- discarded phrase `в его роде было несколько художников` absent;
- discarded phrase `В роде этого мастера было несколько известных художников` absent;
- discarded old `за то` example absent;
- earlier course-grade N/NN corrections remain intact;
- current `в конце концов` contrast remains intact;
- current `заревать / заревал` remains intact;
- forbidden Rosenthal/Gramota/Drabkina/provenance/source-path labels remain absent from learner runtime.

## Current coverage

Canonical source exception/special-case items: **127**.

Practice-covered exception IDs: **88**.

Uncovered source IDs: **39**.

Coverage ratio: **0.6929**.

P0/P1 uncovered: **0**.

Uncovered by priority:

- P2: 39

There are no hidden P0/P1 omissions. The remaining expansion backlog is deliberately lower-priority P2 material.

## Package shape

Generated runtime version:
`sha256-f9e11fa4416492d0e062`

Standalone T123 package:

- total T123 blocks: **10**;
- runtime-data blocks: **5**;
- largest T123 block: **34,757 bytes**.

Chromium preview: PASS.

## Safety

- Tilda unchanged.
- Live Exceptions page remains TEST/PREVIEW only.
- Current EGE Russian trainer unchanged.
- Current EGE Russian trainer scoring/answers/storage unchanged.
- Standalone storage namespace remains separate.
- PR remains draft/unmerged.
- Public rollout remains HOLD.

## Next recommended content work

Freeze 121 as the reviewed current checkpoint.

Select the next P2 wave from the remaining 39 source cases by course architecture and transfer value, not raw count.

Each future wave must repeat the same cycle:

source review -> Drabkina-style rule/table/algorithm -> original bidirectional/transfer contexts -> manual card review -> isolated candidate build -> runtime/T123/package/Chromium -> generated-payload inspection -> promotion.
