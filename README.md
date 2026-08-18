# Eksamio

Репозиторий учебной платформы Эксамио: интерактивные демоверсии ЕГЭ, тренажёры, предметные source-корпуса и Eksamio Learning Engine.

## Read first

Перед любой новой продуктовой или архитектурной работой прочитать:

1. `00-EKSAMIO-PRODUCT-MASTERPLAN.md` — целевой продукт, архитектура и приоритеты.
2. Для демоверсий — `00-READ-FIRST-EGE-DEMOVERSII-MASTER.md` и предметные регламенты/source gates.
3. Для персонализации и русского Learning Engine — `eksamio-learning-engine/AGENTS.md` и указанную там current authority chain.

## Главный принцип

Демоверсии, тренажёры и полная предметная программа не являются независимыми продуктами. Они должны работать как части одного learning loop:

`diagnose -> model -> prioritize -> practice/help -> verify -> retain -> reassess -> replan`

Официальное экзаменационное содержание и scoring остаются deterministic/source-controlled. AI подключается поверх проверенной структуры и не является источником истины.
