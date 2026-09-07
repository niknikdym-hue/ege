import crypto from 'node:crypto';
import fs from 'node:fs';
import vm from 'node:vm';

const pages = {
  orthoepy: 'https://eksamio.ru/trenazhery/russkiy/orfoepiya/',
  dictionary_words: 'https://eksamio.ru/trenazhery/russkiy/slovarnye-slova/',
  paronyms: 'https://eksamio.ru/trenazhery/russkiy/paronimy/',
  phraseology: 'https://eksamio.ru/trenazhery/russkiy/frazeologizmy/',
};

function sha256(text) {
  return crypto.createHash('sha256').update(text, 'utf8').digest('hex');
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
    else if (ch === close) {
      depth -= 1;
      if (depth === 0) return source.slice(start, i + 1);
    }
  }
  return null;
}

function findLiteralAssignments(script) {
  const assignments = [];
  const re = /(?:^|[;\n])\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*/g;
  let match;
  while ((match = re.exec(script)) !== null) {
    const name = match[1];
    let start = re.lastIndex;
    while (/\s/.test(script[start] ?? '')) start += 1;
    if (!['[', '{'].includes(script[start])) continue;
    const literal = extractBalanced(script, start);
    if (!literal) continue;
    assignments.push({ name, literal });
    re.lastIndex = start + literal.length;
  }
  return assignments;
}

function extractQuotedLiteral(source, start) {
  const quote = source[start];
  if (!['"', "'", '`'].includes(quote)) return null;
  let escaped = false;
  for (let i = start + 1; i < source.length; i += 1) {
    const ch = source[i];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (ch === '\\') {
      escaped = true;
      continue;
    }
    if (ch === quote) return source.slice(start, i + 1);
  }
  return null;
}

function findStringAssignments(script) {
  const assignments = [];
  const re = /(?:^|[;\n])\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*/g;
  let match;
  while ((match = re.exec(script)) !== null) {
    const name = match[1];
    let start = re.lastIndex;
    while (/\s/.test(script[start] ?? '')) start += 1;
    if (!['"', "'", '`'].includes(script[start])) continue;
    const literal = extractQuotedLiteral(script, start);
    if (!literal) continue;
    const tail = script.slice(start + literal.length, start + literal.length + 80).replace(/\s+/g, ' ').trim();
    assignments.push({ name, literal, tail });
    re.lastIndex = start + literal.length;
  }
  return assignments;
}

function commonKeys(rows) {
  if (!rows.length) return [];
  const counts = new Map();
  for (const row of rows) {
    for (const key of Object.keys(row)) counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return [...counts.entries()]
    .filter(([, count]) => count === rows.length)
    .map(([key]) => key)
    .sort();
}

function summarizeArrays(root, maxDepth = 6) {
  const seen = new Set();
  const arrays = [];
  function walk(value, path, depth) {
    if (depth > maxDepth || value === null || typeof value !== 'object') return;
    if (seen.has(value)) return;
    seen.add(value);
    if (Array.isArray(value)) {
      const objectRows = value.filter((row) => row && typeof row === 'object' && !Array.isArray(row));
      const rowCount = value.length;
      const summary = {
        path,
        length: rowCount,
        object_rows: objectRows.length,
      };
      if (objectRows.length === rowCount && rowCount > 0) {
        summary.common_keys = commonKeys(objectRows);
        summary.scalar_unique = {};
        for (const key of summary.common_keys) {
          const vals = objectRows.map((row) => row[key]);
          if (vals.every((v) => ['string', 'number', 'boolean'].includes(typeof v))) {
            summary.scalar_unique[key] = new Set(vals.map(String)).size;
          }
        }
        for (const key of ['id', 'item_id', 'word', 'phrase', 'term', 'text', 'answer']) {
          const vals = objectRows.map((row) => row[key]).filter((v) => typeof v === 'string' || typeof v === 'number');
          if (vals.length === rowCount) {
            summary[`${key}_unique`] = new Set(vals.map(String)).size;
            if ((key === 'id' || key === 'item_id') && rowCount <= 1000) {
              const ids = vals.map(String);
              summary.identity_values = ids;
              summary.identity_values_sha256 = sha256(ids.join('\n'));
            }
          }
        }
      }
      arrays.push(summary);
      value.forEach((item, index) => walk(item, `${path}[${index}]`, depth + 1));
      return;
    }
    for (const [key, child] of Object.entries(value)) walk(child, `${path}.${key}`, depth + 1);
  }
  walk(root, 'root', 0);
  return arrays
    .filter((x) => x.length >= 2)
    .sort((a, b) => b.length - a.length || a.path.localeCompare(b.path))
    .slice(0, 20);
}

function safeEvaluateLiteral(literal) {
  const sandbox = Object.create(null);
  return vm.runInNewContext(`(${literal})`, sandbox, { timeout: 250, microtaskMode: 'afterEvaluate' });
}

async function inspectPage(key, url) {
  const profiles = [
    {
      name: 'reconciliation-bot',
      headers: {
        'user-agent': 'Eksamio-live-asset-reconciliation/0.1 (+https://github.com/niknikdym-hue/ege)',
        'accept': 'text/html,application/xhtml+xml',
      },
    },
    {
      name: 'browser-compatible',
      headers: {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'accept-language': 'ru-RU,ru;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'upgrade-insecure-requests': '1',
      },
    },
  ];

  const attempts = [];
  let response = null;
  let html = null;
  let selectedProfile = null;
  for (const profile of profiles) {
    const candidate = await fetch(url, { redirect: 'follow', headers: profile.headers });
    const body = await candidate.text();
    attempts.push({
      profile: profile.name,
      http_status: candidate.status,
      final_url: candidate.url,
      content_type: candidate.headers.get('content-type'),
      body_bytes_utf8: Buffer.byteLength(body, 'utf8'),
      body_sha256: sha256(body),
    });
    if (candidate.ok) {
      response = candidate;
      html = body;
      selectedProfile = profile.name;
      break;
    }
  }

  if (!response || html === null) {
    return {
      key,
      requested_url: url,
      probe_status: 'FAIL_CLOSED_HTTP_BLOCKED',
      attempts,
      admission_effect: 'NONE',
    };
  }

  const scriptMatches = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];
  const inlineScripts = scriptMatches
    .map((m, index) => ({ index, attrs: m[1], text: m[2] }))
    .filter((s) => s.text.trim().length > 0);

  const assignments = [];
  for (const script of inlineScripts) {
    for (const candidate of findLiteralAssignments(script.text)) {
      let evaluation = { status: 'NOT_EVALUATED' };
      try {
        const value = safeEvaluateLiteral(candidate.literal);
        evaluation = {
          status: 'EVALUATED_LITERAL',
          root_type: Array.isArray(value) ? 'array' : typeof value,
          root_keys: value && typeof value === 'object' && !Array.isArray(value) ? Object.keys(value).sort() : [],
          arrays: summarizeArrays(value),
        };
      } catch (error) {
        evaluation = {
          status: 'LITERAL_EVALUATION_FAILED',
          error: String(error?.message ?? error).slice(0, 240),
        };
      }
      assignments.push({
        script_index: script.index,
        variable: candidate.name,
        literal_bytes_utf8: Buffer.byteLength(candidate.literal, 'utf8'),
        literal_sha256: sha256(candidate.literal),
        ...evaluation,
      });
    }
  }

  const stringAssignments = [];
  for (const script of inlineScripts) {
    for (const candidate of findStringAssignments(script.text)) {
      let decoded = null;
      let status = 'STRING_LITERAL_NOT_EVALUATED';
      try {
        decoded = safeEvaluateLiteral(candidate.literal);
        status = typeof decoded === 'string' ? 'EVALUATED_STRING_LITERAL' : 'NON_STRING_RESULT';
      } catch (error) {
        status = 'STRING_LITERAL_EVALUATION_FAILED';
      }
      stringAssignments.push({
        script_index: script.index,
        variable: candidate.name,
        literal_bytes_utf8: Buffer.byteLength(candidate.literal, 'utf8'),
        literal_sha256: sha256(candidate.literal),
        decoded_string_bytes_utf8: typeof decoded === 'string' ? Buffer.byteLength(decoded, 'utf8') : null,
        decoded_string_line_count: typeof decoded === 'string' ? decoded.split(/\r?\n/).length : null,
        decoded_string_sha256: typeof decoded === 'string' ? sha256(decoded) : null,
        initializer_tail: candidate.tail,
        status,
      });
    }
  }

  return {
    key,
    requested_url: url,
    probe_status: 'LIVE_HTML_FETCHED',
    selected_profile: selectedProfile,
    attempts,
    final_url: response.url,
    http_status: response.status,
    content_type: response.headers.get('content-type'),
    html_bytes_utf8: Buffer.byteLength(html, 'utf8'),
    html_sha256: sha256(html),
    script_tag_count: scriptMatches.length,
    inline_script_count: inlineScripts.length,
    literal_assignment_count: assignments.length,
    literal_assignments: assignments,
    string_assignment_count: stringAssignments.length,
    string_assignments: stringAssignments,
  };
}

const results = [];
for (const [key, url] of Object.entries(pages)) {
  results.push(await inspectPage(key, url));
}

const output = {
  schema: 'eksamio.live-thematic-backing-probe.v0.1',
  authority: 'live eksamio.ru public trainer surfaces; read-only GET probe',
  admission_effect: 'NONE',
  semantic_admissions: 0,
  object_closures: 0,
  mastery_admissions: 0,
  false_exact_mastery: 0,
  resolved_page_count: results.filter((x) => x.probe_status === 'LIVE_HTML_FETCHED').length,
  blocked_page_count: results.filter((x) => x.probe_status !== 'LIVE_HTML_FETCHED').length,
  pages: results,
};

const outPath = process.env.PROBE_OUT || 'live-thematic-backing-probe.json';
fs.writeFileSync(outPath, `${JSON.stringify(output, null, 2)}\n`, 'utf8');
console.log(JSON.stringify(output));
