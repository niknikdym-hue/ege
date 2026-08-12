# TASK-007 — Russian Exceptions Wave 8: ПРЕ-/ПРИ- lexical pairs

Date: 2026-08-12

## Goal

Build the next coherent P2 course module from six uncovered lexical pairs where spelling changes with lexical meaning.

Theme:
**ПРЕ-/ПРИ-: сначала значение конкретного слова, а не механический выбор приставки.**

Current reviewed 133-card bank remains frozen while Wave 8 is developed separately.

## Target uncovered source IDs

1. `pre_pri_predel_pridel`
2. `pre_pri_predat_pridat`
3. `pre_pri_prekhod_prikhod`
4. `pre_pri_preemnik_priemnik`
5. `pre_pri_prestupit_pristupit`
6. `pre_pri_pretvorit_pritvorit`

Related already-covered scaffold:
`pre_pri_prebyvat_pribyvat`.

The generic `pre_pri_vocabulary_group` is intentionally excluded from this wave and must be audited as a separate dictionary-oriented unit later.

## Planned size

12 cards — exactly two directions per lexical pair.

Each pair receives:
- one context requiring the ПРЕ-/lexical form;
- one independent context requiring the ПРИ-/lexical form;
- both meanings explained explicitly;
- at least one independent_context/transfer item.

## Course architecture

Do not teach these six pairs by the generic school slogans «ПРЕ = очень» / «ПРИ = приближение».
Those broad prefix meanings do not reliably derive these lexicalized contrasts.

Course table:

PAIR | MEANING A | NORMAL COLLOCATIONS | MEANING B | NORMAL COLLOCATIONS | TRAP

Core pairs:
- ПРЕДЕЛ — boundary / ПРИДЕЛ — side chapel or additional church section;
- ПРЕДАТЬ — betray/hand over / ПРИДАТЬ — give/add a property, form, importance;
- ПРЕХОДЯЩИЙ — temporary/transient / ПРИХОДЯЩИЙ — one who comes/arrives, non-resident/visiting in context;
- ПРЕЕМНИК — successor/continuator / ПРИЁМНИК — receiver/device or receiving person/object by lexical meaning;
- ПРЕСТУПИТЬ — violate/cross a norm or law / ПРИСТУПИТЬ — begin/start doing something;
- ПРЕТВОРИТЬ — put an idea/plan into practice / ПРИТВОРИТЬ — close partly; also lexical family ПРИТВОРИТЬСЯ = pretend.

## Method baseline

Drabkina/Subbotin:
lexical table -> meaning question -> normal collocation -> contrast -> trap -> independent context.

Normative basis:
- `35-RUSSIAN-EXCEPTIONS-ROOTS-PREFIXES-v0.1.json`;
- linked PRE/PRI explanation unit in `34-RUSSIAN-EXPLANATION-ORTHOGRAPHY-9-10-v0.1.json`;
- project Rosenthal orthography contrast chain;
- current dictionary/Gramota cross-check for lexical meanings/collocations.

## Safety

- Do not add Wave 8 to current manifest 119 during drafting.
- Current 133 must stay independently PASS.
- Do not update Tilda.
- Every card requires manual review before promotion.
- No learner-facing internal provenance.

## Acceptance before promotion

- source gate PASS 6/6;
- 12/12 cards manually reviewed;
- exactly two directions per pair;
- candidate current 133 + Wave 8 = 145 cards;
- candidate schema/source-mode/ID checks PASS;
- source coverage gains all six target IDs;
- learner runtime/source-leak/T123/package/Chromium PASS;
- generated candidate payload manually inspected;
- current 133 remains independently PASS;
- Tilda unchanged.
