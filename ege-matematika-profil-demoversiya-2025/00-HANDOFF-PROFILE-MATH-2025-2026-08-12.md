# HANDOFF — ЕГЭ профильная математика 2025

Дата контрольной точки: 2026-08-12

## ТЕКУЩИЙ СТАТУС

**SOURCE LAYER: PASS.**

**BUILD / BROWSER AUDIT: НЕ ЗАВЕРШЕНЫ.**

**TILDA: НЕ ОБНОВЛЯЛАСЬ.**

**LIVE GO: НЕТ.**

Эта точка специально зафиксирована перед перерывом так, чтобы после возвращения не повторять уже выполненный источниковый аудит и не восстанавливать контекст по переписке.

---

## ЧТО УЖЕ СДЕЛАНО

### 1. Прочитаны обязательные регламенты

Перед работой прочитаны и применены:

- `00-READ-FIRST-EGE-DEMOVERSII-MASTER.md`
- `demo-production-standard/README.md`
- `MATEMATIKA-EGE-DEMOVERSII-REGLAMENT-SOZDANIYA-I-PROVERKI.md`

Принцип соблюдён: сначала source layer, потом build/runtime.

### 2. Подтверждены источники ФИПИ 2025

Источник содержания только:

- `matematika-source-2025/ege-2025-matematika-profil-demoversiya.pdf`
- `matematika-source-2025/ege-2025-matematika-profil-specifikatsiya.pdf`
- `matematika-source-2025/ege-2025-matematika-kodifikator.pdf`

Зафиксированы SHA-256 и размеры в:

- `ege-matematika-profil-demoversiya-2025-SOURCE-REGISTER.json`

Профильная математика 2026 используется только как технический эталон движка, не как источник содержания.

### 3. Построен воспроизводимый source preprocessing

Созданы:

- `matematika-source-2025/scripts/preprocess_profile_2025.py`
- `.github/workflows/math-profile-2025-source-preprocessing.yml`

GitHub Actions успешно прогнал preprocessing на реальных PDF из репозитория.

Последний успешный source-preprocessing run:

- workflow: `Profile mathematics 2025 source preprocessing`
- run id: `31641505734`
- conclusion: `success`

Сформированы:

- канонические печатные страницы;
- текст страниц;
- координаты слов;
- source evidence;
- 37 отдельных condition-assets прямыми crop из PDF ФИПИ 2025.

### 4. Исправлена ложная проверка слова «ПРОЕКТ»

Первый валидатор ошибочно принимал слова `проектной` / `проектов` в кодификаторе за служебную метку `ПРОЕКТ`.

Исправлено: теперь дефектом считается только отдельная строка `ПРОЕКТ`.

После исправления все три источника проходят source validation.

### 5. Подтверждена структура экзамена 2025

По ФИПИ 2025 подтверждено:

- 19 заданий;
- №1–12 — краткий ответ;
- №13–19 — развёрнутый ответ;
- 235 минут;
- максимум 32 первичных балла;
- автоматическая часть: максимум 12;
- развёрнутая часть: максимум 20;
- максимумы №13–19: `2 / 3 / 2 / 2 / 3 / 4 / 4`.

### 6. Подтверждено главное отличие от профильной 2026

В демоверсии ФИПИ 2025 — **37 официальных примеров**, а не 55.

Распределение:

- №1 — 4
- №2 — 2
- №3 — 3
- №4 — 2
- №5 — 2
- №6 — 4
- №7 — 3
- №8 — 2
- №9 — 1
- №10 — 3
- №11 — 1
- №12 — 3
- №13–19 — по 1

Итого:

- краткая часть: 30 официальных примеров;
- развёрнутая часть: 7;
- всего: 37.

Это уже отражено в source maps и build data.

### 7. Ответы краткой части привязаны к ФИПИ 2025

В build script заведены ответы 30 официальных примеров №1–12, сверенные с официальной таблицей ответов ФИПИ 2025.

Не использовать ответы 2026.

### 8. Условия сделаны прямыми PDF-crop

Все 37 условий сформированы как прямые crop официального PDF ФИПИ 2025.

Важно: для альтернативных примеров красная структурная метка `ИЛИ` исключена из learner crop, потому что система сама назначает один официальный пример и ученик не должен видеть выбор вариантов.

### 9. Созданы основные карты и служебные файлы

В папке `ege-matematika-profil-demoversiya-2025/` уже есть как минимум:

- `ege-matematika-profil-demoversiya-2025-SOURCE-REGISTER.json`
- `ege-matematika-profil-demoversiya-2025-SOURCE-GATE.txt`
- `ege-matematika-profil-demoversiya-2025-SOURCE-INVENTORY.generated.json`
- `ege-matematika-profil-demoversiya-2025-ASSET-MAP.generated.json`
- `ege-matematika-profil-demoversiya-2025-EXAM-MAP.json`
- `ege-matematika-profil-demoversiya-2025-INPUT-CONTRACT.json`
- `ege-matematika-profil-demoversiya-2025-ENGINE-REUSE-MATRIX.md`
- `ege-matematika-profil-demoversiya-2025-PAGE-STATUS.txt`
- `assets/condition-*.webp`
- `source-evidence/`
- `source-diagnostics/`

### 10. Зафиксирован отдельный storage key 2025

Использовать только:

`eksamio_ege_math_profile_demo_2025_v1_0`

2025 и 2026 не должны делить попытки/localStorage.

### 11. Начат build на основе проверенного движка 2026

Созданы:

- `ege-matematika-profil-demoversiya-2025/scripts/build_profile_2025.py`
- `ege-matematika-profil-demoversiya-2025/tests/test_profile_2025.py`
- `.github/workflows/math-profile-2025-build-audit.yml`

Архитектурная идея сохранена:

**проверенный runtime 2026 + полностью отдельные данные/ассеты/ответы/критерии 2025.**

Тест рассчитан на реальный DOM-прогон всех 37 официальных примеров, scorer, reload, pagehide, navigation state, self-assessment и responsive widths.

---

## ГДЕ ИМЕННО ОСТАНОВИЛИСЬ

Первый build-and-browser-audit workflow был запущен:

- workflow: `Profile mathematics 2025 build and browser audit`
- run id: `31641851052`
- conclusion: `failure`

**Source preprocessing внутри этого run прошёл успешно.**

Падение произошло на build stage до browser audit.

Причина — чисто техническая ошибка генератора audit matrix, не содержательная ошибка ФИПИ/data layer.

Traceback:

`KeyError: 1`

Файл:

`ege-matematika-profil-demoversiya-2025/scripts/build_profile_2025.py`

Функция:

`write_audit_matrix()`

Проблемная логика:

```python
v.get("answer", f"official criteria pages {','.join(map(str,SOL_PAGES[n]))}; max {v['max_score']}")
```

У `dict.get()` default-выражение вычисляется заранее, поэтому для коротких заданий №1–12 всё равно происходит обращение к `SOL_PAGES[n]`, где ключей 1–12 нет.

### ТОЧНАЯ ПРАВКА ПРИ ПРОДОЛЖЕНИИ

Заменить эту конструкцию на явное ветвление, например:

```python
correct_answer = (
    v["answer"]
    if short
    else f"official criteria pages {','.join(map(str, SOL_PAGES[n]))}; max {v['max_score']}"
)
```

и в row использовать:

```python
"correct_answer": correct_answer,
```

Это первый следующий шаг. Не начинать заново source audit.

---

## ЧТО ДЕЛАТЬ ПОСЛЕ ПЕРЕРЫВА

Строго с текущего места:

1. Открыть этот handoff.
2. Исправить описанный `KeyError` в `build_profile_2025.py`.
3. Повторно запустить `math-profile-2025-build-audit.yml`.
4. Если build проходит — выполнить static gates.
5. Затем реальный Selenium/DOM audit всех 37 официальных примеров.
6. Проверить:
   - 30/30 short examples через настоящий input;
   - правильный и неправильный допустимый ответ;
   - green = заполнено, не правильно;
   - 7/7 textarea;
   - official criteria only after finish;
   - scorer 1–12;
   - self-assessment 13–19;
   - reload/pagehide/state;
   - отдельный storage key;
   - responsive 1280/768/390/360/320;
   - JS console;
   - каждый T123 < 45 000 bytes.
7. Только после PASS browser audit сформировать финальный `ege-matematika-profil-demoversiya-2025-v1.0.zip`.
8. После этого — Tilda upload.
9. После публикации — production smoke-test.
10. Затем ручная студенческая попытка с пользователем.
11. Только после неё возможно `LIVE GO`.

---

## ЧЕГО НЕ ДЕЛАТЬ ПРИ ПРОДОЛЖЕНИИ

- Не повторять source audit с нуля.
- Не менять профильную математику 2026.
- Не переносить 55 вариантов 2026 в 2025.
- Не заменять PDF-crop на перепечатанные условия без необходимости.
- Не показывать ученику номера официальных вариантов или `ИЛИ`.
- Не присваивать READY/LIVE GO до browser + Tilda + production + manual acceptance.
- Не использовать сторонние образовательные сайты как доказательство содержания 2025.

---

## КОНТРОЛЬНАЯ ТОЧКА

**Надёжная точка возобновления:** source layer полностью подготовлен и воспроизводим; build infrastructure создан; известен один конкретный технический blocker до первого полного build/browser audit.

Продолжать нужно с исправления `write_audit_matrix()` — не раньше и не позже.
