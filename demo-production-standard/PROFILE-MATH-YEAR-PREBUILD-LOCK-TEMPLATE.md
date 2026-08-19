# PROFILE MATH YYYY — PREBUILD LOCK TEMPLATE

Use one copy per year. Do not mark `READY_FOR_VERIFIED_BUILD` until every mandatory lock below is PASS from exact FIPI source of that year.

## A. SOURCE-LOCK.json
Required fields:
- exam / subject / level / year;
- exact demo/spec/codifier filenames;
- SHA-256 + bytes of each PDF;
- physical pages;
- printed pages;
- physical → printed page/half map;
- source authority = FIPI exact year;
- source anomalies.

## B. EXAM-LOCK.json
Required fields:
- task_count;
- short_task_range;
- extended_task_range;
- duration_minutes;
- max_primary_score;
- per_task_max_score;
- reference materials;
- allowed equipment;
- official_example_count;
- examples_per_task;
- variant_source_pages for every official example;
- answer/solution/criteria source pages.

All values must be proven from current-year demo/spec, never copied from a neighboring year.

## C. ANSWER-LOCK.json
For every short official example:
- task / variant;
- exact official accepted answer(s);
- normalization rules;
- alternatives explicitly allowed by FIPI;
- independently checked answer status where mathematically feasible;
- source page/evidence.

## D. INPUT-CONTRACT.json
For every short official example:
- required learner action;
- actual control type;
- allowed characters;
- comma/dot/minus/plus/fractions/spaces rules;
- paste behavior;
- empty/partial state;
- canonicalization permitted by UI;
- invalid input behavior.

No universal sanitizer may silently turn a wrong answer into a correct one.

## E. EXTENDED-CRITERIA-MAP.json
For every extended official example:
- task / variant;
- task max score;
- condition page;
- official solution/answer page(s);
- criteria page(s);
- source asset IDs;
- self-evaluation score buttons/range;
- own-answer/result display requirement;
- math-toolbar requirement.

## F. VISUAL-INVENTORY.json
For every required visual/source crop:
- asset ID;
- task / variant / semantic role;
- exact source file + SHA-256;
- printed page;
- representation = direct source crop/full source render;
- must_include;
- must_exclude;
- four-edge audit requirement;
- desktop/mobile target;
- zoom requirement.

Final crop rectangle is determined only from the exact current-year source. Never copy crop coordinates from another year.

## G. AUDIT-MATRIX.csv
One row per official example. Minimum gates:
- source/text/typography;
- formula;
- visual source;
- visual UI crop;
- required/actual control;
- interaction;
- answer/criteria;
- scorer/self-evaluation;
- state/reload;
- result.

## H. BUILD ADMISSION
`READY_FOR_VERIFIED_BUILD = YES` only when:
- SOURCE LOCK PASS;
- EXAM LOCK PASS;
- ANSWER LOCK PASS for every short example;
- INPUT CONTRACT PASS for every short example;
- EXTENDED CRITERIA MAP PASS for every extended example;
- VISUAL PREBUILD INVENTORY PASS;
- no TODO/ASSUMED/UNVERIFIED.

## I. RELEASE ADMISSION
`READY_FOR_TILDA = YES` only after:
- all official variants implemented;
- direct-source visual fidelity PASS;
- per-asset crop/UI PASS;
- short correct+wrong real-DOM PASS;
- extended own-answer + official FIPI solution/criteria + self-evaluation PASS;
- state/reload/navigation/timer/results PASS;
- responsive 1280/768/390/360/320 PASS;
- zoom PASS;
- T123 atomic `<42500` + manifest + ordered paste PASS;
- frozen ZIP;
- full clean-extraction rerun PASS;
- independent final audit PASS.

`LIVE_GO` remains NO until publication + production smoke + manual student acceptance.
