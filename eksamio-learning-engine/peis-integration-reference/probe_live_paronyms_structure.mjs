import crypto from 'node:crypto';
import fs from 'node:fs';

const URL = 'https://eksamio.ru/trenazhery/russkiy/paronimy/';
const OUT = process.env.PROBE_OUT || 'live-paronyms-structure.json';

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

function boundedWindows(text, regex, radius = 700, limit = 30) {
  const out = [];
  const re = new RegExp(regex.source, regex.flags.includes('g') ? regex.flags : `${regex.flags}g`);
  let match;
  while ((match = re.exec(text)) !== null && out.length < limit) {
    const start = Math.max(0, match.index - radius);
    const end = Math.min(text.length, match.index + match[0].length + radius);
    out.push({
      match: match[0],
      index: match.index,
      start,
      end,
      snippet: text.slice(start, end),
      snippet_sha256: sha256(text.slice(start, end)),
    });
    if (match[0].length === 0) re.lastIndex += 1;
  }
  return out;
}

function collectDataAttributes(html) {
  const counts = new Map();
  const values = new Map();
  const re = /\b(data-[a-zA-Z0-9:_-]+)\s*=\s*(["'])(.*?)\2/gs;
  let match;
  while ((match = re.exec(html)) !== null) {
    const name = match[1].toLowerCase();
    const value = match[3];
    counts.set(name, (counts.get(name) ?? 0) + 1);
    if (!values.has(name)) values.set(name, []);
    const list = values.get(name);
    if (list.length < 12 && !list.includes(value)) list.push(value);
  }
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count, sample_values: values.get(name) }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}

function collectDeclaredVariables(script) {
  const out = [];
  const re = /\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*([^;\n]{0,220})/g;
  let match;
  while ((match = re.exec(script)) !== null) {
    out.push({ name: match[1], initializer_prefix: match[2].trim() });
  }
  return out;
}

const { response, html, attempts, selected_profile } = await fetchHtml();
const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
  .map((m, index) => ({ index, attrs: m[1], text: m[2] }));
const targetScripts = scripts.filter((s) => /\bEXAM_BANK\b/.test(s.text) || /\bCARDS\b/.test(s.text));
if (targetScripts.length !== 1) throw new Error(`expected exactly one paronym application script, got ${targetScripts.length}`);
const target = targetScripts[0];

const anchorRegex = /\b(?:EXAM_BANK|CARDS|card|groups?|words?|mapFilter|querySelectorAll|dataset|JSON\.parse|\.push|\.concat|forEach)\b/g;
const result = {
  schema: 'eksamio.live-paronyms-structure-probe.v0.1',
  authority: 'live eksamio.ru paronyms trainer HTML; read-only GET; bounded static source inspection only',
  checked_at_runtime: new Date().toISOString(),
  requested_url: URL,
  final_url: response.url,
  http_status: response.status,
  selected_profile,
  attempts,
  html_bytes_utf8: Buffer.byteLength(html, 'utf8'),
  html_sha256: sha256(html),
  script_tag_count: scripts.length,
  target_script_index: target.index,
  target_script_bytes_utf8: Buffer.byteLength(target.text, 'utf8'),
  target_script_sha256: sha256(target.text),
  declared_variables: collectDeclaredVariables(target.text),
  data_attributes: collectDataAttributes(html),
  anchor_windows: boundedWindows(target.text, anchorRegex, 700, 40),
  admission_effect: 'NONE',
  semantic_admissions: 0,
  object_closures: 0,
  mastery_admissions: 0,
  false_exact_mastery: 0,
  registered_user_identity_required_for_future_canonical_evidence: true,
  notes: [
    'This probe is forensic only and does not execute the live application script.',
    'Bounded source windows are used only to locate the actual full live paronym backing construction path.',
    'No route/title/task-number inference, semantic admission, or learner mastery is permitted from this probe.',
  ],
};

fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
console.log(`wrote ${OUT}`);
console.log(`target script bytes=${result.target_script_bytes_utf8} sha256=${result.target_script_sha256}`);
console.log(`data attributes=${result.data_attributes.length} windows=${result.anchor_windows.length}`);
