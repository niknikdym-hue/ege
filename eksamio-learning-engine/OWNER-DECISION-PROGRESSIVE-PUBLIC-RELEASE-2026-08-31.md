# Owner Decision — Progressive Public Release

**Дата:** 2026-08-31  
**Статус:** APPROVED / MUST MERGE INTO PRODUCT AUTHORITY

## Решение владельца

Eksamio не ждёт полного завершения всей платформы, чтобы показать ученикам уже готовую и безопасную ценность.

Любая learner-facing функция, раздел, предметный срез, тренажёр, диагностика, маршрут или иной продуктовый этап, который:

1. прошёл собственные обязательные subject/runtime/product acceptance gates;
2. не создаёт ложного claim полноты;
3. безопасен для ученика и не требует незакрытых payment/identity/privacy/Tutor gates;
4. production-ready для заявленного публичного scope,

**должен быть опубликован на живом сайте Eksamio без ожидания полного Pro launch или закрытия несвязанных launch blockers.**

Для уже опубликованной бесплатной и безопасной ценности разрешено и требуется начинать привлечение реальных пользователей и измерение поведения/learning outcomes; незавершённые платные/Pro/payment/identity/Tutor функции в рекламе и публичном UI не обещаются как доступные.

## Обязательный publication status

Каждый закрытый learner-facing этап получает один из статусов:

- `LIVE` — реально доступен ученику на production-сайте;
- `READY_TO_PUBLISH` — acceptance пройден, требуется только фактическая публикация;
- `BLOCKED:<reason>` — существует конкретный blocker, мешающий безопасной публикации.

Статус `DONE` без `LIVE` либо явного `BLOCKED:<reason>` не считается операционно завершённым.

Удержание готового learner-facing этапа «под капотом» без конкретного blocker запрещено.

## Scope boundary

Это решение не отменяет отдельные production gates для платного Pro, оплаты, identity, entitlements, receipt/refund/revoke, privacy и Tutor. Оно отменяет только blanket-подход «ничего нового не показывать ученикам до полного запуска всей системы» для уже готового, правдивого и безопасного публичного scope.

Это решение должно быть включено в `00-PRODUCT-MASTERPLAN.md` и учитываться `00B-PROJECT-PRIORITIES-CURRENT.md` как release-инвариант.