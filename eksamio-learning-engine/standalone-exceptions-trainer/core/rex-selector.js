(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    root.EksamioRussianExceptions = root.EksamioRussianExceptions || {};
    Object.assign(root.EksamioRussianExceptions, api);
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const PRIORITY_RANK = { P0: 0, P1: 1, P2: 2, P3: 3 };
  const TRANSFER_RANK = { recognition: 0, guided_recall: 1, independent_context: 2, transfer: 3 };
  const ALLOWED_SOURCES = new Set(['all_exceptions','my_exceptions','work_on_errors','handoff']);

  class RexSelectionError extends Error {
    constructor(message, code) { super(message); this.name = 'RexSelectionError'; this.code = code || 'selection_error'; }
  }

  function parseTime(value) {
    if (!value) return null;
    const time = Date.parse(value);
    return Number.isFinite(time) ? time : null;
  }

  function bucketFor(exceptionId, state, nowMs, source, handoff) {
    if (handoff.has(exceptionId) && (source === 'handoff' || source === 'work_on_errors')) return ['Q4_HANDOFF', 0];
    if (state) {
      const due = parseTime(state.next_due_at);
      if (due != null && due <= nowMs) return ['Q1_DUE', (source === 'handoff' || source === 'work_on_errors') ? 1 : 0];
      if (['active','due'].includes(state.status) || Number(state.active_error_count || 0) > 0) return ['Q2_ACTIVE_ERROR', (source === 'handoff' || source === 'work_on_errors') ? 2 : 1];
      if (state.transfer_passed === false && Number(state.seen_count || 0) > 0) return ['Q3_FAILED_TRANSFER', (source === 'handoff' || source === 'work_on_errors') ? 3 : 2];
      if (state.status === 'stabilized') return ['Q7_STABILIZED', 7];
    }
    if (handoff.has(exceptionId)) return ['Q4_HANDOFF', 3];
    return ['Q5_NEW', 5];
  }

  function desiredTransferLevel(state) {
    if (!state || Number(state.seen_count || 0) === 0) return ['recognition','guided_recall','independent_context','transfer'];
    if (state.last_result === 'wrong') return ['guided_recall','independent_context','recognition','transfer'];
    if (state.last_transfer_level === 'recognition') return ['guided_recall','independent_context','transfer','recognition'];
    if (state.transfer_passed === false) return ['independent_context','transfer','guided_recall','recognition'];
    if (state.retention_passed === false) return ['transfer','independent_context','guided_recall','recognition'];
    return ['independent_context','transfer','guided_recall','recognition'];
  }

  function practiceSortKey(row, state, usedContexts, recentContexts) {
    const desired = desiredTransferLevel(state);
    const transfer = String(row.transfer_level || 'recognition');
    const desiredRank = desired.indexOf(transfer) < 0 ? 99 : desired.indexOf(transfer);
    const signature = String(row.context_signature || '');
    const repeatPenalty = signature && (usedContexts.has(signature) || recentContexts.has(signature)) ? 1 : 0;
    return [repeatPenalty, desiredRank, Object.prototype.hasOwnProperty.call(TRANSFER_RANK, transfer) ? TRANSFER_RANK[transfer] : 99, String(row.practice_item_id || '')];
  }

  function compareTuple(a, b) {
    for (let i = 0; i < Math.max(a.length, b.length); i += 1) {
      if (a[i] < b[i]) return -1;
      if (a[i] > b[i]) return 1;
    }
    return 0;
  }

  function buildCandidates(runtime, states, nowMs, source, handoff) {
    const result = [];
    for (const [exceptionId, exception] of Object.entries(runtime.exceptions || {})) {
      const practiceIds = Array.isArray(exception.practice_item_ids) ? exception.practice_item_ids : [];
      if (!practiceIds.some((pid) => runtime.practice_items && runtime.practice_items[pid] && runtime.practice_items[pid].status === 'enabled')) continue;
      const state = states[exceptionId] || null;
      if (source === 'my_exceptions' && !state) continue;
      if ((source === 'handoff' || source === 'work_on_errors') && handoff.size && !handoff.has(exceptionId)) continue;
      const [queueBucket, queueRank] = bucketFor(exceptionId, state, nowMs, source, handoff);
      const dueAt = state && state.next_due_at ? String(state.next_due_at) : '';
      const wrongMs = state ? parseTime(state.last_wrong_at) : null;
      const launchRank = Object.prototype.hasOwnProperty.call(PRIORITY_RANK, exception.launch_priority) ? PRIORITY_RANK[exception.launch_priority] : PRIORITY_RANK.P2;
      result.push({ exception_id: exceptionId, queue_bucket: queueBucket, queue_rank: queueRank, due_at: dueAt, wrong_rank: wrongMs == null ? 0 : -wrongMs, launch_rank: launchRank });
    }
    result.sort((a, b) => compareTuple([
      a.queue_rank, a.due_at || '9999-12-31T23:59:59+00:00', a.wrong_rank, a.launch_rank, a.exception_id,
    ], [
      b.queue_rank, b.due_at || '9999-12-31T23:59:59+00:00', b.wrong_rank, b.launch_rank, b.exception_id,
    ]));
    return result;
  }

  function selectSession(runtime, profile, options) {
    const opts = options || {};
    const source = opts.source || 'all_exceptions';
    if (!ALLOWED_SOURCES.has(source)) throw new RexSelectionError(`Unsupported session source: ${source}`, 'source_invalid');
    const count = Number.isInteger(opts.count) ? opts.count : 10;
    if (count <= 0) return [];
    const handoff = new Set(Array.isArray(opts.handoff_exception_ids) ? opts.handoff_exception_ids.filter(Boolean).map(String) : []);
    if ((source === 'handoff' || source === 'work_on_errors') && handoff.size === 0) return [];
    const nowMs = opts.now ? parseTime(opts.now) : Date.now();
    if (nowMs == null) throw new RexSelectionError(`Invalid now timestamp: ${String(opts.now)}`, 'now_invalid');
    const states = profile && profile.exceptions && typeof profile.exceptions === 'object' ? profile.exceptions : {};
    const candidates = buildCandidates(runtime, states, nowMs, source, handoff);

    const selected = [];
    const usedPractice = new Set();
    const usedContexts = new Set();
    const lastExceptionIds = [];
    const lastDomains = [];

    for (let passIndex = 0; passIndex < 4; passIndex += 1) {
      let madeProgress = false;
      const relaxDomain = passIndex >= 1;
      const relaxExceptionGap = passIndex >= 2;
      for (const candidate of candidates) {
        if (selected.length >= count) break;
        const exceptionId = candidate.exception_id;
        const exception = runtime.exceptions[exceptionId];
        const state = states[exceptionId] || null;
        const recentContexts = new Set(state && Array.isArray(state.recent_context_signatures) ? state.recent_context_signatures : []);
        let practices = (exception.practice_item_ids || [])
          .map((pid) => runtime.practice_items[pid])
          .filter((row) => row && row.status === 'enabled' && !usedPractice.has(row.practice_item_id));
        if (!practices.length) continue;
        if (!relaxExceptionGap && lastExceptionIds.slice(-2).includes(exceptionId)) continue;
        const domain = exception.topic_id || 'unknown';
        if (!relaxDomain && lastDomains.length >= 3 && lastDomains.slice(-3).every((x) => x === domain)) continue;
        practices.sort((a, b) => compareTuple(practiceSortKey(a, state, usedContexts, recentContexts), practiceSortKey(b, state, usedContexts, recentContexts)));
        let choice = null;
        for (const row of practices) {
          const signature = String(row.context_signature || '');
          if (signature && usedContexts.has(signature)) continue;
          choice = row;
          break;
        }
        if (!choice) continue;
        const signature = String(choice.context_signature || '');
        const reasonCode = ({
          Q1_DUE: 'due_review', Q2_ACTIVE_ERROR: 'unresolved_error', Q3_FAILED_TRANSFER: 'failed_transfer',
          Q4_HANDOFF: 'exact_handoff', Q5_NEW: 'new_core_rule', Q7_STABILIZED: 'stabilized_maintenance',
        })[candidate.queue_bucket] || 'fallback_fill';
        selected.push({
          position: selected.length + 1,
          practice_item_id: choice.practice_item_id,
          exception_id: exceptionId,
          queue_bucket: candidate.queue_bucket,
          reason_code: reasonCode,
          domain,
          mode: choice.mode,
          transfer_level: choice.transfer_level,
          context_signature: signature,
          soft_constraints_relaxed: { domain: relaxDomain, exception_gap: relaxExceptionGap },
        });
        usedPractice.add(choice.practice_item_id);
        if (signature) usedContexts.add(signature);
        lastExceptionIds.push(exceptionId);
        lastDomains.push(domain);
        madeProgress = true;
      }
      if (selected.length >= count) break;
      if (!madeProgress && passIndex >= 2) break;
    }
    return selected;
  }

  return { RexSelectionError, parseTime, desiredTransferLevel, buildCandidates, selectSession };
});
