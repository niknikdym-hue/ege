import crypto from 'node:crypto';
import fs from 'node:fs';

const URL = 'https://eksamio.ru/trenazhery/russkiy/paronimy/';
const OUT = process.env.PROBE_OUT || 'live-paronyms-full-inventory.json';

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

function extractBalanced(source, start, open = '[', close = ']') {
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

function locateSingleArray(html, regex, label) {
  const matches = [...html.matchAll(new RegExp(regex.source, regex.flags.includes('g') ? regex.flags : `${regex.flags}g`))];
  if (matches.length !== 1) throw new Error(`expected exactly one ${label} assignment, got ${matches.length}`);
  const match = matches[0];
  const start = html.indexOf('[', match.index + match[0].length - 1);
  if (start < 0) throw new Error(`${label}: array start not found`);
  return extractBalanced(html, start, '[', ']');
}

function parseJsonArray(literal, label) {
  let value;
  try {
    value = JSON.parse(literal);
  } catch (error) {
    throw new Error(`${label}: literal is not strict JSON: ${error.message}`);
  }
  if (!Array.isArray(value)) throw new Error(`${label}: expected array`);
  return value;
}

function normalizedGroupProjection(group) {
  return JSON.stringify({
    id: group.id,
    words: group.words,
    entry_ids: group.entries.map((entry) => entry.id),
    entry_words: group.entries.map((entry) => entry.word),
  });
}

const { response, html, attempts, selected_profile } = await fetchHtml();
const prefixLiteral = locateSingleArray(
  html,
  /window\.__EKSAMIO_PARONYMS_GROUPS__\s*=\s*\[/m,
  'window.__EKSAMIO_PARONYMS_GROUPS__',
);
const suffixLiteral = locateSingleArray(
  html,
  /\b(?:var|let|const)\s+GROUPS\s*=\s*\(window\.__EKSAMIO_PARONYMS_GROUPS__\s*\|\|\s*\[\]\)\.concat\(\s*\[/m,
  'GROUPS concat suffix',
);

const prefix = parseJsonArray(prefixLiteral.text, 'prefix');
const suffix = parseJsonArray(suffixLiteral.text, 'suffix');
const groups = prefix.concat(suffix);

const groupIds = [];
const entryIds = [];
const words = [];
for (const [index, group] of groups.entries()) {
  if (!group || typeof group !== 'object' || Array.isArray(group)) throw new Error(`group ${index + 1}: not object`);
  if (typeof group.id !== 'string' || !group.id) throw new Error(`group ${index + 1}: missing id`);
  if (!Array.isArray(group.words) || group.words.length < 2 || !group.words.every((x) => typeof x === 'string' && x)) {
    throw new Error(`group ${group.id}: invalid words`);
  }
  if (!Array.isArray(group.entries) || group.entries.length !== group.words.length) {
    throw new Error(`group ${group.id}: entries/words cardinality mismatch`);
  }
  groupIds.push(group.id);
  for (const entry of group.entries) {
    if (!entry || typeof entry.id !== 'string' || typeof entry.word !== 'string') {
      throw new Error(`group ${group.id}: invalid entry identity`);
    }
    entryIds.push(entry.id);
    words.push(entry.word);
  }
}
if (new Set(groupIds).size !== groupIds.length) throw new Error('group ids are not unique');
if (new Set(entryIds).size !== entryIds.length) throw new Error('entry ids are not unique');

const groupProjections = groups.map(normalizedGroupProjection);
const result = {
  schema: 'eksamio.live-paronyms-full-inventory.v0.1',
  authority: 'live eksamio.ru paronyms trainer HTML; read-only GET; exact static reconstruction of split GROUPS backing',
  checked_at_runtime: new Date().toISOString(),
  requested_url: URL,
  final_url: response.url,
  http_status: response.status,
  selected_profile,
  attempts,
  html_bytes_utf8: Buffer.byteLength(html, 'utf8'),
  html_sha256: sha256(html),
  prefix_literal_bytes_utf8: Buffer.byteLength(prefixLiteral.text, 'utf8'),
  prefix_literal_sha256: sha256(prefixLiteral.text),
  suffix_literal_bytes_utf8: Buffer.byteLength(suffixLiteral.text, 'utf8'),
  suffix_literal_sha256: sha256(suffixLiteral.text),
  prefix_group_count: prefix.length,
  suffix_group_count: suffix.length,
  full_live_group_count: groups.length,
  unique_group_id_count: new Set(groupIds).size,
  full_live_entry_count: entryIds.length,
  unique_entry_id_count: new Set(entryIds).size,
  unique_entry_word_count: new Set(words).size,
  first_group_id: groupIds[0] ?? null,
  last_group_id: groupIds.at(-1) ?? null,
  ordered_group_id_sha256: sha256(groupIds.join('\n')),
  ordered_entry_id_sha256: sha256(entryIds.join('\n')),
  ordered_group_projection_sha256: sha256(groupProjections.join('\n')),
  group_ids: groupIds,
  entry_ids: entryIds,
  live_item_identity_discovery_status: 'COMPLETE_EXPLICIT_GROUP_AND_ENTRY_IDS_FROM_SPLIT_BACKING',
  canonical_item_identity_status: 'UNKNOWN_BLOCKER_PENDING_EXACT_FIPI_GROUP_CORRESPONDENCE_AND_SEMANTIC_ACCEPTANCE',
  provenance_binding_status: 'UNKNOWN_BLOCKER_PENDING_EXACT_FIPI_GROUP_CORRESPONDENCE',
  exam_bank_status: 'SEPARATE_30_ROW_EXAM_CHECK_SUB_BANK_NOT_USED_AS_FULL_THEMATIC_INVENTORY',
  admission_effect: 'NONE',
  semantic_admissions: 0,
  object_closures: 0,
  mastery_admissions: 0,
  false_exact_mastery: 0,
  registered_user_identity_required_for_future_canonical_evidence: true,
  notes: [
    'The live thematic GROUPS backing is split across window.__EKSAMIO_PARONYMS_GROUPS__ and an inline concat suffix; this probe reconstructs both exact JSON arrays without executing the application script.',
    'Explicit live group and entry IDs are inventory identities only; exact FIPI provenance and PEIS semantic ownership remain separate fail-closed gates.',
    'The 30-row EXAM_BANK is intentionally excluded from the full thematic denominator.',
  ],
};

fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
console.log(`wrote ${OUT}`);
console.log(`paronym groups prefix=${result.prefix_group_count} suffix=${result.suffix_group_count} total=${result.full_live_group_count}`);
console.log(`entries=${result.full_live_entry_count} uniqueEntries=${result.unique_entry_id_count}`);
console.log(`group hash=${result.ordered_group_id_sha256}`);
