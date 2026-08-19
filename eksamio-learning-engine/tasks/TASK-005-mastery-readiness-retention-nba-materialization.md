# TASK-005 — Mastery Confidence + Readiness + Retention + Next Best Action Materialization

TASK_ID: TASK-005
STATUS: READY
MODE: ADD_ONLY / ARCHITECTURE_MATERIALIZATION / NO_PRODUCTION_INTEGRATION
SCOPE: Materialize versioned mastery inference, prerequisite/readiness, retention and Next Best Action contracts after TASK-004 generalized learner evidence/state schemas are reviewed and merged.

ACTIVATION_GATE: SATISFIED
TASK-004 PR #33 is reviewed, approved and merged into `main`.
TASK-004 merge commit: `cc2d3e255c18b7935a2941f81dec0dc0306afbbf`.
Merged TASK-004 artifacts `277...280` and `results/RESULT-004...` are present on `main`.

## Read first

1. `../AGENTS.md`
2. `../00-WORK-STATUS.txt`
3. `../00A-WORK-STATUS-CURRENT-ADDENDUM.txt`
4. `../COMMUNICATION-PROTOCOL.md`
5. `../02-CODEX-BUILD-INDEX.txt`
6. `../276-EKSAMIO-LEARNER-EVIDENCE-STATE-CONTRACT-v1.0.txt`
7. `../281-EKSAMIO-MASTERY-READINESS-RETENTION-NBA-CONTRACT-v1.0.txt`
8. merged TASK-004 artifacts `277...280` and `results/RESULT-004...` on `main`.

Also use current semantic registry/crosswalk authorities and Tutor Core contracts.

If an older status/index line still names TASK-004 as current, treat this explicit TASK-005 activation record and the merged `main` state as authoritative for this task. Do not rewrite unrelated parallel Russian-program work merely to normalize historical status text.

## Goal

Produce machine-readable, versioned, subject-agnostic contracts for:

1. mastery estimate + inference confidence/uncertainty;
2. source-backed prerequisite/readiness state;
3. retention schedule/state;
4. Next Best Action recommendation + outcome logging;
5. deterministic validation/scenario fixtures.

Do not choose opaque arbitrary coefficients merely to make the schemas look complete.

## Allowed outputs

Create ADD-ONLY artifacts:

- `../282-EKSAMIO-MASTERY-INFERENCE-CONTRACT-v0.1.json`
- `../283-EKSAMIO-PREREQUISITE-READINESS-CONTRACT-v0.1.json`
- `../284-EKSAMIO-RETENTION-SCHEDULE-STATE-CONTRACT-v0.1.json`
- `../285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json`
- `../286-EKSAMIO-MASTERY-READINESS-RETENTION-NBA-VALIDATION.txt`
- `../results/RESULT-005-mastery-readiness-retention-nba-materialization.md`

A narrow validator/tests may be added under `../build/` if required.

## 282 — Mastery inference requirements

Represent separately:
- mastery estimate/band/status;
- system confidence/uncertainty;
- supporting evidence features;
- independent vs assisted evidence summaries;
- transfer evidence;
- retention evidence;
- contradictory evidence;
- inference version;
- semantic registry version;
- evidence watermark/reference;
- computed_at.

Do not equate mastery with raw percent correct or a product `mastered` flag.

Do not merge learner self-confidence with system inference confidence.

No final coefficient table is required unless justified by an explicit deterministic MVP policy. If an MVP rule is supplied, label/version it as provisional and transparent.

## 283 — Prerequisite/readiness requirements

Prerequisite relations must support at least:
- `REQUIRED`;
- `RECOMMENDED`;
- `SUPPORTS`.

Each edge must have:
- source semantic ID;
- target semantic ID;
- relation type;
- provenance;
- graph version;
- review status;
- optional conditional scope.

Do not infer prerequisite from course ordering alone.
Do not let AI invent edges.

Readiness must distinguish at least:
- ready to learn/practice;
- blocked by required prerequisite;
- insufficient evidence;
- needs verification due to stale/contradictory state;
- already strong/not current priority where useful.

## 284 — Retention requirements

Represent:
- current retention state;
- last delayed check;
- due/overdue window;
- previous retention successes/failures;
- schedule policy version;
- source evidence references;
- next due calculation inputs/reason codes.

Same-session repetition is not delayed retention.
Do not claim one universal forgetting curve.

A retention failure adds evidence and triggers reinference; it does not erase history.

## 285 — NBA requirements

Support recommendation candidate/action types such as:
- diagnose target;
- verify uncertain state;
- learn prerequisite;
- explain concept/rule;
- guided practice;
- independent practice;
- transfer check;
- retention review;
- exam control/demo recheck;
- homework follow-up;
- essay repair/rewrite;
- move to next target;
- stop/session complete.

Inputs may include:
- learner goal;
- exam/date context;
- mastery estimate;
- inference confidence;
- readiness;
- retention due;
- recent errors;
- assistance dependence;
- content availability;
- estimated duration;
- session time budget;
- exam relevance;
- prior recommendation outcomes.

Recommendation must contain structured reason codes supporting `WHY THIS NOW?`.

Do not optimize NBA primarily for engagement, chat length, clicks or voice minutes.

Recommendation outcome logging must support shown/accepted/skipped/completed/abandoned and subsequent independent/transfer/retention outcomes.

## Required scenarios / fixtures

Validate at least:

1. low mastery + high diagnostic confidence -> targeted learning/practice;
2. low mastery + required prerequisite gap -> prerequisite repair;
3. apparently strong but low-confidence/stale evidence -> verification;
4. assisted Tutor success -> independent verification required;
5. independent success without delayed evidence -> later retention review;
6. retention failure -> restabilization without deleting history;
7. conflicting evidence -> uncertainty increases / verification candidate;
8. high-value EGE gap under near exam date -> exam relevance affects priority, not semantic truth;
9. homework urgent goal with prerequisite gap;
10. mastered/retained target -> move to another useful target;
11. no meaningful next work -> stop/session complete;
12. cross-subject structural scenario for Mathematics or Physics without Russian-only core fields.

## Validation requirements

Report at minimum:
- JSON/schema validity;
- version fields present;
- mastery estimate and inference confidence separate;
- learner self-confidence not used as system confidence;
- assisted vs independent evidence separation;
- prerequisite edges require provenance/review/version;
- no course-order-as-prerequisite shortcut;
- no AI-guessed prerequisite truth;
- same-session repetition not retention;
- retention policy versioned;
- NBA reason codes present;
- NBA policy version/watermark present;
- recommendation outcome logging present;
- educational-value objective explicit;
- no engagement-first objective;
- cross-subject core validation;
- no production changes.

## Forbidden

Do NOT:
- change production demos/trainers/Tilda/runtime/scoring/localStorage;
- invent prerequisite relations;
- invent psychometric precision;
- declare universal forgetting constants as scientific truth;
- let AI directly write canonical mastery/readiness/NBA truth;
- implement payment/auth/runtime infrastructure;
- add vector DB/Kafka/Kubernetes;
- rewrite current Russian course/trainer state;
- overwrite or normalize unrelated files changed by parallel Russian-program work.

## Required result

Create `../results/RESULT-005-mastery-readiness-retention-nba-materialization.md` with:
- TASK_ID / STATUS;
- created/modified/deleted files;
- checks run;
- policy/schema versions;
- scenario results;
- unresolved decisions;
- cross-subject structural result;
- production files changed YES/NO;
- branch/commit/PR.

## Stop condition

STOP after the four machine-readable contracts, validation and RESULT-005 are complete.

Do not begin production runtime/service integration inside TASK-005.
