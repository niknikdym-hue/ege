ЕГЭ РУССКИЙ ЯЗЫК 2026 — TASK 27 / v4.2
FINAL STATUS: PASS — GO FOR TILDA UPLOAD
Дата независимого повторного аудита: 2026-08-14

Итоговая модель:
1. Во время экзамена доступны «На бумаге» и «Демо-ввод в браузере».
2. В demo textarea отключены spellcheck, autocomplete, autocorrect, autocapitalize и сторонние writing suggestions.
3. При завершении demo-текст фиксируется один раз и показывается read-only в блоке «Ваше сочинение».
4. Редактируемый «Перенесённый текст» и локальный фото/скан-референс доступны только paper mode.
5. После завершения выполняется «Предварительная автоматическая проверка» с confirmed/possible/technical слоями.
6. Встроенный regex-анализ формирует только possible/technical; confirmed автоматически не создаётся.
7. Confirmed, полученный только отдельной однозначной проверкой, задаёт hard cap К7–К10: 1–2 → 2, 3–4 → 1, 5+ → 0.
8. Possible и technical hard cap не меняют.
9. Отсутствие findings не доказывает отсутствие ошибок и не выставляет автоматически 3.
10. Самооценка задания 27 — только 0–22; официальный общий результат без экспертной проверки остаётся недоступен.

Архитектура пакета:
- обязательны T123-01 … T123-06;
- T123-06 непосредственно после T123-05;
- reset-guard для отдельного Task 27 review-state находится в T123-06;
- основной state key: eksamio_ege_russian_demo_2026_v4_1;
- review key: eksamio_ege_russian_demo_2026_v4_2_task27_review.

Reset guard:
при отсутствии/idle/повреждённом core state stale review-state удаляется; при running/finished сохраняется. Regression: PASS 6/6 assertions.

Подробный аудит regex-правил: TASK27-ANALYSIS-RULE-AUDIT.txt.
Результаты тестов: TASK27-HOTFIX-TEST-RESULT.txt и LOCAL-TEST-RESULT.txt.

Пакет разрешён к загрузке в Tilda. LIVE GO присваивается только после полного PASS AFTER-PUBLISH-CHECKLIST.txt.
