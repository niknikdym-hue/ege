# Eksamio Learning Engine — Product Masterplan

**Статус:** PRODUCT / ARCHITECTURE AUTHORITY  
**Версия:** 1.2
**Дата исходной фиксации:** 2026-08-18  
**Актуализация:** 2026-08-22
**Корень системы:** `eksamio-learning-engine/`

Утверждённые owner decisions по первому Pro launch, product client, production cloud, AI/provider boundary, audio privacy, identity, payments и Tutor policy зафиксированы в `OWNER-DECISIONS-2026-08-22.md`. Они являются частью текущей product/architecture authority и явно заменяют прежний порядок, в котором realtime voice относился к позднему/P3-слою после первого Pro launch.

## 1. Целевой продукт

Eksamio — не набор независимых страниц «демоверсия / тренажёр / теория» и не универсальный AI-чат для ЕГЭ.

Целевая модель:

> **Eksamio = Personal Exam Intelligence System (PEIS)**

Система должна понимать:

- какие проверенные знания, умения и решения составляют предмет;
- что конкретный ученик действительно умеет;
- где и почему он системно теряет баллы;
- какие prerequisite gaps мешают продвижению;
- что выгоднее изучать следующим;
- помогло ли конкретное объяснение или тренировка;
- сохранился ли навык через время;
- как меняется ожидаемый экзаменационный результат.

Главная единица ценности — не просмотренный урок и не ответ AI, а **доказанное изменение состояния знания ученика**.

## 2. Предметный приоритет

Зафиксированный порядок предметов Eksamio:

1. **Русский язык** — первый предмет.
2. **Математика** — второй предмет.
3. **Физика** — третий предмет.

Приоритет ресурсов:

- **P0: русский язык + математика** — два главных предметных направления Eksamio;
- **P1: физика** — развивается параллельно, но не должна замедлять русский и математику.

Для математики учитываются оба экзаменационных маршрута: **профильная и базовая математика**. Профильная математика является ключевым интеллектуальным маршрутом второго предмета; базовая математика сохраняется как отдельный официальный exam route той же Mathematics Identity Model, а не как отдельная система.

## 3. Единый PEIS, а не отдельные предметные движки

Русский, математика и физика подключаются к **одной системе**.

Нельзя создавать для нового предмета параллельные:

- Student Model;
- learner state architecture;
- универсальный Evidence contract;
- mastery engine;
- readiness engine;
- retention engine;
- Recommendation / Next Best Action engine.

У каждого предмета свой предметный слой:

- verified source authority;
- semantic / identity model;
- prerequisite relationships;
- exam-route mapping;
- content/program layer;
- demo/trainer mappings.

Общий PEIS-слой получает предметные semantic identities и evidence, но не дублируется по предметам.

## 4. Исторический официальный корпус

Для каждого предмета целевой исторический корпус демоверсий и связанных официальных материалов — **2022–2026**.

Принципы:

- официальный источник является source of truth;
- существующие 2026-source не реконструируются и не переписываются без необходимости;
- готовая интерактивная демоверсия Eksamio не считается официальным source;
- отсутствующее не синтезируется «по смыслу»;
- provenance и целостность должны быть проверяемыми;
- предметные source-контуры не должны ломать уже проверенные специализированные build/audit-контуры, особенно математики.

## 5. Единый learning loop

Все части продукта замыкаются в один цикл:

`DIAGNOSE -> MODEL -> PRIORITIZE -> TEACH/PRACTICE -> VERIFY -> RETAIN -> REASSESS -> REPLAN`

1. **DIAGNOSE** — демоверсия, контрольная или отдельное задание дают evidence.
2. **MODEL** — evidence обновляет состояние конкретных semantic skills/subskills.
3. **PRIORITIZE** — система выбирает следующий лучший шаг.
4. **TEACH/PRACTICE** — правило, тренировка или персональная помощь.
5. **VERIFY** — новый независимый item без помощи.
6. **RETAIN** — проверка навыка позже.
7. **REASSESS** — контроль/демоверсия проверяет перенос в экзамен.
8. **REPLAN** — маршрут и прогноз пересчитываются.

Функции, которые не усиливают этот цикл и не дают самостоятельной ценности ученику, имеют меньший приоритет.

## 6. Роль существующих продуктов

### Демоверсии

Остаются максимально точными симуляторами официального экзамена и не становятся адаптивными внутри экзаменационного режима.

В PEIS демоверсия дополнительно является **диагностическим сенсором** и должна передавать структурированные evidence-события, а не только итоговый балл.

### ЕГЭ-тренажёры

Становятся двигателями персонального маршрута, практики и подтверждения mastery. Они должны уметь принимать handoff из диагностики и работать с конкретными слабостями.

### Тематические тренажёры

Не должны иметь отдельную несвязанную модель знания. Проверяемые items связываются со стабильными semantic identities и, где применимо, пишут evidence в единый Student Model.

### Полные предметные программы

Полная программа — не отдельный линейный курс, а knowledge/content layer PEIS:

- карта знаний и навыков;
- verified rules / explanations / methods;
- prerequisites;
- типичные ошибки и контрасты;
- teach/practice/check content;
- база adaptive practice;
- база AI Tutor / retrieval;
- retention/transfer layer.

## 7. Identity Model — обязательный предметный фундамент

Exam task number, элемент содержания, проверяемое умение и semantic identity — не одно и то же.

Для каждого предмета должна существовать единая непротиворечивая identity model, связывающая:

`official sources -> school knowledge/skills -> semantic identities -> prerequisites -> exam routes -> demo items -> trainer items -> full program -> learner evidence`

Нельзя создавать вторую ontology только потому, что появился новый курс, тренажёр или AI-функция.

## 8. Student Learning Twin

Рабочее понятие: **Student Learning Twin**.

Это не профиль с процентами. Для skill/subskill система постепенно хранит evidence и выводы о:

- mastery;
- последних attempts;
- повторяющихся error patterns;
- assisted / unassisted evidence;
- transfer;
- retention;
- давности проверки;
- prerequisite gaps;
- confidence / uncertainty;
- intervention effectiveness;
- recommendation results.

Персонализация объяснения должна опираться на наблюдаемый learning outcome, а не на псевдотипологии вроде «визуал/аудиал».

## 9. Что должно отличать Eksamio

Просто `diagnosis -> adaptive plan -> lesson -> quiz` уже является мировым baseline.

Eksamio строится вокруг пяти более сильных механизмов:

### Score Gain per Minute

Recommendation Engine оптимизирует ожидаемую полезность следующего шага:

`expected_exam_gain / expected_study_time`

### Error Fingerprint

Система должна различать с evidence/confidence как минимум:

- knowledge gap;
- prerequisite gap;
- confusion между похожими правилами/методами;
- application error;
- reading/formulation error;
- unstable skill;
- retention failure;
- likely accidental error;
- high-confidence misconception.

### Intervention Effectiveness

После помощи измеряется не «понравилось объяснение», а результат следующего независимого действия, серии, transfer и retention.

### Calibrated Score Forecast

Прогноз — диапазон с uncertainty и последующей проверкой calibration на реальных контрольных попытках.

### Explainable Next Best Action

Система объясняет, почему именно этот следующий шаг выбран: evidence, exam value, prerequisite/readiness, retention state, история ошибок и ожидаемая стоимость времени.

## 10. Продуктовые слои

### Eksamio Base — бесплатный базовый learning loop

- демоверсии;
- тренажёры;
- базовая проверка;
- карта слабых мест;
- работа над ошибками;
- demo -> trainer handoff;
- базовый персональный маршрут;
- next-item correctness;
- spaced repetition / retention;
- reassessment.

Базовый learning loop не должен деградировать ради paywall.

### Eksamio Pro — платный персональный слой

- глубокий AI-разбор ошибки;
- персональный AI Tutor с text и realtime voice как двумя интерфейсами одного Tutor и одного learning episode;
- расширенный Error Fingerprint;
- долгосрочная оптимизация маршрута;
- расширенный score forecast;
- AI-проверка сочинения/развёрнутого ответа как учебная оценка;
- персональные аналитические отчёты.

Первый paid Pro launch запрещён, пока одновременно не production-ready:

- text AI Tutor;
- realtime voice AI Tutor;

Text-only и voice-only Pro launch запрещены. Переключение `voice -> text -> voice` внутри одной сессии не должно терять learning context или PEIS state. Voice является P0 launch capability, но не отдельным Tutor и не разрешением обходить shared PEIS dependency graph.

### Позднее расширение Pro

- vision/photo analysis;
- совместный разбор черновика/изображения;
- richer multimodal coaching после доказанного production contour text + realtime voice.

## 11. Роль AI

AI — reasoning/teaching layer поверх verified structure.

AI может:

- объяснять конкретную ошибку;
- задавать наводящие вопросы;
- менять форму объяснения;
- формировать персональный разбор из structured evidence;
- выдвигать гипотезу причины ошибки с confidence;
- вести диалог по verified knowledge base;
- проверять развёрнутые ответы по явной rubric в учебном режиме;
- работать через text и realtime voice в общем Tutor session state;
- позже расширяться на фото/vision и другие multimodal inputs.

AI **не является source of truth** для:

- официальных ответов;
- критериев;
- task numbering;
- scoring;
- exam rules;
- canonical semantic identity;
- mastery state без deterministic policy/evidence contract.

После существенной AI-помощи, где применимо, обязателен новый независимый verification item.

## 12. Общие PEIS-контракты

Предметы должны переиспользовать уже созданные общие контракты learner evidence / state и последующие PEIS contracts, включая materialized contracts TASK-004 и TASK-005.

Логическая цепочка:

`Attempt -> EvidenceEvent -> StudentSkillState -> Mastery -> Readiness -> Next Best Action -> Practice/Help -> Independent Verify -> Retention -> Reassess`

Контракты mastery/readiness/retention/NBA не содержат предметную истину. Предметные prerequisite edges и semantic truth допускаются только через source-backed reviewed authority.

Learning policy также фиксирует:

- фраза ученика «я понял» не является mastery evidence;
- существенная AI-помощь требует независимой проверки, а её провал меняет объяснение/диагностику вместо автоматического продвижения;
- prerequisite repair может временно изменить маршрут, после чего система возвращается к исходной цели;
- полный worked solution допустим после реальных попыток, но просмотр решения не считается mastery;
- immediate mastery и retained mastery различаются; retention перепроверяется индивидуально, а failure снижает confidence и возвращает skill в review;
- deadline/exam value могут менять приоритет, не отменяя critical prerequisites;
- score forecast всегда range/probability, не гарантия;
- ученик может отойти от рекомендованного маршрута; critical prerequisite даёт объяснимое предупреждение, но не hard lock;
- Next Best Action имеет понятное человеку объяснение.

## 13. Приоритет реализации

### P0 — сейчас

1. Masterplan + hierarchy of authority должны быть доступны из актуального `main`.
2. Не останавливать verified production-работу по демоверсиям.
3. **Русский:** завершить Unified Russian Identity Model и data alignment между 185 identities, Skill Graph, demo, 174 trainer items, thematic trainers и full program.
4. **Математика:** провести non-destructive inventory существующих profile/base source/audit/build-контуров и закрыть реальные gaps исторического корпуса 2022–2026 без повторной переделки готового.
5. **Физика:** вести source 2022–2026 и Physics Identity Model параллельно, не отбирая темп у русского и математики.
6. Зафиксировать стабильные identity/mapping contracts предметов.
7. Переиспользовать общие Student / Attempt / Evidence / StudentSkillState / Mastery / Readiness / Retention / NBA contracts.
8. Реализовать и проверить первый полный vertical slice: `demo -> diagnosis -> trainer -> verify`.
9. Начать outcome telemetry: NIC-1, NIC-3, transfer, retention, recommendation result.
10. Только затем подключить первый AI-разбор поверх structured evidence.

### P0.5 — первый монетизируемый AI-срез

`verified attempt -> failed skill -> grounded AI explanation -> personalized help -> independent item -> measured outcome`

Первый AI-продукт: **AI-разбор результата / конкретной ошибки + следующий проверочный шаг**.

Не начинать с универсального пустого чата.

Этот ранний bounded AI-срез не является разрешением на text-only Pro launch. До первого paid Pro должны быть закрыты production gates для одного Tutor в обоих интерфейсах — text и realtime voice — поверх shared PEIS, deployment/security и verified knowledge foundations.

### P1

- account/server sync;
- «Тренировка на сегодня»;
- retention schedule;
- Recommendation Engine;
- Error Fingerprint v1;
- paid entitlements/limits;
- AI cost/outcome telemetry;
- Student Learning Twin v1.

### P2

- AI essay/extended-answer evaluation с criterion evidence и uncertainty;
- calibrated score forecast;
- dynamic plan to exam;
- confidence calibration;
- vision/photo analysis;
- intervention experiments.

### P3

- richer multimodal live sessions после первого Pro launch;
- richer Student Learning Twin;
- proactive replanning;
- long-term cross-session personalization.

### P4

- масштабирование PEIS на следующие предметы после русского, математики и физики;
- cross-subject profile;
- dashboards при доказанной потребности;
- извлечение proven shared Living Core services;
- internationalization после product-market proof.

## 14. Что не делать сейчас

- не строить generic AI-чат для ЕГЭ;
- не трактовать P0 voice launch gate как voice-first обход PEIS: первый implementation slice остаётся verified attempt -> grounded help -> independent verify, но первый paid Pro не может быть text-only или voice-only;
- не делать отдельные базы прогресса для demo/trainer/program;
- не создавать вторую Skill Graph/ontology поверх current canonical layer;
- не давать AI владеть official answers/scoring;
- не ставить завершение 100% всей программы блокером первого безопасного vertical slice;
- не строить абстрактную универсальную платформу раньше работающего Eksamio loop;
- не оптимизировать продукт прежде всего по времени на сайте/числу сообщений;
- не менять verified production demo content ради персонализации;
- не переносить старые разрозненные localStorage состояния в cloud как есть без versioned data contract.

## 15. Метрики

Learning:

- NIC-1;
- NIC-3;
- transfer success;
- retention success;
- mastery gain;
- repeat-error rate;
- time-to-mastery;
- score delta between controls;
- expected/actual score gain per study minute;
- forecast calibration.

AI:

- outcome after help;
- direct-answer leakage rate;
- unsupported/factual error rate;
- latency;
- cost per successful learning intervention;
- fallback rate.

Business:

- diagnosis -> practice conversion;
- repeat study days;
- paid conversion after demonstrated free value;
- paid retention;
- AI cost / revenue;
- share of users with measurable improvement.

## 16. AI evaluation gate

Каждая новая AI-функция до массового rollout получает фиксированный eval set.

Минимум:

- factual/source correctness;
- правильная skill binding;
- отсутствие подмены official answer;
- pedagogical protocol;
- отсутствие преждевременной выдачи ответа;
- uncertainty;
- structured output contract;
- post-help learning outcome после запуска.

AI не является единственным судьёй собственного качества. Нужны deterministic checks, source-backed fixtures и reviewed evaluation contour.

## 17. Eksamio-first / Living-Core-aware

Не строить сейчас абстрактную универсальную платформу для всех будущих проектов до запуска работающего Eksamio.

Стратегия: **product-first, core-aware**.

Потенциально shared services позже:

- identity/account;
- session/memory;
- AI Gateway/provider routing;
- knowledge retrieval;
- usage/cost accounting;
- entitlements/billing limits;
- safety/moderation;
- analytics/experimentation;
- audit/logging;
- transient speech/realtime transport без persistent learner audio storage.

Предметное ядро Eksamio не надо преждевременно делать generic:

- semantic identity models;
- Skill Graph;
- exam routes;
- subject source authority;
- mastery/readiness interpretation;
- recommendation policy;
- score forecast;
- exam scoring;
- learning evidence semantics.

## 18. Provider architecture

Предметная логика не зависит напрямую от конкретного AI/cloud provider.

Provider-specific model/API не должен становиться частью Student Model или subject source-of-truth.

Нужны provider abstraction, model/version logging, prompt/policy version logging, cost telemetry, fallback policy и feature flags.

Production architecture должна обеспечивать работу в России без VPN, включая text и realtime voice Tutor; learner browser не обращается напрямую к foreign AI service. Primary production cloud — Yandex Cloud Russia, но canonical PEIS/learner/subject state и core business logic остаются portable/provider-neutral.

OpenAI и Google являются principal candidates для conversational brain, а Yandex SpeechKit — priority candidate для Russian STT/TTS. Candidate не означает production approval. Admission требует применимых Russia/accessibility, legal, quality и security gates; automatic fallback допустим только между pre-approved production providers. Learner provider не выбирает.

## 19. Production, client, identity, payment и privacy boundaries

- Первый Pro client — отдельное Eksamio web application с качественным desktop/mobile-browser UX; native mobile apps не обязательны для первого launch.
- Tilda остаётся public/site/free-demo layer и не владеет accounts, canonical learner state, PEIS, AI Tutor или payments.
- Pro authentication passwordless: verified e-mail или phone по выбору пользователя; anonymous same-device free-demo progress безопасно связывается с permanent account, но browser не становится identity authority.
- Первый payment candidate для self-employed/NPD contour — Robokassa + Robocheki SMZ; payment layer replaceable, а production admission требует legal/API/webhook-idempotency/receipt/SBP-card/refund/failure-retry validation. Плательщик — фактически платящее и юридически способное лицо; blanket parent-only rule отсутствует.
- Tutor session text/structured history может сохраняться для continuity/PEIS по privacy/retention policy.
- **Learner audio не хранится вообще и ни в какой форме.** Допустима только transient обработка текущего realtime pipeline; recordings/fragments/copies/backups/voiceprints/persistent speaker embeddings/audio datasets запрещены. Launch legal/privacy documentation должна явно сообщать отсутствие audio storage; выбор конкретного legal document остаётся отдельным review.

Полный owner-decision contract: `OWNER-DECISIONS-2026-08-22.md`.

## 20. Change control

Следующие решения нельзя молча менять историческим checkpoint, локальной задачей или отдельным предметным чатом:

- `eksamio-learning-engine/` — корень интеллектуальной системы;
- Eksamio = Personal Exam Intelligence System;
- единый semantic/skill identity principle;
- единый Student Model и общие PEIS contracts;
- русский и математика — P0;
- математика — второй предмет;
- физика — третий предмет;
- исторический source-корпус каждого предмета — 2022–2026;
- бесплатный базовый learning loop;
- AI не является source of truth;
- первый Pro launch только при совместной production readiness text + realtime voice одного Tutor;
- learner audio non-storage;
- learning outcome важнее engagement;
- Eksamio-first / Living-Core-aware;
- provider abstraction.

Если требуется изменить одно из этих решений — обновить этот masterplan или создать явный ADR/product decision.

## 21. Ближайшая обязательная последовательность

Если нет более нового явно утверждённого product decision:

1. сохранить и синхронизировать product authority в `main`;
2. Unified Russian Identity Model / alignment;
3. Mathematics inventory + 2022–2026 gaps + Mathematics Identity Model;
4. Physics source 2022–2026 + Physics Identity Model — параллельно, но P1;
5. первый `demo -> diagnosis -> trainer -> verify` vertical slice;
6. NIC/transfer/retention measurement;
7. AI Review MVP на verified vertical slice;
8. usage/cost/eval telemetry;
9. production deployment/security + Russia/no-VPN + portable Yandex Cloud contour;
10. passwordless account/server sync, anonymous-to-account linking, entitlements и replaceable payment contour gates;
11. один production Tutor поверх shared PEIS: text + realtime voice с общей session continuity; paid Pro launch только после прохождения gates обоими интерфейсами;
12. Student Learning Twin / Recommendation Engine expansion;
13. essay/vision и richer multimodal capabilities;
14. scale to further subjects;
15. extract proven shared Living Core services.

## 22. Короткая формула

**Имеем:** verified exam sources + демоверсии + тренажёры + предметный контент + общие PEIS contracts.

**Строим:**

`точный экзамен -> semantic evidence -> Student Learning Twin -> следующий лучший шаг -> персональная помощь -> независимая проверка -> retention -> прогноз -> новый план`

Именно эта система, а не отдельный AI-чат, является целевым продуктом Eksamio.
