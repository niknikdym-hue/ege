from __future__ import annotations
import base64, hashlib, json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P='ege-biologiya-demoversiya'
DATA=json.loads((ROOT/f'{P}-EXAM-DATA.json').read_text(encoding='utf-8'))
TASKS=DATA['tasks']
assert DATA['package_version']=='1.0.2'
assert DATA['storage_key']=='eksamio_ege_biologiya_demo_2026_v1_0_2'
assert len(TASKS)==35
assert {t['number'] for t in TASKS}==set(range(1,29))
from collections import Counter
assert Counter(t['number'] for t in TASKS)==Counter({27:4,4:2,5:2,6:2,24:2,**{n:1 for n in range(1,29) if n not in {4,5,6,24,27}}})
assert sum(t['max_score'] for t in TASKS if t['kind']=='short' and t['variant_id']=='1' and t['number'] not in {4,5,6}) + 1 + 1 + 2 == 36
assert len([n for n in range(1,29) if next(t for t in TASKS if t['number']==n)['kind']=='extended'])==7

expected={1:'биосферный',2:'31',3:'800',7:'134',8:'54132',9:'4',10:'123313',11:'126',12:'421563',13:'4',14:'131233',15:'456',16:'164325',17:'235',18:'456',19:'212112',20:'763',21:'13'}
for n,v in expected.items():
    assert next(t for t in TASKS if t['number']==n and t['variant_id']=='1')['answer']['canonical']==v
assert [next(t for t in TASKS if t['number']==4 and t['variant_id']==v)['answer']['canonical'] for v in ('1','2')]==['31','0,25']
assert [next(t for t in TASKS if t['number']==5 and t['variant_id']==v)['answer']['canonical'] for v in ('1','2')]==['5','6']
assert [next(t for t in TASKS if t['number']==6 and t['variant_id']==v)['answer']['canonical'] for v in ('1','2')]==['122122','312231']

by_type={}
for t in TASKS:
    by_type.setdefault(t['interaction']['type'],set()).add(t['number'])
assert by_type['table_selects']=={2,20}
assert by_type['matching_selects']=={6,10,14,19}
assert by_type['sequence_builder']=={8,12,16}
assert by_type['multiple_choice']=={7,11,15,17,18,21}
assert by_type['text_input']=={1,3,4,5,9,13}
assert by_type['extended_text']==set(range(22,29))
for t in TASKS:
    it=t['interaction']
    if it['type'] in {'table_selects','matching_selects'}:
        assert len(it['rows'])==len(t['answer']['canonical'])
        assert all(r['key'] for r in it['rows'])
        assert all(c['value'] and c['text'] for c in it['choices'])
    if it['type']=='sequence_builder':
        assert len(it['options'])==len(t['answer']['canonical'])
    if it['type']=='multiple_choice':
        assert len(it['options'])>=5
        if t['number']==21: assert it['max_select'] is None
        else: assert it['max_select']==3
for t in TASKS:
    if t['kind']=='extended':
        assert t['criterion_elements'] and t['score_rules'] and t['model_answer_html']
        assert max(r['score'] for r in t['score_rules'])==3

blocks=sorted(ROOT.glob(f'{P}-T123-*.txt'))
contract=json.loads((ROOT/f'{P}-PACKAGE-CONTRACT.json').read_text())
assert len(blocks)==contract['t123_blocks']==19
assert max(b.stat().st_size for b in blocks)<55000
assert [b.name for b in blocks]==contract['load_order']
joined='\n'.join(b.read_text(encoding='utf-8') for b in blocks)
assert 'eksamio_ege_biologiya_demo_2026_v1_0_2' in joined
assert 'data-structured-select' in joined and 'data-sequence-value' in joined and 'data-multi-value' in joined

# Reassemble embedded data and compare with canonical JSON.
def chunks(name):
    out=[]
    pat=re.compile(rf'<script>window\.{re.escape(name)}=window\.{re.escape(name)}\|\|\[\];window\.{re.escape(name)}\.push\((.*)\);</script>',re.S)
    for b in blocks:
        m=pat.fullmatch(b.read_text(encoding='utf-8').strip())
        if m: out.append(json.loads(m.group(1)))
    return out
embedded=json.loads(''.join(chunks('__BIO_TASK_CHUNKS__')))
assert embedded==DATA
asset_data=json.loads(''.join(chunks('__BIO_ASSET_CHUNKS__')))
assert len(asset_data)==11
for k,v in asset_data.items():
    assert v.startswith('data:image/webp;base64,')
    raw=base64.b64decode(v.split(',',1)[1])
    assert raw[:4]==b'RIFF' and raw[8:12]==b'WEBP'

preview=(ROOT/f'{P}-PREVIEW.html').read_text(encoding='utf-8')
assert preview.count('<title>')==1
assert preview.count('id="eksamio-bio-demo"')==1
assert '—/57' in preview
for name in ['ege-2026-biologiya-demoversiya.pdf','ege-2026-biologiya-kodifikator.pdf','ege-2026-biologiya-specifikatsiya.pdf']:
    f=ROOT/'source'/name
    assert f.exists() and f.stat().st_size>100_000
print('STATIC PASS')
