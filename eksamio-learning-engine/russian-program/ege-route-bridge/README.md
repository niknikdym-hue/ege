# EGE 2026 exact route bridge — fail-closed blocker state

This lane tests whether the merged Russian official requirement/admission-unit layer can be connected to the already reviewed EGE-2026 task authority in current main without guessing.

## Current exact result

- EGE admission units: **259**
- official requirement members: **275**
- units with an explicitly proven EGE task number in their own normalized locator: **0**
- `TASK_ID_NOT_PROVEN`: **259/259**
- semantic admissions: **0**

The reason is structural, not a parser defect. Current normalized source locators contain:
- EDSOO distributed program/codifier codes such as `2.1.3`;
- FIPI EGE checked-requirement/content-element codes such as `1.1.2`, `3.11`, `3.8.9`;
- specification-level `STRUCTURE`, `DURATION`, `MAX-POINTS`;
- demo-level `DEMO-ROUTE`.

None of these values is itself an EGE task number. In particular, dotted FIPI codes such as `3.11` must never be interpreted as task 3 or task 11.

## Missing authority layer

The next required source artifact is the exact official FIPI EGE 2026 relation:

`task number (1–27) -> checked requirement/content-element code(s)`

with precise source document/table/page locators and source fingerprint. Only after that relation is extracted deterministically may this bridge connect an exact source admission unit to the already reviewed `ege-2026-task-* -> school-*` authority.

A bridge candidate is never semantic admission by itself. `russian_content` remains `BLOCKED_SUBJECT`; no `ru-*` identity is admitted; no learner state/mastery is written; all production switches remain OFF.
