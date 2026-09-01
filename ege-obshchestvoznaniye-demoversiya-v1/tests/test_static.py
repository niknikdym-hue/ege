from pathlib import Path
import json,re,hashlib,zipfile,sys
root=Path(__file__).resolve().parents[1];p='ege-obshchestvoznaniye-demoversiya'
data=json.loads((root/f'{p}-EXAM-DATA.json').read_text('utf-8'))
assert data['packageVersion']=='1.0.5' and data['storageKey']=='eksamio_ege_soc_demo_v3'
assert len(data['tasks'])==25 and len([x for x in data['tasks'] if x['part']==1])==16
assert all(x.get('interaction',{}).get('type') in {'multiple_choice','matching'} for x in data['tasks'][:16])
assert [x['n'] for x in data['tasks'][:16] if x['interaction']['type']=='matching']==[3,6,13,15]
assert [x['n'] for x in data['tasks'][:16] if x['interaction']['type']=='multiple_choice']==[1,2,4,5,7,8,9,10,11,12,14,16]
blocks=[root/f'{p}-T123-{i:02d}.txt' for i in range(1,7)]
assert all(x.exists() for x in blocks) and max(x.stat().st_size for x in blocks)<55000
runtime=blocks[-1].read_text('utf-8'); shell=blocks[0].read_text('utf-8')
for token in ['multiple_choice','matching','answerCode','soc-match-select','soc-choice-list','soc-official-example','ФИПИ 2026 · официальный пример ${t.n}','eksamio_ege_soc_demo_v3']: assert token in runtime+shell,token
assert "done?`${p1+p2}/58`:'—/58'" in runtime
assert "if(!longFilled(t))return true" in runtime
assert 'Задания без ответа учитываются как 0 баллов.' in shell
assert 'Ответ не дан. Задание учитывается как 0 из ${t.max}; самооценка не требуется.' in runtime
assert '__MACOSX' not in '\n'.join(x.as_posix() for x in root.rglob('*'))
assert not list(root.rglob('.DS_Store'))
contract=json.loads((root/f'{p}-PACKAGE-CONTRACT.json').read_text('utf-8'))
assert contract['result_contract']['orientational_total_after_self_assessment']=='part1 + part2 / 58'
print('STATIC PASS')
