#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'templates'/'runtime.js'
s=p.read_text(encoding='utf-8')
old="const options=right.map((x,i)=>({value:String(i+1),html:rightHtml[i]||esc(x)}));"
new="const optionCount=Math.max(right.length,rightHtml.length);const options=Array.from({length:optionCount},(_,i)=>({value:String(i+1),html:rightHtml[i]||esc(right[i]||'')}));"
if old not in s:raise SystemExit('matching option constructor target not found')
s=s.replace(old,new,1)
old2="${right.length?`<div class=\"mb-table-wrap\""
new2="${options.length?`<div class=\"mb-table-wrap\""
if old2 not in s:raise SystemExit('matching options table condition target not found')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
print('runtime formula-only matching options fixed')
