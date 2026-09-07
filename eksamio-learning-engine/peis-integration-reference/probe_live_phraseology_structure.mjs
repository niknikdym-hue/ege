import crypto from 'node:crypto';
import fs from 'node:fs';

const URL = 'https://eksamio.ru/trenazhery/russkiy/frazeologizmy/';
const OUT = process.env.PROBE_OUT || 'live-phraseology-structure-probe.json';

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

function collectDataAttributes(html) {
  const byName = new Map();
  const re = /\b(data-[A-Za-z0-9_-]+)\s*=\s*(["'])(.*?)\2/gms;
  let match;
  while ((match = re.exec(html)) !== null) {
    const name = match[1].toLowerCase();
    const value = match[3];
    if (!byName.has(name)) byName.set(name, []);
    byName.get(name).push(value);
  }
  return [...byName.entries()]
    .map(([name, values]) => ({
      name,
      count: values.length,
      unique_count: new Set(values).size,
      ordered_values_sha256: sha256(values.join('\n')),
    }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}

function collectSelectors(script) {
  const selectors = [];
  const re = /\.(querySelectorAll|querySelector)\(\s*(["'])(.*?)\2\s*\)/gms;
  let match;
  while ((match = re.exec(script)) !== null) {
    selectors.push({ method: match[1], selector: match[3] });
  }
  return selectors;
}

function collectElementIds(script) {
  const ids = [];
  const re = /getElementById\(\s*(["'])(.*?)\1\s*\)/gms;
  let match;
  while ((match = re.exec(script)) !== null) ids.push(match[2]);
  return ids;
}

function collectSplitLiteralShapes(script) {
  const rows = [];
  const re = /(["'`])([\s\S]{0,12000}?)\1\s*\.split\(\s*(["'`])([\s\S]{0,120}?)\3\s*\)/g;
  let match;
  while ((match = re.exec(script)) !== null) {
    const source = match[2];
    const separator = match[4];
    const pieces = separator ? source.split(separator) : [...source];
    rows.push({
      source_bytes_utf8: Buffer.byteLength(source, 'utf8'),
      source_sha256: sha256(source),
      separator,
      split_count: pieces.length,
      unique_piece_count: new Set(pieces).size,
      ordered_piece_sha256: sha256(pieces.join('\n')),
    });
  }
  return rows;
}

function collectTokenCounts(script) {
  const tokens = [
    'PHRASES', 'BY_ID', 'used', 'neutral', 'JSON.parse', 'JSON.stringify', '.split(', '.map(', '.forEach(', '.reduce(',
    'querySelectorAll', 'querySelector', 'getElementById', 'dataset', 'textContent', 'innerHTML', 'fetch(', 'atob(',
    'localStorage', 'sessionStorage', 'Object.keys', 'Object.values', 'Object.entries',
  ];
  const out = {};
  for (const token of tokens) out[token] = script.split(token).length - 1;
  return out;
}

function normalizedReferenceShapes(script, token) {
  const lines = script.split(/\r?\n/);
  const rows = [];
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line.includes(token)) continue;
    const normalized = line.replace(/\s+/g, ' ').trim();
    rows.push({
      line_number: index + 1,
      line_bytes_utf8: Buffer.byteLength(line, 'utf8'),
      line_sha256: sha256(line),
      normalized_shape: normalized
        .replace(/(["'])(?:(?!\1).|\\.)*\1/g, '<STRING>')
        .replace(/\b\d+(?:\.\d+)?\b/g, '<N>')
        .slice(0, 1200),
    });
  }
  return rows;
}

const { response, html, attempts, selected_profile } = await fetchHtml();
const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
  .map((match, index) => ({ index, attrs: match[1], text: match[2] }))
  .filter((entry) => entry.text.trim().length > 0);
const candidateScripts = scripts.filter((entry) => entry.text.includes('BY_ID'));
if (candidateScripts.length !== 1) {
  throw new Error(`expected exactly one inline BY_ID script, got ${candidateScripts.length}`);
}
const script = candidateScripts[0];

const result = {
  schema: 'eksamio.live-phraseology-structure-probe.v0.2',
  authority: 'live eksamio.ru phraseology trainer HTML; read-only GET',
  authority_checked_at_runtime: new Date().toISOString(),
  requested_url: URL,
  final_url: response.url,
  http_status: response.status,
  selected_profile,
  attempts,
  html_bytes_utf8: Buffer.byteLength(html, 'utf8'),
  html_sha256: sha256(html),
  inline_script_count: scripts.length,
  phraseology_script_index: script.index,
  phraseology_script_bytes_utf8: Buffer.byteLength(script.text, 'utf8'),
  phraseology_script_sha256: sha256(script.text),
  token_counts: collectTokenCounts(script.text),
  selectors: collectSelectors(script.text),
  element_ids: collectElementIds(script.text),
  split_literal_shapes: collectSplitLiteralShapes(script.text),
  phrases_reference_shapes: normalizedReferenceShapes(script.text, 'PHRASES'),
  by_id_mutation_shapes: normalizedReferenceShapes(script.text, 'BY_ID'),
  html_data_attribute_inventory: collectDataAttributes(html),
  canonical_item_identity_status: 'UNKNOWN_BLOCKER',
  admission_effect: 'NONE',
  semantic_admissions: 0,
  object_closures: 0,
  mastery_admissions: 0,
  false_exact_mastery: 0,
  registered_user_identity_required_for_future_canonical_evidence: true,
};

fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
console.log(`wrote ${OUT}`);
console.log(`phraseology html=${result.html_sha256} script=${result.phraseology_script_sha256}`);
console.log(`PHRASES occurrences=${result.token_counts.PHRASES}; BY_ID occurrences=${result.token_counts.BY_ID}`);
