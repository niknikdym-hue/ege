import crypto from 'node:crypto';
import fs from 'node:fs';

const URL = 'https://eksamio.ru/trenazhery/russkiy/paronimy/';
const OUT = process.env.PROBE_OUT || 'paronym-admission-authority-capture.json';

const EXPECTED = Object.freeze({
  issue185Head: 'c5592c212557b91578ed48e1bf778e30dd489dc7',
  liveHtmlSha256: '63ac66e839505930b2a9a2f3b5243d60e422226ec90890553aac5abc52b7cbda',
  groupCount: 144,
  entryCount: 334,
  orderedGroupIdSha256: '81c91d069a28cd9a2c1c7547c9fc92cb9df92c6cde38f3100750e2585c113813',
  orderedEntryIdSha256: '48eedc3e5f3751cec57152671456d314b7bcb6b13f2ee5002f35ec6660482c99',
  fipiExactGroupCorrespondence: '144/144',
});

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
        'user-agent': 'Eksamio-paronym-admission-capture/0.1 (+https://github.com/niknikdym-hue/ege)',
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
      if (response.ok) return { response, html, attempts, selectedProfile: profile.name };
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

const { response, html, attempts, selectedProfile } = await fetchHtml();
const liveHtmlSha256 = sha256(html);
if (liveHtmlSha256 !== EXPECTED.liveHtmlSha256) {
  throw new Error(`live paronym HTML drift: expected ${EXPECTED.liveHtmlSha256}, got ${liveHtmlSha256}`);
}

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
const items = [];

for (const [groupIndex, group] of groups.entries()) {
  if (!group || typeof group !== 'object' || Array.isArray(group)) throw new Error(`group ${groupIndex + 1}: not object`);
  if (typeof group.id !== 'string' || !group.id) throw new Error(`group ${groupIndex + 1}: missing id`);
  if (!Array.isArray(group.words) || group.words.length < 2 || !group.words.every((x) => typeof x === 'string' && x)) {
    throw new Error(`group ${group.id}: invalid words`);
  }
  if (!Array.isArray(group.entries) || group.entries.length !== group.words.length) {
    throw new Error(`group ${group.id}: entries/words cardinality mismatch`);
  }
  groupIds.push(group.id);
  for (const [entryIndex, entry] of group.entries.entries()) {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) throw new Error(`group ${group.id} entry ${entryIndex + 1}: not object`);
    if (typeof entry.id !== 'string' || !entry.id) throw new Error(`group ${group.id}: missing entry id`);
    if (typeof entry.word !== 'string' || !entry.word || !group.words.includes(entry.word)) {
      throw new Error(`entry ${entry.id}: word is not an exact group choice`);
    }
    if (typeof entry.context !== 'string' || !entry.context) throw new Error(`entry ${entry.id}: missing context`);
    if (typeof entry.meaning !== 'string' || !entry.meaning) throw new Error(`entry ${entry.id}: missing meaning`);
    const placeholderCount = (entry.context.match(/_____/g) || []).length;
    entryIds.push(entry.id);
    items.push({
      item_id: entry.id,
      group_id: group.id,
      group_words: [...group.words],
      correct_word: entry.word,
      context: entry.context,
      meaning: entry.meaning,
      exact_context_placeholder_count: placeholderCount,
      context_choice_candidate: placeholderCount === 1,
    });
  }
}

if (groups.length !== EXPECTED.groupCount) throw new Error(`expected 144 groups, got ${groups.length}`);
if (items.length !== EXPECTED.entryCount) throw new Error(`expected 334 entries, got ${items.length}`);
if (new Set(groupIds).size !== groupIds.length) throw new Error('group ids are not unique');
if (new Set(entryIds).size !== entryIds.length) throw new Error('entry ids are not unique');
if (sha256(groupIds.join('\n')) !== EXPECTED.orderedGroupIdSha256) throw new Error('ordered group id hash drift');
if (sha256(entryIds.join('\n')) !== EXPECTED.orderedEntryIdSha256) throw new Error('ordered entry id hash drift');

const candidates = items.filter((item) => item.context_choice_candidate);
const result = {
  schema: 'eksamio.paronym-context-choice-authority-capture.v0.1',
  status: 'READ_ONLY_CAPTURE_NO_PRODUCTION_ADMISSION',
  authority: 'exact live eksamio.ru split GROUPS backing, reconstructed without executing application code',
  checked_at_runtime: new Date().toISOString(),
  issue_185_pr: 187,
  issue_185_exact_head: EXPECTED.issue185Head,
  requested_url: URL,
  final_url: response.url,
  http_status: response.status,
  selected_profile: selectedProfile,
  attempts,
  live_html_bytes_utf8: Buffer.byteLength(html, 'utf8'),
  live_html_sha256: liveHtmlSha256,
  prefix_literal_bytes_utf8: Buffer.byteLength(prefixLiteral.text, 'utf8'),
  prefix_literal_sha256: sha256(prefixLiteral.text),
  suffix_literal_bytes_utf8: Buffer.byteLength(suffixLiteral.text, 'utf8'),
  suffix_literal_sha256: sha256(suffixLiteral.text),
  group_count: groupIds.length,
  entry_count: entryIds.length,
  ordered_group_id_sha256: sha256(groupIds.join('\n')),
  ordered_entry_id_sha256: sha256(entryIds.join('\n')),
  fipi_2026_exact_group_correspondence: EXPECTED.fipiExactGroupCorrespondence,
  context_choice_candidate_count: candidates.length,
  ordered_candidate_item_id_sha256: sha256(candidates.map((item) => item.item_id).join('\n')),
  ordered_candidate_correct_word_sha256: sha256(candidates.map((item) => item.correct_word).join('\n')),
  ordered_candidate_context_sha256: sha256(candidates.map((item) => item.context).join('\n')),
  ordered_candidate_group_choices_sha256: sha256(candidates.map((item) => JSON.stringify(item.group_words)).join('\n')),
  items,
  admission_effect: 'NONE',
  semantic_admissions: 0,
  object_closures: 0,
  mastery_admissions: 0,
  false_exact_mastery: 0,
  registered_user_identity_required_for_future_canonical_evidence: true,
  boundaries: {
    action_binding: 'context/collocation choice only -> ru-lexis-paronym-collocation-choice',
    meaning_match_admitted: false,
    independent_paronym_recall_admitted: false,
    exam_error_correction_admitted: false,
    generic_trainer_completion_mastery: false,
    browser_local_progress_mastery: false,
    asset_wide_mastery: false,
  },
};

fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
console.log(`wrote ${OUT}`);
console.log(`groups=${result.group_count} entries=${result.entry_count} candidates=${result.context_choice_candidate_count}`);
console.log(`live sha256=${result.live_html_sha256}`);
console.log(`candidate ids sha256=${result.ordered_candidate_item_id_sha256}`);
