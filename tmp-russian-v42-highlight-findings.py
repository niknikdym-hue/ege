from pathlib import Path
import hashlib,re
base=Path('ege-russkiy-demoversiya-2026-v4.2')
p=base/'ege-russkiy-demoversiya-T123-07.txt'
s=p.read_text(encoding='utf-8')
css_anchor='#ege-demo-2026 .edemo-check-action{margin-top:14px}\\\n'
css_add='''#ege-demo-2026 .edemo-finding-box{padding:12px 14px;border:1px solid #dfe4eb;border-radius:12px;background:#fff;transition:border-color .15s ease,background .15s ease,box-shadow .15s ease}\\\n#ege-demo-2026 .edemo-finding-box--error-active{border-color:#e4a3a3;border-left:5px solid #c84343;background:#fff4f4;box-shadow:0 0 0 3px rgba(200,67,67,.06)}\\\n#ege-demo-2026 .edemo-finding-box--error-active>strong:first-child{color:#a62f2f}\\\n#ege-demo-2026 .edemo-finding-box--check-active{border-color:#e4c36d;border-left:5px solid #d99a19;background:#fff9e8;box-shadow:0 0 0 3px rgba(217,154,25,.06)}\\\n#ege-demo-2026 .edemo-finding-box--check-active>strong:first-child{color:#8a5a00}\\\n'''
if css_anchor not in s: raise SystemExit('CSS anchor missing')
s=s.replace(css_anchor,css_add+css_anchor,1)
func_anchor='  function resetSpellOnEdit(){'
func='''  function highlightFindingBlocks(){var rows=document.querySelectorAll("#ege-demo-2026 .edemo-error-row");rows.forEach(function(row){var boxes=Array.from(row.children).filter(function(el){return el.tagName==="DIV";});if(boxes.length<2)return;var confirmed=boxes[0],possible=boxes[1];confirmed.classList.add("edemo-finding-box");possible.classList.add("edemo-finding-box");confirmed.classList.toggle("edemo-finding-box--error-active",!!confirmed.querySelector("ul.edemo-findings li"));possible.classList.toggle("edemo-finding-box--check-active",!!possible.querySelector("ul.edemo-findings li"));});}\n'''
if func_anchor not in s: raise SystemExit('function anchor missing')
s=s.replace(func_anchor,func+func_anchor,1)
old='  function enhance(){api=window.__edemoRussian2026Task27Review;if(!api)return;addStyles();enhanceFiles();resetSpellOnEdit();decorateCheck();}'
new='  function enhance(){api=window.__edemoRussian2026Task27Review;if(!api)return;addStyles();enhanceFiles();resetSpellOnEdit();decorateCheck();highlightFindingBlocks();}'
if old not in s: raise SystemExit('enhance anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

# Add browser assertions.
t=base/'test-russian-task27-browser.py'; q=t.read_text(encoding='utf-8')
a="    check(any('карова' in x['message'].lower() for x in checked['possibleFindings']['K7']),'speller candidate appears in K7 possible findings')\n"
b=a+"    check(page.locator('.edemo-error-row').nth(0).locator('.edemo-finding-box--check-active').count()==1,'K7 Стоит проверить block highlighted when finding exists')\n"
if a not in q: raise SystemExit('possible assertion anchor missing')
q=q.replace(a,b,1)
a2="    page.select_option('[data-review-score=\"K10\"]','2')\n"
b2="    page.wait_for_timeout(50)\n    check(page.locator('.edemo-error-row').nth(3).locator('.edemo-finding-box--error-active').count()==1,'K10 Найдены ошибки block highlighted when confirmed finding exists')\n"+a2
if a2 not in q: raise SystemExit('confirmed assertion anchor missing')
q=q.replace(a2,b2,1)
t.write_text(q,encoding='utf-8')

# Update manifest.
m=base/'MANIFEST-SHA256.txt'; ms=m.read_text(encoding='utf-8'); fn=p.name; h=hashlib.sha256(p.read_bytes()).hexdigest(); ms=re.sub(r'^[0-9a-f]{64}  '+re.escape(fn)+r'$',h+'  '+fn,ms,flags=re.M); m.write_text(ms,encoding='utf-8')
print('PATCH READY')
# trigger
