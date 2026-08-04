from __future__ import annotations
import json,re,subprocess,tempfile
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];P='ege-biologiya-demoversiya'
DATA=json.loads((ROOT/f'{P}-EXAM-DATA.json').read_text(encoding='utf-8'))
pdf=ROOT/'source'/'ege-2026-biologiya-demoversiya.pdf'
with tempfile.NamedTemporaryFile(suffix='.txt') as tmp:
    subprocess.run(['pdftotext','-layout',str(pdf),tmp.name],check=True)
    source=Path(tmp.name).read_text(encoding='utf-8',errors='replace')
def tokens(s):
    s=s.lower().replace('ё','е').replace('–','-').replace('—','-')
    return re.findall(r'[а-яa-z0-9]+',s)
src=tokens(source);src_text=' '.join(src)
fail=[]
for t in DATA['tasks']:
    text=BeautifulSoup(t['prompt_html'],'html.parser').get_text(' ',strip=True)
    tok=tokens(text)
    found=False
    for size in (10,8,6,4):
        for i in range(0,max(0,len(tok)-size+1)):
            phrase=' '.join(tok[i:i+size])
            if phrase in src_text:
                found=True;break
        if found: break
    if not found: fail.append((t['number'],t['variant_id'],text[:120]))
assert not fail,fail
# Official answer table and scoring passages.
for phrase in ['биосферный','122122','312231','54132','123313','421563','131233','164325','212112','правильное выполнение каждого из заданий 2 6 10 14 19 20','правильное выполнение каждого из заданий 7 11 15 17 18 21']:
    assert ' '.join(tokens(phrase)) in src_text,phrase
print('SOURCE FIDELITY PASS')
