import { spawnSync } from 'node:child_process';
import fs from 'node:fs';

const OUT = process.env.PROBE_OUT || 'dictionary-same-row-family-membership.json';
const PRIMARY_OUT = 'dictionary-same-row-family-membership-primary.json';

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

const child = spawnSync(
  process.execPath,
  ['eksamio-learning-engine/peis-integration-reference/probe_live_fipi_primary_correspondence.mjs'],
  {
    encoding: 'utf8',
    env: { ...process.env, PROBE_OUT: PRIMARY_OUT },
  },
);
if (child.status !== 0) {
  process.stderr.write(child.stdout || '');
  process.stderr.write(child.stderr || '');
  throw new Error(`primary correspondence probe failed with exit ${child.status}`);
}

const primary = JSON.parse(fs.readFileSync(PRIMARY_OUT, 'utf8'));
const dictionary = primary.dictionary_words;
if (dictionary.live_count !== 308 || dictionary.source_count !== 308) throw new Error('dictionary denominator drift');
if (dictionary.exact_primary_mismatch_count !== dictionary.mismatch_sample.length) {
  throw new Error(`bounded mismatch sample is incomplete: ${dictionary.mismatch_sample.length}/${dictionary.exact_primary_mismatch_count}`);
}

const sameRowMemberMatches = [];
const unresolved = [];
for (const mismatch of dictionary.mismatch_sample) {
  const sourceMembers = stripParenthetical(mismatch.source_full_row)
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);
  const normalizedMembers = sourceMembers.map(normalize);
  const live = normalize(mismatch.live);
  const memberIndex = normalizedMembers.indexOf(live);
  const record = {
    index_1based: mismatch.index_1based,
    live_id: mismatch.live_id,
    live: mismatch.live,
    source_full_row: mismatch.source_full_row,
    source_members: sourceMembers,
  };
  if (memberIndex >= 0) {
    sameRowMemberMatches.push({ ...record, exact_member_index_1based: memberIndex + 1 });
  } else {
    unresolved.push(record);
  }
}

const result = {
  schema: 'eksamio.dictionary-same-row-family-membership.v0.1',
  authority: 'exact output of live/FIPI primary correspondence probe on this run',
  authority_checked_at_runtime: primary.authority_checked_at_runtime,
  exact_sources: primary.exact_sources,
  rule: 'same indexed FIPI row only -> remove parenthetical segment(s) -> split comma-separated forms -> require exact normalized live word membership; no morphology, fuzzy matching, reordering, or route/title inference',
  dictionary_total: dictionary.live_count,
  primary_exact_count: dictionary.exact_primary_match_count,
  primary_mismatch_count: dictionary.exact_primary_mismatch_count,
  additional_exact_same_row_member_count: sameRowMemberMatches.length,
  exact_same_row_supported_count: dictionary.exact_primary_match_count + sameRowMemberMatches.length,
  unresolved_count: unresolved.length,
  status: unresolved.length === 0 ? 'EXACT_SAME_ROW_FIPI_FAMILY_MEMBERSHIP_ALL' : 'BOUNDED_UNRESOLVED_BLOCKER',
  unresolved,
  same_row_member_matches: sameRowMemberMatches,
  admission_effect: 'NONE',
  semantic_admissions: 0,
  object_closures: 0,
  mastery_admissions: 0,
  false_exact_mastery: 0,
  registered_user_identity_required_for_future_canonical_evidence: true,
  notes: [
    'This is provenance/text membership evidence only and cannot self-admit PEIS semantic ownership or mastery.',
    'Unresolved rows remain explicit blockers; no morphological equivalence is inferred.'
  ],
};

fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
console.log(`wrote ${OUT}`);
console.log(`dictionary supported=${result.exact_same_row_supported_count}/${result.dictionary_total}; unresolved=${result.unresolved_count}`);
for (const row of unresolved) console.log(`unresolved ${row.index_1based} ${row.live_id}: ${row.live} <> ${row.source_full_row}`);
