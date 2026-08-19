# Eksamio — Brain Continuity Protocol

**Статус:** CONTINUITY / HANDOFF AUTHORITY  
**Версия:** 1.0  
**Дата:** 2026-08-19  
**Назначение:** восстановление архитектурного контекста Eksamio в новом чате, у нового AI-сеанса или после длительного перерыва.

## 1. Принцип

«Мозг проекта» не должен существовать только внутри одного чата.

Durable memory Eksamio хранится в GitHub через:
- product/architecture authority;
- current priorities;
- contracts;
- source/identity authorities;
- validation/result artifacts;
- merged code/data;
- worklog checkpoints.

Чат — это рабочий интерфейс, а не source of truth.

## 2. Обязательный старт нового Brain-сеанса

Новый Brain-сеанс обязан начинать не с проектирования, а с восстановления фактического состояния.

### Шаг 1 — определить актуальный baseline

Проверить:
- repository: `niknikdym-hue/ege`;
- branch: `main`;
- текущий HEAD `main`;
- последние значимые merges;
- открытые PR, если они влияют на текущую работу.

Не продолжать работу от старой remembered SHA, если `main` изменился.

### Шаг 2 — прочитать durable authority в порядке

Обязательный minimum:

1. `00-PRODUCT-MASTERPLAN.md`
2. `00B-PROJECT-PRIORITIES-CURRENT.md`
3. `00C-IMPLEMENTATION-GOVERNANCE-GUIDE.md`
4. последний файл в `worklog/`
5. relevant shared PEIS contracts/results
6. relevant subject authority/source/identity files
7. relevant open PRs / task result artifacts

`00-WORK-STATUS.txt` и `00A-WORK-STATUS-CURRENT-ADDENDUM.txt` являются исторически важными checkpoints, но новые decisions сверяются с более новой authority выше.

### Шаг 3 — восстановить текущий dependency state

Новый Brain должен явно установить:
- что уже merged/materialized;
- что является только spec/contract;
- что является executable reference implementation;
- что production-integrated;
- какие gaps ещё открыты;
- какой milestone сейчас активен;
- какой gate должен быть закрыт следующим.

### Шаг 4 — проверить предметный приоритет

На текущем этапе:
- Russian = P0;
- Mathematics = P0;
- Physics = P1.

Нельзя переключать ресурсы с P0 на P1 без явного нового product decision.

### Шаг 5 — проверить shared-core invariant

Перед любым новым проектированием убедиться, что не предлагается отдельный предметный:
- Student Model;
- learner state;
- universal Evidence;
- Mastery;
- Readiness;
- Retention;
- Recommendation/NBA.

Если такой duplicate предлагается, решение считается архитектурно ошибочным до отдельного пересмотра Masterplan.

## 3. Краткий handoff snapshot, который Brain должен уметь восстановить

Новый Brain после чтения документов должен суметь ответить на 10 вопросов:

1. Что такое Eksamio как продукт?
2. Какой главный измеримый пользовательский outcome?
3. Какой текущий главный milestone?
4. Какие subjects P0/P1?
5. Какие shared PEIS foundations уже существуют?
6. Какие из них contracts, а какие реально исполняются?
7. Какие subject-level gaps сейчас критичны?
8. Что запрещено делать преждевременно?
9. Какой следующий gate?
10. Какие PR/branches требуют решения?

Если на один из этих вопросов нет документально подтверждённого ответа, сначала проводится repository audit, а не делается предположение.

## 4. Правило архитектурного решения

Если в новом чате принимается значимое решение, которое меняет:
- product direction;
- dependency order;
- subject priority;
- shared PEIS architecture;
- identity/source authority;
- runtime boundary;
- AI/provider boundary;
- commerce/account boundary;
- production gate;

оно должно быть отражено в durable repository artifact до того, как станет рабочей нормой проекта.

Одного сообщения в чате недостаточно.

## 5. Правило ежедневного/сессионного checkpoint

После значимого рабочего периода Brain должен обновить durable worklog.

Минимальный шаблон:

```text
DATE:
MAIN BASELINE:
ACTIVE MILESTONE:

COMPLETED:
- ...

MERGED:
- ...

OPEN / REVIEW:
- ...

DECISIONS:
- ...

SPEC ONLY / NOT IMPLEMENTED:
- ...

BLOCKERS / GAPS:
- ...

NEXT GATE:
- ...

DO NOT DO YET:
- ...

AUTHORITY TO READ NEXT TIME:
- ...
```

Не требуется искусственно создавать запись в день, когда существенной работы не было.

## 6. Правило проверки старых PR

Новый Brain не должен считать старый открытый PR корректным только потому, что он mergeable.

Перед merge проверяются:
- base относительно текущего `main`;
- conflict с новой product authority;
- conflict с shared PEIS contracts;
- namespace/path discipline;
- source/provenance;
- validation status;
- production side effects.

Старый PR может быть:
- accepted after sync/revalidation;
- partially salvaged;
- superseded;
- closed without merge.

## 7. Правило памяти пользователя

Пересказ пользователя и память ChatGPT полезны как навигация, но не заменяют repository verification, если вопрос касается фактического состояния кода, PR, contracts, source corpus или current authority.

При расхождении между remembered context и актуальным `main` побеждает проверенный `main`, если только пользователь явно не принимает новое решение изменить authority.

## 8. Правило Codex handoff

Codex получает ограниченный task contract, но не становится владельцем архитектуры проекта.

Codex должен получать через task contract:
- exact baseline;
- allowed paths;
- forbidden paths;
- relevant authority files;
- acceptance criteria;
- validation commands;
- required durable result artifact.

Результат Codex без committed branch/PR/result artifact не считается достаточным durable handoff.

## 9. Rule of evidence

Каждое утверждение «готово» должно иметь доказательство одного из типов:
- merged commit;
- validated result artifact;
- reproducible tests;
- accepted source audit;
- production smoke/manual acceptance там, где это необходимо.

Фразы в чате «мы это уже сделали» без такой опоры не считаются достаточным основанием для архитектурного dependency.

## 10. Current continuity checkpoint — 2026-08-19

На дату создания этого протокола durable direction таков:

- Eksamio = Personal Exam Intelligence System.
- Главная единица ценности = доказанное изменение learner knowledge state.
- Первый обязательный системный milestone = end-to-end closed loop от demo evidence до independent verification и measured outcome.
- Shared PEIS contracts TASK-004/TASK-005 существуют, но contracts не должны выдаваться за production runtime.
- Russian и Mathematics = P0.
- Physics = P1.
- Russian должен дать первый verified subject slice.
- Mathematics нуждается в одной Mathematics Identity Model для profile + base.
- shared executable PEIS runtime — центральный platform dependency.
- AI Review/Tutor подключается после structured learner state, verified knowledge и independent verification.
- voice/realtime — поздний слой.

Продолжение проекта должно исходить из актуального `main`, а не только из этого snapshot.
