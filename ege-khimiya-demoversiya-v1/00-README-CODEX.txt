ПАКЕТ ИНТЕРАКТИВНОЙ ДЕМОВЕРСИИ ЕГЭ ПО ХИМИИ

Версия: 1.0.0
Статус: READY_FOR_TILDA_TEST
URL: https://eksamio.ru/ege/khimiya/demoversiya/

Источник истины: SOURCE-REGISTER, EXAM-MAP, TASK-MAP, ASSET-MAP и ACCEPTANCE-CASES.
Финальные PDF ФИПИ находятся в source/.

Команды:
python -m unittest discover tests
node tests/browser_test.mjs
python scripts/build_demo_release.py ege-khimiya-demoversiya-PACKAGE-CONTRACT.json
python scripts/validate_demo_package.py ege-khimiya-demoversiya-PACKAGE-CONTRACT.json

T123 устанавливаются по порядку 01–08. Шапка и футер подключаются отдельно.
До отдельного smoke-test опубликованной страницы статус не повышать.
