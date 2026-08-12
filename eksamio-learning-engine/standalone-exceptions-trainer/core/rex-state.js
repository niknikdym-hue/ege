(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    root.EksamioRussianExceptions = root.EksamioRussianExceptions || {};
    Object.assign(root.EksamioRussianExceptions, api);
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const STORAGE_KEY = 'eksamio:russian:exceptions';
  const SCHEMA_VERSION = 1;

  class RexStateError extends Error {
    constructor(message, code) {
      super(message);
      this.name = 'RexStateError';
      this.code = code || 'state_error';
    }
  }

  function clone(value) { return JSON.parse(JSON.stringify(value)); }
  function nowIso() { return new Date().toISOString(); }
  function randomId(prefix) {
    if (typeof crypto !== 'undefined' && crypto && typeof crypto.randomUUID === 'function') return `${prefix}${crypto.randomUUID()}`;
    return `${prefix}${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
  }

  function createProfile(options) {
    const opts = options || {};
    const created = opts.now || nowIso();
    return {
      schema_version: SCHEMA_VERSION,
      profile_id: opts.profile_id || randomId('local-'),
      created_at: created,
      updated_at: created,
      exceptions: {},
      processed_event_ids: [],
      state_revision: 0,
      session_history: [],
    };
  }

  function validateProfile(profile) {
    if (!profile || typeof profile !== 'object' || Array.isArray(profile)) throw new RexStateError('Learner profile must be an object.', 'profile_invalid');
    if (profile.schema_version !== SCHEMA_VERSION) throw new RexStateError(`Unsupported learner-state schema: ${String(profile.schema_version)}`, 'schema_unsupported');
    if (!profile.exceptions || typeof profile.exceptions !== 'object' || Array.isArray(profile.exceptions)) throw new RexStateError('profile.exceptions must be object.', 'profile_invalid');
    if (!Array.isArray(profile.processed_event_ids) || !profile.processed_event_ids.every((x) => typeof x === 'string')) throw new RexStateError('processed_event_ids must be string array.', 'profile_invalid');
    if (!Number.isInteger(profile.state_revision) || profile.state_revision < 0) throw new RexStateError('state_revision must be non-negative integer.', 'profile_invalid');
    return true;
  }

  function loadProfile(storage, key) {
    const storageKey = key || STORAGE_KEY;
    if (!storage || typeof storage.getItem !== 'function') return { profile: null, status: 'unavailable', persistable: false, raw: null };
    let raw;
    try { raw = storage.getItem(storageKey); } catch (error) { return { profile: null, status: 'unavailable', persistable: false, raw: null }; }
    if (raw == null || raw === '') return { profile: createProfile(), status: 'new', persistable: true, raw: null };
    try {
      const parsed = JSON.parse(raw);
      validateProfile(parsed);
      return { profile: parsed, status: 'loaded', persistable: true, raw };
    } catch (error) {
      return { profile: null, status: error && error.code === 'schema_unsupported' ? 'unsupported_schema' : 'corrupt', persistable: false, raw };
    }
  }

  function saveProfile(storage, profile, key) {
    validateProfile(profile);
    if (!storage || typeof storage.setItem !== 'function') throw new RexStateError('Storage is unavailable.', 'storage_unavailable');
    storage.setItem(key || STORAGE_KEY, JSON.stringify(profile));
    return true;
  }

  function originFromSource(source) {
    return ({
      exceptions_all: 'manual_practice', my_exceptions: 'manual_practice', retry: 'manual_practice',
      retention: 'retention_failure', main_trainer_handoff: 'main_trainer_exact_error',
    })[source] || 'manual_practice';
  }

  function newExceptionState(exceptionId, answeredAt, origin) {
    return {
      exception_id: exceptionId, status: 'new', seen_count: 0, correct_count: 0, wrong_count: 0,
      consecutive_correct: 0, last_seen_at: null, last_wrong_at: null, last_correct_at: null,
      last_result: null, last_mode: null, last_transfer_level: null, next_due_at: null,
      retention_stage: 'new', transfer_passed: false, retention_passed: false, origin,
      origin_ref: null, active_error_count: 0, last_practice_item_id: null,
      recent_context_signatures: [], updated_at: answeredAt,
    };
  }

  function validateEvent(event) {
    if (!event || typeof event !== 'object' || Array.isArray(event)) throw new RexStateError('Attempt event must be object.', 'event_invalid');
    const required = ['event_id','practice_item_id','exception_id','mode','started_at','answered_at','is_correct','response','source'];
    const missing = required.filter((field) => !(field in event));
    if (missing.length) throw new RexStateError(`Attempt event missing fields: ${missing.join(', ')}`, 'event_invalid');
    for (const field of ['event_id','practice_item_id','exception_id','mode','started_at','answered_at','source']) {
      if (typeof event[field] !== 'string' || !event[field]) throw new RexStateError(`event.${field} must be non-empty string.`, 'event_invalid');
    }
    if (typeof event.is_correct !== 'boolean') throw new RexStateError('event.is_correct must be boolean.', 'event_invalid');
    if (event.transfer_level != null && !['recognition','guided_recall','independent_context','transfer'].includes(event.transfer_level)) throw new RexStateError(`invalid transfer_level: ${String(event.transfer_level)}`, 'event_invalid');
    return true;
  }

  function applyAttemptEvent(profileInput, eventInput) {
    validateEvent(eventInput);
    const event = clone(eventInput);
    const profile = profileInput == null ? createProfile({ now: event.answered_at }) : clone(profileInput);
    validateProfile(profile);
    if (profile.processed_event_ids.includes(event.event_id)) return { profile, applied: false };

    const id = event.exception_id;
    let state = profile.exceptions[id] ? clone(profile.exceptions[id]) : newExceptionState(id, event.answered_at, originFromSource(event.source));
    for (const key of ['seen_count','correct_count','wrong_count','consecutive_correct','active_error_count']) {
      if (!Number.isInteger(state[key]) || state[key] < 0) state[key] = 0;
    }
    if (!Array.isArray(state.recent_context_signatures)) throw new RexStateError(`${id}: recent_context_signatures must be array.`, 'profile_invalid');
    if (typeof state.transfer_passed !== 'boolean') state.transfer_passed = false;
    if (typeof state.retention_passed !== 'boolean') state.retention_passed = false;

    state.seen_count += 1;
    state.last_seen_at = event.answered_at;
    state.last_mode = event.mode;
    state.last_transfer_level = event.transfer_level || null;
    state.last_practice_item_id = event.practice_item_id;
    state.updated_at = event.answered_at;

    if (typeof event.context_signature === 'string' && event.context_signature) {
      state.recent_context_signatures = state.recent_context_signatures.filter((x) => x !== event.context_signature);
      state.recent_context_signatures.push(event.context_signature);
      state.recent_context_signatures = state.recent_context_signatures.slice(-12);
    }

    if (event.is_correct) {
      state.correct_count += 1;
      state.consecutive_correct += 1;
      state.last_correct_at = event.answered_at;
      state.last_result = 'correct';
      if (state.status === 'new') state.status = 'active';
      if (['independent_context','transfer'].includes(event.transfer_level)) {
        state.transfer_passed = true;
        state.status = 'stabilizing';
        if ([null, undefined, 'new', 'learning'].includes(state.retention_stage)) state.retention_stage = 'short_review';
      }
      if (event.source === 'retention' && ['independent_context','transfer'].includes(event.transfer_level)) {
        state.retention_passed = true;
        state.status = 'stabilizing';
        state.retention_stage = 'delayed_review';
      }
    } else {
      state.wrong_count += 1;
      state.consecutive_correct = 0;
      state.last_wrong_at = event.answered_at;
      state.last_result = 'wrong';
      state.active_error_count += 1;
      state.status = 'active';
      state.retention_stage = 'learning';
      if (['independent_context','transfer'].includes(event.transfer_level)) state.transfer_passed = false;
      if (event.source === 'retention') state.retention_passed = false;
    }

    if (state.origin_ref == null) state.origin_ref = event.practice_item_id;
    profile.exceptions[id] = state;
    profile.processed_event_ids.push(event.event_id);
    profile.state_revision += 1;
    profile.updated_at = event.answered_at;
    return { profile, applied: true };
  }

  return { STORAGE_KEY, SCHEMA_VERSION, RexStateError, createProfile, validateProfile, loadProfile, saveProfile, applyAttemptEvent };
});
