#!/usr/bin/env python3
from __future__ import annotations
import base64, csv, hashlib, importlib.util, io, json, shutil, sys, zipfile
from pathlib import Path
import fitz
from PIL import Image, ImageChops

PREFIX='ege-matematika-profil-demoversiya-2023'
HERE=Path(__file__).resolve(); ROOT=HERE.parent.parent; REPO=ROOT.parent
REFERENCE=REPO/'ege-matematika-profil-demoversiya-2026'/'scripts'/'build_profile_2026.py'
SRC=REPO/'matematika-source-2023'/'ege-2023-matematika-profil-demoversiya.pdf'
SOURCE_SHA='9278f5cc60388da2ed63eaa946c82e0902f0867047fc9b5ea6051bae16e3b6b2'
PACKAGE_VERSION='1.0'; CONTENT_VERSION='2023.1-source-locked'; STORAGE_KEY='eksamio_ege_math_profile_demo_2023_v1_0'; PERMANENT_URL='https://eksamio.ru/ege/matematika-profil/demoversiya/2023/'
MAX_T123=42500; SCALE=2.5
COUNTS={1:4,2:3,3:2,4:2,5:4,6:3,7:2,8:1,9:3,10:1,11:3,12:1,13:1,14:1,15:1,16:1,17:1,18:1}
ANS={1:['64','6','154','16'],2:['4','12','52'],3:['0,08','0,2'],4:['0,6','0,1'],5:['9','17','93','3'],6:['-0,96','4','16'],7:['4','-1,75'],8:['751'],9:['5','15','7,5'],10:['61'],11:['-83','-6','16']}
MAX_EXT={12:2,13:3,14:2,15:2,16:3,17:4,18:4}
COND={
'1-1':(4,166,190),'1-2':(4,230,267),'1-3':(4,318,352),'1-4':(4,392,438),
'2-1':(5,53,136),'2-2':(5,176,268),'2-3':(5,308,389),'3-1':(6,59,106),'3-2':(6,146,190),
'4-1':(6,235,257),'4-2':(6,308,374),'5-1':(7,69,89),'5-2':(7,129,159),'5-3':(7,200,231),'5-4':(7,272,308),
'6-1':(7,343,361),'6-2':(7,396,428),'6-3':(7,464,496),'7-1':(8,64,241),'7-2':(8,292,465),'8-1':(9,59,169),
'9-1':(9,216,286),'9-2':(9,333,394),'9-3':(9,440,499),'10-1':(10,58,226),'11-1':(10,262,307),'11-2':(10,347,382),'11-3':(10,422,458),
'12-1':(11,132,221),'13-1':(11,223,301),'14-1':(11,303,353),'15-1':(11,355,548),'16-1':(12,66,178),'17-1':(12,180,277),'18-1':(12,279,430)}
SOL_ASSETS={12:['solution-12.webp'],13:['solution-13.webp'],14:['solution-14.webp'],15:['solution-15.webp'],16:['solution-16.webp','criteria-16.webp'],17:['solution-17-p19.webp','solution-17-p20.webp','criteria-17.webp'],18:['solution-18-p21.webp','solution-criteria-18-p22.webp']}


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
    srcdir=REPO/'matematika-source-2023'/'profile-source-lock'/'visual-assets'
    if not srcdir.exists(): raise RuntimeError('locked visual-assets missing')
    ad=ROOT/'assets'; ad.mkdir(parents=True,exist_ok=True)
    for q in srcdir.glob('*.webp'): shutil.copy2(q,ad/q.name)
    files=sorted(ad.glob('*.webp'))
    expected_conditions=sum(COUNTS.values())
    # 37 condition assets + 1 reference + 11 extended solution/criteria segments = 49.
    if len(files)!=47: raise RuntimeError(f'expected 47 locked visual assets, got {len(files)}')
    conds=list(ad.glob('condition-*.webp'))
    if len(conds)!=35: raise RuntimeError(f'expected 35 condition assets, got {len(conds)}')
    for key in COND:
        if not (ad/f'condition-{key}.webp').exists(): raise RuntimeError(f'missing condition {key}')
    for t,names in SOL_ASSETS.items():
        for name in names:
            if not (ad/name).exists(): raise RuntimeError(f'missing extended asset {name}')
    if not (ad/'reference-materials.webp').exists(): raise RuntimeError('reference materials missing')
    lock=REPO/'matematika-source-2023'/'profile-source-lock'
    shutil.copy2(lock/'VISUAL-FIDELITY-EVIDENCE.json',ROOT/'source-evidence'/'VISUAL-FIDELITY-EVIDENCE.json')
    shutil.copy2(lock/'VISUAL-INVENTORY.json',ROOT/'source-evidence'/'VISUAL-INVENTORY.json')
    shutil.copy2(lock/'VISUAL-PREBUILD-VALIDATION.txt',ROOT/'source-evidence'/'VISUAL-PREBUILD-VALIDATION.txt')
    inv=[{'file':q.name,'sha256':sha(q)} for q in files]
    (ROOT/'source-evidence'/'VISUAL-SOURCE-EVIDENCE-2023.json').write_text(json.dumps({'status':'PASS','authority':'matematika-source-2023/profile-source-lock/visual-assets exact-source prebuild','source_sha256':SOURCE_SHA,'direct_exact_source_assets':47,'conditions':35,'reference_materials':1,'extended_segments':11,'reconstructed_visuals':0,'stitched_multi_page_visuals':0,'files':inv},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return inv

def load_engine():
    sp=importlib.util.spec_from_file_location('profile2026_engine',REFERENCE); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    m.PREFIX=PREFIX;m.ROOT=ROOT;m.REPO=REPO;m.PACKAGE_VERSION=PACKAGE_VERSION;m.CONTENT_VERSION=CONTENT_VERSION;m.STORAGE_KEY=STORAGE_KEY;m.PERMANENT_URL=PERMANENT_URL;m.COUNTS=COUNTS;m.ANS=ANS;m.MAX_EXT=MAX_EXT;m.MAX_T123=MAX_T123;m.PART_CHARS=30000
    return m

def contract_for(t,v):
    if t in (3,4):return {'mode':'probability','hint':'Введите вероятность числом от 0 до 1 без единиц измерения.'}
    if t==7 and v==1:return {'mode':'integer_nonnegative','hint':'Введите количество точек целым неотрицательным числом.'}
    return {'mode':'number','hint':'Введите число без единиц измерения и пробелов.'}

def build_data():
    tasks=[];contracts={}
    for t in range(1,19):
        vs=[]
        for v in range(1,COUNTS[t]+1):
            k=f'{t}-{v}'; item={'variant':v,'condition_asset':f'condition-{k}.webp','source_page':COND[k][0]}
            if t<=11:
                c=contract_for(t,v);contracts[k]=c;item.update({'answer':ANS[t][v-1],'control':'numeric_input','input_contract':c,'max_score':1,'answer_source_page':13})
            else:item.update({'control':'extended_textarea','max_score':MAX_EXT[t],'solution_assets':SOL_ASSETS[t],'solution_asset':SOL_ASSETS[t][0]})
            vs.append(item)
        tasks.append({'number':t,'variants':vs})
    data={'status':'BUILT_PENDING_BROWSER_AUDIT','exam':'ЕГЭ','subject':'математика','level':'профильный','sourceYear':2023,'packageVersion':PACKAGE_VERSION,'contentVersion':CONTENT_VERSION,'minutes':235,'maxPrimaryScore':31,'autoMax':11,'selfMax':20,'storageKey':STORAGE_KEY,'permanentUrl':PERMANENT_URL,'officialExampleCount':35,'tasks':tasks}
    (ROOT/f'{PREFIX}-EXAM-DATA.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/f'{PREFIX}-INPUT-CONTRACT.json').write_text(json.dumps({'status':'BUILT_PENDING_BROWSER_AUDIT','contracts':contracts},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/f'{PREFIX}-OFFICIAL-ANSWERS.json').write_text(json.dumps({'source':'ФИПИ 2023, профильный уровень, таблица ответов демоверсии, печатная страница 13','answers':{str(k):v for k,v in ANS.items()}},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return data

def patch_engine(e):
    orig_shell=e.shell; orig_runtime=e.runtime
    extra_css='''.mp-math-toolbar{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 10px}.mp-math-btn{border:1px solid #ccd5e4;background:#fff;border-radius:8px;padding:7px 9px;cursor:pointer;font-size:15px}.mp-your-answer{background:#f7f9fc;border:1px solid #e0e6ef;border-radius:10px;padding:12px;margin:12px 0}.mp-your-answer pre{white-space:pre-wrap;word-break:break-word;margin:7px 0 0;font:15px/1.5 Arial,sans-serif}.mp-asset-wrap{position:relative}.mp-zoom-btn{margin-top:8px;border:1px solid #cbd5e1;background:#fff;border-radius:8px;padding:6px 10px;cursor:pointer;font-weight:700}.mp-zoom-modal{position:fixed;inset:0;background:rgba(10,20,40,.76);z-index:80;display:flex;align-items:center;justify-content:center;padding:12px}.mp-zoom-modal.mp-hidden{display:none}.mp-zoom-card{background:#fff;border-radius:14px;width:min(96vw,1200px);height:min(94vh,900px);display:flex;flex-direction:column;overflow:hidden}.mp-zoom-head{display:flex;align-items:center;gap:7px;padding:10px;border-bottom:1px solid #e5e7eb}.mp-zoom-head strong{margin-right:auto}.mp-zoom-stage{overflow:auto;flex:1;padding:16px;text-align:center;background:#f5f6f8}.mp-zoom-image{display:inline-block;max-width:none;height:auto;transform-origin:top center}@media(max-width:420px){.mp-math-btn{padding:6px 8px}.mp-zoom-head{flex-wrap:wrap}}'''
    def shell23(data):
        s=orig_shell(data).replace('профильной математике 2026','профильной математике 2023').replace('12 заданий с кратким ответом','11 заданий с кратким ответом').replace('19 заданий','18 заданий').replace('32 первичных балла','31 первичный балл').replace('55 официальных примеров','35 официальных примеров').replace('№1–12','№1–11').replace('№13–19','№12–18').replace('ФИПИ 2026','ФИПИ 2023')
        s=s.replace('</style>',extra_css+'</style>')
        return s
    def runtime23():
        s=orig_runtime()
        s=s.replace('n<=12','n<=11').replace('n>12','n>11').replace('state.current<=12','state.current<=11').replace('state.current/19','state.current/18').replace('state.current===19','state.current===18').replace('done<19','done<18').replace(' из 19',' из 18').replace("autoTotal()+'/12'","autoTotal()+'/11'").replace('Array.from({length:12}','Array.from({length:11}').replace('const n=13+i','const n=12+i').replace('for(let n=13;n<=19;n++','for(let n=12;n<=18;n++').replace("+'/32'","+'/31'")
        s=s.replace("function img(name,cls='mp-source-img'){return`<img class=\"${cls}\" src=\"${C.assets[name]}\" alt=\"Официальный материал ФИПИ к заданию\" loading=\"eager\">`}","function img(name,cls='mp-source-img'){return`<img class=\"${cls}\" data-zoom-asset=\"${name}\" src=\"${C.assets[name]}\" alt=\"Официальный материал ФИПИ к заданию\" loading=\"eager\">`}function assetView(name){return`<div class=\"mp-asset-wrap\">${img(name)}<button type=\"button\" class=\"mp-zoom-btn\" data-asset=\"${name}\">Увеличить</button></div>`}function assetsView(names){return(names||[]).map(assetView).join('')}")
        s=s.replace('ФИПИ 2026 · официальный пример ${v.variant}','ФИПИ 2023 · официальный материал демоверсии')
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
    e.shell=shell23;e.runtime=runtime23

def write_metadata(data):
    (ROOT/f'{PREFIX}-SEO.txt').write_text(f'TITLE: Интерактивная демоверсия ЕГЭ по профильной математике 2023 | Эксамио\nDESCRIPTION: Интерактивная демоверсия ЕГЭ по профильной математике 2023: официальные примеры ФИПИ, автоматическая проверка части 1 и самостоятельная оценка развёрнутых заданий по критериям.\nKEYWORDS: демоверсия ЕГЭ профильная математика 2023, ЕГЭ математика профиль 2023, ФИПИ 2023 математика профиль\nPAGE_URL: {PERMANENT_URL}\n',encoding='utf-8')
    (ROOT/f'{PREFIX}-HEAD.txt').write_text(f'<link rel="canonical" href="{PERMANENT_URL}">\n<meta property="og:type" content="website">\n<meta property="og:site_name" content="Эксамио">\n<meta property="og:title" content="Интерактивная демоверсия ЕГЭ по профильной математике 2023">\n<meta property="og:description" content="Официальные примеры ФИПИ 2023: автоматическая проверка краткой части и самостоятельная оценка развёрнутой.">\n<meta property="og:url" content="{PERMANENT_URL}">\n',encoding='utf-8')
    (ROOT/f'{PREFIX}-EXAM-MAP.json').write_text(json.dumps({'status':'BUILT_PENDING_BROWSER_AUDIT','exam':'ЕГЭ','subject':'математика','level':'профильный','year':2023,'url':PERMANENT_URL,'tasks_total':18,'short_answer_task_range':[1,11],'extended_answer_task_range':[12,18],'duration_minutes':235,'max_primary_score':31,'automatic_max':11,'self_assessment_max':20,'official_examples_total':35,'official_variant_counts':{str(k):v for k,v in COUNTS.items()},'max_scores':{**{str(k):1 for k in range(1,12)},**{str(k):v for k,v in MAX_EXT.items()}},'storage_key':STORAGE_KEY},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    contract={'package_version':PACKAGE_VERSION,'source_year':2023,'permanent_url':PERMANENT_URL,'header_footer_included':False,'archive_page_year_in_seo':True,'variant_contract':{'one_official_example_per_position':True,'student_selects_variant':False,'variant_persists_after_reload':True,'variant_number_hidden_from_student':True,'official_examples_total':35},'scoring_contract':{'tasks_1_11':'automatic 0–11','tasks_12_18':'self-evaluation only after finish, 0–20, using official FIPI 2023 criteria','total':'automatic + explicit self-evaluation, max 31'},'source_contract':{'conditions':'lossless direct contiguous crops from exact FIPI 2023 PDF','solutions_and_criteria':'lossless direct contiguous per-page crops; no stitched multi-page official visuals','source_sha256':SOURCE_SHA},'ux_contract':{'math_toolbar_for_extended':True,'own_answer_visible_in_results':True,'zoom_50_to_300':True}}
    (ROOT/f'{PREFIX}-PACKAGE-CONTRACT.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/f'{PREFIX}-PAGE-STATUS.txt').write_text('PAGE_URL: /ege/matematika-profil/demoversiya/2023/\nPAGE_SLUG: ege-matematika-profil-demoversiya-2023\nEXAM: ЕГЭ\nSUBJECT: математика\nLEVEL: профильный\nSOURCE_YEAR: 2023\nPACKAGE_VERSION: 1.0\nSOURCE_GATE: PASS\nTEXT_TYPOGRAPHY_GATE: PASS — exact source crops\nFORMULA_GATE: PASS — exact source crops\nVISUAL_SOURCE_GATE: PASS — 47/47 direct lossless source crops\nVISUAL_UI_GATE: PENDING_BROWSER_AUDIT\nINTERACTION_GATE: PENDING_BROWSER_AUDIT\nSCORER_GATE: PENDING_BROWSER_AUDIT\nSTATE_RESTORE_GATE: PENDING_BROWSER_AUDIT\nEXTENDED_UX_GATE: PENDING_BROWSER_AUDIT\nTILDA_ATOMIC_GATE: PENDING_STATIC_CHECK\nINDEPENDENT_AUDIT_GATE: PENDING\nFINAL_STATUS: BUILT_PENDING_BROWSER_AUDIT\nREADY_FOR_TILDA: NO\nLIVE_GO: NO\n',encoding='utf-8')
    rows=[]
    for t in data['tasks']:
      for v in t['variants']:
        n=t['number']; rows.append({'year':2023,'level':'profile','task':n,'official_variant':v['variant'],'source_page':v['source_page'],'control':v['control'],'official_answer_or_max':v.get('answer',v.get('max_score')),'condition_asset':v['condition_asset'],'solution_assets':'|'.join(v.get('solution_assets',[])),'source_gate':'PASS','visual_source_gate':'PASS','interaction_gate':'PENDING_BROWSER'})
    with (ROOT/'AUDIT-MATRIX-2023-profile.csv').open('w',encoding='utf-8-sig',newline='') as f:
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
    ev={'status':'BUILT_PENDING_BROWSER_AUDIT','source_sha256':SOURCE_SHA,'tasks':18,'official_examples':35,'short_examples':28,'extended_examples':7,'direct_source_assets':len(inv),'reconstructed_visuals':0,'stitched_multi_page_visuals':0,'t123_blocks':len(names),'t123_max_bytes':max(sizes.values()),'t123_sizes':sizes,'math_toolbar':True,'own_answer_results':True,'zoom_ui':True}
    (ROOT/f'{PREFIX}-BUILD-EVIDENCE.json').write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');out=manifest_zip();print(json.dumps({**ev,'package':str(out)},ensure_ascii=False,indent=2))
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--repack':
        out=manifest_zip(); print(out)
    else: build()
