import crypto from 'node:crypto';
import fs from 'node:fs';
import vm from 'node:vm';

const LIVE_URL = 'https://eksamio.ru/trenazhery/russkiy/slovarnye-slova/';
const EXPECTED_ISSUE_185_HEAD = 'c5592c212557b91578ed48e1bf778e30dd489dc7';
const EXPECTED_ACTION_BINDING_BLOB_SHA1 = '6b513376a3040dc28e9c869028687144ccf0ff87';
const EXPECTED_HTML_SHA256 = '610e866aad13c901b944c3fac9acfa840a01fecf89091cd0c7fc6e0dbb537d1a';
const EXPECTED_WORDS_LITERAL_SHA256 = 'f0794a22340fa3ff71c0a2b21b79ce6cc64bc120f3b0030431923e73c4a1a186';
const EXPECTED_ORDERED_ID_SHA256 = '989ff8c27d3017bd3c5d3b7cb3a4a47979d7354a18daa0318589a6a01a116ea2';
const EXPECTED_COUNT = 308;
const OUT = process.env.PROBE_OUT || 'dictionary-words-admission-authority-capture.json';

function sha256(value) {
  return crypto.createHash('sha256').update(value, 'utf8').digest('hex');
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

function findNamedLiteral(html, variable) {
  const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)].map((match) => match[1]);
  const literals = [];
  for (const script of scripts) {
    const re = new RegExp(`(?:^|[;\\n])\\s*(?:const|let|var)\\s+${variable}\\s*=\\s*`, 'g');
    let match;
    while ((match = re.exec(script)) !== null) {
      let start = re.lastIndex;
      while (/\s/.test(script[start] ?? '')) start += 1;
      if (!['[', '{'].includes(script[start])) continue;
      const literal = extractBalanced(script, start);
      if (literal) literals.push(literal);
      re.lastIndex = start + (literal?.length ?? 1);
    }
  }
  if (literals.length !== 1) throw new Error(`${variable}: expected exactly one literal assignment, got ${literals.length}`);
  return literals[0];
}

async function fetchLive() {
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
      },
    },
    {
      name: 'admissions-authority-capture',
      headers: {
        'user-agent': 'Eksamio-admissions-authority-capture/0.1 (+https://github.com/niknikdym-hue/ege)',
        accept: 'text/html,application/xhtml+xml',
      },
    },
  ];
  const attempts = [];
  for (let round = 1; round <= 3; round += 1) {
    for (const profile of profiles) {
      const response = await fetch(LIVE_URL, { redirect: 'follow', headers: profile.headers });
      const html = await response.text();
      attempts.push({ round, profile: profile.name, status: response.status, final_url: response.url, html_sha256: sha256(html) });
      if (response.ok) return { html, attempts, selected_profile: profile.name, final_url: response.url };
      await new Promise((resolve) => setTimeout(resolve, 1200));
    }
    await new Promise((resolve) => setTimeout(resolve, 2500 * round));
  }
  throw new Error(`live dictionary trainer fetch failed: ${JSON.stringify(attempts)}`);
}

const live = await fetchLive();
const htmlSha = sha256(live.html);
if (htmlSha !== EXPECTED_HTML_SHA256) {
  throw new Error(`live HTML drift: expected ${EXPECTED_HTML_SHA256}, got ${htmlSha}`);
}
const literal = findNamedLiteral(live.html, 'WORDS');
const literalSha = sha256(literal);
if (literalSha !== EXPECTED_WORDS_LITERAL_SHA256) {
  throw new Error(`WORDS literal drift: expected ${EXPECTED_WORDS_LITERAL_SHA256}, got ${literalSha}`);
}
const rows = vm.runInNewContext(`(${literal})`, Object.create(null), { timeout: 1000, microtaskMode: 'afterEvaluate' });
if (!Array.isArray(rows) || rows.length !== EXPECTED_COUNT) throw new Error(`WORDS must contain exactly ${EXPECTED_COUNT} rows`);
const ids = [];
const letters = [];
const answerKey = {};
const allowedLetters = new Set(['а', 'е', 'ё', 'и', 'о', 'у', 'ы', 'э', 'ю', 'я']);
for (const [index, row] of rows.entries()) {
  if (!row || typeof row !== 'object' || Array.isArray(row)) throw new Error(`WORDS row ${index + 1} is not an object`);
  const { id, letter, mask, word } = row;
  if (typeof id !== 'string' || !id) throw new Error(`WORDS row ${index + 1} missing id`);
  if (typeof letter !== 'string' || !allowedLetters.has(letter)) throw new Error(`WORDS row ${id} has invalid answer letter`);
  if (typeof mask !== 'string' || !mask) throw new Error(`WORDS row ${id} missing mask`);
  if (typeof word !== 'string' || !word) throw new Error(`WORDS row ${id} missing word`);
  if (Object.hasOwn(answerKey, id)) throw new Error(`duplicate dictionary item id: ${id}`);
  ids.push(id);
  letters.push(letter);
  answerKey[id] = letter;
}
if (new Set(ids).size !== EXPECTED_COUNT) throw new Error('dictionary item IDs are not unique');
const orderedIdSha = sha256(ids.join('\n'));
if (orderedIdSha !== EXPECTED_ORDERED_ID_SHA256) {
  throw new Error(`ordered dictionary ID drift: expected ${EXPECTED_ORDERED_ID_SHA256}, got ${orderedIdSha}`);
}

const output = {
  schema: 'eksamio.dictionary-words-admission-authority-capture.v0.1',
  status: 'READ_ONLY_CAPTURE_PINNED_TO_ACCEPTED_ISSUE_185_BYTES',
  source_authority: {
    issue_185_pr: 187,
    issue_185_exact_head: EXPECTED_ISSUE_185_HEAD,
    action_binding_blob_sha1: EXPECTED_ACTION_BINDING_BLOB_SHA1,
    live_url: LIVE_URL,
    live_html_sha256: htmlSha,
    words_literal_sha256: literalSha,
    ordered_id_sha256: orderedIdSha,
    source_backed_textual_provenance: '308/308',
  },
  admission: {
    item_count: EXPECTED_COUNT,
    action_id: 'missing_root_vowel_insertion',
    semantic_id: 'school-root-vowel-dictionary-unverifiable',
    mapping_resolution: 'EXACT',
    registered_user_identity_ref_required: true,
    anonymous_identity_ref_forbidden: true,
    server_evaluator: 'deterministic_missing_root_vowel_v1',
  },
  ordered_item_ids: ids,
  answer_letter_by_item_id: answerKey,
  ordered_answer_letters_sha256: sha256(letters.join('\n')),
  boundaries: {
    whole_word_recall_admitted: false,
    five_row_exam_mode_admitted: false,
    generic_trainer_completion_mastery: false,
    browser_local_progress_mastery: false,
    asset_wide_mastery: false,
    false_exact_mastery: 0,
  },
  capture: {
    selected_profile: live.selected_profile,
    final_url: live.final_url,
    attempts: live.attempts,
  },
};
fs.writeFileSync(OUT, `${JSON.stringify(output, null, 2)}\n`, 'utf8');
console.log(`DICTIONARY_WORDS_AUTHORITY_CAPTURE=PASS rows=${ids.length} html=${htmlSha} literal=${literalSha}`);
