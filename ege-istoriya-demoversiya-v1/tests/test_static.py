from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
P='ege-istoriya-demoversiya'
exam=json.loads((ROOT/f'{P}-EXAM-DATA.json').read_text())
assert exam['task_count']==21 and len(exam['tasks'])==21
assert sum(t['max_score'] for t in exam['tasks'] if t['kind']=='short')==20
assert sum(t['max_score'] for t in exam['tasks'] if t['kind']=='extended')==22
assert exam['max_primary']==42 and exam['duration_minutes']==210
assert [t['answer']['canonical'] for t in exam['tasks'][:12]]==['6235','132','3126','943517','4625','2456','6524','сорок пятом','Алексей Михайлович','Симбирск','Астрахань','56']
blocks=sorted(ROOT.glob(f'{P}-T123-*.txt'))
assert blocks and max(f.stat().st_size for f in blocks)<55000
contract=json.loads((ROOT/f'{P}-PACKAGE-CONTRACT.json').read_text())
assert len(blocks)==contract['t123_blocks']
seo=(ROOT/f'{P}-SEO.txt').read_text()
for line in seo.splitlines():
    if line.startswith(('PAGE_URL:','TITLE:','DESCRIPTION:','CANONICAL:')): assert '2026' not in line
preview=(ROOT/f'{P}-PREVIEW.html').read_text()
assert 'Официальный итог до экспертной проверки' in preview and 'учебная самооценка' in preview.lower()
for a in json.loads((ROOT/f'{P}-ASSET-MAP.json').read_text()):
    f=ROOT/'assets'/a['file'];assert f.exists() and f.stat().st_size==a['bytes']
print('STATIC PASS')
