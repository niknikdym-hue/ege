import crypto from 'node:crypto';
import fs from 'node:fs';

const URL = 'https://eksamio.ru/trenazhery/russkiy/frazeologizmy/';
const OUT = process.env.PROBE_OUT || 'phraseology-admission-authority-capture.json';
const EXPECTED_HTML_SHA256 = '69f69716dbad959b754354a0f3d1523dc4b05ae4732eeb234a68b3a43ebfe68b';
const EXPECTED_ORDERED_ID_SHA256 = '22b33854b09b4b212310169f48c69237d4a4c8ee1ed0b5aed95b50f9ec63b534';
const PART1 = '__EKSAMIO_PHRASEOLOGY_PART1';

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
        'user-agent': 'Eksamio-admission-authority-capture/0.1 (+https://github.com/niknikdym-hue/ege)',
        accept: 'text/html,application/xhtml+xml',
      },
    },
  ];
  const attempts = [];
  for (let round = 1; round <= 3; round += 1) {
    for (const profile of profiles) {
      const response = await fetch(URL, { redirect: 'follow', headers: profile.headers });
      const html = await response.text();
      attempts.push({ round, profile: profile.name, http_status: response.status, final_url: response.url, html_bytes_utf8: Buffer.byteLength(html, 'utf8'), html_sha256: sha256(html) });
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

function extractSafeId(objectLiteral, rowIndex) {
  const matches = [...objectLiteral.matchAll(/(?:^|[{,]\s*)(?:id|["']id["'])\s*:\s*(["'])([A-Za-z0-9._:-]+)\1/gm)];
  if (matches.length !== 1) throw new Error(`row ${rowIndex} must have exactly one simple explicit id; got ${matches.length}`);
  return matches[0][2];
}

function extractTopLevelKeyCandidates(objectLiteral) {
  const keys = [];
  for (const match of objectLiteral.matchAll(/(?:^|[{,]\s*)([A-Za-z_$][A-Za-z0-9_$]*|["'][^"']+["'])\s*:/gm)) {
    keys.push(match[1].replace(/^['"]|['"]$/g, ''));
  }
  return [...new Set(keys)].sort();
}

function locatePart1Array(html) {
  const re = new RegExp(`(?:window\\.)?${PART1}\\s*=\\s*\\[`, 'm');
  const match = re.exec(html);
  if (!match) throw new Error(`${PART1} array assignment not found`);
  const start = match.index + match[0].lastIndexOf('[');
  return extractBalanced(html, start, '[', ']');
}

function locatePart2Array(script) {
  const declaration = /\b(?:var|let|const)\s+PHRASES\s*=\s*\(\s*window\.__EKSAMIO_PHRASEOLOGY_PART1\s*\|\|\s*\[\s*\]\s*\)\s*\.concat\s*\(\s*\[/m.exec(script);
  if (!declaration) throw new Error('split PHRASES concat declaration not found');
  const start = declaration.index + declaration[0].lastIndexOf('[');
  return extractBalanced(script, start, '[', ']');
}

const { response, html, attempts, selected_profile } = await fetchHtml();
const htmlHash = sha256(html);
if (htmlHash !== EXPECTED_HTML_SHA256) throw new Error(`live phraseology HTML drift: ${htmlHash}`);

const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
  .map((match, index) => ({ index, attrs: match[1], text: match[2] }))
  .filter((entry) => entry.text.trim().length > 0);
const candidateScripts = scripts.filter((entry) => entry.text.includes('BY_ID') && entry.text.includes('PHRASES'));
if (candidateScripts.length !== 1) throw new Error(`expected exactly one inline PHRASES/BY_ID script, got ${candidateScripts.length}`);
const script = candidateScripts[0];

const part1Array = locatePart1Array(html);
const part2Array = locatePart2Array(script.text);
const part1Rows = splitTopLevelObjects(part1Array.text, 'PART1');
const part2Rows = splitTopLevelObjects(part2Array.text, 'PART2');
const rowLiterals = [...part1Rows, ...part2Rows];
const ids = rowLiterals.map((row, index) => extractSafeId(row, index));
if (rowLiterals.length !== 285 || new Set(ids).size !== 285) throw new Error(`expected exact 285 unique phraseology rows, got ${rowLiterals.length}/${new Set(ids).size}`);
const orderedIdHash = sha256(ids.join('\n'));
if (orderedIdHash !== EXPECTED_ORDERED_ID_SHA256) throw new Error(`ordered phraseology IDs drift: ${orderedIdHash}`);

const result = {
  schema: 'eksamio.phraseology-admission-authority-capture.v0.1',
  authority: 'live eksamio.ru phraseology trainer HTML; read-only capture only; no admission effect',
  source_pr_187_head: 'c5592c212557b91578ed48e1bf778e30dd489dc7',
  requested_url: URL,
  final_url: response.url,
  http_status: response.status,
  selected_profile,
  attempts,
  html_bytes_utf8: Buffer.byteLength(html, 'utf8'),
  html_sha256: htmlHash,
  phraseology_script_sha256: sha256(script.text),
  part1_row_count: part1Rows.length,
  part2_row_count: part2Rows.length,
  row_count: rowLiterals.length,
  unique_id_count: new Set(ids).size,
  ordered_id_sha256: orderedIdHash,
  rows: rowLiterals.map((literal, index) => ({
    index_1based: index + 1,
    id: ids[index],
    literal_sha256: sha256(literal),
    top_level_key_candidates: extractTopLevelKeyCandidates(literal),
    literal,
  })),
  admission_effect: 'NONE_CAPTURE_ONLY',
  semantic_admissions: 0,
  mastery_admissions: 0,
  false_exact_mastery: 0,
};

fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
console.log(`wrote ${OUT}`);
console.log(`rows=${result.row_count} ids=${result.unique_id_count} hash=${result.ordered_id_sha256}`);
console.log(`first_keys=${result.rows[0].top_level_key_candidates.join(',')}`);
