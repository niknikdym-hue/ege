'use strict';

const fs = require('fs');
const path = require('path');
const assert = require('assert');
const os = require('os');
const child = require('child_process');

const loader = require('../core/rex-runtime-loader.js');
const evaluators = require('../core/rex-evaluators.js');
const stateApi = require('../core/rex-state.js');
const selector = require('../core/rex-selector.js');

const ROOT = path.resolve(__dirname, '../..');
const RUNTIME_PATH = path.join(ROOT, 'build/RUSSIAN-EXCEPTIONS-RUNTIME.json');
const PRACTICE_MANIFEST_PATH = path.join(ROOT, '119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json');
const runtime = JSON.parse(fs.readFileSync(RUNTIME_PATH, 'utf8'));
const practiceManifest = JSON.parse(fs.readFileSync(PRACTICE_MANIFEST_PATH, 'utf8'));
const EXPECTED_ACTIVE_PRACTICE_ITEMS = practiceManifest.expected_active_items;
assert(Number.isInteger(EXPECTED_ACTIVE_PRACTICE_ITEMS) && EXPECTED_ACTIVE_PRACTICE_ITEMS > 0, 'manifest expected_active_items must be a positive integer');

function readChunkPayloads() {
  const dir = path.join(ROOT, 'build/t123-exceptions-runtime');
  return fs.readdirSync(dir).filter((x) => x.endsWith('.txt')).sort().map((name) => {
    const text = fs.readFileSync(path.join(dir, name), 'utf8');
    const start = text.indexOf('>');
    const end = text.lastIndexOf('</script>');
    assert(start >= 0 && end > start, `bad wrapper ${name}`);
    return JSON.parse(text.slice(start + 1, end).replace(/<\\\/script/g, '</script'));
  });
}

function runtimeContentView(value) {
  return { topics: value.topics, exceptions: value.exceptions, practice_items: value.practice_items };
}

function testRuntimeLoader() {
  const chunks = readChunkPayloads();
  const assembled = loader.assembleRuntimeChunks(chunks, { expectedProductId: 'russian_exceptions', expectedContentVersion: runtime.content_version });
  assert.deepStrictEqual(runtimeContentView(assembled), runtimeContentView(runtime));
  assert.throws(() => loader.assembleRuntimeChunks(chunks.slice(0, -1)), (e) => e.code === 'chunk_count_mismatch');
  assert.throws(() => loader.assembleRuntimeChunks([chunks[0], chunks[0], ...chunks.slice(2)]), (e) => e.code === 'chunk_duplicate');
  const mixed = JSON.parse(JSON.stringify(chunks));
  mixed[1].content_version = 'sha256-wrong';
  assert.throws(() => loader.assembleRuntimeChunks(mixed), (e) => e.code === 'version_mismatch');
}

function correctResponse(item) {
  if (item.response_kind === 'single_choice' || item.response_kind === 'classification') return { option_index: item.answer.option_index };
  return { text: item.answer.text };
}

function wrongResponse(item) {
  if (item.response_kind === 'single_choice' || item.response_kind === 'classification') {
    const options = item.prompt && Array.isArray(item.prompt.options) ? item.prompt.options : [];
    if (options.length < 2) return null;
    return { option_index: (Number(item.answer.option_index) + 1) % options.length };
  }
  return { text: `${item.answer.text}x` };
}

function testEvaluators() {
  let count = 0;
  for (const item of Object.values(runtime.practice_items)) {
    assert.strictEqual(evaluators.evaluatePractice(item, correctResponse(item)).is_correct, true, item.practice_item_id);
    const wrong = wrongResponse(item);
    if (wrong) assert.strictEqual(evaluators.evaluatePractice(item, wrong).is_correct, false, `${item.practice_item_id} wrong must fail`);
    count += 1;
  }
  assert.strictEqual(count, EXPECTED_ACTIVE_PRACTICE_ITEMS, 'runtime practice count must match current manifest');
  assert.strictEqual(Object.keys(runtime.practice_items).length, EXPECTED_ACTIVE_PRACTICE_ITEMS, 'runtime practice_items object must match current manifest');
  assert.strictEqual(evaluators.textMatches(' Доктора ', 'доктора'), true);
  assert.strictEqual(evaluators.textMatches('дождалась', 'дождалАсь'), false, 'stress marker case is meaningful');
  assert.strictEqual(evaluators.textMatches('дождалАсь', 'дождалАсь'), true);
  assert.strictEqual(evaluators.textMatches('кое с кем', 'кое-с-кем'), false, 'hyphens must not be over-normalized');
  assert.strictEqual(evaluators.textMatches('всё', 'все'), false, 'ё/е must not be silently merged');
}

class FakeStorage {
  constructor() { this.map = new Map(); }
  getItem(k) { return this.map.has(k) ? this.map.get(k) : null; }
  setItem(k, v) { this.map.set(k, String(v)); }
}

function event(overrides) {
  return Object.assign({
    event_id: 'ev-1', practice_item_id: 'ex-practice-nn-forged-transfer-002', exception_id: 'n_nn_forged',
    mode: 'context_choice', started_at: '2026-08-12T10:00:00Z', answered_at: '2026-08-12T10:00:05Z',
    is_correct: false, response: { option_index: 1 }, source: 'exceptions_all', transfer_level: 'transfer',
    context_signature: 'forged_gates_transfer_context',
  }, overrides || {});
}

function testState() {
  const storage = new FakeStorage();
  const loaded = stateApi.loadProfile(storage);
  assert.strictEqual(loaded.status, 'new');
  assert.strictEqual(loaded.persistable, true);
  stateApi.saveProfile(storage, loaded.profile);
  assert.strictEqual(stateApi.loadProfile(storage).status, 'loaded');

  storage.setItem(stateApi.STORAGE_KEY, '{broken');
  const corrupt = stateApi.loadProfile(storage);
  assert.strictEqual(corrupt.status, 'corrupt');
  assert.strictEqual(corrupt.persistable, false);
  assert.strictEqual(storage.getItem(stateApi.STORAGE_KEY), '{broken', 'corrupt raw state must remain untouched');

  storage.setItem(stateApi.STORAGE_KEY, JSON.stringify({ schema_version: 99, exceptions: {}, processed_event_ids: [], state_revision: 0 }));
  const future = stateApi.loadProfile(storage);
  assert.strictEqual(future.status, 'unsupported_schema');
  assert.strictEqual(future.persistable, false);

  let profile = stateApi.createProfile({ now: '2026-08-12T10:00:00Z', profile_id: 'local-test' });
  let out = stateApi.applyAttemptEvent(profile, event());
  assert.strictEqual(out.applied, true);
  profile = out.profile;
  assert.strictEqual(profile.exceptions.n_nn_forged.wrong_count, 1);
  assert.strictEqual(profile.exceptions.n_nn_forged.active_error_count, 1);
  assert.strictEqual(profile.exceptions.n_nn_forged.transfer_passed, false);
  const replay = stateApi.applyAttemptEvent(profile, event());
  assert.strictEqual(replay.applied, false);
  assert.deepStrictEqual(replay.profile, profile);

  out = stateApi.applyAttemptEvent(profile, event({ event_id: 'ev-2', is_correct: true, answered_at: '2026-08-12T10:10:00Z', response: { option_index: 0 } }));
  profile = out.profile;
  assert.strictEqual(profile.exceptions.n_nn_forged.transfer_passed, true);
  assert.strictEqual(profile.exceptions.n_nn_forged.status, 'stabilizing');
  assert.strictEqual(profile.exceptions.n_nn_forged.active_error_count, 1, 'correct event must not silently erase unresolved error count');

  out = stateApi.applyAttemptEvent(profile, event({ event_id: 'ev-3', is_correct: true, answered_at: '2026-08-20T10:10:00Z', response: { option_index: 0 }, source: 'retention' }));
  profile = out.profile;
  assert.strictEqual(profile.exceptions.n_nn_forged.retention_passed, true);
  assert.strictEqual(profile.exceptions.n_nn_forged.retention_stage, 'delayed_review');
  assert.notStrictEqual(profile.exceptions.n_nn_forged.status, 'stabilized', 'reducer must not invent mastery threshold');
}

function pythonSelection(profile, options) {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'rex-selector-'));
  const statePath = path.join(temp, 'state.json');
  fs.writeFileSync(statePath, JSON.stringify(profile), 'utf8');
  const args = [path.join(ROOT, 'build/select_russian_exceptions_session_v2.py'), '--state', statePath, '--source', options.source, '--count', String(options.count), '--now', options.now];
  for (const id of (options.handoff_exception_ids || [])) args.push('--exception-id', id);
  const raw = child.execFileSync('python3', args, { cwd: ROOT, encoding: 'utf8' });
  fs.rmSync(temp, { recursive: true, force: true });
  return JSON.parse(raw).items;
}

function idView(rows) { return rows.map((x) => [x.practice_item_id, x.exception_id, x.queue_bucket, x.reason_code]); }

function testSelectorParity() {
  const scenarios = [];
  const empty = stateApi.createProfile({ now: '2026-08-12T10:00:00Z', profile_id: 'selector-empty' });
  scenarios.push([empty, { source: 'all_exceptions', count: 10, now: '2026-08-12T10:00:00Z', handoff_exception_ids: [] }]);

  const personal = stateApi.createProfile({ now: '2026-08-01T10:00:00Z', profile_id: 'selector-personal' });
  personal.exceptions.n_nn_forged = {exception_id:'n_nn_forged',status:'active',seen_count:2,correct_count:1,wrong_count:1,consecutive_correct:0,last_seen_at:'2026-08-11T10:00:00Z',last_wrong_at:'2026-08-11T10:00:00Z',last_correct_at:null,last_result:'wrong',last_mode:'context_choice',last_transfer_level:'transfer',next_due_at:null,retention_stage:'learning',transfer_passed:false,retention_passed:false,origin:'manual_practice',origin_ref:null,active_error_count:1,last_practice_item_id:null,recent_context_signatures:[],updated_at:'2026-08-11T10:00:00Z'};
  personal.exceptions.morph_kupol_plural = {exception_id:'morph_kupol_plural',status:'stabilizing',seen_count:3,correct_count:3,wrong_count:0,consecutive_correct:3,last_seen_at:'2026-08-01T10:00:00Z',last_wrong_at:null,last_correct_at:'2026-08-01T10:00:00Z',last_result:'correct',last_mode:'context_choice',last_transfer_level:'independent_context',next_due_at:'2026-08-10T10:00:00Z',retention_stage:'short_review',transfer_passed:true,retention_passed:false,origin:'manual_practice',origin_ref:null,active_error_count:0,last_practice_item_id:null,recent_context_signatures:[],updated_at:'2026-08-01T10:00:00Z'};
  scenarios.push([personal, { source: 'all_exceptions', count: 8, now: '2026-08-12T10:00:00Z', handoff_exception_ids: [] }]);
  scenarios.push([personal, { source: 'my_exceptions', count: 8, now: '2026-08-12T10:00:00Z', handoff_exception_ids: [] }]);
  scenarios.push([empty, { source: 'handoff', count: 4, now: '2026-08-12T10:00:00Z', handoff_exception_ids: ['paronym_garantiynyy_garantirovannyy'] }]);

  for (const [profile, opts] of scenarios) {
    assert.deepStrictEqual(idView(selector.selectSession(runtime, profile, opts)), idView(pythonSelection(profile, opts)), `selector mismatch for ${opts.source}`);
  }
  assert.deepStrictEqual(selector.selectSession(runtime, empty, { source: 'handoff', count: 5, now: '2026-08-12T10:00:00Z', handoff_exception_ids: [] }), [], 'empty exact handoff must fail closed');
  const focused = selector.selectSession(runtime, empty, { source: 'handoff', count: 10, now: '2026-08-12T10:00:00Z', handoff_exception_ids: ['paronym_garantiynyy_garantirovannyy'] });
  assert(focused.length > 0 && focused.length < 10, 'focused handoff should under-fill instead of padding duplicates');
  assert(focused.every((x) => x.exception_id === 'paronym_garantiynyy_garantirovannyy'));
  assert.strictEqual(new Set(focused.map((x) => x.practice_item_id)).size, focused.length, 'practice IDs must be unique in session');
  assert.strictEqual(new Set(focused.map((x) => x.context_signature).filter(Boolean)).size, focused.map((x) => x.context_signature).filter(Boolean).length, 'context signatures must be unique in session');
}

function testStorageNamespaceIsolation() {
  const trainer = fs.readFileSync(path.join(ROOT, 'russkiy-knigi/ege-russkiy-trenazher/ege-russkiy-trenazher-T123-10.txt'), 'utf8');
  assert(trainer.includes('eksamio:ege-russian-trainer:progress:v1'));
  assert(trainer.includes('eksamio:ege-russian-trainer:session:v1'));
  assert(!trainer.includes(stateApi.STORAGE_KEY), 'new Exceptions storage key must not collide with current trainer');
}

function main() {
  testRuntimeLoader();
  testEvaluators();
  testState();
  testSelectorParity();
  testStorageNamespaceIsolation();
  console.log(`PASS: browser core runtime/evaluator/state/selector tests; practice=${EXPECTED_ACTIVE_PRACTICE_ITEMS}`);
}

main();
