import crypto from 'node:crypto';
import fs from 'node:fs';

const URL = 'https://eksamio.ru/trenazhery/russkiy/paronimy/';
const OUT = process.env.PROBE_OUT || 'live-paronyms-exact-inventory.json';
const EXPECTED_COUNT = 30;

function sha256(value) {
  return crypto.createHash('sha256').update(value, 'utf8').digest('hex');
}

async function fetchHtml() {
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
      const response = await fetch(URL, { redirect: 'follow', headers: profile.headers });
      const html = await response.text();
      attempts.push({
        round,
        profile: profile.name,
        http_status: response.status,
        final_url: response.url,
        html_bytes_utf8: Buffer.byteLength(html, 'utf8'),
        html_sha256: sha256(html),
      });
      if (response.ok) return { response, html, attempts, selected_profile: profile.name };
      await new Promise((resolve) => setTimeout(resolve, 1200));
    }
    await new Promise((resolve) => setTimeout(resolve, 2500 * round));
  }
  throw new Error(`all read-only fetch attempts failed; last=${attempts.at(-1)?.http_status ?? 'unknown'}`);
}

function skipString(source, index) {
  const quote = source[index];
  let i = index + 1;
  while (i < source.length) {
    if (source[i] === '\\') { i += 2; continue; }
    if (source[i] === quote) return i + 1;
    i += 1;
  }
  throw new Error(`unterminated string at ${index}`);
}

function skipLineComment(source, index) {
  const newline = source.indexOf('\n', index + 2);
  return newline === -1 ? source.length : newline + 1;
}

function skipBlockComment(source, index) {
  const end = source.indexOf('*/', index + 2);
  if (end === -1) throw new Error(`unterminated block comment at ${index}`);
  return end + 2;
}

function extractBalanced(source, start, open, close) {
  if (source[start] !== open) throw new Error(`expected ${open} at ${start}`);
  let depth = 0;
  let i = start;
  while (i < source.length) {
    const ch = source[i];
    if (ch === '"' || ch === "'" || ch === '`') { i = skipString(source, i); continue; }
    if (ch === '/' && source[i + 1] === '/') { i = skipLineComment(source, i); continue; }
    if (ch === '/' && source[i + 1] === '*') { i = skipBlockComment(source, i); continue; }
    if (ch === open) depth += 1;
    if (ch === close) {
      depth -= 1;
      if (depth === 0) return { text: source.slice(start, i + 1), end: i + 1 };
    }
    i += 1;
  }
  throw new Error(`unterminated ${open}${close} literal at ${start}`);
}

function splitTopLevelObjects(arrayLiteral) {
  const rows = [];
  let i = 1;
  const end = arrayLiteral.length - 1;
  while (i < end) {
    while (i < end) {
      const ch = arrayLiteral[i];
      if (/\s|,/.test(ch)) { i += 1; continue; }
      if (ch === '/' && arrayLiteral[i + 1] === '/') { i = skipLineComment(arrayLiteral, i); continue; }
      if (ch === '/' && arrayLiteral[i + 1] === '*') { i = skipBlockComment(arrayLiteral, i); continue; }
      break;
    }
    if (i >= end) break;
    if (arrayLiteral[i] !== '{') throw new Error(`EXAM_BANK contains non-object top-level value at ${i}`);
    const object = extractBalanced(arrayLiteral, i, '{', '}');
    rows.push(object.text);
    i = object.end;
  }
  return rows;
}

function compactLiteral(source) {
  let out = '';
  let i = 0;
  while (i < source.length) {
    const ch = source[i];
    if (ch === '"' || ch === "'" || ch === '`') {
      const end = skipString(source, i);
      out += source.slice(i, end);
      i = end;
      continue;
    }
    if (ch === '/' && source[i + 1] === '/') { i = skipLineComment(source, i); continue; }
    if (ch === '/' && source[i + 1] === '*') { i = skipBlockComment(source, i); continue; }
    if (/\s/.test(ch)) { i += 1; continue; }
    out += ch;
    i += 1;
  }
  return out;
}

function locateExamBank(html) {
  const re = /\b(?:const|let|var)\s+EXAM_BANK\s*=\s*\[/m;
  const matches = [...html.matchAll(new RegExp(re.source, 'gm'))];
  if (matches.length !== 1) throw new Error(`expected exactly one EXAM_BANK array assignment, got ${matches.length}`);
  const match = matches[0];
  const start = match.index + match[0].lastIndexOf('[');
  return extractBalanced(html, start, '[', ']');
}

const { response, html, attempts, selected_profile } = await fetchHtml();
const bank = locateExamBank(html);
const rows = splitTopLevelObjects(bank.text);
if (rows.length !== EXPECTED_COUNT) throw new Error(`EXAM_BANK expected ${EXPECTED_COUNT} rows, got ${rows.length}`);

const normalizedRows = rows.map(compactLiteral);
const rowHashes = normalizedRows.map(sha256);
if (new Set(rowHashes).size !== rows.length) throw new Error('EXAM_BANK deterministic row fingerprints are not unique');
const candidateIds = rowHashes.map((hash) => `par-live-v1-${hash.slice(0, 20)}`);
if (new Set(candidateIds).size !== rows.length) throw new Error('EXAM_BANK deterministic candidate IDs are not unique');

const result = {
  schema: 'eksamio.live-paronyms-exact-inventory.v0.1',
  authority: 'live eksamio.ru paronyms trainer HTML; read-only GET',
  authority_checked_at_runtime: new Date().toISOString(),
  requested_url: URL,
  final_url: response.url,
  http_status: response.status,
  selected_profile,
  attempts,
  html_bytes_utf8: Buffer.byteLength(html, 'utf8'),
  html_sha256: sha256(html),
  variable: 'EXAM_BANK',
  literal_bytes_utf8: Buffer.byteLength(bank.text, 'utf8'),
  literal_sha256: sha256(bank.text),
  live_row_count: rows.length,
  deterministic_row_fingerprint_count: rowHashes.length,
  unique_deterministic_row_fingerprint_count: new Set(rowHashes).size,
  ordered_row_fingerprint_sha256: sha256(rowHashes.join('\n')),
  sorted_row_fingerprint_sha256: sha256([...rowHashes].sort().join('\n')),
  deterministic_live_candidate_id_scheme: 'par-live-v1-<first20hex(sha256(compacted-row-literal))>',
  deterministic_live_candidate_id_count: candidateIds.length,
  unique_deterministic_live_candidate_id_count: new Set(candidateIds).size,
  deterministic_live_candidate_ids: candidateIds,
  ordered_candidate_id_sha256: sha256(candidateIds.join('\n')),
  sorted_candidate_id_sha256: sha256([...candidateIds].sort().join('\n')),
  first_candidate_id: candidateIds[0],
  last_candidate_id: candidateIds.at(-1),
  live_item_identity_discovery_status: 'COMPLETE_DETERMINISTIC_CONTENT_ADDRESSED_CANDIDATES',
  canonical_item_identity_status: 'UNKNOWN_BLOCKER',
  provenance_binding_status: 'UNKNOWN_BLOCKER',
  admission_effect: 'NONE',
  semantic_admissions: 0,
  object_closures: 0,
  mastery_admissions: 0,
  false_exact_mastery: 0,
  registered_user_identity_required_for_future_canonical_evidence: true,
  notes: [
    'The live EXAM_BANK exposes no explicit stable item-id field; these IDs are deterministic forensic candidates derived from exact live row content.',
    'Formatting-only whitespace/comments outside literals do not affect the candidate hash; semantic/canonical ownership is not inferred.',
    'No route/title/task-number inference is permitted and no learner mastery is admitted from this inventory.',
  ],
};

fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
console.log(`wrote ${OUT}`);
console.log(`paronyms rows=${result.live_row_count} candidates=${result.unique_deterministic_live_candidate_id_count}`);
console.log(`candidate hash=${result.ordered_candidate_id_sha256}`);
