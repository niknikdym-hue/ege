# Eksamio — Current Brain Handoff / Recovery Authority v2

**Status:** CURRENT RECOVERY / CONTINUATION AUTHORITY  
**Date:** 2026-08-31  
**Repository:** `niknikdym-hue/ege`  
**Supersedes for continuation:** `00A-CURRENT-BRAIN-HANDOFF-2026-08-31.md`  
**Product authority:** `00-PRODUCT-MASTERPLAN.md` v1.5  
**Operational board:** `00B-PROJECT-PRIORITIES-CURRENT.md`

This file is the first recovery document to read after current `main`. The earlier handoff remains historical evidence; this v2 contains all later owner decisions and growth-system additions from 2026-08-31.

## 0. Recovery protocol

1. Read current GitHub `main`; never assume the SHA in chat is current.
2. Read this file, then `00-PRODUCT-MASTERPLAN.md` and `00B-PROJECT-PRIORITIES-CURRENT.md`.
3. For public-site truth, freshly verify `eksamio.ru`; never infer current learner-visible state from GitHub or stale crawl snapshots.
4. Chat is not authority. New owner decisions affecting product, release, privacy, monetization, providers or rollout must be committed.
5. `GitHub outage != Eksamio outage` remains a hard runtime invariant.

## 1. Product and launch identity

Eksamio is a Personal Exam Intelligence System (PEIS), not a set of unrelated demos and not a generic exam chatbot.

Learning loop:

`DIAGNOSE -> MODEL -> PRIORITIZE -> TEACH/PRACTICE -> VERIFY -> RETAIN -> REASSESS -> REPLAN`

First paid launch: **Eksamio Pro — Russian**.

Subject order:

1. Russian;
2. Mathematics (profile + basic routes);
3. Physics.

## 2. Progressive Public Release

Authority: `OWNER-DECISION-PROGRESSIVE-PUBLIC-RELEASE-2026-08-31.md` and masterplan v1.5.

Hard rule:

- accepted, safe, truthful learner-facing value is published when its own gates pass;
- it does not wait for unrelated Pro/payment/Tutor blockers;
- `DONE` without `LIVE` or explicit blocker is not operationally complete for a public learner surface;
- unfinished paid capability remains hidden/fail-closed.

Acquisition/measurement starts with `LIVE` product, not after the whole platform is finished.

## 3. Current growth architecture — one system

Authority: `31-ACQUISITION-CONTROLLER-SEO-v0.1.md`.

Canonical commercial loop:

`SEO + Direct + referral -> Eksamio -> Metrika -> server-owned commercial truth -> Acquisition Controller -> channel/budget/landing decisions`

North star:

**Acquire verified paid Pro customers at healthy CAC, not cheap traffic.**

After Pro launch:

`CAC_paid = attributable paid acquisition spend / server-confirmed new paid Pro customers`

Free demo/trainer actions remain useful leading signals but never replace verified purchase economics.

## 4. Yandex Metrika — current canonical measurement

Counter: **`110348386`**.

Authority: `30-METRIKA-GROWTH-MEASUREMENT-v0.2.md`.

### Learning goals

- `eks_demo_open`
- `eks_demo_start`
- `eks_demo_complete`
- `eks_result_to_practice`
- `eks_trainer_open`
- `eks_trainer_start`
- `eks_trainer_meaningful`
- `eks_return_learning`

### Commercial goals

- `eks_pro_offer_view`
- `eks_pro_intent`
- `eks_checkout_start`
- `eks_purchase`
- `eks_entitlement_active`
- `eks_refund`

### Referral goals

- `eks_referral_visit`
- `eks_referral_qualified`
- `eks_referral_purchase_verified`
- `eks_referral_reward_granted`
- `eks_referral_reward_reversed`

Total canonical goal registry: **19**.

Tool: `tools/eksamio_metrika_goals_setup.py`.

The tool:

- reads the existing counter first;
- verifies `eksamio.ru` identity;
- inventories existing goals;
- preserves all existing/user-created goals;
- creates only missing canonical JavaScript-event goals;
- fails on duplicate canonical event IDs;
- reads back after apply.

### Server-only conversion truth

The following can never be authoritative client-side events:

- `eks_purchase`;
- `eks_entitlement_active`;
- `eks_refund`;
- `eks_referral_qualified`;
- `eks_referral_purchase_verified`;
- `eks_referral_reward_granted`;
- `eks_referral_reward_reversed`.

They originate from backend payment/entitlement/referral truth and are attributed to Metrika with retained `ClientID`, `yclid`, `PurchaseId` or other admitted identifier.

Only successfully matched server/offline conversions may become Direct optimization evidence.

Browser bridge: `tilda-ready/eksamio-metrika-events-v0.1.js`; it intentionally excludes all server-only commercial/reward events.

## 5. Yandex Direct — exact roles and sequence

Authority: `OWNER-DECISION-EKSAMIO-YANDEX-DIRECT-ACCESS-2026-08-31.md`.

- technical API/OAuth operator: `reklamadymova`;
- managed advertiser: `dymova`;
- Eksamio campaign data/economics stay isolated from Dilivox;
- secure OAuth secret values are never copied to repo/chat/logs.

First campaign candidate: `EKSAMIO_FREE_EGE_SEARCH_2026`.

Authority: `29-DIRECT-FIRST-SEARCH-CAMPAIGN-CANDIDATE-v0.1.md`.

First acquisition channel is **Yandex Search**, not RSYA-only.

Initial subject groups:

- Russian EGE;
- Profile Mathematics EGE;
- Basic Mathematics EGE;
- Physics EGE.

First provider creation state:

- Search `SERVING_OFF`;
- Network `SERVING_OFF`;
- spend impossible;
- campaign may be created/moderated before a budget is authorized.

Correct rollout:

1. apply/read back canonical Metrika goals;
2. verify live event instrumentation;
3. create/read back inert Direct Search campaign;
4. Owner fixes exact Eksamio advertising budget/cap;
5. activate bounded Search learning mode;
6. collect query -> learning -> commercial evidence;
7. after Pro, optimize primarily on verified purchase/CAC/value;
8. add separate Network retargeting only after evidence;
9. cold Network scaling only if purchase economics justify it.

## 6. Programmatic Acquisition Controller

Direct is not managed indefinitely by hand.

The controller reads:

- Direct spend/campaign/query data;
- Metrika source/goals/revenue;
- server-owned purchase/refund/entitlement truth;
- SEO landing registry;
- referral ledger;
- Owner budget policy.

It may eventually, inside admitted bounds:

- add evidence-backed negatives;
- pause wasteful keywords/groups;
- promote converting queries;
- redistribute approved budget;
- adjust CPA/CRR/bid strategy only after enough evidence;
- create retargeting cohorts;
- stop anomalous spend.

It may never exceed the Owner-approved total cap or optimize to CTR/cheap clicks as the business objective.

## 7. SEO — first-class growth channel

SEO is part of the same funnel, not a separate content exercise.

Every important indexable landing should have:

- unique truthful title;
- useful meta description;
- one correct H1;
- canonical URL;
- correct robots/indexability;
- sitemap membership;
- internal linking;
- stable mobile performance;
- valid structured data where truthful;
- no thin keyword doorway pages.

Priority SEO architecture:

`homepage -> EGE hub -> subject -> year/demo/topic -> result/practice -> Pro when live`

Direct and SEO reuse the same canonical landing taxonomy and Metrika downstream goals.

## 8. Referral growth system

Authorities:

- `OWNER-DECISION-REFERRAL-AFTER-PAID-PURCHASE-2026-08-31.md`;
- `32-REFERRAL-GROWTH-SYSTEM-v0.1.md`.

Hard invariant:

**No verified paid purchase = no referral reward.**

Canonical lifecycle:

`ATTRIBUTED -> QUALIFYING_ORDER_CREATED -> PAYMENT_VERIFIED -> ENTITLEMENT_GRANTED -> PENDING_REWARD -> GRANTED`

Refund/abuse path supports deterministic `REVERSED`.

Must block:

- self-referrals;
- duplicate reward from one payment/order;
- webhook replay;
- refund/rebuy cycling;
- referral-code switching after qualifying purchase;
- fabricated client-side referral state.

Reward type/value remains configuration until Owner approves final economics. Possible product-safe forms include bounded Pro time, bounded Tutor/AI credits or bounded future-purchase credit; no cash payout is implied.

## 9. No on-site advertising blocks

Permanent decision:

**Eksamio contains no RSYA/YAN or other third-party ad-network blocks.**

This applies to homepage, demos, results, trainers, Pro, Tutor, checkout and other learner-critical surfaces.

Yandex Direct acquisition into Eksamio is separate and allowed under budget/measurement gates.

## 10. Eksamio Owner Console — local Mac dashboard

Authority: `33-OWNER-CONSOLE-v0.1.md`.

Target: a local macOS owner application/panel with aggregate business analytics.

First release is **read-only**.

Default screen contains only six headline KPIs:

1. visitors;
2. meaningful learners;
3. checkout starts;
4. verified paid Pro customers;
5. Pro revenue;
6. paid CAC.

Below that:

- one funnel: `visit -> meaningful learning -> Pro intent -> checkout -> verified purchase`;
- one channel table: `Organic SEO / Direct Search / Referral / Other`;
- one trend chart: paid customers + CAC;
- maximum three prioritized alerts.

No dashboard clutter, no raw log stream, no PII.

Data sources:

- Metrika `110348386`;
- Direct advertiser `dymova` via `reklamadymova`;
- server payment/order/entitlement/refund truth;
- referral ledger;
- canonical live/SEO landing registry.

Normal dashboard runtime must not depend on GitHub or ChatGPT.

## 11. Russian full-subject current gate

PR #164 remains the current Russian subject closure line until superseded by fresher GitHub evidence.

Last authority snapshot before this v2:

- 1325 / 1325 admission units accounted;
- 1400 / 1400 official requirements accounted;
- exact object-bound accepted component sets: 22 / 22;
- remaining: 1294 units / 1369 requirements;
- 74 finite semantic review groups;
- 16 / 16 modules;
- false exact-mastery admissions: 0;
- status: `BLOCKED_SUBJECT / NO-GO`.

Always re-read PR #164 before acting because it is actively moving.

No broad `normalized_meaning` fan-out is allowed as exact semantic acceptance.

## 12. Tutor policy preserved

AI brain and voice are provider-neutral separate layers.

Tutor brain shortlist for the real pedagogical test:

- OpenAI;
- Qwen;
- DeepSeek;
- Yandex.

Order is not a quality ranking.

Russian voice layer:

- Yandex SpeechKit primary;
- Lera;
- neutral / 1.04 / 0 Hz / marked pauses;
- learner audio persistence exactly 0.

Text and voice are interfaces of one Tutor/learning episode.

## 13. Paid launch chain preserved

Paid Russian Pro launch still requires one exact production release proving:

`public entry -> identity -> purchase -> receipt -> entitlement -> Russian learning -> PEIS -> practice -> Tutor text/voice -> independent verification -> persisted progress -> return login -> refund/revoke`

Progressive free publication, SEO, Metrika or Direct preparation do not waive paid launch gates.

## 14. Current owner-action boundary

Owner does not send secrets/tokens/passwords into chat/GitHub.

Immediate acquisition work can proceed without spend:

- Metrika inventory/apply;
- event instrumentation verification;
- inert Direct campaign creation/read-back;
- SEO strengthening;
- Owner Console implementation planning.

Paid Search activation requires explicit Eksamio budget/cap.

Referral production reward granting requires explicit reward economics plus admitted payment/refund/anti-abuse runtime.

## 15. Exact continuation order

If this conversation disappears, continue in this order unless fresher GitHub evidence changes the critical path:

1. read current `main` and PR #164/#172;
2. finish live Metrika goal inventory/apply and event verification;
3. create/read back inert Direct Search campaign;
4. continue Russian subject closure and paid-launch blockers in parallel;
5. strengthen SEO landing/structured-data/internal-linking layer;
6. build Owner Console read-only v0.1;
7. after explicit budget, activate bounded Search;
8. after verified Pro purchases exist, optimize Direct/controller to paid CAC/value;
9. enable referral rewards only after server payment + anti-abuse gates;
10. Network retargeting, then cold Network scale only if purchase economics justify it.

**Business truth:** Eksamio growth is successful when it acquires and retains real paid learners at healthy economics while preserving real educational value.