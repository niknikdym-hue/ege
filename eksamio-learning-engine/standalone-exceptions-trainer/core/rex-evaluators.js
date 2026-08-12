(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    root.EksamioRussianExceptions = root.EksamioRussianExceptions || {};
    Object.assign(root.EksamioRussianExceptions, api);
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  class RexEvaluationError extends Error {
    constructor(message, code) {
      super(message);
      this.name = 'RexEvaluationError';
      this.code = code || 'evaluation_error';
    }
  }

  function normalizeText(value) {
    return String(value == null ? '' : value).normalize('NFC').trim().replace(/\s+/g, ' ');
  }

  function hasInternalUppercaseMarker(value) {
    const text = normalizeText(value);
    if (!text) return false;
    for (let i = 1; i < text.length; i += 1) {
      const ch = text[i];
      if (ch.toLocaleUpperCase('ru-RU') === ch && ch.toLocaleLowerCase('ru-RU') !== ch) return true;
    }
    return false;
  }

  function textMatches(actual, expected) {
    const a = normalizeText(actual);
    const e = normalizeText(expected);
    if (hasInternalUppercaseMarker(e)) return a === e;
    return a.toLocaleLowerCase('ru-RU') === e.toLocaleLowerCase('ru-RU');
  }

  function evaluatePractice(practice, response) {
    if (!practice || typeof practice !== 'object') {
      throw new RexEvaluationError('Practice item is missing.', 'practice_missing');
    }
    const kind = practice.response_kind;
    const answer = practice.answer;
    if (!answer || typeof answer !== 'object') {
      throw new RexEvaluationError(`${practice.practice_item_id || 'practice'}: answer is missing.`, 'answer_missing');
    }

    if (kind === 'single_choice' || kind === 'classification') {
      const expected = Number(answer.option_index);
      const actual = Number(typeof response === 'object' && response !== null ? response.option_index : response);
      if (!Number.isInteger(expected)) throw new RexEvaluationError('Expected option_index is invalid.', 'answer_invalid');
      return {
        is_correct: Number.isInteger(actual) && actual === expected,
        normalized_response: { option_index: Number.isInteger(actual) ? actual : null },
      };
    }

    if (kind === 'short_text' || kind === 'normalize_form') {
      if (typeof answer.text !== 'string') throw new RexEvaluationError('Expected text answer is invalid.', 'answer_invalid');
      const actual = typeof response === 'object' && response !== null && 'text' in response ? response.text : response;
      const candidates = [answer.text].concat(Array.isArray(practice.alt_answers) ? practice.alt_answers : []);
      return {
        is_correct: candidates.some((candidate) => textMatches(actual, candidate)),
        normalized_response: { text: normalizeText(actual) },
      };
    }

    throw new RexEvaluationError(`Unsupported response_kind: ${String(kind)}`, 'response_kind_unsupported');
  }

  return { RexEvaluationError, normalizeText, hasInternalUppercaseMarker, textMatches, evaluatePractice };
});
