import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { spawnSync } from 'node:child_process';

const OUT = process.env.PROBE_OUT || 'live-fipi-primary-correspondence.json';
const SOURCES = {
  dictionary_live: 'https://eksamio.ru/trenazhery/russkiy/slovarnye-slova/',
  phraseology_live: 'https://eksamio.ru/trenazhery/russkiy/frazeologizmy/',
  orthography_fipi: 'https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-5-orfografija.pdf',
  lexicon_fipi: 'https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-2-leksika-i-frazeologija.pdf',
};
const UA = 'Eksamio-live-fipi-primary-correspondence/0.1 (+https://github.com/niknikdym-hue/ege)';

function sha256(value) {
  const bytes = Buffer.isBuffer(value) ? value : Buffer.from(value, 'utf8');
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function normalize(value) {
  return String(value)
    .normalize('NFKC')
    .replace(/\u00a0/g, ' ')
    .replace(/[–—−]/g, '-')
    .replace(/[«»„“”]/g, '"')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/[.;]+$/u, '')
    .toLocaleLowerCase('ru-RU');
}

function stripParenthetical(value) {
  let current = String(value);
  let previous;
  do {
    previous = current;
    current = current.replace(/\s*\([^()]*\)/gu, '');
  } while (current !== previous);
  return current.replace(/\s+/g, ' ').trim();
}

function dictionaryPrimary(value) {
  return stripParenthetical(value).split(',')[0].trim();
}

function phraseologyPrimary(value) {
  return stripParenthetical(value);
}

async function fetchBytes(url, accept) {
  const profiles = [
    {
      name: 'browser-compatible',
      headers: {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        accept,
        'accept-language': 'ru-RU,ru;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        pragma: 'no-cache',
        referer: 'https://eksamio.ru/trenazhery/russkiy/',
      },
    },
    { name: 'reconciliation-bot', headers: { 'user-agent': UA, accept } },
  ];
  const attempts = [];
  for (let round = 1; round <= 3; round += 1) {
    for (const profile of profiles) {
      try {
        const response = await fetch(url, { redirect: 'follow', headers: profile.headers });
        const bytes = Buffer.from(await response.arrayBuffer());
        attempts.push({ round, profile: profile.name, http_status: response.status, final_url: response.url, byte_count: bytes.length, sha256: sha256(bytes) });
        if (response.ok) return { bytes, attempts, selected_profile: profile.name, final_url: response.url, http_status: response.status };
      } catch (error) {
        attempts.push({ round, profile: profile.name, error: String(error?.message ?? error) });
      }
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    await new Promise((resolve) => setTimeout(resolve, 2500 * round));
  }
  throw new Error(`${url}: all read-only fetch attempts failed`);
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

function findArray(html, pattern, label) {
  const match = pattern.exec(html);
  if (!match) throw new Error(`${label} array not found`);
  const start = match.index + match[0].lastIndexOf('[');
  return extractBalanced(html, start, '[', ']');
}

function splitTopLevelObjects(arrayLiteral, label) {
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
    if (arrayLiteral[i] !== '{') throw new Error(`${label}: expected object at ${i}`);
    const row = extractBalanced(arrayLiteral, i, '{', '}');
    rows.push(row.text);
    i = row.end;
  }
  return rows;
}

function evaluateLiteral(literal) {
  return vm.runInNewContext(`(${literal})`, Object.create(null), { timeout: 750, microtaskMode: 'afterEvaluate' });
}

function pdfPageLines(pdfPath, page) {
  const proc = spawnSync('pdftotext', ['-f', String(page), '-l', String(page), '-layout', pdfPath, '-'], { encoding: 'utf8' });
  if (proc.status !== 0) throw new Error(`pdftotext page ${page} failed: ${proc.stderr}`);
  return proc.stdout.replace(/\u00a0/g, ' ').split(/\r?\n/).map((line) => line.trim().replace(/\s+/g, ' ')).filter(Boolean);
}

function span(lines, start, end) {
  const folded = lines.map(normalize);
  const s = folded.findIndex((line) => line.startsWith(normalize(start)));
  if (s < 0) throw new Error(`span start not found: ${start}`);
  const e = folded.findIndex((line, i) => i >= s && line.startsWith(normalize(end)));
  if (e < s) throw new Error(`span end not found: ${end}`);
  return lines.slice(s, e + 1);
}

function collectPdfValues(pdfPath, specs) {
  const out = [];
  for (const [page, start, end, expected] of specs) {
    const values = span(pdfPageLines(pdfPath, page), start, end);
    if (values.length !== expected) throw new Error(`page ${page}: expected ${expected}, got ${values.length}`);
    out.push(...values);
  }
  return out;
}

function comparePrimary(label, liveRaw, sourceRaw, liveIds, projector) {
  if (liveRaw.length !== sourceRaw.length) throw new Error(`${label}: count mismatch ${liveRaw.length} vs ${sourceRaw.length}`);
  const live = liveRaw.map(normalize);
  const projectedSourceRaw = sourceRaw.map(projector);
  const source = projectedSourceRaw.map(normalize);
  const mismatches = [];
  for (let i = 0; i < live.length; i += 1) {
    if (live[i] !== source[i]) {
      mismatches.push({
        index_1based: i + 1,
        live_id: liveIds[i],
        live: liveRaw[i],
        source_full_row: sourceRaw[i],
        source_primary_projection: projectedSourceRaw[i],
        live_normalized: live[i],
        source_primary_normalized: source[i],
      });
    }
  }
  return {
    rule: label === 'dictionary_words'
      ? 'same indexed FIPI row -> remove parenthetical segment(s) -> take first comma-separated form; no reordering/fuzzy matching'
      : 'same indexed FIPI row -> remove parenthetical alternative segment(s); no reordering/fuzzy matching',
    live_count: live.length,
    source_count: source.length,
    exact_primary_match_count: live.length - mismatches.length,
    exact_primary_mismatch_count: mismatches.length,
    status: mismatches.length === 0 ? 'EXACT_PRIMARY_ROW_CORRESPONDENCE' : 'PRIMARY_PROJECTION_MISMATCH_BLOCKER',
    live_ordered_sha256: sha256(live.join('\n')),
    source_primary_ordered_sha256: sha256(source.join('\n')),
    mismatch_sample: mismatches.slice(0, 30),
    admission_effect: 'NONE',
    canonical_binding_status: mismatches.length === 0
      ? 'TEXTUAL_PRIMARY_ROW_CORRESPONDENCE_PROVEN_SEMANTIC_ADMISSION_STILL_SEPARATE'
      : 'UNKNOWN_BLOCKER',
  };
}

const [dictionaryLive, phraseologyLive, orthographyFipi, lexiconFipi] = await Promise.all([
  fetchBytes(SOURCES.dictionary_live, 'text/html,application/xhtml+xml'),
  fetchBytes(SOURCES.phraseology_live, 'text/html,application/xhtml+xml'),
  fetchBytes(SOURCES.orthography_fipi, 'application/pdf,*/*'),
  fetchBytes(SOURCES.lexicon_fipi, 'application/pdf,*/*'),
]);

const dictionaryHtml = dictionaryLive.bytes.toString('utf8');
const wordsLiteral = findArray(dictionaryHtml, /(?:^|[;\n])\s*(?:const|let|var)\s+WORDS\s*=\s*\[/m, 'WORDS');
const words = evaluateLiteral(wordsLiteral.text);
if (!Array.isArray(words) || words.length !== 308) throw new Error(`WORDS expected 308, got ${words?.length}`);
const dictionaryRows = words.map((row, i) => {
  if (!row || typeof row !== 'object' || typeof row.word !== 'string' || typeof row.id !== 'string') throw new Error(`WORDS row ${i + 1} missing word/id`);
  return row;
});
if (new Set(dictionaryRows.map((row) => row.id)).size !== 308) throw new Error('WORDS ids are not unique');

const phraseologyHtml = phraseologyLive.bytes.toString('utf8');
const part1 = findArray(phraseologyHtml, /(?:window\.)?__EKSAMIO_PHRASEOLOGY_PART1\s*=\s*\[/m, 'phraseology PART1');
const part2 = findArray(phraseologyHtml, /\b(?:var|let|const)\s+PHRASES\s*=\s*\(\s*window\.__EKSAMIO_PHRASEOLOGY_PART1\s*\|\|\s*\[\s*\]\s*\)\s*\.concat\s*\(\s*\[/m, 'phraseology PART2');
const phraseRows = [...splitTopLevelObjects(part1.text, 'PART1'), ...splitTopLevelObjects(part2.text, 'PART2')].map(evaluateLiteral);
if (phraseRows.length !== 285) throw new Error(`PHRASES expected 285, got ${phraseRows.length}`);
if (!phraseRows.every((row) => row && typeof row === 'object' && typeof row.expression === 'string' && typeof row.id === 'string')) throw new Error('PHRASES rows missing expression/id');
if (new Set(phraseRows.map((row) => row.id)).size !== 285) throw new Error('PHRASES ids are not unique');

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'eksamio-primary-correspondence-'));
try {
  const orthographyPath = path.join(tmp, 'orthography.pdf');
  const lexiconPath = path.join(tmp, 'lexicon.pdf');
  fs.writeFileSync(orthographyPath, orthographyFipi.bytes);
  fs.writeFileSync(lexiconPath, lexiconFipi.bytes);

  const dictionarySource = collectPdfValues(orthographyPath, [
    [1, 'абитуриент', 'аттракцион', 18],
    [2, 'аукцион', 'декларация', 52],
    [3, 'декорация', 'колебание', 52],
    [4, 'коллектив', 'оборона', 52],
    [5, 'одолеть', 'рациональный', 52],
    [6, 'реалист', 'уничтожить', 52],
    [7, 'утрамбовать', 'эстакада', 30],
  ]);
  const phraseologySource = collectPdfValues(lexiconPath, [
    [6, 'альфа и омега', 'во весь рост', 44],
    [7, 'во всяком случае', 'души не чаять', 52],
    [8, 'душой и телом', 'между делом', 52],
    [9, 'между прочим', 'по белу свету', 52],
    [10, 'поднять на ноги', 'спать мёртвым сном', 52],
    [11, 'с первого взгляда', 'язык не повернулся', 33],
  ]);

  const result = {
    schema: 'eksamio.live-fipi-primary-correspondence.v0.1',
    authority: 'live eksamio.ru trainer rows + same-index official FIPI 2026 Navigator rows; read-only',
    authority_checked_at_runtime: new Date().toISOString(),
    scope: 'bounded textual/provenance candidate correspondence only; never semantic/mastery admission',
    exact_sources: {
      dictionary_live: { url: SOURCES.dictionary_live, byte_count: dictionaryLive.bytes.length, sha256: sha256(dictionaryLive.bytes), selected_profile: dictionaryLive.selected_profile },
      phraseology_live: { url: SOURCES.phraseology_live, byte_count: phraseologyLive.bytes.length, sha256: sha256(phraseologyLive.bytes), selected_profile: phraseologyLive.selected_profile },
      orthography_fipi: { url: SOURCES.orthography_fipi, byte_count: orthographyFipi.bytes.length, sha256: sha256(orthographyFipi.bytes) },
      lexicon_fipi: { url: SOURCES.lexicon_fipi, byte_count: lexiconFipi.bytes.length, sha256: sha256(lexiconFipi.bytes) },
    },
    dictionary_words: comparePrimary('dictionary_words', dictionaryRows.map((row) => row.word), dictionarySource, dictionaryRows.map((row) => row.id), dictionaryPrimary),
    phraseology: comparePrimary('phraseology', phraseRows.map((row) => row.expression), phraseologySource, phraseRows.map((row) => row.id), phraseologyPrimary),
    semantic_admissions: 0,
    object_closures: 0,
    mastery_admissions: 0,
    false_exact_mastery: 0,
    registered_user_identity_required_for_future_canonical_evidence: true,
    notes: [
      'Projection is deterministic and same-index only; no fuzzy matching, reordering, route/title inference, or semantic self-admission is permitted.',
      'A textual primary-row match can narrow provenance but cannot by itself create PEIS mastery.',
      'Any mismatch remains explicit and fail-closed.'
    ],
  };
  fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
  console.log(`wrote ${OUT}`);
  console.log(`dictionary=${result.dictionary_words.status} ${result.dictionary_words.exact_primary_match_count}/${result.dictionary_words.live_count}`);
  console.log(`phraseology=${result.phraseology.status} ${result.phraseology.exact_primary_match_count}/${result.phraseology.live_count}`);
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
