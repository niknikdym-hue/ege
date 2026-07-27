ПАКЕТ ИНТЕРАКТИВНОЙ ДЕМОВЕРСИИ ЕГЭ

ПРЕДМЕТ: <ПРЕДМЕТ>
ПРЕФИКС: ege-<slug>-demoversiya
ВЕРСИЯ ПАКЕТА: <VERSION>
ТЕКУЩИЙ СТАТУС: <STATUS>
ПОСТОЯННЫЙ URL: https://eksamio.ru/ege/<slug>/demoversiya/

ИСТОЧНИК ИСТИНЫ
1. <prefix>-PACKAGE-CONTRACT.json
2. <prefix>-SOURCE-REGISTER.json
3. <prefix>-EXAM-MAP.json
4. <prefix>-TASK-MAP.json
5. <prefix>-ASSET-MAP.json
6. <prefix>-ACCEPTANCE-CASES.json
7. Финальные PDF ФИПИ в source/

Сгенерированные файлы нельзя редактировать вручную:
- T123;
- PREVIEW;
- MANIFEST;
- release ZIP;
- встроенные копии SVG;
- TEST-REPORT и evidence после фактического тестового прогона.

КОМАНДА ПРЕДМЕТНЫХ ТЕСТОВ
python -m unittest discover tests
node tests/browser_test.mjs

КОМАНДА СБОРКИ
python scripts/build_demo_release.py <prefix>-PACKAGE-CONTRACT.json

КОМАНДА RELEASE-GATE
python scripts/validate_demo_package.py <prefix>-PACKAGE-CONTRACT.json

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА
- Использовать только финальную демоверсию, спецификацию и кодификатор ФИПИ.
- Не добавлять accepted answer без страницы официального источника.
- Не удалять посторонние символы до проверки ответа.
- Не сокращать критерии частичных баллов.
- Все зависимости защищать и в UI, и в scorer.
- Технические эвристики считать только ориентировочными.
- Самооценку не выдавать за официальный результат.
- Отдельные и встроенные SVG должны собираться из одного файла.
- Не включать PDF «ПРОЕКТ», старые версии, временные логи, __pycache__ и node_modules.
- Не использовать абсолютные пути.
- До проверки опубликованной страницы максимальный статус READY_FOR_TILDA_TEST.

ПОРЯДОК T123
<ВСТАВИТЬ ТОЧНЫЙ СПИСОК ИЗ EXAM MAP>

СОСТАВ RELEASE ZIP
<ВСТАВИТЬ БЕЛЫЙ СПИСОК ИЗ PACKAGE CONTRACT>

ОГРАНИЧЕНИЯ
- Реальная страница Tilda до публикации не проверена.
- Production smoke-test выполняется отдельно по TILDA-PUBLICATION-GATE.md.

РАБОЧИЙ РЕЖИМ
Выполни полный цикл проверки, исправления, сборки и тестов. Не создавай отдельные служебные архивы и не выдавай промежуточные версии как финальные.
