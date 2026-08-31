# Eksamio — Current Project Priorities / Operational Launch Board

**Status:** CURRENT PRODUCT / DELIVERY AUTHORITY
**Updated:** 2026-08-31
**Baseline main:** `ab3839085743759ac61857dec6cec1607e306e68`
**Primary deadline:** paid `Eksamio Pro — Russian` production launch by **2026-09-01**

This file is the single operational launch board for the current Russian launch. It supplements `00-PRODUCT-MASTERPLAN.md` v1.4 and approved owner decisions.

Its purpose is to prevent late surprises about product scope, missing learner surfaces, infrastructure, commercial dependencies or rollout stages. A launch-critical item must be present here. A new mandatory item may be added only when new owner, legal, security or production evidence genuinely creates a new gate; ordinary implementation detail does not expand launch scope.

## 1. One launch definition

The launch is not “content ready”, “Tutor ready”, “checkout ready” or “site ready” in isolation.

The paid Russian launch is complete only when one exact production release proves:

`public entry -> identity -> purchase -> receipt -> entitlement -> Russian learning -> PEIS state -> practice -> Tutor text/voice -> independent verification -> persisted progress -> return login -> refund/revoke`

Primary dependency chain:

`FULL_RUSSIAN_TRUTH -> WORKING_RUSSIAN_PRODUCT -> YANDEX_PRODUCTION -> REAL_IDENTITY -> REAL_PAYMENT -> REAL_TUTOR -> END_TO_END_ACCEPTANCE -> PUBLIC_GO_LIVE`

Until this chain is complete, Mathematics, Physics, nonessential historical work, SourceCraft migration, visual polish and speculative platform work are deferred.

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
| Public `eksamio.ru` entry | REQUIRED | **ЕСТЬ** | existing Tilda/public site and accepted demo surfaces | Preserve; add only launch entry/sign-in/purchase links when production target is admitted. |
| Free demos / diagnostics | REQUIRED BASE | **ЕСТЬ** | accepted demo/scorer surfaces; protected by Russian closure gates | Keep anonymous and free; connect evidence handoff without modifying accepted exam truth. |
| Protected Eksamio Pro shell | REQUIRED | **КОД ЕСТЬ — НУЖНО ПОДКЛЮЧИТЬ/ПРИНЯТЬ** | merged PR #142 | Replace mock adapters with admitted real backend/TLS/CORS/session endpoints and rerun mobile/desktop E2E. |
| Full Russian program navigation / course shell | REQUIRED | **КОД ЕСТЬ — BLOCKED_SUBJECT** | PR #142 renders 5–11 + all 16 modules + OGE/EGE routes | Bind only subject-accepted content; full learner content opens as PR #164 denominator is accepted. |
| Work on mistakes | REQUIRED R1 | **КОД ЕСТЬ — НУЖНО ПОДКЛЮЧИТЬ** | Pro-client vertical slice + PEIS contracts | Wire real failed-attempt -> exact skill -> practice/help -> verify handoff to server-owned PEIS. |
| Thematic trainer | REQUIRED R1 | **КОД/ITEM BASE ЕСТЬ — НУЖНО ПОДКЛЮЧИТЬ** | reviewed Russian trainer/semantic mappings + Pro client | Connect admitted items to real PEIS evidence/persistence; never create a second trainer knowledge model. |
| EGE Russian trainer / route | FIRST COMMERCIAL EXAM ROUTE | **КОД/ROUTE ЕСТЬ — BLOCKED_SUBJECT** | Pro client + reviewed EGE/demo/trainer authority | Finish subject acceptance for marketed EGE scope; connect route to live PEIS. |
| OGE Russian trainer / route | PROGRESSIVE R3 | **SHELL/ROUTE ЕСТЬ — BLOCKED_SUBJECT** | Pro client + current OGE authority work in PR #164 | Open after exact OGE component acceptance; reuse same school identities and PEIS. |
| School Russian 5–11 views | PROGRESSIVE R4 | **SHELL ЕСТЬ — BLOCKED_SUBJECT** | PR #142 + full-subject 16-module model | Open grade/topic views only over accepted full-school content. |
| Trainer constructor | PROGRESSIVE R2 | **НУЖНО СДЕЛАТЬ** | no durable current-main production implementation is being assumed | Build selection UI/service over admitted canonical topics/task families/item pool; no separate ontology. Not a first R1 blocker unless marketed at launch. |
| Personal “Training for today” / NBA | REQUIRED R1 as next action | **КОД/CONTRACTS ЕСТЬ — НУЖНО ПОДКЛЮЧИТЬ** | PEIS NBA contracts + PR #142 progress/NBA shell | Connect real server-owned learner evidence, retention risk and exam value to generated next action. |
| Russian guided course / learning route | REQUIRED CORE, progressively filled | **SHELL ЕСТЬ — BLOCKED_SUBJECT** | PR #142 program shell | Materialize accepted teach/practice/verify content and prerequisite traversal from full program. |
| Progress / weak-points / readiness | REQUIRED R1 | **КОД ЕСТЬ — НУЖНО ПОДКЛЮЧИТЬ** | PR #142 progress/NBA surface + shared PEIS contracts | Replace fixture state with real persistence/recompute and cross-session proof. |
| Independent verification after help | REQUIRED | **КОД/CONTRACT ЕСТЬ — НУЖНО LIVE E2E** | shared PEIS/Tutor policy and merged Tutor slice | Prove exactly-once independent evidence after substantial Tutor help. |
| Retention / spaced recheck | REQUIRED CORE | **КОД/CONTRACT ЕСТЬ — НУЖНО LIVE E2E** | shared retention contracts | Persist schedule/state and prove later recheck changes retained mastery correctly. |
| Tutor text | REQUIRED | **КОД ЕСТЬ — НУЖНО PRODUCTION INTEGRATION** | merged grounded Tutor slice + current PR #172 benchmark work | Land final Russian provider policy into production Tutor path; Yandex brain default; prove latency/reliability/PEIS continuity. |
| Tutor realtime voice | REQUIRED | **КОД ЕСТЬ — НУЖНО PRODUCTION INTEGRATION** | SpeechKit adapters + PR #172 human acceptance | Use accepted Lera profile; finish production streaming/continuity/reliability; audio persistence exactly 0. |
| Trainer/course Tutor handoff | REQUIRED | **КОДОВЫЕ ОСНОВЫ ЕСТЬ — НУЖНО E2E** | shared Tutor + PEIS boundaries | One learning episode must preserve goal/evidence when moving trainer -> Tutor -> verify. |
| Essay / extended-answer AI support | LATER / R5 | **LATER** | architecture authority only for gated expansion | Add only after rubric/source/eval gate; not a Sep-1 closed-loop blocker unless marketed. |
| Parent/reporting surfaces | LATER / R5 | **LATER** | product authority | Do not delay first closed loop; implement under separate privacy/access rules later. |
| Vision/photo/richer multimodal | LATER | **LATER** | masterplan | Explicitly deferred. |

### Product-scope rule

Full Russian **subject truth** is mandatory for any claim that Eksamio offers the complete Russian subject. Specialized learner surfaces may be released progressively after their own UI/runtime gates without rebuilding the subject.

If a progressive surface is not ready, it is hidden or described as unavailable; it does not silently expand the first-release blocker list.

## 6. Commercial / account launch inventory

| Capability | Rollout | Current truth | Evidence | Remaining blocker / next action |
| --- | --- | --- | --- | --- |
| Passwordless account core | REQUIRED | **ЕСТЬ КАК КОД** | merged identity core | Connect real delivery and production persistence. |
| Yandex Postbox e-mail delivery | REQUIRED | **КОД ЕСТЬ — BLOCKED_EXTERNAL** | merged PR #148 | Verify sender/domain, IAM/service-account role and bounded real delivery smoke. |
| SMS.RU phone delivery | REQUIRED while phone login is offered | **КОД ЕСТЬ — BLOCKED_EXTERNAL** | merged PR #148 | Configure real account/API credential/sender and bounded real SMS smoke; otherwise do not advertise phone login. |
| Anonymous demo -> account continuity | REQUIRED | **КОД ЕСТЬ — НУЖНО PRODUCTION E2E** | identity/Pro-client contracts | Prove safe link to server-owned identity without duplicate/lost learner evidence. |
| Pro offer / SKU contract | REQUIRED | **НУЖНО ДОКОНЦА МАТЕРИАЛИЗОВАТЬ** | payment/entitlement architecture exists | Persist exact launch SKUs, durations, prices, quotas and entitlement IDs before real checkout; do not invent prices in adapter code. |
| Pro 30-day access | COMMERCIAL | **OWNER PRODUCT DECISION — НУЖНО SKU** | existing product decision | Materialize server-owned SKU/price/entitlement; no auto-renewal. |
| Pro 90-day access | COMMERCIAL | **OWNER PRODUCT DECISION — НУЖНО SKU** | existing product decision | Materialize server-owned SKU/price/entitlement; 90-day daily value may be better; no auto-renewal. |
| Separate paid full AI analysis | PROGRESSIVE COMMERCIAL | **PRODUCT DECISION — НУЖНО PRODUCTIZATION** | existing product decision | Do not block R1 if not marketed on day one; when enabled, define exact price/quota/credit-to-Pro rule server-side. |
| Robokassa initiation | REQUIRED | **КОД ЕСТЬ — BLOCKED_EXTERNAL** | merged PR #147 | Actual merchant settings/credentials + bounded real SBP/card acceptance. |
| NPD receipt / Robocheki SMZ | REQUIRED | **КОД ЕСТЬ — BLOCKED_EXTERNAL/LEGAL** | PR #147 candidate | Accept fiscal/legal configuration and prove real receipt lifecycle. |
| Exactly-once entitlement grant | REQUIRED | **КОД ЕСТЬ — НУЖНО REAL E2E** | payment core / E2E harness | Prove provider webhook replay/idempotency with server-owned amount/order identity. |
| Refund -> entitlement revoke | REQUIRED | **КОД ЕСТЬ — НУЖНО REAL E2E** | payment candidate + E2E harness | Prove real/safely bounded refund path and deterministic revoke. |
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
| Backup / restore | **НУЖНО PRODUCTION PROOF** | production architecture | Prove restore path for canonical state before public go-live. |
| Rollback / kill switches | **КОД ЕСТЬ — НУЖНО PRODUCTION PROOF** | reliability/deployment/E2E contracts | Prove release rollback and provider/payment/Tutor kill-switch behavior. |
| GitHub runtime independence | **AUTHORITY FIXED — НУЖНО PRODUCTION PROOF** | masterplan v1.4 | Deployed release must run with GitHub unavailable; images/config/knowledge required at runtime exist in Yandex contour. |
| Google Drive runtime independence | **AUTHORITY FIXED — НУЖНО PRODUCTION PROOF** | source-storage policy | Normal learning/Tutor/trainer must work after ingestion with Drive unavailable. |
| Learner audio persistence | **MUST = 0** | Tutor/privacy authority | Production E2E must prove no recording/fragment/voiceprint/persistent acoustic representation is stored. |

## 8. Subject truth launch inventory — current finite denominator

Current PR #164 exact state:

- admission units accounted: **1325 / 1325**;
- official requirements accounted: **1400 / 1400**;
- exact object-bound accepted component sets: **21 units / 21 requirements**;
- remaining without accepted component set: **1295 units / 1370 requirements**;
- accepted bounded `ru-*` semantics: **75**;
- finite semantic review groups: **74**;
- modules with reviewed accounting: **16 / 16**;
- false exact-mastery admissions: **0**.

This is a finite closure problem. No new broad scope audit is allowed unless a concrete source contradiction appears.

### Mandatory acceleration algorithm

Do not process 1295 objects one by one when multiple objects share an already proven exact owner set.

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

1. integrate the accepted PR #172 policy/results into the production Tutor path based on current `main`;
2. retain one session across text <-> voice;
3. prove Yandex default routing and bounded fallback/kill switch;
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

Remaining job is to feed it real admitted evidence for one release identity and prove:

`public entry -> passwordless account -> anonymous link -> purchase -> receipt -> entitlement -> Russian PEIS persistence -> trainer -> Tutor text/voice -> independent verify -> progress -> logout/login -> refund/revoke -> kill switch`

Status: **КОД ЕСТЬ — BLOCKED_DEPENDENCY** until Russian subject + external production gates pass.

## 12. The finite blocker list as of 2026-08-31

There are **eight launch blocker classes**. Do not invent a ninth class merely because an implementation contains subtasks.

1. **Russian subject/content acceptance** — PR #164; convert the known 1325/1400 denominator to exact accepted component ownership at batch throughput.
2. **Russian PEIS/product live assembly** — connect real accepted content, trainer/work-on-errors/NBA/progress and account state to the real backend.
3. **Tutor production integration** — land final Yandex-default/Lera policy from PR #172 into the production path and prove text/voice continuity/reliability.
4. **Yandex production infrastructure** — real runtime, PostgreSQL, Lockbox, API edge/TLS/CORS, monitoring, backup/rollback and runtime independence from GitHub/Drive.
5. **Identity delivery** — real Postbox and, if offered, SMS.RU delivery acceptance plus anonymous->account continuity.
6. **Payment/receipt/entitlement** — materialize exact launch SKU(s), accept Robokassa/Robocheki and prove payment -> receipt -> entitlement -> refund/revoke.
7. **Legal/privacy/operator acceptance** — accept actual production values/docs/operations; audio storage remains zero.
8. **Exact-release production E2E + owner go-live** — run the merged harness against the admitted release, then explicitly enable public paid traffic.

If all eight are PASS, there is no hidden “architecture completion” gate after them.

## 13. Parallel execution lanes — start now

Run independent work in parallel without waiting for another planning cycle:

### P0-A — Russian subject batch closure

- compute batch-eligible groups from the existing 74 finite semantic review groups;
- materialize the first high-throughput exact acceptance wave;
- reconcile counters;
- repeat immediately until `russian_content = PASS` or a genuinely new source/semantic blocker is isolated.

### P0-B — production Russian assembly

- wire PR #142 client to production-shaped backend;
- real PEIS state for attempt/error/practice/NBA/progress;
- accepted Russian content only;
- prepare dedicated surface feature flags so progressive R2–R5 sections can open without redeploying subject truth.

### P0-C — Tutor integration

- rebase/extract final accepted PR #172 delta onto current-main production Tutor boundary;
- Yandex brain default;
- accepted Lera profile;
- text/voice continuity, latency/reliability and kill-switch gates.

### P0-D — external production acceptance

- Yandex resources/deployment;
- Postbox/SMS delivery;
- launch SKU + Robokassa/Robocheki;
- legal/operator values;
- exact evidence URIs/checksums for preflight/E2E.

### P0-E — final release

- freeze exact candidate identity;
- production E2E;
- rollback/kill-switch rehearsal;
- owner go-live;
- public traffic ON only after all mandatory gates pass.

## 14. Progressive rollout stages

- **R0 — private production assembly:** all real components connected, public paid traffic OFF.
- **R1 — first paid Russian closed loop:** account + entitlement + accepted Russian learning + trainer/work on mistakes + next action + progress + Tutor text/voice + independent verify + persistence + refund/revoke.
- **R2 — EGE expansion:** full admitted EGE route, richer thematic/exam training, trainer constructor when implemented, complete EGE course/personal route and retention.
- **R3 — OGE expansion:** full admitted OGE learner surface over the same full-subject identities.
- **R4 — school 5–11 expansion:** grade/topic navigation and full school-program learning surfaces.
- **R5 — advanced:** essay/extended answers, richer forecast/analytics, parent/reporting and later multimodal features.

A rollout stage controls what is visible; it does not create a new Russian knowledge base.

## 15. No-surprise / no-circle execution rules

1. **Do not reopen merged accepted work** without a concrete regression, changed external requirement or source contradiction.
2. **Do not repeat scope discovery:** the Russian denominator is already 1325/1400 and 16/16 modules.
3. **Audit only to make a decision that immediately changes code/content/admission.** Narrative audit with no executable consequence is deferred.
4. **Prefer batch execution:** if one exact authority safely resolves many objects, bind them in one reviewed wave.
5. **No hidden feature inflation:** progressive/later features do not become Sep-1 blockers unless the product markets them as present or a hard law/security invariant requires them.
6. **No false readiness:** code-ready, provider-ready and production-ready are different statuses.
7. **No provider lock in core:** Yandex is the Russian production default/runtime, but PEIS/business/subject contracts remain portable.
8. **No GitHub/Drive runtime dependency.**
9. **No secrets or learner audio persistence.**
10. After each accepted delta, update only the affected board row/counter and move to the next blocker; do not run a new project-wide audit.

## 16. Immediate next executable action

The next Central Brain action is **not another plan**.

Start P0-A on PR #164 by creating a deterministic **batch-eligibility + batch-acceptance wave** over the existing 74 finite semantic review groups. The first wave must maximize exact object/requirement closure using already canonical source-supported owners while preserving `false_exact_mastery = 0`.

In parallel, P0-B/P0-C/P0-D may proceed where they do not conflict.

The operational success measure is no longer “documents produced”. It is the downward movement of the eight blocker classes and the exact Russian remaining denominator.