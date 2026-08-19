# EKSAMIO — ПРОФИЛЬНАЯ МАТЕМАТИКА ЕГЭ: ОБЯЗАТЕЛЬНЫЙ ПРОИЗВОДСТВЕННЫЙ СТАНДАРТ

**Статус:** обязателен для всех новых/архивных годовых демоверсий профильной математики.
**Дата фиксации:** 2026-08-19.

Этот документ дополняет и не ослабляет:
- `/00-SOURCE-FIDELITY-ZERO-TOLERANCE.md`;
- `/00-READ-FIRST-EGE-DEMOVERSII-MASTER.md`;
- `/demo-production-standard/README.md`;
- `/MATEMATIKA-EGE-DEMOVERSII-REGLAMENT-SOZDANIYA-I-PROVERKI.md`;
- `/eksamio-learning-engine/130-EXTENDED-ANSWER-INPUT-UX-STANDARD.txt`.

При конфликте действует более строгий запрет/gate.

## 1. SOURCE AUTHORITY — ТОЛЬКО ФИПИ НУЖНОГО ГОДА

Для каждого года источник содержания — только официальный комплект ФИПИ соответствующего года, сохранённый в `matematika-source-YYYY/`:
- `ege-YYYY-matematika-profil-demoversiya.pdf`;
- `ege-YYYY-matematika-profil-specifikatsiya.pdf`;
- `ege-YYYY-matematika-kodifikator.pdf`.

До source lock запрещено брать из соседнего года:
- число заданий;
- границу краткой/развёрнутой части;
- время;
- максимальный первичный балл;
- число официальных примеров;
- варианты `ИЛИ`;
- тексты/формулы/рисунки;
- ответы;
- критерии;
- баллы развёрнутых заданий;
- типы контролов;
- asset/page mapping;
- storage key/content version.

Принятые 2026 и 2025 — **только технические references**. Их содержание не является доказательством для 2024/2023/2022.

## 2. ЖЁСТКАЯ ПОСЛЕДОВАТЕЛЬНОСТЬ ГОДА

Нельзя переходить к следующему этапу при FAIL/TODO/ASSUMED/UNVERIFIED на предыдущем.

### Stage A — SOURCE PRELOCK
Обязательно:
1. зафиксировать точные три профильных PDF;
2. SHA-256 каждого файла;
3. размер файла;
4. physical PDF pages;
5. rotation-aware physical → printed page/half map;
6. полный текстовый extract и координаты слов для навигации по источнику;
7. проверку года/предмета/уровня;
8. отдельный namespace `matematika-source-YYYY/profile-source-lock/`.

**Запрещено использовать BASE `source-lock/` для PROFILE.** В одной годовой папке могут лежать оба уровня.

После Stage A разрешён только статус `READY_FOR_EXAM_LOCK`. `READY_FOR_BUILD = NO`.

### Stage B — YEAR-SPECIFIC EXAM LOCK
Из демоверсии + спецификации конкретного года фиксируются:
- task count;
- short/extended split;
- official examples per task;
- task/variant → printed page;
- duration;
- max primary score;
- max score per extended task;
- reference materials;
- permitted equipment;
- answer/criteria page map;
- все source anomalies.

Ни одна цифра не переносится из 2026/2025 без доказательства из PDF нужного года.

### Stage C — ANSWER / INPUT / CRITERIA LOCK
До сборки создаются и независимо сверяются:
- `ANSWER-LOCK.json` для каждого краткого официального примера;
- `INPUT-CONTRACT.json` для фактического действия ученика;
- `EXTENDED-CRITERIA-MAP.json` для каждого развёрнутого официального примера;
- официальные альтернативы, частичные баллы и зависимости критериев;
- разумная независимая перепроверка кратких ответов вычислением, где это возможно.

Scorer не строится по памяти/соседнему году.

### Stage D — VISUAL PREBUILD LOCK
Создаётся поштучный `VISUAL-INVENTORY.json` для всех:
- условий, где формула/типографика не может быть безопасно восстановлена текстом;
- графиков;
- геометрических чертежей;
- схем/диаграмм;
- таблиц-изображений;
- справочных материалов;
- официальных решений и критериев развёрнутой части.

Для каждого элемента фиксируются: task, official variant, source file SHA-256, printed page, назначение, обязательное содержимое, zoom requirement. Финальный crop не копируется из соседнего года.

Только после PASS Stages A–D разрешено `READY_FOR_VERIFIED_BUILD = YES`.

## 3. ОФИЦИАЛЬНЫЕ ПРИМЕРЫ `ИЛИ`

`ИЛИ` в PDF означает альтернативные официальные примеры одной позиции, а не выбор ученика.

Обязательное поведение:
- система назначает один официальный пример;
- назначение сохраняется после reload;
- ученик не выбирает вариант `ИЛИ`;
- structural label `ИЛИ` может быть исключён из learner condition crop, если условие после него сохранено полностью;
- каждый пример `ИЛИ` имеет отдельную audit row, answer/input/criteria contract и browser test.

## 4. ТЕКСТ, ФОРМУЛЫ И ВИЗУАЛЫ

Каждый официальный пример проходит цепочку:
`FIPI PDF → printed page → condition → typography/formula → visual → control → answer/criteria → scorer/self-evaluation → browser result`.

Официальные формулы/графики/геометрия/диаграммы/значимые visual structures — только direct contiguous render/crop из exact FIPI PDF. Допустимы только crop/rotation/safe resize/lossless technical conversion.

Запрещены:
- SVG/Canvas redraw;
- ручная перерисовка;
- реконструкция по смыслу/ответу;
- замена официальной геометрии «более красивой»;
- crop из 2026/2025 для другого года;
- сторонний сайт как visual source.

Если exact source crop получить нельзя — `VISUAL_SOURCE_GATE = FAIL`.

## 5. VISUAL UI CROP GATE — ОТДЕЛЬНО ОТ SOURCE FIDELITY

Direct source bytes сами по себе не дают PASS.

Каждый asset отдельно проверяется в интерфейсе:
- четыре края;
- оси и стрелки;
- все крайние подписи/ticks;
- единицы;
- легенды;
- точки/вершины/стороны/размеры;
- все элементы формулы;
- отсутствие строки печатного ответа;
- отсутствие соседнего задания/`ИЛИ`/чужой таблицы;
- desktop readability;
- mobile readability;
- базовая ширина;
- zoom decision.

Большие/мелкодетальные assets: enlarge + zoom in/out/reset + mobile test. Никакого универсального механического crop preset.

## 6. КРАТКАЯ ЧАСТЬ

Тип UI определяется фактическим действием ученика, а не кодом бумажного бланка.

Каждый официальный краткий пример должен пройти через **реальный DOM-control**:
- корректный ввод;
- неправильный ввод;
- очистку/изменение;
- input hygiene;
- autosave;
- reload restore;
- scorer;
- результат.

Прямая запись в state/localStorage тестом не считается.

## 7. РАЗВЁРНУТАЯ ЧАСТЬ — ОБЯЗАТЕЛЬНЫЙ UX

Для каждого развёрнутого задания текущего года:
- поле полноценного решения;
- математическая панель символов по стандарту `130-EXTENDED-ANSWER-INPUT-UX-STANDARD.txt`;
- вставка в позицию курсора и корректные шаблоны;
- reload persistence;
- до завершения официальное решение/критерии скрыты;
- после завершения показываются **«Ваш ответ» + официальный материал ФИПИ** именно назначенного примера;
- официальный solution/criteria asset полностью source-exact и читаем;
- самооценка идёт отдельно от автоматического scorer краткой части;
- максимальные баллы берутся только из спецификации/критериев данного года;
- пользовательский ответ выводится безопасно как текст, не как HTML.

## 8. АУДИТ-МАТРИЦА

Для каждого официального примера обязательна строка, как минимум:
`year, level, task, official_variant, source_file, source_sha256, printed_page, text_checked, typography_checked, formula_checked, visual_checked, visual_ui_crop_checked, asset_ref, required_control, actual_control, interaction_checked, official_answer_or_criteria, scorer_or_self_eval_checked, state_checked, result, defect_id, evidence`.

Любое пустое применимое поле запрещает PASS.

## 9. TECHNICAL ENGINE REUSE

Из принятых 2026/2025 разрешено переиспользовать только после очистки year-specific content:
- общий shell;
- navigation/timer/state patterns;
- generic short-control renderer;
- result renderer;
- zoom/lightbox;
- extended-answer toolbar mechanics;
- atomic T123 packer;
- test architecture.

Запрещено переиспользовать как evidence/content:
- task bank;
- answers;
- criteria;
- variant counts;
- crops/assets;
- references;
- page maps;
- input contracts без year-specific проверки.

## 10. T123 ATOMIC GATE

Для новых 2024/2023/2022:
- каждый T123 самостоятельный синтаксически закрытый фрагмент;
- никакого mechanical byte split;
- никакого незакрытого `<script>`, `<style>`, HTML tag, JS string/template/comment;
- base64 разбивается только заранее на отдельные законченные `<script>...</script>` chunks;
- каждый блок валидируется отдельно;
- затем симулируется paste `01..N`;
- формируется `T123-MANIFEST` с bytes + SHA-256;
- лимит **< 42 500 bytes**;
- после repack полный browser regression.

Принятый старый пакет может иметь иной исторический count/threshold; это не переносится на новый год.

## 11. FULL BROWSER / STATE / RESPONSIVE GATES

До release:
- каждый официальный краткий пример correct + wrong через DOM;
- каждый extended example: ввод/сохранение/результат/официальный критерий/self-eval;
- полный экзаменационный attempt;
- таймер;
- Previous/Next/number navigation;
- mark-for-return;
- assigned variant persistence;
- answer persistence;
- reload/pagehide restore;
- reset;
- results;
- no severe console errors;
- 1280/768/390/360/320;
- zoom in/out/reset/mobile.

## 12. FREEZE / CLEAN ZIP / INDEPENDENT AUDIT

Финальный порядок:
1. все working-directory gates PASS;
2. manifest/package contract обновлены;
3. ZIP frozen;
4. ZIP распакован в новую чистую папку;
5. полный gate chain повторён из clean extraction;
6. отдельный independent final audit с нуля по FIPI source + clean ZIP;
7. только после этого `READY_FOR_TILDA = YES`.

`LIVE_GO = YES` только после Tilda publication + public production smoke + manual student acceptance.

## 13. CHANGE CONTROL

После приёмки года пакет замораживается. Не пересобирать «ради чистоты» или нового общего renderer. Reopen только при:
- подтверждённом дефекте;
- подтверждённом mismatch с ФИПИ;
- обязательной platform compatibility change;
- прямом указании пользователя.

После изменения повторяются все затронутые gates; изменение общего renderer требует regression всех использующих его типов.

## 14. ПОРЯДОК АРХИВА 2024 → 2023 → 2022

Работать последовательно по годам, но каждый год начинать как независимый source-locked продукт:
`PROFILE YYYY SOURCE PRELOCK → EXAM LOCK → ANSWER/INPUT/CRITERIA LOCK → VISUAL PREBUILD LOCK → VERIFIED BUILD → FULL GATES → CLEAN ZIP → INDEPENDENT AUDIT → TILDA`.

Успех предыдущего года не отменяет ни одного source gate следующего.
