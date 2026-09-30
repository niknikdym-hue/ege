#!/usr/bin/env node

import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const HookApi = require('./peis_browser_hook.js');

function assert(condition, message) {
  if (!condition) throw new Error(message);
  console.log(`PASS assertion: ${message}`);
}

function blobSha(buffer) {
  const prefix = Buffer.from(`blob ${buffer.length}\0`, 'utf8');
  return crypto.createHash('sha1').update(Buffer.concat([prefix, buffer])).digest('hex');
}

function countOf(text, needle) {
  if (!needle) return 0;
  let count = 0;
  let index = 0;
  while ((index = text.indexOf(needle, index)) !== -1) {
    count += 1;
    index += needle.length;
  }
  return count;
}

function sortedKeys(value) {
  return Object.keys(value).sort();
}

const contract = JSON.parse(fs.readFileSync(path.join(HERE, 'PEIS-BROWSER-HOOK-CONTRACT-v0.1.json'), 'utf8'));
const integrationMap = JSON.parse(fs.readFileSync(path.join(HERE, 'RUSSIAN-TRAINER-BROWSER-HOOK-MAP-v0.1.json'), 'utf8'));
const hookPath = path.join(HERE, 'peis_browser_hook.js');
const hookSource = fs.readFileSync(hookPath, 'utf8');
const runtimePath = path.resolve(HERE, integrationMap.runtime.path);
const runtimeBefore = fs.readFileSync(runtimePath);
const runtimeText = runtimeBefore.toString('utf8');

assert(blobSha(runtimeBefore) === integrationMap.runtime.git_blob_sha, 'browser hook map is pinned to the actual current trainer runtime blob');
assert(countOf(runtimeText, integrationMap.runtime.anchor) === integrationMap.runtime.anchor_expected_count, 'current scoring/progress integration anchor exists exactly once');
assert(runtimeText.includes('function checkCurrent(card)'), 'actual current runtime still exposes checkCurrent(card)');
assert(runtimeText.includes('function recordCard(card,checked)'), 'actual current runtime still records current product progress before any future PEIS hook');

for (const literal of [
  'school-verb-personal-ending-conjugation-base',
  'school-participle-vowel-suffix-conjugation-base',
  'ege-ru-12-2026-12-01',
  'russian-ege-trainer-task12-v0.1'
]) {
  assert(!hookSource.includes(literal), `generic browser hook does not embed subject truth literal ${literal}`);
}
assert(!hookSource.includes('localStorage'), 'generic browser hook does not write canonical state to localStorage');
assert(!hookSource.includes('sessionStorage'), 'generic browser hook does not write canonical state to sessionStorage');
assert(!hookSource.includes('http://') && !hookSource.includes('https://'), 'generic browser hook contains no production endpoint');
assert(!hookSource.includes('fetch('), 'generic browser hook requires host-injected transport instead of defining deployment/auth itself');

const anchor = integrationMap.runtime.anchor;
const snippet = integrationMap.reference_projection.snippet;
assert(countOf(runtimeText, snippet) === 1, 'staging runtime contains exactly one canonical learner-state observation call');
assert(!snippet.includes('await'), 'runtime projection is fire-and-forget and introduces no await');
assert(runtimeText.includes('try{var hook=window.__EKSAMIO_PEIS_HOOK__') && runtimeText.includes('catch(e){return"FAILED_OPEN";}'), 'runtime adapter protects current trainer from synchronous hook failure');
assert(runtimeText.indexOf(snippet) > runtimeText.indexOf('trainerEvent("trainer_answer"'), 'hook observation occurs after existing local attempt recording');

const card = { id: 'fixture-card-12' };
const answer = ['2', '5'];
const session = {
  startedAt: 1787238000000,
  mode: 'practice',
  answers: { 'fixture-card-12': answer }
};

let disabledCalls = 0;
const disabled = HookApi.createBrowserHook({
  adapterId: 'fixture-adapter-v0.1',
  transport: async () => { disabledCalls += 1; return {}; }
});
assert(disabled.enabled === false, 'browser hook is disabled by default');
const disabledResult = await disabled.observeCheckedCard(card, session);
assert(disabledResult.status === 'DISABLED' && disabledCalls === 0, 'disabled hook sends nothing and does not call transport');

const fixedClock = () => '2026-08-20T17:30:00+03:00';
let capturedRequest = null;
let deliveredDirective = null;
const goodResponse = {
  status: 'ACCEPTED',
  event_receipt: { event_id: 'server-owned-event' },
  directive: {
    recommendation_id: 'nba.fixture.001',
    action_type: 'DIAGNOSE_TARGET',
    semantic_targets: ['server-semantic-target'],
    prerequisite_targets: ['server-prerequisite'],
    reason_codes: ['INSUFFICIENT_EVIDENCE'],
    verification_required: true,
    learner_state_watermark: 'server-state-watermark',
    route: { source_type: 'diagnostic' },
    canonical_state_owner: 'shared_peis',
    mastery: { band: 'SHOULD_NOT_LEAK' },
    evidence: ['SHOULD_NOT_LEAK']
  },
  mastery: { band: 'SHOULD_NOT_LEAK' },
  state: { hidden: true }
};
const enabled = HookApi.createBrowserHook({
  enabled: true,
  adapterId: 'fixture-adapter-v0.1',
  timeoutMs: 100,
  clock: fixedClock,
  transport: async (request) => {
    capturedRequest = request;
    return goodResponse;
  },
  onDirective: (directive) => { deliveredDirective = directive; }
});

const built1 = enabled.buildCheckedCardRequest(card, session);
const built2 = enabled.buildCheckedCardRequest(card, session);
assert(built1.payload.client_request_id === built2.payload.client_request_id, 'client_request_id is stable for the same adapter/session/card');
assert(built1.payload.answer !== answer && JSON.stringify(built1.payload.answer) === JSON.stringify(answer), 'browser request clones the product answer instead of retaining a mutable reference');
assert(sortedKeys(built1).join('|') === contract.client_request.top_level_allowed.slice().sort().join('|'), 'browser request uses only allowed top-level service fields');
assert(sortedKeys(built1.payload).join('|') === contract.client_request.payload_allowed.slice().sort().join('|'), 'browser payload uses only allowed current-product facts');
for (const field of contract.client_request.forbidden) {
  assert(!Object.prototype.hasOwnProperty.call(built1, field) && !Object.prototype.hasOwnProperty.call(built1.payload, field), `browser request does not assert forbidden field ${field}`);
}

const delivered = await enabled.observeCheckedCard(card, session);
assert(delivered.status === 'DELIVERED', 'valid host transport response is consumed without blocking current product flow');
assert(JSON.stringify(capturedRequest) === JSON.stringify(built1), 'transport receives exactly the browser-safe checked-card request');
assert(delivered.directive.canonical_state_owner === 'shared_peis', 'browser hook accepts only shared-PEIS-owned directive');
assert(deliveredDirective.action_type === 'DIAGNOSE_TARGET', 'read-only directive callback receives shared PEIS action');
assert(!Object.prototype.hasOwnProperty.call(delivered.directive, 'mastery') && !Object.prototype.hasOwnProperty.call(delivered.directive, 'evidence'), 'extra server state/evidence fields do not leak into browser directive');
assert(sortedKeys(delivered.directive).every((key) => contract.directive.allowed_fields.includes(key)), 'browser directive is filtered to the contract allowlist');

const callbackFailure = HookApi.createBrowserHook({
  enabled: true,
  adapterId: 'fixture-adapter-v0.1',
  timeoutMs: 100,
  clock: fixedClock,
  transport: async () => goodResponse,
  onDirective: () => { throw new Error('consumer failed'); }
});
const callbackResult = await callbackFailure.observeCheckedCard(card, session);
assert(callbackResult.status === 'DELIVERED' && callbackResult.callback_status === 'FAILED_OPEN', 'directive consumer failure remains fail-open and does not reject observation');

const transportFailure = HookApi.createBrowserHook({
  enabled: true,
  adapterId: 'fixture-adapter-v0.1',
  timeoutMs: 100,
  clock: fixedClock,
  transport: () => { throw new Error('transport unavailable'); }
});
const failedTransportResult = await transportFailure.observeCheckedCard(card, session);
assert(failedTransportResult.status === 'FAILED_OPEN' && failedTransportResult.reason === 'TRANSPORT_ERROR', 'synchronous transport failure is non-fatal');

const timeoutHook = HookApi.createBrowserHook({
  enabled: true,
  adapterId: 'fixture-adapter-v0.1',
  timeoutMs: 10,
  clock: fixedClock,
  transport: () => new Promise(() => {})
});
const timeoutResult = await timeoutHook.observeCheckedCard(card, session);
assert(timeoutResult.status === 'FAILED_OPEN' && timeoutResult.reason === 'TRANSPORT_TIMEOUT', 'transport timeout is non-fatal and fail-open');

const invalidDirectiveHook = HookApi.createBrowserHook({
  enabled: true,
  adapterId: 'fixture-adapter-v0.1',
  timeoutMs: 100,
  clock: fixedClock,
  transport: async () => ({ directive: { action_type: 'BAD', canonical_state_owner: 'browser' } })
});
const invalidDirectiveResult = await invalidDirectiveHook.observeCheckedCard(card, session);
assert(invalidDirectiveResult.status === 'FAILED_OPEN' && invalidDirectiveResult.reason === 'DIRECTIVE_REJECTED', 'browser rejects directive not owned by shared PEIS');

const noTransport = HookApi.createBrowserHook({ enabled: true, adapterId: 'fixture-adapter-v0.1' });
const noTransportResult = await noTransport.observeCheckedCard(card, session);
assert(noTransportResult.status === 'FAILED_OPEN' && noTransportResult.reason === 'TRANSPORT_NOT_CONFIGURED', 'enabled hook without host transport remains non-fatal');

const runtimeAfter = fs.readFileSync(runtimePath);
assert(runtimeAfter.equals(runtimeBefore), 'validation leaves actual current Russian trainer runtime byte-identical');

const summary = {
  task: 'PEIS-BROWSER-HOOK-001',
  result: 'PASS',
  current_runtime: {
    blob_sha: integrationMap.runtime.git_blob_sha,
    mutated: true,
    staging_wired: true,
    public_config_enabled: false
  },
  browser_hook: {
    default_enabled: false,
    transport: 'HOST_INJECTED',
    production_endpoint_defined: false,
    public_authentication_defined: false,
    browser_identity_sent: false,
    canonical_state_persisted_in_browser: false
  },
  safety: {
    disabled_sends_nothing: true,
    transport_error: 'FAILED_OPEN',
    transport_timeout: 'FAILED_OPEN',
    callback_error: 'FAILED_OPEN',
    invalid_directive: 'FAILED_OPEN',
    runtime_observation_fire_and_forget: true
  },
  request: {
    allowed_payload_fields: contract.client_request.payload_allowed,
    stable_client_request_id: true,
    forbidden_truth_fields_absent: true
  },
  directive: {
    read_only: true,
    canonical_state_owner: 'shared_peis',
    allowlist_enforced: true
  },
  implementation_status: 'STAGING_BROWSER_HOOK_WIRED_PUBLIC_CONFIG_DISABLED'
};
console.log(JSON.stringify(summary, null, 2));
console.log('PEIS-BROWSER-HOOK-001 VALIDATION PASS');
