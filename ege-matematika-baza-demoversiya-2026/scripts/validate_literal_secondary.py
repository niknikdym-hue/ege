#!/usr/bin/env python3
import html
import json
import re
import unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'matematika-source-2026'/'canonical-printed-pages'/'base-demo'
PRIMARY=ROOT/'ege-matematika-baza-demoversiya-2026-LITERAL-AUDIT-EVIDENCE.json'

MAP={
    '\uf03d':'=', '\uf0b4':'×', '\uf05b':'[', '\uf05d':']', '\uf02d':'−',
    'ꞏ':'·', '':'×', '':'=', '':'[', '':']', '':'−'
}
SUBS=str.maketrans('₀₁₂₃₄₅₆₇₈₉','0123456789')
SUPS=str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹','0123456789')

def canonical(s):
    s=unicodedata.normalize('NFC',html.unescape(s or '')).replace('\u00a0',' ')
    for a,b in MAP.items(): s=s.replace(a,b)
    s=s.translate(SUBS).translate(SUPS)
    s=s.replace('—','—').replace('–','–')
    return s

def tokens(s):
    s=canonical(s)
    # Split words, numbers, math symbols and punctuation separately so PDF column
    # interleaving can be ignored without changing the order of the target text.
    return re.findall(r'[A-Za-zА-Яа-яЁё]+|\d+(?:[.,]\d+)?|[=×√−+:/;,.()\[\]³²]|\S',s)

def is_subsequence(target,source):
    j=0
    for tok in source:
        if j < len(target) and tok == target[j]:
            j+=1
    return j==len(target)

primary=json.loads(PRIMARY.read_text(encoding='utf-8'))
records=[]
remaining=[]
for f in primary['failures']:
    src=(SOURCE/f"page-{f['page']:02d}.txt").read_text(encoding='utf-8')
    tt=tokens(f['text']); st=tokens(src)
    passed=is_subsequence(tt,st)
    reason='LAYOUT_SUBSEQUENCE_PASS' if passed else 'FORMULA_OR_VISUAL_GLYPH_REVIEW_REQUIRED'
    rec={**f,'secondary_status':reason,'target_tokens':tt}
    records.append(rec)
    if not passed: remaining.append(rec)

out={
    'primary_failures':len(primary['failures']),
    'layout_subsequence_pass':sum(r['secondary_status']=='LAYOUT_SUBSEQUENCE_PASS' for r in records),
    'formula_or_visual_review_required':len(remaining),
    'status':'PASS_WITH_SECONDARY_GATES_PENDING' if remaining else 'PASS',
    'records':records,
    'remaining':remaining
}
(ROOT/'ege-matematika-baza-demoversiya-2026-LITERAL-SECONDARY-EVIDENCE.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:out[k] for k in ('primary_failures','layout_subsequence_pass','formula_or_visual_review_required','status')},ensure_ascii=False,indent=2))
