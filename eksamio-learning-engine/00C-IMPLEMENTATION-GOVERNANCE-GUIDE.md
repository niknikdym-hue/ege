# Eksamio — Implementation Governance Guide

**Статус:** EXECUTION / GOVERNANCE AUTHORITY  
**Версия:** 1.2  
**Дата:** 2026-08-23  
**Корень:** `eksamio-learning-engine/`

## 1. Назначение

Этот документ определяет, **как именно вести реализацию Eksamio**, чтобы проект не распадался на несвязанные задачи, предметные ветки и локальные решения.

Он не заменяет продуктовую authority.

Главная продуктовая authority:
- `00-PRODUCT-MASTERPLAN.md`;
- явно утверждённые owner decisions, включая `OWNER-DECISIONS-2026-08-22.md`.

Текущий порядок исполнения:
- `00B-PROJECT-PRIORITIES-CURRENT.md`.

Этот файл задаёт execution discipline: порядок чтения, систему gates, правила постановки задач, архитектурные проверки, требования к результатам и периодическую фиксацию состояния проекта.

## 2. Основной принцип реализации

Eksamio строится **строго по dependency graph**, а не по принципу «что проще сделать сейчас».

Каждая новая работа должна отвечать:

1. Какой утверждённый milestone или blocker она приближает/закрывает?
2. Какой конкретный gap она закрывает?
3. Какой следующий dependency она разблокирует?
4. Как она входит в общий PEIS closed loop или обязательный production/launch gate?
5. Почему выбран именно минимальный способ решения, а не более широкий проект?

Если работа не приближает утверждённый milestone, не закрывает gap и не разблокирует dependency, она не должна становиться приоритетной только потому, что технически удобна или визуально эффектна.

### Обязательный task-admission contract

Перед выдачей любой значимой implementation/audit задачи Central Brain должен уметь записать:

- `WHY_NOW` — почему задача нужна сейчас;
- `ACTIVE_BLOCKER_OR_MILESTONE` — точный blocker/milestone;
- `BASELINE_MAIN_SHA` — актуальный durable baseline;
- `DEPENDENCY_IN` — что уже должно быть истинно;
- `MINIMAL_DELTA` — минимальный требуемый change/evidence;
- `EXPECTED_UNLOCK` — что станет возможно после PASS;
- `EXECUTOR` — Brain / Codex / Spark / deterministic tool и почему это самый дешёвый достаточный вариант;
- `ALLOWED_PATHS` / `FORBIDDEN_PATHS` для write-задач;
- `ACCEPTANCE_EVIDENCE` — измеримый proof;
- `STOP_CONDITIONS`;
- допустимые `FINAL_STATUS`.

Если `WHY_NOW` или `EXPECTED_UNLOCK` невозможно сформулировать конкретно, задача не допускается к исполнению.

## 3. Неподвижный системный milestone

Первый обязательный системный milestone:

`demo -> diagnosis -> EvidenceEvent -> StudentSkillState -> Mastery/Readiness -> Next Best Action -> trainer/help -> independent verify -> measured outcome`

До его доказанной реализации не допускается смещение фокуса на декоративный AI, voice-first обход PEIS, отдельный чат-бот, параллельные learner engines или несвязанные personalization-механики.

При этом `OWNER-DECISIONS-2026-08-22.md` устанавливает отдельный P0 launch gate: первый paid Pro запрещён, пока text и realtime voice интерфейсы одного Tutor не прошли production gates. Это меняет старый delivery order, но не отменяет dependency-first построение closed loop.

## 4. Authority hierarchy

При конфликте решений использовать следующий порядок:

1. `00-PRODUCT-MASTERPLAN.md` и явно утверждённые owner decisions.
2. `00B-PROJECT-PRIORITIES-CURRENT.md` — текущая очередь реализации и приоритеты.
3. Общие PEIS contracts и их validation/result artifacts.
4. Subject-level identity/source/program authorities.
5. Task contracts / implementation specs.
6. Validation / result artifacts конкретной задачи.
7. Код и данные production/runtime.
8. Текст отдельных чатов, сообщения Codex и временные заметки.

Чат сам по себе не является долговременной authority.

## 5. Обязательный execution gate для любой новой задачи

### GATE A — Product fit
- соответствует ли работа PEIS Masterplan;
- не превращает ли Eksamio в набор независимых страниц или generic AI chat;
- направлена ли она на доказанное изменение learner knowledge state или обязательный production/launch dependency.

### GATE B — Dependency fit
- понятна ли предшествующая dependency;
- не выполняется ли работа раньше обязательного нижележащего слоя;
- не существует ли уже аналогичный contract / engine / registry;
- указан ли конкретный `EXPECTED_UNLOCK`.

### GATE C — Shared-core fit
- не создаёт ли работа отдельный Student Model, learner state, Evidence, Mastery, Readiness, Retention или NBA для одного предмета;
- переиспользует ли общий PEIS foundation.

### GATE D — Source truth
- есть ли документально проверяемый источник;
- сохранена ли provenance;
- не заменяется ли official/source truth догадкой AI или реконструкцией «по смыслу».

### GATE E — Scope safety
- отделена ли architecture/spec работа от production integration;
- не меняются ли frozen runtime/Tilda/scoring/localStorage/production побочно;
- определён ли rollback или HOLD там, где интеграция ещё не разрешена;
- не расширяется ли задача за пределы минимальной delta.

### GATE F — Completion evidence
- есть ли валидатор, тест, аудит или result artifact;
- можно ли доказать, что заявленный результат действительно достигнут;
- ясно ли, что осталось незавершённым.

### GATE G — Efficiency / existing-path reuse
- проверен ли уже существующий рабочий путь;
- можно ли решить задачу меньшим числом изменений/шагов;
- не создаётся ли новый CI, staging layer, framework, service или документ без доказанной необходимости;
- не используется ли дорогой AI/agent там, где достаточно deterministic tool или маленькой bounded модели.

### GATE H — Scope expansion stop

Если во время исполнения выясняется, что задача требует существенно большего объёма, новой архитектуры, новых global dependencies или изменения frozen authority, исполнитель обязан STOP и вернуть конкретный blocker Central Brain.

Нельзя самостоятельно превращать небольшую delivery/fix задачу в новый infrastructure/project workstream.

Задача, которая не проходит эти gates, должна быть переработана до исполнения.

## 6. Правило spec != implementation

В проекте всегда явно различать:

- архитектурное решение;
- contract/schema/spec;
- reference implementation;
- production implementation;
- integration;
- validation;
- live publication.

Наличие документа или JSON-contract не означает, что функциональность существует в runtime.

Наличие готового локального runtime не означает, что он прошёл production integration gate.

Нельзя в статусах смешивать эти состояния.

## 7. Task lifecycle

Каждая значимая задача проходит жизненный цикл:

`DECISION -> TASK CONTRACT -> BRANCH/WORKTREE -> IMPLEMENTATION/AUDIT -> VALIDATION -> RESULT/EVIDENCE -> ARCHITECTURAL REVIEW -> PR -> MERGE -> STATUS UPDATE`

Для маленьких add-only governance/source задач допустим сокращённый цикл, но результат всё равно должен быть восстановим из GitHub.

Не создавать отдельный task/result/review artifact, если branch/PR + tests уже являются достаточным durable evidence.

## 8. Branch / PR discipline

- Работа начинается от актуального `main`.
- Одна логическая задача — одна изолированная ветка/PR, если нет явной причины объединить изменения.
- Параллельные предметы не должны менять общий PEIS foundation независимо друг от друга.
- Перед merge проверяется конфликт с current authority и уже merged contracts.
- Production/runtime changes требуют отдельного integration review.
- Add-only architecture не выдаётся за production delivery.
- После merge новый `main` становится единственной durable baseline для следующей работы.

## 9. Предметная дисциплина

### P0
- Русский язык.
- Математика.

### P1
- Физика.

Физика может развиваться параллельно только при отсутствии замедления P0/central blocker.

Каждый subject-layer может иметь собственные:
- verified sources;
- Identity Model;
- semantic identities;
- prerequisites;
- exam routes;
- content/program mappings;
- demo/trainer mappings;
- deterministic subject tools.

Но не собственный PEIS learner engine.

## 10. Решение о следующей работе

Следующая работа выбирается не по количеству незакрытых файлов, а по bottleneck проекта.

**Текущий central bottleneck:** `PEIS-DEPLOYMENT-SECURITY-001`.

Пока он открыт, central/platform tasks должны либо закрывать конкретную часть этого gate, либо прямо готовить следующий обязательный dependency после него.

Параллельно допускаются только bounded subject lanes с собственным доказуемым endpoint, если они не замедляют central P0 work.

После production/deployment foundation следующий порядок определяется current authority и фактическим delta, но paid Pro остаётся запрещён до совместной production readiness text + realtime voice Tutor и применимых identity/payment/legal/security gates.

## 11. Периодическое подведение итогов

После каждого существенного рабочего периода фиксируется durable checkpoint.

Базовый ритм:
- не реже одного раза за рабочий день, если в этот день велась значимая работа;
- дополнительно после крупного merge, смены blocker/milestone или важного owner/architecture decision.

Checkpoint должен содержать:

1. дату;
2. фактический `main` baseline / важные merge commits;
3. что завершено;
4. что только спроектировано, но не реализовано;
5. какие PR открыты и их архитектурный статус;
6. какие решения приняты;
7. какие gaps/blockers остаются;
8. какой следующий gate;
9. что запрещено делать до закрытия этого gate;
10. какие документы являются authority для продолжения.

Ежедневный checkpoint хранится в `eksamio-learning-engine/worklog/`.

Не создавать checkpoint, если существенной работы/изменения состояния не было.

## 12. Правило нового чата

Новый ChatGPT/Codex/другой AI-сеанс не должен пытаться продолжить проект только по памяти пользователя или по пересказу прошлого чата.

Он обязан восстановить рабочую точку из репозитория согласно `00D-BRAIN-CONTINUITY-PROTOCOL.md`.

## 13. Что считается качественным прогрессом

Качественный прогресс — это не число созданных файлов, PR или строк кода.

Качественный прогресс означает, что:
- уменьшилось число архитектурных неизвестных;
- закрыт реальный source/identity/runtime/production gap;
- разблокирован следующий dependency;
- получен проверяемый learner signal;
- заработала часть closed loop;
- появилась измеримая связь intervention -> outcome;
- система стала ближе к production-ready subject-neutral PEIS.

## 14. Запрещённые паттерны управления

Не допускаются:
- повторное проектирование уже принятых решений без нового evidence;
- создание параллельных архитектур «на всякий случай»;
- придумывание CI/staging/deployment layer, которого не требует реальный процесс;
- превращение маленькой delivery-задачи в инфраструктурный проект;
- повторный широкий audit из-за ограничения одного web/tool surface;
- subject-specific копии PEIS engines;
- AI-first вместо source/evidence/verification-first;
- merge старого PR только потому, что он mergeable;
- трактовка чата как единственного хранилища решений;
- неконтролируемое накопление открытых PR без статуса;
- выдача спецификации за работающий продукт;
- смена milestone без обновления durable authority;
- перекладывание на owner ручной технической работы, которую исполнитель может безопасно сделать сам после минимального authentication step.

## 15. Текущая точка проекта — 2026-08-23

Durable main перед этим обновлением:

`85b1f4316cf33dc6ab0eebce2e9281b6432e4bbb`

Состояние:

- owner decisions 2026-08-22 merged и являются authority;
- Physics 2025 v1.5 result-order fix merged через PR #96;
- Physics 2024 official source-access pack merged через PR #97; subject source-lock/build-spec lane активен;
- Russian PR #72 остаётся активным read-only/decision lane, PR #57 HOLD, PR #23 reviewed content checkpoint;
- central reference PEIS chain дошла до trusted-host identity boundary;
- главный central production blocker — `PEIS-DEPLOYMENT-SECURITY-001`.

Следующая central работа выбирается только из concrete gaps этого blocker. Physics/Russian идут параллельно bounded lanes и не должны оттягивать central execution.

Все последующие решения проверяются против current `main`, owner authority, measurable learning outcome и `EXPECTED_UNLOCK` каждой задачи.
