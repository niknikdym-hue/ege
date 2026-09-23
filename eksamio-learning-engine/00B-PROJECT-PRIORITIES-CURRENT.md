# Eksamio — Current Project Priorities / Operational Launch Board

**Status:** CURRENT PRODUCT / DELIVERY AUTHORITY
**Updated:** 2026-09-02
**Baseline main:** `85d2f2b3dd0cf56c428f57c8a5c7d1b636ecebbb`
**Primary objective:** launch the first truthful paid Russian product as soon as its own bounded gates pass; launch full `Eksamio Pro — Russian` only after the full-subject gate is green.

This file is the single operational launch board for the current Russian launch. It supplements `00-PRODUCT-MASTERPLAN.md` v1.4 and approved owner decisions.

Its purpose is to prevent late surprises about product scope, missing learner surfaces, infrastructure, commercial dependencies or rollout stages. A launch-critical item must be present here. A new mandatory item may be added only when new owner, legal, security or production evidence genuinely creates a new gate; ordinary implementation detail does not expand launch scope.

## 1. One launch definition

The launch is not “content ready”, “Tutor ready”, “checkout ready” or “site ready” in isolation.

The **full Eksamio Pro Russian launch** is complete only when one exact production release proves:

`public entry -> identity -> purchase -> receipt -> entitlement -> Russian learning -> PEIS state -> practice -> Tutor text/voice -> independent verification -> persisted progress -> return login -> refund/revoke`

Primary dependency chain for full Pro:

`FULL_RUSSIAN_TRUTH -> WORKING_RUSSIAN_PRODUCT -> YANDEX_PRODUCTION -> REAL_IDENTITY -> REAL_PAYMENT -> REAL_TUTOR -> END_TO_END_ACCEPTANCE -> PUBLIC_GO_LIVE`

**Owner decision 2026-09-02:** this full-Pro chain does **not** prohibit a narrower free or paid Russian product from launching earlier. A bounded product may open before full-subject closure only when every subject claim and learner action exposed by that product is backed by accepted Russian authority and that product's own runtime/payment/privacy/Tutor gates pass. It must not imply that the complete Russian 5–11 + OGE + EGE product is ready.

Until the Russian commercial path is real, Mathematics, Physics, nonessential historical work, SourceCraft migration, visual polish and speculative platform work are deferred.

## 2. Status vocabulary — use only these meanings

- **ЕСТЬ** — merged/accepted capability exists for its current boundary; do not reopen without a concrete regression.
- **КОД ЕСТЬ — НУЖНО ПОДКЛЮЧИТЬ/ПРИНЯТЬ** — implementation exists, but real production provider, persistence, subject content, live backend or external acceptance is still missing.
- **НУЖНО СДЕЛАТЬ** — no durable production-capable implementation is proven in current `main`; it requires an implementation delta before the relevant rollout stage.
- **BLOCKED_SUBJECT** — blocked by exact Russian subject/content acceptance; credentials cannot cure it.
- **BLOCKED_EXTERNAL** — code boundary exists; real external/provider/operator evidence is missing.
- **LATER** — intentionally outside first public paid closed loop and must not delay it unless marketed as available.

A mock, sandbox or browser fixture is never renamed `ЕСТЬ В PRODUCTION`.

## 3. Product architecture — fixed

For the learner there is one Eksamio.

Technically:

- `eksamio.ru` / Tilda = public marketing + free-demo entry layer;
- protected Eksamio web application = account, Russian learning, PEIS, progress, entitlement and Tutor;
- primary Russian production runtime = **Yandex Cloud Russia**;
- canonical learner state, PEIS and entitlements are server-owned;
- GitHub is development/version-control infrastructure, not a runtime dependency;
- Google Drive may be a Source Archive, never a learner runtime dependency;
- provider/repository hosting remains replaceable.

Hard invariant: **GitHub outage != Eksamio outage**.

## 4. Russian program — one truth, many learner products

The full Russian program is one canonical knowledge/content layer. Course, EGE, OGE, school routes, trainers, constructor, Tutor and progress do not get separate ontologies or separate mastery databases.

All **16/16 Russian program modules** are part of the full-subject scope. The official denominator is already finite and accounted: `1325 / 1325` admission units and `1400 / 1400` official requirements. The remaining bottleneck is exact subject acceptance throughput, not discovery of what the program contains.

## 5. Learner product launch inventory

| Learner surface | Rollout | Current truth | Durable evidence | Remaining blocker / next executable action |
| --- | --- | --- | --- | --- |
| Public `eksamio.ru` entry | REQUIRED | **ЕСТЬ** | existing Tilda/public site and accepted demo surfaces | Preserve; expose only truthful currently admitted Russian products. |
| Free EGE Russian demos | FREE BASE | **ЕСТЬ** | accepted demo/scorer surfaces; protected by Russian closure gates | Keep anonymous and free; do not modify accepted exam truth. |
| Russian diagnostics | FIRST FREE PRODUCT EXPANSION | **НУЖНО PRODUCTIZATION** | accepted demos + PEIS/program contracts | Build `result -> errors -> weak skills -> next actions`; emit only conclusions supported by accepted semantic authority. |
| Protected Eksamio Pro shell | REQUIRED FOR PRO | **КОД ЕСТЬ — НУЖНО ПОДКЛЮЧИТЬ/ПРИНЯТЬ** | merged PR #142 + production runtime binding | Connect admitted real backend/TLS/CORS/session endpoints and rerun mobile/desktop E2E. |
| Full Russian program navigation / course shell | FULL PRO | **КОД ЕСТЬ — BLOCKED_SUBJECT** | PR #142 renders 5–11 + all 16 modules + OGE/EGE routes | Bind only subject-accepted content; do not market complete Russian until full subject gate is green. |
| Work on mistakes | REQUIRED CORE | **КОД ЕСТЬ — НУЖНО ПОДКЛЮЧИТЬ** | Pro-client vertical slice + PEIS contracts | Wire real failed-attempt -> exact skill -> practice/help -> verify handoff to server-owned PEIS. |
| Unified Russian trainer | FIRST FREE/PRODUCT CORE | **LEGACY PRODUCT EXISTS — REBUILD/REBIND** | existing trainer surfaces + reviewed Russian program/semantic mappings | Rebuild against the new Russian program/learning engine and accepted data; old learner data/content is not subject authority. |
| Thematic trainer modes | PROGRESSIVE FREE/PRO | **LEGACY MODES EXIST — REBIND REQUIRED** | ударения, словарные слова, паронимы, фразеологизмы surfaces | Reuse only after exact check/rebinding to accepted semantics; keep one PEIS/knowledge model. |
| Trainer constructor | PRODUCT CORE | **LEGACY PRODUCT EXISTS — REBUILD/REBIND** | owner-confirmed current/legacy trainer+constructor surface | Rebuild as a mode of the unified trainer over admitted topics/task families/item pool; do not preserve old data merely because it exists. |
| EGE Russian trainer / route | COMMERCIAL EXAM ROUTE | **КОД/ROUTE ЕСТЬ — BLOCKED_SUBJECT FOR FULL CLAIM** | Pro client + reviewed EGE/demo/trainer authority | Progressive bounded exposure is allowed only for accepted scope; full EGE route requires marketed-scope acceptance. |
| OGE Russian trainer / route | PROGRESSIVE | **SHELL/ROUTE ЕСТЬ — BLOCKED_SUBJECT FOR FULL CLAIM** | Pro client + PR #164 + owner decision issue #180 | Build the new unified OGE route; do not salvage old `zadanie-1…8` prototype pages. |
| School Russian 5–11 views | FULL PRO / LATER EXPANSION | **SHELL ЕСТЬ — BLOCKED_SUBJECT** | PR #142 + full-subject 16-module model | Open grade/topic views only over accepted full-school content. |
| Personal “Training for today” / NBA | PRO CORE | **КОД/CONTRACTS ЕСТЬ — НУЖНО ПОДКЛЮЧИТЬ** | PEIS NBA contracts + PR #142 progress/NBA shell | Connect real server-owned learner evidence, retention risk and exam value to generated next action. |
| Russian guided course / learning route | FULL PRO, PROGRESSIVELY FILLED | **SHELL ЕСТЬ — BLOCKED_SUBJECT** | PR #142 program shell | Materialize accepted teach/practice/verify content and prerequisite traversal from full program. |
| Progress / weak-points / readiness | PRODUCT CORE | **КОД ЕСТЬ — НУЖНО ПОДКЛЮЧИТЬ** | PR #142 progress/NBA surface + shared PEIS contracts | Replace fixture state with real persistence/recompute and cross-session proof. |
| Independent verification after help | PRODUCT CORE | **КОД/CONTRACT ЕСТЬ — НУЖНО LIVE E2E** | shared PEIS/Tutor policy and merged Tutor slice | Prove exactly-once independent evidence after substantial Tutor help. |
| Retention / spaced recheck | PRODUCT CORE | **КОД/CONTRACT ЕСТЬ — НУЖНО LIVE E2E** | shared retention contracts | Persist schedule/state and prove later recheck changes retained mastery correctly. |
| Tutor text | AI ANALYSIS + PRO | **КОД ЕСТЬ — НУЖНО PRODUCTION INTEGRATION** | merged grounded Tutor slice | Admit selected brain/provider path and prove grounded error analysis, latency/reliability and PEIS continuity. |
| Tutor realtime voice | FULL PRO | **КОД ЕСТЬ — НУЖНО PRODUCTION INTEGRATION** | SpeechKit adapters + accepted voice profile | Finish production streaming/continuity/reliability; audio persistence exactly 0. |
| Trainer/course Tutor handoff | FULL PRO | **КОДОВЫЕ ОСНОВЫ ЕСТЬ — НУЖНО E2E** | shared Tutor + PEIS boundaries | One learning episode must preserve goal/evidence when moving trainer -> Tutor -> verify. |
| Essay / extended-answer AI support | LATER | **LATER** | architecture authority only for gated expansion | Add only after rubric/source/eval gate; do not market before acceptance. |
| Parent/reporting surfaces | LATER | **LATER** | product authority | Implement under separate privacy/access rules after the core commercial path. |
| Vision/photo/richer multimodal | LATER | **LATER** | masterplan | Explicitly deferred. |

### Product-scope rule

Full Russian **subject truth** is mandatory for any claim that Eksamio offers the complete Russian subject. Specialized learner surfaces may be released progressively after their own subject/UI/runtime gates without rebuilding the subject.

If a progressive surface is not ready, it is hidden or described as unavailable; it does not silently expand the first-release blocker list.

### Owner decision — 2026-09-02: Russian product launch sequencing

Do **not** wait for all `1325 / 1400` subject objects to become accepted before rebuilding the learner product. Subject closure and product assembly now proceed in parallel.

Launch order:

1. **FREE RUSSIAN CONTOUR**
   - keep the accepted EGE Russian demos live and free;
   - rebuild the unified Russian trainer + constructor against the new Russian program/learning engine;
   - expose only accepted/verified content and semantics;
   - progressively rebind useful thematic modes (ударения, словарные слова, паронимы, фразеологизмы) instead of treating their old data as authority.
2. **RUSSIAN DIAGNOSTICS**
   - product result must be `result -> errors -> weak skills -> next actions`;
   - no weak-skill/mastery claim may be emitted from an unaccepted semantic mapping;
   - diagnostics is a primary free entry into the commercial funnel.
3. **FIRST PAID PRODUCT — PERSONAL RUSSIAN AI ANALYSIS**
   - detailed bounded error analysis;
   - grounded explanations;
   - weak-skill map and priorities;
   - concrete preparation plan;
   - next exercises/actions;
   - grounded Tutor follow-up on the learner's own mistakes;
   - may launch before full Pro only after its exact subject boundary plus identity/payment/receipt/privacy/Tutor/runtime E2E are proven.
4. **FULL PAID EKSAMIO PRO — RUSSIAN**
   - full 5–11 + OGE + EGE claim remains fail-closed;
   - launch only after the full Russian subject/content gate is green and full production E2E passes.

Do not prematurely market a complete OGE course, complete EGE course, “Tutor knows all Russian 5–11”, or a complete adaptive route across the entire subject before the corresponding subject gate is green.

The free contour, diagnostics, AI analysis and later Pro are **surfaces over the same Russian program, learning engine, PEIS and Tutor**. They must not become independent content databases or separate products with divergent semantic truth.

### Owner decision — OGE legacy surfaces

Issue #180 is the execution authority for the old OGE prototype pages. Keep only `/oge/`, `/oge/russkiy/` and `/oge/russkiy/konstruktor-variantov/` as Tilda/product entry surfaces. The old `/oge/russkiy/zadanie-1/` … `/zadanie-8/` pages are unpublished/archived and must not be audited, repaired or salvaged into the new product. Old URLs should permanently redirect to the intentional unified replacement route. Individual OGE task numbers later become modes/deep-links inside the unified trainer/runtime, not eight standalone Tilda product pages.

## 6. Commercial / account launch inventory

| Capability | Rollout | Current truth | Evidence | Remaining blocker / next action |
| --- | --- | --- | --- | --- |
| Passwordless account core | REQUIRED | **ЕСТЬ КАК КОД** | merged identity core | Connect real delivery and production persistence. |
| Yandex Postbox e-mail delivery | REQUIRED | **КОД ЕСТЬ — BLOCKED_EXTERNAL** | merged PR #148 | Verify sender/domain, IAM/service-account role and bounded real delivery smoke. |
| SMS.RU phone delivery | REQUIRED while phone login is offered | **КОД ЕСТЬ — BLOCKED_EXTERNAL** | merged PR #148 | Configure real account/API credential/sender and bounded real SMS smoke; otherwise do not advertise phone login. |
| Anonymous demo -> account continuity | REQUIRED | **КОД ЕСТЬ — НУЖНО PRODUCTION E2E** | identity/Pro-client contracts | Prove safe link to server-owned identity without duplicate/lost learner evidence. |
| Personal Russian AI analysis | **FIRST PAID NARROW PRODUCT** | **OWNER PRODUCT DECISION — НУЖНО PRODUCTIZATION** | owner decision 2026-09-02 + existing AI/Tutor/payment architecture | Define exact SKU/price/quota/entitlement and accepted analysis boundary; prove real payment -> receipt -> access -> grounded analysis -> follow-up -> refund/revoke. It must not claim full-subject Pro. |
| Pro offer / SKU contract | FULL PRO | **НУЖНО ДОКОНЦА МАТЕРИАЛИЗОВАТЬ** | payment/entitlement architecture exists | Persist exact launch SKUs, durations, prices, quotas and entitlement IDs before full-Pro checkout; do not invent prices in adapter code. |
| Pro 30-day access | FULL PRO COMMERCIAL | **OWNER PRODUCT DECISION — НУЖНО SKU** | existing product decision | Materialize server-owned SKU/price/entitlement; no auto-renewal. |
| Pro 90-day access | FULL PRO COMMERCIAL | **OWNER PRODUCT DECISION — НУЖНО SKU** | existing product decision | Materialize server-owned SKU/price/entitlement; 90-day daily value may be better; no auto-renewal. |
| AI-analysis credit toward Pro | COMMERCIAL RULE TO MATERIALIZE | **OWNER PRODUCT DECISION — НУЖНО SERVER CONTRACT** | existing product decision | When AI analysis is enabled, encode the approved credit-to-Pro window/amount server-side; never infer it client-side. |
| Robokassa initiation | REQUIRED FOR PAID PRODUCT | **КОД ЕСТЬ — BLOCKED_EXTERNAL** | merged PR #147 | Actual merchant settings/credentials + bounded real SBP/card acceptance. |
| NPD receipt / Robocheki SMZ | REQUIRED FOR PAID PRODUCT | **КОД ЕСТЬ — BLOCKED_EXTERNAL/LEGAL** | PR #147 candidate | Accept fiscal/legal configuration and prove real receipt lifecycle. |
| Exactly-once entitlement grant | REQUIRED FOR PAID PRODUCT | **КОД ЕСТЬ — НУЖНО REAL E2E** | payment core / E2E harness | Prove provider webhook replay/idempotency with server-owned amount/order identity. |
| Refund -> entitlement revoke | REQUIRED FOR PAID PRODUCT | **КОД ЕСТЬ — НУЖНО REAL E2E** | payment candidate + E2E harness | Prove real/safely bounded refund path and deterministic revoke. |
| Saved card / auto-renewal | NOT IN FIRST OFFER | **НЕ ДЕЛАЕМ** | product decision | Must not appear accidentally in checkout. |

## 7. Production infrastructure launch inventory

| Production capability | Current truth | Evidence | Remaining blocker / next action |
| --- | --- | --- | --- |
| Yandex Cloud deployment package | **КОД ЕСТЬ — BLOCKED_EXTERNAL** | merged PR #150 | Create/admit real staging/production resources and exact release deployment. |
| Application runtime | **КОД ЕСТЬ — НУЖНО DEPLOY** | PR #150 | Deploy immutable release artifact/image in Yandex; runtime must not fetch GitHub. |
| Managed PostgreSQL / admitted persistence | **КОД/SCHEMA ЕСТЬ — НУЖНО REAL RESOURCE** | portable substrate + PR #150 | Provision/admit database, migrations, connection, persistence and restore proof. |
| Lockbox / production secrets | **КОД/CONFIG ЕСТЬ — НУЖНО REAL RESOURCE** | PR #150 | Provision secrets outside Git/client/logs with minimum roles and rotation path. |
| API edge / TLS / CORS | **КОД ЕСТЬ — НУЖНО REAL ACCEPTANCE** | Pro client + Yandex package | Admit domains/origins/certificates and reject untrusted origins. |
| Monitoring / redacted logs | **КОДОВЫЕ ОСНОВЫ ЕСТЬ — НУЖНО OPERATIONAL PROOF** | staging/operational packages | Verify health, failure alerts, no secret/contact/audio leakage. |
| Backup / restore | **НУЖНО PRODUCTION PROOF** | production architecture | Prove restore path for canonical state before public paid go-live. |
| Rollback / kill switches | **КОД ЕСТЬ — НУЖНО PRODUCTION PROOF** | reliability/deployment/E2E contracts | Prove release rollback and provider/payment/Tutor kill-switch behavior. |
| GitHub runtime independence | **AUTHORITY FIXED — НУЖНО PRODUCTION PROOF** | masterplan v1.4 | Deployed release must run with GitHub unavailable; images/config/knowledge required at runtime exist in Yandex contour. |
| Google Drive runtime independence | **AUTHORITY FIXED — НУЖНО PRODUCTION PROOF** | source-storage policy | Normal learning/Tutor/trainer must work after ingestion with Drive unavailable. |
| Learner audio persistence | **MUST = 0** | Tutor/privacy authority | Production E2E must prove no recording/fragment/voiceprint/persistent acoustic representation is stored. |

## 8. Subject truth launch inventory — current finite denominator

Current PR #164 exact state at the 2026-09-02 owner-decision update:

- admission units accounted: **1325 / 1325**;
- official requirements accounted: **1400 / 1400**;
- exact semantic component-set acceptances: **28 units / 28 requirements**;
- accepted nonsemantic object dispositions: **1 unit / 1 requirement**;
- total subject-disposed objects: **29 units / 29 requirements**;
- remaining subject-review objects: **1287 units / 1362 requirements**;
- accepted bounded `ru-*` semantics: **75**;
- finite semantic review groups: **74**;
- modules with reviewed accounting: **16 / 16**;
- false exact-mastery admissions: **0**.

This is a finite closure problem. No new broad scope audit is allowed unless a concrete source contradiction appears.

### Mandatory acceleration algorithm

Do not process 1287 objects one by one when multiple objects share an already proven exact owner set.

Use this implementation loop:

`74 review groups -> batch-eligibility computation -> exact canonical owner sets -> source-backed batch packet -> deterministic object bindings -> subject acceptance -> denominator reconciliation`

A group is batch-eligible only when every object admitted by the batch has:

- an exact source-supported component owner set;
- no unresolved family placeholder;
- no broader/nonexact owner substituted for an explicit atomic owner;
- no rights-blocked learner prose dependency;
- deterministic object and requirement identities;
- independent-evidence semantics that cannot emit false atomic mastery.

If a group fails those conditions, split only that group at the smallest meaningful semantic boundary. Do not reopen unrelated accepted groups.

## 9. Tutor launch policy — closed decisions vs remaining work

Closed decisions — do not revisit without a new defect:

- Russian learner default conversational brain: **Yandex**;
- OpenAI: fallback/escalation after production admission;
- learner provider selector: none;
- voice: **Yandex SpeechKit Lera**;
- reading profile: **neutral / 1.04 / 0 Hz / marked pauses**;
- learner audio persistence: **0**.

Remaining executable work:

1. integrate the accepted provider policy/results into the production Tutor path based on current `main`;
2. retain one session across text <-> voice;
3. prove default routing and bounded fallback/kill switch;
4. reduce/guard unacceptable latency and provider failures;
5. prove Tutor help -> independent verification -> exactly-once PEIS evidence;
6. do not run more subjective voice casting.

## 10. Legal / privacy / operations

The production-facing legal/privacy/operational packet is implemented and linked from the Pro client (merged PR #153), but real external/operator acceptance remains required.

Before public paid traffic:

- operator/legal values and versions must be current and accepted;
- product claims must match actually open Russian surfaces;
- payment/refund/receipt disclosures must match production behavior;
- privacy wording must state learner audio is not stored;
- support/escalation and privacy/audio incident procedures must be operational;
- no document may claim `READY` from code presence alone.

Status: **КОД ЕСТЬ — BLOCKED_EXTERNAL**.

## 11. Final E2E — do not redesign

The exact-release production E2E harness is already merged (PR #163). It is the acceptance skeleton, not a simulation to be rewritten.

For the **first paid AI-analysis product**, run a bounded product-specific production E2E proving its exact chain: `public/free result -> identity/contact -> purchase -> receipt -> entitlement/access -> grounded analysis -> permitted Tutor follow-up -> persisted access/state -> refund/revoke`.

For **full Eksamio Pro Russian**, the existing full release chain remains:

`public entry -> passwordless account -> anonymous link -> purchase -> receipt -> entitlement -> Russian PEIS persistence -> trainer -> Tutor text/voice -> independent verify -> progress -> logout/login -> refund/revoke -> kill switch`

Status: **КОД ЕСТЬ — BLOCKED_DEPENDENCY** until each marketed product's own subject + external production gates pass.

## 12. The finite blocker list as of 2026-09-02

There are **eight full-Pro launch blocker classes**. Do not invent a ninth class merely because an implementation contains subtasks. A narrower product may pass its own subset of these gates without falsely declaring full Pro ready.

1. **Russian subject/content acceptance** — PR #164; convert the known 1325/1400 denominator and current `1287 / 1362` subject-review remainder to exact accepted ownership/disposition at batch throughput.
2. **Russian PEIS/product live assembly** — connect real accepted content, trainer/work-on-errors/NBA/progress and account state to the real backend; productize diagnostics and rebuild trainer/constructor on accepted data.
3. **Tutor production integration** — land the accepted provider/voice policy into the production path and prove text/voice continuity/reliability; the first AI-analysis product needs only its exact permitted Tutor boundary.
4. **Yandex production infrastructure** — real runtime, PostgreSQL, Lockbox, API edge/TLS/CORS, monitoring, backup/rollback and runtime independence from GitHub/Drive.
5. **Identity delivery** — real Postbox and, if offered, SMS.RU delivery acceptance plus anonymous->account continuity.
6. **Payment/receipt/entitlement** — materialize exact product SKU(s), accept Robokassa/Robocheki and prove payment -> receipt -> entitlement/access -> refund/revoke.
7. **Legal/privacy/operator acceptance** — accept actual production values/docs/operations; audio storage remains zero.
8. **Exact-release production E2E + owner go-live** — run the correct bounded harness for the marketed release, then explicitly enable that product's public paid traffic.

If all eight are PASS for full Pro, there is no hidden “architecture completion” gate after them.

## 13. Parallel execution lanes — start now

Run independent work in parallel without waiting for another planning cycle:

### P0-A — Russian subject batch closure

- continue exact high-throughput acceptance from the current PR #164 remainder;
- reuse accepted canonical identities/content first;
- reconcile counters after accepted waves;
- repeat immediately until `russian_content = PASS` or a genuinely new source/semantic blocker is isolated.

### P0-B — Russian product assembly and first launchable surfaces

- preserve accepted free EGE demos;
- rebuild the unified trainer + constructor against the new Russian program/learning engine and accepted data;
- productize Russian diagnostics with fail-closed semantic conclusions;
- connect real PEIS state for attempt/error/practice/NBA/progress;
- productize **Personal Russian AI Analysis** as the first paid narrow product;
- use one product shell, one PEIS and one Russian truth layer;
- keep full-course/full-OGE/full-EGE/full-5–11 claims hidden until their subject gates pass;
- apply issue #180: no work on legacy OGE `zadanie-1…8` content.

### P0-C — Tutor integration

- integrate the accepted provider policy onto current-main production Tutor boundary;
- keep the layer provider-neutral even where a current production default is selected;
- text/voice continuity, latency/reliability and kill-switch gates;
- add the exact bounded Tutor interaction needed by the paid AI-analysis product without weakening full-Pro Tutor gates.

### P0-D — external production acceptance

- Yandex resources/deployment;
- Postbox/SMS delivery where actually offered;
- first-paid-product SKU + Robokassa/Robocheki;
- legal/operator values;
- exact evidence URIs/checksums for preflight/E2E.

### P0-E — release progression

- release the free Russian contour as soon as each exposed surface passes its own gate;
- freeze exact candidate identity for Personal Russian AI Analysis;
- run its bounded production E2E and owner go-live;
- continue subject + product closure to full Pro;
- public full-Pro traffic ON only after all full-Pro mandatory gates pass.

## 14. Progressive rollout stages

- **R0 — existing free base:** accepted EGE Russian demos remain free/anonymous.
- **R0.1 — rebuilt free Russian contour:** unified trainer/constructor and diagnostics may open progressively on accepted scope only.
- **R0.2 — first paid narrow product:** Personal Russian AI Analysis; detailed grounded error analysis + weak-skill priorities + plan + next actions + bounded Tutor follow-up. It is not full Pro and must never be marketed as full-subject coverage.
- **R1 — full paid Eksamio Pro Russian closed loop:** only after full Russian subject/content gate is green; account + entitlement + accepted full Russian learning + trainer/work on mistakes + next action + progress + Tutor text/voice + independent verify + persistence + refund/revoke.
- **R2 — EGE expansion/depth:** richer admitted EGE route, thematic/exam training, complete EGE course/personal route and retention.
- **R3 — OGE expansion:** full admitted OGE learner surface over the same full-subject identities; legacy task pages remain archived per #180.
- **R4 — school 5–11 expansion:** grade/topic navigation and full school-program learning surfaces.
- **R5 — advanced:** essay/extended answers, richer forecast/analytics, parent/reporting and later multimodal features.

A rollout stage controls what is visible; it does not create a new Russian knowledge base.

## 15. No-surprise / no-circle execution rules

1. **Do not reopen merged accepted work** without a concrete regression, changed external requirement or source contradiction.
2. **Do not repeat scope discovery:** the Russian denominator is already 1325/1400 and 16/16 modules.
3. **Audit only to make a decision that immediately changes code/content/admission.** Narrative audit with no executable consequence is deferred.
4. **Prefer batch execution:** if one exact authority safely resolves many objects, bind them in one reviewed wave.
5. **Do not block narrow truthful products on unrelated unaccepted subject scope.** Conversely, never use a narrow-product launch to imply full-subject readiness.
6. **No hidden feature inflation:** progressive/later features do not become full-Pro blockers unless the product markets them as present or a hard law/security invariant requires them.
7. **No false readiness:** code-ready, provider-ready, bounded-product-ready and full-Pro-ready are different statuses.
8. **No provider lock in core:** production defaults may change; PEIS/business/subject contracts remain portable.
9. **No GitHub/Drive runtime dependency.**
10. **No secrets or learner audio persistence.**
11. After each accepted delta, update only the affected board row/counter and move to the next blocker; do not run a new project-wide audit.

## 16. Immediate next executable action

The next Central Brain action is **not another plan**.

Run two independent P0 lines now:

1. **P0-A subject:** continue exact PR #164 closure with high-throughput reuse of already accepted semantic owners, preserving `false_exact_mastery = 0`.
2. **P0-B product:** inventory the existing unified Russian trainer/constructor runtime, discard old data as authority, define the new-program rebinding boundary, and materialize the first launchable free diagnostic/trainer slice plus the paid AI-analysis product contract.

P0-C/P0-D proceed in parallel where they do not conflict.

The operational success measure is no longer “documents produced”. It is (a) downward movement of the Russian subject remainder, and (b) movement of the free contour / Personal Russian AI Analysis toward real user-facing launch without false full-Pro claims.
