# Eksamio Acquisition — Metrika + Yandex Direct v0.1

**Status:** ACTIVE P0 ACQUISITION CONTRACT  
**Date:** 2026-08-31  
**Site:** `https://eksamio.ru`  
**Metrika counter:** `110348386` (verified on live site)  
**Direct technical API/operator:** `reklamadymova`  
**Direct managed advertiser:** `dymova`

## 1. Operating rule

Traffic and measurement start with the product, not after the whole platform is finished.

When a learner-facing surface becomes `LIVE` under the Progressive Public Release invariant, it must also become measurable in Metrika and, when a suitable acquisition intent exists, eligible as a Direct landing page.

`LIVE` without measurement is incomplete for acquisition purposes.

Paid traffic may promote only capabilities that are actually live. Unfinished Pro/payment/identity/Tutor capabilities must not be advertised as available.

## 2. Current acquisition objective

Before Pro is publicly available, Direct traffic is used to acquire real learners into already-live free value and build conversion/learning evidence.

Initial funnel:

`Direct click -> live Eksamio landing -> demo/trainer start -> meaningful completion -> next learning action -> return`

The first optimization target is not CTR and not raw pageviews. It is completion of a useful learner action.

## 3. Metrika event contract

Counter: `110348386`.

Canonical goal/event IDs:

| Goal ID | Meaning | Role |
| --- | --- | --- |
| `eks_demo_open` | user opened/clicked into a demo route | diagnostic only |
| `eks_demo_start` | real demo attempt started | funnel |
| `eks_demo_complete` | demo attempt completed and result produced | **primary pre-Pro conversion** |
| `eks_result_to_practice` | result led to trainer/practice | quality conversion |
| `eks_trainer_open` | trainer route opened | diagnostic only |
| `eks_trainer_start` | real trainer session started | funnel |
| `eks_trainer_meaningful` | meaningful bounded practice completed | **primary pre-Pro conversion** |
| `eks_return_learning` | learner returned for another study session | retention signal |
| `eks_pro_intent` | user explicitly entered future Pro offer/checkout intent | future commercial funnel |
| `eks_purchase` | successful paid entitlement after payment E2E is admitted | future primary commercial conversion |

Rules:

- pageview/click goals are never treated as equivalent to learning completion;
- `eks_demo_complete` requires a completed attempt/result, not merely opening the page;
- `eks_trainer_meaningful` must be emitted only by the trainer/product logic after a defined useful practice unit, not by elapsed page time alone;
- no contact data, learner answers, free text, phone, e-mail or other personal data may be sent in Metrika goal parameters;
- parameters may contain non-sensitive product dimensions such as subject, year, route, task family, source surface and anonymized release/version identifiers.

## 4. Direct attribution

The Metrika counter must be attached to every Eksamio Direct campaign. `yclid` must remain intact on landing URLs.

Canonical campaign URL parameters:

`utm_source=yandex&utm_medium=cpc&utm_campaign={campaign_id}&utm_content={source_type}.{ad_id}.{gbid}.{device_type}&utm_term={keyword}`

Direct dynamic parameters are used only for attribution; they do not become learner identity.

## 5. First paid traffic wave

Phase A starts with high-intent Search traffic to already-live free surfaces. Initial subject/ad-group boundaries:

1. Russian EGE — demo + Russian practice/trainer path;
2. Mathematics profile — live demo route;
3. Mathematics basic — live demo route;
4. Physics — live demo route.

Other live subjects may be added after landing/measurement parity is confirmed.

Do not combine subject intent into a generic landing when a direct subject landing exists.

Initial campaign naming contract:

`EKSAMIO_FREE_EGE_SEARCH_2026`

Campaign is created in managed advertiser `dymova`; API/operator identity remains `reklamadymova`.

## 6. Optimization sequence

Cold start:

1. collect clean Search traffic and goal evidence;
2. verify `yclid`, UTM, counter and goal attribution;
3. measure `click -> start -> complete -> next learning action` per subject;
4. exclude clearly irrelevant queries;
5. only after sufficient real conversion evidence consider conversion-optimized bidding and YAN/network expansion.

Primary pre-Pro optimization goals:

- `eks_demo_complete`;
- `eks_trainer_meaningful`.

Secondary quality signals:

- `eks_result_to_practice`;
- `eks_return_learning`.

## 7. Spend boundary

No paid delivery begins without an explicit Eksamio advertising budget/limit.

Before that number is fixed, the allowed state is:

`MEASUREMENT_LIVE + CAMPAIGN_READY/PAUSED + SPEND=0`.

Once the Owner fixes the budget, campaign activation is permitted within that exact limit. Eksamio spend/economics must remain isolated from Dilivox even though the same technical Direct operator is reused.

## 8. Advertising-block policy

Acquisition advertising (Direct -> Eksamio) and on-site ad monetization are separate decisions.

The Eksamio homepage is permanently ad-block-free. Learner-critical demo/trainer/Pro/Tutor flows are not to be polluted with third-party display blocks as part of this acquisition launch. The current objective is learner acquisition, learning outcome and future Pro conversion, not monetizing learner attention with external ads.

## 9. Publication gate for measurement

For a newly released learner surface, publication status for acquisition is one of:

- `LIVE_MEASURED` — live and required Metrika events verified;
- `LIVE_MEASUREMENT_BLOCKED:<reason>` — live but exact instrumentation blocker exists;
- `READY_TO_PUBLISH_MEASURED` — accepted, instrumentation ready, waiting only for publication.

A new high-value public surface should not remain unmeasured by default.
