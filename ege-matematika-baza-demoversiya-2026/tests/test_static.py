#!/usr/bin/env python3
import json
import os
import zipfile
from pathlib import Path

ROOT=Path(os.environ.get('DEMO_ROOT') or Path(__file__).resolve().parents[1])
PREFIX='ege-matematika-baza-demoversiya-2026'

def j(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))

exam=j(f'{PREFIX}-EXAM-DATA.json')
contract=j(f'{PREFIX}-PACKAGE-CONTRACT.json')
formula=j(f'{PREFIX}-FORMULA-GATE-EVIDENCE.json')
visual=j('source-evidence/ASSET-CROP-EVIDENCE.json')
build=j(f'{PREFIX}-BUILD-EVIDENCE.json')

assert exam['packageVersion']==contract['package_version']==build['package_version']
assert exam['storageKey']==build['storage_key']
assert exam['durationMinutes']==180 and exam['maxPrimaryScore']==21
assert len(exam['tasks'])==21 and sum(len(t['variants']) for t in exam['tasks'])==70
assert contract['variant_contract']['official_examples_total']==70
assert contract['interaction_contract']['browser_test_uses_real_controls'] is True
assert formula['status']=='PASS' and formula['counts']['passed']==6
assert visual['status']=='PASS' and visual['asset_count']==25
assert all(r['status']=='PASS' for r in visual['records'])
assert build['official_examples']==70 and build['assets']==25

installation=(ROOT/f'{PREFIX}-INSTALLATION.txt').read_text(encoding='utf-8')
blocks=sorted(ROOT.glob(f'{PREFIX}-T123-*.txt'))
assert blocks and len(blocks)==build['t123_blocks']
assert max(p.stat().st_size for p in blocks)<45000
for p in blocks:assert p.name in installation
assert (ROOT/f'{PREFIX}-PREVIEW.html').exists()
preview=(ROOT/f'{PREFIX}-PREVIEW.html').read_text(encoding='utf-8')
assert 'window.EKSAMIO_MATH_BASE_TEST' in preview
assert exam['storageKey'] in preview
assert f'packageVersion:"{exam["packageVersion"]}"' in preview
assert '03:00:00' in preview
assert 'Справочные материалы ФИПИ' in preview
for token in ['numeric_input','matching_selects_4','checkboxes','row_checkboxes']:
    assert token in preview,token

seo=(ROOT/f'{PREFIX}-SEO.txt').read_text(encoding='utf-8')
head=(ROOT/f'{PREFIX}-HEAD.txt').read_text(encoding='utf-8')
assert 'TITLE:' in seo and '2026' not in seo.splitlines()[0]
assert '<link rel="canonical" href="https://eksamio.ru/ege/matematika-baza/demoversiya/">' in head
assert '2026' not in head.split('og:title',1)[1].split('\n',1)[0]
assert not list(ROOT.rglob('.DS_Store'))
assert '__MACOSX' not in '\n'.join(str(p) for p in ROOT.rglob('*'))
assert not list(ROOT.rglob('*.pyc'))

repo_zip=ROOT.parent/build['package']
if repo_zip.exists():
    with zipfile.ZipFile(repo_zip) as z:
        names=z.namelist()
        assert any(n.endswith(f'{PREFIX}-PREVIEW.html') for n in names)
        assert not any('__MACOSX' in n or n.endswith('.DS_Store') or n.endswith('.pyc') for n in names)
print(f'STATIC PASS: {len(blocks)} T123, max={max(p.stat().st_size for p in blocks)} bytes, package={exam["packageVersion"]}')
