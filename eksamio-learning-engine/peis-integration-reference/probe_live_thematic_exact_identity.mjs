import crypto from 'node:crypto';
import fs from 'node:fs';
import vm from 'node:vm';

const OUT = process.env.PROBE_OUT || 'live-thematic-exact-identity-probe.json';

const pages = {
  orthoepy: {
    url: 'https://eksamio.ru/trenazhery/russkiy/orfoepiya/',
    variable: 'RAW',
    expectedCount: 291,
    candidateKey: 'i',
  },
  dictionary_words: {
    url: 'https://eksamio.ru/trenazhery/russkiy/slovarnye-slova/',
    variable: 'WORDS',
    expectedCount: 308,
    candidateKey: 'id',
  },
  paronyms: {
    url: 'https://eksamio.ru/trenazhery/russkiy/paronimy/',
    variable: 'EXAM_BANK',
    expectedCount: 30,
    candidateKey: null,
  },
  phraseology: {
    url: 'https://eksamio.ru/trenazhery/russkiy/frazeologizmy/',
    variable: null,
    expectedCount: null,
    candidateKey: null,
  },
};

function sha256(value) {
  return crypto.createHash('sha256').update(value, 'utf8').digest('hex');
}

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${canonical(value[k])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function extractBalanced(source, start) {
  const open = source[start];
  const close = open === '[' ? ']' : open === '{' ? '}' : null;
  if (!close) return null;
  let depth = 0;
  let quote = null;
  let escaped = false;
  let lineComment = false;
  let blockComment = false;
  for (let i = start; i < source.length; i += 1) {
    const ch = source[i];
    const next = source[i + 1] ?? '';
    if (lineComment) {
      if (ch === '\n') lineComment = false;
      continue;
    }
    if (blockComment) {
      if (ch === '*' && next === '/') {
        blockComment = false;
        i += 1;
      }
      continue;
    }
    if (quote) {
      if (escaped) {
        escaped = false;
        continue;
      }
      if (ch === '\\') {
        escaped = true;
        continue;
      }
      if (ch === quote) quote = null;
      continue;
    }
    if (ch === '/' && next === '/') {
      lineComment = true;
      i += 1;
      continue;
    }
    if (ch === '/' && next === '*') {
      blockComment = true;
      i += 1;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') {
      quote = ch;
      continue;
    }
    if (ch === open) depth += 1;
    if (ch === close) {
      depth -= 1;
      if (depth === 0) return source.slice(start, i + 1);
    }
  }
  return null;
}

function findAssignments(script) {
  const out = [];
  const re = /(?:^|[;\n])\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*/g;
  let match;
  while ((match = re.exec(script)) !== null) {
    let start = re.lastIndex;
    while (/\s/.test(script[start] ?? '')) start += 1;
    if (!['[', '{'].includes(script[start])) continue;
    const literal = extractBalanced(script, start);
    if (!literal) continue;
    out.push({ name: match[1], literal });
    re.lastIndex = start + literal.length;
  }
  return out;
}

function evaluateLiteral(literal) {
  return vm.runInNewContext(`(${literal})`, Object.create(null), {
    timeout: 500,
    microtaskMode: 'afterEvaluate',
  });
}

async function fetchHtml(url) {
  const profiles = [
    {
      name: 'browser-compatible',
      headers: {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-language': 'ru-RU,ru;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': 'https://eksamio.ru/trenazhery/russkiy/',
        'upgrade-insecure-requests': '1',
      },
    },
    {
      name: 'reconciliation-bot',
      headers: {
        'user-agent': 'Eksamio-live-asset-reconciliation/0.1 (+https://github.com/niknikdym-hue/ege)',
        'accept': 'text/html,application/xhtml+xml',
      },
    },
  ];
  const attempts = [];
  for (let round = 1; round <= 3; round += 1) {
    for (const profile of profiles) {
      const response = await fetch(url, { redirect: 'follow', headers: profile.headers });
      const html = await response.text();
      attempts.push({
        round,
        profile: profile.name,
        http_status: response.status,
        final_url: response.url,
        html_bytes_utf8: Buffer.byteLength(html, 'utf8'),
        html_sha256: sha256(html),
      });
      if (response.ok) {
        return {
          html,
          attempts,
          selected_profile: profile.name,
          http_status: response.status,
          final_url: response.url,
          html_bytes_utf8: Buffer.byteLength(html, 'utf8'),
          html_sha256: sha256(html),
        };
      }
      await new Promise((resolve) => setTimeout(resolve, 1200));
    }
    await new Promise((resolve) => setTimeout(resolve, 3000 * round));
  }
  const last = attempts[attempts.length - 1];
  throw new Error(`${url}: all read-only profiles failed; last HTTP ${last?.http_status ?? 'unknown'}`);
}

function summarizeNamedArray(assignments, variable, expectedCount, candidateKey) {
  const matches = assignments.filter((x) => x.name === variable);
  if (matches.length !== 1) throw new Error(`${variable}: expected exactly one literal assignment, got ${matches.length}`);
  const { literal } = matches[0];
  const value = evaluateLiteral(literal);
  if (!Array.isArray(value)) throw new Error(`${variable}: expected array`);
  if (value.length !== expectedCount) throw new Error(`${variable}: expected ${expectedCount}, got ${value.length}`);
  if (!value.every((row) => row && typeof row === 'object' && !Array.isArray(row))) {
    throw new Error(`${variable}: expected object rows`);
  }

  const commonKeys = Object.keys(value[0]).filter((key) => value.every((row) => Object.hasOwn(row, key))).sort();
  const rowHashes = value.map((row) => sha256(canonical(row)));
  const result = {
    variable,
    literal_bytes_utf8: Buffer.byteLength(literal, 'utf8'),
    literal_sha256: sha256(literal),
    row_count: value.length,
    common_keys: commonKeys,
    unique_row_fingerprints: new Set(rowHashes).size,
    row_fingerprints_sha256: sha256(rowHashes.join('\n')),
  };

  if (candidateKey) {
    const candidateValues = value.map((row) => row[candidateKey]);
    if (!candidateValues.every((v) => typeof v === 'string' || typeof v === 'number')) {
      throw new Error(`${variable}.${candidateKey}: missing scalar values`);
    }
    const normalized = candidateValues.map(String);
    const unique = new Set(normalized).size;
    if (unique !== value.length) {
      throw new Error(`${variable}.${candidateKey}: expected ${value.length} unique values, got ${unique}`);
    }
    result.live_candidate_key_field = candidateKey;
    result.live_candidate_key_count = normalized.length;
    result.live_candidate_key_unique = unique;
    result.live_candidate_keys = normalized;
    result.live_candidate_keys_sha256 = sha256(normalized.join('\n'));
    result.canonical_item_identity_status = 'LIVE_EXACT_CANDIDATE_KEYS_CAPTURED_NOT_SEMANTICALLY_ADMITTED';
  } else {
    result.canonical_item_identity_status = 'NO_EXPLICIT_STABLE_ITEM_ID_IN_CAPTURED_LITERAL';
  }
  return result;
}

function summarizeAllAssignments(assignments) {
  return assignments.map(({ name, literal }) => {
    let value;
    try {
      value = evaluateLiteral(literal);
    } catch (error) {
      return {
        variable: name,
        literal_bytes_utf8: Buffer.byteLength(literal, 'utf8'),
        literal_sha256: sha256(literal),
        status: 'EVALUATION_FAILED',
        error: String(error?.message ?? error),
      };
    }
    return {
      variable: name,
      literal_bytes_utf8: Buffer.byteLength(literal, 'utf8'),
      literal_sha256: sha256(literal),
      status: 'EVALUATED',
      root_type: Array.isArray(value) ? 'array' : typeof value,
      root_count: Array.isArray(value) ? value.length : null,
      root_keys: value && typeof value === 'object' && !Array.isArray(value) ? Object.keys(value).sort() : [],
    };
  });
}

const results = [];
for (const [key, spec] of Object.entries(pages)) {
  const live = await fetchHtml(spec.url);
  const scriptMatches = [...live.html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];
  const inlineScripts = scriptMatches.map((m, index) => ({ index, text: m[2] })).filter((x) => x.text.trim());
  const assignments = inlineScripts.flatMap((script) =>
    findAssignments(script.text).map((assignment) => ({ ...assignment, script_index: script.index })),
  );

  const record = {
    key,
    requested_url: spec.url,
    final_url: live.final_url,
    http_status: live.http_status,
    selected_profile: live.selected_profile,
    attempts: live.attempts,
    html_bytes_utf8: live.html_bytes_utf8,
    html_sha256: live.html_sha256,
    script_tag_count: scriptMatches.length,
    inline_script_count: inlineScripts.length,
    admission_effect: 'NONE',
    semantic_admissions: 0,
    mastery_admissions: 0,
    false_exact_mastery: 0,
  };

  if (spec.variable) {
    record.exact_live_backing_candidate = summarizeNamedArray(
      assignments,
      spec.variable,
      spec.expectedCount,
      spec.candidateKey,
    );
  } else {
    record.exact_live_backing_candidate = null;
    record.canonical_item_identity_status = 'UNKNOWN_BLOCKER';
    record.literal_assignment_inventory = summarizeAllAssignments(assignments);
  }

  results.push(record);
  await new Promise((resolve) => setTimeout(resolve, 2500));
}

const output = {
  schema: 'eksamio.live-thematic-exact-identity-probe.v0.1',
  authority: 'live eksamio.ru public thematic trainer HTML; read-only GET',
  authority_checked_at_runtime: new Date().toISOString(),
  scope: 'forensic live backing capture only; no semantic owner inference',
  semantic_admissions: 0,
  object_closures: 0,
  mastery_admissions: 0,
  false_exact_mastery: 0,
  registered_user_identity_required_for_future_canonical_evidence: true,
  pages: results,
};

fs.writeFileSync(OUT, `${JSON.stringify(output, null, 2)}\n`, 'utf8');
console.log(`wrote ${OUT}`);
for (const page of results) {
  const c = page.exact_live_backing_candidate;
  console.log(
    `${page.key}: html=${page.html_sha256} candidate=${c ? `${c.variable}:${c.row_count}` : 'UNKNOWN_BLOCKER'}`,
  );
}
