# Eksamio — Current Project Priorities

**Status:** CURRENT PRODUCT / DELIVERY SNAPSHOT  
**Updated:** 2026-08-23  
**Baseline at update:** `63e916f86b1e024bb01cb879048b50cb9d1ccf30`

This file does not replace `00-PRODUCT-MASTERPLAN.md` or `OWNER-DECISIONS-2026-08-22.md`. The owner decision of 2026-08-23 sets a hard delivery deadline: **full paid `Eksamio Pro — Russian` launch by 2026-09-01**.

## 1. Product priority

Eksamio remains one **Personal Exam Intelligence System (PEIS)**.

Subject order remains:

1. Russian — subject #1, P0 and the only Full Subject launch target before 2026-09-01.
2. Mathematics — subject #2, P0 system subject, but non-launch-critical Full Subject acquisition is deferred until Russian source completeness.
3. Physics — subject #3, P1; bounded accepted-demo closure may finish but must not consume Russian launch-critical capacity.

Until September 1, priority is determined by contribution to the real paid Russian Pro launch, not by historical P0/P1 labels alone.

## 2. Primary milestone and critical path

Primary milestone:

`PAID_EKSAMIO_PRO_RUSSIAN_PRODUCTION_LAUNCHED_BY_2026_09_01`

The deadline does not weaken hard product/security/source/privacy gates. It changes scheduling: every new task must reduce one concrete launch blocker or be deferred.

Current launch-critical lanes are:

1. **Russian subject truth/content** — normative scope coverage, textbook/source ingestion, canonical identities/prerequisites, complete launch-relevant content bundles and subject acceptance.
2. **Russian PEIS connection** — move the merged 121-card mapping from integration-ready to real shared-PEIS evidence flow/end-to-end learning loop.
3. **Yandex deployment/security** — staging -> production candidate, private service/persistence, secrets, monitoring, rollback and Russia/no-VPN operation.
4. **Tutor** — provider-neutral/evaluation -> admitted text path -> realtime voice -> same-session continuity -> reliability/kill switch.
5. **Identity/session** — passwordless e-mail/phone and safe anonymous -> account continuity with server-owned canonical identity.
6. **Payments/entitlements** — real SBP/card paid path, NPD-compatible receipt, webhook idempotency, entitlement and refund/failure behavior.
7. **Product client** — separate Eksamio Pro web application with strong desktop/mobile-browser flow; Tilda remains public/free-demo layer.
8. **Legal/privacy/production acceptance** — required launch copy/controls, learner audio persisted = 0, final end-to-end production acceptance.

A task outside these lanes needs an explicit reason why it is still launch-critical before September 1.

## 3. Russian launch lane — immediate work

### RUSSIAN SOURCE / FULL SUBJECT

`FULL_SUBJECT_SCOPE_SOURCE_COMPLETE` is launch-blocking for a complete paid Russian subject offer.

Current active textbook/source step:

`RUSSIAN_TEXTBOOK_SELECTION_MATRIX`

Rules:

- official school-program authority defines scope skeleton;
- FIPI/OGE/EGE are assessment overlays, not the whole subject;
- selected textbooks are knowledge/pedagogy evidence;
- no batch textbook download before matrix approval;
- source PDFs belong in Source Archive, not product runtime;
- Google Drive may be Source Archive but Yandex runtime must work without Drive after ingestion;
- no persistent owner-local textbook folders unless explicitly requested.

### RUSSIAN 121-CARD MAPPING / PEIS CONNECTION

PR #112 was reviewed and merged on 2026-08-23 as merge commit `63e916f86b1e024bb01cb879048b50cb9d1ccf30`.

Accepted bounded result:

- 121 active unique cards;
- 116 EXACT;
- 5 PARTIAL_COMPOSITE;
- 121 integration-ready;
- 0 blocked;
- 0 live-connected at the mapping artifact layer;
- exactly 12 previously admitted new canonical `ru-*` identities in that reconciliation wave;
- 185 canonical school identities preserved;
- Russian demos/Tilda/shared PEIS contracts unchanged by the landing.

The mapping-landing blocker is CLOSED. Do not reopen the broad RU-1 reconciliation.

**Next launch-critical action:** production-shaped Russian shared-PEIS connection using the already merged PEIS integration/service-bridge/browser-hook/trusted-host/substrate contracts. Move real Russian learner attempts through server-owned evidence/persistence/recompute/NBA while preserving current scoring/local fallback and source truth. Do not stop at `integration_ready`.

## 4. Central platform lane

The portable PostgreSQL/container substrate has passed and is merged.

Next platform milestone is real Yandex staging and then production-candidate admission. Public traffic remains OFF until security/identity gates pass.

Required production invariants include:

- private runtime behind controlled API edge;
- Managed PostgreSQL or admitted production persistence;
- secrets outside Git/client/logs;
- server-owned learner identity;
- kill switches and fail-safe behavior;
- monitoring/rollback;
- Google Drive/source archive not on production hot path;
- deterministic/base product survives Tutor/provider/source-archive outage.

## 5. Tutor lane

Merged foundations:

- provider-neutral Tutor boundary;
- reliability gateway;
- transient-failure circuit repair;
- bounded real OpenAI sandbox authority.

Active/next execution must produce repo-visible results, not only design notes:

- real-provider sandbox evidence;
- provider-neutral evaluation harness;
- production-eligible conversational provider admission for Russia/no-VPN contour;
- grounded Russian text Tutor vertical slice;
- realtime speech path with learner audio persistence = 0;
- `voice -> text -> voice` same-session continuity;
- independent verification and exactly-once PEIS evidence behavior;
- provider failure/fallback/kill switch.

The first paid Pro launch remains forbidden if either text or realtime voice Tutor is not production-ready.

## 6. Identity / payment / client lanes

These are now immediate launch dependencies, not later backlog items.

### Identity

- passwordless verified e-mail or phone;
- browser is not canonical identity authority;
- anonymous free-demo evidence can be safely linked to permanent account;
- session/privacy/retention behavior tested.

### Payments

First candidate remains `Robokassa + Robocheki SMZ` for the self-employed/NPD contour, subject to production acceptance.

Launch requires real:

- SBP and bank-card flow;
- legal receipt behavior;
- no mandatory card saving/autocharging;
- webhook replay/idempotency;
- entitlement grant;
- refund/failure/retry handling.

### Product client

- separate Pro web app;
- desktop + mobile-browser acceptance;
- demos remain anonymously usable through public layer;
- Pro sections may be previewed/locked according to product authority;
- no accounts/payments/PEIS/Tutor authority inside Tilda.

## 7. Deferred until after Russian launch unless directly blocking it

Normally defer before September 1:

- Mathematics Full Subject acquisition/ingestion;
- Physics Full Subject acquisition/ingestion;
- broad historical demo re-audits;
- speculative infrastructure/framework work;
- nonessential dashboard/report polish;
- later vision/photo/multimodal features;
- cross-subject expansion;
- refactors without launch evidence;
- new governance documents when existing authority can be updated instead.

## 8. Mandatory task admission test through September 1

Every significant task must state:

- `WHY_NOW`;
- `SEP1_LAUNCH_BLOCKER` — exact launch blocker reduced;
- `BASELINE_MAIN_SHA`;
- `DEPENDENCY_IN`;
- `MINIMAL_DELTA`;
- `EXPECTED_UNLOCK`;
- `EXECUTOR`;
- `ALLOWED_PATHS` / `FORBIDDEN_PATHS`;
- `ACCEPTANCE_EVIDENCE`;
- `STOP_CONDITIONS`;
- bounded `FINAL_STATUS`.

If a task cannot name the September 1 launch blocker it reduces, defer it.

Use existing working infrastructure and contracts. Do not turn a bounded launch task into a new architecture project.

## 9. Parallel execution rule

Launch-critical independent lanes may run in parallel when they do not conflict:

- Russian source/content;
- Russian mapping/PEIS integration;
- Yandex deployment/security;
- Tutor;
- identity;
- payments;
- client/legal acceptance.

This parallelism uses cloud isolation + GitHub branches/PRs. It must not create persistent owner-local clones/worktrees/folders without explicit owner permission.

## 10. Delivery rule

Until paid Russian Pro is live, choose work by:

`Sep 1 blocker -> smallest executable delta -> evidence -> accept/repair -> next blocker`.

Avoid:

`new paper -> re-audit -> process document -> another paper`.

A repository document is justified only when it is necessary authority for executable work or records a material owner decision. The default next action is implementation, testing, integration or production acceptance.