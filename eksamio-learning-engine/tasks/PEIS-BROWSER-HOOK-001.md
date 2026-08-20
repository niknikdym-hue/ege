# PEIS-BROWSER-HOOK-001

## Purpose

Prove a fail-open, feature-gated browser integration boundary between the actual current Russian EGE trainer runtime and the already merged PEIS service bridge, without changing production/Tilda or current trainer behavior.

## Architectural position

This task sits after:

`current product sensor -> EvidenceEvent -> shared persistence -> shared PEIS -> service bridge`

and before any deployment/auth/production rollout decision.

It must NOT create a browser learner engine or move canonical learner state into JavaScript/localStorage.

## Scope

Add-only reference artifacts under:

`eksamio-learning-engine/peis-browser-hook-reference/`

and this task contract.

Do not edit:
- current Russian trainer runtime;
- current trainer scoring;
- current trainer localStorage/session logic;
- Tilda/public production;
- shared PEIS contracts;
- mathematics or physics lanes.

## Current runtime integration surface

Pinned current runtime:

`russkiy-knigi/ege-russkiy-trenazher/ege-russkiy-trenazher-T123-10.txt`

Pinned blob SHA:

`97143363a5adfaef5609bc28fe823c31a2c1fc4d`

The current `checkCurrent(card)` path first computes the checked result, writes it into `session.checked`, calls `recordCard(card,checked)`, saves session/progress, and only then continues UI/metrics rendering.

The reference integration projection may insert only a non-blocking observation call after the existing local result/progress write path. The real runtime remains byte-identical in this gate.

## Browser trust boundary

The browser hook may send only product facts already known by the current runtime:
- card_id;
- session_started_at_ms;
- session_mode;
- answer;
- occurred_at_client;
- stable client_request_id.

The browser hook must NOT send:
- score;
- correctness;
- max_score;
- semantic_targets / semantic_id;
- mapping_resolution;
- evaluator / trust class;
- mastery;
- readiness;
- retention;
- NBA;
- prerequisite edges;
- learner_profile_id;
- anonymous/user identity refs;
- server_sequence;
- server_watermark;
- received_at_server.

Identity/auth context belongs to a later trusted host/deployment boundary, not the learner-facing hook.

## Required hook behavior

1. Disabled by default.
2. Requires explicit adapter_id and injected transport before sending anything.
3. Builds a stable browser-safe checked-card request from `card` + `session` only.
4. Never reads `checked.score`/`checked.correctness` because those are server-owned truth.
5. Never writes canonical PEIS state to localStorage/sessionStorage.
6. Never blocks current answer checking or progress saving.
7. Transport failure, timeout, invalid response, callback failure or synchronous hook failure must be fail-open.
8. Returned PEIS directive is advisory/read-only and filtered to a narrow allowlist.
9. Unknown response fields such as mastery/state/evidence are ignored by the hook.
10. Duplicate product submission uses stable request identity.

## Reference integration projection

The validator may create an in-memory projection of the current runtime with one guarded, fire-and-forget call after the existing `recordCard + saveSession` path, for example:

`try { if (window.__EKSAMIO_PEIS_HOOK__) void window.__EKSAMIO_PEIS_HOOK__.observeCheckedCard(card, session); } catch (e) {}`

This projection is validation evidence only. It must not be committed into the current trainer runtime in this task.

## Validation gates

The executable validator must prove:

- current runtime blob SHA still matches the pinned current runtime;
- exact existing scoring/progress anchor still exists once;
- real runtime remains byte-identical before/after validation;
- in-memory projection inserts only the guarded fire-and-forget hook call;
- projection preserves existing scoring/progress statements and does not introduce `await`;
- disabled hook sends nothing;
- enabled hook emits only allowed client fields;
- browser request contains no learner identity or canonical educational truth;
- client_request_id is stable for the same session/card;
- transport rejection returns FAILED_OPEN rather than throwing;
- transport timeout returns FAILED_OPEN;
- synchronous callback failure remains fail-open;
- valid service response produces only a sanitized read-only directive;
- extra server response fields do not leak into the directive;
- hook module contains no localStorage/sessionStorage writes;
- no production endpoint or public authentication claim is introduced.

## Completion evidence

Required durable files:
- `PEIS-BROWSER-HOOK-CONTRACT-v0.1.json`
- `RUSSIAN-TRAINER-BROWSER-HOOK-MAP-v0.1.json`
- `peis_browser_hook.js`
- `validate_peis_browser_hook_001.mjs`
- run output JSON
- validation TXT.

A temporary GitHub Actions workflow may be used for validation and must be removed before merge.

## Completion status

Passing this task means:

`REFERENCE_BROWSER_HOOK_VALIDATED_NOT_WIRED_TO_PRODUCTION`

It does NOT authorize Tilda publication, backend deployment, or production authentication decisions.
