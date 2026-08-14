from pathlib import Path
import hashlib,re,json

base=Path('ege-russkiy-demoversiya-2026-v4.2')
p1=base/'ege-russkiy-demoversiya-T123-01.txt'
p6=base/'ege-russkiy-demoversiya-T123-06.txt'
preview=base/'ege-russkiy-demoversiya-PREVIEW.html'

old1=p1.read_text(encoding='utf-8')
s1=old1
s1=s1.replace('<p>Общий результат</p><p class="edemo-mini" id="edemo-total-status">После оценки сочинения</p>','<p>Ваш результат</p><p class="edemo-mini" id="edemo-total-status">Появится после оценки сочинения</p>',1)
if s1==old1: raise SystemExit('T123-01 total-card anchor not found')
p1.write_text(s1,encoding='utf-8')

old6=p6.read_text(encoding='utf-8')
s=old6
zero='''  var ZERO_REASONS=[\n    {id:"under150",label:"В сочинении меньше 150 слов."},\n    {id:"noTextSupport",label:"Сочинение не опирается на исходный текст."},\n    {id:"copiedOrRetold",label:"Сочинение полностью переписывает или пересказывает исходный текст вместо собственного ответа."}\n  ];\n'''
help_block='''  var CRITERION_HELP={\n    K1:'<ul><li><strong>1 балл</strong> — позиция автора по указанной проблеме сформулирована верно.</li><li><strong>0 баллов</strong> — позиция не сформулирована или сформулирована неверно. Тогда К2 и К3 тоже равны 0.</li></ul>',\n    K2:'<ul><li><strong>3 балла</strong> — есть 2 важных примера из текста, оба пояснены; указана смысловая связь между ними и объяснено, в чём она.</li><li><strong>2 балла</strong> — оба примера и пояснения есть, но связь между примерами не указана, указана неверно или не объяснена.</li><li><strong>1 балл</strong> — есть 1 важный пример из текста и его пояснение.</li><li><strong>0 баллов</strong> — нет засчитываемого примера с пояснением, комментарий не опирается на текст, заменён пересказом/большой цитатой или отсутствует.</li></ul><p class="edemo-mini">Пример без пояснения не засчитывается. Фактическая ошибка в комментарии учитывается по К4.</p>',\n    K3:'<ul><li><strong>2 балла</strong> — своё отношение к позиции автора сформулировано и обосновано, приведён пример-аргумент.</li><li><strong>1 балл</strong> — отношение сформулировано и обосновано, но примера-аргумента нет; либо пример есть, но отношение явно не сформулировано.</li><li><strong>0 баллов</strong> — только формальное «согласен/не согласен», нет полноценного отношения и обоснования или они не соответствуют проблеме.</li></ul><p class="edemo-mini">Для примера-аргумента подходят читательский, историко-культурный или жизненный опыт. Он не должен просто повторять мысли автора.</p>',\n    K4:'<ul><li><strong>1 балл</strong> — фактических ошибок нет.</li><li><strong>0 баллов</strong> — есть хотя бы одна фактическая ошибка.</li></ul><p class="edemo-mini">Проверьте имена, события, сведения о тексте и факты, на которые вы ссылаетесь.</p>',\n    K5:'<ul><li><strong>2 балла</strong> — логических ошибок нет.</li><li><strong>1 балл</strong> — 1–2 логические ошибки.</li><li><strong>0 баллов</strong> — 3 логические ошибки или больше.</li></ul><p class="edemo-mini">Проверьте, не противоречат ли части сочинения друг другу и понятно ли связаны мысли.</p>',\n    K6:'<ul><li><strong>1 балл</strong> — этических нарушений нет.</li><li><strong>0 баллов</strong> — есть недопустимые или оскорбительные высказывания, нецензурная брань либо иной материал, нарушающий этические нормы или законодательство.</li></ul>',\n    K7:'<ul><li><strong>3 балла</strong> — орфографических ошибок нет.</li><li><strong>2 балла</strong> — 1–2 ошибки.</li><li><strong>1 балл</strong> — 3–4 ошибки.</li><li><strong>0 баллов</strong> — 5 ошибок или больше.</li></ul>',\n    K8:'<ul><li><strong>3 балла</strong> — пунктуационных ошибок нет.</li><li><strong>2 балла</strong> — 1–2 ошибки.</li><li><strong>1 балл</strong> — 3–4 ошибки.</li><li><strong>0 баллов</strong> — 5 ошибок или больше.</li></ul>',\n    K9:'<ul><li><strong>3 балла</strong> — грамматических ошибок нет.</li><li><strong>2 балла</strong> — 1–2 ошибки.</li><li><strong>1 балл</strong> — 3–4 ошибки.</li><li><strong>0 баллов</strong> — 5 ошибок или больше.</li></ul>',\n    K10:'<ul><li><strong>3 балла</strong> — речевых ошибок нет.</li><li><strong>2 балла</strong> — 1–2 ошибки.</li><li><strong>1 балл</strong> — 3–4 ошибки.</li><li><strong>0 баллов</strong> — 5 ошибок или больше.</li></ul>'\n  };\n  function criterionHelp(id){return '<details class="edemo-criterion-help"><summary>Как оценивать</summary><div>'+CRITERION_HELP[id]+'</div></details>';}\n'''
if zero not in s: raise SystemExit('criteria help anchor missing')
s=s.replace(zero,zero+'\n'+help_block,1)

css_old='''#ege-demo-2026 .edemo-scan-preview img{display:block;max-width:100%;max-height:420px;object-fit:contain}\\\n#ege-demo-2026 .edemo-transfer-text'''
css_new='''#ege-demo-2026 .edemo-scan-preview img{display:block;max-width:100%;max-height:420px;object-fit:contain}\\\n#ege-demo-2026 .edemo-scan-open{display:block;width:100%;padding:0;border:0;background:transparent;color:inherit;font:inherit;cursor:zoom-in}\\\n#ege-demo-2026 .edemo-scan-open img{margin:0 auto}\\\n#ege-demo-2026 .edemo-scan-open span{display:block;margin-top:8px;font-size:13px;font-weight:700;color:#315fb5}\\\n#ege-demo-2026 .edemo-criterion-help{margin-top:8px}\\\n#ege-demo-2026 .edemo-criterion-help summary{cursor:pointer;font-weight:750;color:#315fb5}\\\n#ege-demo-2026 .edemo-criterion-help ul{margin:8px 0 0;padding-left:20px}\\\n#ege-demo-2026 .edemo-criterion-help li{margin:6px 0;line-height:1.45}\\\n#edemo-scan-lightbox{position:fixed;inset:0;z-index:100000;background:rgba(11,20,32,.88);display:flex;align-items:center;justify-content:center;padding:16px}\\\n#edemo-scan-lightbox .edemo-scan-dialog{width:min(96vw,1400px);height:min(94vh,1000px);display:flex;flex-direction:column;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 24px 70px rgba(0,0,0,.4)}\\\n#edemo-scan-lightbox .edemo-scan-toolbar{display:flex;gap:8px;align-items:center;padding:10px 12px;border-bottom:1px solid #dfe4eb;background:#f7f9fc}\\\n#edemo-scan-lightbox .edemo-scan-toolbar button{min-width:42px;min-height:38px;padding:7px 12px;border:1px solid #c9d3df;border-radius:9px;background:#fff;color:#17324d;font:inherit;font-weight:750;cursor:pointer}\\\n#edemo-scan-lightbox .edemo-scan-close{margin-left:auto}\\\n#edemo-scan-lightbox .edemo-scan-viewport{flex:1;min-height:0;overflow:auto;padding:18px;background:#eef1f5;text-align:center}\\\n#edemo-scan-lightbox .edemo-scan-viewport img{display:block;height:auto;max-width:none;max-height:none;margin:auto;box-shadow:0 4px 18px rgba(0,0,0,.16)}\\\n@media(max-width:560px){#edemo-scan-lightbox{padding:0}#edemo-scan-lightbox .edemo-scan-dialog{width:100vw;height:100vh;border-radius:0}#edemo-scan-lightbox .edemo-scan-toolbar{flex-wrap:wrap}}\\\n#ege-demo-2026 .edemo-transfer-text'''
if css_old not in s: raise SystemExit('zoom css anchor missing')
s=s.replace(css_old,css_new,1)

mount='''  function mountCompletedEssay(){\n'''
zoom_funcs='''  var scanZoomReturnFocus=null,scanZoomKeyHandler=null;\n  function closeScanZoom(){var overlay=byId("edemo-scan-lightbox");if(!overlay)return;if(scanZoomKeyHandler)document.removeEventListener("keydown",scanZoomKeyHandler);scanZoomKeyHandler=null;overlay.remove();if(scanZoomReturnFocus&&typeof scanZoomReturnFocus.focus==="function")scanZoomReturnFocus.focus();scanZoomReturnFocus=null;}\n  function openScanZoom(src,alt,trigger){\n    closeScanZoom();scanZoomReturnFocus=trigger||document.activeElement;var overlay=document.createElement("div");overlay.id="edemo-scan-lightbox";overlay.setAttribute("role","dialog");overlay.setAttribute("aria-modal","true");overlay.setAttribute("aria-label","Увеличенное фото сочинения");\n    overlay.innerHTML='<div class="edemo-scan-dialog"><div class="edemo-scan-toolbar"><button type="button" data-scan-zoom="out" aria-label="Уменьшить">−</button><button type="button" data-scan-zoom="reset">По размеру</button><button type="button" data-scan-zoom="in" aria-label="Увеличить">+</button><button type="button" class="edemo-scan-close" data-scan-close>Закрыть</button></div><div class="edemo-scan-viewport"><img alt="'+escapeHtml(alt||"Фото сочинения")+'" src="'+src+'"></div></div>';document.body.appendChild(overlay);\n    var img=overlay.querySelector("img"),zoom=1,baseWidth=0;function applyZoom(){if(baseWidth>0)img.style.width=Math.max(1,Math.round(baseWidth*zoom))+"px";overlay.setAttribute("data-zoom",zoom.toFixed(2));}function fitImage(){var nw=img.naturalWidth||1,nh=img.naturalHeight||1,fit=Math.min((window.innerWidth*.88)/nw,(window.innerHeight*.72)/nh,1);baseWidth=Math.max(1,nw*fit);applyZoom();}if(img.complete)fitImage();else img.addEventListener("load",fitImage,{once:true});\n    overlay.querySelector('[data-scan-zoom="in"]').addEventListener("click",function(){zoom=Math.min(4,zoom+.25);applyZoom();});overlay.querySelector('[data-scan-zoom="out"]').addEventListener("click",function(){zoom=Math.max(.5,zoom-.25);applyZoom();});overlay.querySelector('[data-scan-zoom="reset"]').addEventListener("click",function(){zoom=1;applyZoom();});overlay.querySelector('[data-scan-close]').addEventListener("click",closeScanZoom);overlay.addEventListener("click",function(e){if(e.target===overlay)closeScanZoom();});scanZoomKeyHandler=function(e){if(e.key==="Escape")closeScanZoom();};document.addEventListener("keydown",scanZoomKeyHandler);overlay.querySelector('[data-scan-close]').focus();\n  }\n\n'''
if mount not in s: raise SystemExit('zoom function anchor missing')
s=s.replace(mount,zoom_funcs+mount,1)

old_scan='''    var scan=byId("edemo-essay-scan");if(scan)scan.addEventListener("change",function(e){var f=e.target.files&&e.target.files[0],preview=byId("edemo-scan-preview");if(!f)return;reviewState.sourceFileName=f.name;saveReviewState();if(/^image\\//.test(f.type)){var reader=new FileReader();reader.onload=function(){preview.innerHTML='<img alt="Предпросмотр рукописного сочинения" src="'+reader.result+'">';};reader.readAsDataURL(f);}else preview.textContent="Выбран файл: "+f.name;});'''
new_scan='''    var scan=byId("edemo-essay-scan");if(scan)scan.addEventListener("change",function(e){var f=e.target.files&&e.target.files[0],preview=byId("edemo-scan-preview");if(!f)return;reviewState.sourceFileName=f.name;saveReviewState();if(/^image\\//.test(f.type)){var reader=new FileReader();reader.onload=function(){preview.innerHTML='<button type="button" class="edemo-scan-open" aria-label="Увеличить фото сочинения"><img alt="Предпросмотр рукописного сочинения" src="'+reader.result+'"><span>Нажмите, чтобы увеличить</span></button>';var opener=preview.querySelector(".edemo-scan-open");if(opener)opener.addEventListener("click",function(){openScanZoom(reader.result,"Фото рукописного сочинения",opener);});};reader.readAsDataURL(f);}else preview.textContent="Выбран файл: "+f.name;});'''
if old_scan not in s: raise SystemExit('scan handler anchor missing')
s=s.replace(old_scan,new_scan,1)

old_general='''row.className="edemo-criterion";row.innerHTML='<div><strong>'+c.label+'</strong><br><span class="edemo-mini">Максимум: '+c.max+(dep?' · если К1 = 0, здесь тоже 0':'')+'</span></div><select data-review-score="'+c.id+'"'+(dep?' disabled':'')+'>'+opts+'</select>';'''
new_general='''row.className="edemo-criterion";row.innerHTML='<div><strong>'+c.label+'</strong><br><span class="edemo-mini">Максимум: '+c.max+(dep?' · если К1 = 0, здесь тоже 0':'')+'</span>'+criterionHelp(c.id)+'</div><select data-review-score="'+c.id+'"'+(dep?' disabled':'')+'>'+opts+'</select>';'''
if old_general not in s: raise SystemExit('K1-K6 row anchor missing')
s=s.replace(old_general,new_general,1)

old_error='''row.innerHTML='<strong>'+k+'. '+ERROR_LABELS[k]+'</strong><p class="edemo-mini">Найдено: '+confirmed.length+' · стоит проверить: '+possible.length+'</p>'''
new_error='''row.innerHTML='<strong>'+k+'. '+ERROR_LABELS[k]+'</strong>'+criterionHelp(k)+'<p class="edemo-mini">Найдено: '+confirmed.length+' · стоит проверить: '+possible.length+'</p>'''
if old_error not in s: raise SystemExit('K7-K10 row anchor missing')
s=s.replace(old_error,new_error,1)

old_total='''    var old=byId("edemo-diagnostic24");if(old)old.remove();var total=byId("edemo-total-score"),totalStatus=byId("edemo-total-status");if(total)total.textContent="—";if(totalStatus)totalStatus.textContent="После оценки сочинения";'''
new_total='''    var old=byId("edemo-diagnostic24");if(old)old.remove();var total=byId("edemo-total-score"),totalStatus=byId("edemo-total-status"),shortEl=byId("edemo-short-score"),shortScore=shortEl?Number(shortEl.textContent):NaN;if(score!==null&&Number.isFinite(shortScore)){if(total)total.textContent=shortScore+score;if(totalStatus)totalStatus.textContent="Задания 1–26: "+shortScore+" + сочинение: "+score+" (по вашей оценке)";}else{if(total)total.textContent="—";if(totalStatus)totalStatus.textContent="Появится после оценки сочинения";}'''
if old_total not in s: raise SystemExit('total score anchor missing')
s=s.replace(old_total,new_total,1)

p6.write_text(s,encoding='utf-8')

pv=preview.read_text(encoding='utf-8')
if old1 not in pv: raise SystemExit('PREVIEW old T123-01 missing')
pv=pv.replace(old1,s1,1)
if old6 not in pv: raise SystemExit('PREVIEW old T123-06 missing')
pv=pv.replace(old6,s,1)
preview.write_text(pv,encoding='utf-8')

# Browser regression: criterion help, total, scan zoom.
bt=base/'test-russian-task27-browser.py';t=bt.read_text(encoding='utf-8')
anchor="""    check(page.locator('#edemo-transferred-essay').count()==1,'paper result has editable transferred text')\n    page.fill('#edemo-transferred-essay','Это пример , текста.')\n"""
block="""    check(page.locator('#edemo-transferred-essay').count()==1,'paper result has editable transferred text')\n    scan_svg=b'<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"800\" height=\"1200\"><rect width=\"800\" height=\"1200\" fill=\"white\"/><path d=\"M80 140h640M80 220h640M80 300h640\" stroke=\"black\" stroke-width=\"8\"/></svg>'\n    page.set_input_files('#edemo-essay-scan',files={'name':'essay-scan.svg','mimeType':'image/svg+xml','buffer':scan_svg})\n    check(page.locator('.edemo-scan-open').count()==1,'image preview has zoom opener')\n    page.click('.edemo-scan-open')\n    check(page.locator('#edemo-scan-lightbox').count()==1,'scan lightbox opens')\n    page.click('[data-scan-zoom=\"in\"]')\n    check(page.locator('#edemo-scan-lightbox').get_attribute('data-zoom')=='1.25','scan zoom in works')\n    page.keyboard.press('Escape')\n    check(page.locator('#edemo-scan-lightbox').count()==0,'scan lightbox closes with Escape')\n    page.fill('#edemo-transferred-essay','Это пример , текста.')\n"""
if anchor not in t: raise SystemExit('browser paper anchor missing')
t=t.replace(anchor,block,1)
# Add structural checks for all 10 help controls.
needle="""    check(page.get_by_text('Проверка ошибок',exact=False).count()>=1,'student-friendly analysis label shown')\n"""
repl=needle+"""    check(page.locator('details.edemo-criterion-help').count()==10,'all K1-K10 have optional scoring help')\n"""
if needle not in t: raise SystemExit('browser help anchor missing')
t=t.replace(needle,repl,1)
bt.write_text(t,encoding='utf-8')

# Unit test for displayed total formula via source contract.
ut=base/'test-russian-task27-v4.2.js';u=ut.read_text(encoding='utf-8')
if 'displayed demo total formula' not in u:
    insert="\ncheck(/shortScore\\+score/.test(hotfix),'displayed demo total formula');\ncheck(/criterionHelp\\(c\\.id\\)/.test(hotfix)&&/criterionHelp\\(k\\)/.test(hotfix),'K1-K10 optional scoring help wired');\n"
    pos=u.rfind("console.log(")
    if pos<0: raise SystemExit('unit test console anchor missing')
    u=u[:pos]+insert+u[pos:]
ut.write_text(u,encoding='utf-8')

# Contracts/docs.
sp=base/'SUBJECT-PROFILE-RUSSIAN.json';obj=json.loads(sp.read_text(encoding='utf-8'))
inv=obj['invariants']
inv['essay_criterion_help']='optional expandable student-facing guidance for K1-K10, aligned to 2026 criteria'
inv['displayed_demo_total']='after essay self-assessment: tasks 1-26 score + essay self-assessment, out of 50; clearly labeled as based on user essay assessment'
inv['official_total']='official expert assessment remains conceptually distinct from the displayed demo result'
sp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

yp=base/'YEAR-PASSPORT-2026.json';obj=json.loads(yp.read_text(encoding='utf-8'))
rv=obj['task27_review'];rv['new_attempt_reset']='T123-06 guard clears review state when core is missing, idle or invalid; preserves running/finished state';rv['criterion_help']='expandable guidance for K1-K10';rv['displayed_demo_total']='short score + essay self-assessment, max 50, labeled as based on user assessment'
yp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

ic=base/'ege-russkiy-demoversiya-INTERACTION-CONTRACT.json';obj=json.loads(ic.read_text(encoding='utf-8'))
t27=[x for x in obj['tasks'] if x.get('number')==27][0];t27['criterion_help']='expandable K1-K10 guidance';t27['displayed_demo_total']='tasks 1-26 automatic score + essay self-assessment, out of 50, with explicit user-assessment label'
ic.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

cp=base/'CHANGELOG.txt';c=cp.read_text(encoding='utf-8')
entry='''v4.2 — ESSAY REVIEW UX\n- Для каждого критерия К1–К10 добавлена раскрываемая подсказка «Как оценивать».\n- После заполнения критериев показывается результат за всю демоверсию из 50: задания 1–26 + оценка сочинения.\n- Рядом с итогом явно указано, что часть за сочинение основана на оценке самого пользователя.\n- Для прикреплённого изображения сочинения добавлен крупный просмотр с увеличением и уменьшением.\n\n'''
mark='ЕГЭ РУССКИЙ ЯЗЫК 2026 — CHANGELOG\n\n'
if 'v4.2 — ESSAY REVIEW UX' not in c:c=c.replace(mark,mark+entry,1)
cp.write_text(c,encoding='utf-8')

ap=base/'AFTER-PUBLISH-CHECKLIST.txt';a=ap.read_text(encoding='utf-8')
extra='''\n17а. У каждого К1–К10 раскрыть «Как оценивать»: подсказка присутствует и соответствует шкале критерия.\n17б. Заполнить все К1–К10: карточка «Ваш результат» показывает сумму заданий 1–26 и сочинения из 50, а подпись показывает обе составляющие и пометку «по вашей оценке».\n17в. Прикрепить изображение сочинения: по клику на превью открывается крупный просмотр; работают +, −, «По размеру», «Закрыть» и Esc.\n'''
if '17а. У каждого К1–К10' not in a:a+=extra
ap.write_text(a,encoding='utf-8')

# runtime manifest
mp=base/'MANIFEST-SHA256.txt';m=mp.read_text(encoding='utf-8')
for fn in ['ege-russkiy-demoversiya-T123-01.txt','ege-russkiy-demoversiya-T123-06.txt']:
    h=hashlib.sha256((base/fn).read_bytes()).hexdigest();m=re.sub(r'^[0-9a-f]{64}  '+re.escape(fn)+r'$',h+'  '+fn,m,flags=re.M)
mp.write_text(m,encoding='utf-8')

if p6.stat().st_size>=42500: raise SystemExit(f'T123-06 size limit exceeded: {p6.stat().st_size}')
print('PATCH OK; T123-06 bytes',p6.stat().st_size)
