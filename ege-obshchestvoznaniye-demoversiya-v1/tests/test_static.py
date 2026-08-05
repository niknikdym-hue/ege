from pathlib import Path
import json,re,hashlib,zipfile,sys
root=Path(__file__).resolve().parents[1];p='ege-obshchestvoznaniye-demoversiya'
data=json.loads((root/f'{p}-EXAM-DATA.json').read_text('utf-8'))
assert data['packageVersion']=='1.0.2' and data['storageKey']=='eksamio_ege_soc_demo_v3'
assert len(data['tasks'])==25 and len([x for x in data['tasks'] if x['part']==1])==16
assert all(x.get('interaction',{}).get('type') in {'multiple_choice','matching'} for x in data['tasks'][:16])
assert [x['n'] for x in data['tasks'][:16] if x['interaction']['type']=='matching']==[3,6,13,15]
assert [x['n'] for x in data['tasks'][:16] if x['interaction']['type']=='multiple_choice']==[1,2,4,5,7,8,9,10,11,12,14,16]
blocks=[root/f'{p}-T123-{i:02d}.txt' for i in range(1,7)]
assert all(x.exists() for x in blocks) and max(x.stat().st_size for x in blocks)<55000
runtime=blocks[-1].read_text('utf-8'); shell=blocks[0].read_text('utf-8')
for token in ['multiple_choice','matching','answerCode','soc-match-select','soc-choice-list','eksamio_ege_soc_demo_v3']: assert token in runtime+shell,token
assert "$('#soc-total-score').textContent='—/58'" in runtime
assert 'done?`${p1+p2}/58`' not in runtime
assert '__MACOSX' not in '\n'.join(x.as_posix() for x in root.rglob('*'))
assert not list(root.rglob('.DS_Store'))
contract=json.loads((root/f'{p}-PACKAGE-CONTRACT.json').read_text('utf-8'))
assert contract['result_contract']['official_total_before_expert']=='— / 58'
print('STATIC PASS')
