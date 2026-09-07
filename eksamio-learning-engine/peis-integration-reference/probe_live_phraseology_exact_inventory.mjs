import crypto from 'node:crypto';
import fs from 'node:fs';

const URL = 'https://eksamio.ru/trenazhery/russkiy/frazeologizmy/';
const OUT = process.env.PROBE_OUT || 'live-phraseology-exact-inventory.json';

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
    if (source[i] === '\\') {
      i += 2;
      continue;
    }
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
    if (ch === '"' || ch === "'" || ch === '`') {
      i = skipString(source, i);
      continue;
    }
    if (ch === '/' && source[i + 1] === '/') {
      i = skipLineComment(source, i);
      continue;
    }
    if (ch === '/' && source[i + 1] === '*') {
      i = skipBlockComment(source, i);
      continue;
    }
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
      if (/\s|,/.test(ch)) {
        i += 1;
        continue;
      }
      if (ch === '/' && arrayLiteral[i + 1] === '/') {
        i = skipLineComment(arrayLiteral, i);
        continue;
      }
      if (ch === '/' && arrayLiteral[i + 1] === '*') {
        i = skipBlockComment(arrayLiteral, i);
        continue;
      }
      break;
    }
    if (i >= end) break;
    if (arrayLiteral[i] !== '{') throw new Error(`PHRASES contains non-object top-level value at ${i}`);
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

const { response, html, attempts, selected_profile } = await fetchHtml();
const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
  .map((match, index) => ({ index, attrs: match[1], text: match[2] }))
  .filter((entry) => entry.text.trim().length > 0);
const candidateScripts = scripts.filter((entry) => entry.text.includes('BY_ID') && entry.text.includes('PHRASES'));
if (candidateScripts.length !== 1) throw new Error(`expected exactly one inline PHRASES/BY_ID script, got ${candidateScripts.length}`);
const script = candidateScripts[0];

const declaration = /\b(?:var|let|const)\s+PHRASES\s*=\s*\[/m.exec(script.text);
if (!declaration) throw new Error('PHRASES array declaration not found');
const arrayStart = declaration.index + declaration[0].lastIndexOf('[');
const array = extractBalanced(script.text, arrayStart, '[', ']');
const rows = splitTopLevelObjects(array.text);
if (rows.length === 0) throw new Error('PHRASES array is empty');
const ids = rows.map((row, index) => extractSafeId(row, index));
const uniqueIds = new Set(ids);
if (uniqueIds.size !== ids.length) throw new Error(`PHRASES ids are not unique: ${ids.length} rows / ${uniqueIds.size} unique ids`);

const orderedRowFingerprints = rows.map((row) => sha256(row));
const result = {
  schema: 'eksamio.live-phraseology-exact-inventory.v0.1',
  authority: 'live eksamio.ru phraseology trainer HTML; read-only GET',
  authority_checked_at_runtime: new Date().toISOString(),
  requested_url: URL,
  final_url: response.url,
  http_status: response.status,
  selected_profile,
  attempts,
  html_bytes_utf8: Buffer.byteLength(html, 'utf8'),
  html_sha256: sha256(html),
  phraseology_script_index: script.index,
  phraseology_script_bytes_utf8: Buffer.byteLength(script.text, 'utf8'),
  phraseology_script_sha256: sha256(script.text),
  phrases_array_bytes_utf8: Buffer.byteLength(array.text, 'utf8'),
  phrases_array_sha256: sha256(array.text),
  live_row_count: rows.length,
  explicit_id_count: ids.length,
  unique_explicit_id_count: uniqueIds.size,
  ordered_id_sha256: sha256(ids.join('\n')),
  sorted_id_sha256: sha256([...ids].sort().join('\n')),
  first_id: ids[0],
  last_id: ids.at(-1),
  ordered_row_fingerprint_sha256: sha256(orderedRowFingerprints.join('\n')),
  live_item_identity_discovery_status: 'COMPLETE_EXPLICIT_UNIQUE_ID_CANDIDATES',
  canonical_item_identity_status: 'UNKNOWN_BLOCKER',
  provenance_binding_status: 'UNKNOWN_BLOCKER',
  admission_effect: 'NONE',
  semantic_admissions: 0,
  object_closures: 0,
  mastery_admissions: 0,
  false_exact_mastery: 0,
  registered_user_identity_required_for_future_canonical_evidence: true,
};

fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
console.log(`wrote ${OUT}`);
console.log(`phraseology rows=${result.live_row_count} ids=${result.unique_explicit_id_count}/${result.explicit_id_count}`);
console.log(`PHRASES=${result.phrases_array_sha256} ids=${result.ordered_id_sha256}`);
