import crypto from 'node:crypto';
import fs from 'node:fs';
import vm from 'node:vm';

const OUT = process.env.PROBE_OUT || 'live-orthoepy-exact-rows.json';
const URL = 'https://eksamio.ru/trenazhery/russkiy/orfoepiya/';
const EXPECTED_COUNT = 291;

function sha256(value) {
  return crypto.createHash('sha256').update(value, 'utf8').digest('hex');
}

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
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
        accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-language': 'ru-RU,ru;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        pragma: 'no-cache',
        referer: 'https://eksamio.ru/trenazhery/russkiy/',
        'upgrade-insecure-requests': '1',
      },
    },
    {
      name: 'reconciliation-bot',
      headers: {
        'user-agent': 'Eksamio-live-asset-reconciliation/0.1 (+https://github.com/niknikdym-hue/ege)',
        accept: 'text/html,application/xhtml+xml',
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

const live = await fetchHtml(URL);
const scripts = [...live.html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
  .map((match, index) => ({ index, text: match[2] }))
  .filter((item) => item.text.trim());
const assignments = scripts.flatMap((script) =>
  findAssignments(script.text).map((assignment) => ({ ...assignment, script_index: script.index })),
);
const rawMatches = assignments.filter((assignment) => assignment.name === 'RAW');
if (rawMatches.length !== 1) throw new Error(`RAW: expected exactly one assignment, got ${rawMatches.length}`);
const raw = evaluateLiteral(rawMatches[0].literal);
if (!Array.isArray(raw)) throw new Error('RAW is not an array');
if (raw.length !== EXPECTED_COUNT) throw new Error(`RAW expected ${EXPECTED_COUNT}, got ${raw.length}`);
if (!raw.every((row) => row && typeof row === 'object' && !Array.isArray(row))) throw new Error('RAW rows must be objects');
const requiredKeys = ['g', 'i', 'p', 's'];
for (const row of raw) {
  for (const key of requiredKeys) {
    if (!Object.hasOwn(row, key)) throw new Error(`RAW row missing ${key}`);
  }
}
const ids = raw.map((row) => String(row.i));
const expectedIds = Array.from({ length: EXPECTED_COUNT }, (_, index) => `w${String(index + 1).padStart(3, '0')}`);
if (JSON.stringify(ids) !== JSON.stringify(expectedIds)) throw new Error('RAW ids are not exact sequential w001..w291');
if (new Set(ids).size !== EXPECTED_COUNT) throw new Error('RAW ids are not unique');

const rowCanonical = raw.map((row) => canonical(row));
const output = {
  schema: 'eksamio.live-orthoepy-exact-rows.v0.1',
  authority: 'live eksamio.ru public orthoepy trainer HTML; read-only GET',
  authority_checked_at_runtime: new Date().toISOString(),
  requested_url: URL,
  final_url: live.final_url,
  http_status: live.http_status,
  selected_profile: live.selected_profile,
  attempts: live.attempts,
  html_bytes_utf8: live.html_bytes_utf8,
  html_sha256: live.html_sha256,
  raw_literal_bytes_utf8: Buffer.byteLength(rawMatches[0].literal, 'utf8'),
  raw_literal_sha256: sha256(rawMatches[0].literal),
  row_count: raw.length,
  unique_id_count: new Set(ids).size,
  ordered_id_sha256: sha256(ids.join('\n')),
  ordered_row_sha256: sha256(rowCanonical.join('\n')),
  common_keys: Object.keys(raw[0]).filter((key) => raw.every((row) => Object.hasOwn(row, key))).sort(),
  rows: raw,
  admission_boundary: {
    identity_capture_only: true,
    source_provenance_admission: 0,
    semantic_admissions: 0,
    object_closures: 0,
    mastery_admissions: 0,
    false_exact_mastery: 0,
    registered_user_identity_ref_required_for_future_canonical_evidence: true,
    browser_local_progress_can_emit_mastery: false,
  },
};
fs.writeFileSync(OUT, `${JSON.stringify(output, null, 2)}\n`, 'utf8');
console.log(`LIVE_ORTHOEPY_EXACT_ROWS=PASS count=${output.row_count} ids=${output.unique_id_count}`);
console.log(`html_sha256=${output.html_sha256}`);
console.log(`raw_literal_sha256=${output.raw_literal_sha256}`);
console.log(`ordered_row_sha256=${output.ordered_row_sha256}`);
console.log('source_provenance_admission=0 semantic_admissions=0 mastery_admissions=0 false_exact_mastery=0');
