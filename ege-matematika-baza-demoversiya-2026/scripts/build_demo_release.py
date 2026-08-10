#!/usr/bin/env python3
import base64
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

from latex2mathml.converter import convert as latex_to_mathml

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
PREFIX='ege-matematika-baza-demoversiya-2026'
PACKAGE_VERSION='1.1'
CONTENT_VERSION='2026.2'
STORAGE_KEY='eksamio_ege_math_base_demo_2026_v1_1'
ZIP_NAME=f'{PREFIX}-v{PACKAGE_VERSION}.zip'
MAX_T123=45000
TARGET_BLOCK=41000
PART_CHARS=26000


def load_json(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))
def dump_json(path,data):
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def bsize(text): return len(text.encode('utf-8'))
def fix_typography(value):
    if isinstance(value,str):return value.replace('ꞏ','·')
    if isinstance(value,list):return [fix_typography(x) for x in value]
    if isinstance(value,dict):return {k:fix_typography(v) for k,v in value.items()}
    return value

def mathml(latex):
    if not latex:return None
    return latex_to_mathml(latex).replace('<?xml version="1.0" ?>','').strip()

def math_item(value):
    """Return safe generated HTML for a source item that may have a label prefix plus LaTeX."""
    m=re.match(r'^\s*([А-ЯЁA-D1-9]+\))\s*(.*)$',value or '')
    if m:
        prefix,expr=m.groups()
        return f'<strong>{prefix}</strong> {mathml(expr) if expr.strip() else ""}'
    return mathml(value)

def check_gates():
    task_e=load_json(f'{PREFIX}-TASK-MAP-BUILD-EVIDENCE.json')
    literal2=load_json(f'{PREFIX}-LITERAL-SECONDARY-EVIDENCE.json')
    formula=load_json(f'{PREFIX}-FORMULA-GATE-EVIDENCE.json')
    assets=load_json('source-evidence/ASSET-CROP-EVIDENCE.json')
    failures=[]
    if task_e.get('status')!='PASS':failures.append('TASK-MAP build evidence is not PASS')
    if literal2.get('layout_subsequence_pass')!=23 or literal2.get('formula_or_visual_review_required')!=6:failures.append('secondary literal evidence does not match expected 23+6 split')
    if formula.get('status')!='PASS' or formula.get('counts',{}).get('passed')!=6:failures.append('formula/glyph gate is not PASS 6/6')
    if assets.get('status')!='PASS' or assets.get('asset_count')!=25:failures.append('visual asset gate is not PASS 25/25')
    if failures:raise RuntimeError('Release gate blocked: '+'; '.join(failures))
    return {'task_map':'PASS','literal_layout':23,'formula_glyph':6,'visual_assets':25}

def enhance_task_map():
    tm=fix_typography(load_json(f'{PREFIX}-TASK-MAP.json'))
    tasks=[]
    for task in tm['tasks']:
        out={'number':task['number'],'variants':[]}
        for src in task['variants']:
            v=dict(src)
            if v.get('formula_latex'):v['formula_mathml']=mathml(v['formula_latex'])
            if v.get('left_latex'):
                v['left_html']=[math_item(x) for x in v['left_latex']]
            elif v.get('left'):
                v['left_html']=[]
            if v.get('right_latex'):
                v['right_html']=[math_item(x) for x in v['right_latex']]
            elif v.get('right'):
                v['right_html']=[]
            out['variants'].append(v)
        tasks.append(out)
    encoded=json.dumps(tasks,ensure_ascii=False)
    if 'ꞏ' in encoded:raise RuntimeError('Typography regression: malformed middle-dot remains in enhanced task map')
    return tasks

def chunk_items(items,prefix,suffix):
    blocks=[];cur=[]
    for item in items:
        trial=cur+[item]
        text=prefix+json.dumps(trial,ensure_ascii=False,separators=(',',':'))+suffix
        if cur and bsize(text)>TARGET_BLOCK:
            blocks.append(prefix+json.dumps(cur,ensure_ascii=False,separators=(',',':'))+suffix)
            cur=[item]
        else:cur=trial
    if cur:blocks.append(prefix+json.dumps(cur,ensure_ascii=False,separators=(',',':'))+suffix)
    return blocks

def append_parts(blocks,obj_name,key,b64):
    parts=[b64[i:i+PART_CHARS] for i in range(0,len(b64),PART_CHARS)]
    for part in parts:
        script=f'<script>window.EKSAMIO_MATH_BASE.{obj_name}[{json.dumps(str(key))}]=window.EKSAMIO_MATH_BASE.{obj_name}[{json.dumps(str(key))}]||[];window.EKSAMIO_MATH_BASE.{obj_name}[{json.dumps(str(key))}].push({json.dumps(part)});</script>\n'
        if bsize(script)>=MAX_T123:raise RuntimeError(f'fragment block too large for {key}: {bsize(script)}')
        blocks.append(script)

def write_metadata(tasks,gate_summary):
    exam=load_json(f'{PREFIX}-EXAM-MAP.json')
    exam_data={
        'exam':'ЕГЭ','subject':'математика','level':'базовый','sourceYear':2026,'packageVersion':PACKAGE_VERSION,
        'durationMinutes':180,'maxPrimaryScore':21,'storageKey':STORAGE_KEY,'permanentUrl':exam['permanent_url'],
        'officialExampleCount':70,'tasks':tasks
    }
    dump_json(ROOT/f'{PREFIX}-EXAM-DATA.json',exam_data)
    contract={
        'package_version':PACKAGE_VERSION,'source_year':2026,'permanent_url':exam['permanent_url'],
        'header_footer_included':False,'canonical_year_free':True,
        'result_contract':{'automatic_scoring':True,'primary_score':'0–21','test_score_conversion':False},
        'variant_contract':{'one_official_example_per_position':True,'student_selects_variant':False,'variant_persists_after_reload':True,'official_examples_total':70},
        'interaction_contract':{'numeric_input':'numeric syntax is validated independently from answer correctness; dot normalizes to comma; raw invalid input is preserved','matching_selects_4':'four real selects; system assembles code','checkboxes':'real checkboxes; system assembles set','row_checkboxes':'real row selection; system assembles set','browser_test_uses_real_controls':True},
        'release_gate_summary':gate_summary
    }
    dump_json(ROOT/f'{PREFIX}-PACKAGE-CONTRACT.json',contract)
    interaction={}
    for t in tasks:
        interaction[str(t['number'])]=[{'variant':v['variant'],'control':v['control'],'source_page':v['source_page'],'canonical_forms':v['canonical_forms'],'order_ignored':bool(v.get('order_ignored'))} for v in t['variants']]
    dump_json(ROOT/f'{PREFIX}-INTERACTION-CONTRACT.json',interaction)
    (ROOT/f'{PREFIX}-SEO.txt').write_text(
        'TITLE: Интерактивная демоверсия ЕГЭ по математике — базовый уровень | Эксамио\n'
        'DESCRIPTION: Пройдите интерактивную демоверсию ЕГЭ по базовой математике: 21 задание, таймер, автосохранение, справочные материалы и проверка результата после завершения.\n'
        'KEYWORDS: демоверсия ЕГЭ математика базовый уровень, ЕГЭ базовая математика, интерактивная демоверсия, задания ФИПИ\n'
        f'PAGE_URL: {exam["permanent_url"]}\n',encoding='utf-8')
    (ROOT/f'{PREFIX}-HEAD.txt').write_text(f'''<link rel="canonical" href="{exam['permanent_url']}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Эксамио">
<meta property="og:title" content="Интерактивная демоверсия ЕГЭ по математике — базовый уровень">
<meta property="og:description" content="21 задание, таймер, автосохранение, справочные материалы и проверка после завершения.">
<meta property="og:url" content="{exam['permanent_url']}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"LearningResource","name":"Интерактивная демоверсия ЕГЭ по математике — базовый уровень","url":"{exam['permanent_url']}","inLanguage":"ru-RU","educationalLevel":"11 класс","learningResourceType":"Интерактивная демоверсия экзамена","isAccessibleForFree":true,"provider":{{"@type":"Organization","name":"Эксамио","url":"https://eksamio.ru/"}},"about":{{"@type":"Thing","name":"ЕГЭ по математике, базовый уровень"}}}}</script>
''',encoding='utf-8')

def build_blocks(tasks):
    shell=(ROOT/'templates'/'T123-shell.html').read_text(encoding='utf-8')
    shell=re.sub(r'packageVersion:"[^"]+"',f'packageVersion:"{PACKAGE_VERSION}"',shell)
    shell=re.sub(r'contentVersion:"[^"]+"',f'contentVersion:"{CONTENT_VERSION}"',shell)
    shell=re.sub(r'storageKey:"[^"]+"',f'storageKey:"{STORAGE_KEY}"',shell)
    runtime=(ROOT/'templates'/'runtime.js').read_text(encoding='utf-8')
    blocks=[shell]
    blocks.extend(chunk_items(tasks,'<script>window.EKSAMIO_MATH_BASE.tasks.push(...',' );</script>\n'.replace(' ','')))
    for path in sorted((ROOT/'assets').glob('*.webp')):
        append_parts(blocks,'assetParts',path.stem,base64.b64encode(path.read_bytes()).decode('ascii'))
    for n in range(4,8):
        path=ROOT/'source-evidence'/'printed-pages'/f'page-{n:02d}.webp'
        append_parts(blocks,'refParts',n,base64.b64encode(path.read_bytes()).decode('ascii'))
    blocks.append('<script>\n'+runtime+'\n</script>\n')
    for i,text in enumerate(blocks,1):
        if bsize(text)>=MAX_T123:raise RuntimeError(f'T123 block {i} is {bsize(text)} bytes (limit {MAX_T123})')
    for old in ROOT.glob(f'{PREFIX}-T123-*.txt'):old.unlink()
    names=[]
    for i,text in enumerate(blocks,1):
        name=f'{PREFIX}-T123-{i:02d}.txt';(ROOT/name).write_text(text,encoding='utf-8');names.append(name)
    return names

def update_exam_map(t123):
    path=ROOT/f'{PREFIX}-EXAM-MAP.json';data=json.loads(path.read_text(encoding='utf-8'))
    data['package_version']=PACKAGE_VERSION;data['storage_key']=STORAGE_KEY
    data['t123_order']=t123;data['build_status']='BUILT';data['source_gate_status']='PASS';data['content_lock_status']='LOCKED';data['release_status']='BUILT_PENDING_TESTS'
    dump_json(path,data)

def write_installation(t123):
    lines=['УСТАНОВКА В TILDA',f'Пакет: {PREFIX}-v{PACKAGE_VERSION}', '', '1. Использовать SEO и HEAD из одноимённых файлов.',f'2. Создать {len(t123)} блоков T123 и вставить их строго в указанном порядке.','3. Между этими T123 не вставлять другие блоки.','4. Шапка и футер подключаются отдельно и в пакет не входят.','5. Опубликовать страницу.','6. После публикации выполнить production smoke-test на реальном URL.','', 'ПОРЯДОК T123:']+t123
    (ROOT/f'{PREFIX}-INSTALLATION.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def build_preview(t123):
    head=(ROOT/f'{PREFIX}-HEAD.txt').read_text(encoding='utf-8')
    body='\n'.join((ROOT/name).read_text(encoding='utf-8') for name in t123)
    preview='<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+head+'</head><body>'+body+'</body></html>\n'
    (ROOT/f'{PREFIX}-PREVIEW.html').write_text(preview,encoding='utf-8')

def manifest_and_zip():
    manifest=ROOT/f'{PREFIX}-MANIFEST-SHA256.txt'
    if manifest.exists():manifest.unlink()
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!=manifest.name)
    manifest.write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n' for p in files),encoding='utf-8')
    out=REPO/ZIP_NAME
    if out.exists():out.unlink()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(ROOT.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':z.write(p,Path(ROOT.name)/p.relative_to(ROOT))
    return out

if __name__=='__main__':
    gates=check_gates();tasks=enhance_task_map();write_metadata(tasks,gates);t123=build_blocks(tasks);write_installation(t123);update_exam_map(t123);build_preview(t123);out=manifest_and_zip()
    evidence={'status':'BUILT_PENDING_TESTS','package':out.name,'package_version':PACKAGE_VERSION,'content_version':CONTENT_VERSION,'storage_key':STORAGE_KEY,'t123_blocks':len(t123),'t123_max_bytes':max((ROOT/n).stat().st_size for n in t123),'official_examples':sum(len(t['variants']) for t in tasks),'assets':len(list((ROOT/'assets').glob('*.webp'))),'reference_pages':[4,5,6,7],'acceptance_fixes':['numeric input syntax decoupled from answer correctness','raw invalid numeric input persists without stale-value fallback','task 1 integer-answer hint','Нꞏм normalized to Н·м']}
    dump_json(ROOT/f'{PREFIX}-BUILD-EVIDENCE.json',evidence)
    print(json.dumps(evidence,ensure_ascii=False,indent=2))
