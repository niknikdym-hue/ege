# Eksamio — Current Brain Handoff / Recovery Authority

**Status:** CURRENT RECOVERY / CONTINUATION AUTHORITY  
**Date:** 2026-08-31  
**Repository:** `niknikdym-hue/ege`  
**Pre-handoff verified `main`:** `3b1e21cfc7f7aa0fdf4bdb214b04bb482ca5696e`  
**Product masterplan:** `eksamio-learning-engine/00-PRODUCT-MASTERPLAN.md` v1.5  
**Operational board:** `eksamio-learning-engine/00B-PROJECT-PRIORITIES-CURRENT.md`

This file exists so that loss of a ChatGPT/Codex conversation cannot erase product state, owner decisions or the exact next critical path.

## 0. Recovery protocol — mandatory in every new chat

1. GitHub `niknikdym-hue/ege` is the development/source-of-truth repository. Never reconstruct current implementation state from chat memory when current `main`, PRs or committed authority can be read.
2. First read current `main`; the SHA above is only the verified pre-handoff baseline. If `main` is newer, inspect the delta before acting.
3. Then read this file, `00-PRODUCT-MASTERPLAN.md`, `00B-PROJECT-PRIORITIES-CURRENT.md`, and any authority file referenced by the active workstream.
4. **Live public-site truth is not inferred from GitHub, old crawler output, or old Tilda exports.** What a learner can see now must be verified from a fresh fetch/browser view of `https://eksamio.ru` and the exact public route.
5. A stale search/crawl snapshot is not allowed to override a fresher live fetch. If sources disagree, freshness must be stated and the public site rechecked.
6. Chat is not an authority store. Any new owner decision that changes product, release, privacy, monetization, provider or rollout rules must be committed to GitHub.

## 1. Role and governance

- Owner: final approval for commercial spend, provider/operator/legal decisions and public paid go-live.
- Central Brain: architecture, critical-path sequencing, acceptance, truth reconciliation, owner-decision capture and final `GO / NO-GO` decisions.
- Codex/Spark: implementation executors. Their self-reported PASS is evidence to audit, not authority by itself.
- Subject acceptance may not be bypassed by implementation convenience, AI inference or broad semantic fan-out.
- GitHub outage must never become an Eksamio runtime outage.

Hard runtime invariant:

`GitHub outage != Eksamio outage`

## 2. Product identity — fixed

Eksamio is a **Personal Exam Intelligence System (PEIS)**, not a collection of unrelated demos/trainers and not a generic exam chatbot.

Canonical learning loop:

`DIAGNOSE -> MODEL -> PRIORITIZE -> TEACH/PRACTICE -> VERIFY -> RETAIN -> REASSESS -> REPLAN`

The key value unit is a **verified change in learner knowledge state**, not a pageview, AI answer or watched explanation.

Subject order remains:

1. Russian;
2. Mathematics (profile + basic as routes of one Mathematics Identity Model);
3. Physics.

The first paid launch remains **Eksamio Pro — Russian**.

## 3. Progressive Public Release — NEW hard invariant 2026-08-31

Authority:

- `OWNER-DECISION-PROGRESSIVE-PUBLIC-RELEASE-2026-08-31.md`;
- `00-PRODUCT-MASTERPLAN.md` v1.5, section `Progressive Public Release`.

Decision:

- Eksamio does **not** wait for the whole platform or whole Pro stack to be finished before exposing already-ready learner value.
- A learner-facing function/surface that has passed its own subject/runtime/product acceptance, is truthful for its stated scope, safe and production-ready **must be published** without waiting for unrelated blockers.
- `DONE` without `LIVE` or an explicit blocker is not operationally complete for a public learner function.
- Allowed publication states:
  - `LIVE`;
  - `READY_TO_PUBLISH`;
  - `BLOCKED:<reason>`.
- Holding accepted learner value “under the hood” without a concrete blocker is prohibited.
- Paid Pro/payment/identity/Tutor/legal gates remain independent and may stay closed while free accepted value is released.

Operational meaning: **ready free learner value goes public immediately; paid Pro remains fail-closed until its own gates pass.**

## 4. Current live-site truth and anti-staleness rule

Fresh homepage verification on 2026-08-31 shows:

- title: `Eksamio — образовательная платформа для персонального обучения и подготовки к экзаменам`;
- hero: `Подготовка к ЕГЭ: проверьте знания и выберите, что улучшить`;
- public CTAs for demos and trainers;
- Russian, Basic Mathematics, Profile Mathematics and Physics presented with 2022–2026 year availability on the freshly fetched homepage;
- additional live demo entries for Social Studies, Chemistry, Biology and History;
- Russian EGE trainer / thematic-practice entry is visible.

Important: some crawler snapshots of inner `/ege/` and `/ege/demoversii/` routes may lag behind the live homepage. Do not use an older crawl as proof that current public tabs are missing. Recheck the actual route freshly before changing the site.

## 5. Acquisition starts with LIVE product — NEW P0 workstream

Authority:

`eksamio-learning-engine/28-ACQUISITION-METRIKA-DIRECT-v0.1.md`

Hard rule:

**traffic and measurement start together with the public product, not after the full Pro launch.**

For a newly released high-value learner surface, acquisition status should become:

- `LIVE_MEASURED`;
- `LIVE_MEASUREMENT_BLOCKED:<reason>`;
- `READY_TO_PUBLISH_MEASURED`.

A live valuable surface should not remain unmeasured by default.

Initial pre-Pro acquisition funnel:

`Direct click -> LIVE Eksamio surface -> demo/trainer start -> meaningful completion -> next learning action -> return`

Primary optimization is **not CTR and not raw visits**. Primary pre-Pro quality conversions are meaningful learner actions.

## 6. Yandex Metrika — exact current contract

Live Eksamio counter:

`110348386`

Canonical goal/event IDs:

- `eks_demo_open` — diagnostic click/open signal only;
- `eks_demo_start` — real attempt started;
- `eks_demo_complete` — completed demo/result; **primary pre-Pro conversion**;
- `eks_result_to_practice` — result led to practice;
- `eks_trainer_open` — diagnostic open signal;
- `eks_trainer_start` — real trainer session started;
- `eks_trainer_meaningful` — defined useful bounded practice completed; **primary pre-Pro conversion**;
- `eks_return_learning` — return learning signal;
- `eks_pro_intent` — future commercial-intent signal;
- `eks_purchase` — future successful paid entitlement signal after payment E2E admission.

Privacy rule: no phone, e-mail, learner answer text, free text or other personal data goes in Metrika goal parameters. Only bounded non-sensitive product dimensions are allowed.

Prepared implementation:

- `tilda-ready/eksamio-metrika-events-v0.1.js` — allowlisted browser event bridge for counter `110348386`;
- `eksamio-learning-engine/tools/eksamio_metrika_goals_setup.py` — read-first/idempotent Management API setup; verifies counter/domain before creating only missing goals.

Secure token source already used by the other Yandex API contour:

- Keychain service: `ProfitEngine-YandexOAuth-Read`;
- Keychain account: `profit-engine`.

These are **references only**, not secret values. OAuth/token values must never be copied into GitHub, chat, issues or logs.

### Metrika truth at this snapshot

- counter on live site: **CONFIRMED**;
- goal contract/code: **READY IN REPO**;
- actual live API application of all canonical goals: **NOT YET PROVEN IN THIS CHAT**;
- event bridge committed: **YES**;
- event bridge published on every required live Tilda/product surface and deep runtime events verified: **NOT YET PROVEN**.

Never relabel prepared code as live measurement without provider/read-back evidence.

## 7. Yandex Direct — exact account binding

Authority:

`OWNER-DECISION-EKSAMIO-YANDEX-DIRECT-ACCESS-2026-08-31.md`

Exact roles:

- technical API/OAuth operator: `reklamadymova`;
- managed advertiser where Eksamio campaigns must live: `dymova`;
- Direct managed requests use the exact advertiser target `Client-Login: dymova` where required;
- do not confuse, alias or silently substitute these two accounts.

The existing secure OAuth contour is reused. Eksamio must not create a second independent OAuth identity unless the existing manager binding ceases to satisfy provider/security requirements.

Eksamio acquisition state, conversions and economics remain isolated from Dilivox even though the technical API operator is shared.

## 8. First Direct campaign candidate — prepared, not spending

Authority:

`eksamio-learning-engine/29-DIRECT-FIRST-SEARCH-CAMPAIGN-CANDIDATE-v0.1.md`

Campaign identity:

`EKSAMIO_FREE_EGE_SEARCH_2026`

Initial design:

- geography: Russia;
- first wave: high-intent Search;
- four initial subject groups: Russian EGE, Profile Mathematics EGE, Basic Mathematics EGE, Physics EGE;
- each group lands directly on the corresponding live subject demo route instead of a generic page;
- Metrika counter: `110348386`;
- canonical UTM:
  `utm_source=yandex&utm_medium=cpc&utm_campaign={campaign_id}&utm_content={source_type}.{ad_id}.{gbid}.{device_type}&utm_term={keyword}`;
- `yclid` must remain intact;
- no claims about unfinished Pro/payment/identity/Tutor capabilities.

Prepared API creator:

`eksamio-learning-engine/tools/eksamio_direct_inert_campaign_setup.py`

Safety design:

- current Direct endpoint: `/json/v501`;
- current Unified Campaign / ResponsiveAd path;
- `Search = SERVING_OFF`;
- `Network = SERVING_OFF`;
- therefore the candidate can be created inertly with spend impossible until a separate deliberate strategy/budget activation.

### Direct truth at this snapshot

- account-role contract: **FIXED**;
- campaign/group/keyword/creative candidate: **READY IN REPO**;
- live Direct `Campaigns.add -> AdGroups.add -> Keywords.add -> Ads.add` apply: **NOT YET PROVEN IN THIS CHAT**;
- campaign spending: **0 / NOT AUTHORIZED**;
- no Eksamio budget has yet been fixed in this authority snapshot.

No paid traffic may start without an explicit Eksamio advertising budget/limit from the Owner.

## 9. On-site advertising / RSYA — NEW permanent decision

**No third-party advertising blocks are placed on Eksamio.**

This is not merely a temporary “until Pro” decision.

Prohibited on-site monetization includes RSYA/YAN display blocks and equivalent third-party ad-network blocks on:

- homepage;
- demo catalogue and demo attempts;
- result flows;
- trainers/practice;
- Pro;
- Tutor;
- checkout/payment;
- other learner-critical surfaces.

Direct acquisition (`Yandex Direct -> Eksamio`) is a completely separate mechanism and remains allowed under budget/measurement gates.

Eksamio optimizes for learner value and eventual own-product conversion, not for monetizing learner attention with third-party ads.

## 10. Russian full-subject P0 — fresh PR truth

Active closure PR:

`#164 — SEP1 Russian subject closure: complete object accounting + finite semantic acceptance packet`

Snapshot verified 2026-08-31:

- PR state: **OPEN / DRAFT / NO-GO**;
- admission units accounted: **1325 / 1325**;
- official requirements accounted: **1400 / 1400**;
- exact object-bound accepted component sets: **22 units / 22 requirements**;
- remaining without accepted component set: **1294 units / 1369 requirements**;
- unique accepted canonical `school-*` refs: **78**;
- accepted bounded `ru-*`: **75 total = 66 subject + 9 route**;
- finite semantic review groups: **74**;
- modules with reviewed accounting: **16 / 16**;
- false exact-mastery admissions: **0**.

Critical safety correction already made:

- a prior broad batch fan-out that claimed +48 exact bindings was rejected by Central Brain;
- shared broad `normalized_meaning`, same document/module or nearby code is **not enough** to reuse exact canonical ownership;
- future batching must prove exact source/content identity or a narrower authority-grade equivalence relation;
- false fan-out did not survive as canonical launch truth.

Current launch truth:

`russian_content = BLOCKED_SUBJECT / NO-GO`

Do not merge #164 while this remains true.

## 11. Paid Russian launch chain — still authoritative

The paid launch is complete only when one exact production release proves the whole closed loop:

`public entry -> identity -> purchase -> receipt -> entitlement -> Russian learning -> PEIS state -> practice -> Tutor text/voice -> independent verification -> persisted progress -> return login -> refund/revoke`

Primary dependency chain:

`FULL_RUSSIAN_TRUTH -> WORKING_RUSSIAN_PRODUCT -> YANDEX_PRODUCTION -> REAL_IDENTITY -> REAL_PAYMENT -> REAL_TUTOR -> END_TO_END_ACCEPTANCE -> PUBLIC_GO_LIVE`

Launch blocker classes remain:

1. Russian subject/content acceptance;
2. Russian PEIS/product live assembly;
3. Tutor production integration;
4. Yandex production infrastructure;
5. identity delivery;
6. payment/receipt/entitlement;
7. legal/privacy/operator acceptance;
8. exact-release production E2E + Owner go-live.

Progressive free publication and acquisition do **not** waive these paid launch gates.

## 12. Commercial decisions preserved

First market: Russia; initial paid cohort: grades 10–11 / EGE Russian.

Paid product decisions already fixed:

- Pro access shelf: 30 days and 90 days;
- no auto-renewal;
- no saved-card dependency;
- SBP + card required for payment launch;
- NPD receipt required;
- separate paid full AI analysis is a product option and may be progressively commercialized when productized;
- base Pro contains a small AI-session package; additional packages may be sold; unused quotas do not roll over indefinitely;
- anonymous free demo remains allowed;
- registration is not required merely to use free demos;
- guest paid analysis may use one contact for receipt/access;
- free Pro trial is not allowed to create an uncontrolled expensive Tutor entitlement;
- parent functionality is later/progressive and follows separate privacy boundaries.

Do not invent launch prices/SKUs in code. Exact prices/quotas/SKU identities must be explicit server-owned launch configuration before checkout.

## 13. Tutor / AI provider policy — preserve provider neutrality

Core architectural invariant:

**AI brain and voice layer are separate provider-neutral boundaries.**

A Tutor brain may be one provider while STT/TTS uses Yandex SpeechKit.

Russian voice layer:

- Yandex SpeechKit is the primary Russian speech layer;
- accepted Lera voice profile: `neutral / 1.04 / 0 Hz / marked pauses`;
- learner audio persistence must remain exactly **0**;
- voice and text are two interfaces of the same Tutor/learning episode, not separate Tutors.

Brain shortlist for the real pedagogical Eksamio Tutor comparison must preserve:

- OpenAI;
- Qwen;
- DeepSeek;
- Yandex.

This order is **not a predeclared quality ranking**. Final provider choice is based on Eksamio's own comparative pedagogical test, reliability, production fit and cost/latency evidence.

Current fast benchmark PR:

`#172 — P0 Tutor: OpenAI + Yandex fast text/voice acceptance`

Snapshot:

- OPEN / DRAFT;
- fast private benchmark intentionally compares OpenAI and Yandex only in the immediate runner;
- same Yandex SpeechKit voice boundary used for fair voice comparison;
- production realtime SpeechKit streaming remains a separate gate;
- #172 does **not** erase Qwen/DeepSeek from the broader real Tutor shortlist.

No Tutor provider may become canonical solely because one benchmark harness currently contains only two providers.

## 14. Production/privacy invariants preserved

- Yandex Cloud Russia is the primary production runtime target for the Russian launch.
- Canonical learner state, PEIS and entitlements are server-owned.
- Secrets never live in Git/client/chat/logs.
- Learner audio persistence = `0`.
- Production runtime must not depend on GitHub availability.
- Google Drive may be source archive but not learner runtime dependency.
- Real provider, payment, SMS/e-mail and paid AI operations require their explicit bounded gates and evidence.

## 15. Current owner-action boundary

### Nothing to send

The Owner must **not** send OAuth tokens, API keys, passwords, Keychain values or other secrets into ChatGPT, GitHub or Codex text.

### What is needed from the Owner for acquisition

To start **paid Direct traffic**, one owner decision is still mandatory:

`EKSAMIO_WEEKLY_DIRECT_BUDGET_RUB = <explicit amount>`

Without that number, campaign preparation/measurement may continue, but spend remains `0`.

A live provider apply also requires execution in the trusted local environment that can read the existing macOS Keychain entry. This is a secure local execution requirement, not a request to disclose the token.

### What is needed from the Owner for Tutor acceptance

When the human Tutor benchmark runner is ready and its CI/authority are accepted, a real learner/person should execute the fixed comparison scenario. This can be delegated to the Owner's son as previously planned. Do not run an uncontrolled paid provider test before the bounded scenario and explicit authorization.

### What does NOT need an Owner action right now

The Owner does not need to manually redesign the site, duplicate OAuth identities, create a new Metrika counter, create an RSYA block setup, or copy credentials between projects.

Central Brain/Codex should continue repository work on the critical path without waiting for those nonexistent tasks.

## 16. Immediate next critical-path actions after recovery

In order:

1. Re-read current `main` and #164 exact HEAD; continue **exact** Russian subject closure without broad/fuzzy fan-out.
2. Continue working Russian PEIS/product live assembly in parallel where accepted subject truth already permits it.
3. Complete bounded Tutor human/provider acceptance and production integration; preserve provider-neutral brain/voice separation and audio persistence `0`.
4. Close Yandex production, identity, payment/receipt/entitlement and production E2E gates.
5. In parallel, finish Metrika instrumentation/read-back for already-live free surfaces.
6. Prepare/apply the Direct campaign only in inert/non-spending state until the Owner fixes the weekly budget; after budget, activate a bounded Search wave and optimize on meaningful learner completion, not CTR.
7. Every newly accepted learner-facing scope that is production-ready must be opened publicly and measured instead of being held until the whole platform is finished.

## 17. Files added/changed by the 2026-08-31 release/acquisition decisions

Read these first when recovering this workstream:

- `eksamio-learning-engine/OWNER-DECISION-PROGRESSIVE-PUBLIC-RELEASE-2026-08-31.md`;
- `eksamio-learning-engine/00-PRODUCT-MASTERPLAN.md` v1.5;
- `eksamio-learning-engine/OWNER-DECISION-EKSAMIO-YANDEX-DIRECT-ACCESS-2026-08-31.md`;
- `eksamio-learning-engine/28-ACQUISITION-METRIKA-DIRECT-v0.1.md`;
- `eksamio-learning-engine/29-DIRECT-FIRST-SEARCH-CAMPAIGN-CANDIDATE-v0.1.md`;
- `tilda-ready/eksamio-metrika-events-v0.1.js`;
- `eksamio-learning-engine/tools/eksamio_metrika_goals_setup.py`;
- `eksamio-learning-engine/tools/eksamio_direct_inert_campaign_setup.py`;
- this handoff file.

## 18. No-regression summary

Do not regress these owner decisions:

- GitHub is source of truth for code/governance; live site is source of truth for what learners see now.
- Ready learner value is published progressively.
- Measurement begins with public learner value.
- Direct acquisition is allowed; on-site third-party advertising is not.
- Direct operator = `reklamadymova`; advertiser = `dymova`.
- Metrika counter = `110348386`.
- No paid Direct spend without explicit Eksamio budget.
- No secrets copied into repository/chat.
- Tutor remains provider-neutral; voice and brain are separable.
- Tutor real shortlist includes OpenAI, Qwen, DeepSeek and Yandex; no predeclared ranking.
- Yandex SpeechKit/Lera is the Russian speech-layer baseline; learner audio persistence = 0.
- Full Russian exact subject truth remains fail-closed; broad semantic shortcuts are forbidden.
- Paid Russian go-live still requires the complete production closed loop and Owner GO.
