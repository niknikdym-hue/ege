# Eksamio — First Yandex Direct Search Campaign Candidate v0.1

**Status:** READY EXCEPT OWNER BUDGET + LIVE API APPLY  
**Date:** 2026-08-31  
**Campaign:** `EKSAMIO_FREE_EGE_SEARCH_2026`  
**Technical API/operator:** `reklamadymova`  
**Managed advertiser:** `dymova`  
**Metrika counter:** `110348386`  
**Network/YAN placements:** OFF for first wave  
**Initial geography:** Russia (`region_id=225`)

## 1. Purpose

Acquire high-intent learners into already-live free Eksamio exam products and establish clean Metrika conversion evidence before Pro launch.

The first wave is Search-only. It is not an on-site advertising/RSYA monetization experiment.

## 2. Campaign strategy candidate

Unified Performance Campaign / search traffic.

Cold-start strategy candidate:

- Search: `WB_MAXIMUM_CLICKS` with Owner-approved `WeeklySpendLimit`;
- Network: `SERVING_OFF`;
- Metrika counter: `110348386`;
- attribution: `AUTO`;
- site monitoring: ON;
- URL tracking parameters:

`utm_source=yandex&utm_medium=cpc&utm_campaign={campaign_id}&utm_content={source_type}.{ad_id}.{gbid}.{device_type}&utm_term={keyword}`

Do not enable conversion-optimized bidding before the canonical goals have real verified volume.

## 3. Ad group — Russian EGE

Landing:

`https://eksamio.ru/ege/russkiy/demoversiya/`

Responsive titles:

- `Демоверсия ЕГЭ по русскому 2026`
- `Русский ЕГЭ: полный вариант онлайн`
- `Проверьте знания перед ЕГЭ`
- `Демоверсии русского 2022–2026`

Responsive texts:

- `Пройдите полный вариант в экзаменационном режиме. Проверка после завершения.`
- `Демоверсии 2022–2026 и тренажёры по темам. Начните бесплатно.`

Initial phrase cluster:

- `демоверсия егэ русский 2026`
- `егэ русский демоверсия фипи`
- `пробник егэ русский онлайн`
- `пробный егэ русский онлайн`
- `демоверсия русский язык егэ`
- `тренажер егэ русский`
- `подготовка егэ русский демоверсия`

Group exclusions to review after search-query data:

- `огэ`
- `впр`
- `скачать`
- `pdf`
- `ответы`
- `решебник`
- `варианты с ответами`

## 4. Ad group — Profile Mathematics EGE

Landing:

`https://eksamio.ru/ege/matematika-profil/demoversiya/`

Responsive titles:

- `ЕГЭ профиль: демоверсия 2026`
- `Профильная математика — полный вариант`
- `Проверьте профильную математику`

Responsive texts:

- `19 заданий по формату демоверсии ФИПИ. Краткая часть проверяется автоматически.`
- `Полный вариант профильной математики. Результат и критерии после завершения.`

Initial phrase cluster:

- `демоверсия егэ профильная математика 2026`
- `фипи профильная математика демоверсия`
- `пробник егэ профильная математика`
- `пробный егэ профиль математика онлайн`
- `егэ профиль математика полный вариант`

Group exclusions:

- `база`
- `базовая`
- `огэ`
- `скачать`
- `pdf`
- `ответы`
- `решебник`

## 5. Ad group — Basic Mathematics EGE

Landing:

`https://eksamio.ru/ege/matematika-baza/demoversiya/`

Responsive titles:

- `ЕГЭ база: демоверсия 2026`
- `Базовая математика — полный вариант`
- `Проверьте базовую математику`

Responsive texts:

- `21 задание, 180 минут. Полная попытка с проверкой только после завершения.`
- `Базовая математика по демоверсии ФИПИ. Пройдите вариант бесплатно.`

Initial phrase cluster:

- `демоверсия егэ базовая математика 2026`
- `фипи базовая математика демоверсия`
- `пробник егэ базовая математика`
- `пробный егэ база математика онлайн`
- `егэ базовая математика полный вариант`

Group exclusions:

- `профиль`
- `профильная`
- `огэ`
- `скачать`
- `pdf`
- `ответы`
- `решебник`

## 6. Ad group — Physics EGE

Landing:

`https://eksamio.ru/ege/fizika/demoversiya/`

Responsive titles:

- `Демоверсия ЕГЭ по физике 2026`
- `Физика ЕГЭ: полный вариант онлайн`
- `Проверьте знания по физике`

Responsive texts:

- `26 заданий, 235 минут. Проверка краткой части и критерии развёрнутых решений.`
- `Физика по демоверсии ФИПИ в экзаменационном режиме. Начните бесплатно.`

Initial phrase cluster:

- `демоверсия егэ физика 2026`
- `фипи физика егэ демоверсия`
- `пробник егэ физика онлайн`
- `пробный егэ физика 2026`
- `егэ физика полный вариант`

Group exclusions:

- `огэ`
- `впр`
- `скачать`
- `pdf`
- `ответы`
- `решебник`

## 7. Search-query policy

Do not aggressively over-minus before real query evidence. The purpose of the first bounded wave is to learn which high-intent formulations actually produce `eks_demo_start` and `eks_demo_complete`.

Daily/early review should classify queries into:

- relevant exam intent;
- ambiguous informational intent;
- answer-seeking/cheating intent;
- wrong exam/subject;
- irrelevant.

Only evidence-backed exclusions are promoted to campaign-level negatives.

## 8. Metrika conversion sequence

Mandatory before activation:

- counter `110348386` visible to the API token;
- canonical action goals installed;
- `eks_demo_open` reaches the counter from public navigation;
- deeper product events wired and verified where available;
- Direct campaign attached to the same counter;
- `yclid` survives landing and page navigation;
- UTM parameters visible in Metrika.

Primary cold-start quality metrics:

- click -> `eks_demo_start`;
- `eks_demo_start` -> `eks_demo_complete`;
- cost per `eks_demo_complete`;
- `eks_demo_complete` -> next learning action;
- return-learning rate when enough observation time exists.

## 9. Exact remaining blockers

1. Owner sets the first Eksamio weekly advertising budget.
2. Run Metrika goal setup against live counter `110348386` using the existing protected OAuth token.
3. Publish/attach the event bridge to the live Tilda/public surface and add deep events to demo/trainer runtime.
4. Build and send the Direct `Campaigns.add -> AdGroups.add -> Keywords.add -> Ads.add` chain under `Client-Login: dymova`.
5. Keep the newly created campaign non-spending until read-back confirms exact campaign/group/ad/keyword/CounterIds/tracking identity and Owner activates it within the fixed budget.

No separate OAuth identity is required for Eksamio unless the existing manager binding fails live certification.
