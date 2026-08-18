# Eksamio Learning Engine — Product Masterplan

**Статус:** PRODUCT / ARCHITECTURE AUTHORITY  
**Версия:** 1.0  
**Дата фиксации:** 2026-08-18  
**Корень новой системы:** `eksamio-learning-engine/`  
**Первый предмет:** русский язык

## 1. Роль папки `eksamio-learning-engine/`

Репозиторий `niknikdym-hue/ege` остаётся общим репозиторием Эксамио: в нём живут демоверсии, предметные пакеты, тренажёры, регламенты, источники и новая система.

`eksamio-learning-engine/` — **корень новой интеллектуальной учебной системы Эксамио**. Все новые архитектурные решения по персонализации, Student Model, Learning Engine и AI должны исходить отсюда.

Это не отдельный тренажёр и не экспериментальная надстройка. Это будущая системная основа, к которой постепенно подключаются существующие демоверсии, ЕГЭ-тренажёры, тематические тренажёры и полные предметные программы.

## 2. Что должно получиться на выходе

Эксамио не должен остаться набором независимых страниц «демоверсия / тренажёр / теория» и не должен превращаться в обычный AI-чат для ЕГЭ.

Целевая модель:

> **Eksamio = Personal Exam Intelligence System**

Система должна знать:

- какие проверенные навыки и решения составляют предмет;
- что конкретный ученик действительно умеет;
- где он системно теряет баллы;
- какова вероятная причина ошибки;
- что выгоднее изучать следующим;
- помогло ли конкретное объяснение;
- сохранился ли навык через время;
- как меняется ожидаемый экзаменационный результат.

Главная единица ценности — не просмотренный урок и не ответ AI, а **доказанное изменение состояния знания ученика**.

## 3. Единый learning loop

Все части продукта должны замыкаться в один цикл:

`DIAGNOSE -> MODEL -> PRIORITIZE -> TEACH/PRACTICE -> VERIFY -> RETAIN -> REASSESS -> REPLAN`

1. **DIAGNOSE** — демоверсия, контрольная или отдельное задание дают evidence.
2. **MODEL** — evidence обновляет состояние конкретных skills/subskills.
3. **PRIORITIZE** — система выбирает следующий лучший шаг.
4. **TEACH/PRACTICE** — правило, тренировка или персональная помощь.
5. **VERIFY** — новый независимый item без помощи.
6. **RETAIN** — проверка навыка позже.
7. **REASSESS** — контроль/демоверсия проверяет перенос в экзамен.
8. **REPLAN** — маршрут и прогноз пересчитываются.

Функции, не усиливающие этот цикл и не дающие самостоятельной ценности, имеют меньший приоритет.

## 4. Как существующие продукты входят в новую систему

### Демоверсии

Остаются максимально точными симуляторами официального экзамена и не становятся адаптивными внутри экзаменационного режима.

Дополнительная роль: **диагностический сенсор**. После попытки демоверсия должна передавать структурированные evidence-события в Student Model, а не только итоговый балл.

### ЕГЭ-тренажёр

Становится **двигателем персонального маршрута и подтверждения mastery**. Он должен принимать handoff из диагностики и автоматически собирать работу над конкретными слабостями.

### Тематические тренажёры

Ударения, словарные слова, паронимы, фразеологизмы, исключения и будущие тренажёры не должны иметь отдельные несвязанные модели прогресса. Проверяемые items связываются со стабильными semantic/skill identities и, где применимо, пишут evidence в единый Student Model.

### Полная программа по русскому языку

Полная программа — **не отдельный линейный курс**. Она является knowledge layer новой системы:

- каноническая карта навыков/решений;
- проверенные правила и объяснения;
- prerequisite relationships;
- исключения и контрасты;
- база adaptive practice;
- база AI Tutor / retrieval;
- база диагностики причин ошибок;
- база retention/transfer.

### Explanation Bank, exceptions, essay criteria

Это части общего verified knowledge/evidence layer. Они должны обслуживать deterministic feedback, AI-разбор, tutor dialogue, post-help verification и будущие multimodal/voice сценарии.

## 5. Текущее состояние русского и обязательная authority

На 2026-08-18 текущая предметная authority:

`266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json`

Текущий canonical school denominator: **185 semantic identities**.

137 и 179 — исторические checkpoint и не являются current denominator.

Следующий предметный шаг уже зафиксирован current authority: **аудит покрытия существующего русского тренажёра против 185 semantic identities и отдельных маршрутов ЕГЭ/ОГЭ**.

Критическое правило:

> существующий Skill Graph, 185 canonical identities, demo task map, trainer items и full-program content должны быть сведены в одну непротиворечивую identity model.

Нельзя создавать вторую параллельную ontology только потому, что появился новый курс, тренажёр или AI-функция.

## 6. Student Learning Twin

Рабочее внутреннее понятие: **Student Learning Twin**.

Это не профиль с процентами. Для skill/subskill система постепенно хранит доказательства:

- mastery state;
- последние attempts;
- повторяющиеся error patterns;
- response time и аномально долгие решения;
- answer changes / revisits при доступности данных;
- результат после подсказки;
- NIC-1 / NIC-3;
- transfer;
- retention;
- давность проверки;
- confidence/calibration при наличии данных;
- prerequisite gaps;
- intervention effectiveness — какой тип помощи реально улучшил следующий независимый ответ.

Персонализация способа объяснения должна опираться на наблюдаемый результат, а не на псевдотипологии вроде «визуал/аудиал».

## 7. Чем Эксамио должен превосходить обычный adaptive tutor

Диагностика -> персональный план -> адаптивные задания -> повторная проверка уже является мировым benchmark. Этого недостаточно как дифференциации.

Целевые преимущества Эксамио:

### Score Gain per Minute

Recommendation Engine оптимизирует ожидаемую полезность следующего шага:

`expected_exam_gain / expected_study_time`

Система должна уметь ответить: **где этот ученик сейчас быстрее всего вернёт экзаменационные баллы?**

### Error Fingerprint

С evidence/confidence различать хотя бы:

- knowledge gap;
- prerequisite gap;
- confusion between similar rules;
- application error;
- reading/formulation error;
- unstable skill;
- retention failure;
- likely accidental error;
- high-confidence wrong answer.

### Intervention Effectiveness

После помощи измерять не «понравилось объяснение», а успешность нового item, серии, transfer и retention.

### Calibrated Score Forecast

Прогноз — диапазон с неопределённостью. Качество прогноза измеряется на последующих контрольных попытках.

### Explainable Recommendation

Система объясняет, почему конкретный шаг приоритетен: какие evidence, экзаменационная ценность, retention state и история ошибок привели к решению.

## 8. Три продуктовых слоя

### Eksamio Base — бесплатный

Базовый learning loop не paywall:

- демоверсии;
- тренажёры;
- базовая проверка;
- карта слабых мест;
- работа над ошибками;
- demo -> trainer handoff;
- базовый персональный маршрут;
- next-item correctness;
- spaced repetition;
- базовая карта навыков;
- control/reassessment.

### Eksamio Intelligence — платный персональный слой

Платными могут быть вычислительно дорогие индивидуальные функции:

- глубокий AI-разбор ошибки;
- персональный текстовый AI Tutor;
- расширенный Error Fingerprint;
- долгосрочная оптимизация маршрута;
- расширенный score forecast;
- AI-проверка сочинения/развёрнутого ответа как учебная оценка;
- персональные аналитические отчёты.

### Eksamio Live — более поздний realtime/multimodal слой

- голосовой AI Tutor;
- фото/vision-разбор работы ученика;
- разговорное занятие;
- совместный разбор черновика/изображения;
- realtime coaching.

**Voice не является первым MVP.** Сначала система должна доказать, что правильно диагностирует и исправляет навык в структурированном/text контуре.

## 9. AI: роль и ограничения

AI — reasoning/teaching layer поверх verified structure.

AI может:

- объяснять конкретную ошибку;
- задавать наводящие вопросы;
- менять форму объяснения;
- формировать персональный разбор из structured evidence;
- выдвигать гипотезу причины ошибки с confidence;
- вести диалог по verified knowledge base;
- проверять развёрнутые ответы по явной rubric в учебном режиме;
- позже работать с фото/голосом.

AI **не является source of truth** для:

- официальных ответов;
- критериев;
- task numbering;
- scoring;
- exam rules;
- canonical skill identity;
- mastery state без deterministic policy/evidence contract.

После AI-помощи, где применимо, обязателен новый независимый verification item.

Базовый help ladder:

1. микроподсказка;
2. наводящий вопрос;
3. указание места/типа ошибки;
4. объяснение правила;
5. полный разбор;
6. новый независимый пример без помощи.

## 10. Архитектура данных

Non-negotiable:

> демоверсия, тренажёр, тематические тренажёры, полная программа и AI используют один semantic/skill identity space и один Student Model.

Минимальные доменные сущности:

- `StudentProfile`;
- `SkillIdentity` / `SubskillIdentity`;
- `ExamRoute`;
- `ContentUnit`;
- `DemoItem`;
- `TrainerItem`;
- `Attempt`;
- `EvidenceEvent`;
- `StudentSkillState`;
- `ErrorHypothesis`;
- `Intervention`;
- `Recommendation`;
- `RecommendationResult`;
- `RetentionSchedule`;
- `ControlAttempt`;
- `ScoreForecast`.

До завершения coverage/mapping audit нельзя считать current trainer snapshot доказательством полного покрытия 185 identities.

## 11. Eksamio-first, Living-Core-aware

Не строить сейчас абстрактную универсальную платформу для всех будущих проектов до запуска работающего Эксамио.

Стратегия: **product-first, core-aware**.

Сначала строится замкнутый контур Эксамио. При этом интерфейсы, которые очевидно переиспользуются, отделяются от предметной логики.

Потенциально shared Living Core services:

- identity/account;
- session/memory service;
- AI Gateway/provider routing;
- knowledge retrieval;
- usage/cost accounting;
- entitlements/billing limits;
- safety/moderation;
- analytics/experimentation;
- audit/logging;
- media/audio storage.

Eksamio domain core не надо преждевременно делать generic:

- Skill Graph;
- exam routes;
- mastery logic;
- recommendation policy;
- score forecast;
- exam scoring;
- subject source authority;
- learning evidence semantics.

Позже доказанные shared services могут обслуживать Dilivox, MarketVox и другие проекты.

## 12. Provider architecture

Предметная логика не зависит напрямую от конкретного AI/cloud provider.

OpenAI через AI Gateway — reasoning, structured analysis, text tutoring, vision, realtime voice, tools/function calling и подходящие retrieval-сценарии.

Yandex — SpeechKit/массовый TTS, производственная аудиостудия и облачная инфраструктура (serverless/backend/storage/database/API) там, где это экономически и технически оправдано.

Provider-specific model/API не должен становиться частью Student Model или subject source-of-truth.

Нужны provider abstraction, model/version logging, prompt/policy version logging, cost telemetry, fallback policy и feature flags.

## 13. Приоритет реализации

### P0 — сейчас

1. Этот masterplan и hierarchy of authority.
2. Не останавливать verified production-работу по демоверсиям.
3. Завершить Russian trainer coverage audit против **185 identities** и FIPI route overlays.
4. Свести Skill Graph + 185 identities + demo task map + trainer items + full-program content в единую identity model.
5. Зафиксировать stable ID/contracts v1.
6. Зафиксировать Student / Attempt / Evidence / StudentSkillState / Event contracts.
7. Реализовать и проверить один полный vertical slice: `demo -> diagnosis -> trainer -> verify`.
8. Начать outcome telemetry: NIC-1, NIC-3, transfer, retention, recommendation result.
9. Только затем подключить первый AI-разбор поверх structured evidence.

### P0.5 — первый монетизируемый AI-срез

`attempt -> failed skill -> grounded AI explanation -> personalized help -> independent item -> measured outcome`

Первый AI-продукт: **AI-разбор результата / конкретной ошибки + следующий проверочный шаг**.

Не начинать с универсального пустого чата.

### P1

- text AI Tutor;
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

- realtime voice tutor;
- multimodal live sessions;
- richer Student Learning Twin;
- proactive replanning;
- long-term cross-session personalization.

### P4

- перенос ядра на другие предметы;
- cross-subject profile;
- dashboards при доказанной потребности;
- извлечение proven shared Living Core services;
- internationalization после product-market proof.

## 14. Что не делать сейчас

- Не строить generic AI-чат для ЕГЭ.
- Не запускать voice первым AI-продуктом.
- Не делать отдельные базы прогресса для демоверсии, тренажёра и программы.
- Не создавать вторую Skill Graph/ontology поверх current canonical layer.
- Не давать AI владеть official answers/scoring.
- Не ставить завершение 100% всей программы блокером первого безопасного AI vertical slice.
- Не строить всю абстрактную Living Worlds platform раньше работающего Eksamio loop.
- Не оптимизировать продукт прежде всего по времени на сайте/числу сообщений.
- Не менять verified production demo content ради персонализации.
- Не переносить старые разрозненные localStorage состояния в cloud как есть без versioned data contract.

## 15. Главные метрики

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

## 17. Что означает «выше мировых»

Это целевой стандарт разработки, а не маркетинговая декларация.

Он будет доказан только если одновременно есть:

1. exam fidelity;
2. verified semantic knowledge structure;
3. longitudinal learner model с transfer/retention;
4. optimization по learning outcome / exam gain, а не engagement;
5. grounded AI с измеримым error rate;
6. post-intervention proof;
7. calibrated prediction;
8. multimodal UX там, где он улучшает обучение;
9. архитектурное разделение deterministic truth и AI inference;
10. масштабируемая экономика на активного ученика.

## 18. Ближайшая обязательная последовательность

Если нет более нового явно утверждённого product decision:

1. Russian 185 trainer coverage audit.
2. Unified Russian identity/mapping contract.
3. Demo/trainer/full-program data alignment.
4. Student + Attempt + Evidence + StudentSkillState schema v1.
5. Demo -> trainer handoff vertical slice.
6. NIC/transfer/retention measurement.
7. AI Review MVP на verified vertical slice.
8. Usage/cost/eval telemetry.
9. Account/server sync + entitlements для платного rollout.
10. Text AI Tutor.
11. Student Learning Twin / Recommendation Engine expansion.
12. Essay/vision.
13. Voice realtime.
14. Scale to other subjects.
15. Extract proven shared Living Core services.

## 19. Change control

Следующие решения нельзя молча менять историческим checkpoint или локальной задачей:

- `eksamio-learning-engine/` — корень новой системы;
- единый semantic/skill identity layer;
- единый Student Model;
- бесплатный базовый learning loop;
- AI не является source of truth;
- порядок Base -> Intelligence -> Live;
- Eksamio-first / Living-Core-aware strategy;
- learning outcome важнее engagement;
- provider abstraction.

Если требуется изменить одно из этих решений — обновить этот masterplan или создать явный ADR/product decision.

## 20. Короткая формула

**Имеем:** демоверсии + тренажёры + verified subject content + русский Learning Engine.

**Строим:**

`точный экзамен -> Student Learning Twin -> следующий лучший шаг -> персональная помощь -> независимая проверка -> retention -> прогноз -> новый план`

Именно эта система, а не отдельный AI-чат, является целевым продуктом Эксамио.
