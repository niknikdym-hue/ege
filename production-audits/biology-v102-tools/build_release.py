#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, json, re, shutil, zipfile
from pathlib import Path
from bs4 import BeautifulSoup

P='ege-biologiya-demoversiya';VERSION='1.0.2';KEY='eksamio_ege_biologiya_demo_2026_v1_0_2'

def parse_push(script:str,name:str)->str:
    prefix=f'window.{name}=window.{name}||[];window.{name}.push('
    if not script.startswith(prefix) or not script.endswith(');'): raise ValueError(name)
    return json.loads(script[len(prefix):-2])

def options(prompt):
    s=BeautifulSoup(prompt,'html.parser');ol=s.select_one('ol.bio-options')
    return [x.get_text(' ',strip=True) for x in ol.find_all('li',recursive=False)] if ol else []

def matching(prompt):
    s=BeautifulSoup(prompt,'html.parser');cols=s.select('.bio-match > div')
    if len(cols)!=2: raise RuntimeError('matching columns')
    rows=[];choices=[]
    for div in cols[0].find_all('div',recursive=False):
        b=div.find('b')
        if b:
            mark=b.get_text(' ',strip=True);text=re.sub(r'^'+re.escape(mark)+r'\s*','',div.get_text(' ',strip=True))
            rows.append({'key':mark.rstrip(')'),'text':text})
    for div in cols[1].find_all('div',recursive=False):
        b=div.find('b')
        if b:
            mark=b.get_text(' ',strip=True);v=re.sub(r'\D','',mark);text=re.sub(r'^'+re.escape(mark)+r'\s*','',div.get_text(' ',strip=True))
            choices.append({'value':v,'text':text or v})
    return rows,choices

def sentence_options(prompt):
    s=BeautifulSoup(prompt,'html.parser');text=s.select_one('.bio-source-text').get_text(' ',strip=True);parts=re.split(r'\((\d)\)\s*',text)
    return [parts[i+1].strip() for i in range(1,len(parts),2)]

def payload_from_record(record):
    raw=str(record.select_one('.t123'));a=raw.find('<!-- nominify begin -->');b=raw.find('<!-- nominify end -->')
    return raw[a+len('<!-- nominify begin -->'):b].strip()

def chunks(text,n): return [text[i:i+n] for i in range(0,len(text),n)]
def push(name,text): return f'<script>window.{name}=window.{name}||[];window.{name}.push({json.dumps(text,ensure_ascii=False,separators=(",",":"))});</script>'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--repo',default='.');args=ap.parse_args()
    source=Path(args.source).resolve();repo=Path(args.repo).resolve();tool=Path(__file__).resolve().parent;root=repo/'ege-biologiya-demoversiya-v1'
    if root.exists(): shutil.rmtree(root)
    (root/'source').mkdir(parents=True);(root/'tests').mkdir();(root/'scripts').mkdir()
    g=json.loads((source/'live/globals.json').read_text(encoding='utf-8'))
    task_chunks=[];asset_chunks=[]
    for s in g['scripts']:
        txt=s.get('text') or ''
        if '__BIO_TASK_CHUNKS__.push' in txt: task_chunks.append(parse_push(txt,'__BIO_TASK_CHUNKS__'))
        if '__BIO_ASSET_CHUNKS__.push' in txt: asset_chunks.append(parse_push(txt,'__BIO_ASSET_CHUNKS__'))
    data=json.loads(''.join(task_chunks));assets=json.loads(''.join(asset_chunks));tasks=data['tasks']
    for t in tasks:
        n=t['number'];t['package_version']=VERSION
        if n==2:
            t['interaction']={'type':'table_selects','rows':[{'key':'А','text':'Количество рибосом'},{'key':'Б','text':'Объём цитоплазмы'}],'choices':[{'value':'1','text':'увеличилась'},{'value':'2','text':'уменьшилась'},{'value':'3','text':'не изменилась'}],'allow_repeat':True,'answer_length':2}
        elif n in {6,10,14,19}:
            rows,choices=matching(t['prompt_html']);t['interaction']={'type':'matching_selects','rows':rows,'choices':choices,'allow_repeat':True,'answer_length':len(rows)}
        elif n==20:
            opts=options(t['prompt_html']);t['interaction']={'type':'table_selects','rows':[{'key':'А','text':'Тип приспособленности'},{'key':'Б','text':'Уровень эволюционных изменений'},{'key':'В','text':'Путь достижения биологического прогресса'}],'choices':[{'value':str(i+1),'text':x} for i,x in enumerate(opts)],'allow_repeat':False,'answer_length':3}
        elif n in {8,12,16}:
            opts=options(t['prompt_html']);t['interaction']={'type':'sequence_builder','options':[{'value':str(i+1),'text':x} for i,x in enumerate(opts)],'answer_length':len(opts),'hide_prompt_options':True}
        elif n in {7,11,15,17,18,21}:
            opts=sentence_options(t['prompt_html']) if n==17 else options(t['prompt_html']);plain=BeautifulSoup(t['prompt_html'],'html.parser').get_text(' ',strip=True)
            t['interaction']={'type':'multiple_choice','options':[{'value':str(i+1),'text':x} for i,x in enumerate(opts)],'max_select':3 if re.search(r'Выберите\s+три',plain,re.I) else None,'hide_prompt_options':n!=17,'source_sentences':n==17}
        elif t['kind']=='short': t['interaction']={'type':'text_input'}
        else: t['interaction']={'type':'extended_text'}
    data.update({'schema_version':'1.1','package_version':VERSION,'storage_key':KEY,'tasks':tasks})
    (root/f'{P}-EXAM-DATA.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    page=BeautifulSoup((source/'live/page-content.html').read_text(encoding='utf-8'),'html.parser');target=page.select_one('#eksamio-bio-demo').find_parent(class_='r')
    root_html=payload_from_record(target).replace(' style="display: block;"','')
    css_record=None
    for r in target.find_all_previous(class_='r'):
        if '--bio-bg' in str(r): css_record=r;break
    if not css_record: raise RuntimeError('biology CSS record not found')
    css=payload_from_record(css_record).replace('</style>','')+'\n'+(tool/'interaction.css').read_text(encoding='utf-8')+'</style>\n'
    runtime='<script>\n'+(tool/'runtime.js').read_text(encoding='utf-8').strip()+'\n</script>'
    compact_data=json.dumps(data,ensure_ascii=False,separators=(',',':'));compact_assets=json.dumps(assets,ensure_ascii=False,separators=(',',':'))
    blocks=[css,root_html]+[push('__BIO_TASK_CHUNKS__',x) for x in chunks(compact_data,30000)]+[push('__BIO_ASSET_CHUNKS__',x) for x in chunks(compact_assets,48000)]+[runtime]
    for i,b in enumerate(blocks,1):
        f=root/f'{P}-T123-{i:02d}.txt';f.write_text(b,encoding='utf-8');assert f.stat().st_size<55000
    head='''<title>Демоверсия ЕГЭ по биологии | Эксамио</title>\n<meta name="description" content="Интерактивная демоверсия ЕГЭ по биологии: полный вариант, таймер, автоматическая проверка кратких ответов и критерии развёрнутых заданий.">\n<link rel="canonical" href="https://eksamio.ru/ege/biologiya/demoversiya/">\n<meta property="og:type" content="website">\n<meta property="og:title" content="Демоверсия ЕГЭ по биологии | Эксамио">\n<meta property="og:description" content="Полный вариант ЕГЭ по биологии с типизированными заданиями, таймером и сохранением ответов.">\n<meta property="og:url" content="https://eksamio.ru/ege/biologiya/demoversiya/">\n<meta name="twitter:card" content="summary">\n<script type="application/ld+json">{"@context":"https://schema.org","@type":"LearningResource","name":"Интерактивная демоверсия ЕГЭ по биологии","educationalLevel":"среднее общее образование","learningResourceType":"practice exam","inLanguage":"ru","url":"https://eksamio.ru/ege/biologiya/demoversiya/"}</script>\n'''
    (root/f'{P}-HEAD.txt').write_text(head,encoding='utf-8');(root/f'{P}-SEO.txt').write_text('TITLE: Демоверсия ЕГЭ по биологии | Эксамио\nDESCRIPTION: Интерактивная демоверсия ЕГЭ по биологии: 28 заданий, таймер, сохранение, автоматическая проверка первой части и критерии развёрнутых ответов.\nCANONICAL: https://eksamio.ru/ege/biologiya/demoversiya/\n',encoding='utf-8')
    (root/f'{P}-PREVIEW.html').write_text('<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+head+'</head><body style="margin:0">'+'\n'.join(blocks)+'</body></html>',encoding='utf-8')
    pdf_dir=source/'repo/biologiya/biologiya-source-2026'
    for f in pdf_dir.glob('*.pdf'): shutil.copy2(f,root/'source'/f.name)
    contract={'package_version':VERSION,'t123_blocks':len(blocks),'t123_max_bytes':max((root/f'{P}-T123-{i:02d}.txt').stat().st_size for i in range(1,len(blocks)+1)),'t123_target_max_bytes':55000,'load_order':[f'{P}-T123-{i:02d}.txt' for i in range(1,len(blocks)+1)],'header_footer_included':False,'canonical_year_free':True,'result_contract':{'short_auto':True,'extended_self_assessment':'separate','official_total_before_expert':'— / 57','official_criteria_22_28':'complete'},'interaction_contract':{'answer_code_assembled_automatically':True,'browser_test_uses_real_controls':True,'incomplete_structured_answer_is_not_ready':True,'do_not_reveal_unstated_answer_count':True}}
    (root/f'{P}-PACKAGE-CONTRACT.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    exam={'exam':'ЕГЭ','subject':'Биология','source_year':2026,'task_count':28,'short_count':21,'extended_count':7,'duration_minutes':235,'short_max':36,'extended_max':21,'max_primary':57,'official_total_before_expert':'— / 57','variants':{'4':2,'5-6_linked':2,'24':2,'27':4}}
    (root/f'{P}-EXAM-MAP.json').write_text(json.dumps(exam,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    ic={'package_version':VERSION,'storage_key':KEY,'typed_interactions':{'table_selects':[2,20],'matching_selects':[6,10,14,19],'sequence_builder':[8,12,16],'multiple_choice':[7,11,15,17,18,21],'text_input':[1,3,4,5,9,13],'extended_text':list(range(22,29))},'rules':contract['interaction_contract']}
    (root/f'{P}-INTERACTION-CONTRACT.json').write_text(json.dumps(ic,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    install='ПОРЯДОК РАЗМЕЩЕНИЯ В TILDA\n\nURL: https://eksamio.ru/ege/biologiya/demoversiya/\n\nШапка и футер подключаются отдельно. Разместить блоки T123 строго подряд:\n'+''.join(f'{i}. {P}-T123-{i:02d}.txt\n' for i in range(1,len(blocks)+1))+'\nПосле публикации очистить кэш страницы и проверить новую попытку. Версия 1.0.2 использует новый ключ localStorage.\n'
    (root/f'{P}-INSTALLATION.txt').write_text(install,encoding='utf-8')
    (root/'00-README-CODEX.txt').write_text('ИНТЕРАКТИВНАЯ ДЕМОВЕРСИЯ ЕГЭ ПО БИОЛОГИИ\nВерсия: 1.0.2\nИсточник: официальный комплект ФИПИ 2026\n\nЗадания 2, 6–8, 10–12, 14–21 используют типизированные controls; код ответа формируется автоматически. Официальный итог до экспертной проверки: — / 57.\n',encoding='utf-8')
    for f in (tool/'tests').glob('*.py'): shutil.copy2(f,root/'tests'/f.name)
    for f in (tool/'templates').glob('*'): shutil.copy2(f,root/f.name)
    build='''#!/usr/bin/env python3\nfrom pathlib import Path\nimport zipfile\nroot=Path(__file__).resolve().parents[1];out=root.parent/'ege-biologiya-demoversiya-v1.0.2.zip'\nif out.exists():out.unlink()\nwith zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:\n for f in sorted(root.rglob('*')):\n  if f.is_file() and '__pycache__' not in f.parts and 'evidence' not in f.parts:z.write(f,Path(root.name)/f.relative_to(root))\nprint(out)\n'''
    (root/'scripts/build_demo_release.py').write_text(build,encoding='utf-8')
    manifest=root/f'{P}-MANIFEST-SHA256.txt';lines=[]
    for f in sorted(root.rglob('*')):
        if f.is_file() and f!=manifest and '__pycache__' not in f.parts: lines.append(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(root).as_posix()}')
    manifest.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    std=repo/'demo-production-standard';patch=tool/'standard'
    if patch.exists():
        for f in patch.rglob('*'):
            if f.is_file():
                dest=std/f.relative_to(patch);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
    print(f'Built {root} with {len(blocks)} T123 blocks')
if __name__=='__main__':main()
