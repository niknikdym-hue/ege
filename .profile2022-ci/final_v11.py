#!/usr/bin/env python3
from __future__ import annotations
import base64, gzip, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time, zipfile
from pathlib import Path

REPO=Path.cwd()
ROOT=REPO/'ege-matematika-profil-demoversiya-2022'
LOCK=REPO/'matematika-source-2022'/'profile-source-lock'
PREFIX='ege-matematika-profil-demoversiya-2022'
SOURCE_SHA='14f2039ed7820fb74f0d98269d8add25041a1668b094b173852ea00fb15a36aa'
ZIP=REPO/f'{PREFIX}-v1.0.zip'
FINAL=REPO/f'{PREFIX}-v1.0-SOURCE-LOCKED.zip'

def run(cmd, cwd=None, env=None):
    print('+',' '.join(map(str,cmd)),flush=True)
    subprocess.run(list(map(str,cmd)),cwd=cwd or REPO,env=env,check=True)

def decode(parts, dest):
    raw=''.join((REPO/p).read_text(encoding='utf-8') for p in parts)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(gzip.decompress(base64.b64decode(raw)))

def restore():
    (LOCK).mkdir(parents=True,exist_ok=True)
    (ROOT/'scripts').mkdir(parents=True,exist_ok=True)
    (ROOT/'tests'/'evidence').mkdir(parents=True,exist_ok=True)
    (ROOT/'audit').mkdir(parents=True,exist_ok=True)
    decode(['.profile2022-bootstrap/prepare.part1.b64','.profile2022-bootstrap/prepare.part2.b64'],LOCK/'prepare_profile_2022.py')
    decode(['.profile2022-bootstrap/build.part1.b64','.profile2022-bootstrap/build.part2.b64'],ROOT/'scripts'/'build_profile_2022.py')
    decode(['.profile2022-bootstrap/test.part1.b64','.profile2022-bootstrap/test.part2.b64'],ROOT/'tests'/'test_profile_2022.py')
    decode(['.profile2022-bootstrap/audit.b64'],ROOT/'audit'/'independent_audit_2022.py')

def patch_sources():
    p=LOCK/'prepare_profile_2022.py'; s=p.read_text(encoding='utf-8')
    repl=[
      ("same=sorted((int(c['task']),float(c['rect'][1])) for c in d.get('task_candidates',[]) if float(c['rect'][1])>start+2 and 1<=int(c['task'])<=18)","same=sorted(((int(c['task']),float(c['rect'][1])) for c in d.get('task_candidates',[]) if float(c['rect'][1])>float(loc[t]['rect'][1])+1 and float(c['rect'][0])<45 and 1<=int(c['task'])<=18), key=lambda r:r[1])"),
      ("ors=sorted(r for r in d.get('or_marks',[]) if start < float(r[1]) < end)","ors=sorted(((float(w['x0']),float(w['y0']),float(w['x1']),float(w['y1'])) for w in d['words'] if str(w.get('text','')).strip()=='ИЛИ' and start < float(w['y0']) < end), key=lambda r:r[1])"),
      ("c=[x for x in d.get('task_candidates',[]) if int(x['task'])==t]","c=[x for x in d.get('task_candidates',[]) if int(x['task'])==t and float(x['rect'][0])<45]"),
      ("c17=[x for x in d19.get('task_candidates',[]) if int(x['task'])==17]","c17=[x for x in d19.get('task_candidates',[]) if int(x['task'])==17 and float(x['rect'][0])<45]"),
      ("c18=[x for x in d21.get('task_candidates',[]) if int(x['task'])==18]","c18=[x for x in d21.get('task_candidates',[]) if int(x['task'])==18 and float(x['rect'][0])<45]"),
    ]
    for a,b in repl:
        if a in s:s=s.replace(a,b,1)
        elif b not in s:raise RuntimeError('prepare patch target missing: '+a)
    compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')

    bp=ROOT/'scripts'/'build_profile_2022.py'; bs=bp.read_text(encoding='utf-8')
    marker='def delayed_preview(names):'; i=bs.index(marker); head,tail=bs[:i],bs[i:]
    a="        if 'assetParts[' in s:\n"
    b="        if re.search(r'window\\.EKSAMIO_MATH_PROFILE\\.assetParts\\[[^\\n]+?\\]\\.push\\(',s):\n"
    if a in tail:tail=tail.replace(a,b,1)
    elif b not in tail:raise RuntimeError('delayed preview classifier target missing')
    bs=head+tail

    oldret="        return s\n    e.shell=shell22; e.runtime=runtime22"
    persistence=r'''        # Persistence hardening stays inside the existing 2022 learner state.
        s=s.replace("function save(){localStorage.setItem(C.storageKey,JSON.stringify(state))}function rnd", "function save(){localStorage.setItem(C.storageKey,JSON.stringify(state))}function syncCurrentInput(){const si=$('#mp-short'),li=$('#mp-long');if(si){const v=variantFor(state.current),chk=validate(v,si.value);state.answers[state.current]={value:si.value,valid:!!chk.valid}}if(li){state.answers[state.current]={text:li.value}}save()}function rnd")
        s=s.replace("b.onclick=()=>{state.current=+b.dataset.n;save();render()}", "b.onclick=()=>{syncCurrentInput();state.current=+b.dataset.n;save();render()}")
        s=s.replace("$('#mp-mark').onclick=()=>{state.marked[state.current]=!state.marked[state.current];save();renderGrid();render()}", "$('#mp-mark').onclick=()=>{syncCurrentInput();state.marked[state.current]=!state.marked[state.current];save();renderGrid();render()}")
        s=s.replace("$('#mp-prev').onclick=()=>{if(state.current>1){state.current--;save();render()}}", "$('#mp-prev').onclick=()=>{if(state.current>1){syncCurrentInput();state.current--;save();render()}}")
        s=s.replace("else{state.current++;save();render()}", "else{syncCurrentInput();state.current++;save();render()}")
        s=s.replace("forceVariant:(n,v)=>{state.variants[n]=v;state.current=n;save();if(!state.finished)render()}", "forceVariant:(n,v)=>{syncCurrentInput();state.variants[n]=v;state.current=n;save();if(!state.finished)render()}")
        s=s.replace("setCurrent:n=>{state.current=n;save();if(!state.finished)render()}", "setCurrent:n=>{syncCurrentInput();state.current=n;save();if(!state.finished)render()}")
        s=s.replace("window.addEventListener('pagehide',save);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')save()});", "window.addEventListener('pagehide',syncCurrentInput);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')syncCurrentInput()});")
        return s
    e.shell=shell22; e.runtime=runtime22'''
    if oldret not in bs:raise RuntimeError('runtime return patch target missing')
    bs=bs.replace(oldret,persistence,1)
    compile(bs,str(bp),'exec');bp.write_text(bs,encoding='utf-8')
    run([sys.executable,'-m','py_compile',p,bp,ROOT/'tests'/'test_profile_2022.py',ROOT/'audit'/'independent_audit_2022.py'])

def prebuild_assertions():
    src=REPO/'matematika-source-2022'/'ege-2022-matematika-profil-demoversiya.pdf'
    assert hashlib.sha256(src.read_bytes()).hexdigest()==SOURCE_SHA
    sl=json.loads((LOCK/'SOURCE-LOCK.json').read_text())
    ex=json.loads((LOCK/'EXAM-LOCK.json').read_text())
    ans=json.loads((LOCK/'ANSWER-LOCK.json').read_text())
    cr=json.loads((LOCK/'EXTENDED-CRITERIA-MAP.json').read_text())
    inv=json.loads((LOCK/'VISUAL-INVENTORY.json').read_text())
    fid=json.loads((LOCK/'VISUAL-FIDELITY-EVIDENCE.json').read_text())
    ids=json.loads((LOCK/'DEMO-ITEM-IDENTITY-MAP.json').read_text())
    assert sl['status']=='SOURCE_BYTES_AND_PAGE_MAP_LOCKED' and sl['year']==2022 and sl['level']=='профильный'
    assert ex['status']=='EXAM_LOCK_PASS' and ex['exam_structure']['task_count']==18 and ex['official_examples']['total_examples']==35
    assert ex['exam_structure']['short_task_range']==[1,11] and ex['exam_structure']['extended_task_range']==[12,18]
    assert ans['status']=='ANSWER_LOCK_PASS' and ans['short_examples']==28 and len(ans['answers'])==28
    assert cr['status']=='EXTENDED_CRITERIA_LOCK_PASS' and len(cr['tasks'])==7
    assert inv['status']=='VISUAL_PREBUILD_LOCK_PASS' and inv['conditions']==35 and inv['direct_exact_source_assets']==47 and inv['reconstructed_official_visuals']==0
    assert fid['pixel_identity_pass']==47 and fid['pixel_identity_fail']==0
    assert ids['status']=='HISTORICAL_IDENTITY_LOCK_PASS' and len(ids['items'])==35
    assert all(x['semantic_mapping_status']=='UNRESOLVED' and x['semantic_id'] is None for x in ids['items'])
    cond=[x for x in inv['assets'] if x['semantic_role']=='learner_condition']
    assert len(cond)==35 and len({(x['task'],x['variant']) for x in cond})==35
    print('STRICT PREBUILD ASSERTIONS PASS')

def browser(root:Path,port:int):
    out=open(f'/tmp/profile2022-http-{port}.log','w')
    srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],cwd=root,stdout=out,stderr=subprocess.STDOUT)
    try:
        time.sleep(2)
        env=os.environ.copy();env.update({
          'EKSAMIO_PACKAGE_ROOT':str(root),
          'EKSAMIO_PREVIEW_URL':f'http://127.0.0.1:{port}/{PREFIX}-PREVIEW.html',
          'EKSAMIO_DELAYED_PREVIEW_URL':f'http://127.0.0.1:{port}/{PREFIX}-DELAYED-T123-PREVIEW.html'})
        run([sys.executable,root/'tests'/'test_profile_2022.py'],env=env)
    finally:
        srv.terminate()
        try:srv.wait(timeout=5)
        except subprocess.TimeoutExpired:srv.kill()
        out.close()

def promote():
    blocks=sorted(ROOT.glob(f'{PREFIX}-T123-*.txt')); assert blocks
    mx=max(p.stat().st_size for p in blocks);assert mx<42500
    for name in [f'{PREFIX}-EXAM-DATA.json',f'{PREFIX}-INPUT-CONTRACT.json',f'{PREFIX}-EXAM-MAP.json',f'{PREFIX}-BUILD-EVIDENCE.json']:
        p=ROOT/name;d=json.loads(p.read_text(encoding='utf-8'));d['status']='READY_FOR_TILDA';d['browser_audit']='tests/evidence/profile-2022-browser-evidence.json';d['clean_zip_regression']='PASS';d['ui_parity_gate']='PASS';d['all_variant_asset_reliability_gate']='PASS';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=[
      'SOURCE_GATE: PASS — exact FIPI 2022 SOURCE/EXAM/ANSWER/CRITERIA locks',
      'VISUAL_SOURCE_GATE: PASS — 47/47 direct exact-source crops; reconstructed 0',
      'UI_PARITY_GATE: PASS — ФИПИ 2022 · официальный пример N for every forced variant and after reload',
      'ALL_VARIANT_ASSET_RELIABILITY_GATE: PASS — 35/35 first render + away/back + reload + rerender + delayed T123',
      'INTERACTION_GATE: PASS — 35/35 official examples real DOM',
      'SCORER_GATE: PASS — 28/28 correct+wrong',
      'STATE_RESTORE_GATE: PASS',
      'EXTENDED_UX_GATE: PASS — toolbar + own answer + exact FIPI solution/criteria + self-evaluation 7/7',
      f'TILDA_ATOMIC_GATE: PASS — {len(blocks)} T123, max {mx} bytes < 42500',
      'RESPONSIVE_GATE: PASS — 1280/768/390/360/320',
      'INDEPENDENT_AUDIT_GATE: PASS',
      'CLEAN_ZIP_REGRESSION_GATE: PASS',
      'FINAL_STATUS: READY_FOR_TILDA','READY_FOR_TILDA: YES','LIVE_GO: NO']
    (ROOT/f'{PREFIX}-PAGE-STATUS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def static_final(clean:Path):
    blocks=sorted(clean.glob(f'{PREFIX}-T123-*.txt'))
    nums=[int(re.search(r'T123-(\d+)\.txt$',p.name).group(1)) for p in blocks]
    assert nums==list(range(1,len(blocks)+1));assert max(p.stat().st_size for p in blocks)<42500
    for p in blocks:
        s=p.read_text(encoding='utf-8');assert s.count('<script')==s.count('</script>');assert s.count('<style')==s.count('</style>')
        for m in re.finditer(r'<script[^>]*>(.*?)</script>',s,re.S|re.I):
            with tempfile.NamedTemporaryFile('w',suffix='.js',delete=False) as f:f.write(m.group(1));n=f.name
            cp=subprocess.run(['node','--check',n],capture_output=True,text=True);Path(n).unlink(missing_ok=True);assert cp.returncode==0,(p.name,cp.stderr)
    st=(clean/f'{PREFIX}-PAGE-STATUS.txt').read_text(encoding='utf-8')
    for g in ['SOURCE_GATE: PASS','UI_PARITY_GATE: PASS','ALL_VARIANT_ASSET_RELIABILITY_GATE: PASS','SCORER_GATE: PASS — 28/28','STATE_RESTORE_GATE: PASS','EXTENDED_UX_GATE: PASS','TILDA_ATOMIC_GATE: PASS','RESPONSIVE_GATE: PASS','INDEPENDENT_AUDIT_GATE: PASS','CLEAN_ZIP_REGRESSION_GATE: PASS','READY_FOR_TILDA: YES']:assert g in st,g
    ev=json.loads((clean/'tests'/'evidence'/'profile-2022-browser-evidence.json').read_text(encoding='utf-8'));assert ev['status']=='PASS'

def extract(zip_path:Path,target:Path)->Path:
    shutil.rmtree(target,ignore_errors=True);target.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as z:z.extractall(target)
    return target/PREFIX

def main():
    restore();patch_sources()
    run([sys.executable,LOCK/'prepare_profile_2022.py','--repo-root','.']);prebuild_assertions()
    run([sys.executable,ROOT/'scripts'/'build_profile_2022.py'])
    browser(ROOT,8765)
    run([sys.executable,ROOT/'audit'/'independent_audit_2022.py',ROOT])
    run([sys.executable,ROOT/'scripts'/'build_profile_2022.py','--repack'])
    clean=extract(ZIP,Path('/tmp/profile2022-clean-v11'))
    run([sys.executable,ROOT/'audit'/'independent_audit_2022.py',clean,'--clean'])
    browser(clean,8766)
    promote();run([sys.executable,ROOT/'scripts'/'build_profile_2022.py','--repack'])
    final_clean=extract(ZIP,Path('/tmp/profile2022-final-v11'))
    run([sys.executable,ROOT/'audit'/'independent_audit_2022.py',final_clean,'--clean']);static_final(final_clean)
    shutil.copy2(ZIP,FINAL)
    digest=hashlib.sha256(FINAL.read_bytes()).hexdigest()
    (REPO/'PROFILE-MATH-2022-FINAL-SHA256.txt').write_text(f'{digest}  {FINAL.name}\n',encoding='utf-8')
    blocks=sorted(ROOT.glob(f'{PREFIX}-T123-*.txt'));mx=max(p.stat().st_size for p in blocks)
    (REPO/'PROFILE-MATH-2022-LATEST-BUILD-RUN.txt').write_text(f'Status: READY_FOR_TILDA\nArchive: {FINAL.name}\nArchive SHA256: {digest}\nSource SHA256: {SOURCE_SHA}\nTasks: 18\nOfficial examples: 35/35\nShort correct+wrong: 28/28\nDirect exact-source assets: 47/47\nReconstructed official visuals: 0\nT123: {len(blocks)} blocks; max {mx} bytes <42500\nTwo browser regressions: PASS\nIndependent source/runtime audit: PASS\n',encoding='utf-8')
    print('READY_FOR_TILDA',digest,FINAL,flush=True)
if __name__=='__main__':main()
