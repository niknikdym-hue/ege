#!/usr/bin/env python3
import csv, hashlib, json, re, subprocess, sys, zipfile
from pathlib import Path
HERE=Path(__file__).resolve(); ROOT=HERE.parent.parent; REPO=ROOT.parent; PREFIX='ege-matematika-profil-demoversiya-2023'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(root=ROOT,clean=False):
    root=Path(root);checks={}
    src=REPO/'matematika-source-2023'/'ege-2023-matematika-profil-demoversiya.pdf';assert sha(src)=='9278f5cc60388da2ed63eaa946c82e0902f0867047fc9b5ea6051bae16e3b6b2';checks['source_sha']='PASS'
    data=json.loads((root/f'{PREFIX}-EXAM-DATA.json').read_text(encoding='utf-8'));assert data['sourceYear']==2023 and data['officialExampleCount']==35 and data['minutes']==235 and data['maxPrimaryScore']==31
    assert len(data['tasks'])==18 and sum(len(t['variants']) for t in data['tasks'])==35;checks['structure']='PASS 18/35/235/31'
    anslock=json.loads((REPO/'matematika-source-2023'/'profile-source-lock'/'ANSWER-LOCK.json').read_text(encoding='utf-8'));official={(x['task'],x['variant']):x['official'][0] for x in anslock['answers']};assert len(official)==28
    for t in data['tasks']:
        if t['number']<=11:
            for v in t['variants']:assert v['answer']==official[(t['number'],v['variant'])]
    checks['answers']='PASS 28/28 from ANSWER-LOCK'
    source_assets=REPO/'matematika-source-2023'/'profile-source-lock'/'visual-assets';assets=root/'assets';sf=sorted(source_assets.glob('*.webp'));af=sorted(assets.glob('*.webp'));assert len(sf)==len(af)==47
    for p in sf:assert sha(p)==sha(assets/p.name),p.name
    checks['visual_assets']='PASS 47/47 byte-identical to locked prebuild'
    ve=json.loads((REPO/'matematika-source-2023'/'profile-source-lock'/'VISUAL-FIDELITY-EVIDENCE.json').read_text(encoding='utf-8'));txt=json.dumps(ve,ensure_ascii=False);assert txt.count('"pixel_identity": "PASS"')>=47 or '47/47' in (REPO/'matematika-source-2023'/'profile-source-lock'/'VISUAL-PREBUILD-VALIDATION.txt').read_text(encoding='utf-8');checks['visual_fidelity']='PASS prebuild evidence'
    browser=json.loads((root/'tests'/'evidence'/'profile-2023-browser-evidence.json').read_text(encoding='utf-8'));assert browser['status']=='PASS' and browser['checks']['javascript_errors']==0;checks['browser']='PASS'
    blocks=sorted(root.glob(f'{PREFIX}-T123-*.txt'));assert blocks
    for p in blocks:
        text=p.read_text(encoding='utf-8');assert p.stat().st_size<42500
        for tag in ('script','style'):assert len(re.findall(fr'<{tag}(?:\s|>)',text,re.I))==len(re.findall(fr'</{tag}>',text,re.I)),p.name
        for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',text,re.I|re.S)):
            tmp=root/'tests'/f'.audit-{i}.js';tmp.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(tmp)],capture_output=True,text=True);tmp.unlink(missing_ok=True);assert cp.returncode==0,(p.name,cp.stderr)
    checks['t123']=f'PASS {len(blocks)} blocks max {max(p.stat().st_size for p in blocks)} <42500'
    preview=(root/f'{PREFIX}-PREVIEW.html').read_text(encoding='utf-8');assert 'ФИПИ 2024' not in preview and 'ФИПИ 2025' not in preview and 'ФИПИ 2026' not in preview and 'официальный пример ${v.variant}' not in preview;assert 'mp-math-toolbar' in preview and 'mp-zoom-modal' in preview and 'Ваш ответ' in preview;checks['year_ux_isolation']='PASS'
    rows=list(csv.DictReader((root/'AUDIT-MATRIX-2023-profile.csv').open('r',encoding='utf-8-sig')));assert len(rows)==35 and all(r['interaction_gate']=='PASS_BROWSER' for r in rows);checks['audit_matrix']='PASS 35/35'
    out={'status':'PASS','clean_zip_mode':clean,'checks':checks};(root/'INDEPENDENT-AUDIT-2023-profile.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT, '--clean' in sys.argv)
