#!/usr/bin/env python3
import html
import json
import re
import unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
SOURCE=REPO/'matematika-source-2026'/'canonical-printed-pages'/'base-demo'
CONTENT=ROOT/'content'
PARTS=['tasks-01-07.json','tasks-08-14.json','tasks-15-21.json']

TAG=re.compile(r'<[^>]+>')
SPACE=re.compile(r'\s+')

def plain(value):
    value=html.unescape(TAG.sub(' ',value or ''))
    value=unicodedata.normalize('NFC',value).replace('\u00a0',' ')
    return SPACE.sub(' ',value).strip()

def norm(value):
    return plain(value).replace('–','–').replace('−','−')

def source_text(page):
    return norm((SOURCE/f'page-{page:02d}.txt').read_text(encoding='utf-8'))

def paragraph_chunks(value):
    if not value: return []
    parts=re.findall(r'<p>(.*?)</p>',value,flags=re.S)
    return [plain(x) for x in parts] if parts else [plain(value)]

records=[]
failures=[]
manual=[]
for filename in PARTS:
    data=json.loads((CONTENT/filename).read_text(encoding='utf-8'))
    for task in data['tasks']:
        for v in task['variants']:
            key=f'{task["number"]}.{v["variant"]}'
            src=source_text(v['source_page'])
            checks=[]
            for field in ('prompt_html','continuation_html','instruction'):
                for chunk in paragraph_chunks(v.get(field)):
                    if not chunk: continue
                    checks.append((field,chunk))
            for field in ('options','left','right'):
                for chunk in v.get(field,[]) or []:
                    checks.append((field,plain(chunk)))
            table=v.get('table')
            if table:
                for chunk in table.get('headers',[]): checks.append(('table_header',plain(chunk)))
                for row in table.get('rows',[]):
                    for chunk in row: checks.append(('table_cell',plain(str(chunk))))

            row={'task':task['number'],'variant':v['variant'],'page':v['source_page'],'checks':[]}
            for field,chunk in checks:
                # Short numeric/table cells and symbolic fragments are separately covered by
                # formula/table visual gates; substring matching is too ambiguous for them.
                letters=sum(ch.isalpha() for ch in chunk)
                if len(chunk)<12 or letters<5:
                    status='MANUAL_VISUAL_OR_FORMULA_GATE'
                    manual.append((key,field,chunk))
                else:
                    status='PASS' if norm(chunk) in src else 'FAIL'
                    if status=='FAIL': failures.append((key,field,chunk,v['source_page']))
                row['checks'].append({'field':field,'text':chunk,'status':status})
            records.append(row)

result={
    'status':'PASS' if not failures else 'FAIL',
    'official_examples':len(records),
    'literal_failures':len(failures),
    'manual_visual_or_formula_checks':len(manual),
    'failures':[{'example':k,'field':f,'text':t,'page':p} for k,f,t,p in failures],
    'records':records
}
(ROOT/'ege-matematika-baza-demoversiya-2026-LITERAL-AUDIT-EVIDENCE.json').write_text(
    json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('status','official_examples','literal_failures','manual_visual_or_formula_checks')},ensure_ascii=False,indent=2))
for f in failures[:100]: print('FAIL',f)
if failures: raise SystemExit(1)
