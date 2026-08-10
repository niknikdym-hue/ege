#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))

exam = load('ege-matematika-baza-demoversiya-2026-EXAM-MAP.json')
answers = load('ege-matematika-baza-demoversiya-2026-OFFICIAL-ANSWERS.json')
index = load('ege-matematika-baza-demoversiya-2026-TASK-SOURCE-INDEX.json')

errors=[]

def require(condition, message):
    if not condition:
        errors.append(message)

require(exam['task_count'] == 21, 'EXAM-MAP task_count must be 21')
require(exam['duration_minutes'] == 180, 'duration must be 180')
require(exam['max_primary_score'] == 21, 'max primary score must be 21')
require(len(index['tasks']) == 21, 'TASK-SOURCE-INDEX must have 21 positions')

expected_counts={int(k):v for k,v in exam['official_example_counts_by_task'].items()}
actual_counts={}
examples=[]
for task in index['tasks']:
    n=task['number']
    variants=task['variants']
    actual_counts[n]=len(variants)
    for v in variants:
        examples.append((n,v['variant'],v['control']))
        require(8 <= v['page'] <= 28, f'task {n} variant {v["variant"]}: source page outside task pages')

require(actual_counts == expected_counts, f'variant counts mismatch: {actual_counts} != {expected_counts}')
require(len(examples) == 70, f'expected 70 official examples, got {len(examples)}')

# Every indexed variant must have exactly one corresponding official answer record.
answer_pairs=[]
for task_no, variants in answers['tasks'].items():
    for row in variants:
        answer_pairs.append((int(task_no), row['variant']))
        forms=row.get('canonical_forms',[])
        require(bool(forms), f'task {task_no} variant {row["variant"]}: no canonical answer forms')
        require(len(forms) == len(set(forms)), f'task {task_no} variant {row["variant"]}: duplicate canonical forms')

index_pairs=[(n,v) for n,v,_ in examples]
require(sorted(index_pairs) == sorted(answer_pairs), 'TASK-SOURCE-INDEX variants and OFFICIAL-ANSWERS variants differ')

# Controls are constrained to the subject protocol.
allowed={'numeric_input','matching_selects_4','checkboxes','row_checkboxes'}
for n,v,c in examples:
    require(c in allowed, f'task {n} variant {v}: unsupported control {c}')

matching=sum(c=='matching_selects_4' for _,_,c in examples)
checkbox=sum(c in {'checkboxes','row_checkboxes'} for _,_,c in examples)
numeric=sum(c=='numeric_input' for _,_,c in examples)
require(matching == index['counts']['matching_examples'] == 8, f'matching count {matching}')
require(checkbox == index['counts']['checkbox_examples'] == 4, f'checkbox count {checkbox}')
require(numeric == index['counts']['numeric_input_examples'] == 58, f'numeric count {numeric}')
require(matching+checkbox+numeric == 70, 'control counts do not total 70')

# Matching and checkbox controls must declare enough structural metadata.
for task in index['tasks']:
    for v in task['variants']:
        c=v['control']
        if c=='matching_selects_4':
            require(v.get('positions') == ['А','Б','В','Г'], f'task {task["number"]} v{v["variant"]}: matching positions invalid')
        if c in {'checkboxes','row_checkboxes'}:
            require(len(v.get('option_ids',[])) >= 4, f'task {task["number"]} v{v["variant"]}: missing checkbox options')
            require(v.get('selection_semantics') == 'set', f'task {task["number"]} v{v["variant"]}: checkbox scorer must use set semantics')

# Official special rule for task 8 is represented by alternative orders in the answer source.
for row in answers['tasks']['8']:
    require(row.get('order_ignored') is True, f'task 8 v{row["variant"]}: order_ignored must be true')

result={
    'status':'PASS' if not errors else 'FAIL',
    'task_count':len(index['tasks']),
    'official_examples':len(examples),
    'control_counts':{'matching_selects_4':matching,'checkbox_examples':checkbox,'numeric_input':numeric},
    'variant_counts':actual_counts,
    'errors':errors
}
(ROOT/'ege-matematika-baza-demoversiya-2026-SOURCE-INDEX-TEST-EVIDENCE.json').write_text(
    json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if errors:
    for error in errors:
        print('FAIL:',error)
    raise SystemExit(1)
print('SOURCE INDEX VALIDATION: PASS')
print(json.dumps(result,ensure_ascii=False,indent=2))
