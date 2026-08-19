# Eksamio — Current Project Priorities

**Статус:** CURRENT PRODUCT PRIORITY SNAPSHOT  
**Дата:** 2026-08-19  
**Горизонт:** до 2026-09-01 и далее до первого работающего PEIS vertical slice

Этот файл не заменяет `00-PRODUCT-MASTERPLAN.md`. Он фиксирует текущую очередь исполнения и существует, чтобы новые чаты, Codex-задачи и параллельные предметные ветки не переизобретали приоритеты.

## 1. Предметный приоритет

### P0 — два главных предмета

1. **Русский язык** — первый предмет Eksamio.
2. **Математика** — второй предмет Eksamio.

Русский и математика имеют одинаковый высший ресурсный приоритет. Если возникает конкуренция за время, архитектурное внимание или delivery capacity, они не должны замедляться ради третьего предмета.

В математике:

- профильная математика — ключевой интеллектуальный маршрут;
- базовая математика — отдельный официальный exam route той же предметной системы;
- уже существующие math source/audit/build-контуры сначала инвентаризируются и переиспользуются, а не перестраиваются ради унификации каталогов.

### P1 — третий предмет

3. **Физика** — третий предмет Eksamio.

Физика развивается параллельно, но не в ущерб русскому и математике.

## 2. Общий архитектурный инвариант

Все предметы подключаются к одной Eksamio Personal Exam Intelligence System.

Нельзя создавать предметные копии:

- Student Model;
- universal learner evidence;
- mastery;
- readiness;
- retention;
- Next Best Action / Recommendation Engine.

У предмета собственные source authority, identity model, prerequisites, exam routes и content mappings.

## 3. Текущий общий фундамент

Уже materialized / accepted как общий PEIS foundation:

- TASK-003 — Russian semantic inventory / crosswalk foundation;
- TASK-004 — generalized learner evidence and materialized state contracts;
- TASK-005 — mastery / prerequisite-readiness / retention / Next Best Action contracts;
- PR #37 — subject source contours 2022–2026 для соответствующих предметов без перестройки математики.

Новые предметные работы обязаны переиспользовать этот фундамент.

## 4. Текущая очередь русского

1. Не повторять общий coverage audit 185 × 174 как новый проект.
2. Свести 185 canonical identities, Skill Graph, FIPI exam routes, demo items, 174 trainer items, thematic trainers и full-program content в Unified Russian Identity Model.
3. Source-backed разобрать unresolved semantic candidates через admit / merge / split / reject.
4. Материализовать teach/practice/check content там, где identity model уже устойчива.
5. Использовать русский как первый verified vertical slice PEIS.

## 5. Текущая очередь математики

1. Провести non-destructive inventory всего, что уже существует в `main` по профильной и базовой математике.
2. Зафиксировать фактический source matrix 2022–2026 для обоих маршрутов.
3. Не переделывать уже проверенные source/prelock/build/audit контуры без причины.
4. Закрыть только реальные gaps.
5. Построить единую Mathematics Identity Model с route overlays `profile` и `base`.
6. Затем подключить math evidence к тем же общим PEIS contracts.

## 6. Текущая очередь физики

1. Проверенный официальный source-корпус 2022–2026.
2. Physics Identity Model.
3. Source-backed prerequisite relationships.
4. Mapping существующей физической демоверсии.
5. Coverage/diagnostic audit.
6. Подключение к общему PEIS.

## 7. Главный системный milestone

Первый работающий end-to-end контур:

`demo -> diagnosis -> EvidenceEvent -> StudentSkillState -> Mastery/Readiness -> Next Best Action -> trainer/help -> independent verify -> measured outcome`

До этого момента не распыляться на декоративный AI.

## 8. После vertical slice

Последовательно:

1. NIC-1 / NIC-3 / transfer / retention / recommendation-result telemetry;
2. grounded AI Review конкретной ошибки + independent verification;
3. usage/cost/eval telemetry;
4. account/server sync;
5. «Тренировка на сегодня»;
6. text AI Tutor;
7. Student Learning Twin / Recommendation Engine expansion;
8. essay/extended-answer evaluation;
9. calibrated score forecast;
10. vision;
11. realtime voice.

## 9. Delivery discipline до 1 сентября

- не оставлять архитектурно готовые безопасные PR без причины;
- каждую ветку начинать от актуального `main`;
- перед merge проверять конфликт с общими PEIS contracts и current authority;
- прямые изменения `main` в source/authority/identity/PEIS/runtime считать audit trigger;
- production не менять побочно;
- не создавать повторные аудиты уже закрытых вопросов;
- приоритет delivery: русский + математика, затем физика;
- параллельная работа допустима только при разделённых ветках/предметных контурах;
- после существенного рабочего периода фиксировать durable checkpoint в `worklog/`; базовый ритм — не реже одного раза за рабочий день, если велась значимая работа.

## 10. Если новый чат не понимает, что делать

Читать в таком порядке:

1. `00-PRODUCT-MASTERPLAN.md`;
2. этот файл — `00B-PROJECT-PRIORITIES-CURRENT.md`;
3. `00C-IMPLEMENTATION-GOVERNANCE-GUIDE.md`;
4. `00D-BRAIN-CONTINUITY-PROTOCOL.md`;
5. последний checkpoint в `worklog/`;
6. `00-WORK-STATUS.txt` и current addendum как исторический контекст;
7. `AGENTS.md`;
8. current subject authority;
9. exact task / branch / PR context.

Ни один локальный task не может молча изменить зафиксированные product priorities.
