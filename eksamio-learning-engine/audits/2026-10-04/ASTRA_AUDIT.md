# Независимый аудит Eksamio

Дата проверки: 4 октября 2026. Автор: Astra. Изменения продукта, веток, инфраструктуры и внешних сервисов не выполнялись.

## Решение

**GO_WITH_BLOCKERS для ограниченных исправлений, интеграции и закрытой приёмки владельцем. Публичный платный запуск сейчас: NO GO.**

Архитектура уже существует и не требует нового движка, новой панели или очередного уровня согласования. Но готового сквозного релиза в проверенных ветках пока нет. Главный разрыв состоит из трёх частей: существенные реализации разнесены по старым несведённым PR; в них есть воспроизводимые дефекты обучения, согласий и безопасного отключения; реальные инфраструктура, регистрационная доставка, оплата и voice приёмка не доказаны.

Проверенные исправления ниже относятся к уже существующим требованиям запуска. Это не новые продуктовые функции и не дополнительные архитектурные ворота.

## Проверенная база

- Основной продукт: [ege main 77cdb7ca](https://github.com/niknikdym-hue/ege/commit/77cdb7ca071320dc6de90272ded7d43a0b07ea6c), повторно подтверждён через GitHub во время аудита.
- Регистрация и серверный ученический цикл: [PR 186 ae169c82](https://github.com/niknikdym-hue/ege/pull/186).
- Инвентаризация действующих учебных поверхностей: [PR 187 c5592c21](https://github.com/niknikdym-hue/ege/pull/187).
- Четыре допуска точных учебных действий: [PR 189 05e54aa4](https://github.com/niknikdym-hue/ege/pull/189), основан на PR 186.
- Русская предметная приёмка: takeover a52bffbe, current v30. Старый PR 164 закрыт без merge. Его описание с v29 не является текущим состоянием.
- Tutor и голос: [PR 172 c964ce2b](https://github.com/niknikdym-hue/ege/pull/172) и его существующие зависимости; это источник нужных изменений, не готовый к целиковому merge релиз.
- Составной имитационный сценарий: [PR 163 fa70cf4b](https://github.com/niknikdym-hue/ege/pull/163).
- Управление разработкой: [PR 209 34003dc1](https://github.com/niknikdym-hue/ege/pull/209); отдельный [eksamio-brain e77cfff5](https://github.com/niknikdym-hue/eksamio-brain/commit/e77cfff50a9998fe3c05c6459952903108d86f49).

Охват: карта проекта и критический путь от учётной записи до повторного входа, PEIS, Tutor, независимой проверки, оплаты и отзыва доступа; предметная приёмка, CI, контроль затрат, приватность, staging и rollback. Это аудит рисков и исполнения ключевых сценариев, а не утверждение, что вручную просмотрена каждая строка всех файлов. Незавершённые локальные исправления DeepSeek и independent verification не использованы как база и не приняты аудитом.

## Что уже полезно и должно быть сохранено

Общий PEIS, канонические EvidenceEvent и разделение предметной истины от provider output реализованы. Production client не переключается молча на mock вне localhost. Не принятый полный русский закрыт. Учётная запись и entitlement в PR 186 читаются сервером; браузер не получает raw session token. Платёжный normal path проверяет подпись, сумму и заказ, а refund отзывает entitlement. Runtime package использует immutable image и Lockbox references. Эти основы следует соединять и точечно исправлять, а не переписывать.

Основания: [граница Tutor](https://github.com/niknikdym-hue/ege/blob/77cdb7ca071320dc6de90272ded7d43a0b07ea6c/eksamio-learning-engine/ai-tutor-reference/tutor_boundary.py#L132-L204), [защита Pro от production mock](https://github.com/niknikdym-hue/ege/blob/77cdb7ca071320dc6de90272ded7d43a0b07ea6c/eksamio-pro-client/app.js#L22-L49), [server entitlement](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/payments-reference/entitlement_read.py#L37-L67).

## Воспроизводимые дефекты

Приоритет P1 означает исправить до включения соответствующей реальной функции. P2 означает ограниченный дефект или риск интеграции, который не следует изображать уже случившейся production аварией. Доказательств действующей эксплуатации или утечки нет.

### F1 P1 Выключатель записи не закрывает Tutor

**База:** PR 186, унаследовано PR 189.

**Сценарий:** runtime.writes_enabled=false, зарегистрированный пользователь с активным entitlement вызывает /api/tutor/turn.

**Ожидание:** отказ до вызова модели и до любых Tutor или PEIS записей.

**Факт:** обработчик возвращает 200 и вызывает tutor.turn. В настоящем lifecycle этот метод вызывает provider, затем пишет help event и tutor_contexts. Офлайн probe обработчика на неизменённом SHA получил tutor_calls=1 при выключенных записях.

**Место:** [learner_tutor_web_runtime.py, маршрут Tutor](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/peis-production-substrate/learner_tutor_web_runtime.py#L151-L216), [вызов provider и сохранение](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/peis-production-substrate/tutor_lifecycle.py#L429-L474). У practice guard есть: [learner_web_runtime.py](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/peis-production-substrate/learner_web_runtime.py#L283-L291).

**Минимум:** тот же fail-closed guard на Tutor до provider и любых записей; явно определить независимый запрет provider execution, если продукт должен уметь отключать модель отдельно.

**Регрессия:** writes OFF, provider OFF, entitlement absent, provider exception; в каждом запрещённом случае provider calls=0 и таблицы evidence/context/turn/quota неизменны.

### F2 P1 Повтор подсказанной карточки принимается за независимую проверку

**База:** PR 186 и его потомки.

**Сценарий:** ошибка в ex-practice-alt-sochetat-001, Tutor показывает правильный ответ, ученик вводит этот ответ в ту же карточку.

**Ожидание:** повтор не доказывает независимый перенос навыка. Нужно новое допущенное задание либо честное отсутствие доступной независимой проверки.

**Факт:** pending context ищется по той же card_id, а event получает independent_verification=true. Существующий PostgreSQL тест специально считает правильный ответ той же FIRST_SLICE_CARD_ID успешной независимой проверкой. Новая lineage или event id не делает само задание новым.

**Место:** [tutor_lifecycle.py](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/peis-production-substrate/tutor_lifecycle.py#L114-L165), [тест](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/peis-production-substrate/validate_tutor_lifecycle_postgres.py#L282-L310).

**Минимум:** фиксировать раскрытые item/answer, выдавать другой принятый item по той же exact capability; пока его нет, verification unavailable без самостоятельного mastery credit. Не создавать новый semantic ID ради обхода. Также учитывать раскрытие правильного ответа обычным feedback без Tutor: [learner_views.py](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/peis-production-substrate/learner_views.py#L228-L247), [adapter всегда UNASSISTED](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/peis-service-bridge-reference/russian_exceptions_practice_adapter.py#L263-L296).

**Регрессия:** та же карточка после ответа/подсказки, свежая карточка, повтор сетевого запроса, неправильная проверка, возврат в новую сессию; ложных независимых допусков 0.

### F3 P1 Старая успешная retention проверка перекрывает новую ошибку

**База:** main, общий PEIS kernel.

**Сценарий:** корректная delayed-retention проверка; позже новая самостоятельная ошибка по тому же exact skill.

**Ожидание:** новая ошибка учитывается, текущий навык не представляется уверенно освоенным и снятым с приоритета.

**Факт:** на schema-valid fixtures одновременно получены mastery=STRONG, contradiction=PRESENT_VERIFICATION_RECOMMENDED и readiness=ALREADY_STRONG_NOT_CURRENT_PRIORITY. Причина: старый успешный retention проверяется раньше свежего противоречия; readiness также предпочитает STRONG.

**Место:** [infer_mastery 203–219](https://github.com/niknikdym-hue/ege/blob/77cdb7ca071320dc6de90272ded7d43a0b07ea6c/eksamio-learning-engine/peis-reference-kernel/peis_reference_kernel.py#L203-L219), [readiness 430–437](https://github.com/niknikdym-hue/ege/blob/77cdb7ca071320dc6de90272ded7d43a0b07ea6c/eksamio-learning-engine/peis-reference-kernel/peis_reference_kernel.py#L430-L437).

**Минимум:** согласовать приоритет свежего противоречивого evidence в существующих infer_mastery/infer_retention/readiness. Не менять весь алгоритм и не вводить неподтверждённые коэффициенты.

**Регрессия:** retained success → ordinary error → новая независимая проверка; retained success → assisted answer; более новая проваленная retention. Проверять совместимость всех трёх проекций, не только valid JSON.

### F4 P1 Runtime Tutor не поддерживает уточняющий диалог

**База:** PR 186.

**Сценарий:** после первого объяснения ученик задаёт другой вопрос, например просит объяснить ещё раз или привести другой пример.

**Ожидание:** новый ответ в том же учебном эпизоде; повтор именно того же сетевого запроса должен быть idempotent.

**Факт:** любой непустой message при pending verification возвращает прежний tutor_text без обращения к provider. Офлайн проверка двух разных вопросов дала идентичный ответ. В turn contract нет client turn id; pending-help lineage используется вместо идентичности запроса. Provider boundary здесь принимает message/explanation, но не историю диалога; это ещё не подключение существующего ReliabilityGateway к реальному durable Tutor.

**Место:** [tutor_lifecycle.py 398–435](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/peis-production-substrate/tutor_lifecycle.py#L398-L435), [provider protocol](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/peis-production-substrate/tutor_lifecycle.py#L48-L64).

**Минимум:** различить logical turn и help lineage; сохранять request identity и bounded context, подключить существующую provider-neutral orchestration. Повтор turn возвращает сохранённый результат, новый вопрос получает новый ответ при сохранённом verification_required. Квота и стоимость должны ограничиваться сервером и переживать retries/restart, не только жить в in-memory reference gateway.

**Регрессия:** два разных вопроса, exact replay, mutated replay, concurrent duplicate, restart, текст → голос → текст; одна lineage, отдельные turns, ровно одна фиксация каждого принятого turn.

### F5 P1 Согласие существующего аккаунта меняется до подтверждения email

**База:** PR 186.

**Сценарий:** для уже подтверждённого synthetic аккаунта с marketing=false выполняется новый unauthenticated registration begin с marketing=true; код не вводится.

**Ожидание:** новое неподтверждённое намерение не изменяет effective consent существующего пользователя.

**Факт:** marketing_allowed меняется false → true сразу после begin. Принята и вымышленная unpublished document_version, потому что проверяется формат строки, а не актуальный server allowlist версий.

**Место:** [record decision до verification](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/identity-reference/registration_consent.py#L850-L917), [effective state](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/identity-reference/registration_consent.py#L410-L444), [проверка версии](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/identity-reference/registration_consent.py#L149-L153).

**Минимум:** записывать pending consent intent, сделать его effective только после подтверждения соответствующего контакта; preserve existing revoke до подтверждённого нового grant. Версии и hash документов разрешает сервер.

**Регрессия:** existing opted-out user + неподтверждённый begin; неверный/истёкший код; подтверждение; replay; неизвестная/устаревшая document version; revoke между begin и verify.

### F6 P1 перед реальной оплатой Неверный тип mode обходит fail closed

**База:** main, RobokassaAdapter.

**Сценарий:** constructor получает строку TEST вместо RobokassaMode.TEST, либо неизвестное значение.

**Ожидание:** безопасный TEST или явный отказ, без формирования production-shaped initiation.

**Факт:** проверки `is Enum` пропускают production admission и не добавляют IsTest. Это подтверждённая ошибка границы конфигурации. Прямой доступ злоумышленника к mode не доказан; существующий ProductionPaymentApiBoundary из PR 163 дополнительно требует правильный enum и снижает этот риск в своём пути.

**Место:** [constructor 89–111](https://github.com/niknikdym-hue/ege/blob/77cdb7ca071320dc6de90272ded7d43a0b07ea6c/eksamio-learning-engine/payments-reference/robokassa_production.py#L89-L111), [формирование поля IsTest](https://github.com/niknikdym-hue/ege/blob/77cdb7ca071320dc6de90272ded7d43a0b07ea6c/eksamio-learning-engine/payments-reference/robokassa_production.py#L142-L175).

**Минимум:** строгая нормализация/валидация enum в constructor; любое неразрешённое значение отклоняется. Production требует все точные admission flags, TEST всегда IsTest=1.

**Регрессия:** оба enum, оба строковых значения по выбранному контракту, None, typo, ложные/небулевы admission flags и отозванный admission.

### F7 P1 до включения голосового пути Потеря текста при отказе TTS

**База:** main.

**Сценарий:** STT и LLM успешны, TTS недоступен.

**Ожидание:** ученик получает уже готовый текст без второй LLM операции.

**Факт:** voice_turn бросает VoiceProviderFailure после принятия text turn. Офлайн: accepted turns=1 и history=2, но ответа нет; повтор той же аудиопосылки создаёт второй text call и второй mock quota debit.

**Место:** [sep1_russian_tutor.py 363–387](https://github.com/niknikdym-hue/ege/blob/77cdb7ca071320dc6de90272ded7d43a0b07ea6c/eksamio-learning-engine/ai-tutor-reference/sep1_russian_tutor.py#L363-L387).

**Минимум:** взять существующий подход текстового fallback из Tutor ветки; не создавать новый voice stack. [Уже имеющийся overlay](https://github.com/niknikdym-hue/ege/blob/c964ce2bb897240d2dbcd4b1527b537d17227b39/eksamio-learning-engine/ai-tutor-reference/resilient_voice_tutor.py#L31-L48) сохраняет ответ при TTS failure.

**Регрессия:** STT failure → 0 LLM; TTS failure → текст и 1 LLM; retry проигрывания → 0 новых LLM; text/voice сохраняют один episode. Имеющийся bounded REST STT не следует переименовывать в доказанный realtime streaming.

### F8 P2 Контроль ключа ударения проверяет метаданные вместо фактических ответов

**База:** PR 189.

**Сценарий:** один stress-index в pinned authority случайно меняется, остальные метаданные сохранены.

**Ожидание:** отказ source-fidelity gate.

**Факт:** изменение w002 с 1 на 2 проходит `_validate_authority`. Проверяются размер, типы, последовательные IDs и заявленные source hashes, но не hash самого вектора ответов. Неверность текущего неизменённого ключа этим не утверждается; доказана слепая зона проверки.

**Место:** [russian_orthoepy_stress_adapter.py 88–134](https://github.com/niknikdym-hue/ege/blob/05e54aa4d43abd813f306f46345f1d913f8611a2/eksamio-learning-engine/peis-service-bridge-reference/russian_orthoepy_stress_adapter.py#L88-L134).

**Минимум:** привязать hash canonical ordered ID+answer vector к уже принятому #187 evidence, как сделано у dictionary words. Добавить отрицательный тест изменения любого ответа при прежних metadata.

### F9 P2 Retry заказа меняет цену без изменения заказа

**База:** main, sandbox service; важен при переиспользовании этой логики в production.

**Сценарий:** failed order создан по цене 123 руб.; каталог обновлён до 234 руб.; retry того же заказа.

**Факт:** новый form OutSum=234, сохранённый amount=123; корректно подписанный callback на сумму retry отклоняется PaymentAmountMismatch. Реальная оплата не проводилась.

**Место:** [payments.py retry](https://github.com/niknikdym-hue/ege/blob/77cdb7ca071320dc6de90272ded7d43a0b07ea6c/eksamio-learning-engine/payments-reference/payments.py#L604-L645).

**Минимум:** retry использует immutable snapshot SKU/цены/срока/фискальных параметров исходного заказа; если нужна новая оферта, это новый явно подтверждённый заказ.

**Регрессия:** изменение цены/срока/названия, удаление SKU, повтор callback, refund после retry. Дополнительно не позволять позднему обычному receipt update перетирать REFUNDED receipt state: [update_receipt_status](https://github.com/niknikdym-hue/ege/blob/77cdb7ca071320dc6de90272ded7d43a0b07ea6c/eksamio-learning-engine/payments-reference/payments.py#L362-L399). В probe entitlement остался REVOKED, то есть повторного доступа не возникло.

## Непроверенные обязательные эксплуатационные условия

Это не новые найденные production аварии. Их нельзя считать выполненными по зелёному offline CI.

1. **Защита passwordless входа.** Код не считает неверные OTP попытки; bounded локальный тест после 12 ошибок всё ещё принимает верный код. [Проверка кода](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/identity-reference/passwordless_identity.py#L346-L371). Сам HTTP контракт уже выносит throttling/bot protection в deployment acceptance: [registration_http.py 9–12](https://github.com/niknikdym-hue/ege/blob/ae169c82a6f6e515e95293625e31e342b447f867/eksamio-learning-engine/identity-reference/registration_http.py#L9-L12). До публичной регистрации нужны проверенные лимиты challenge/contact/IP, ограничения resend и атомарная обработка. Exact-origin CORS это не заменяет.
2. **Реальный платежный маршрут.** В PR 186 имеется entitlement read, но не смонтированы create-order, provider callback, receipt/refund endpoints. PR 163 даёт framework-neutral boundary, а не действующий HTTP runtime. [Его описание границы](https://github.com/niknikdym-hue/ege/blob/fa70cf4b13bd085fd1f99f8fe320ff42ab738de4/eksamio-learning-engine/payments-reference/production_e2e_boundary.py#L183-L198). Требуется именно монтаж и PostgreSQL integration в один release, затем merchant/receipt/refund acceptance.
3. **Производственный Tutor.** PR 186/189 намеренно создаёт FailClosedTutorProvider. Сам DeepSeek adapter не соединит его автоматически с ученическим web runtime. Нужна ограниченная интеграция существующих interfaces, immutable provider/model/config identity, request/turn budget и stop switch.
4. **Retention.** Kernel возвращает scheduled/due timestamps как null. [next_due_calculation](https://github.com/niknikdym-hue/ege/blob/77cdb7ca071320dc6de90272ded7d43a0b07ea6c/eksamio-learning-engine/peis-reference-kernel/peis_reference_kernel.py#L330-L339). Имеется контракт/вывод, но не доказан реальный поздний recheck и расписание.
5. **Yandex runtime.** Не проверялись действующие ресурсы, миграции, TLS/origins, доставка почты, реальный PostgreSQL restart/restore, alerts и backup. Нельзя считать административную Owner Control панель доказательством ученического сервера.
6. **Аудио и данные несовершеннолетних.** Проверки доказывают отсутствие bytes в конкретных fixture состояниях, но не logs/storage/backups и условия реального STT/LLM/TTS провайдера. Transcript является текстовыми данными и не исчезает от обещания audio=0. До реальных учеников нужны принятые операторские/юридические значения, правила retention текста, минимальный provider context и проверка конкретной цепочки провайдеров. В audit использованы только synthetic данные.
7. **Rollback.** Скрипт переключения container revision есть; его команда соответствует официальной Yandex документации. Не доказана сквозная обратимость release с DB schema/config/model versions и восстановлением. Это rehearsal существующего плана, не требование нового deployment framework.

## Русский предмет и источник истины

current-v30 на a52bffbe содержит 46 объектов с принятыми exact component sets, 47 предметных dispositions с учётом отдельного несемантического случая; дополнительно 9 исходных route/format-only единиц. Остаются 1269 admission units и 1344 requirements предметной проверки. Равенства 9+47+1269=1325 и 9+47+1344=1400 объясняют знаменатели. **1325/1400 — учтённый объём, а не завершённое учебное покрытие.** Эти числа не являются процентом педагогической готовности.

Источники: [current-v30 counters](https://github.com/niknikdym-hue/ege/blob/a52bffbe2defef325ab5c2db4caac36b43a207e6/eksamio-learning-engine/russian-program/subject-admission/build_russian_semantic_acceptance_progress_launch_current_v30.py#L52-L90), [original packet disposition](https://github.com/niknikdym-hue/ege/blob/a52bffbe2defef325ab5c2db4caac36b43a207e6/eksamio-learning-engine/russian-program/subject-admission/build_russian_semantic_acceptance_packet.py#L226-L235), [exact-head acceptance run 34706893718](https://github.com/niknikdym-hue/ege/actions/runs/34706893718), шаги current-v30 twice/determinism/source correction все SUCCESS, проверены заново.

Утверждение false_exact_mastery=0 в предметной приёмке означает, что эта процедура не допускала ложные semantic closures. Оно не доказывает отсутствие F2/F3 в отдельном runtime inference.

121 reviewed карточка и 116 EXACT mappings не равны полной работающей программе. Production-shaped adapter допускает одну FIRST_SLICE_CARD_ID. PR 189 расширяет event admission только на четыре точных действия: stress 291, словарная пропущенная гласная 308, phraseology 199 из 285, paronym context choice по принятому корпусу. Это полезная существующая база, не завершённый школьный русский, ЕГЭ и ОГЭ.

Приоритет полного русского сохраняется. Предметную работу следует вести пакетами связанных принятых capabilities с teach/practice/fresh verify/retain и source evidence. Не дробить запуск на 1269 новых инфраструктурных задач и не обходить semantic review автоматическим fan-out по названию темы. Закрытые owner тесты runtime могут идти до окончания полного покрытия; обещание полного русского открывается только после его настоящей приёмки.

## Матрица готовности

| Область | CODE | INTEGRATED в main | LIVE |
|---|---|---|---|
| Принятые бесплатные демо и материалы | Есть; #187 уточняет identity/actions | Часть есть, reconciliation отдельный PR | В этом аудите сайт не переобследован |
| Полный русский 5–11 и EGE OGE | Частичная content/subject приёмка | Полная программа не сведена | Не доказан; scope закрыт |
| Registration session consent | Main reference; #186 durable PostgreSQL | #186 не merged; F5 и throttling acceptance | Не доказан |
| Профиль progress history plan | #186 bounded implementation | Не merged; один skill, F2/F3 | Не доказан |
| Точные события четырёх тренажёров | #187 provenance + #189 endpoints | Оба не merged; learner UI emission не подключён | Не доказан |
| Оплата receipt entitlement refund | Main reference + #163 service boundary | Не смонтировано в learner runtime | Merchant path не доказан |
| Tutor text | Main boundary; #172 benchmark; #186 lifecycle | Нет production provider; F1/F4 | Ни выбранная модель, ни качество не приняты |
| Voice и смена modality | Main fixture + веточные adapters/fallback | Требуется перенос проверенного delta; F7 | Streaming/latency/audio non-storage не доказаны |
| Retention | Контракт и ordinal inference | Schedule/recheck не доказаны | Не доказан |
| Private Yandex release | Deploy package и image pinning | Кандидаты разделены по веткам | Реальные DB/TLS/backup/rollback неизвестны |
| Owner Control | Отдельный development control plane | #209 готов к review, не merged | Не заменяет learner acceptance |

## Состояние веток и CI

Числа divergence рассчитаны по Git graph относительно main 77cdb7ca: сначала commits только в main, затем только в ветке. Это не число конфликтов и не календарный возраст. SUCCESS относится к тому точному старому tree, не к будущему merge.

| PR | HEAD | Main only / branch only | Свежо прочитанный результат |
|---|---|---:|---|
| 186 | ae169c82 | 77 / 79 | Draft; 9 workflow runs SUCCESS; не merged |
| 187 | c5592c21 | 77 / 85 | Draft; 25 runs SUCCESS; не merged |
| 189 | 05e54aa4 | 77 / 119 | Draft; 7 runs SUCCESS; base #186 |
| 172 | c964ce2b | 112 / 358 | Draft; four-brain text и voice launcher CI FAIL |
| 163 | fa70cf4b | 112 / 10 | 7 runs SUCCESS; CI_SIMULATED_CONTRACT_EVIDENCE |
| 209 | 34003dc1 | 0 / 1 | Draft; 4 workflows, 7 jobs SUCCESS; review still required |
| 200 | 99c99349 | 36 / 2 | Draft; mergeable=false; смешаны counters и UI |
| 191 | f84a74c5 | 77 / 3 | Draft; mergeable=false; основной product authority не заменён |
| 204 | 67699d5b | 24 / 4 | Draft; mergeable=false |
| 205 | 7942b6b2 | 10 / 2 | Command channel DO NOT MERGE |
| 190 / 192 | b1de5584 / 395eb696 | 77 / 24 и 77 / 1 | Development orchestration; не learner blockers |
| 181 / 182 | f722d20e / 73866031 | 77 / 1 оба | Sequencing docs; #182 Demo production standard FAIL |
| 177 | ecaf1b87 | 85 / 5 | Growth acceptance blockers; 5 runs SUCCESS; не причина задерживать closed learner test |
| 139 | f16884ec | 256 / 39 | Старый source/content salvage; 3 runs SUCCESS не semantic admission |
| 166 | e64b7e96 | 112 / 156 | Draft, 2 SUCCESS; старый Tutor stack |
| 167 / 169 | e9ca5a9b | 112 / 192 | Один HEAD на разных bases; API возвращает SUCCESS и исторический FAIL, нельзя смешивать контекст этих PR |
| 170 / 171 | 8d5485ad / cf9e3316 | 112 / 301 и 112 / 356 | Draft; по 2 SUCCESS; частные benchmark candidates |
| 164 | 8ac4b15b | 86 / 893 | CLOSED UNMERGED, архив; takeover a52bffbe имеет 86 / 894 |
| 183 | fc70100a | 77 / 77 | Поглощён #186, не main |

Открытые математические, физические и обществоведческие PR 108/119/121/122/123 сохраняются вне русского critical path. Их предметная готовность не переаттестована в этом аудите.

По #172 просмотрены точные job logs: [four-brain failure](https://github.com/niknikdym-hue/ege/actions/runs/34043488926) падает в первом OpenAI forced-provider сценарии с TutorSliceError; этот FAIL независимо повторён офлайн. [Voice humanization](https://github.com/niknikdym-hue/ege/actions/runs/34043488882) падает на Validate launchers, предыдущие voice checks проходят. Нельзя заменить это обещанием, что весь Tutor stack зелёный.

[Owner Control issue 194](https://github.com/niknikdym-hue/ege/issues/194) само показывает STALE/CONFLICT. Current 00B и handoff всё ещё содержат исторические адреса веток и старую anonymous continuity формулировку; #186 уже задаёт registered-only canonical state. При интеграции нужна точечная синхронизация действующих ссылок и статусов, без переделки панели.

## Рекомендуемый порядок после разрешения владельца

1. **Зафиксировать один release integration target на текущем main.** Старые PR остаются источниками точных deltas; не сливать цепочки целиком только потому, что GitHub показывает mergeable. Сначала regression tests на F1–F6 и F8, затем минимальные исправления. Основы — существующие PEIS, identity и provider contracts.
2. **Свести #186.** Внести исправления consent, kill switch, независимой проверки и настоящих logical Tutor turns; сохранить server-owned identity, cookie/CORS, durable lineage и registered-only scope. Повторить PostgreSQL 16, security, browser и retry/restart проверки на конечном integration SHA.
3. **Подключить #187 и #189.** Сначала source/action authority #187, затем его уже существующие Admissions Gate deltas #189 поверх исправленного runtime. Проверить F8, записать точные источники в release image; затем связать actual learner actions с этими routes. Сам endpoint без клиентского emission не даёт работающую learner функцию.
4. **Tutor выполнить двумя параллельными ограниченными частями.** DeepSeek V4.1 Flash через Yandex можно проверить раньше готовности платежей и полного русского: существующий reviewed-card benchmark + точный model URI + execution OFF default + bounded owner-authorized test. Отдельно интегрировать принятый provider в durable ученический episode. Из #172 переносить только нужные проверенные UI/provider/voice deltas; сначала исправить его известные offline FAIL. Сохранить существующий voice fallback, не менять production default по названию модели.
5. **Оплата в тот же runtime.** Переиспользовать проверяемые границы #163 и main, исправить F6/F9, смонтировать реальные routes и shared PostgreSQL; проверить replay/concurrent callbacks, receipt/refund, expiry и revoke. Не выдавать SQLite simulation за production proof.
6. **Одна закрытая deployed приёмка.** Реальная регистрация → тот же learner → отдельная Pro entitlement → русское задание → ошибка → несколько осмысленных Tutor turns → свежая независимая проверка → progress → logout/login → поздний recheck → refund/revoke. Текст, затем voice с тем же episode. Пройти desktop/mobile, провайдерные отказы, kill switches, restore и rollback на одном exact SHA/image/config.
7. **Полный русский и публичный paid go live.** Продолжать действующую предметную приёмку параллельно; открыть только реально принятый scope. Не называть bounded private learner test полным русским продуктом. Публичный promised full Russian запуск только после закрытия его content/source и существующих production gates и явного решения владельца.

**#209:** рекомендуем принять узкую проверенную защиту control proxy до следующего платного запуска API-Codex через Owner Control. Она не является зависимостью локального/native audit, offline DeepSeek adapter или learner runtime. Не ждать A1.4 ради запуска образовательного теста. README eksamio-brain прямо отделяет control plane от product runtime: [источник](https://github.com/niknikdym-hue/eksamio-brain/blob/e77cfff50a9998fe3c05c6459952903108d86f49/README.md#L1-L7).

## Первый результат который владелец сможет реально проверить

**Самый ранний: частный текстовый DeepSeek Tutor на существующей проверенной русской карточке, с несколькими последовательными вопросами.** До него нужны выбранный точный Yandex model URI, узкий adapter/runtime hookup, offline negative tests, отсутствие silent fallback, заданные лимиты времени/turns/стоимости и разрешение на конкретный live test. Не нужны A1.4, новый Owner Console, платёж или завершение всей русской программы.

Это проверяет педагогическое качество конкретной модели, а не готовность Pro. Следующий полезный результат — одна закрытая server-backed регистрация и сохранённый учебный эпизод через повторный вход. Полный оплачиваемый продукт определяется всей цепочкой выше; переименовывать частный benchmark в выполненную задачу нельзя.

Официальный каталог, ранее проверенный в текущей работе, называет модель gpt://<folder_id>/deepseek-v4.1-flash. Доступ конкретного аккаунта, latency, качество и фактический расход в этом аудите не проверялись. Старый direct DeepSeek deepseek-v4-pro в #172 не является выполнением запроса V4.1 Flash через Yandex.

## Выполненные проверки и ограничения

**Выполнены локально, без сети провайдеров:** Tutor provider-neutral boundary PASS; reliability gateway PASS; circuit repair PASS; Yandex adapter fixture PASS; main production preflight PASS с общим NOT_READY; Pro client static PASS; PEIS reference kernel PASS; payment sandbox PASS; Robokassa production admission fixture PASS; PR 186 registration consent 13 gates PASS. Дополнительные отрицательные probes воспроизвели F1/F3/F4/F5/F6/F7/F8/F9. F2 подтверждён неизменённой реализацией и тестом точного PR; PostgreSQL CI этого SHA SUCCESS.

**FAIL:** PR 172 four-brain text validator повторён локально и падает как GitHub CI. **Не выполнены здесь:** реальный PostgreSQL integration из-за отсутствия DSN и psycopg; локальный browser suite пытался запуститься, но Chromium остановлен sandbox ограничением socket/process, поэтому browser PASS не заявляется. Не выполнялись provider, payment, production HTTP вызовы, dispatch, deploy, merge или secret lookup. Исторические exact-head CI проверены чтением GitHub, но не заменяют свежий integration run.

Основной вывод: нужен один управляемый цикл исправление → интеграция → пользовательская проверка с конкретным runtime результатом. Дополнительная управляющая архитектура не закрывает обнаруженные ошибки.
