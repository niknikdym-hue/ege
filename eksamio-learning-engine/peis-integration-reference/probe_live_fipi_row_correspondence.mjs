import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { spawnSync } from 'node:child_process';

const OUT = process.env.PROBE_OUT || 'live-fipi-row-correspondence.json';
const DICT_URL = 'https://eksamio.ru/trenazhery/russkiy/slovarnye-slova/';
const PHRASE_URL = 'https://eksamio.ru/trenazhery/russkiy/frazeologizmy/';
const ORTHOGRAPHY_PDF = 'https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-5-orfografija.pdf';
const LEXICON_PDF = 'https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-2-leksika-i-frazeologija.pdf';
const UA = 'Eksamio-live-fipi-row-correspondence/0.1 (+https://github.com/niknikdym-hue/ege)';

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
    if (arrayLiteral[i] !== '{') throw new Error(`${label} contains non-object top-level value at ${i}`);
    const object = extractBalanced(arrayLiteral, i, '{', '}');
    rows.push(object.text);
    i = object.end;
  }
  return rows;
}

function evaluateLiteral(literal) {
  return vm.runInNewContext(`(${literal})`, Object.create(null), { timeout: 750, microtaskMode: 'afterEvaluate' });
}

async function fetchWithRetry(url, accept) {
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
        if (response.ok) return { bytes, response, attempts, selected_profile: profile.name };
      } catch (error) {
        attempts.push({ round, profile: profile.name, error: String(error?.message ?? error) });
      }
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    await new Promise((resolve) => setTimeout(resolve, 2500 * round));
  }
  throw new Error(`${url}: all read-only fetch attempts failed`);
}

function findNamedArray(html, variable) {
  const re = new RegExp(`(?:^|[;\\n])\\s*(?:const|let|var)\\s+${variable}\\s*=\\s*\\[`, 'm');
  const match = re.exec(html);
  if (!match) throw new Error(`${variable} array assignment not found`);
  const start = match.index + match[0].lastIndexOf('[');
  return extractBalanced(html, start, '[', ']');
}

function locatePhraseologyArrays(html) {
  const firstRe = /(?:window\.)?__EKSAMIO_PHRASEOLOGY_PART1\s*=\s*\[/m;
  const first = firstRe.exec(html);
  if (!first) throw new Error('phraseology PART1 array not found');
  const firstStart = first.index + first[0].lastIndexOf('[');
  const part1 = extractBalanced(html, firstStart, '[', ']');

  const secondRe = /\b(?:var|let|const)\s+PHRASES\s*=\s*\(\s*window\.__EKSAMIO_PHRASEOLOGY_PART1\s*\|\|\s*\[\s*\]\s*\)\s*\.concat\s*\(\s*\[/m;
  const second = secondRe.exec(html);
  if (!second) throw new Error('phraseology PHRASES.concat array not found');
  const secondStart = second.index + second[0].lastIndexOf('[');
  const part2 = extractBalanced(html, secondStart, '[', ']');
  return { part1, part2 };
}

function pdftotextPage(pdfPath, page) {
  const proc = spawnSync('pdftotext', ['-f', String(page), '-l', String(page), '-layout', pdfPath, '-'], { encoding: 'utf8' });
  if (proc.status !== 0) throw new Error(`pdftotext page ${page} failed: ${proc.stderr}`);
  return proc.stdout.replace(/\u00a0/g, ' ').split(/\r?\n/).map((line) => line.trim().replace(/\s+/g, ' ')).filter(Boolean);
}

function span(lines, start, end) {
  const folded = lines.map((line) => normalize(line));
  const s = folded.findIndex((line) => line.startsWith(normalize(start)));
  if (s < 0) throw new Error(`span start not found: ${start}`);
  const e = folded.findIndex((line, i) => i >= s && line.startsWith(normalize(end)));
  if (e < s) throw new Error(`span end not found: ${end}`);
  return lines.slice(s, e + 1);
}

function collectPdfValues(pdfPath, specs) {
  const values = [];
  for (const [page, start, end, expected] of specs) {
    const pageValues = span(pdftotextPage(pdfPath, page), start, end);
    if (pageValues.length !== expected) throw new Error(`page ${page} ${start}..${end}: expected ${expected}, got ${pageValues.length}`);
    values.push(...pageValues);
  }
  return values;
}

function compareSequences(label, liveRaw, sourceRaw, liveIds) {
  if (liveRaw.length !== sourceRaw.length) throw new Error(`${label}: count mismatch ${liveRaw.length} vs ${sourceRaw.length}`);
  const live = liveRaw.map(normalize);
  const source = sourceRaw.map(normalize);
  const mismatches = [];
  for (let i = 0; i < live.length; i += 1) {
    if (live[i] !== source[i]) {
      mismatches.push({ index_1based: i + 1, live_id: liveIds?.[i] ?? null, live: liveRaw[i], source: sourceRaw[i], live_normalized: live[i], source_normalized: source[i] });
    }
  }
  const liveSet = new Set(live);
  const sourceSet = new Set(source);
  const liveOnly = [...liveSet].filter((v) => !sourceSet.has(v));
  const sourceOnly = [...sourceSet].filter((v) => !liveSet.has(v));
  return {
    live_count: live.length,
    source_count: source.length,
    exact_index_match_count: live.length - mismatches.length,
    exact_index_mismatch_count: mismatches.length,
    exact_index_status: mismatches.length === 0 ? 'EXACT_ROW_BY_ROW' : 'MISMATCH_BLOCKER',
    set_status: liveOnly.length === 0 && sourceOnly.length === 0 ? 'EXACT_NORMALIZED_SET' : 'SET_MISMATCH_BLOCKER',
    live_ordered_normalized_sha256: sha256(live.join('\n')),
    source_ordered_normalized_sha256: sha256(source.join('\n')),
    live_sorted_normalized_sha256: sha256([...live].sort().join('\n')),
    source_sorted_normalized_sha256: sha256([...source].sort().join('\n')),
    mismatch_sample: mismatches.slice(0, 20),
    live_only_sample: liveOnly.slice(0, 20),
    source_only_sample: sourceOnly.slice(0, 20),
    admission_effect: 'NONE',
    canonical_binding_status: mismatches.length === 0 ? 'ROW_TEXT_CORRESPONDENCE_PROVEN_BUT_SEMANTIC_ADMISSION_STILL_SEPARATE' : 'UNKNOWN_BLOCKER',
  };
}

const [dictLiveFetch, phraseLiveFetch, orthoPdfFetch, lexiconPdfFetch] = await Promise.all([
  fetchWithRetry(DICT_URL, 'text/html,application/xhtml+xml'),
  fetchWithRetry(PHRASE_URL, 'text/html,application/xhtml+xml'),
  fetchWithRetry(ORTHOGRAPHY_PDF, 'application/pdf,*/*'),
  fetchWithRetry(LEXICON_PDF, 'application/pdf,*/*'),
]);

const dictHtml = dictLiveFetch.bytes.toString('utf8');
const dictArray = findNamedArray(dictHtml, 'WORDS');
const dictRows = evaluateLiteral(dictArray.text);
if (!Array.isArray(dictRows) || dictRows.length !== 308) throw new Error(`WORDS expected 308 rows, got ${dictRows?.length}`);
const dictWords = dictRows.map((row, i) => {
  if (!row || typeof row !== 'object' || typeof row.word !== 'string' || typeof row.id !== 'string') throw new Error(`WORDS row ${i + 1} missing word/id`);
  return row.word;
});
const dictIds = dictRows.map((row) => row.id);
if (new Set(dictIds).size !== 308) throw new Error('WORDS ids must be unique');

const phraseHtml = phraseLiveFetch.bytes.toString('utf8');
const { part1, part2 } = locatePhraseologyArrays(phraseHtml);
const phraseRowLiterals = [...splitTopLevelObjects(part1.text, 'PART1'), ...splitTopLevelObjects(part2.text, 'PART2')];
if (phraseRowLiterals.length !== 285) throw new Error(`PHRASES expected 285 rows, got ${phraseRowLiterals.length}`);
const phraseRows = phraseRowLiterals.map(evaluateLiteral);
const phraseExpressions = phraseRows.map((row, i) => {
  if (!row || typeof row !== 'object' || typeof row.expression !== 'string' || typeof row.id !== 'string') throw new Error(`PHRASES row ${i + 1} missing expression/id`);
  return row.expression;
});
const phraseIds = phraseRows.map((row) => row.id);
if (new Set(phraseIds).size !== 285) throw new Error('PHRASES ids must be unique');

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'eksamio-live-fipi-'));
try {
  const orthographyPath = path.join(tmp, 'orthography.pdf');
  const lexiconPath = path.join(tmp, 'lexicon.pdf');
  fs.writeFileSync(orthographyPath, orthoPdfFetch.bytes);
  fs.writeFileSync(lexiconPath, lexiconPdfFetch.bytes);

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
    schema: 'eksamio.live-fipi-row-correspondence-probe.v0.1',
    authority: 'live eksamio.ru trainer HTML + official FIPI 2026 Navigator PDFs; read-only fetch',
    authority_checked_at_runtime: new Date().toISOString(),
    normalization: 'NFKC + NBSP->space + dash/quote normalization + whitespace collapse + terminal .; removal + ru-RU lowercase',
    exact_sources: {
      live_dictionary_words: { url: DICT_URL, byte_count: dictLiveFetch.bytes.length, sha256: sha256(dictLiveFetch.bytes), selected_profile: dictLiveFetch.selected_profile },
      live_phraseology: { url: PHRASE_URL, byte_count: phraseLiveFetch.bytes.length, sha256: sha256(phraseLiveFetch.bytes), selected_profile: phraseLiveFetch.selected_profile },
      fipi_orthography_2026: { url: ORTHOGRAPHY_PDF, byte_count: orthoPdfFetch.bytes.length, sha256: sha256(orthoPdfFetch.bytes) },
      fipi_lexicon_phraseology_2026: { url: LEXICON_PDF, byte_count: lexiconPdfFetch.bytes.length, sha256: sha256(lexiconPdfFetch.bytes) },
    },
    dictionary_words: compareSequences('dictionary_words', dictWords, dictionarySource, dictIds),
    phraseology: compareSequences('phraseology', phraseExpressions, phraseologySource, phraseIds),
    semantic_admissions: 0,
    object_closures: 0,
    mastery_admissions: 0,
    false_exact_mastery: 0,
    registered_user_identity_required_for_future_canonical_evidence: true,
    notes: [
      'This probe may prove textual row correspondence only; it never self-admits PEIS semantic ownership or mastery.',
      'Any mismatch remains an explicit blocker and is reported with bounded samples.',
      'Anonymous/device-only learner state is never canonical.'
    ],
  };
  fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
  console.log(`wrote ${OUT}`);
  console.log(`dictionary: ${result.dictionary_words.exact_index_status} ${result.dictionary_words.exact_index_match_count}/${result.dictionary_words.live_count}`);
  console.log(`phraseology: ${result.phraseology.exact_index_status} ${result.phraseology.exact_index_match_count}/${result.phraseology.live_count}`);
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
