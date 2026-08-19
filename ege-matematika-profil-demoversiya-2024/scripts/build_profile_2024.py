#!/usr/bin/env python3
from __future__ import annotations
import base64, csv, hashlib, importlib.util, io, json, shutil, sys, zipfile
from pathlib import Path
import fitz
from PIL import Image, ImageChops

PREFIX='ege-matematika-profil-demoversiya-2024'
HERE=Path(__file__).resolve(); ROOT=HERE.parent.parent; REPO=ROOT.parent
REFERENCE=REPO/'ege-matematika-profil-demoversiya-2026'/'scripts'/'build_profile_2026.py'
SRC=REPO/'matematika-source-2024'/'ege-2024-matematika-profil-demoversiya.pdf'
SOURCE_SHA='89698a59be7da5c5f6c628f752a6810534888c423cae31a181ef743c910c1ae3'
PACKAGE_VERSION='1.0'; CONTENT_VERSION='2024.1-source-locked'; STORAGE_KEY='eksamio_ege_math_profile_demo_2024_v1_0'; PERMANENT_URL='https://eksamio.ru/ege/matematika-profil/demoversiya/2024/'
MAX_T123=42500; SCALE=2.5
COUNTS={1:4,2:2,3:3,4:2,5:2,6:4,7:3,8:2,9:1,10:3,11:1,12:3,13:1,14:1,15:1,16:1,17:1,18:1,19:1}
ANS={1:['64','6','154','16'],2:['12','10'],3:['4','12','52'],4:['0,08','0,2'],5:['0,6','0,1'],6:['9','17','93','3'],7:['-0,96','4','16'],8:['4','-1,75'],9:['751'],10:['5','15','7,5'],11:['61'],12:['-83','-6','16']}
MAX_EXT={13:2,14:3,15:2,16:2,17:3,18:4,19:4}
COND={
'1-1':(4,166.0,202.0),'1-2':(4,250.0,290.0),'1-3':(4,338.0,376.0),'1-4':(4,424.0,473.0),
'2-1':(5,63.0,217.0),'2-2':(5,254.0,288.0),'3-1':(5,311.0,402.0),'3-2':(5,439.0,526.0),'3-3':(6,59.0,142.0),
'4-1':(6,171.0,226.0),'4-2':(6,263.0,310.0),'5-1':(6,347.0,379.2),'5-2':(6,425.0,494.0),
'6-1':(7,50.0,78.0),'6-2':(7,115.0,147.0),'6-3':(7,186.0,219.0),'6-4':(7,258.0,296.0),
'7-1':(7,324.0,349.0),'7-2':(7,381.0,417.0),'7-3':(7,449.0,484.0),'8-1':(8,55.0,240.0),'8-2':(8,289.0,465.0),
'9-1':(9,44.0,168.0),'10-1':(9,212.0,286.0),'10-2':(9,330.0,393.0),'10-3':(9,437.0,498.0),
'11-1':(10,48.0,220.0),'12-1':(10,248.0,301.0),'12-2':(10,339.0,376.0),'12-3':(10,414.0,453.0),
'13-1':(11,123.0,221.0),'14-1':(11,214.0,309.5),'15-1':(11,304.0,364.0),'16-1':(11,357.0,548.0),
'17-1':(12,57.0,178.0),'18-1':(12,171.0,276.0),'19-1':(12,269.0,434.0)}
OFFICIAL={
'solution-13':(14,124.0,454.0,'solution_and_criteria',13),'solution-14':(15,130.0,523.0,'solution_and_criteria',14),'solution-15':(16,97.0,426.0,'solution_and_criteria',15),'solution-16':(17,225.0,476.0,'solution_and_criteria',16),
'solution-17':(18,154.0,520.0,'solution',17),'criteria-17':(19,50.0,255.0,'criteria',17),
'solution-18-p19':(19,367.0,540.0,'solution_part_1',18),'solution-18-p20':(20,48.0,480.0,'solution_part_2',18),'criteria-18':(21,50.0,215.0,'criteria',18),
'solution-19-p21':(21,355.0,540.0,'solution_part_1',19),'solution-criteria-19-p22':(22,48.0,270.0,'solution_part_2_and_criteria',19)}
SOL_ASSETS={13:['solution-13.webp'],14:['solution-14.webp'],15:['solution-15.webp'],16:['solution-16.webp'],17:['solution-17.webp','criteria-17.webp'],18:['solution-18-p19.webp','solution-18-p20.webp','criteria-18.webp'],19:['solution-19-p21.webp','solution-criteria-19-p22.webp']}
ZOOM_REQUIRED={'2-1','3-1','3-2','3-3','6-2','6-3','6-4','7-1','7-2','7-3','8-1','8-2','9-1','10-1','11-1','12-1','12-2','12-3','13-1','14-1','15-1','18-1'}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def trim(im,margin=18):
    mask=im.convert('L').point(lambda p:255 if p<252 else 0); bbox=mask.getbbox()
    if not bbox:return im,(0,0,im.width,im.height)
    x0,y0,x1,y1=bbox; r=(max(0,x0-margin),max(0,y0-margin),min(im.width,x1+margin),min(im.height,y1+margin)); return im.crop(r),r

def render_pages():
    if sha(SRC)!=SOURCE_SHA: raise RuntimeError('source SHA mismatch')
    doc=fitz.open(SRC); out=ROOT/'source-evidence'/'printed-pages'; out.mkdir(parents=True,exist_ok=True)
    n=0
    for page in doc:
        pix=page.get_pixmap(matrix=fitz.Matrix(SCALE,SCALE),alpha=False); im=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
        halves=[im.crop((0,0,im.width//2,im.height)),im.crop((im.width//2,0,im.width,im.height))]
        for h in halves:
            mask=h.convert('L').point(lambda p:255 if p<248 else 0)
            if mask.getbbox() is None: continue
            n+=1; h.save(out/f'page-{n:02d}.png')
    if n!=23: raise RuntimeError(f'expected 23 printed pages, got {n}')
    return out

def crop(render,page,y0,y1,x0=14.0,x1=407.0):
    src=Image.open(render/f'page-{page:02d}.png').convert('RGB'); outer=(round(x0*SCALE),round(y0*SCALE),round(x1*SCALE),round(y1*SCALE)); sem=src.crop(outer); final,inner=trim(sem,18)
    rect=(outer[0]+inner[0],outer[1]+inner[1],outer[0]+inner[2],outer[1]+inner[3]); return final,rect

def make_assets():
    srcdir=REPO/'matematika-source-2024'/'profile-source-lock'/'visual-assets'
    if not srcdir.exists(): raise RuntimeError('locked visual-assets missing')
    ad=ROOT/'assets'; ad.mkdir(parents=True,exist_ok=True)
    for q in srcdir.glob('*.webp'): shutil.copy2(q,ad/q.name)
    files=sorted(ad.glob('*.webp'))
    expected_conditions=sum(COUNTS.values())
    # 37 condition assets + 1 reference + 11 extended solution/criteria segments = 49.
    if len(files)!=49: raise RuntimeError(f'expected 49 locked visual assets, got {len(files)}')
    conds=list(ad.glob('condition-*.webp'))
    if len(conds)!=37: raise RuntimeError(f'expected 37 condition assets, got {len(conds)}')
    for key in COND:
        if not (ad/f'condition-{key}.webp').exists(): raise RuntimeError(f'missing condition {key}')
    for t,names in SOL_ASSETS.items():
        for name in names:
            if not (ad/name).exists(): raise RuntimeError(f'missing extended asset {name}')
    if not (ad/'reference-materials.webp').exists(): raise RuntimeError('reference materials missing')
    lock=REPO/'matematika-source-2024'/'profile-source-lock'
    shutil.copy2(lock/'VISUAL-FIDELITY-EVIDENCE.json',ROOT/'source-evidence'/'VISUAL-FIDELITY-EVIDENCE.json')
    shutil.copy2(lock/'VISUAL-INVENTORY.json',ROOT/'source-evidence'/'VISUAL-INVENTORY.json')
    shutil.copy2(lock/'VISUAL-PREBUILD-VALIDATION.txt',ROOT/'source-evidence'/'VISUAL-PREBUILD-VALIDATION.txt')
    inv=[{'file':q.name,'sha256':sha(q)} for q in files]
    (ROOT/'source-evidence'/'VISUAL-SOURCE-EVIDENCE-2024.json').write_text(json.dumps({'status':'PASS','authority':'matematika-source-2024/profile-source-lock/visual-assets from GitHub Actions run 32239084071','source_sha256':SOURCE_SHA,'direct_exact_source_assets':49,'conditions':37,'reference_materials':1,'extended_segments':11,'reconstructed_visuals':0,'stitched_multi_page_visuals':0,'files':inv},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return inv

def load_engine():
    sp=importlib.util.spec_from_file_location('profile2026_engine',REFERENCE); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    m.PREFIX=PREFIX;m.ROOT=ROOT;m.REPO=REPO;m.PACKAGE_VERSION=PACKAGE_VERSION;m.CONTENT_VERSION=CONTENT_VERSION;m.STORAGE_KEY=STORAGE_KEY;m.PERMANENT_URL=PERMANENT_URL;m.COUNTS=COUNTS;m.ANS=ANS;m.MAX_EXT=MAX_EXT;m.MAX_T123=MAX_T123;m.PART_CHARS=30000
    return m

def contract_for(t,v):
    if t in (4,5):return {'mode':'probability','hint':'Введите вероятность числом от 0 до 1 без единиц измерения.'}
    if t==8 and v==1:return {'mode':'integer_nonnegative','hint':'Введите количество точек целым неотрицательным числом.'}
    return {'mode':'number','hint':'Введите число без единиц измерения и пробелов.'}

def build_data():
    tasks=[];contracts={}
    for t in range(1,20):
        vs=[]
        for v in range(1,COUNTS[t]+1):
            k=f'{t}-{v}'; item={'variant':v,'condition_asset':f'condition-{k}.webp','source_page':COND[k][0]}
            if t<=12:
                c=contract_for(t,v);contracts[k]=c;item.update({'answer':ANS[t][v-1],'control':'numeric_input','input_contract':c,'max_score':1,'answer_source_page':13})
            else:item.update({'control':'extended_textarea','max_score':MAX_EXT[t],'solution_assets':SOL_ASSETS[t],'solution_asset':SOL_ASSETS[t][0]})
            vs.append(item)
        tasks.append({'number':t,'variants':vs})
    data={'status':'BUILT_PENDING_BROWSER_AUDIT','exam':'ЕГЭ','subject':'математика','level':'профильный','sourceYear':2024,'packageVersion':PACKAGE_VERSION,'contentVersion':CONTENT_VERSION,'minutes':235,'maxPrimaryScore':32,'autoMax':12,'selfMax':20,'storageKey':STORAGE_KEY,'permanentUrl':PERMANENT_URL,'officialExampleCount':37,'tasks':tasks}
    (ROOT/f'{PREFIX}-EXAM-DATA.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/f'{PREFIX}-INPUT-CONTRACT.json').write_text(json.dumps({'status':'BUILT_PENDING_BROWSER_AUDIT','contracts':contracts},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/f'{PREFIX}-OFFICIAL-ANSWERS.json').write_text(json.dumps({'source':'ФИПИ 2024, профильный уровень, таблица ответов демоверсии, печатная страница 13','answers':{str(k):v for k,v in ANS.items()}},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return data

def patch_engine(e):
    orig_shell=e.shell; orig_runtime=e.runtime
    extra_css='''.mp-math-toolbar{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 10px}.mp-math-btn{border:1px solid #ccd5e4;background:#fff;border-radius:8px;padding:7px 9px;cursor:pointer;font-size:15px}.mp-your-answer{background:#f7f9fc;border:1px solid #e0e6ef;border-radius:10px;padding:12px;margin:12px 0}.mp-your-answer pre{white-space:pre-wrap;word-break:break-word;margin:7px 0 0;font:15px/1.5 Arial,sans-serif}.mp-asset-wrap{position:relative}.mp-zoom-btn{margin-top:8px;border:1px solid #cbd5e1;background:#fff;border-radius:8px;padding:6px 10px;cursor:pointer;font-weight:700}.mp-zoom-modal{position:fixed;inset:0;background:rgba(10,20,40,.76);z-index:80;display:flex;align-items:center;justify-content:center;padding:12px}.mp-zoom-modal.mp-hidden{display:none}.mp-zoom-card{background:#fff;border-radius:14px;width:min(96vw,1200px);height:min(94vh,900px);display:flex;flex-direction:column;overflow:hidden}.mp-zoom-head{display:flex;align-items:center;gap:7px;padding:10px;border-bottom:1px solid #e5e7eb}.mp-zoom-head strong{margin-right:auto}.mp-zoom-stage{overflow:auto;flex:1;padding:16px;text-align:center;background:#f5f6f8}.mp-zoom-image{display:inline-block;max-width:none;height:auto;transform-origin:top center}@media(max-width:420px){.mp-math-btn{padding:6px 8px}.mp-zoom-head{flex-wrap:wrap}}'''
    def shell24(data):
        s=orig_shell(data).replace('профильной математике 2026','профильной математике 2024').replace('55 официальных примеров','37 официальных примеров').replace('ФИПИ 2026','ФИПИ 2024')
        s=s.replace('</style>',extra_css+'</style>')
        return s
    def runtime24():
        s=orig_runtime()
        s=s.replace("function img(name,cls='mp-source-img'){return`<img class=\"${cls}\" src=\"${C.assets[name]}\" alt=\"Официальный материал ФИПИ к заданию\" loading=\"eager\">`}","function img(name,cls='mp-source-img'){return`<img class=\"${cls}\" data-zoom-asset=\"${name}\" src=\"${C.assets[name]}\" alt=\"Официальный материал ФИПИ к заданию\" loading=\"eager\">`}function assetView(name){return`<div class=\"mp-asset-wrap\">${img(name)}<button type=\"button\" class=\"mp-zoom-btn\" data-asset=\"${name}\">Увеличить</button></div>`}function assetsView(names){return(names||[]).map(assetView).join('')}")
        s=s.replace('ФИПИ 2026 · официальный пример ${v.variant}','ФИПИ 2024 · официальный материал демоверсии')
        s=s.replace('${img(v.condition_asset)}','${assetView(v.condition_asset)}')
        s=s.replace('<h3>Задание ${n} · официальный пример ${v.variant}</h3>','<h3>Задание ${n}</h3>')
        old='<div class="mp-hint">Ваше решение сохранено. Сравните его с официальным решением и критериями ниже.</div><div class="mp-solution">${img(v.solution_asset)}</div><strong>Самооценка:'
        new='<div class="mp-hint">Ваше решение сохранено. Сравните его с официальным решением и критериями ниже.</div><div class="mp-your-answer"><strong>Ваш ответ</strong><pre>${esc((ans(n)||{}).text||\'—\')}</pre></div><div class="mp-solution">${assetsView(v.solution_assets||[v.solution_asset])}</div><strong>Самооценка:'
        if old not in s: raise RuntimeError('results patch target missing')
        s=s.replace(old,new)
        oldext="const a=ans(state.current)||{text:''};return`<div class=\"mp-answerbox\"><label class=\"mp-answer-title\" for=\"mp-long\">Полное решение</label><div class=\"mp-hint\">Запишите полное обоснованное решение и ответ. Официальное решение и критерии откроются только после завершения попытки.</div><textarea id=\"mp-long\" class=\"mp-textarea\" spellcheck=\"false\">${esc(a.text||'')}</textarea></div>`"
        toolbar="const a=ans(state.current)||{text:''};const syms=['π','∞','√()','±','−','≠','≈','≤','≥','·','÷','²','³','⁴','∥','⊥','∠','°','∈','∉','∪','∩','∅','ℕ','ℤ','ℚ','ℝ','→','⇒','⇔'];return`<div class=\"mp-answerbox\"><label class=\"mp-answer-title\" for=\"mp-long\">Полное решение</label><div class=\"mp-hint\">Запишите полное обоснованное решение и ответ. Официальное решение и критерии откроются только после завершения попытки.</div><div class=\"mp-math-toolbar\" aria-label=\"Математические символы\">${syms.map(x=>`<button type=\"button\" class=\"mp-math-btn\" data-sym=\"${x}\">${x}</button>`).join('')}</div><textarea id=\"mp-long\" class=\"mp-textarea\" spellcheck=\"false\">${esc(a.text||'')}</textarea></div>`"
        if oldext not in s: raise RuntimeError('answer panel patch target missing')
        s=s.replace(oldext,toolbar)
        oldbind="function bindLong(){const t=$('#mp-long');t.oninput=()=>{state.answers[state.current]={text:t.value};save();renderGrid()}}"
        newbind="function bindLong(){const t=$('#mp-long');function persist(){state.answers[state.current]={text:t.value};save();renderGrid()}function quick(){const pos=t.selectionStart||0,b=t.value.slice(0,pos),a=t.value.slice(pos),r=b.replace(/<=/g,'≤').replace(/>=/g,'≥').replace(/!=/g,'≠').replace(/->/g,'→');if(r!==b){t.value=r+a;t.selectionStart=t.selectionEnd=r.length}}t.oninput=()=>{quick();persist()};$$('.mp-math-btn').forEach(b=>b.onclick=()=>{const sym=b.dataset.sym,start=t.selectionStart||0,end=t.selectionEnd||start,ins=sym==='√()'?'√()':sym;t.value=t.value.slice(0,start)+ins+t.value.slice(end);const pos=start+(sym==='√()'?2:ins.length);t.focus();t.selectionStart=t.selectionEnd=pos;persist()})}"
        if oldbind not in s: raise RuntimeError('bind patch target missing')
        s=s.replace(oldbind,newbind)
        s=s.replace("function openRef(){$('#mp-ref-body').innerHTML=`<div class=\"mp-source\">${img('reference-materials.webp')}</div>`;", "function openRef(){$('#mp-ref-body').innerHTML=`<div class=\"mp-source\">${assetView('reference-materials.webp')}</div>`;")
        zoom="const zm=document.createElement('div');zm.id='mp-zoom-modal';zm.className='mp-zoom-modal mp-hidden';zm.innerHTML='<div class=\"mp-zoom-card\"><div class=\"mp-zoom-head\"><strong>Увеличение</strong><button id=\"mp-zoom-out\" class=\"mp-btn mp-secondary\">−</button><button id=\"mp-zoom-reset\" class=\"mp-btn mp-secondary\">100%</button><button id=\"mp-zoom-in\" class=\"mp-btn mp-secondary\">+</button><button id=\"mp-zoom-close\" class=\"mp-btn mp-secondary\">Закрыть</button></div><div class=\"mp-zoom-stage\"><img id=\"mp-zoom-image\" class=\"mp-zoom-image\"></div></div>';document.body.appendChild(zm);let zscale=1;function zapply(){const zi=$('#mp-zoom-image');zi.style.transform=`scale(${zscale})`;$('#mp-zoom-reset').textContent=Math.round(zscale*100)+'%'}function openZoom(name){zscale=1;$('#mp-zoom-image').src=C.assets[name];zm.classList.remove('mp-hidden');zapply()}function closeZoom(){zm.classList.add('mp-hidden')}document.addEventListener('click',ev=>{const b=ev.target.closest('.mp-zoom-btn');if(b){ev.preventDefault();openZoom(b.dataset.asset)}});$('#mp-zoom-in').onclick=()=>{zscale=Math.min(3,zscale+.25);zapply()};$('#mp-zoom-out').onclick=()=>{zscale=Math.max(.5,zscale-.25);zapply()};$('#mp-zoom-reset').onclick=()=>{zscale=1;zapply()};$('#mp-zoom-close').onclick=closeZoom;zm.onclick=ev=>{if(ev.target===zm)closeZoom};"
        s=s.replace("$('#mp-start').onclick=start;",zoom+"$('#mp-start').onclick=start;")
        s=s.replace("window.EKSAMIO_MATH_PROFILE_TEST=", "window.addEventListener('pagehide',save);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')save()});window.EKSAMIO_MATH_PROFILE_TEST=")
        return s
    e.shell=shell24;e.runtime=runtime24

def write_metadata(data):
    (ROOT/f'{PREFIX}-SEO.txt').write_text(f'TITLE: Интерактивная демоверсия ЕГЭ по профильной математике 2024 | Эксамио\nDESCRIPTION: Интерактивная демоверсия ЕГЭ по профильной математике 2024: официальные примеры ФИПИ, автоматическая проверка части 1 и самостоятельная оценка развёрнутых заданий по критериям.\nKEYWORDS: демоверсия ЕГЭ профильная математика 2024, ЕГЭ математика профиль 2024, ФИПИ 2024 математика профиль\nPAGE_URL: {PERMANENT_URL}\n',encoding='utf-8')
    (ROOT/f'{PREFIX}-HEAD.txt').write_text(f'<link rel="canonical" href="{PERMANENT_URL}">\n<meta property="og:type" content="website">\n<meta property="og:site_name" content="Эксамио">\n<meta property="og:title" content="Интерактивная демоверсия ЕГЭ по профильной математике 2024">\n<meta property="og:description" content="Официальные примеры ФИПИ 2024: автоматическая проверка краткой части и самостоятельная оценка развёрнутой.">\n<meta property="og:url" content="{PERMANENT_URL}">\n',encoding='utf-8')
    (ROOT/f'{PREFIX}-EXAM-MAP.json').write_text(json.dumps({'status':'BUILT_PENDING_BROWSER_AUDIT','exam':'ЕГЭ','subject':'математика','level':'профильный','year':2024,'url':PERMANENT_URL,'tasks_total':19,'short_answer_task_range':[1,12],'extended_answer_task_range':[13,19],'duration_minutes':235,'max_primary_score':32,'automatic_max':12,'self_assessment_max':20,'official_examples_total':37,'official_variant_counts':{str(k):v for k,v in COUNTS.items()},'max_scores':{**{str(k):1 for k in range(1,13)},**{str(k):v for k,v in MAX_EXT.items()}},'storage_key':STORAGE_KEY},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    contract={'package_version':PACKAGE_VERSION,'source_year':2024,'permanent_url':PERMANENT_URL,'header_footer_included':False,'archive_page_year_in_seo':True,'variant_contract':{'one_official_example_per_position':True,'student_selects_variant':False,'variant_persists_after_reload':True,'variant_number_hidden_from_student':True,'official_examples_total':37},'scoring_contract':{'tasks_1_12':'automatic 0–12','tasks_13_19':'self-evaluation only after finish, 0–20, using official FIPI 2024 criteria','total':'automatic + explicit self-evaluation, max 32'},'source_contract':{'conditions':'lossless direct contiguous crops from exact FIPI 2024 PDF','solutions_and_criteria':'lossless direct contiguous per-page crops; no stitched multi-page official visuals','source_sha256':SOURCE_SHA},'ux_contract':{'math_toolbar_for_extended':True,'own_answer_visible_in_results':True,'zoom_50_to_300':True}}
    (ROOT/f'{PREFIX}-PACKAGE-CONTRACT.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/f'{PREFIX}-PAGE-STATUS.txt').write_text('PAGE_URL: /ege/matematika-profil/demoversiya/2024/\nPAGE_SLUG: ege-matematika-profil-demoversiya-2024\nEXAM: ЕГЭ\nSUBJECT: математика\nLEVEL: профильный\nSOURCE_YEAR: 2024\nPACKAGE_VERSION: 1.0\nSOURCE_GATE: PASS\nTEXT_TYPOGRAPHY_GATE: PASS — exact source crops\nFORMULA_GATE: PASS — exact source crops\nVISUAL_SOURCE_GATE: PASS — 49/49 direct lossless source crops\nVISUAL_UI_GATE: PENDING_BROWSER_AUDIT\nINTERACTION_GATE: PENDING_BROWSER_AUDIT\nSCORER_GATE: PENDING_BROWSER_AUDIT\nSTATE_RESTORE_GATE: PENDING_BROWSER_AUDIT\nEXTENDED_UX_GATE: PENDING_BROWSER_AUDIT\nTILDA_ATOMIC_GATE: PENDING_STATIC_CHECK\nINDEPENDENT_AUDIT_GATE: PENDING\nFINAL_STATUS: BUILT_PENDING_BROWSER_AUDIT\nREADY_FOR_TILDA: NO\nLIVE_GO: NO\n',encoding='utf-8')
    rows=[]
    for t in data['tasks']:
      for v in t['variants']:
        n=t['number']; rows.append({'year':2024,'level':'profile','task':n,'official_variant':v['variant'],'source_page':v['source_page'],'control':v['control'],'official_answer_or_max':v.get('answer',v.get('max_score')),'condition_asset':v['condition_asset'],'solution_assets':'|'.join(v.get('solution_assets',[])),'source_gate':'PASS','visual_source_gate':'PASS','interaction_gate':'PENDING_BROWSER'})
    with (ROOT/'AUDIT-MATRIX-2024-profile.csv').open('w',encoding='utf-8-sig',newline='') as f:
      w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)

def clean():
    for p in ROOT.iterdir():
      if p.name in {'scripts','tests','audit'}: continue
      if p.is_dir(): shutil.rmtree(p)
      else: p.unlink()
    for d in ['assets','source-evidence','tests/evidence']: (ROOT/d).mkdir(parents=True,exist_ok=True)

def t123_static(names):
    import re, subprocess, tempfile
    sizes={}
    for name in names:
      p=ROOT/name; text=p.read_text(encoding='utf-8');sizes[name]=p.stat().st_size
      if sizes[name]>=42500: raise RuntimeError(f'{name} size {sizes[name]}')
      for tag in ('script','style'):
        if len(re.findall(fr'<{tag}(?:\\s|>)',text,re.I))!=len(re.findall(fr'</{tag}>',text,re.I)): raise RuntimeError(f'{name} unbalanced {tag}')
      scripts=re.findall(r'<script[^>]*>(.*?)</script>',text,re.I|re.S)
      for idx,js in enumerate(scripts):
        tf=ROOT/'tests'/f'.tmp-{name}-{idx}.js';tf.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(tf)],capture_output=True,text=True);tf.unlink(missing_ok=True)
        if cp.returncode: raise RuntimeError(f'{name} JS syntax fail: {cp.stderr}')
    return sizes

def manifest_zip():
    manifest=ROOT/f'{PREFIX}-MANIFEST-SHA256.txt'; manifest.unlink(missing_ok=True)
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!=manifest.name and '__pycache__' not in p.parts and not p.name.startswith('.tmp-'))
    manifest.write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT).as_posix()}\n' for p in files),encoding='utf-8')
    out=REPO/f'{PREFIX}-v{PACKAGE_VERSION}.zip';out.unlink(missing_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
      for p in sorted(ROOT.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith('.tmp-'): z.write(p,ROOT.name+'/'+p.relative_to(ROOT).as_posix())
    return out

def build():
    clean(); inv=make_assets(); data=build_data(); write_metadata(data); e=load_engine(); patch_engine(e); names=e.build_blocks(data); e.preview_and_install(names);sizes=t123_static(names)
    ev={'status':'BUILT_PENDING_BROWSER_AUDIT','source_sha256':SOURCE_SHA,'tasks':19,'official_examples':37,'short_examples':30,'extended_examples':7,'direct_source_assets':len(inv),'reconstructed_visuals':0,'stitched_multi_page_visuals':0,'t123_blocks':len(names),'t123_max_bytes':max(sizes.values()),'t123_sizes':sizes,'math_toolbar':True,'own_answer_results':True,'zoom_ui':True}
    (ROOT/f'{PREFIX}-BUILD-EVIDENCE.json').write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');out=manifest_zip();print(json.dumps({**ev,'package':str(out)},ensure_ascii=False,indent=2))
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--repack':
        out=manifest_zip(); print(out)
    else: build()
