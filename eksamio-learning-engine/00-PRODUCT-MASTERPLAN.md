# Eksamio Learning Engine — Product Masterplan

**Статус:** PRODUCT / ARCHITECTURE AUTHORITY  
**Версия:** 2.0  
**Актуализация:** 2026-09-09  
**Baseline main:** `85d2f2b3dd0cf56c428f57c8a5c7d1b636ecebbb`  
**Корень системы:** `eksamio-learning-engine/`

Этот документ задаёт целевой продукт, обязательную последовательность его реализации и границы архитектуры. Исполнимый текущий статус до запуска ведётся в `00B-PROJECT-PRIORITIES-CURRENT.md`. Более новое явно подтверждённое owner decision может изменить план только через явное обновление authority; исторические PR, чаты и промежуточные handoff не могут тихо переписать этот документ.

## 1. Целевой продукт

Eksamio — **умная образовательная платформа / Personal Exam Intelligence System (PEIS)**, а не набор отдельных страниц, тренажёров и AI-чатов.

Главная единица ценности — **доказанное изменение знания и экзаменационной готовности конкретного ученика**.

Единый цикл:

`DIAGNOSE -> MODEL -> PRIORITIZE -> TEACH/PRACTICE -> VERIFY -> RETAIN -> REASSESS -> REPLAN`

Платформа должна понимать:

- что ученик действительно знает и умеет;
- где и почему он теряет баллы;
- какие prerequisite gaps мешают продвижению;
- что выгоднее делать следующим;
- помогла ли конкретная тренировка или помощь Tutor;
- сохранился ли навык через время;
- как меняется ожидаемый экзаменационный результат.

## 2. Главная последовательность проекта — зафиксирована

Работа идёт не «по всем предметам понемногу», а по продуктовым завершениям.

### Этап A — критический запуск Eksamio Pro — Русский

Сначала должен появиться **реальный, видимый и оплачиваемый продукт Русского**, которым ученик может воспользоваться от входа на сайт до повторного входа и сохранённого прогресса.

Критический launch chain:

`PUBLIC SITE -> REGISTRATION/LOGIN -> PURCHASE -> RECEIPT -> ENTITLEMENT -> RUSSIAN LEARNING -> PEIS -> PRACTICE/ERROR WORK -> TUTOR TEXT/VOICE -> INDEPENDENT VERIFY -> PROGRESS -> RETURN LOGIN -> REFUND/REVOKE -> PUBLIC GO-LIVE`

### Этап B — полная реализация Русского

После первого production launch Русский доводится до полной продуктовой системы на одной canonical Russian truth layer: 5–11 классы, ОГЭ, ЕГЭ, курс, тренажёры, конструктор, персональная тренировка, работа над ошибками, retention, план, прогресс и Tutor. Нельзя переключать основной продуктовый ресурс на следующий предмет, оставив Русский набором незавершённых внутренних веток.

### Этап C — масштабирование умной платформы на другие предметы

Только после устойчивого работающего Русского общий PEIS/runtime/product shell переиспользуется для следующих предметов.

Зафиксированный порядок:

1. **Русский язык** — первый полностью реализуемый предмет и доказательство всей платформы.
2. **Математика** — второй предмет; база и профиль являются exam routes одной Mathematics Identity Model.
3. **Физика** — третий предмет.
4. Остальные предметы — по коммерческому приоритету после доказанной повторяемости PEIS на первых трёх.

До завершения критического запуска Русского Mathematics/Physics могут сохранять уже принятые assets и устранять только действительно критические regressions, но **не конкурируют за основной delivery capacity**.

## 3. Что считается «готово»

Eksamio не считает работу готовой только потому, что существует код, PR, тест, документ или staging-кандидат.

Используются разные состояния:

- `DESIGNED` — решение описано;
- `CODE_READY` — код существует и локальные/CI проверки прошли;
- `INTEGRATED` — код безопасно интегрирован в канонический release path;
- `PRIVATE_PRODUCTION_PASS` — реальный production contour доказан без публичного трафика;
- `VISIBLE_TO_LEARNER` — пользователь реально видит и может использовать функцию через продукт;
- `PUBLIC_LAUNCH_PASS` — один exact release прошёл полный E2E и owner go-live.

**Пользовательская функция не считается законченной, пока она не видна и не работает в соответствующем production surface.** Это правило специально запрещает бесконечную работу «внутри репозитория», не превращающуюся в продукт.

## 4. Архитектура продукта Русского

Для ученика существует один Eksamio.

- `eksamio.ru` / Tilda — public marketing, бесплатные демоверсии, понятные входы в регистрацию/Pro.
- Protected Eksamio web application — регистрация, кабинет, Русский, PEIS, прогресс, entitlement, Tutor и Pro-функции.
- Primary production runtime — **Yandex Cloud Russia**.
- Canonical learner state, PEIS, entitlement и session — server-owned.
- GitHub — development/source-of-truth infrastructure, **не learner runtime dependency**.
- Google Drive может быть Source Archive, но не normal learner runtime dependency.
- Core PEIS/business/subject contracts должны оставаться portable/provider-neutral.

Hard invariants:

- `GitHub outage != Eksamio outage`;
- `Drive outage != Eksamio outage` после ingestion;
- browser/localStorage не является canonical learner identity/mastery authority;
- learner audio persisted bytes = `0`;
- `false_exact_mastery = 0`.

## 5. Регистрация и learner identity

Бесплатные публичные демоверсии могут проходиться без регистрации.

Canonical learner history начинается только в server-owned registered identity contour:

- passwordless registration/login;
- verified e-mail и/или другой отдельно production-admitted delivery method;
- один registered identity -> один canonical `learner_profile_id`;
- free/paid различаются entitlement, а не разными learner identities;
- device-only/anonymous browser state не становится canonical mastery;
- consent boundaries и privacy/legal versioning server-verifiable;
- session cookie secure / HttpOnly / SameSite и exact-origin CSRF/CORS boundary.

Если anonymous demo evidence позднее связывается с аккаунтом, это допускается только как отдельно доказанный server-owned import/link contract без выдачи недоказанного mastery. Наличие localStorage само по себе такого права не даёт.

## 6. Серверы и production contour

До публичного Pro должны реально существовать и пройти acceptance:

1. Yandex application runtime / immutable release artifact;
2. Managed PostgreSQL или другой явно admitted server-owned persistence substrate;
3. API Gateway / edge;
4. TLS/domain/CORS/session boundary;
5. secrets в production secret storage, не в Git/browser/logs;
6. migrations + persistence proof;
7. monitoring / redacted logs / health checks;
8. backup + restore proof;
9. rollback и provider/payment/Tutor kill switches;
10. production independence from GitHub/Drive.

`CODE_READY` deployment templates не равны реальному production resource.

## 7. Полное отображение продукта на сайте

Запуск считается реальным только если ученик видит законченную цепочку, а не внутренние технические компоненты.

Обязательные visible surfaces первого production launch:

- понятная public entry page;
- регистрация / вход;
- purchase/checkout path;
- подтверждение доступа Pro;
- личный кабинет / профиль;
- Русский как активный предмет;
- диагностика / результаты / ошибки;
- следующий рекомендуемый шаг;
- тренировка / работа над ошибкой;
- Tutor text;
- Tutor realtime voice;
- независимая проверка после помощи;
- прогресс / weak points / readiness;
- сохранение состояния после logout/login;
- понятные access dates без автопродления;
- support/refund path;
- корректный desktop + mobile browser UX.

Нельзя объявлять Pro подключённым, если learner-facing UI всё ещё работает на fixtures/mocks или скрыт от реального production route.

## 8. Eksamio Base и Eksamio Pro

### Бесплатный Base

- официальные демоверсии;
- базовая диагностика;
- доступные бесплатные тренировки;
- корректный результат и handoff к дальнейшей работе.

Base не должен искусственно портиться ради paywall.

### Pro

Первый коммерческий contour включает:

- server-owned learner state;
- персональный learning loop;
- расширенную диагностику слабых мест;
- работу над ошибками и Next Best Action;
- AI Tutor text + realtime voice как два интерфейса одной Tutor session;
- progress/retention/personal plan по мере admission соответствующих Russian surfaces;
- ограниченные AI-квоты и прозрачный entitlement.

Owner product contract: 30/90 дней без автопродления; отдельные AI-продукты/пакеты допускаются только как явные SKU, а не скрытые billing side effects.

## 9. Payments / receipt / entitlement

Production paid path должен доказать:

`order -> provider payment -> verified callback -> receipt -> entitlement grant -> use -> refund -> entitlement revoke`

Обязательно:

- exact SKU/amount/duration server-owned;
- SBP/card production acceptance для выбранного provider contour;
- NPD/receipt compliance;
- webhook idempotency и replay protection;
- exactly-once entitlement semantics;
- refund/revoke path;
- отсутствие случайного auto-renewal/saved-card поведения, если оно не утверждено.

Payment code без реального bounded provider acceptance не является launch PASS.

## 10. Russian truth — один предмет, одна authority

Полная программа Русского является одной canonical knowledge/content layer для всех learner surfaces.

Она связывает:

`official sources -> Russian semantic identities -> prerequisites -> 5–11 -> OGE/EGE routes -> demos -> trainers -> course -> Tutor grounding -> learner evidence`

Нельзя создавать отдельные ontology/mastery databases для курса, ОГЭ, ЕГЭ, thematic trainers или Tutor.

Все **16/16 Russian program modules** входят в full-subject scope. Текущий exact closure ведётся в PR #164 и остаётся fail-closed до полного acceptance соответствующего заявляемого scope.

Hard rule: title/route/task number/fuzzy match/embedding не создают exact semantic mastery.

## 11. Полная продуктовая реализация Русского

До перехода основного продукта на следующий предмет Русский должен иметь единый production-capable набор:

1. official demos / diagnostics;
2. diagnosis -> exact errors -> weak skills;
3. work on mistakes;
4. thematic trainer;
5. EGE Russian trainer/route;
6. OGE Russian trainer/route;
7. school Russian 5–11 views;
8. trainer constructor;
9. personal `Training for today` / Next Best Action;
10. guided Russian course;
11. prerequisite repair and return-to-goal logic;
12. progress / weak-points / readiness;
13. independent verification after substantial help;
14. retention / spaced recheck;
15. personalized exam/study plan;
16. Tutor text;
17. Tutor realtime voice;
18. Tutor <-> trainer/course handoff without losing PEIS context;
19. extended-answer/essay support only after rubric/source/eval admission;
20. reliable cross-session learner history and explainable next action.

Progressive rollout is allowed, но скрытая функция не считается реализованной. Board должен показывать и launch milestone, и остаток до `RUSSIAN_FULL_PRODUCT_PASS`.

## 12. AI Tutor и provider architecture

Tutor — teaching/reasoning layer поверх verified Russian truth и server-owned learner state, не source of truth.

Shortlist learner-facing brain для реального педагогического Eksamio acceptance:

- OpenAI;
- Qwen;
- DeepSeek;
- Yandex.

Порядок списка **не является рейтингом**. Финальный primary/fallback policy определяется собственным сравнительным педагогическим тестом Eksamio и production/accessibility/security/cost evidence.

Voice layer остаётся provider-neutral относительно brain. Yandex SpeechKit может быть production STT/TTS независимо от выбранного AI-brain.

После существенной Tutor-помощи требуется независимый verification item; фраза ученика «я понял» и сам ответ AI не создают mastery.

## 13. PEIS — общий движок будущей платформы

Все предметы переиспользуют общие контракты:

`Attempt -> EvidenceEvent -> StudentSkillState -> Mastery -> Readiness -> Next Best Action -> Practice/Help -> Independent Verify -> Retention -> Reassess`

Общие platform services после доказательства на Русском:

- identity/account/session;
- learner state persistence;
- PEIS evidence/mastery/readiness/retention/NBA;
- entitlement/billing limits;
- AI Gateway/provider routing;
- Tutor session/reliability/cost telemetry;
- observability/audit;
- transient speech/realtime transport;
- product shell/navigation/progress surfaces.

Предмет-специфичны:

- source authority;
- semantic identity model;
- prerequisites;
- exam routes/scoring;
- content/program;
- subject-specific evidence semantics.

## 14. Критический план запуска Русского

Исполнимые детали и exact evidence находятся в `00B-PROJECT-PRIORITIES-CURRENT.md`. Masterplan фиксирует обязательные классы результата:

1. **Russian truth:** заявляемый launch scope source-backed и subject-accepted.
2. **Identity:** real registration/login -> one server-owned learner profile.
3. **Visible product:** public site -> protected Pro UX на desktop/mobile.
4. **PEIS assembly:** attempts/errors/practice/NBA/progress/persistence соединены с real backend.
5. **Admissions:** production evidence принимается только по exact registered learner/item/action/evaluator contract.
6. **Yandex production:** runtime/database/edge/TLS/secrets/monitoring/backup/rollback реально подняты и приняты.
7. **Delivery:** passwordless delivery реально доказана.
8. **Commercial:** exact SKU -> payment -> receipt -> entitlement -> refund/revoke реально доказаны.
9. **Tutor:** pedagogically selected brain + grounded text + realtime voice + reliability + independent verify.
10. **Legal/privacy/operations:** production values/docs/support/refund/audio-zero policy accepted.
11. **Private production E2E:** один exact release проходит всю learner цепочку.
12. **Public go-live:** owner gate, launch links/site visible, post-launch smoke + rollback readiness.

Если хотя бы один обязательный класс не `PASS`, публичный paid launch не считается завершённым.

## 15. После первого запуска: `RUSSIAN_FULL_PRODUCT_PASS`

Первый paid launch не даёт права бросить Русский. Следующая основная цель — закрыть все Russian surfaces из раздела 11 и доказать:

- единый registered learner profile;
- cross-session persistence;
- одна canonical Russian truth layer;
- один PEIS;
- корректный handoff между demo/course/trainer/Tutor;
- полный visible navigation по фактически admitted Russian product;
- learner-facing status не обещает скрытые/непринятые функции;
- production observability и support позволяют сопровождать реальных пользователей.

Только после `RUSSIAN_FULL_PRODUCT_PASS` основной roadmap переходит к следующему предмету.

## 16. Математика — второй предмет

Математика подключается к уже работающим platform services, а не строит свой новый Eksamio.

Порядок:

1. source corpus 2022–2026 + gap closure;
2. Mathematics Identity Model;
3. BASE + PROFILE route mappings;
4. demo/trainer/course content alignment;
5. exact evidence semantics;
6. reuse registration/server/PEIS/Pro/Tutor/product shell;
7. visible mathematics learner loop;
8. private production E2E;
9. public rollout.

Base и Profile — маршруты одной предметной модели.

## 17. Физика — третий предмет

После математического platform reuse доказательства Физика проходит тот же предметный pipeline:

`official sources -> Physics identities -> content/routes -> exact evidence -> shared PEIS -> Tutor -> visible learner product -> E2E -> rollout`.

Существующие принятые physics/demo assets сохраняются; они не дают права создать отдельный learner engine.

## 18. Остальные предметы

После Русского, Математики и Физики новые предметы добавляются только через повторяемый subject onboarding contract. Новый предмет не может дублировать account, PEIS, billing, Tutor session platform или progress engine.

Порядок следующих предметов определяется commercial demand, quality/corpus readiness и стоимостью full-subject admission.

## 19. Owner Console — обязательная панель управления проектом

Разработка Eksamio должна иметь отдельную **Owner Console / Project Control Panel** для владельца. Это development/management surface, а не learner-facing часть `eksamio.ru`.

Панель обязана показывать **весь проект целиком**, а не только текущий PR или сегодняшнюю работу.

Верхний уровень всегда отображает:

`CRITICAL RUSSIAN LAUNCH -> RUSSIAN FULL PRODUCT -> MATHEMATICS -> PHYSICS -> NEXT SUBJECTS / PLATFORM SCALE`

Для каждого этапа и каждой задачи должны быть видны:

- название и конечный пользовательский результат;
- stage / workstream;
- приоритет;
- статус по словарю раздела 3;
- `%` или finite denominator только там, где он математически честный;
- зависимости;
- blocking reason;
- exact branch / PR / SHA;
- CI/evidence status;
- `VISIBLE_TO_LEARNER: yes/no`;
- production status;
- owner gate, если требуется;
- текущий исполнитель: Astra / Codex / owner / external provider;
- следующий конкретный action;
- дата последнего доказанного изменения;
- исторически завершённые этапы, чтобы прогресс не исчезал из поля зрения.

Панель должна иметь минимум пять представлений:

1. **Whole Project** — все этапы и задачи от критического запуска до следующих предметов.
2. **Critical Path** — только блокеры ближайшего реального пользовательского milestone.
3. **Russian Product** — полный путь Русского, включая launch + остаток до `RUSSIAN_FULL_PRODUCT_PASS`.
4. **Visible Product** — что реально доступно пользователю сейчас на сайте/в Pro, отдельно от `CODE_READY`.
5. **Owner Gates** — только решения/действия, где действительно требуется владелец.

Панель не должна быть ручным вторым источником истины. План/смысл берётся из canonical Masterplan + Operational Board, а фактические branch/PR/SHA/CI — из GitHub. Если панель и GitHub расходятся, она обязана показать `STALE/CONFLICT`, а не скрыть расхождение.

## 20. Astra / Codex как development layer

Development automation не является частью learner runtime.

- Astra может быть Senior Brain / planner / reviewer проекта через отдельный agent-orchestration contour.
- Codex — bounded execution engineer.
- GitHub — source of truth.
- CI — deterministic evidence.
- Owner Console — человекочитаемая проекция полного project state.

Ни Astra, ни Codex не получают автоматического права на merge, deploy, production learner writes, payment/refund, provider spend, secret rotation или public publication без соответствующей owner policy/gate.

Learner-facing Tutor provider policy является отдельным решением и не выводится из выбора development Brain.

## 21. Метрики

### Learning

- NIC-1 / NIC-3;
- transfer success;
- retention success;
- mastery gain;
- repeat-error rate;
- time-to-mastery;
- score delta between controls;
- expected/actual score gain per study minute;
- forecast calibration.

### AI

- outcome after help;
- direct-answer leakage;
- unsupported/factual error;
- latency;
- cost per successful learning intervention;
- fallback/error rate.

### Product / delivery

- registration success;
- purchase -> entitlement success;
- return-login continuity;
- diagnosis -> practice conversion;
- repeat study days;
- paid conversion after demonstrated value;
- AI cost / revenue;
- share of learners with measurable improvement;
- visible-feature completion vs code-only completion.

## 22. No-circle execution rules

1. Не проводить новый проект-wide audit, если можно продолжить от текущей exact truth.
2. Не считать документ/PR/CI пользовательским результатом.
3. Любой большой workstream должен двигать конкретную строку Owner Console к `VISIBLE_TO_LEARNER` / `PUBLIC_LAUNCH_PASS`.
4. Не открывать новый предмет, чтобы избежать трудного blocker Русского.
5. Не создавать вторую ontology/PEIS/account/billing систему для нового learner surface или предмета.
6. Не допускать false exact mastery ради ускорения.
7. Не создавать runtime dependency от GitHub/Drive.
8. Не хранить learner audio.
9. Не публиковать paid feature, не прошедшую exact production E2E.
10. После каждого существенного accepted delta обновлять Operational Board/structured project state, чтобы Owner Console показывала новый факт.

## 23. Текущий главный milestone

**Следующая цель проекта: `RUSSIAN_PUBLIC_PAID_LAUNCH_PASS`.**

До неё вся работа ранжируется по тому, сокращает ли она путь к реальному ученику:

`registration + servers + visible site/app + Russian truth + PEIS + Pro + payments + Tutor + persistence + E2E + go-live`.

После неё следующая цель: **`RUSSIAN_FULL_PRODUCT_PASS`**.

Только затем основной продуктовый roadmap переходит к Mathematics, затем Physics и дальнейшему построению умной многопредметной образовательной платформы.