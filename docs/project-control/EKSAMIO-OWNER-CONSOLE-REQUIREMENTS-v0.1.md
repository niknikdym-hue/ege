# Eksamio Owner Console — Whole-Project Control Panel Requirements v0.1

**Status:** DRAFT implementation contract  
**Date:** 2026-09-09  
**Authority inputs:**
- `eksamio-learning-engine/00-PRODUCT-MASTERPLAN.md` v2.0;
- `eksamio-learning-engine/00B-PROJECT-PRIORITIES-CURRENT.md`;
- live GitHub repository/PR/commit/workflow state.

## 1. Purpose

Owner Console is the owner's control surface for the **entire Eksamio development program**. It is not a learner-facing page and must not be deployed inside the public/protected learner runtime merely to provide project management UI.

The console answers, at a glance:

1. Where are we in the whole Eksamio roadmap?
2. What is the exact critical path to the next real user-visible milestone?
3. What work is code-only versus actually visible/working in production?
4. What is blocked, by what, and who can unblock it?
5. What is Astra/Codex working on now?
6. What remains after the first Russian launch before Russian is fully implemented?
7. What follows after Russian: Mathematics, Physics and later subjects?
8. What genuinely requires owner action now?

## 2. Non-negotiable project visibility

The console must always show this complete product route:

`A RUSSIAN PUBLIC PAID LAUNCH -> B RUSSIAN FULL PRODUCT -> C MATHEMATICS -> D PHYSICS -> E NEXT SUBJECTS / PLATFORM SCALE`

Later stages may be collapsed, but they may not disappear from the Whole Project view.

A user must never need to inspect GitHub branches manually to understand whether registration, servers, Pro, payments, Russian learning, Tutor, progress or future subjects are unfinished.

## 3. Required top-level layout

### Header

- current repository;
- current `main` SHA;
- current active milestone;
- last successful synchronization time;
- `SOURCE OF TRUTH OK` or `STALE/CONFLICT`;
- owner-action count;
- current autonomous work count;
- critical blocker count.

### Whole-project stage rail

Five persistent stage blocks:

1. `A — Russian Public Paid Launch`;
2. `B — Russian Full Product`;
3. `C — Mathematics`;
4. `D — Physics`;
5. `E — Next Subjects / Platform Scale`.

Each block shows:

- stage status;
- honest completion denominator when finite;
- number of tasks by status;
- number of blockers;
- learner-visible result achieved yes/no;
- next milestone.

Do not fabricate a percentage when the denominator is not objectively defined. Prefer `12/31 required tasks at target state` over an invented 73%.

## 4. Required views

### 4.1 Whole Project

All stages A–E and all product/workstream tasks.

### 4.2 Critical Path

Only tasks that can move or block the next milestone. Must preserve dependency order, not merely priority labels.

### 4.3 Russian Product

Stage A + Stage B together. The first paid launch must never make unfinished full-Russian work disappear.

### 4.4 Visible Product

A user-facing truth table:

- public site;
- registration/login;
- Pro purchase;
- entitlement;
- Russian navigation;
- diagnostics;
- work on mistakes;
- next action;
- Tutor text;
- Tutor voice;
- progress;
- return login;
- support/refund.

Each row visibly separates:

`CODE_READY` / `PRIVATE_PRODUCTION_PASS` / `VISIBLE_TO_LEARNER`.

### 4.5 Owner Gates

Only actions that actually require the owner under current policy. Example classes:

- merge approval if policy requires it;
- deployment/publication;
- provider live spend outside an already approved bounded smoke;
- payment/refund live action;
- production learner-data write/migration;
- secret create/rotate/expose;
- public traffic go-live.

No routine development question may be placed here merely because an agent lacks confidence.

### 4.6 Blockers

Grouped by blocker type:

- `SUBJECT`;
- `INTEGRATION`;
- `EXTERNAL_PROVIDER`;
- `PRODUCTION_INFRA`;
- `LEGAL/OPERATOR`;
- `OWNER_GATE`;
- `QUALITY/E2E`.

### 4.7 History

Accepted milestones, merged work and previously critical items remain queryable. Completed work must not disappear and make the project look as though nothing has been achieved.

## 5. Task row/card contract

Every task must expose:

- `task_id`;
- title;
- plain-Russian user-visible outcome;
- stage;
- workstream;
- priority;
- status;
- target state;
- dependencies;
- blocker type + blocker detail;
- branch;
- PR;
- exact head SHA;
- CI/check evidence;
- `visible_to_learner`;
- `production_state`;
- executor (`Astra`, `Codex`, `Owner`, `External`);
- owner gate required yes/no;
- current action;
- next action;
- last evidence timestamp;
- evidence links/identifiers;
- optional finite denominator with numerator/denominator and unit meaning.

## 6. Status semantics

Use the shared project vocabulary:

- `NOT_STARTED`;
- `DESIGNED`;
- `CODE_READY`;
- `INTEGRATION_PENDING`;
- `BLOCKED_SUBJECT`;
- `BLOCKED_EXTERNAL`;
- `PRIVATE_PRODUCTION_PASS`;
- `VISIBLE_TO_LEARNER`;
- `PUBLIC_LAUNCH_PASS`;
- `DONE`.

The console must never collapse these to one generic green `Done`.

## 7. Source-of-truth model

The panel itself is not authority.

### Semantic/project plan

Read from:

1. `00-PRODUCT-MASTERPLAN.md`;
2. `00B-PROJECT-PRIORITIES-CURRENT.md`;
3. explicit owner decisions referenced by them.

### Repository facts

Read from GitHub:

- `main`;
- branches;
- PR metadata;
- exact SHA;
- workflow/check results;
- merge state.

### Runtime/production facts

A claim such as `VISIBLE_TO_LEARNER` or `PRIVATE_PRODUCTION_PASS` requires a registered acceptance artifact/evidence source, not inference from a successful CI job.

If two sources disagree, show `STALE/CONFLICT`; never silently choose the more optimistic value.

## 8. Astra/Codex activity panel

Show current agent activity separately from product completion:

- Senior Brain current objective;
- current task plan ID;
- bounded executor task(s);
- expected evidence;
- exact repo/branch/SHA boundary;
- run state;
- last review decision;
- owner gate if encountered.

Agent activity is not progress by itself. It becomes product progress only after accepted evidence moves a project task.

## 9. Notifications

The console should surface only actionable notifications:

- owner gate reached;
- critical-path task newly blocked;
- CI/evidence contradiction;
- branch/source-of-truth moved under an active task;
- private-production acceptance passed/failed;
- user-visible milestone changed;
- all gates for owner go-live are finally green.

Routine successful commits need not interrupt the owner if the board updates normally.

## 10. Safety / isolation

Owner Console must be isolated from learner production:

- no learner production writes merely to display project state;
- no payment/refund actions from status rendering;
- no secrets rendered or logged;
- no raw provider credentials in browser;
- no dependency that can make Eksamio learner runtime fail if the console is unavailable;
- no public internet exposure by default for a local/private development console.

## 11. Acceptance criteria for Owner Console v1

Owner Console v1 is accepted only when:

1. Whole Project shows all A–E stages from the operational board.
2. Every Stage A launch task is represented.
3. Every Stage B full-Russian task remains visible after Stage A is complete.
4. Mathematics and Physics appear as future stages without stealing current critical-path priority.
5. GitHub current main/PR/SHA/CI facts are refreshed automatically.
6. A code-only item cannot render as learner-visible.
7. Owner Gates contains only real owner-gated actions.
8. A source conflict renders visibly as `STALE/CONFLICT`.
9. No secrets or learner data are required to display the console.
10. The console can fail without affecting the learner-facing Eksamio runtime.

## 12. Implementation order

1. machine-readable projection of Masterplan + Operational Board;
2. GitHub read-only status adapter;
3. local/private whole-project UI;
4. Critical Path + Russian Product + Visible Product + Owner Gates views;
5. Astra/Codex activity feed;
6. conflict detection;
7. automated tests for stage/task completeness and status semantics;
8. only then optional remote/private hosting if the owner wants it and security review permits it.