# Eksamio — Product Masterplan

**Статус:** PRODUCT / ARCHITECTURE AUTHORITY  
**Версия:** 1.0  
**Дата фиксации:** 2026-08-18  
**Первый домен реализации:** ЕГЭ — русский язык  
**Цель:** превратить набор демоверсий, тренажёров и учебных материалов в единую персональную систему подготовки к экзамену с измеримым результатом обучения.

---

## 1. Назначение этого документа

Этот файл задаёт верхнеуровневую продуктовую цель Эксамио, архитектурные границы и порядок реализации.

Он нужен для того, чтобы демоверсии, тренажёры, полная программа по русскому, Learning Engine, AI-функции и будущие предметы не развивались как независимые продукты, которые потом приходится сшивать задним числом.

**Главное правило:** все новые части Эксамио должны усиливать один замкнутый learning loop и одну модель ученика.

Этот документ НЕ заменяет:

- регламенты точности демоверсий;
- официальные источники ФИПИ;
- предметные source gates;
- текущие frozen/source authority-файлы русского языка;
- конкретные task/review/result-файлы.

Он определяет, **во что всё это должно собраться как продукт**.

---

## 2. Иерархия источников истины

При конфликте инструкций использовать следующий порядок.

### Уровень 1 — продукт и архитектура

`00-EKSAMIO-PRODUCT-MASTERPLAN.md`

Определяет:

- конечный продукт;
- общую архитектуру;
- продуктовые границы;
- приоритеты реализации;
- роль AI;
- роль Learning Engine;
- связь демоверсий, тренажёров и учебной программы.

### Уровень 2 — производственная точность конкретного контура

Для демоверсий:

- `00-READ-FIRST-EGE-DEMOVERSII-MASTER.md`;
- `demo-production-standard/README.md`;
- предметные регламенты;
- source gates и официальные материалы нужного экзаменационного цикла.

Для Learning Engine:

- `eksamio-learning-engine/AGENTS.md`;
- `eksamio-learning-engine/00-WORK-STATUS.txt`;
- `eksamio-learning-engine/COMMUNICATION-PROTOCOL.md`;
- `eksamio-learning-engine/02-CODEX-BUILD-INDEX.txt`.

### Уровень 3 — текущая предметная authority chain

Для русского языка действует **последняя явно зафиксированная current/final authority**, а не старое числовое значение из исторического checkpoint.

На дату этого документа текущая authority:

`eksamio-learning-engine/266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json`

Текущий canonical school denominator: **185 semantic identities**.

Значения 137 и 179 являются историческими checkpoint и не должны возвращаться как current denominator.

### Уровень 4 — конкретная задача

Task/spec/review может уточнять способ реализации, но не может молча менять продуктовую архитектуру, официальный exam truth или действующую предметную authority.

Если обнаружено реальное противоречие, работа должна остановиться на этом конфликте и он должен быть явно зафиксирован. Нельзя разрешать архитектурный конфликт «по памяти».

---

## 3. Что такое Эксамио на выходе

Эксамио — не каталог материалов и не чат-бот для ЕГЭ.

Целевая модель:

> **Eksamio = Personal Exam Intelligence System**
>
> Система знает, какие навыки экзамена существуют, какие из них конкретный ученик действительно освоил, где именно и почему он теряет баллы, что выгоднее учить следующим и подтвердилось ли обучение на новом независимом задании и через время.

Главная единица ценности — не просмотренный урок и не ответ AI.

Главная единица ценности — **доказанное изменение состояния знания ученика и ожидаемого экзаменационного результата**.

---

## 4. Единый замкнутый learning loop

Все продуктовые модули должны замыкаться в цикл:

`DIAGNOSE -> MODEL -> PRIORITIZE -> TEACH/PRACTICE -> VERIFY -> RETAIN -> REASSESS -> REPLAN`

Расшифровка:

1. **DIAGNOSE** — демоверсия, контрольная, отдельное задание или входная диагностика показывают фактическую ошибку.
2. **MODEL** — ошибка привязывается к skill/subskill и обновляет состояние ученика.
3. **PRIORITIZE** — система выбирает следующий лучший шаг.
4. **TEACH/PRACTICE** — ученик получает правило, объяснение, тренировку или AI-помощь.
5. **VERIFY** — после помощи даётся новый независимый item того же навыка.
6. **RETAIN** — система проверяет, сохранился ли навык позже.
7. **REASSESS** — контрольная/демоверсия проверяет перенос в экзаменационный контекст.
8. **REPLAN** — маршрут и прогноз пересчитываются.

Любая функция, которая не усиливает этот цикл и не даёт самостоятельной пользовательской ценности, имеет более низкий приоритет.

---

## 5. Что уже есть и во что это превращается

### 5.1. Демоверсии

Текущее назначение: максимально точное воспроизведение экзамена, таймер, навигация, ответы, scoring/self-check.

Целевое назначение дополнительно:

> **диагностический сенсор системы**.

Демоверсия остаётся неадаптивной и сохраняет официальный порядок. Персонализация начинается после завершения или за пределами экзаменационного режима.

После попытки демоверсия должна отдавать структурированные evidence-события в Student Model, а не только итоговый балл.

### 5.2. Тренажёр ЕГЭ

Текущее назначение: практика заданий и повтор ошибок.

Целевое назначение:

> **исполнитель персонального маршрута и двигатель подтверждения mastery**.

Тренажёр должен уметь принять handoff из демоверсии и автоматически собрать релевантную работу над ошибками.

### 5.3. Тематические тренажёры

Ударения, словарные слова, паронимы, фразеологизмы, исключения и будущие тематические тренажёры не должны быть отдельными островами данных.

Каждый проверяемый item должен быть связан со стабильными semantic/skill identifiers и при возможности писать evidence в тот же Student Model.

### 5.4. Полная программа по русскому языку

Полная программа — **не отдельный линейный курс, конкурирующий с тренажёрами**.

Она является одновременно:

- проверенным knowledge layer;
- канонической картой школьных решений/навыков;
- источником объяснений;
- источником контрастов и исключений;
- базой для adaptive practice;
- базой для AI Tutor/RAG;
- базой для диагностики пробелов prerequisite;
- базой для повторения до уровня retention/transfer.

На 2026-08-18 current canonical denominator русского — **185 semantic identities** после Rosenthal/current-norm normalization и official FIPI 2026 backstop/overlay.

Следующий предметный шаг уже определён текущей authority: провести coverage audit существующего русского тренажёра против этих 185 identities и отдельных маршрутов ЕГЭ/ОГЭ.

### 5.5. Explanation Bank / exceptions / essay criteria

Это не побочные контентные проекты.

Они становятся проверенным knowledge/evidence layer для:

- deterministic feedback;
- AI-разбора;
- tutor dialogue;
- post-help verification;
- essay/self-check;
- последующего multimodal/voice tutoring.

---

## 6. Три продуктовых слоя

### Eksamio Base — бесплатная система подготовки

Не paywall:

- интерактивные демоверсии;
- тренажёры;
- базовая проверка;
- карта слабых мест;
- работа над ошибками;
- demo -> trainer handoff;
- базовый персональный маршрут;
- next-item correctness;
- spaced repetition;
- базовая карта навыков;
- контроль и reassessment.

Бесплатный контур должен быть полезным сам по себе.

### Eksamio Intelligence — платная персональная вычислительная работа

Платным может быть то, что требует дорогой индивидуальной обработки и создаёт дополнительную ценность:

- глубокий AI-разбор конкретной ошибки;
- персональный AI Tutor;
- расширенная диагностика error fingerprint;
- долгосрочная оптимизация маршрута;
- расширенный score forecast;
- AI-проверка сочинения/развёрнутого ответа как учебная оценка;
- сравнение нескольких стратегий подготовки;
- объяснение «почему именно это задание сейчас»;
- углублённые персональные отчёты.

### Eksamio Live — realtime и multimodal слой

Позже, после доказанной пользы текстового Intelligence:

- голосовой AI Tutor;
- фото/vision-разбор записи ученика;
- разговорное занятие;
- совместный разбор изображения/черновика;
- realtime coaching.

**Voice не является первым MVP.** Сначала система должна доказать, что умеет правильно диагностировать и исправлять навык в текстовом/структурированном контуре.

---

## 7. Главное конкурентное преимущество: Student Learning Twin

Внутреннее рабочее понятие: **Student Learning Twin**.

Это не «профиль с процентами».

Для каждого skill/subskill система должна постепенно хранить доказательства о состоянии знания:

- mastery state;
- последние попытки;
- повторяющиеся типы ошибок;
- скорость/аномально долгие решения;
- ответ после подсказки;
- next-item correctness;
- NIC-3;
- transfer;
- retention;
- давность последней проверки;
- confidence/calibration при наличии данных;
- prerequisite gaps;
- response-to-intervention: какой тип объяснения/помощи реально улучшил следующий независимый ответ.

Нельзя утверждать, что ученик «визуал», «аудиал» и т. п. по предположению. Персонализация метода должна опираться на наблюдаемое улучшение результата.

---

## 8. Уровень выше обычного adaptive tutor

К 2026 году диагностика -> персональный план -> адаптивные уроки -> повторные квизы уже является мировым benchmark, а не уникальностью.

Поэтому целевая дифференциация Эксамио должна быть глубже.

### 8.1. Score Gain per Minute

Recommendation Engine должен оптимизировать не «процент прохождения курса», а ожидаемую полезность следующего шага.

Рабочая целевая функция:

`expected_exam_gain / expected_study_time`

Система должна уметь ответить:

> Где конкретно этот ученик сейчас быстрее всего вернёт экзаменационные баллы?

### 8.2. Error Fingerprint

Система различает хотя бы:

- knowledge gap;
- prerequisite gap;
- confusion between similar rules;
- application error;
- reading/formulation error;
- unstable skill;
- retention failure;
- likely accidental error;
- high-confidence wrong answer.

Классификация должна иметь evidence/confidence и не должна выдаваться как факт при недостатке данных.

### 8.3. Intervention Effectiveness

После любой помощи измеряется не «понравилось объяснение», а:

- смог ли ученик решить новый item без помощи;
- смог ли решить серию;
- перенёс ли принцип в изменённую ситуацию;
- сохранил ли навык позже.

### 8.4. Calibrated Score Forecast

Прогноз должен быть диапазоном с неопределённостью, а не ложным числом «вы получите 84».

Нужно измерять калибровку прогноза на реальных последующих контрольных попытках.

### 8.5. Explainable Recommendation

Для каждого важного персонального решения система должна уметь объяснить причину человеческим языком:

> «Эта тема сейчас приоритетна, потому что вы ошиблись в ней дважды, она влияет на задания с такой-то экзаменационной ценностью, а последняя успешная попытка была давно».

---

## 9. Архитектура данных: один skill-space, не три продукта

Критическое non-negotiable правило:

> Демоверсия, тренажёр, полная программа и AI не имеют независимых конкурирующих карт навыков.

Нужен единый стабильный semantic/skill identity layer с предметными маршрутами поверх него.

Каждый релевантный объект должен иметь стабильный идентификатор и версию.

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

Существующий 185-identity Russian layer и существующий Skill Graph должны быть **сопоставлены и нормализованы**, а не превращены в две параллельные ontology.

До завершения coverage/mapping audit нельзя автоматически считать текущий snapshot тренажёра полным покрытием 185 identities.

---

## 10. AI: роль и границы

AI — teacher/reasoning layer поверх проверенной структуры, а не владелец exam truth.

AI может:

- объяснять ошибку;
- задавать наводящие вопросы;
- адаптировать форму объяснения;
- формировать персональный разбор из структурированных evidence;
- помогать классифицировать возможную причину ошибки с confidence;
- вести диалог по проверенной knowledge base;
- проверять развёрнутые ответы в учебном режиме по явной rubric;
- работать с фото/голосом на поздних этапах.

AI не является source of truth для:

- официальных ответов;
- критериев;
- task numbering;
- scoring;
- exam rules;
- canonical skill identity;
- mastery state без deterministic policy/evidence contract.

После AI-помощи система обязана, где применимо, дать независимый verification item.

### Help ladder

Базовый tutor protocol:

1. микроподсказка;
2. наводящий вопрос;
3. указание места/типа ошибки;
4. объяснение правила;
5. полный разбор;
6. новый независимый пример без помощи.

AI не должен по умолчанию превращаться в генератор готовых ответов.

---

## 11. Технологическая стратегия: Eksamio-first, Living-Core-aware

Не строить сейчас абстрактную универсальную платформу для всех будущих проектов до запуска Эксамио.

Правильная стратегия:

> **product-first, core-aware**.

Сначала строим работающий замкнутый контур Эксамио, но сразу отделяем переиспользуемые сервисы от предметной логики.

### Shared Living Core services

Можно проектировать как независимые интерфейсы:

- identity/account;
- session/memory service;
- AI Gateway и provider routing;
- knowledge retrieval;
- usage/cost accounting;
- entitlements/billing limits;
- safety/moderation;
- analytics/experimentation;
- audit/logging;
- media/audio storage.

### Eksamio domain core

Не выносить преждевременно в generic core:

- Skill Graph;
- exam routes;
- mastery logic;
- recommendation policy;
- score forecast;
- exam scoring;
- subject source authority;
- learning evidence semantics.

Позже shared core может обслуживать Dilivox, MarketVox и другие продукты, но предметная логика Эксамио должна оставаться чистой.

---

## 12. Provider architecture

Доменная логика не должна зависеть напрямую от одного AI/cloud provider.

### OpenAI

Использовать через AI Gateway для:

- reasoning;
- structured AI analysis;
- text tutoring;
- vision;
- realtime voice;
- tool/function calling;
- retrieval/file-search scenarios where appropriate.

### Yandex

Использовать для:

- SpeechKit / массового TTS;
- производственной аудиостудии;
- Yandex Cloud infrastructure;
- serverless backend/storage/database/API where экономически и технически оправдано.

### Правило

Provider-specific model name/API schema не должен становиться частью Student Model или предметной source-of-truth структуры.

Нужны:

- provider abstraction;
- model/version logging;
- prompt/policy version logging;
- cost telemetry;
- fallback policy;
- feature flags.

---

## 13. Приоритет реализации

### P0 — СЕЙЧАС: объединить фундамент до наращивания функций

1. Зафиксировать этот Product Masterplan и hierarchy of authority.
2. Не останавливать текущую verified production-работу по демоверсиям.
3. Завершить текущий Russian trainer coverage audit против **185 semantic identities** и FIPI route overlays.
4. Сопоставить существующий Skill Graph, 185 canonical identities, demo task map, trainer items и full-program content в одну непротиворечивую identity model.
5. Заморозить стабильные ID/contracts v1 до массовой интеграции.
6. Зафиксировать Student/Attempt/Evidence/StudentSkillState/Event contracts.
7. Реализовать/проверить `demo -> diagnosis -> trainer -> verify` на одном узком вертикальном срезе русского.
8. Обязательно начать писать learning outcome telemetry: NIC-1, NIC-3, transfer, retention, recommendation result.
9. Только после этого подключить первый AI-разбор поверх структурированных данных.

### P0.5 — ПЕРВЫЙ МОНЕТИЗИРУЕМЫЙ AI-СРЕЗ

Приоритет AI-функции №1:

> **AI-разбор результата / конкретной ошибки + следующий проверочный шаг.**

Минимальный поток:

`attempt -> failed skill -> grounded explanation -> personalized help -> new independent item -> measured outcome`

Не начинать с универсального пустого чата.

Для старта не требуется завершить 100% всей будущей программы, если выбранный vertical slice имеет полный source/coverage/eval gate.

### P1 — СЕНТЯБРЬ / ПОСЛЕ СТАБИЛЬНОГО P0

- текстовый AI Tutor;
- единый аккаунт и server sync;
- персональная «Тренировка на сегодня»;
- retention schedule;
- Recommendation Engine;
- Error Fingerprint v1;
- платные entitlements/limits;
- расширенная аналитика AI cost/outcomes;
- первая версия Student Learning Twin.

### P2

- AI essay/extended-answer evaluation с criterion-by-criterion evidence и uncertainty;
- calibrated score forecast;
- dynamic plan to exam;
- confidence calibration;
- vision/photo разбор;
- learning intervention experiments.

### P3

- realtime voice tutor;
- multimodal live sessions;
- richer Student Learning Twin;
- proactive replanning;
- cross-session long-term personalization.

### P4

- перенос ядра на другие предметы;
- cross-subject student profile;
- parent/teacher dashboards при доказанной потребности;
- выделение реально переиспользуемых Living Core services для Dilivox/MarketVox;
- internationalization только после product-market proof.

---

## 14. Что НЕ делать сейчас

- Не строить generic «AI-чат для ЕГЭ».
- Не запускать voice первым AI-продуктом.
- Не делать отдельные базы прогресса для демоверсии, тренажёра и полной программы.
- Не создавать вторую независимую Skill Graph/ontology поверх current 185 layer.
- Не давать AI владеть официальными ответами/scoring.
- Не ставить завершение всей русской программы как обязательный блокер первого безопасного AI vertical slice.
- Не строить всю абстрактную Living Worlds platform раньше работающего Eksamio loop.
- Не оптимизировать продукт по времени на сайте, числу AI-сообщений или числу просмотренных уроков как главным success metrics.
- Не менять verified production demo content ради персонализации.
- Не переносить текущие localStorage-разрозненные состояния в cloud «как есть» без нормального data contract/versioning.

---

## 15. Метрики продукта

### Learning metrics — главные

- NIC-1;
- NIC-3;
- transfer success;
- retention success;
- mastery gain;
- repeat-error rate;
- time-to-mastery;
- exam score delta between controls;
- expected/actual score gain per study minute;
- forecast calibration.

### AI tutor metrics

- outcome after help;
- answer leakage/direct-answer rate;
- unsupported/factual error rate;
- latency;
- cost per successful learning intervention;
- escalation/fallback rate.

### Product/business metrics

- diagnosis -> practice conversion;
- repeat study days;
- paid conversion after demonstrated free value;
- paid retention;
- AI cost as share of revenue;
- share of users with measurable improvement.

Время на сайте и число сообщений являются диагностическими, но не главными метриками качества обучения.

---

## 16. AI quality/evaluation gate

Каждая новая AI-функция до массового rollout должна иметь фиксированный eval set.

Минимум проверять:

- factual/source correctness;
- правильную привязку к skill;
- отсутствие подмены official answer;
- педагогический protocol;
- отсутствие преждевременной выдачи ответа;
- корректную uncertainty;
- выполнение structured output contract;
- post-help next-item outcome на реальных данных после запуска.

AI не должен оценивать собственное качество единственным судьёй. Нужны deterministic checks, source-backed fixtures и/или независимый reviewed evaluation contour.

---

## 17. Принцип монетизации

Бесплатная часть доказывает ценность платформы и даёт полноценный learning loop.

Платная часть продаёт:

> дополнительную персональную интеллектуальную работу системы.

Нельзя специально ухудшать бесплатную диагностику/тренировку для создания Premium.

Платные функции должны иметь явную вычислительную или персональную ценность.

Для дорогих realtime/vision/essay функций разрешены квоты/лимиты, связанные с себестоимостью.

---

## 18. Что означает «уровень выше мировых» внутри проекта

Это не маркетинговая фраза и не статус, который можно присвоить себе документом.

Эксамио может претендовать на такой уровень только если одновременно доказаны:

1. **Exam fidelity** — официальная часть воспроизводится точнее обычных учебных симуляторов.
2. **Knowledge structure** — предмет разложен на проверенную semantic model, а не на произвольные теги.
3. **Longitudinal learner model** — система знает не только текущий ответ, но transfer/retention/error history.
4. **Outcome optimization** — рекомендации оптимизируются по реальному эффекту на результат, а не engagement.
5. **Grounded AI** — AI работает поверх verified knowledge/evidence и имеет измеримый error rate.
6. **Intervention proof** — после помощи проверяется, научился ли ученик.
7. **Calibrated prediction** — прогнозы измеряются и калибруются.
8. **Multimodal natural UX** — фото/голос подключаются там, где реально улучшают обучение.
9. **Trust** — deterministic truth и AI inference разделены архитектурно.
10. **Economics** — система масштабируется без разрушительной стоимости на активного ученика.

До появления данных это **целевой стандарт разработки**, а не публичное утверждение.

---

## 19. Ближайшая обязательная последовательность

Если нет более нового явно утверждённого product decision, следующий порядок считать приоритетным:

1. Russian 185 trainer coverage audit.
2. Unified Russian identity/mapping contract.
3. Demo/trainer/full-program data alignment.
4. Student + Attempt + Evidence + StudentSkillState schema v1.
5. Demo -> trainer handoff vertical slice.
6. NIC/transfer/retention measurement.
7. AI Review MVP на verified vertical slice.
8. Usage/cost/eval telemetry.
9. Account/server sync + entitlements when needed for paid rollout.
10. Text AI Tutor.
11. Student Learning Twin / Recommendation Engine expansion.
12. Essay/vision.
13. Voice realtime.
14. Scale to other subjects.
15. Extract proven shared Living Core services.

---

## 20. Change control

Изменение одного из следующих решений требует явного обновления этого masterplan или отдельного ADR/product-decision, на который он ссылается:

- бесплатный базовый learning loop;
- единый skill/semantic identity layer;
- AI не является source of truth;
- порядок Base -> Intelligence -> Live;
- Eksamio-first / core-aware strategy;
- приоритет измеримого learning outcome над engagement;
- provider abstraction;
- текущая продуктовая цель.

Исторический checkpoint не может молча отменить этот документ.

---

## 21. Короткая формула проекта

**Сейчас:**

`демоверсии + тренажёры + материалы + русский learning engine`

**Цель:**

`точный экзамен -> цифровая модель знаний ученика -> следующий лучший шаг -> персональная помощь -> независимая проверка -> удержание -> прогноз -> новый план`

Именно эта система, а не отдельный AI-чат, является целевым продуктом Эксамио.
