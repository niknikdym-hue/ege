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

A learner has one knowledge profile. Switching route does not duplicate or reset knowledge. Topic is a separate filter.

## Mandatory class-routing source

The 5–11 class split is based on the **Drabkina/Subbotin school vertical** in the project corpus.

Do not infer class from EGE task number, current card location, intuition or project convenience.

Rosenthal is a completeness / difficult-case control, not the primary class router. Current academic/dictionary norm overrides outdated teaching formulations. Current FIPI scope is used for OGE/EGE overlays.

## Routing semantics

- `first_studied_class` — first verified school stage for the underlying knowledge.
- `route_classes` — all Drabkina class routes in which the item is taught, practised, repeated or systematized.
- `reinforcement_classes` — later-route subset after first study.

The future class-mode denominator uses the **complete verified `route_classes` membership**, not only `first_studied_class`.

Cards/questions are evidence, not programme units. No class/OGE/EGE/whole-base learner percentage is authorized yet.

## Latest verified current-127 checkpoint

Main workflow: `Russian Exceptions Course-Grade Gate`  
Run: `31640423806` / run number `151`  
Head: `81a070343963a77a55335458b3c84f3ae935cdab`  
Conclusion: **SUCCESS**  
Artifact: `9158630555`  
Digest: `sha256:bc35f6610407bb7336a21399791ef558464ecc521d4e7dda4fc85a301825a0b5`

Current canonical source items: **127**.  
Current learner practice cards: **121** — separate metric.

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
- grade 10 route: 82
- grade 11 route: 24

### Source evidence status

- candidate school-base items with a class route: **108**
- class-route source pending: **18**
- historical EGE-only record excluded from future school denominator: **1**

## Direct Drabkina route resolutions now present

Grade 6 route:

- СКАК-/СКОЧ- + СКАЧОК/СКАЧУ;
- ПЛАВ-/ПЛОВ- + ПЛОВЕЦ/ПЛОВЧИХА;
- ПЛЫВУНЫ family route, exact word occurrence still pending;
- ТВАР-/ТВОР- + УТВАРЬ;
- ЗАР-/ЗОР- family, while current learner norm remains **ЗАРЕВАТЬ** and obsolete **ЗОРЕВАТЬ** remains disabled;
- ПОМИДОРОВ as direct grade-6 route material, earlier first-study stage still pending.

Grade 7 route:

- after-event ПО-constructions through direct error targets such as `по приезду` / `по завершению`;
- feminine-past stress family through direct testing of `бралА`.

Grade 10 route:

- МИЛОСТИВЫЙ / ЮРОДИВЫЙ;
- ЗАСТРЕВАТЬ / ЗАТМЕВАТЬ / ПРОДЛЕВАТЬ;
- title/apposition declension: Drabkina directly diagnoses `В пьесе «Грозе»...` as an error in a construction with an uncoordinated apposition.

Grade 11 route:

- СОГЛАСНО / ВОПРЕКИ / БЛАГОДАРЯ government norms;
- after-event ПО-constructions as repeated government training.

## Current unresolved 18

Morphology / difficult forms:

- `morph_doktor_plural`
- `morph_kupol_plural`
- `morph_polotentse_genitive_plural`
- `morph_polutorasta_oblique`
- `morph_povidlo_instrumental`
- `morph_vorota_genitive_plural`
- `verb_poezzhay_imperative`
- `verb_zapechatlet_infinitive`

Paronyms / lexical norms:

- `paronym_garantiynyy_garantirovannyy`
- `paronym_ledovyi_ledyanoi`
- `paronym_otborochnyi_otbornyi`
- `paronym_pamyatlivyi_pamyatnyi`
- `paronym_prazdnyi_prazdnichnyi`
- `paronym_priznatelnyi_priznannyi`
- `paronym_produktovyi_produktivnyi`

Orthoepy:

- `stress_otzyv_meaning_pair`

Syntax:

- `syntax_homogeneous_different_government`
- `syntax_indirect_speech_person_shift`

These remain unresolved until direct class-route evidence is established. EGE relevance alone is insufficient.

## Main-gate safety

The main gate now runs `build/build_russian_drabkina_class_routing_current.py` and the same run also passed:

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

1. Resolve the remaining 18 only through direct Drabkina class-route evidence or leave them explicitly unassigned.
2. Complete the exact grade-8 project-practicum structure.
3. Itemize the full Drabkina 5–11 difficult-case / exception / contrast vertical beyond the current 127.
4. Deduplicate repeated grade-10/11 systematization from earlier knowledge units while preserving `route_classes` membership.
5. Run Rosenthal completeness control and current-norm audit.
6. Add current FIPI OGE/EGE route overlays.
7. Only after that compute learner-facing progress denominators.
8. Add new practice because the master map proves a gap, never to hit an arbitrary card count.

## Publication safety

No Tilda publication is authorized by this result.
Current EGE trainer remains unchanged.
Production integration remains HOLD.
