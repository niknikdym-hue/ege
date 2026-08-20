# PROFILE MATH HISTORICAL UI PARITY CONTRACT

Authority for shared UI behavior: accepted PROFILE Mathematics 2025 and 2026 implementations.

This contract applies to historical PROFILE demo builds unless a year-specific FIPI rule requires a content difference.

## Mandatory visible source label

For every assigned official example, the learner-facing source tag MUST be:

`ФИПИ <YEAR> · официальный пример <VARIANT_NUMBER>`

The official example number is visible metadata. It must not be replaced by a generic label such as `официальный материал демоверсии`.

## Variant behavior

- no learner-facing variant selector;
- one official example is assigned to the task position;
- assigned variant persists after reload;
- variant number remains visible in the source label;
- historical order/count comes only from the exact FIPI source for that year.

## Extended results

The heading MUST preserve the assigned official example number:

`Задание <TASK_NUMBER> · официальный пример <VARIANT_NUMBER>`

## Historical-content boundary

UI parity never permits copying content, answers, criteria, scoring, task count, variant count, source visuals or year-specific structure from another year. 2025/2026 are technical/UI reference only after exact-year source lock.

## Release gate

A PROFILE historical demo is not READY_FOR_TILDA if any task with multiple official examples renders a generic source label without the assigned official example number.

This requirement must be checked in real DOM/browser acceptance, including after reload.
