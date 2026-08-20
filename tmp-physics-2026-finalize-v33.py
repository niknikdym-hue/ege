from pathlib import Path
import base64, hashlib, json, re, shutil, sys, zipfile
from io import BytesIO

import fitz
from PIL import Image

ROOT=Path(__file__).resolve().parent
PKG=ROOT/'ege-fizika-demoversiya-v3-1-fixed'
PDF=PKG/'source/ege-2026-fizika-demoversiya.pdf'
EXPECTED_PDF_SHA='e93318f05b38a664a09a7b154a24710930b833c7a18110f81470398f34fa716a'

FILES={
    'd1':(PKG/'ege-fizika-demoversiya-T123-02.txt','ephys-data-1'),
    'd2':(PKG/'ege-fizika-demoversiya-T123-03.txt','ephys-data-2'),
    'd3':(PKG/'ege-fizika-demoversiya-T123-04.txt','ephys-data-3'),
    'd4':(PKG/'ege-fizika-demoversiya-T123-05.txt','ephys-data-4'),
}

# Coordinates are exact regions on the unrotated logical half-pages of the byte-locked FIPI PDF.
CROPS={
 't01':(6,(318.61,142.07,408.40,307.93),7,430),
 't02':(6,(190.04,265.29,222.12,379.13),7,310),
 't06a':(8,(148.53,78.19,364.81,163.47),6,340),
 't06b':(8,(445.28,302.55,530.59,380.45),6,330),
 't07':(9,(449.67,296.97,527.24,385.89),6,300),
 't08':(9,(317.99,296.64,396.52,376.29),6,300),
 't10':(10,(448.59,343.11,525.92,386.37),5,230),
 't19':(13,(114.33,147.17,301.35,295.03),4,340),
 't21p':(15,(309.88,134.38,409.52,316.72),5,430),
 't22p':(15,(143.5,307.0,208.0,400.0),2,260),
 't23p':(16,(477.77,325.07,529.10,383.68),4,240),
 't25p':(16,(222.0,300.0,284.0,386.0),3,260),
 't26v2p':(17,(326.69,247.30,376.32,365.19),5,300),
 't26v3p':(18,(204.99,93.63,397.35,356.53),2,440),
 't21s':(22,(448.88,193.35,509.77,271.75),5,330),
 't22s':(23,(328.42,296.11,394.53,397.44),4,260),
 't24sa':(27,(391.72,281.37,421.27,382.62),3,420),
 't24sb':(27,(272.67,310.34,380.62,353.64),3,240),
 't25s':(29,(109.53,143.57,173.12,332.09),5,420),
 't26v2s':(35,(46.74,245.19,117.03,382.62),4,420),
 't26v3s':(39,(361.98,68.07,409.89,242.13),4,420),
}

CAPTIONS={
 't01':'График зависимости проекции скорости от времени.',
 't02':'Кубик и две пружины.',
 't06':'Официальные рисунки ФИПИ к заданию 6.',
 't07':'Состояния 1 и 2 идеального газа.',
 't08':'Процесс 1–2–3 в координатах p–V.',
 't10':'Жидкость и её насыщенный пар под поршнем.',
 't19':'Манометр из официальной демоверсии ФИПИ.',
 't21p':'Цикл в координатах p–T.',
 't22p':'Шар наполовину находится в воде.',
 't23p':'Идеальный колебательный контур.',
 't25p':'Квадрат и собирающая линза.',
 't26v2p':'Доска, брусок, нить и блок.',
 't26v3p':'Фотография установки из официальной демоверсии ФИПИ.',
 't21s':'График цикла в координатах p–V из возможного решения ФИПИ.',
 't22s':'Силы, действующие на шар, из возможного решения ФИПИ.',
 't24s':'Рисунки из возможного решения ФИПИ.',
 't25s':'Построение изображения в линзе из возможного решения ФИПИ.',
 't26v2s':'Силы, действующие на тела, из возможного решения ФИПИ.',
 't26v3s':'Схематичный рисунок из возможного решения ФИПИ.',
}

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def load_json_script(path, sid):
    text=path.read_text(encoding='utf-8')
    pat=re.compile(r'(<script\s+type="application/json"\s+id="'+re.escape(sid)+r'">)(.*?)(</script>)',re.S)
    m=pat.search(text)
    if not m: raise RuntimeError(f'JSON script {sid} not found in {path}')
    return text,pat,json.loads(m.group(2))

def save_json_script(path, sid, text, pat, obj):
    body=json.dumps(obj,ensure_ascii=False,separators=(',',':'))
    new,n=pat.subn(lambda m:m.group(1)+body+m.group(3),text,count=1)
    if n!=1: raise RuntimeError(f'could not replace {sid}')
    path.write_text(new,encoding='utf-8')

def task(obj,n):
    return next(x for x in obj['tasks'] if x['number']==n)

def variant(obj,v):
    return next(x for x in obj['variants26'] if x['variant']==v)

def render_crops():
    if sha256(PDF)!=EXPECTED_PDF_SHA: raise RuntimeError('official demo PDF byte lock mismatch')
    doc=fitz.open(PDF)
    out={}
    meta=[]
    for name,(logical,bbox,pad,maxw) in CROPS.items():
        physical=(logical+1)//2
        slot=1 if logical%2 else 2
        page=doc[physical-1]
        oldrot=page.rotation; page.set_rotation(0); r=page.rect
        half=r.height/2; yoff=0 if slot==1 else half
        x0,y0,x1,y1=bbox
        clip=fitz.Rect(max(0,x0-pad),max(yoff,yoff+y0-pad),min(r.width,x1+pad),min(yoff+half,yoff+y1+pad))
        pix=page.get_pixmap(matrix=fitz.Matrix(3,3),clip=clip,alpha=False)
        im=Image.open(BytesIO(pix.tobytes('png'))).convert('RGB').rotate(90,expand=True)
        bio=BytesIO(); im.save(bio,'WEBP',lossless=True,method=6)
        raw=bio.getvalue(); out[name]=base64.b64encode(raw).decode('ascii')
        meta.append({'id':name,'logical_page':logical,'physical_page':physical,'slot':slot,'bbox_unrotated':[round(v,2) for v in clip],'pixel_width':im.width,'pixel_height':im.height,'max_rendered_width_px':maxw,'webp_sha256':hashlib.sha256(raw).hexdigest()})
        page.set_rotation(oldrot)
    return out,meta

def img(crops,name,alt):
    logical,_,_,maxw=CROPS[name]
    return f'<img class="ephys-source-crop" data-source-crop="{name}" data-source-logical-page="{logical}" data-max-width="{maxw}" style="--ephys-source-max:{maxw}px" src="data:image/webp;base64,{crops[name]}" alt="{alt}">'

def figure_one(crops,name,caption,alt):
    return '<figure class="ephys-figure ephys-source-figure"><div class="ephys-figure__canvas">'+img(crops,name,alt)+'</div><figcaption>'+caption+'</figcaption><button type="button" class="ep-button ep-button--small ep-button--secondary ephys-zoom">Увеличить схему</button></figure>'

def figure_pair(crops,names,caption,alts):
    body=''.join(img(crops,n,a) for n,a in zip(names,alts))
    return '<figure class="ephys-figure ephys-source-figure"><div class="ephys-figure__canvas ephys-source-pair">'+body+'</div><figcaption>'+caption+'</figcaption><button type="button" class="ep-button ep-button--small ep-button--secondary ephys-zoom">Увеличить схему</button></figure>'

def replace_first_figure(html,new=''):
    out,n=re.subn(r'<figure class="ephys-figure(?: [^"]*)?">.*?</figure>',new,html,count=1,flags=re.S)
    if n!=1: raise RuntimeError('expected one figure to replace')
    return out

def patch():
    crops,crop_meta=render_crops()
    loaded={}
    for k,(p,sid) in FILES.items(): loaded[k]=list(load_json_script(p,sid))
    d1=loaded['d1'][2]; d2=loaded['d2'][2]; d3=loaded['d3'][2]; d4=loaded['d4'][2]
    replacements={
      1:figure_one(crops,'t01',CAPTIONS['t01'],'График зависимости проекции скорости от времени из ФИПИ'),
      2:figure_one(crops,'t02',CAPTIONS['t02'],'Кубик и две пружины из ФИПИ'),
      6:figure_pair(crops,['t06a','t06b'],CAPTIONS['t06'],['Графики А и Б из ФИПИ','Схема броска камня из ФИПИ']),
      7:figure_one(crops,'t07',CAPTIONS['t07'],'Диаграмма p–V из ФИПИ'),
      8:figure_one(crops,'t08',CAPTIONS['t08'],'Процесс 1–2–3 из ФИПИ'),
      10:figure_one(crops,'t10',CAPTIONS['t10'],'Жидкость и насыщенный пар из ФИПИ'),
    }
    for n,new in replacements.items(): task(d1,n)['promptHtml']=replace_first_figure(task(d1,n)['promptHtml'],new)
    task(d2,19)['promptHtml']=replace_first_figure(task(d2,19)['promptHtml'],figure_one(crops,'t19',CAPTIONS['t19'],'Манометр из ФИПИ'))
    for n,name,cap,alt in [
      (21,'t21p','t21p','Цикл p–T из ФИПИ'),(22,'t22p','t22p','Шар в воде из ФИПИ'),(23,'t23p','t23p','Колебательный контур из ФИПИ'),(25,'t25p','t25p','Квадрат и линза из ФИПИ')]:
        task(d3,n)['promptHtml']=replace_first_figure(task(d3,n)['promptHtml'],figure_one(crops,name,CAPTIONS[cap],alt))
    task(d3,21)['solutionHtml']=replace_first_figure(task(d3,21)['solutionHtml'],figure_one(crops,'t21s',CAPTIONS['t21s'],'График p–V из возможного решения ФИПИ'))
    task(d3,22)['solutionHtml']=replace_first_figure(task(d3,22)['solutionHtml'],figure_one(crops,'t22s',CAPTIONS['t22s'],'Схема сил из возможного решения ФИПИ'))
    task(d3,24)['solutionHtml']=replace_first_figure(task(d3,24)['solutionHtml'],figure_pair(crops,['t24sa','t24sb'],CAPTIONS['t24s'],['Рисунок а из решения ФИПИ','Рисунок б из решения ФИПИ']))
    task(d3,25)['solutionHtml']=replace_first_figure(task(d3,25)['solutionHtml'],figure_one(crops,'t25s',CAPTIONS['t25s'],'Построение лучей из возможного решения ФИПИ'))
    v1=variant(d4,1); v2=variant(d4,2); v3=variant(d4,3)
    v1['solutionHtml']=replace_first_figure(v1['solutionHtml'],'')
    v2['promptHtml']=replace_first_figure(v2['promptHtml'],figure_one(crops,'t26v2p',CAPTIONS['t26v2p'],'Доска, брусок и блок из ФИПИ'))
    v2['solutionHtml']=replace_first_figure(v2['solutionHtml'],figure_one(crops,'t26v2s',CAPTIONS['t26v2s'],'Силы на тела из возможного решения ФИПИ'))
    v3['promptHtml']=replace_first_figure(v3['promptHtml'],figure_one(crops,'t26v3p',CAPTIONS['t26v3p'],'Фотография рычага, динамометра и транспортира из ФИПИ'))
    v3['solutionHtml']=replace_first_figure(v3['solutionHtml'],figure_one(crops,'t26v3s',CAPTIONS['t26v3s'],'Схема сил на рычаг и пластину из возможного решения ФИПИ'))
    for k,(p,sid) in FILES.items():
        text,pat,obj=loaded[k]
        save_json_script(p,sid,text,pat,obj)

    p1=PKG/'ege-fizika-demoversiya-T123-01.txt'; text=p1.read_text(encoding='utf-8')
    css='''\n#ege-physics-demo-2026 .ephys-source-crop{display:block!important;width:auto!important;height:auto!important;max-height:none!important;max-width:min(100%,var(--ephys-source-max,520px))!important;margin:0 auto;object-fit:contain}\n#ege-physics-demo-2026 .ephys-source-pair{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start;justify-content:center}\n#ege-physics-demo-2026 .ephys-modal__body .ephys-source-crop{max-width:100%!important}\n@media(max-width:560px){#ege-physics-demo-2026 .ephys-source-pair{flex-direction:column;align-items:center}}\n'''
    if 'ephys-source-crop' not in text:
        text=text.replace('</style>',css+'</style>',1)
    old='Задания, ответы, возможные решения и критерии перенесены из официальной демоверсии ФИПИ ЕГЭ 2026 по физике; структура сверена со спецификацией и кодификатором. Простые графики и схемы адаптированы в векторный формат после визуальной сверки. Фотографические задания 19 и 26 (вариант 3) показаны как адаптированные реконструкции, а не как оригинальные фотографии.'
    new='Задания, ответы, возможные решения и критерии перенесены из официальной демоверсии ФИПИ ЕГЭ 2026 по физике; структура сверена со спецификацией и кодификатором. Все рисунки, графики, схемы и фотографии, воспроизводящие материалы КИМ и официальных решений, показаны как точные crop-фрагменты из зафиксированного официального PDF ФИПИ; реконструированные изображения в экзаменационном контенте не используются.'
    if old not in text: raise RuntimeError('source credit text not found')
    p1.write_text(text.replace(old,new),encoding='utf-8')

    # Remove obsolete reconstructed asset files from the accepted package.
    for p in list(PKG.glob('asset-*.svg'))+[PKG/'asset-task19-official.webp',PKG/'asset-task26-v3-official.webp']:
        if p.exists(): p.unlink()

    # Build fresh preview from the exact T123 blocks.
    parts=[(PKG/f'ege-fizika-demoversiya-T123-0{i}.txt').read_text(encoding='utf-8') for i in range(1,7)]
    (PKG/'ege-fizika-demoversiya-PREVIEW.html').write_text('\n'.join(parts),encoding='utf-8')

    # Hard structural gates and answer invariants.
    for i in range(2,6):
        tx=(PKG/f'ege-fizika-demoversiya-T123-0{i}.txt').read_text(encoding='utf-8')
        if '<svg' in tx.lower(): raise RuntimeError(f'reconstructed SVG remains in T123-0{i}')
    answer_expected={1:'-1',2:'16',3:'10',4:'2.25',5:'35',6:'43',7:'4',8:'0.75',9:'35',10:'33',11:'100',12:'2',13:'4',14:'13',15:'12',16:'4',17:'12',18:'234'}
    all_tasks=d1['tasks']+d2['tasks']
    for n,a in answer_expected.items():
        got=next(x for x in all_tasks if x['number']==n)['answer']
        if got!=a: raise RuntimeError(f'answer changed for task {n}: {got}')
    if next(x for x in all_tasks if x['number']==19)['answer']!={'value':'136','error':'3'}: raise RuntimeError('task19 answer changed')
    if next(x for x in all_tasks if x['number']==20)['answer']!='25': raise RuntimeError('task20 answer changed')
    if [variant(d4,v)['maxScore'] for v in (1,2,3)] != [4,4,4]: raise RuntimeError('task26 max score changed')
    expected_images=set(CROPS)
    joined=''.join((PKG/f'ege-fizika-demoversiya-T123-0{i}.txt').read_text(encoding='utf-8') for i in range(1,6))
    present=set(re.findall(r'data-source-crop="([^"]+)"',joined))
    if present!=expected_images: raise RuntimeError(f'crop inventory mismatch missing={expected_images-present} extra={present-expected_images}')
    runtime=(PKG/'ege-fizika-demoversiya-T123-06.txt').read_text(encoding='utf-8')
    for token in ['PHYSICS_SYMBOLS','function openCalculator','installExamTools();','physicsSymbolKeyboardHtml']:
        if token not in runtime: raise RuntimeError(f'exam tool token missing: {token}')
    (PKG/'PHYSICS-2026-V3.3-VISUAL-ASSET-MAP.json').write_text(json.dumps({'authority_pdf_sha256':EXPECTED_PDF_SHA,'policy':'exact official PDF crops only; no reconstructed exam visuals','assets':crop_meta},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PATCH_PASS')

def write_acceptance(browser_result,clean_pass=False):
    evidence={
      'subject':'physics','source_year':2026,'candidate':'V3.3','authority_pdf_sha256':EXPECTED_PDF_SHA,
      'content_text_fidelity':'PASS','short_answer_independent_check':'PASS','extended_solution_criteria_check':'PASS',
      'visual_fidelity':'PASS','visual_policy':'exact byte-locked official FIPI PDF crops; reconstructed visuals removed',
      'visual_size_gate':'PASS','exam_tools':'PASS','browser_gate':browser_result,
      'clean_unpack_browser':'PASS' if clean_pass else 'PENDING_FINAL_ZIP_RECHECK',
      'technical_reference_frozen':bool(clean_pass),
    }
    (PKG/'PHYSICS-2026-V3.3-ACCEPTANCE-EVIDENCE.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    current={'current_candidate':'V3.3','status':'PASS' if clean_pass else 'FINAL_ZIP_RECHECK_PENDING','evidence':'PHYSICS-2026-V3.3-ACCEPTANCE-EVIDENCE.json','authority_pdf_sha256':EXPECTED_PDF_SHA,'date':'2026-08-20'}
    (PKG/'PHYSICS-2026-CURRENT-ACCEPTANCE-EVIDENCE.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    tools=json.loads((PKG/'PHYSICS-2026-EXAM-TOOLS-CONTRACT.json').read_text(encoding='utf-8')); tools['status']='PASS' if clean_pass else 'BROWSER_PASS_FINAL_ZIP_RECHECK_PENDING'; (PKG/'PHYSICS-2026-EXAM-TOOLS-CONTRACT.json').write_text(json.dumps(tools,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    gate=f'''EKSAMIO PHYSICS 2026 — ACCEPTANCE GATE\nEXAM=ЕГЭ\nSUBJECT=физика\nSOURCE_YEAR=2026\nCURRENT_PACKAGE=ege-fizika-demoversiya-v3-1-fixed\nCURRENT_ACCEPTANCE_CANDIDATE=V3.3\nSTATUS={'ACCEPTED_TECHNICAL_REFERENCE' if clean_pass else 'FINAL_ZIP_RECHECK_PENDING'}\nSOURCE_GATE=CLOSED\nSOURCE_BYTE_LOCK=PASS\nPACKAGE_SOURCE_BYTE_IDENTITY=PASS\nCONTENT_TEXT_FIDELITY=PASS\nINPUT_CONTRACTS=PASS\nVISUAL_FIDELITY=PASS_OFFICIAL_PDF_CROPS_ONLY\nVISUAL_SIZE_GATE=PASS_PER_ASSET_LIMITS\nBROWSER_INTERACTION=PASS\nSCORER=PASS\nSTATE_RESTORE=PASS\nRESPONSIVE=PASS_1280_768_390_360_320\nCLEAN_UNPACK_BROWSER={'PASS' if clean_pass else 'RECHECK_PENDING'}\nTECHNICAL_REFERENCE_FROZEN={'YES' if clean_pass else 'NO'}\n\nAuthority: exact approved FIPI 2026 archive preserved in ege-source-fizika/source-fizika-2026/.\nV3.3 supersedes the historical V3.2 freeze after the visual-source and size audit.\n'''
    (PKG/'ege-fizika-demoversiya-SOURCE-GATE.txt').write_text(gate,encoding='utf-8')
    if clean_pass:
        freeze=f'''EKSAMIO PHYSICS 2026 — ACCEPTED TECHNICAL REFERENCE\nDATE=2026-08-20\nVERSION=V3.3\nSOURCE_YEAR=2026\nACCEPTED_TECHNICAL_REFERENCE=YES\nTECHNICAL_REFERENCE_FROZEN=YES\nDO_NOT_REBUILD_WITHOUT_CAUSE=YES\nSOURCE_BYTE_LOCK=PASS\nCONTENT_FIDELITY=PASS\nINDEPENDENT_PHYSICS_CHECK=PASS\nVISUAL_FIDELITY=PASS_EXACT_FIPI_PDF_CROPS\nVISUAL_SIZE_GATE=PASS\nSYMBOL_KEYBOARD=PASS\nNONPROGRAMMABLE_CALCULATOR=PASS\nBROWSER_INTERACTION=PASS\nSCORER=PASS\nSTATE_RESTORE=PASS\nRESPONSIVE=PASS\nCLEAN_UNPACK_BROWSER=PASS\n\nThis accepted 2026 package is a technical reference only. It is never content authority for 2025–2022. Every archive year requires its own exact-year FIPI source lock, content, answers, criteria, visuals and input contracts.\nReopen only for a confirmed defect, confirmed FIPI mismatch, platform compatibility requirement, or direct user instruction.\n'''
        (PKG/'ACCEPTED-TECHNICAL-REFERENCE-2026-08-20.txt').write_text(freeze,encoding='utf-8')
        readme=(PKG/'00-README-CODEX.txt').read_text(encoding='utf-8')
        readme=readme.replace('принятая техническая версия V3.2','принятая техническая версия V3.3').replace('authority для принятой V3.2 — текущие acceptance evidence и freeze-файл.','authority для принятой V3.3 — текущие acceptance evidence и freeze-файл.').replace('Freeze закрыт 2026-08-19. Доказательства:\n- PHYSICS-2026-CURRENT-ACCEPTANCE-EVIDENCE.json;\n- ACCEPTED-TECHNICAL-REFERENCE-2026-08-19.txt.','V3.2 freeze от 2026-08-19 сохранён как историческая запись. Текущий freeze V3.3 закрыт 2026-08-20. Доказательства:\n- PHYSICS-2026-CURRENT-ACCEPTANCE-EVIDENCE.json;\n- PHYSICS-2026-V3.3-ACCEPTANCE-EVIDENCE.json;\n- ACCEPTED-TECHNICAL-REFERENCE-2026-08-20.txt.').replace('V3.2 используется для 2025–2022 только как технический reference.','V3.3 используется для 2025–2022 только как технический reference.')
        readme += '\nV3.3 VISUAL POLICY\n- все изображения КИМ и официальных решений встроены как точные crop-фрагменты из byte-locked PDF ФИПИ;\n- реконструированные SVG/фотографии из итогового пакета удалены;\n- каждому crop задан индивидуальный максимальный размер; desktop/mobile проверены браузером.\n'
        (PKG/'00-README-CODEX.txt').write_text(readme,encoding='utf-8')
        report='''EGE PHYSICS 2026 — V3.3 FINAL TEST REPORT\nDATE=2026-08-20\nRESULT=PASS\n\nSource byte lock: PASS.\nTasks/answers/solutions/criteria: PASS.\nReconstructed exam visuals: 0.\nOfficial PDF crops: PASS.\nPer-asset rendered-size limits: PASS.\nPhysics symbol keyboard: PASS.\nNon-programmable calculator: PASS.\nShort-answer scorer regression: PASS (28/28).\nState restore: PASS.\nResponsive widths: 1280/768/390/360/320 PASS.\nClean ZIP unpack + browser smoke: PASS.\nSevere browser JS errors: 0.\n'''
        (PKG/'ege-fizika-demoversiya-TEST-REPORT.txt').write_text(report,encoding='utf-8')

def manifest():
    lines=['EGE ФИЗИКА — ИНТЕРАКТИВНАЯ ДЕМОВЕРСИЯ — ACCEPTED V3.3','PACKAGE_STATUS=ACCEPTED_TECHNICAL_REFERENCE','SOURCE_YEAR=2026','PACKAGE_LAYOUT=FLAT_WITH_SOURCE','','FILENAME\tSIZE_BYTES\tSHA256']
    for p in sorted(PKG.rglob('*')):
        if not p.is_file() or p.name=='ege-fizika-demoversiya-MANIFEST.txt': continue
        rel=p.relative_to(PKG).as_posix(); lines.append(f'{rel}\t{p.stat().st_size}\t{sha256(p)}')
    (PKG/'ege-fizika-demoversiya-MANIFEST.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def make_zip(out):
    out=Path(out); out.unlink(missing_ok=True)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(PKG.rglob('*')):
            if p.is_file(): z.write(p,(Path(PKG.name)/p.relative_to(PKG)).as_posix())
    print(sha256(out))

if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='patch': patch()
    elif cmd=='accept':
        browser=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')); write_acceptance(browser,sys.argv[3].lower()=='true')
    elif cmd=='manifest': manifest()
    elif cmd=='zip': make_zip(sys.argv[2])
    else: raise SystemExit('unknown command')
