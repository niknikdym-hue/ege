# Eksamio — Current Brain Handoff / Recovery Authority v3

**Status:** CURRENT RECOVERY / CONTINUATION AUTHORITY  
**Date:** 2026-09-01  
**Repository:** `niknikdym-hue/ege`  
**Main before this handoff branch:** `4bb8e2584396f5871af151259e494dc919011187`  
**Supersedes for continuation:** `00A-CURRENT-BRAIN-HANDOFF-v2-2026-08-31.md`  
**Product authority:** `00-PRODUCT-MASTERPLAN.md` v1.5  
**Operational board:** `00B-PROJECT-PRIORITIES-CURRENT.md`

This is the first recovery file to read after refreshing current `main`. Chat is never the source of truth.

## 0. Recovery protocol

1. Refresh GitHub `main`; never trust a SHA copied from an earlier chat.
2. Read this file, `00-PRODUCT-MASTERPLAN.md`, and `00B-PROJECT-PRIORITIES-CURRENT.md`.
3. Re-read active launch-critical PRs before acting, especially Russian subject closure and Tutor acceptance.
4. Freshly verify learner-visible `eksamio.ru` when public-site truth matters.
5. Never move secrets/tokens/passwords into chat, GitHub, logs, HTML or test fixtures.
6. `GitHub outage != Eksamio outage` remains a hard runtime invariant.

## 1. Product / launch identity

Eksamio is a Personal Exam Intelligence System (PEIS).

Learning loop:

`DIAGNOSE -> MODEL -> PRIORITIZE -> TEACH/PRACTICE -> VERIFY -> RETAIN -> REASSESS -> REPLAN`

First paid launch remains **Eksamio Pro — Russian**.

Progressive Public Release remains active: accepted, safe, truthful free learner value may publish without waiting for unrelated paid/Tutor blockers, while incomplete paid capability remains hidden/fail-closed.

## 2. Growth system — one commercial loop

Canonical loop:

`SEO + Direct + referral -> Eksamio -> Metrika -> server-owned commercial truth -> Acquisition Controller -> channel/budget/landing decisions`

North star:

**Acquire and retain verified paid Pro learners at healthy economics while preserving real educational value.**

After paid launch:

`CAC_paid = attributable paid acquisition spend / server-confirmed new paid Pro customers`

Free demo/trainer conversion is a leading signal, never a substitute for verified paid economics.

## 3. Yandex Metrika — code/contract state vs live state

Counter: `110348386`.

Authority: `30-METRIKA-GROWTH-MEASUREMENT-v0.2.md`.

Canonical registry contains **19 goals**:

- 8 learning;
- 6 commercial;
- 5 referral.

Tool: `tools/eksamio_metrika_goals_setup.py`.

Implemented in repository:

- counter/domain identity check;
- inventory before mutation;
- preservation of existing/user-created goals;
- create-only-missing behavior;
- duplicate canonical ID failure;
- read-back after apply;
- server-only goal classification;
- browser bridge excludes authoritative purchase/entitlement/refund/referral-reward events.

Browser bridge: `tilda-ready/eksamio-metrika-events-v0.1.js`.

**Live truth is not yet allowed to be overstated.** The current repository authority says actual provider goal inventory/apply still requires execution with the protected local OAuth token plus read-back evidence. Live browser event instrumentation also requires real surface verification.

Server-owned authoritative events include `eks_purchase`, entitlement, refund, referral qualification/purchase/reward grant/reversal. A browser click can never mint those truths.

## 4. Yandex Direct — safe pre-spend state

Technical API/OAuth operator: `reklamadymova`.  
Managed advertiser: `dymova`.

First campaign candidate: `EKSAMIO_FREE_EGE_SEARCH_2026`.

Implemented tools:

- `tools/eksamio_direct_inert_campaign_setup.py`;
- `tools/eksamio_direct_inert_campaign_reconcile.py`.

The reconciler exists specifically so interrupted provider setup can be resumed/read back without duplicating the campaign.

Hard boundary before explicit Owner budget authority:

- Search serving OFF;
- Network serving OFF;
- no spend;
- no autonomous budget activation.

Provider execution/read-back still requires the protected local credentials and must be evidenced from the actual advertiser state.

## 5. SEO

SEO remains a first-class acquisition channel under `31-ACQUISITION-CONTROLLER-SEO-v0.1.md`.

Priority structure:

`homepage -> EGE hub -> subject -> year/demo/topic -> result/practice -> Pro when live`

Important live landings require truthful title/meta/H1/canonical/indexability/sitemap/internal links/mobile quality and truthful structured data. No thin doorway-page strategy.

Direct and SEO reuse the same landing taxonomy and downstream Metrika goals.

## 6. Referral

Authorities:

- `OWNER-DECISION-REFERRAL-AFTER-PAID-PURCHASE-2026-08-31.md`;
- `32-REFERRAL-GROWTH-SYSTEM-v0.1.md`.

Hard invariant:

**No verified paid purchase = no referral reward.**

Reward economics remain Owner configuration. Production reward granting must wait for admitted payment/refund/anti-abuse runtime.

## 7. No on-site advertising

Permanent product decision remains unchanged:

**Eksamio has no third-party ad-network blocks on learner surfaces.**

Yandex Direct acquisition into Eksamio is separate and allowed only inside the approved measurement/budget gates.

## 8. Eksamio Owner Console — current implementation truth

Product authority: `33-OWNER-CONSOLE-v0.1.md`.  
Implementation authority: `34-OWNER-CONSOLE-IMPLEMENTATION-v0.1.md`.

The first release remains **read-only**.

Executable core now exists:

- `tools/eksamio_owner_console.py`;
- `owner-console/sample-snapshot.json`;
- `tests/test_eksamio_owner_console.py`;
- `.github/workflows/owner-console-v0-1.yml`.

First screen:

1. Visitors;
2. Meaningful learners;
3. Checkout starts;
4. verified Paid Pro customers;
5. refund-adjusted Pro revenue;
6. Paid CAC.

Below:

- one funnel `visit -> meaningful learning -> Pro intent -> checkout -> verified purchase`;
- one channel table `Organic SEO / Yandex Direct Search / Referral / Other-direct`;
- one 30-day trend;
- maximum three alerts.

The renderer normalizes a bounded aggregate snapshot and drops unknown fields rather than echoing raw input. It contains no provider write path and no production mutation endpoint.

**What is not yet complete:** the live local collector that joins actual Metrika + Direct + server payment/refund/entitlement + referral + SEO aggregate truth into the `owner-console-v0.1` snapshot. Until that collector is admitted, do not call the dashboard live-connected.

## 9. Russian subject closure — active NO-GO line

PR #164 is active, draft and must be re-read before every decision.

At the 2026-09-01 recovery check:

- PR head: `14e2af68cc5daa6d9c6f9c0ffb0646d18f1b07de`;
- `1325 / 1325` admission units and `1400 / 1400` official requirements accounted;
- exact object-bound accepted component sets: `23 / 23`;
- remaining without accepted component set: `1293 units / 1368 requirements`;
- finite semantic review groups: `74`;
- modules: `16 / 16`;
- false exact-mastery admissions: `0`;
- launch truth remains `BLOCKED_SUBJECT / NO-GO`.

The PR also contains ongoing narrow CI stale-base repairs. Exact-head jobs were not settled in the last read. No merge signal is implied.

Broad normalized-meaning fan-out remains forbidden as exact component mastery.

## 10. Tutor acceptance — preserve provider-neutral authority

AI brain and voice remain separate provider-neutral layers.

Owner-authoritative brain shortlist for the real pedagogical comparison remains:

- OpenAI;
- Qwen;
- DeepSeek;
- Yandex.

This order is not a quality ranking; final provider choice comes from Eksamio's own pedagogical comparison.

PR #172 is currently a draft fast benchmark implementation focused on OpenAI + Yandex. It must not silently redefine the four-provider owner shortlist or become a product-provider authority by itself. Reconcile it with current Tutor authority before merge/acceptance.

Russian voice remains Yandex SpeechKit primary under the approved voice profile; AI-brain choice is independent of STT/TTS provider.

## 11. Paid launch chain unchanged

Paid Russian Pro launch still requires one exact production release proving:

`public entry -> identity -> purchase -> receipt -> entitlement -> Russian learning -> PEIS -> practice -> Tutor text/voice -> independent verification -> persisted progress -> return login -> refund/revoke`

Growth tooling does not waive any paid-launch gate.

## 12. Exact continuation order

Unless fresher GitHub evidence changes the critical path:

1. refresh `main`; re-read PR #164 and current Tutor acceptance PRs;
2. execute **live Metrika inventory** with protected local OAuth and save redacted evidence;
3. if canonical Metrika goals are missing, run create-only-missing `--apply`, then read back all 19;
4. verify browser-eligible Metrika events on accepted live learner surfaces; never emit server-only commercial/reward truth from browser;
5. run/read back the inert Direct reconciler; keep serving/spend OFF;
6. continue Russian subject closure and other paid-launch blockers in parallel;
7. wire the Owner Console **aggregate collector** to admitted Metrika/Direct/server/referral/SEO truth, keeping the UI read-only;
8. strengthen SEO where current live evidence shows gaps;
9. require explicit Owner budget/cap before bounded Search activation;
10. after verified purchases exist, optimize acquisition primarily to paid CAC/value;
11. enable referral rewards only after payment/refund/anti-abuse gates and Owner reward economics;
12. add retargeting/Network only after Search evidence justifies it.

## 13. Immediate external execution boundary

The following cannot be truthfully marked live-complete from repository code alone:

- Metrika provider inventory/apply/read-back;
- live browser event verification;
- Direct provider campaign read-back;
- real payment/refund/entitlement aggregate feed;
- real referral ledger feed;
- Owner Console live aggregate collector validation.

All such steps require actual provider/runtime evidence. Never replace that evidence with a plan, fixture, sample snapshot or client-side click.

**Business truth:** Eksamio commercial measurement is successful only when server-confirmed paid outcomes, attribution, spend and refund-adjusted value reconcile into one auditable owner view.
