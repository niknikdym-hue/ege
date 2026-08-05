from pathlib import Path
import json,hashlib,re,subprocess
root=Path(__file__).resolve().parents[1];p='ege-obshchestvoznaniye-demoversiya'
data=json.loads((root/f'{p}-EXAM-DATA.json').read_text('utf-8'));tasks=data['tasks']
expected={1:'46',2:'13',3:'32132',4:'146',5:'15',6:'24431',7:'2356',8:'125',9:'145',10:'234',11:'245',12:'123',13:'21312',14:'123',15:'21212',16:'125'}
assert {t['n']:t['answer'] for t in tasks[:16]}==expected
assert sum(t['max'] for t in tasks[:16])==28 and sum(t['max'] for t in tasks[16:])==30
assert 'одном или нескольких распространённых предложениях' in tasks[17]['body']
assert 'причинно-следственные' in tasks[24]['body'] and 'для решения экологических проблем' in tasks[24]['body']
assert 'одного или более ошибочных дополнительных примеров' in next(r for r in tasks[24]['rubrics'] if r['id']=='25.3')['levels']['1']
reg=json.loads((root/f'{p}-SOURCE-REGISTER.json').read_text('utf-8'))
for x in reg['files']:
 f=root/'source'/x['file'];assert f.exists() and hashlib.sha256(f.read_bytes()).hexdigest()==x['sha256']
# T123 content blocks must be generated from EXAM-DATA without drift.
ns={'tasks':[]}
import html
for n in range(2,6):
 s=(root/f'{p}-T123-{n:02d}.txt').read_text('utf-8')
 for m in re.finditer(r'tasks\.push\(\.\.\.(\[.*?\])\);',s,re.S):ns['tasks']+=json.loads(m.group(1))
assert ns['tasks']==tasks
print('SOURCE FIDELITY PASS')
