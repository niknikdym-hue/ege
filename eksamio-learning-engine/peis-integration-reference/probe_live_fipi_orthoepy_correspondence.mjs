import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { execFileSync } from 'node:child_process';

const OUT = process.env.PROBE_OUT || 'live-fipi-orthoepy-correspondence-probe.json';
const LIVE_URL = 'https://eksamio.ru/trenazhery/russkiy/orfoepiya/';
const FIPI_URL = 'https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-1-fonetika.pdf';
const EXPECTED_LIVE_COUNT = 291;
const VOWELS = new Set([...('аеёиоуыэюяАЕЁИОУЫЭЮЯ')]);

function sha256(value) {
  const data = typeof value === 'string' ? value : Buffer.from(value);
  return crypto.createHash('sha256').update(data).digest('hex');
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
  return vm.runInNewContext(`(${literal})`, Object.create(null), { timeout: 500, microtaskMode: 'afterEvaluate' });
}

async function fetchWithProfiles(url, accept) {
  const profiles = [
    {
      name: 'browser-compatible',
      headers: {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        accept,
        'accept-language': 'ru-RU,ru;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        pragma: 'no-cache',
      },
    },
    {
      name: 'reconciliation-bot',
      headers: {
        'user-agent': 'Eksamio-live-asset-reconciliation/0.1 (+https://github.com/niknikdym-hue/ege)',
        accept,
      },
    },
  ];
  const attempts = [];
  for (let round = 1; round <= 3; round += 1) {
    for (const profile of profiles) {
      try {
        const response = await fetch(url, { redirect: 'follow', headers: profile.headers });
        const body = Buffer.from(await response.arrayBuffer());
        attempts.push({
          round,
          profile: profile.name,
          http_status: response.status,
          final_url: response.url,
          byte_count: body.length,
          sha256: sha256(body),
        });
        if (response.ok) return { response, body, attempts, selected_profile: profile.name };
      } catch (error) {
        attempts.push({ round, profile: profile.name, error: String(error?.message ?? error) });
      }
      await new Promise((resolve) => setTimeout(resolve, 1200));
    }
    await new Promise((resolve) => setTimeout(resolve, 3000 * round));
  }
  throw new Error(`${url}: all read-only profiles failed`);
}

function renderStress(row) {
  const word = String(row.p);
  const index = Number(row.s);
  if (!Number.isInteger(index) || index < 0 || index >= word.length) throw new Error(`invalid stress index for ${row.i}`);
  const ch = word[index];
  if (!VOWELS.has(ch)) throw new Error(`stress index is not a vowel for ${row.i}: ${word} @ ${index}`);
  return `${word.slice(0, index)}${ch.toLocaleUpperCase('ru-RU')}${word.slice(index + 1)}`;
}

const liveFetch = await fetchWithProfiles(LIVE_URL, 'text/html,application/xhtml+xml');
const liveHtml = liveFetch.body.toString('utf8');
const scriptMatches = [...liveHtml.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];
const assignments = scriptMatches
  .map((match, index) => ({ index, text: match[2] }))
  .filter((item) => item.text.trim())
  .flatMap((script) => findAssignments(script.text).map((assignment) => ({ ...assignment, script_index: script.index })));
const rawMatches = assignments.filter((assignment) => assignment.name === 'RAW');
if (rawMatches.length !== 1) throw new Error(`RAW: expected exactly one assignment, got ${rawMatches.length}`);
const raw = evaluateLiteral(rawMatches[0].literal);
if (!Array.isArray(raw) || raw.length !== EXPECTED_LIVE_COUNT) throw new Error(`RAW count drift: ${raw?.length}`);
const renderedLive = raw.map((row) => ({ id: String(row.i), word: String(row.p), stress_index: Number(row.s), stressed: renderStress(row) }));

const fipiFetch = await fetchWithProfiles(FIPI_URL, 'application/pdf,*/*');
if (!fipiFetch.body.subarray(0, 5).equals(Buffer.from('%PDF-'))) throw new Error('FIPI source is not PDF bytes');
const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'eksamio-orthoepy-'));
const pdfPath = path.join(tmpRoot, 'ru-1-fonetika.pdf');
fs.writeFileSync(pdfPath, fipiFetch.body);
const pdfText = execFileSync('pdftotext', ['-layout', pdfPath, '-'], { encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 }).replace(/\u00a0/g, ' ');
const normalizedPdf = pdfText.replace(/\r\n?/g, '\n');
const start = normalizedPdf.indexOf('Имена существительные');
const end = normalizedPdf.indexOf('Обратите внимание!', start);
if (start < 0 || end < 0 || end <= start) throw new Error('could not bound official orthoepic list span');
const listSpan = normalizedPdf.slice(start, end);

const tokenMatches = listSpan.match(/[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)*/g) ?? [];
const sourceStressTokens = tokenMatches.filter((token) => [...token].some((ch) => VOWELS.has(ch) && ch === ch.toLocaleUpperCase('ru-RU') && ch !== ch.toLocaleLowerCase('ru-RU')));
const sourceTokenSet = new Set(sourceStressTokens);
const exactMatches = renderedLive.filter((row) => sourceTokenSet.has(row.stressed));
const missing = renderedLive.filter((row) => !sourceTokenSet.has(row.stressed));

const output = {
  schema: 'eksamio.live-fipi-orthoepy-correspondence-probe.v0.1',
  authority: {
    live: 'live eksamio.ru public orthoepy trainer HTML; read-only GET',
    source: 'official FIPI 2026 Navigator PDF ru-1-fonetika.pdf; read-only GET',
  },
  live: {
    url: LIVE_URL,
    html_byte_count: liveFetch.body.length,
    html_sha256: sha256(liveFetch.body),
    raw_literal_sha256: sha256(rawMatches[0].literal),
    row_count: raw.length,
    unique_id_count: new Set(renderedLive.map((row) => row.id)).size,
    ordered_stressed_sha256: sha256(renderedLive.map((row) => row.stressed).join('\n')),
  },
  fipi: {
    url: FIPI_URL,
    pdf_byte_count: fipiFetch.body.length,
    pdf_sha256: sha256(fipiFetch.body),
    bounded_list_span_sha256: sha256(listSpan),
    extracted_stress_token_occurrences: sourceStressTokens.length,
    extracted_unique_stress_tokens: sourceTokenSet.size,
  },
  correspondence: {
    exact_live_stressed_token_match_count: exactMatches.length,
    exact_live_stressed_token_mismatch_count: missing.length,
    exact_match_ids_sha256: sha256(exactMatches.map((row) => row.id).join('\n')),
    mismatches: missing,
  },
  admission_boundary: {
    forensic_provenance_probe_only: true,
    semantic_admissions: 0,
    object_closures: 0,
    mastery_admissions: 0,
    false_exact_mastery: 0,
    normative_pronunciation_evidence_status: 'MISSING_BLOCKER',
    stress_correspondence_alone_can_close_pronunciation_component: false,
    registered_user_identity_ref_required_for_future_canonical_evidence: true,
  },
};
fs.writeFileSync(OUT, `${JSON.stringify(output, null, 2)}\n`, 'utf8');
console.log(`LIVE_FIPI_ORTHOEPY_CORRESPONDENCE_PROBE=PASS exact=${exactMatches.length}/${renderedLive.length} mismatches=${missing.length}`);
console.log(`live_html_sha256=${output.live.html_sha256}`);
console.log(`fipi_pdf_sha256=${output.fipi.pdf_sha256}`);
console.log('semantic_admissions=0 object_closures=0 mastery_admissions=0 false_exact_mastery=0');
