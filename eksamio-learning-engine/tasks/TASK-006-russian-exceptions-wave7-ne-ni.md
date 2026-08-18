# TASK-006 — Russian Exceptions Wave 7: НЕ / НИ through meaning and construction

Date: 2026-08-12

## Goal

Build the next coherent P2 course module from the remaining uncovered source items.

Theme:
**НЕ / НИ: сначала значение и структура предложения, потом частица.**

Current reviewed 121-card bank remains frozen while Wave 7 is developed separately.

## Target uncovered source IDs

1. `ne_chto_inoe_vs_nichto_inoe`
2. `ni_odin_vs_ne_odin`
3. `ni_razu_vs_ne_raz`
4. `ni_s_chem_ni_pri_chem`
5. `ni_fixed_turnovers`

Related already-covered contrast used as course scaffold:
`ne_kto_inoi_vs_nikto_inoi`

## Planned practice size

12 cards.

- НЕ ЧТО ИНОЕ, КАК / НИЧТО ИНОЕ НЕ — 2 directions;
- НИ ОДИН / НЕ ОДИН — 2 directions;
- НИ РАЗУ / НЕ РАЗ — 2 directions;
- НИ С ЧЕМ / НИ ПРИ ЧЁМ — 2 independent phrase contexts;
- fixed НИ turns — 4 cards across different phrase models.

## Course teaching architecture

### Table A — positive comparison vs negative sentence

- НЕ КТО ИНОЙ, КАК / НЕ ЧТО ИНОЕ, КАК;
- НИКТО ИНОЙ НЕ / НИЧТО ИНОЕ НЕ.

Diagnostic:
- first group is an affirmative identification/comparison and often contains КАК;
- second group belongs to a genuinely negative sentence with negative pronoun + negative predicate.

### Table B — one/once contrasts

- НИ ОДИН = nobody/not a single one in negative construction;
- НЕ ОДИН = more than one / many;
- НИ РАЗУ = never, not once;
- НЕ РАЗ = more than once, repeatedly.

Do not choose by sound; determine the actual quantity/negation meaning.

### Table C — preposition inside negative pronoun constructions

- ни с чем;
- ни при чём.

The preposition separates the parts of the negative pronoun construction.

### Table D — stable НИ turns

Use exact lexicalized forms and teach the phrase as a whole:
- во что бы то ни стало;
- как ни в чём не бывало;
- откуда ни возьмись;
- ни рыба ни мясо;
- ни жив ни мёртв;
- ни дать ни взять.

Do not invent a single universal syntactic rule that allegedly derives every fixed phrase.

## Method baseline

Drabkina/Subbotin:
rule/table -> diagnostic question -> exact application -> contrast -> trap -> independent context.

Normative basis:
- `39-RUSSIAN-EXCEPTIONS-NE-NI-SOLID-v0.1.json`;
- `85-RUSSIAN-EXCEPTIONS-NE-NI-HIGH-RISK-v0.1.json`;
- linked project Rosenthal НЕ/НИ rules;
- current dictionary/academic cross-check where a fixed phrase boundary needs confirmation.

## Safety

- Do not add Wave 7 to current manifest 119 while drafting.
- Do not change current 121 runtime/package.
- Do not update Tilda.
- Manual review is required for every new card before promotion.
- No learner-facing source labels.

## Acceptance before promotion

- source gate PASS 5/5 uncovered IDs;
- 12/12 cards manually reviewed;
- all four contrast directions correctly represented;
- fixed НИ turns use exact normative forms;
- candidate active count = 133 (121 current + 12 Wave 7);
- candidate build/schema/source-mode checks PASS;
- learner source-leak check PASS;
- candidate T123/package/Chromium PASS;
- generated candidate payload manually inspected;
- current 121 remains independently PASS;
- Tilda remains unchanged.
