# TASK-004 — Russian Exceptions P0 transfer coverage wave

## Goal

Close the remaining high-priority practice gap revealed by the current 80-card coverage audit without disturbing the audited 80-card release candidate.

## Why this wave exists

Current course-grade 80-card bank is linguistically audited and machine/browser validated, but coverage audit still reports:

- 1 P0 exception with no practice: `paronym_priznatelnyi_priznannyi`;
- 11 P0 exceptions covered only by recognition/guided recall, with no `independent_context` or `transfer` evidence.

This is a coverage-quality gap, not a reason to invalidate the current 80 cards.

## Scope

Create a separate non-production Wave 5 candidate with original Eksamio contexts:

1. `paronym_priznatelnyi_priznannyi` — two contexts, one for each side of the pair;
2. `alt_root_skachok_skachu` — independent context;
3. `alt_root_zarevat_current` — current-norm context;
4. `morph_doktor_plural` — independent context;
5. `morph_pomidor_genitive_plural` — independent production context;
6. `morph_vorota_genitive_plural` — independent production context;
7. `n_nn_chewed` — contrast transfer to participial use;
8. `n_nn_glass` — rule/exception contrast;
9. `n_nn_tin` — rule/exception contrast;
10. `n_nn_wooden` — rule/exception contrast;
11. `syntax_dative_prepositions_government` — transfer from СОГЛАСНО to ВОПРЕКИ/БЛАГОДАРЯ;
12. `syntax_po_after_event_forms` — transfer from ПО ПРИЕЗДЕ to ПО ОКОНЧАНИИ/ПО ПРИБЫТИИ.

Total candidate cards: 13.

## Content contract

Every candidate card must:

- map to an already source-verified current exception_id;
- have an original learner-facing context;
- use `transfer_level = independent_context` or `transfer`;
- preserve the verified rule boundary;
- include a compact course-grade explanation, not a bare answer;
- avoid internal source labels in learner text;
- avoid inventing a broader universal rule from one example.

## Safety

- Do NOT add Wave 5 to manifest 119 yet.
- Do NOT change the current 80-card canonical/Tilda package.
- Do NOT update Tilda.
- Candidate must first pass source review, schema/build validation, coverage audit and Chromium preview in a separate candidate path.

## Acceptance

- 13/13 cards source-mapped and individually reviewed;
- candidate build has 93 active cards (80 current + 13 candidate) when tested separately;
- P0 uncovered count becomes 0 in candidate coverage;
- every previously listed P0 no-transfer exception has independent_context/transfer evidence;
- current 80-card production-hold manifest remains unchanged.
