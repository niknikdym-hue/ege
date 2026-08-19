# Eksamio — Implementation Governance Guide

**Статус:** EXECUTION / GOVERNANCE AUTHORITY  
**Версия:** 1.0  
**Дата:** 2026-08-19  
**Корень:** `eksamio-learning-engine/`

## 1. Назначение

Этот документ определяет, **как именно вести реализацию Eksamio**, чтобы проект не распадался на несвязанные задачи, предметные ветки и локальные решения.

Он не заменяет продуктовую authority.

Главная продуктовая authority:
- `00-PRODUCT-MASTERPLAN.md`.

Текущий порядок исполнения:
- `00B-PROJECT-PRIORITIES-CURRENT.md`.

Этот файл задаёт execution discipline: порядок чтения, систему gates, правила постановки задач, архитектурные проверки, требования к результатам и периодическую фиксацию состояния проекта.

## 2. Основной принцип реализации

Eksamio строится **строго по dependency graph**, а не по принципу «что проще сделать сейчас».

Каждая новая работа должна отвечать хотя бы одному из вопросов:

1. Какой утверждённый milestone она приближает?
2. Какой конкретный gap она закрывает?
3. Какой следующий dependency она разблокирует?
4. Как она входит в общий PEIS closed loop?

Если работа не приближает утверждённый milestone, не закрывает gap и не разблокирует dependency, она не должна становиться приоритетной только потому, что технически удобна или визуально эффектна.

## 3. Неподвижный системный milestone

Первый обязательный системный milestone:

`demo -> diagnosis -> EvidenceEvent -> StudentSkillState -> Mastery/Readiness -> Next Best Action -> trainer/help -> independent verify -> measured outcome`

До его доказанной реализации не допускается смещение фокуса на декоративный AI, voice-first продукт, отдельный чат-бот, параллельные learner engines или несвязанные personalization-механики.

## 4. Authority hierarchy

При конфликте решений использовать следующий порядок:

1. `00-PRODUCT-MASTERPLAN.md` — целевой продукт и архитектурные принципы.
2. `00B-PROJECT-PRIORITIES-CURRENT.md` — текущая очередь реализации и приоритеты.
3. Общие PEIS contracts и их validation/result artifacts.
4. Subject-level identity/source/program authorities.
5. Task contracts / implementation specs.
6. Validation / result artifacts конкретной задачи.
7. Код и данные production/runtime.
8. Текст отдельных чатов, сообщения Codex и временные заметки.

Чат сам по себе не является долговременной authority.

## 5. Обязательный execution gate для любой новой задачи

Перед постановкой или принятием задачи необходимо проверить:

### GATE A — Product fit
- соответствует ли работа PEIS Masterplan;
- не превращает ли Eksamio в набор независимых страниц или generic AI chat;
- направлена ли она на доказанное изменение learner knowledge state.

### GATE B — Dependency fit
- понятна ли предшествующая dependency;
- не выполняется ли работа раньше обязательного нижележащего слоя;
- не существует ли уже аналогичный contract / engine / registry.

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
- определён ли rollback или HOLD там, где интеграция ещё не разрешена.

### GATE F — Completion evidence
- есть ли валидатор, тест, аудит или result artifact;
- можно ли доказать, что заявленный результат действительно достигнут;
- ясно ли, что осталось незавершённым.

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

`DECISION -> TASK CONTRACT -> BRANCH/WORKTREE -> IMPLEMENTATION/AUDIT -> VALIDATION -> RESULT ARTIFACT -> ARCHITECTURAL REVIEW -> PR -> MERGE -> STATUS UPDATE`

Для маленьких add-only governance/source задач допустим сокращённый цикл, но результат всё равно должен быть восстановим из GitHub.

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

Физика может развиваться параллельно только при отсутствии замедления P0.

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

Приоритет выбора:

1. blocker первого PEIS vertical slice;
2. blocker P0 Russian/Mathematics identity/source readiness;
3. blocker shared executable PEIS runtime;
4. blocker measurable verification/telemetry;
5. только затем AI/Tutor/platform expansion;
6. voice/realtime — поздний слой.

## 11. Периодическое подведение итогов

Обязательное правило проекта: **после каждого существенного рабочего периода фиксируется durable checkpoint**.

Базовый ритм:
- не реже одного раза за рабочий день, если в этот день велась значимая работа;
- дополнительно — перед окончанием длинной архитектурной сессии;
- дополнительно — после крупного merge, смены milestone или важного архитектурного решения.

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

Ежедневный checkpoint хранится в:
- `eksamio-learning-engine/worklog/`.

## 12. Правило нового чата

Новый ChatGPT/Codex/другой AI-сеанс не должен пытаться продолжить проект только по памяти пользователя или по пересказу прошлого чата.

Он обязан восстановить рабочую точку из репозитория согласно:
- `00D-BRAIN-CONTINUITY-PROTOCOL.md`.

## 13. Что считается качественным прогрессом

Качественный прогресс — это не число созданных файлов, PR или строк кода.

Качественный прогресс означает, что:
- уменьшилось число архитектурных неизвестных;
- закрыт реальный source/identity/runtime gap;
- разблокирован следующий dependency;
- получен проверяемый learner signal;
- заработала часть closed loop;
- появилась измеримая связь intervention -> outcome;
- система стала ближе к subject-neutral PEIS.

## 14. Запрещённые паттерны управления

Не допускаются:
- повторное проектирование уже принятых решений без нового основания;
- создание параллельных архитектур «на всякий случай»;
- subject-specific копии PEIS engines;
- AI-first вместо source/evidence/verification-first;
- merge старого PR только потому, что он mergeable;
- трактовка чата как единственного хранилища решений;
- неконтролируемое накопление открытых PR без статуса;
- выдача спецификации за работающий продукт;
- смена milestone без обновления durable authority.

## 15. Определение текущей точки проекта

На 2026-08-19 текущая системная задача — довести Eksamio от богатого набора source/identity/contracts к **первому доказанному end-to-end PEIS closed loop**.

Ключевые параллельные линии:

1. Russian verified source-backed vertical slice.
2. Unified Mathematics Identity Model для profile + base.
3. Shared executable PEIS runtime поверх TASK-004/TASK-005.
4. Physics source/identity work только без замедления P0.

Все последующие решения должны проверяться против этой точки.
