# Eksamio Learning Engine — Product Masterplan

**Статус:** PRODUCT / ARCHITECTURE AUTHORITY  
**Версия:** 1.5
**Дата исходной фиксации:** 2026-08-18  
**Актуализация:** 2026-08-31
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
- realtime voice AI Tutor.

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

## 23. Full Subject source completeness, source archive и runtime independence

Это глобальные launch-инварианты Eksamio и они обязательны вместе с:

- `FULL-SUBJECT-SOURCE-AND-TEXTBOOK-INGESTION-POLICY-v0.1.md`;
- `FULL-SUBJECT-TEXTBOOK-INGESTION-PRIORITY-2026-08-23.md`;
- `SOURCE-ARCHIVE-AND-PRODUCT-KNOWLEDGE-STORAGE-POLICY-v0.1.md`;
- `LOCAL-WORKSPACE-POLICY.md`.

### Full Subject scope — launch-blocking

Полноценный платный предмет нельзя считать готовым только потому, что существуют демоверсии, ФИПИ-корпус, тренажёры или частичная semantic inventory.

Для каждого полного предмета обязателен gate `FULL_SUBJECT_SCOPE_SOURCE_COMPLETE`: нормативная школьная программа должна быть полностью покрыта source-backed semantic model, а обязательные элементы не могут молча исчезать только потому, что они не встречаются в текущем ЕГЭ/ОГЭ.

Источник полного предметного scope строится иерархически:

`official school-program authority -> canonical semantic capabilities -> textbooks/pedagogical evidence -> exam/diagnostic overlays -> original Eksamio content -> shared PEIS`.

Учебники являются knowledge/pedagogy evidence, но не автоматически canonical truth и не разрешением копировать learner-facing текст или банки задач.

### Последовательность первой source/textbook wave

Первая волна строго последовательная:

`Russian -> Mathematics -> Physics`.

Активный шаг на 2026-08-23: `RUSSIAN_TEXTBOOK_SELECTION_MATRIX`.

Нельзя batch-download Русский до принятия матрицы. Нельзя начинать Mathematics source/textbook acquisition до `FULL_SUBJECT_SCOPE_SOURCE_COMPLETE` Русского. Нельзя начинать Physics source/textbook acquisition до такого же PASS Математики.

Central PEIS/Tutor/infrastructure работа может идти параллельно, если она не подменяет отсутствующую предметную истину.

### Source Archive != Product Knowledge Store

Исходный выбранный учебник сохраняется как Source Archive для provenance, повторного ingestion, аудита и сравнения изданий, когда это допускается rights/retention policy.

GitHub хранит каталог, hashes, locators, statuses и ingestion provenance. Production knowledge layer хранит уже проверенные структурированные Eksamio knowledge/artifacts, а не целые учебники по умолчанию.

Google Drive допускается как начальный bounded Source Archive, но **никогда не является production hot path**.

После успешного ingestion нормальная работа Eksamio в Yandex должна продолжаться при полной недоступности Google Drive:

- PEIS работает;
- Tutor работает на уже принятом structured knowledge;
- диагностика и тренажёры работают;
- learner-facing проверка и learning loop работают;
- никакой emergency fetch целого PDF из Drive в runtime не допускается.

Недоступность Drive может блокировать только операции, которым действительно нужен raw source binary: первичный ingestion, re-ingestion, page-level source audit, edition comparison или dispute resolution.

Если Yandex runtime не способен продолжать normal learner operation без Google Drive после ingestion, соответствующий production gate считается FAIL.

### Срочность перед учебным годом

На 2026-08-23 до 1 сентября остаётся короткое launch-окно. Поэтому приоритет — не формальное закрытие документов, а получение **реально работающего первого контура Русского**, который опирается на проверенную предметную истину и не создаёт ложного claim полноты.

До 1 сентября и в начале учебного года приоритеты должны оцениваться по тому, насколько они приближают работающий путь:

`verified Russian scope -> PEIS evidence -> personalized practice/help -> independent verification -> retained state`.

Нельзя ради календаря обходить source truth, security, identity, Tutor verification или privacy gates. Но нельзя и откладывать первый полезный working contour ради необязательной архитектурной полноты других предметов или поздних функций.

## 24. Russian learner product family and progressive rollout — owner clarification 2026-08-31

Полная программа Русского языка является **единой предметной базой для всей линейки ученических продуктов**, а не только «курсом».

Из одной принятой canonical Russian knowledge/content layer должны последовательно собираться и открываться:

- бесплатные демоверсии и диагностики;
- работа над ошибками;
- тематические тренажёры;
- ЕГЭ-тренажёры;
- ОГЭ-тренажёры;
- **конструктор тренажера**, который собирает тренировку из уже принятых canonical skills/items по выбранным темам, типам заданий, объёму и допустимой сложности;
- персональная «Тренировка на сегодня»;
- полный учебный маршрут / курс Русского;
- школьные маршруты 5–11 классов;
- подготовка к ОГЭ;
- подготовка к ЕГЭ;
- персональная работа с prerequisite gaps;
- text + realtime voice Tutor;
- независимая проверка после помощи;
- retention/spaced practice;
- карта слабых мест, прогресс и readiness;
- персональный план до экзамена;
- essay/extended-answer support после отдельного rubric/eval gate;
- дальнейшие learner/parent analytics и multimodal функции после их собственных acceptance gates.

Ни один из этих продуктов не получает отдельную ontology, отдельную базу знаний или отдельную модель mastery. Все они являются разными интерфейсами одного полного предмета и одного PEIS learner state.

### Progressive opening

Разделы разрешено открывать ученику поэтапно, когда конкретный раздел прошёл свои subject/runtime/product gates. Поэтапное открытие не разрешает ложный claim полноты: UI и коммерческое описание должны точно соответствовать реально доступному покрытию.

Рабочая последовательность открытия:

1. **R0 — private production assembly:** Yandex backend/persistence, account/session, accepted Russian content, protected client, payment candidate, Tutor integration; public paid traffic OFF.
2. **R1 — first paid closed loop:** diagnosis/attempt -> error -> practice/help -> independent verify -> persisted learner state -> next action; account, entitlement, trainer, work on mistakes, personal route and both Tutor interfaces are real.
3. **R2 — EGE Russian surface:** complete admitted EGE route + exam-task trainer + thematic trainer + trainer constructor + course/personal route + Tutor/retention.
4. **R3 — OGE Russian surface:** complete admitted OGE route over the same school identities/PEIS state.
5. **R4 — school Russian 5–11 surfaces:** grade/program navigation, topic study, thematic practice and prerequisite repair over the full school program.
6. **R5 — advanced services:** essay/extended answers, richer forecast/analytics, parent/reporting surfaces and later multimodal capabilities after their own gates.

Full-subject truth and the visual rollout of specialized sections are different concepts. Once the full program is accepted, specialized learner surfaces should be released progressively without rebuilding the subject.

## 25. Russian launch AI/speech policy — owner decision 2026-08-31

For learners in Russia, conversational brain routing is internal and not a learner-facing choice.

Launch policy:

- **Yandex conversational brain is the default brain for Russian learners**;
- OpenAI is fallback/escalation only after applicable production admission;
- the learner sees one product identity: `Tutor Eksamio`;
- provider/model choice remains server-side, logged/versioned and replaceable;
- provider-specific representation may not enter canonical subject truth or PEIS learner state.

The Russian voice casting decision is closed unless a new production defect appears:

- Yandex SpeechKit voice: **Lera**;
- accepted profile: `neutral / speed 1.04 / pitch 0 Hz / marked pauses`;
- further subjective Lera casting is not launch-critical work;
- learner audio persistence remains exactly `0`.

This section supersedes older candidate-only wording for the **Russian launch routing default**. It does not make Yandex proprietary representations part of the core architecture.

## 26. Repository-host independence — hard production invariant 2026-08-31

GitHub is currently the development/version-control source of truth, but **Eksamio must not depend on GitHub for normal production operation or for its long-term architecture**.

Hard invariant:

> **GitHub outage != Eksamio outage.**

After a release is deployed, GitHub may become completely unavailable and normal learner operation must continue from the production contour.

Therefore production must not fetch GitHub in the learner hot path for:

- application startup/runtime;
- Russian knowledge required by already admitted learner features;
- PEIS state;
- account/session state;
- entitlements;
- Tutor runtime configuration required for an already deployed release;
- production assets required for normal service.

Release artifacts/images and production configuration needed to run the admitted version must exist in the production environment independently of GitHub. Secrets and learner data are never stored in GitHub.

Repository hosting is replaceable. Future migration from GitHub to SourceCraft or another Git host may be evaluated after launch, but it is **not** part of the current launch critical path. Such a migration must not require redesign of PEIS, subject truth, business logic, learner data or product interfaces.

Primary Russian production cloud remains Yandex Cloud Russia, while code/business contracts remain portable/provider-neutral.

## 27. Progressive Public Release — hard release invariant 2026-08-31

Owner decision: `OWNER-DECISION-PROGRESSIVE-PUBLIC-RELEASE-2026-08-31.md`.

Eksamio не ждёт полного завершения всей платформы, чтобы показать ученикам уже готовую и безопасную ценность.

Любая learner-facing функция, раздел, предметный срез, тренажёр, диагностика, маршрут или иной продуктовый этап, который прошёл собственные обязательные subject/runtime/product acceptance gates, не создаёт ложного claim полноты и production-ready для заявленного публичного scope, **должен быть опубликован на живом сайте Eksamio без ожидания полного Pro launch или закрытия несвязанных launch blockers**.

Для уже опубликованной бесплатной и безопасной ценности разрешено и требуется начинать привлечение реальных пользователей и измерение поведения/learning outcomes. Незавершённые платные/Pro/payment/identity/Tutor функции не обещаются как доступные и остаются за своими production gates.

Каждый закрытый learner-facing этап обязан иметь один publication status:

- `LIVE` — реально доступен ученику на production-сайте;
- `READY_TO_PUBLISH` — acceptance пройден, требуется только фактическая публикация;
- `BLOCKED:<reason>` — существует конкретный blocker, мешающий безопасной публикации.

`DONE` без `LIVE` либо явного `BLOCKED:<reason>` не считается операционно завершённым. Удержание готового learner-facing этапа «под капотом» без конкретного blocker запрещено.

Этот инвариант отменяет blanket-подход «ничего нового не показывать ученикам до полного запуска всей системы» для уже готового, правдивого и безопасного публичного scope. Он не отменяет отдельные production gates для платного Pro, оплаты, identity, entitlements, receipt/refund/revoke, privacy и Tutor.