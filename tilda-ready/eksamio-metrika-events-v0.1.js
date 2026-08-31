(function () {
  'use strict';

  var COUNTER_ID = 110348386;
  var ALLOWED_GOALS = new Set([
    'eks_demo_open',
    'eks_demo_start',
    'eks_demo_complete',
    'eks_result_to_practice',
    'eks_trainer_open',
    'eks_trainer_start',
    'eks_trainer_meaningful',
    'eks_return_learning',
    'eks_pro_intent',
    'eks_purchase'
  ]);

  function cleanString(value, maxLength) {
    if (typeof value !== 'string') return undefined;
    var text = value.trim();
    if (!text) return undefined;
    return text.slice(0, maxLength || 120);
  }

  function sanitizeParams(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) return {};

    var allowedKeys = new Set([
      'subject',
      'year',
      'route',
      'task_family',
      'surface',
      'release',
      'href',
      'label'
    ]);

    var out = {};
    Object.keys(input).forEach(function (key) {
      if (!allowedKeys.has(key)) return;
      var value = cleanString(String(input[key]), key === 'href' ? 300 : 120);
      if (value !== undefined) out[key] = value;
    });
    return out;
  }

  function reach(goal, params) {
    if (!ALLOWED_GOALS.has(goal)) return false;
    if (typeof window.ym !== 'function') return false;

    window.ym(COUNTER_ID, 'reachGoal', goal, sanitizeParams(params));
    return true;
  }

  function closestAnchor(target) {
    if (!target || typeof target.closest !== 'function') return null;
    return target.closest('a[href]');
  }

  document.addEventListener('click', function (event) {
    var anchor = closestAnchor(event.target);
    if (!anchor) return;

    var href = anchor.getAttribute('href') || '';
    var label = cleanString(anchor.textContent || '', 120);

    if (/\/demoversiya\//.test(href)) {
      reach('eks_demo_open', {
        surface: 'public_site',
        href: href,
        label: label
      });
      return;
    }

    if (/\/trenazhery(?:\/|$)/.test(href) || /\/trenazhery-russkiy(?:\/|$)/.test(href)) {
      reach('eks_trainer_open', {
        surface: 'public_site',
        href: href,
        label: label
      });
    }
  }, true);

  document.addEventListener('eksamio:goal', function (event) {
    var detail = event && event.detail;
    if (!detail || typeof detail !== 'object') return;
    reach(detail.goal, detail.params || {});
  });

  window.EksamioMetrika = Object.freeze({
    counterId: COUNTER_ID,
    reach: reach
  });
})();
