import crypto from 'node:crypto';
import fs from 'node:fs';

const inputPath = process.env.PROBE_IN || 'paronym-admission-authority-capture.json';
const outputPath = process.env.AUTHORITY_OUT || 'eksamio-learning-engine/peis-production-substrate/admissions/PARONYM-CONTEXT-CHOICE-ADMISSION-AUTHORITY-v0.1.json';
const captureHead = process.env.CAPTURE_HEAD || '';
const captureRun = Number(process.env.CAPTURE_RUN || 0);
const captureArtifactId = Number(process.env.CAPTURE_ARTIFACT_ID || 0);
const captureArtifactDigest = process.env.CAPTURE_ARTIFACT_DIGEST || '';

function sha256(value) {
  return crypto.createHash('sha256').update(value, 'utf8').digest('hex');
}

const data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
if (data.status !== 'READ_ONLY_CAPTURE_NO_PRODUCTION_ADMISSION') throw new Error('capture status drift');
if (data.issue_185_exact_head !== 'c5592c212557b91578ed48e1bf778e30dd489dc7') throw new Error('issue185 head drift');
if (data.group_count !== 144 || data.entry_count !== 334) throw new Error('full paronym denominator drift');
if (data.context_choice_candidate_count !== 334) throw new Error('not every exact full-trainer entry has one context placeholder');
if (data.ordered_candidate_item_id_sha256 !== '48eedc3e5f3751cec57152671456d314b7bcb6b13f2ee5002f35ec6660482c99') throw new Error('candidate ids drift');
if (data.ordered_candidate_correct_word_sha256 !== '75ed53cc846cc36009aa66220acb4e9959f3a88dd2068f5ef3b5ec057af569bc') throw new Error('correct-word key drift');
if (data.ordered_candidate_context_sha256 !== '491de4e281c06bbd93a7bdb2e5dbc659909e336b49d5fa316930f35c0943c3f8') throw new Error('context key drift');
if (data.ordered_candidate_group_choices_sha256 !== '4c96b0a49684a7d2988b527feabe831de1dfec60adfa4364ca927ff169b0b41e') throw new Error('group choices drift');

const groups = {};
const entries = [];
for (const item of data.items) {
  if (item.context_choice_candidate !== true || item.exact_context_placeholder_count !== 1) {
    throw new Error(`non-context-choice row leaked into authority: ${item.item_id}`);
  }
  const prior = groups[item.group_id];
  if (prior && JSON.stringify(prior) !== JSON.stringify(item.group_words)) {
    throw new Error(`group choices drift inside ${item.group_id}`);
  }
  groups[item.group_id] = item.group_words;
  if (!item.group_words.includes(item.correct_word)) throw new Error(`answer outside exact choices: ${item.item_id}`);
  entries.push([item.item_id, item.group_id, item.correct_word]);
}
if (Object.keys(groups).length !== 144 || entries.length !== 334) throw new Error('authority cardinality drift');

const authority = {
  schema: 'eksamio.paronym-context-choice-admission-authority.v0.1',
  status: 'BOUNDED_PRODUCTION_EVENT_ADMISSION_KEY',
  source_authority: {
    issue_185_pr: 187,
    issue_185_exact_head: data.issue_185_exact_head,
    capture_head: captureHead || null,
    capture_workflow_run: captureRun || null,
    capture_artifact_id: captureArtifactId || null,
    capture_artifact_digest: captureArtifactDigest || null,
    live_html_sha256: data.live_html_sha256,
    group_count: data.group_count,
    entry_count: data.entry_count,
    ordered_group_id_sha256: data.ordered_group_id_sha256,
    ordered_entry_id_sha256: data.ordered_entry_id_sha256,
    fipi_2026_exact_group_correspondence: data.fipi_2026_exact_group_correspondence,
  },
  admission: {
    item_count: 334,
    selection_rule: 'exact full-trainer entry with exactly one _____ context placeholder',
    action_id: 'context_collocation_choice',
    semantic_id: 'ru-lexis-paronym-collocation-choice',
    mapping_resolution: 'EXACT',
    registered_user_identity_ref_required: true,
    anonymous_identity_ref_forbidden: true,
    server_evaluator: 'deterministic_paronym_exact_context_choice_v1',
  },
  integrity: {
    ordered_item_id_sha256: data.ordered_candidate_item_id_sha256,
    ordered_correct_word_sha256: data.ordered_candidate_correct_word_sha256,
    ordered_context_sha256: data.ordered_candidate_context_sha256,
    ordered_group_choices_sha256: data.ordered_candidate_group_choices_sha256,
  },
  groups,
  entries,
  boundaries: {
    meaning_match_admitted: false,
    independent_paronym_recall_admitted: false,
    exam_error_correction_admitted: false,
    generic_trainer_completion_mastery: false,
    browser_local_progress_mastery: false,
    asset_wide_mastery: false,
    false_exact_mastery: 0,
  },
};

const serialized = `${JSON.stringify(authority, null, 2)}\n`;
fs.mkdirSync(new URL('.', `file://${process.cwd()}/${outputPath}`).pathname, { recursive: true });
fs.writeFileSync(outputPath, serialized, 'utf8');
console.log(`wrote ${outputPath}`);
console.log(`groups=${Object.keys(groups).length} entries=${entries.length}`);
console.log(`authority sha256=${sha256(serialized)}`);
