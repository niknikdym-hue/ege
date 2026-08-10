#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TASK_MAP=ROOT/'ege-matematika-baza-demoversiya-2026-TASK-MAP.json'
if not TASK_MAP.exists():
    raise SystemExit('TASK-MAP.json does not exist; build it first')

task_map=json.loads(TASK_MAP.read_text(encoding='utf-8'))

cases=[]
for task in task_map['tasks']:
    n=task['number']
    for v in task['variants']:
        key=f'{n}.{v["variant"]}'
        control=v['control']
        canonical=v['canonical_forms']
        row={
            'id':f'base-2026-{n:02d}-v{v["variant"]}',
            'task':n,
            'variant':v['variant'],
            'source_page':v['source_page'],
            'control':control,
            'official_correct_forms':canonical,
            'interaction_cases':[
                {'case':'open_variant','expected':'assigned official example is rendered with declared control'},
                {'case':'mark_for_return','expected':'orange return flag persists independently of answer state'},
                {'case':'reload_before_answer','expected':'same official variant is restored'},
                {'case':'complete_correct_answer','expected':'answer becomes valid, autosaves, navigation becomes answered'},
                {'case':'reload_after_answer','expected':'same variant and same valid answer are restored'},
                {'case':'change_answer','expected':'new value replaces old value and autosaves'},
                {'case':'clear_answer','expected':'answer becomes empty and navigation returns to unanswered unless flagged'},
                {'case':'complete_wrong_answer','expected':'answer may be valid-format but receives 0 after finish'},
                {'case':'finish_attempt','expected':'scorer runs only after completion and produces 0 or 1 for this task'}
            ]
        }

        if control=='numeric_input':
            row['input_hygiene_cases']=[
                {'input':'letters','example':'abc','expected':'blocked or invalid; never silently cleaned into a scoreable answer'},
                {'input':'internal_space','example':'1 2','expected':'invalid; scorer must not delete spaces'},
                {'input':'leading_space','example':' 1','expected':'invalid or prevented before save; scorer must not trim it into correctness'},
                {'input':'trailing_space','example':'1 ','expected':'invalid or prevented before save; scorer must not trim it into correctness'},
                {'input':'plus_sign','example':'+1','expected':'invalid unless a future official answer explicitly requires plus'},
                {'input':'two_decimal_marks','example':'1,2,3','expected':'invalid'},
                {'input':'wrong_valid_number','example':'987654321','expected':'valid-format where length allows, score 0'}
            ]
            if any(',' in x for x in canonical):
                point_forms=[x.replace(',','.') for x in canonical if ',' in x]
                row['input_hygiene_cases'].append({
                    'input':'keyboard_decimal_point',
                    'examples':point_forms,
                    'expected':'UI immediately canonicalizes dot to comma before save; stored/scored value uses official comma form'
                })
            if len(canonical)>1:
                row['official_alternative_cases']=[
                    {'input':x,'expected':'score 1'} for x in canonical
                ]

        elif control=='matching_selects_4':
            correct=canonical[0]
            row['matching_cases']=[
                {'case':'empty','expected':'unanswered'},
                {'case':'one_position_missing','expected':'not valid / not answered'},
                {'case':'duplicate_choice','expected':'prevented or marked invalid because mapping is one-to-one'},
                {'case':'correct_mapping','selection':list(correct),'expected':f'system assembles {correct}; score 1'},
                {'case':'wrong_mapping','selection':['1','1','1','1'],'expected':'invalid or score 0; never normalized to correct code'}
            ]

        elif control in {'checkboxes','row_checkboxes'}:
            unique_sets=[]
            for form in canonical:
                s=tuple(sorted(form))
                if s not in unique_sets:
                    unique_sets.append(s)
            row['selection_cases']=[
                {'case':'empty','selection':[],'expected':'unanswered'},
                {'case':'each_official_set','accepted_sets':[list(x) for x in unique_sets],'expected':'each official set scores 1'},
                {'case':'selection_order','expected':'selection order does not affect set comparison'},
                {'case':'missing_member','expected':'score 0'},
                {'case':'extra_member','expected':'score 0'}
            ]

        if v.get('asset_id'):
            row['visual_cases']=[
                {'case':'source_asset_present','asset_id':v['asset_id'],'expected':'asset matches official PDF source crop'},
                {'case':'four_edges','expected':'no source label, axis, arrow, point or boundary is cropped'},
                {'case':'desktop_mobile','expected':'readable at 1280, 768, 390, 360 and 320 px without page horizontal scroll'}
            ]
        if v.get('formula_latex') or v.get('left_latex') or v.get('right_latex'):
            row['formula_cases']=[
                {'case':'semantic_fidelity','expected':'symbols, roots, fractions, exponents, signs and grouping match source'},
                {'case':'visual_fidelity','expected':'display form matches official PDF; mathematical equivalence alone is insufficient'}
            ]

        cases.append(row)

out={
    'exam':'ЕГЭ','subject':'математика','level':'базовый','source_year':2026,
    'status':'GENERATED_FROM_TASK_MAP_PENDING_BROWSER_EXECUTION',
    'case_count':len(cases),
    'official_example_count':70,
    'cases':cases
}
assert len(cases)==70
(ROOT/'ege-matematika-baza-demoversiya-2026-ACCEPTANCE-CASES.json').write_text(
    json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'ACCEPTANCE CASES BUILT: {len(cases)}')
