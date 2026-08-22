# Eksamio Learning Engine — Product Benchmark 2026

**Дата:** 2026-08-18  
**Назначение:** зафиксировать мировой baseline, который Эксамио должен не копировать, а превосходить измеримыми продуктово-учебными характеристиками.

## 1. Текущее публичное состояние Эксамио

Публичная главная `https://eksamio.ru/` на дату фиксации уже предлагает три полезных входа:

- интерактивные демоверсии ЕГЭ;
- тренажёры;
- учебные материалы/разборы.

Русский язык включает ЕГЭ-тренажёр и тематические тренажёры: ударения, словарные слова, паронимы, фразеологизмы.

Это хороший content/product inventory, но публично он пока выглядит как выбор отдельных форматов. Целевая новая система должна превратить эти форматы в один непрерывный персональный маршрут.

## 2. Мировой baseline: что уже существует

### Google Gemini Study Notebooks — 2026

Official source:
`https://blog.google/products-and-platforms/products/education/iste-students-2026/`

Зафиксированный baseline:

- пользователь задаёт learning goal / загружает материалы;
- проходит diagnostic quiz;
- система определяет зоны фокуса;
- строит bite-sized interactive lessons;
- последующие quiz results автоматически меняют lessons/plan;
- есть progress dashboard;
- experience grounded in learner/class materials.

Вывод: `diagnosis -> adaptive plan -> lessons -> quiz -> plan update` уже не является уникальной инновацией.

### Khan Academy / Khanmigo — 2026

Official source:
`https://blog.khanacademy.org/how-khan-academy-is-building-a-better-ai-tutor-our-most-recent-learnings/`

Ключевой baseline:

- Khan Academy измеряет `next-item correctness`: решил ли ученик следующий item по тому же skill самостоятельно после tutoring;
- structured recent learning history дала +3.4% next-item correctness в опубликованном эксперименте;
- информация о неосвоенных prerequisite skills дала +2.7%;
- Khan Academy сообщает суммарное улучшение 6.1% next-item correctness для проверенных structured-signal изменений;
- product development строится через A/B/product experiments, а не через субъективную оценку «ответ AI выглядит хорошо».

Вывод: structured learner history + prerequisite awareness + next-item correctness являются обязательным baseline для серьёзного AI tutor.

### OpenAI Study Mode / learning outcomes — 2026

Official source:
`https://openai.com/index/understanding-ai-and-learning-outcomes/`

Ключевой baseline:

- pedagogically aligned AI uses scaffolding, checks for understanding and guided practice rather than direct answer delivery;
- OpenAI описывает randomized study с более чем 300 college students;
- для microeconomics в опубликованных предварительных результатах участники с Study Mode показали примерно 15% более высокий exam score относительно no-AI control;
- OpenAI отдельно подчёркивает, что финальный exam score недостаточен и важны longitudinal effects и durable learning.

Вывод: guided dialogue сам по себе уже baseline; дифференциация требует долгосрочной измеряемой learner model.

### Google Learn Your Way — 2025/2026 benchmark

Official source:
`https://blog.google/products-and-platforms/products/education/learn-your-way/`

Baseline:

- source-grounded transformation of textbook content;
- адаптация к уровню и интересам ученика;
- multiple representations: interactive guides, mind maps, audio lessons, quizzes;
- Google сообщал +11 percentage points на long-term recall test относительно standard digital reader в своём efficacy study.

Вывод: multimodal content generation и adaptive presentation уже не являются достаточным moat.

## 3. Что Эксамио НЕ должен считать конкурентным преимуществом само по себе

Следующее необходимо, но уже не уникально:

- AI-чат;
- «объясни ответ»;
- Socratic prompting;
- diagnostic quiz;
- adaptive study plan;
- personalized lesson;
- quiz after lesson;
- progress dashboard;
- grounded retrieval from course material;
- voice conversation;
- automatic flashcards;
- simple spaced repetition;
- generic weakness map.

Если Эксамио остановится на этом уровне, он будет догонять существующий мировой рынок.

## 4. Целевая дифференциация Эксамио

### 4.1. Exam-native Student Learning Twin

Не generic learner profile, а longitudinal model, привязанный к:

- официальной структуре экзамена;
- canonical semantic skill identities;
- exam-route value;
- prerequisite graph;
- history of independent evidence;
- transfer and retention.

### 4.2. Score Gain per Minute

Recommendation Engine должен оптимизировать ожидаемый экзаменационный прирост на единицу времени:

`expected_exam_gain / expected_study_time`

Целевая пользовательская ценность:

> «Что мне сделать сейчас за 15 минут, чтобы с максимальной вероятностью вернуть баллы?»

### 4.3. Error Fingerprint

Не просто `wrong`, а evidence-based hypothesis:

- knowledge gap;
- prerequisite gap;
- confusion;
- application error;
- reading/formulation error;
- retention failure;
- unstable skill;
- accidental error candidate;
- confident misconception.

### 4.4. Intervention Effectiveness

Система должна знать не только состояние skill, но и **что реально помогает именно этому ученику**.

После объяснения/подсказки измерять:

- next-item correctness;
- NIC-3;
- transfer;
- retention.

### 4.5. Calibrated Exam Forecast

Не «AI думает, что будет 84», а диапазон + uncertainty + последующая проверка calibration на реальных контрольных попытках.

### 4.6. Deterministic truth + AI reasoning

Official exam facts/scoring и canonical knowledge structure отделены от generative inference архитектурно. AI не может молча переписать источник истины.

### 4.7. Closed-loop AI

Каждая AI-помощь должна по возможности завершаться независимой проверкой learning outcome. Цель AI — изменить результат следующего действия ученика, а не создать красивый ответ.

## 5. Измеримый стандарт «выше мировых»

Не использовать формулировку «лучше/выше мировых» как публичный факт без данных.

Внутренне считать направление успешным только если Эксамио показывает сильные результаты по набору метрик:

- exam/source fidelity;
- next-item correctness uplift;
- retention uplift;
- transfer uplift;
- repeat-error reduction;
- score gain per study minute;
- calibrated score forecast;
- cost per successful learning intervention;
- AI factual/error rate;
- measurable exam/control score improvement.

## 6. Практическое следствие для roadmap

Первый bounded AI implementation slice не должен быть generic chat и не должен быть voice-first обходом verified evidence/PEIS foundations.

Правильный первый vertical slice:

`verified attempt -> exact skill evidence -> grounded personalized explanation -> independent verification item -> measured outcome`

Owner decision `OWNER-DECISIONS-2026-08-22.md` уточняет launch order: realtime voice является P0 gate первого paid Pro вместе с text Tutor. Ранний grounded AI slice может предшествовать полному Pro contour, но paid text-only или voice-only Pro launch запрещён. Long-term Student Learning Twin, Recommendation Engine и essay/vision развиваются по dependency/evidence order, не превращая voice в отдельный Tutor.

## 7. Связь с главным masterplan

Главный product/architecture authority:

`00-PRODUCT-MASTERPLAN.md`

Этот benchmark не меняет source authority и не определяет official exam facts. Он фиксирует внешний продуктовый baseline и критерии, по которым новая система должна оценивать собственную конкурентоспособность.
