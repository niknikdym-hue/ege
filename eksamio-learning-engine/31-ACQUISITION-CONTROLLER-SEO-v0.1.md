# Eksamio Acquisition Controller + SEO Growth System v0.1

**Status:** ACTIVE PRODUCT / GROWTH ARCHITECTURE  
**Date:** 2026-08-31  
**Site:** `eksamio.ru`  
**Metrika:** `110348386`  
**Direct operator:** `reklamadymova`  
**Direct advertiser:** `dymova`

## 1. Product objective

Eksamio acquisition is one closed system, not three unrelated activities:

`SEO + Direct -> Eksamio -> Metrika -> learner/commercial events -> acquisition controller -> Direct/SEO decisions`

The controller must optimize for the cheapest **qualified future/actual Pro customer**, not for cheap clicks, pageviews or free-demo completions in isolation.

No system can truthfully guarantee that a specific visitor will buy. The operational objective is therefore:

`minimize verified paid-CAC subject to conversion-quality, budget, truthfulness and safety constraints`

The final commercial KPI after Pro launch is verified paid acquisition:

`CAC_paid = attributable Direct spend / server-confirmed new paid Pro customers`

Supporting metrics:

- click -> demo/trainer start;
- start -> meaningful completion;
- completion -> Pro intent;
- Pro intent -> checkout start;
- checkout -> server-confirmed purchase;
- purchase -> active entitlement;
- refund/revoke rate;
- revenue and contribution margin per acquired customer;
- paid conversion by query, campaign, subject, device, geo, landing and cohort.

## 2. Conversion hierarchy

### PRE_PRO / learning phase

Free-learning events are **leading quality signals**, not the final business objective:

- `eks_demo_start`;
- `eks_demo_complete`;
- `eks_result_to_practice`;
- `eks_trainer_start`;
- `eks_trainer_meaningful`;
- `eks_return_learning`.

Paid traffic before Pro must remain bounded. The controller may use these signals to detect obviously bad traffic, but must not learn that “the cheapest demo completion” is the end goal.

### PRO_SPARSE / first commercial evidence

Commercial funnel events become primary:

- `eks_pro_offer_view` — diagnostic only;
- `eks_pro_intent` — qualified commercial interest;
- `eks_checkout_start` — strong leading commercial signal;
- `eks_purchase` — **primary verified paid conversion**;
- `eks_entitlement_active` — server-side post-payment integrity signal;
- `eks_refund` — negative quality/economic signal.

When purchase volume is sparse, the controller may use a multi-goal model with purchase weighted highest and checkout/intent as lower-value leading signals. Free learning events remain diagnostic.

### PRO_MATURE / enough paid conversions

Direct optimization must move to real purchase economics:

- `eks_purchase` / eCommerce purchase as the primary conversion;
- dynamic purchase revenue in RUB;
- target CPA / conversion strategy only when supported by real volume;
- revenue/CRR or Maximum Profit strategy only when purchase value and margin evidence are trustworthy.

Free events must never outrank verified purchase once sufficient purchase data exists.

## 3. Server-confirmed purchase attribution

A click on “buy”, checkout page load or browser redirect is **not** a purchase.

Canonical purchase truth is emitted only after the payment backend verifies the provider result and the exactly-once entitlement grant succeeds.

Attribution contract:

1. Preserve `yclid` and canonical UTM parameters on Direct landing.
2. Capture a bounded acquisition attribution record into the anonymous/guest session without PII leakage.
3. Bind attribution to the server-owned order when checkout is created.
4. After verified payment + entitlement, send the purchase conversion and exact server-owned revenue to Metrika/eCommerce/offline conversion path using the retained attribution identifier where applicable.
5. Do not expose e-mail, phone, learner answer text or payment secrets to Metrika/Direct.
6. Refund/revoke is recorded as a negative economic event for controller reporting; it must not silently leave a false profitable cohort.

This allows Direct to learn from real buyers rather than frontend button presses.

## 4. Direct control modes

### `INERT`

- campaign exists but Search and Network are `SERVING_OFF`;
- spend = 0;
- used for API/read-back/moderation preparation.

### `SEARCH_LEARN`

- Search only;
- bounded weekly spend limit;
- high-intent exact subject/query clusters;
- query report audited frequently;
- no broad cold Network traffic;
- objective: establish clean query -> learning -> commercial evidence.

### `SEARCH_PRO_OPTIMIZE`

- purchase/checkout goals connected;
- budget and CPA constraints active;
- query pruning and expansion driven by paid-conversion evidence;
- device/geo/audience adjustments allowed only from statistically meaningful evidence.

### `NETWORK_RETARGET`

- separate campaign from Search;
- first Network use is retargeting/qualified audience recovery;
- examples: meaningful learner who did not start Pro checkout; checkout starter without verified purchase; returning learner with strong Pro fit.

### `NETWORK_SCALE`

- cold Network expansion only after Search/retargeting conversion evidence is trustworthy;
- never enabled merely to obtain cheaper clicks.

## 5. Programmatic Acquisition Controller

The controller must run read-first and fail-closed.

Inputs:

- Direct campaign/ad-group/keyword/query reports;
- Direct spend/click/impression data;
- Metrika visit, source, goal and revenue data;
- server-owned purchase/refund/entitlement truth;
- canonical SEO landing registry;
- explicit Owner budget and write-authority policy.

Derived metrics:

- spend;
- CPC;
- qualified-learning rate;
- Pro-intent rate;
- checkout rate;
- purchase CVR;
- paid CAC;
- revenue per click/visit/customer;
- refund-adjusted revenue;
- contribution margin where available;
- query/landing/device/geo/cohort profitability.

Allowed recommendations/actions when admitted:

- add evidence-backed negative phrases;
- promote converting search queries into explicit keywords/ad-group clusters;
- pause wasteful keywords/ad groups/campaigns;
- adjust bids/CPA/CRR/audience/device coefficients within approved bounds;
- redistribute budget between accepted Search groups;
- create bounded retargeting segments/campaigns;
- change strategy only after an explicit strategy gate is satisfied.

Hard prohibitions:

- never increase total Eksamio spend above the Owner-approved budget cap;
- never infer a purchase from a frontend click;
- never optimize to CTR alone;
- never mix Dilivox economics/data with Eksamio;
- never use PII in advertising parameters;
- never broaden keywords solely because traffic is cheap;
- never hide poor paid-CAC by reporting only free conversions.

## 6. Budget governance

Eksamio has its **own** budget governance. The Dilivox +20% rule is not inherited automatically.

Until the Owner approves a budget policy, programmatic writes that can increase spend remain blocked.

The future controller must support:

- exact weekly cap;
- per-campaign/subchannel caps;
- optional maximum target CPA;
- optional minimum revenue/CRR or contribution-margin threshold;
- kill switch;
- anomaly stop for spend-without-qualified-conversion;
- explicit Owner approval for any expansion beyond admitted policy.

## 7. Search query control

Search-query evidence is a first-class control input.

Each query is classified into:

- high commercial/learning intent;
- useful diagnostic intent;
- broad informational intent;
- answer-seeking/cheating intent;
- wrong exam/subject/year;
- irrelevant/noise.

Evidence-backed actions:

- profitable/qualified queries -> explicit keyword/creative/landing refinement;
- repeated irrelevant/no-purchase queries -> negatives or pause;
- ambiguous queries -> keep only while bounded evidence justifies them.

Free-demo traffic is acceptable only when it contributes measurable evidence toward qualified learning and future Pro conversion at an acceptable acquisition cost.

## 8. SEO is a first-class acquisition channel

SEO is not “put keywords into title”. It uses the same semantic product structure and conversion measurement as Direct.

### Technical SEO hard requirements

Every indexable learner/subject landing must have:

- unique, specific `<title>`;
- unique useful `meta description`;
- one truthful primary H1;
- canonical URL;
- clean 200/301/404 behavior;
- correct robots directives;
- inclusion in an authoritative sitemap when indexable;
- stable internal links from relevant hubs;
- no accidental duplicate/indexable UTM variants;
- mobile-usable, fast learner experience;
- no thin doorway pages created only for keywords.

### Structured data

Where truthful and supported by the page type, use valid Schema.org/JSON-LD. Minimum common layer:

- `BreadcrumbList` for hierarchical learner routes;
- site/organization identity only where the represented facts are real;
- page-specific structured data only when it accurately describes visible content.

Structured data is used to improve machine understanding/snippet presentation, not as a ranking hack.

### Content/landing architecture

High-value SEO surfaces must be real learner assets, not keyword shells. Priority clusters include:

- EGE subject hubs;
- subject + year demo pages, especially 2022–2026 corpus where actually live;
- task-family/topic trainer pages;
- Russian skill/topic pages as accepted learner content becomes public;
- exam-format/explanation pages with genuine source-backed educational value;
- later Pro pages that explain product value truthfully after Pro is live.

Each page should answer a distinct search intent and connect naturally to the next learning action.

### Internal linking

Canonical pathway:

`homepage -> exam hub -> subject -> year/demo or topic -> result/practice -> Pro when available`

Internal links must reinforce semantic hierarchy and learner navigation at the same time.

## 9. Shared SEO + Direct landing registry

Direct and SEO must not build competing landing taxonomies.

Each canonical landing record should eventually contain:

- `landing_id`;
- canonical URL;
- subject;
- exam route;
- year/topic/task family;
- live/public status;
- SEO indexability;
- title/H1/description contract;
- structured-data contract;
- Metrika event coverage;
- Direct eligibility;
- Pro upsell eligibility;
- release/version identity.

Only `LIVE` + truthful + measured pages may be used as paid landing pages.

## 10. Measurement/SEO reporting

Channel truth must remain separable:

- organic Yandex/other search;
- paid Yandex Search;
- Network/retargeting;
- direct/referral/other.

The same downstream commercial events are used across channels so that Eksamio can compare:

- organic acquisition cost proxy and conversion;
- paid CAC;
- landing quality;
- subject demand;
- purchase value and refund-adjusted value.

## 11. Rollout order

1. Inventory the existing Metrika counter/goals and preserve user-created goals.
2. Add only missing canonical learning + commercial funnel goals.
3. Wire live public/runtime events and verify read-back.
4. Add server-owned purchase attribution/eCommerce/offline conversion contract before Pro paid optimization.
5. Create Direct Search campaign inertly; then activate only under explicit budget.
6. Build Search query control loop.
7. Strengthen canonical SEO/structured data/internal linking/sitemaps in parallel.
8. When Pro is live, switch the advertising objective from learning proxies to verified purchase economics.
9. Add Network retargeting.
10. Add cold Network scaling only if purchase economics justify it.

## 12. North-star rule

**Eksamio growth must buy or earn qualified future customers, not traffic.**

The controller may accept a more expensive click if its verified probability/value of becoming a profitable Pro customer is higher. It must reject cheap traffic that systematically consumes budget without producing qualified learning/commercial progression.