# RESULT-006 — Russian Drabkina class-route architecture

Date: 2026-08-12  
Branch: `agent/russian-exceptions-content-polish`  
Status: **PASS for architecture + current-127 routing inventory / FULL SCHOOL DENOMINATOR NOT READY**

## Fixed product decision

The Russian Difficult Cases / Exceptions system uses **one shared knowledge base** with separate learner routes:

- 5 class
- 6 class
- 7 class
- 8 class
- 9 class
- 10 class
- 11 class
- OGE
- EGE
- Whole base

A learner has one knowledge profile. Switching route does not duplicate or reset knowledge.

Topic is a separate filter and does not replace the selected route.

## Mandatory class-routing source

The 5–11 class split is based on the **Drabkina/Subbotin school vertical** in the project corpus.

Do not infer class from:

- EGE task number;
- current card source file;
- current trainer placement;
- intuition;
- project convenience.

Rosenthal is a completeness / difficult-case control, not the primary class router. Current academic/dictionary norm overrides outdated teaching formulations. Current FIPI scope is used for OGE/EGE overlays.

## Routing semantics

Two different concepts are now stored separately:

- `first_studied_class` — first verified school stage for the underlying knowledge;
- `route_classes` — all Drabkina class routes in which the item is actually taught, practised, repeated or systematized.

`reinforcement_classes` is the later-route subset after first study.

This matters especially for grades 10–11: later systematization belongs to the selected class route without creating a duplicate knowledge item.

The future class-mode denominator uses the **complete verified `route_classes` membership**, not only `first_studied_class`.

## Progress semantics

Cards/questions are evidence, not programme units.

Learner-facing progress must be relative to the selected mode. A small perfect session must not imply mastery of the whole route.

The future denominator is:

`mastered knowledge items in selected verified route / all knowledge items in selected verified route`

The internal mastery engine may additionally require independent retrieval, transfer and delayed retention.

No class/OGE/EGE/whole-base learner percentage is authorized yet.

## Verified current-127 routing checkpoint

Main workflow: `Russian Exceptions Course-Grade Gate`  
Run: `31639637314` / run number `141`  
Head: `31b8d67dd72c29e2a200ccc755f0e3ec95a275d8`  
Conclusion: **SUCCESS**  
Artifact: `9158341379`  
Digest: `sha256:3f1629acd9bdf1096a1b89dec4f37b5cdacbf7148b81821974c2b314951d2a55`

Current canonical source items: **127**.

### First-study counts

These are not class-mode denominators:

- grade 5: 15
- grade 6: 22
- grade 7: 43
- grade 8: 12
- grade 9: 6
- first-study stage not yet established: 29

### Overlapping current route membership

These are current-content route memberships, not full programme denominators:

- grade 5 route: 15
- grade 6 route: 26
- grade 7 route: 56
- grade 8 route: 16
- grade 9 route: 6
- grade 10 route: 81
- grade 11 route: 22

### Source evidence status

- candidate school-base items with a class route: **106**
- class-route source pending: **20**
- historical EGE-only record excluded from future school denominator: **1**

## Direct class-route resolutions in the current router

Grade 6 route now has direct Drabkina evidence for:

- СКАК-/СКОЧ- + СКАЧОК/СКАЧУ;
- ПЛАВ-/ПЛОВ- + ПЛОВЕЦ/ПЛОВЧИХА;
- ПЛЫВУНЫ family route (exact word occurrence still pending);
- ТВАР-/ТВОР- + УТВАРЬ;
- ЗАР-/ЗОР- family, while current learner norm remains **ЗАРЕВАТЬ** and obsolete **ЗОРЕВАТЬ** remains disabled;
- ПОМИДОРОВ as a direct grade-6 route item, with earlier first-study stage still pending.

Grade 7 route now has direct Drabkina evidence for:

- after-event ПО-constructions through error targets such as `по приезду` / `по завершению`;
- the feminine-past stress family through direct testing of `бралА`; exact occurrence of every member of the wider current cluster remains pending.

Grade 10 route has direct Drabkina evidence for:

- МИЛОСТИВЫЙ;
- ЮРОДИВЫЙ;
- ЗАСТРЕВАТЬ;
- ЗАТМЕВАТЬ;
- ПРОДЛЕВАТЬ.

For those grade-10 items, earlier first-study stage is still left null until established from the 5–9 vertical.

## Current unresolved 20

### Morphology / difficult forms

- `morph_doktor_plural`
- `morph_kupol_plural`
- `morph_polotentse_genitive_plural`
- `morph_polutorasta_oblique`
- `morph_povidlo_instrumental`
- `morph_vorota_genitive_plural`
- `verb_poezzhay_imperative`
- `verb_zapechatlet_infinitive`

### Paronyms / lexical norms

- `paronym_garantiynyy_garantirovannyy`
- `paronym_ledovyi_ledyanoi`
- `paronym_otborochnyi_otbornyi`
- `paronym_pamyatlivyi_pamyatnyi`
- `paronym_prazdnyi_prazdnichnyi`
- `paronym_priznatelnyi_priznannyi`
- `paronym_produktovyi_produktivnyi`

### Orthoepy

- `stress_otzyv_meaning_pair`

### Syntax / government

- `syntax_apposition_title_declension`
- `syntax_dative_prepositions_government`
- `syntax_homogeneous_different_government`
- `syntax_indirect_speech_person_shift`

These must remain unresolved until direct class-route evidence is established. EGE relevance alone is insufficient.

## Main-gate safety

The routing inventory is now part of the main course-grade gate.

The same verified run also passed:

- canonical 127 source build;
- current 121-card practice build;
- Wave 6 reviewed-content invariants;
- practice coverage 88/127 with P0/P1 uncovered = 0;
- runtime build;
- forbidden learner-source leakage gate;
- core browser validation;
- Chromium standalone preview validation;
- runtime size audit.

## Next source work

1. Resolve the remaining 20 current items only through direct Drabkina class-route evidence or leave them explicitly unassigned.
2. Complete the exact grade-8 project-practicum structure.
3. Itemize the full Drabkina 5–11 difficult-case / exception / contrast vertical beyond the current 127.
4. Deduplicate repeated grade-10/11 systematization from earlier knowledge units while preserving `route_classes` membership.
5. Run Rosenthal completeness control.
6. Run current-norm audit over the complete retained map.
7. Add current FIPI OGE/EGE route overlays.
8. Only after that compute learner-facing progress denominators.
9. Add new practice because the master map proves a gap, never to hit an arbitrary card count.

## Publication safety

No Tilda publication is authorized by this result.
Current EGE trainer remains unchanged.
Production integration remains HOLD.
