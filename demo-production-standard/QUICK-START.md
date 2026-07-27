# Быстрый запуск нового предмета

## 1. Создать распакованный репозиторий предмета

Не начинать работу внутри ZIP.

Рекомендуемое имя:

`ege-<subject-slug>-demoversiya-v1`

## 2. Скопировать основу

В репозиторий предмета скопировать:

- `demo-production-standard/scripts/build_demo_release.py` → `scripts/build_demo_release.py`;
- `demo-production-standard/scripts/validate_demo_package.py` → `scripts/validate_demo_package.py`;
- шаблоны из `demo-production-standard/templates/`;
- workflow из `demo-production-standard/templates/demo-release-gate.workflow.yml` → `.github/workflows/demo-release-gate.yml`;
- чек-листы — в рабочую документацию проекта.

## 3. Переименовать шаблоны

Создать:

- `<prefix>-PACKAGE-CONTRACT.json`;
- `<prefix>-EXAM-MAP.json`;
- `<prefix>-TASK-MAP.json`;
- `<prefix>-ASSET-MAP.json`;
- `<prefix>-ACCEPTANCE-CASES.json`.

Заполнить точные значения предмета. Пустые значения и `FILL_AFTER_DOWNLOAD` блокируют release.

## 4. Положить финальные PDF

Только в:

```text
source/
```

Рассчитать SHA-256 и записать их в contract и SOURCE REGISTER.

## 5. Закрыть SOURCE GATE

До T123 должны быть полностью готовы:

- карта экзамена;
- карта всех заданий и вариантов;
- официальные ответы;
- критерии;
- зависимости;
- общие нули;
- карта ассетов;
- acceptance cases.

Статус меняется на `CONTENT_LOCKED` только после независимой сверки.

## 6. Создать генератор предмета

Предметный генератор читает TASK MAP и ASSET MAP и создаёт T123.

В T123 нельзя вручную повторно набирать:

- ответы;
- максимумы;
- критерии;
- SVG;
- число заданий;
- время.

## 7. Запустить предметные тесты

```bash
python -m unittest discover tests
node tests/browser_test.mjs
```

Команды могут отличаться, но обе группы тестов обязательны.

## 8. Собрать release

```bash
python scripts/build_demo_release.py <prefix>-PACKAGE-CONTRACT.json
```

Сборщик создаёт preview, manifest и ZIP.

## 9. Проверить release

```bash
python scripts/validate_demo_package.py <prefix>-PACKAGE-CONTRACT.json
```

Ожидаемый результат:

```text
STATUS: PASS
```

## 10. Проверить распакованный ZIP

Распаковать ZIP в чистую временную папку и повторно запустить validator и тесты относительными путями.

## 11. Передать в Tilda

До публикации статус:

`READY_FOR_TILDA_TEST`

После установки выполнить `TILDA-PUBLICATION-GATE.md`.

Только успешная опубликованная проверка даёт:

`PUBLISHED_SMOKE_PASS`
