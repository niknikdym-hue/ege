# Eksamio — Current Project Priorities / Whole-Project Operational Board

**Status:** CURRENT PRODUCT / DELIVERY AUTHORITY  
**Updated:** 2026-09-09  
**Baseline main:** `85d2f2b3dd0cf56c428f57c8a5c7d1b636ecebbb`  
**Masterplan:** `00-PRODUCT-MASTERPLAN.md` v2.0

This file is the executable whole-project board. It exists so the owner can always see where Eksamio is from the next launch action through the complete Russian product and subsequent subjects.

## 1. Top-level project route

`A. RUSSIAN PUBLIC PAID LAUNCH -> B. RUSSIAN FULL PRODUCT -> C. MATHEMATICS -> D. PHYSICS -> E. NEXT SUBJECTS / PLATFORM SCALE`

Current active milestone: **A — `RUSSIAN_PUBLIC_PAID_LAUNCH_PASS`**.

Next milestone after A: **B — `RUSSIAN_FULL_PRODUCT_PASS`**.

No new subject may displace the active critical path merely because its work is easier or already has candidate assets.

## 2. Status vocabulary

- `NOT_STARTED` — required but no accepted implementation yet.
- `DESIGNED` — authority/specification exists.
- `CODE_READY` — implementation + deterministic code/CI evidence exist.
- `INTEGRATION_PENDING` — code exists but is not on the accepted integrated release path.
- `BLOCKED_SUBJECT` — exact subject/content truth still blocks admission.
- `BLOCKED_EXTERNAL` — external cloud/provider/operator evidence is missing.
- `PRIVATE_PRODUCTION_PASS` — exact real contour works with public traffic OFF.
- `VISIBLE_TO_LEARNER` — real user can use the feature on the intended product surface.
- `PUBLIC_LAUNCH_PASS` — exact production release + owner go-live passed.
- `DONE` — final required state for that row is proven.

`CODE_READY != VISIBLE_TO_LEARNER`.

## 3. Whole-project summary

| Stage | Product result | Current status | Critical now? |
| --- | --- | --- | --- |
| A | Russian public paid launch | **IN PROGRESS / NO-GO** | YES |
| B | Russian full product | **PLANNED + PARTIAL CODE/CONTENT** | NEXT |
| C | Mathematics full product | **DEFERRED / EXISTING ASSETS PRESERVED** | NO |
| D | Physics full product | **DEFERRED / EXISTING ASSETS PRESERVED** | NO |
| E | Next subjects / platform scale | **FUTURE** | NO |

## 4. Stage A — Russian public paid launch

Target learner path:

`eksamio.ru -> registration/login -> Pro purchase -> receipt -> entitlement -> Russian learning -> PEIS -> practice/error work -> Tutor text/voice -> independent verify -> progress -> logout/login -> refund/revoke`

### A1. Product authority / project control

| Task | Status | Evidence / current truth | Next action |
| --- | --- | --- | --- |
| A1.1 Russian-first masterplan | **DESIGNED in current authority branch** | v2.0 update | Review/merge after CI/doc sanity |
| A1.2 Whole-project operational board | **DESIGNED in current authority branch** | this file | Bind structured board to Owner Console |
| A1.3 Owner Console whole-project view | **DESIGNED / IMPLEMENTATION REQUIRED** | masterplan §19 | Build local development console; no learner runtime dependency |
| A1.4 GitHub/CI live status ingestion | **NOT_STARTED for console** | GitHub remains source of truth | Auto-read PR/SHA/CI; display conflicts/staleness |

### A2. Russian source/content/semantic truth

| Task | Status | Evidence / current truth | Next action |
| --- | --- | --- | --- |
| A2.1 Source corpus / official scope | **CODE/CONTENT AUTHORITY EXISTS** | PR #164; 16/16 modules accounted | Preserve accepted source truth |
| A2.2 Exact semantic/object closure | **BLOCKED_SUBJECT** | PR #164 current branch truth: 36 exact component-set acceptances; 1280 units / 1355 requirements remain without accepted semantic component set; false exact mastery = 0 | Continue bounded exact acceptance from current remainder; no fuzzy/title admission |
| A2.3 Rights-safe learner content | **PARTIAL / BLOCKED_SUBJECT** | #139 salvage input; rights-blocked bytes not admitted | Materialize only source-backed/original accepted content |
| A2.4 Launch-scope content visibility | **BLOCKED_SUBJECT** | full product shell cannot honestly expose unaccepted scope | Open only accepted content via feature/admission gates |

### A3. Registration / identity / sessions

| Task | Status | Evidence / current truth | Next action |
| --- | --- | --- | --- |
| A3.1 Passwordless registration core | **CODE_READY / INTEGRATION_PENDING** | PR #186 HEAD `ae169c82a6f6e515e95293625e31e342b447f867` | Integrate into exact release path when owner allows |
| A3.2 One registered identity -> one learner profile | **CODE_READY / INTEGRATION_PENDING** | PR #186 | Real production persistence proof |
| A3.3 Consent boundary | **CODE_READY / INTEGRATION_PENDING** | PR #186 | Production legal/version acceptance |
| A3.4 Secure cookie/CORS/CSRF boundary | **CODE_READY / INTEGRATION_PENDING** | PR #186 | Real domain/TLS/browser E2E |
| A3.5 Return login / same profile continuity | **CODE_READY / NEEDS PRODUCTION E2E** | PR #186 | Prove across real logout/login |
| A3.6 Anonymous demo handling | **DESIGNED FAIL-CLOSED** | browser state is not canonical mastery | If imported later, use separate server-owned bounded import contract |

### A4. Servers / production infrastructure

| Task | Status | Evidence / current truth | Next action |
| --- | --- | --- | --- |
| A4.1 Yandex application runtime | **CODE_READY / BLOCKED_EXTERNAL** | deployment/runtime candidate exists | Provision/admit real private production runtime |
| A4.2 PostgreSQL canonical persistence | **CODE_READY / BLOCKED_EXTERNAL** | #186 runtime/schema path | Provision real DB, migrate, persist, restore |
| A4.3 API Gateway / edge | **CODE_READY / BLOCKED_EXTERNAL** | Yandex-ready candidate | Admit real gateway/origin contracts |
| A4.4 TLS + production domains | **BLOCKED_EXTERNAL** | code boundary exists | Issue/admit certs and exact origins |
| A4.5 Production secret storage | **BLOCKED_EXTERNAL** | config boundary exists | Provision Lockbox/equivalent + minimum roles |
| A4.6 Monitoring / redacted logs | **PARTIAL CODE / BLOCKED_EXTERNAL** | operational foundations exist | Prove real alerts/health/redaction |
| A4.7 Backup + restore | **NOT PRODUCTION-PROVEN** | production architecture requires it | Execute bounded restore proof |
| A4.8 Rollback / kill switches | **CODE/POLICY EXISTS / NOT PRODUCTION-PROVEN** | release/provider contracts | Rehearse exact release rollback |
| A4.9 GitHub/Drive runtime independence | **DESIGNED / NEEDS PRODUCTION PROOF** | hard invariant | Test runtime with those sources unavailable |

### A5. Admissions Gate / server-owned learning evidence

| Task | Status | Evidence / current truth | Next action |
| --- | --- | --- | --- |
| A5.1 Live educational asset identities/provenance | **CODE_READY / INTEGRATION_PENDING** | PR #187 HEAD `c5592c212557b91578ed48e1bf778e30dd489dc7` | Reuse accepted identities, do not rebuild |
| A5.2 Registered exact-event contract | **NOT YET PRODUCTION-ADMITTED** | #187 intentionally leaves production_event_semantic_admissions=0 | Implement exact learner/item/action event admission on #186 runtime |
| A5.3 No mastery from page/route/local state | **POLICY/CODE GUARD EXISTS** | #187 + PEIS rules | Preserve in integrated runtime |
| A5.4 Exactly-once EvidenceEvent -> PEIS | **PARTIAL CONTRACTS / NEEDS E2E** | shared PEIS + server runtime | Prove retry/idempotency with real persistence |

### A6. Visible site / protected product UX

| Task | Status | Evidence / current truth | Next action |
| --- | --- | --- | --- |
| A6.1 Public Eksamio entry | **VISIBLE BASE EXISTS** | current eksamio.ru | Add honest registration/Pro entry only when target is ready |
| A6.2 Registration/login UI | **CODE_READY / NOT PUBLICLY VISIBLE AS PRODUCT** | staged Tilda-ready/web UI in #186 | Bind to real production API and publish after private E2E |
| A6.3 Protected Pro shell | **CODE_READY / NEEDS REAL BACKEND** | merged product client foundations | Replace fixtures/mocks with admitted backend |
| A6.4 Russian subject navigation | **SHELL EXISTS / BLOCKED_SUBJECT** | program shell + subject authority | Render only admitted Russian surfaces |
| A6.5 Profile/account page | **CODE/PATH EXISTS / NEEDS PRODUCTION E2E** | #186 account runtime + client | Bind and test desktop/mobile |
| A6.6 Progress / weak points / readiness view | **CODE/SHELL EXISTS / NEEDS REAL PEIS** | client + PEIS contracts | Bind server-owned learner state |
| A6.7 Purchase/access state in UI | **PARTIAL / NEEDS COMMERCIAL INTEGRATION** | entitlement contract exists | Show exact SKU/access dates/entitlement from server |
| A6.8 Mobile browser acceptance | **NOT FINAL PRODUCTION-PROVEN** | client tests exist | Run exact release mobile E2E |
| A6.9 Desktop browser acceptance | **NOT FINAL PRODUCTION-PROVEN** | client tests exist | Run exact release desktop E2E |

### A7. Russian learning loop / PEIS assembly

| Task | Status | Evidence / current truth | Next action |
| --- | --- | --- | --- |
| A7.1 Demo/diagnosis evidence handoff | **PARTIAL CODE / NEEDS REGISTERED ADMISSION** | demos + PEIS sensor foundations | Convert exact eligible outcomes into server events |
| A7.2 Error -> exact weak skill | **PARTIAL / BLOCKED BY A2/A5** | semantic mappings + PEIS | Wire accepted exact bindings |
| A7.3 Work on mistakes | **CODE FOUNDATION / NEEDS E2E** | product client + PEIS | Real error -> practice/help -> verify |
| A7.4 Next Best Action / Training today | **CONTRACT/SHELL EXISTS / NEEDS REAL STATE** | PEIS NBA contracts | Generate from persisted evidence |
| A7.5 Progress persistence | **CODE FOUNDATION / NEEDS PRODUCTION PROOF** | #186 + PEIS | Cross-session exact release proof |
| A7.6 Independent verification | **CONTRACT EXISTS / NEEDS LIVE E2E** | Tutor/PEIS policy | Exactly-once fresh item after help |
| A7.7 Retention schedule | **CONTRACT EXISTS / NEEDS LIVE E2E** | retention contracts | Persist and later recheck |

### A8. Pro SKU / payment / receipt / entitlement

| Task | Status | Evidence / current truth | Next action |
| --- | --- | --- | --- |
| A8.1 Pro 30-day SKU | **OWNER DECISION / NEEDS MATERIALIZED SKU** | no auto-renewal | Persist exact price/duration/quota/entitlement |
| A8.2 Pro 90-day SKU | **OWNER DECISION / NEEDS MATERIALIZED SKU** | no auto-renewal | Persist exact price/duration/quota/entitlement |
| A8.3 Robokassa initiation | **CODE_READY / BLOCKED_EXTERNAL** | merged payment candidate | Real merchant credential/settings + bounded payment smoke |
| A8.4 SBP/card acceptance | **BLOCKED_EXTERNAL** | provider contour required | Prove exact real payment path |
| A8.5 NPD / Robocheki receipt | **CODE_READY / BLOCKED_EXTERNAL/LEGAL** | payment candidate | Prove real receipt lifecycle |
| A8.6 Exactly-once entitlement | **CODE FOUNDATION / NEEDS REAL E2E** | server entitlement core | Callback replay/idempotency proof |
| A8.7 Refund -> revoke | **CODE FOUNDATION / NEEDS REAL E2E** | payment/E2E contracts | Bounded real refund/revoke proof |
| A8.8 No auto-renewal / no accidental saved card | **OWNER POLICY** | product decision | Verify checkout UI/provider settings |

### A9. Tutor text + realtime voice

| Task | Status | Evidence / current truth | Next action |
| --- | --- | --- | --- |
| A9.1 Provider-neutral Tutor/PEIS boundary | **CODE FOUNDATION EXISTS** | merged/shared Tutor contracts | Preserve one learning episode across providers/interfaces |
| A9.2 Brain shortlist: OpenAI/Qwen/DeepSeek/Yandex | **TEST CANDIDATES EXIST / FINAL PEDAGOGICAL ACCEPTANCE PENDING** | PRs #171/#172 and accepted owner shortlist | Run same bounded pedagogical comparison; list order is not ranking |
| A9.3 Final learner brain primary/fallback policy | **NOT FINAL** | requires own Eksamio test + production evidence | Decide from pedagogical quality/access/reliability/cost |
| A9.4 Yandex SpeechKit voice layer | **CODE FOUNDATION EXISTS** | SpeechKit adapters / selected voice profile work | Production streaming/latency/reliability acceptance |
| A9.5 Text <-> voice same session | **NEEDS PRODUCTION E2E** | shared Tutor session policy | Prove context/PEIS continuity |
| A9.6 Help -> independent verify -> evidence | **NEEDS PRODUCTION E2E** | Tutor/PEIS contract | Exactly-once verified learner outcome |
| A9.7 Learner audio persistence = 0 | **HARD POLICY / NEEDS PROD PROOF** | privacy/Tutor authority | Verify logs/storage/backups contain no audio |
| A9.8 Tutor kill switch/failure handling | **CODE/POLICY PARTIAL** | reliability gateway foundations | Prove production behavior |

### A10. Legal / privacy / support / operations

| Task | Status | Evidence / current truth | Next action |
| --- | --- | --- | --- |
| A10.1 Personal data / consent texts | **CODE/DOC FOUNDATION / NEEDS FINAL PRODUCTION VALUES** | legal/privacy packet exists | Accept actual operator/version values |
| A10.2 Offer/payment/refund disclosure | **PARTIAL / NEEDS COMMERCIAL FINALIZATION** | existing product/payment docs | Match actual SKU/provider behavior |
| A10.3 Audio non-storage disclosure | **POLICY EXISTS** | audio persisted = 0 | Ensure public docs match runtime |
| A10.4 Support/escalation | **NEEDS OPERATIONAL PROOF** | process foundations | Make real support path visible |
| A10.5 Privacy/security incident process | **NEEDS OPERATIONAL PROOF** | operational docs | Prove owner/operator handling path |

### A11. Exact-release private production E2E

| Task | Status | Evidence / current truth | Next action |
| --- | --- | --- | --- |
| A11.1 Freeze exact release identity | **NOT STARTED FOR FINAL RELEASE** | E2E harness exists | Pin commit/image/config/provider versions |
| A11.2 Full private production flow | **BLOCKED_DEPENDENCIES** | merged E2E skeleton | Run exact chain with real admitted resources |
| A11.3 Failure/retry/idempotency scenarios | **PARTIAL HARNESS / NEEDS PROD** | code gates exist | Execute provider/payment/session failures |
| A11.4 Rollback rehearsal | **NEEDS PROD** | policy/code foundations | Roll back exact candidate |
| A11.5 Owner acceptance packet | **NOT READY** | requires all evidence | Present only factual PASS/FAIL |

### A12. Public go-live

| Task | Status | Evidence / current truth | Next action |
| --- | --- | --- | --- |
| A12.1 Owner go-live approval | **BLOCKED** | A1–A11 incomplete | Ask only when all mandatory gates pass |
| A12.2 Publish/enable registration + Pro routes | **BLOCKED** | public traffic remains off for new Pro contour | Enable exact accepted release |
| A12.3 Public paid traffic | **BLOCKED** | launch NO-GO | Turn on only after owner gate |
| A12.4 Post-launch smoke | **NOT STARTED** | follows public release | Verify real learner path immediately |
| A12.5 Monitoring / rollback readiness | **NOT STARTED FOR PUBLIC RELEASE** | follows candidate admission | Watch exact launch signals |

## 5. Stage B — Russian full product

Stage B begins immediately after the first paid Russian launch; it is not optional polish.

| Task | Required product result | Current state |
| --- | --- | --- |
| B1 | Full accepted 5–11 Russian program | **BLOCKED_SUBJECT / partial assets** |
| B2 | Full EGE Russian route | **PARTIAL assets / subject gate** |
| B3 | Full OGE Russian route | **PARTIAL shell/assets / subject gate** |
| B4 | Thematic trainers on canonical identities | **PARTIAL accepted reconciliation** |
| B5 | Trainer constructor | **NOT FULLY IMPLEMENTED** |
| B6 | Work-on-mistakes across admitted Russian scope | **PARTIAL platform foundation** |
| B7 | Training for today / NBA | **CONTRACT/SHELL exists** |
| B8 | Guided course + prerequisite repair | **PARTIAL shell / content admission required** |
| B9 | Retention / spaced recheck | **CONTRACT exists / production E2E pending** |
| B10 | Progress / readiness / weak-point analytics | **SHELL/CONTRACT exists / real PEIS pending** |
| B11 | Personalized plan / replan | **PARTIAL PEIS foundation** |
| B12 | Tutor across course/trainer/errors with one context | **PARTIAL Tutor foundation** |
| B13 | Essay/extended answer support with rubric/eval gate | **LATER IN RUSSIAN FULL** |
| B14 | Stable production support/observability for Russian | **REQUIRED before Russian full PASS** |
| B15 | Honest complete Russian navigation on site/app | **NOT YET VISIBLE AS FULL PRODUCT** |

Exit criterion: **`RUSSIAN_FULL_PRODUCT_PASS`**.

Only after B exits does the main product delivery lane move to Mathematics.

## 6. Stage C — Mathematics

Existing mathematics assets are preserved, but active expansion waits for Russian full-product completion except urgent regressions.

| Task | Required result | Current state |
| --- | --- | --- |
| C1 | Official source corpus 2022–2026 | **EXISTING WORK / gaps to reconcile later** |
| C2 | Mathematics Identity Model | **PARTIAL candidate work exists** |
| C3 | Base route mapping | **PARTIAL** |
| C4 | Profile route mapping | **PARTIAL** |
| C5 | Demo/trainer/course alignment | **PARTIAL** |
| C6 | Exact evidence semantics | **NOT FULL PRODUCT-ADMITTED** |
| C7 | Reuse account/server/PEIS | **MUST REUSE RUSSIAN PLATFORM** |
| C8 | Reuse Pro/payment/Tutor shell | **MUST REUSE RUSSIAN PLATFORM** |
| C9 | Visible Mathematics learner product | **NOT STARTED AS FULL PRODUCT** |
| C10 | Mathematics private production E2E | **NOT STARTED** |
| C11 | Mathematics public rollout | **NOT STARTED** |

## 7. Stage D — Physics

| Task | Required result | Current state |
| --- | --- | --- |
| D1 | Official source corpus 2022–2026 | **PARTIAL / accepted historical assets exist** |
| D2 | Physics Identity Model | **PARTIAL subject work exists** |
| D3 | Demo/trainer/course alignment | **PARTIAL** |
| D4 | Exact evidence semantics | **NOT FULL PRODUCT-ADMITTED** |
| D5 | Reuse shared platform | **REQUIRED** |
| D6 | Visible Physics learner product | **NOT STARTED AS FULL PRODUCT** |
| D7 | Physics private production E2E | **NOT STARTED** |
| D8 | Physics public rollout | **NOT STARTED** |

## 8. Stage E — next subjects / platform scale

| Task | Required result | Current state |
| --- | --- | --- |
| E1 | Standard subject-onboarding contract | **FUTURE** |
| E2 | Next-subject commercial prioritization | **FUTURE** |
| E3 | Cross-subject learner profile where useful | **FUTURE** |
| E4 | Shared platform service extraction only after proof | **FUTURE** |
| E5 | Advanced analytics / experimentation | **FUTURE** |
| E6 | Additional multimodal capabilities | **FUTURE** |
| E7 | Internationalization only after product-market proof | **FUTURE** |

## 9. Owner Console rendering contract

Owner Console must render **all rows from stages A–E**, including future rows. It may default to Critical Path, but it may never make later stages disappear.

Required views:

1. `Whole Project` — A through E, expandable to every task.
2. `Critical Path` — currently A only, ordered by dependency.
3. `Russian Full Product` — A + B together so launch does not hide the remaining Russian product.
4. `Visible Product` — what a real learner can use today versus code-only work.
5. `Owner Gates` — only tasks genuinely waiting for owner action.
6. `Blockers` — subject, external, integration, production, legal.
7. `History` — completed milestones/PRs remain visible instead of disappearing.

Every task card/row must show:

- task ID;
- user-visible outcome;
- stage/workstream;
- priority;
- status;
- dependencies;
- blocker class;
- exact PR/branch/SHA when applicable;
- exact CI/evidence state;
- production state;
- `VISIBLE_TO_LEARNER` yes/no;
- executor (`Astra`, `Codex`, `Owner`, `External`);
- owner gate yes/no;
- next action;
- last evidence timestamp.

The panel is **not** an independent manual truth store. Semantic plan comes from Masterplan + this board; repository facts come from GitHub/CI. Mismatch must render `STALE/CONFLICT`.

## 10. Current critical path — ordered

Work now proceeds in this order, with safe parallelism only where dependencies allow:

1. keep Russian subject closure moving on exact current #164 remainder;
2. integrate registered server runtime (#186) with exact live asset identities (#187) through the Admissions Gate;
3. provision/admit private Yandex production resources;
4. bind the real protected web app + registration/login + learner state to those resources;
5. materialize launch Pro SKU(s) and real payment/receipt/entitlement contour;
6. complete the learner-facing Tutor pedagogical provider test and production text/voice integration;
7. finish legal/privacy/support production values;
8. run exact private-production E2E;
9. expose the complete accepted Russian launch flow on the site/app;
10. owner go-live -> public paid launch;
11. continue immediately to `RUSSIAN_FULL_PRODUCT_PASS`;
12. only then move the main product lane to Mathematics, then Physics.

## 11. No-circle rules

- Do not reopen accepted work without a concrete regression/source contradiction.
- Do not call code/CI completion a learner-visible result.
- Do not switch to another subject to avoid a Russian blocker.
- Do not create hidden launch classes outside this board; if a genuinely mandatory new class appears, add it explicitly with evidence.
- Do not create a second PEIS/account/billing/Tutor platform for another subject.
- Do not claim exact mastery from broad/fuzzy/title/route evidence.
- Do not make GitHub/Drive a production runtime dependency.
- Do not persist learner audio.
- Every accepted delta must move one or more board rows and therefore become visible in Owner Console.