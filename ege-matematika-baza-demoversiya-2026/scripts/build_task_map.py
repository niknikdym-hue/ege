#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'content'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

index = load(ROOT / 'ege-matematika-baza-demoversiya-2026-TASK-SOURCE-INDEX.json')
answers = load(ROOT / 'ege-matematika-baza-demoversiya-2026-OFFICIAL-ANSWERS.json')
exam = load(ROOT / 'ege-matematika-baza-demoversiya-2026-EXAM-MAP.json')
parts = [
    load(CONTENT / 'tasks-01-07.json'),
    load(CONTENT / 'tasks-08-14.json'),
    load(CONTENT / 'tasks-15-21.json'),
]

errors=[]
def require(cond,msg):
    if not cond: errors.append(msg)

captured=[]
for part in parts:
    captured.extend(part['tasks'])

require([t['number'] for t in captured] == list(range(1,22)), 'content task order must be 1..21')

index_by={(t['number'],v['variant']):v for t in index['tasks'] for v in t['variants']}
answer_by={(int(n),v['variant']):v for n,rows in answers['tasks'].items() for v in rows}
content_by={}
for task in captured:
    for v in task['variants']:
        key=(task['number'],v['variant'])
        require(key not in content_by, f'duplicate content {key}')
        content_by[key]=v

require(len(content_by)==70, f'captured examples must be 70, got {len(content_by)}')
require(set(content_by)==set(index_by), 'content variants differ from TASK-SOURCE-INDEX')
require(set(content_by)==set(answer_by), 'content variants differ from OFFICIAL-ANSWERS')

for key,v in content_by.items():
    idx=index_by[key]
    require(v['source_page']==idx['page'], f'{key}: source page {v["source_page"]} != index {idx["page"]}')
    require(v['control']==idx['control'], f'{key}: control {v["control"]} != index {idx["control"]}')
    require(bool(v.get('prompt_html')), f'{key}: prompt_html missing')
    if idx.get('visual'):
        # Some official examples have a visual embedded in a matching/table structure.
        # Every substantial standalone visual must either have an asset_id or be explicitly formula/table-only.
        if idx.get('visual_type') not in {'four_function_graphs'} or key != (7,3):
            require(bool(v.get('asset_id')), f'{key}: visual example has no asset_id')
    if v['control']=='matching_selects_4':
        left=v.get('left') or v.get('left_latex')
        right=v.get('right') or v.get('right_latex')
        require(left and len(left)==4, f'{key}: matching left must have 4 items')
        require(right and len(right)==4, f'{key}: matching right must have 4 items')
    if v['control'] in {'checkboxes','row_checkboxes'}:
        require(v.get('options') or v.get('table'), f'{key}: selection control missing options/table')

# Merge content with the one official answer source. The generated task map never retypes answers.
output_tasks=[]
for task in captured:
    out={'number':task['number'],'variants':[]}
    for v in task['variants']:
        key=(task['number'],v['variant'])
        merged=dict(v)
        merged['official_answer_ref']={
            'file':'ege-matematika-baza-demoversiya-2026-OFFICIAL-ANSWERS.json',
            'task':task['number'],
            'variant':v['variant']
        }
        merged['canonical_forms']=answer_by[key]['canonical_forms']
        if answer_by[key].get('order_ignored'):
            merged['order_ignored']=True
        out['variants'].append(merged)
    output_tasks.append(out)

result={
    'exam':'ЕГЭ','subject':'математика','level':'базовый','source_year':2026,
    'package_version':exam['package_version'],
    'status':'TASK_MAP_BUILT_SOURCE_CAPTURED_VISUAL_GATE_PENDING',
    'source_register':'ege-matematika-baza-demoversiya-2026-SOURCE-REGISTER.json',
    'official_answers':'ege-matematika-baza-demoversiya-2026-OFFICIAL-ANSWERS.json',
    'tasks':output_tasks,
    'counts':{'tasks':21,'official_examples':70}
}

(ROOT/'ege-matematika-baza-demoversiya-2026-TASK-MAP.json').write_text(
    json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

evidence={'status':'PASS' if not errors else 'FAIL','tasks':len(output_tasks),'official_examples':len(content_by),'errors':errors}
(ROOT/'ege-matematika-baza-demoversiya-2026-TASK-MAP-BUILD-EVIDENCE.json').write_text(
    json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if errors:
    for e in errors: print('FAIL:',e)
    raise SystemExit(1)
print('TASK MAP BUILD: PASS')
print(json.dumps(evidence,ensure_ascii=False,indent=2))
