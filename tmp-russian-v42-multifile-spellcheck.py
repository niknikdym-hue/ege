from pathlib import Path
import hashlib, json, re

base=Path('ege-russkiy-demoversiya-2026-v4.2')
addon=base/'ege-russkiy-demoversiya-T123-07.txt'
addon.write_text(r'''<script>
(function(){
  "use strict";
  var ROOT_ID="ege-demo-2026";
  var REVIEW_KEY="eksamio_ege_russian_demo_2026_v4_2_task27_review";
  var SPELL_KEY="eksamio_ege_russian_demo_2026_v4_2_spelling_check";
  var api=null,scanItems=[],zoomKeyHandler=null,zoomReturnFocus=null,observer=null;
  function byId(id){return document.getElementById(id);}
  function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
  function loadSpell(){try{var x=JSON.parse(localStorage.getItem(SPELL_KEY)||"{}");return x&&typeof x==="object"?x:{};}catch(e){return{};}}
  function saveSpell(status,message){try{localStorage.setItem(SPELL_KEY,JSON.stringify({status:status,message:message||""}));}catch(e){}}
  function essayText(){var frozen=byId("edemo-frozen-essay"),transfer=byId("edemo-transferred-essay");return transfer?transfer.value:(frozen?frozen.textContent:"");}
  function addStyles(){if(byId("edemo-task27-addon-style"))return;var s=document.createElement("style");s.id="edemo-task27-addon-style";s.textContent='\
#ege-demo-2026 .edemo-file-native{position:absolute!important;width:1px!important;height:1px!important;opacity:0!important;overflow:hidden!important;pointer-events:none!important}\
#ege-demo-2026 .edemo-file-pick{display:inline-flex!important;margin:10px 0 6px;background:#315fb5!important;color:#fff!important;-webkit-text-fill-color:#fff!important;border:2px solid #244b92!important;box-shadow:0 0 0 4px rgba(49,95,181,.12)!important;cursor:pointer}\
#ege-demo-2026 .edemo-file-pick:hover{background:#244b92!important}\
#ege-demo-2026 .edemo-scan-preview--multi{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;align-items:stretch;justify-content:stretch;text-align:left;overflow:visible}\
#ege-demo-2026 .edemo-scan-item{border:1px solid #d9e0e9;border-radius:10px;padding:9px;background:#fff;min-width:0}\
#ege-demo-2026 .edemo-scan-item .edemo-scan-open{height:100%}\
#ege-demo-2026 .edemo-scan-item-name{display:block;margin-top:6px;font-size:12px;overflow-wrap:anywhere}\
#ege-demo-2026 .edemo-scan-pdf{display:flex;min-height:120px;flex-direction:column;justify-content:center;gap:8px}\
#ege-demo-2026 .edemo-check-action{margin-top:14px}\
#ege-demo-2026 .edemo-check-status{margin:10px 0 0;font-weight:700}\
#ege-demo-2026 .edemo-speller-credit{margin:10px 0 0;color:inherit}\
#ege-demo-2026 .edemo-speller-credit a{color:inherit}\
';document.head.appendChild(s);}
  function closeZoom(){var o=byId("edemo-scan-lightbox");if(o)o.remove();if(zoomKeyHandler)document.removeEventListener("keydown",zoomKeyHandler);zoomKeyHandler=null;if(zoomReturnFocus&&zoomReturnFocus.focus)zoomReturnFocus.focus();zoomReturnFocus=null;}
  function openZoom(src,alt,trigger){closeZoom();zoomReturnFocus=trigger||document.activeElement;var o=document.createElement("div");o.id="edemo-scan-lightbox";o.setAttribute("role","dialog");o.setAttribute("aria-modal","true");o.setAttribute("aria-label","Увеличенное фото сочинения");o.innerHTML='<div class="edemo-scan-dialog"><div class="edemo-scan-toolbar"><button type="button" data-scan-zoom="out">−</button><button type="button" data-scan-zoom="reset">По размеру</button><button type="button" data-scan-zoom="in">+</button><button type="button" class="edemo-scan-close" data-scan-close>Закрыть</button></div><div class="edemo-scan-viewport"><img alt="'+esc(alt||"Фото сочинения")+'" src="'+src+'"></div></div>';document.body.appendChild(o);var img=o.querySelector("img"),z=1,bw=0;function apply(){if(bw)img.style.width=Math.max(1,Math.round(bw*z))+"px";o.setAttribute("data-zoom",z.toFixed(2));}function fit(){var nw=img.naturalWidth||1,nh=img.naturalHeight||1,f=Math.min((window.innerWidth*.88)/nw,(window.innerHeight*.72)/nh,1);bw=Math.max(1,nw*f);apply();}if(img.complete)fit();else img.addEventListener("load",fit,{once:true});o.querySelector('[data-scan-zoom="in"]').onclick=function(){z=Math.min(4,z+.25);apply();};o.querySelector('[data-scan-zoom="out"]').onclick=function(){z=Math.max(.5,z-.25);apply();};o.querySelector('[data-scan-zoom="reset"]').onclick=function(){z=1;apply();};o.querySelector('[data-scan-close]').onclick=closeZoom;o.onclick=function(e){if(e.target===o)closeZoom();};zoomKeyHandler=function(e){if(e.key==="Escape")closeZoom();};document.addEventListener("keydown",zoomKeyHandler);o.querySelector('[data-scan-close]').focus();}
  function renderScans(){var p=byId("edemo-scan-preview");if(!p)return;p.classList.add("edemo-scan-preview--multi");if(!scanItems.length){p.textContent="Добавьте фото или сканы страниц.";return;}p.innerHTML="";scanItems.forEach(function(it,i){var card=document.createElement("div");card.className="edemo-scan-item";if(it.kind==="image"&&it.src){card.innerHTML='<button type="button" class="edemo-scan-open"><img alt="Страница '+(i+1)+' сочинения" src="'+it.src+'"><span>Страница '+(i+1)+' · увеличить</span></button><span class="edemo-scan-item-name">'+esc(it.name)+'</span>';card.querySelector("button").onclick=function(){openZoom(it.src,"Страница "+(i+1)+" сочинения",this);};}else if(it.kind==="pdf"){card.innerHTML='<div class="edemo-scan-pdf"><strong>Страница/файл '+(i+1)+'</strong><span class="edemo-scan-item-name">'+esc(it.name)+'</span><a href="'+it.src+'" target="_blank" rel="noopener">Открыть PDF</a></div>';}else card.textContent="Подготавливаю файл…";p.appendChild(card);});}
  function enhanceFiles(){var input=byId("edemo-essay-scan");if(!input||input.getAttribute("data-multi-ready"))return;input.setAttribute("data-multi-ready","true");input.multiple=true;input.classList.add("edemo-file-native");var label=document.createElement("label");label.htmlFor=input.id;label.className="ep-button edemo-file-pick";label.textContent="Добавить фото/сканы";input.insertAdjacentElement("afterend",label);var note=document.createElement("p");note.className="edemo-mini";note.textContent="Можно выбрать сразу несколько файлов или добавлять страницы по очереди.";label.insertAdjacentElement("afterend",note);var preview=byId("edemo-scan-preview");if(preview){preview.classList.add("edemo-scan-preview--multi");preview.textContent="Добавьте фото или сканы страниц.";}input.addEventListener("change",function(e){Array.from(e.target.files||[]).forEach(function(f){var item={name:f.name,kind:/^image\//.test(f.type)?"image":(f.type==="application/pdf"?"pdf":"other"),src:""};scanItems.push(item);if(item.kind==="image"){var r=new FileReader();r.onload=function(){item.src=r.result;renderScans();};r.readAsDataURL(f);}else if(item.kind==="pdf"){item.src=URL.createObjectURL(f);renderScans();}else renderScans();});input.value="";renderScans();});}
  function chunks(text){var out=[],s=String(text||"").trim();while(s.length){if(s.length<=700){out.push(s);break;}var cut=s.lastIndexOf(" ",700);if(cut<350)cut=700;out.push(s.slice(0,cut));s=s.slice(cut).trim();}return out;}
  function jsonp(text){return new Promise(function(resolve,reject){var cb="__edemoSpeller"+Date.now()+Math.random().toString(36).slice(2),script=document.createElement("script"),done=false,t=setTimeout(function(){finish();reject(new Error("timeout"));},8000);function finish(){if(done)return;done=true;clearTimeout(t);try{delete window[cb];}catch(e){window[cb]=undefined;}script.remove();}window[cb]=function(data){finish();resolve(Array.isArray(data)?data:[]);};script.onerror=function(){finish();reject(new Error("network"));};script.src="https://speller.yandex.net/services/spellservice.json/checkText?lang=ru&callback="+encodeURIComponent(cb)+"&text="+encodeURIComponent(text);document.head.appendChild(script);});}
  function mergeSpelling(local,rows){var seen={};local.possible.K7.forEach(function(x){seen[x.id]=1;});rows.forEach(function(x,i){if(!x||!(x.code===1||x.code===3)||!x.word)return;var id="speller-k7-"+String(x.word).toLowerCase()+"-"+i;if(seen[id])return;var sug=x.s&&x.s.length?x.s.slice(0,3).join(", "):"";local.possible.K7.push({id:id,criterion:"K7",status:"possible",message:"Проверьте «"+x.word+"»"+(sug?" — варианты: "+sug:".")+"",evidence:"Возможная орфографическая ошибка."});seen[id]=1;});local.version="builtin-plus-yandex-speller-v1";return local;}
  async function runCheck(){api=window.__edemoRussian2026Task27Review;if(!api)return;var text=essayText().trim();if(!text){saveSpell("failed","Сначала введите текст сочинения.");decorateCheck();return;}saveSpell("checking","Проверяю текст…");decorateCheck();var local=api.analyzeEssayText(text);try{var rows=[],parts=chunks(text);for(var i=0;i<parts.length;i++)rows=rows.concat(await jsonp(parts[i]));api.submitAnalysis(mergeSpelling(local,rows));var count=rows.filter(function(x){return x&&((x.code===1)||(x.code===3));}).length;saveSpell("complete",count?"Проверка завершена. Найдено мест для проверки: "+count+".":"Проверка завершена. Явных орфографических ошибок не найдено.");}catch(e){api.submitAnalysis(local);saveSpell("failed","Быстрая проверка выполнена, но сервис проверки орфографии сейчас недоступен.");}decorateCheck();}
  function decorateCheck(){var c=byId("edemo-criteria");if(!c)return;var intro=c.querySelector(".ep-panel");if(!intro)return;var wrap=byId("edemo-check-action");if(!wrap){wrap=document.createElement("div");wrap.id="edemo-check-action";wrap.className="edemo-check-action";wrap.innerHTML='<button type="button" class="ep-button" id="edemo-run-text-check">Проверить текст</button><p class="edemo-check-status" id="edemo-check-status"></p><p>После завершения быстрая проверка уже выполнена. Кнопка выше дополнительно проверяет орфографию. Пунктуацию, грамматику и речь проверяйте также по подсказкам К8–К10.</p><p class="edemo-speller-credit">Проверка правописания: <a href="http://api.yandex.ru/speller/" target="_blank" rel="noopener">Яндекс.Спеллер</a></p>';intro.appendChild(wrap);byId("edemo-run-text-check").onclick=runCheck;}var state=loadSpell(),btn=byId("edemo-run-text-check"),st=byId("edemo-check-status");if(btn){btn.disabled=state.status==="checking";btn.textContent=state.status==="checking"?"Проверяю…":(state.status==="complete"?"Проверить ещё раз":"Проверить текст");}if(st)st.textContent=state.message||(api&&essayText().trim()?"Быстрая проверка выполнена. Дополнительная проверка орфографии ещё не запускалась.":"Сначала введите текст сочинения.");}
  function resetSpellOnEdit(){var t=byId("edemo-transferred-essay");if(t&&!t.getAttribute("data-spell-reset")){t.setAttribute("data-spell-reset","true");t.addEventListener("input",function(){saveSpell("not_run","");decorateCheck();});}}
  function enhance(){api=window.__edemoRussian2026Task27Review;if(!api)return;addStyles();enhanceFiles();resetSpellOnEdit();decorateCheck();}
  function init(){var root=byId(ROOT_ID);if(!root)return;enhance();observer=new MutationObserver(function(){enhance();});observer.observe(root,{childList:true,subtree:true,attributes:true,attributeFilter:["data-state"]});}
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();
</script>''',encoding='utf-8')

# Browser regression: compose T123-07 too, stub Yandex Speller, test explicit check and multiple files.
p=base/'test-russian-task27-browser.py'
s=p.read_text(encoding='utf-8')
s=s.replace("hotfix=(base/'ege-russkiy-demoversiya-T123-06.txt').read_text(encoding='utf-8')\nhtml=preview.replace('</body>',hotfix+'</body>')", "hotfix=(base/'ege-russkiy-demoversiya-T123-06.txt').read_text(encoding='utf-8')\naddon=(base/'ege-russkiy-demoversiya-T123-07.txt').read_text(encoding='utf-8')\nhtml=preview.replace('</body>',hotfix+addon+'</body>')")
s=s.replace("    page.on('pageerror',lambda e:errors.append(f'pageerror: {e}'))\n", "    page.on('pageerror',lambda e:errors.append(f'pageerror: {e}'))\n    from urllib.parse import urlparse,parse_qs\n    def speller_route(route):\n        q=parse_qs(urlparse(route.request.url).query);cb=q.get('callback',[''])[0]\n        body=f'{cb}([{json.dumps({\"code\":1,\"pos\":0,\"row\":0,\"col\":0,\"len\":6,\"word\":\"карова\",\"s\":[\"корова\"]},ensure_ascii=False)}]);'\n        route.fulfill(status=200,content_type='application/javascript; charset=utf-8',body=body)\n    page.route('https://speller.yandex.net/**',speller_route)\n")
s=s.replace("    original='Это это исходное сочинение без точки'", "    original='Карова. Это это исходное сочинение без точки'")
anchor="    check(page.get_by_text('может заметить не все ошибки',exact=False).count()>=1,'automatic-check limitation shown')\n"
insert=anchor+"    check(page.locator('#edemo-run-text-check').count()==1,'explicit text-check button shown')\n    page.click('#edemo-run-text-check')\n    page.wait_for_function(\"JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_2_spelling_check')||'{}').status==='complete'\")\n    check(page.get_by_text('Проверка завершена',exact=False).count()>=1,'spelling-check completion is visible')\n    checked=page.evaluate(\"JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_2_task27_review'))\")\n    check(any('карова' in x['message'].lower() for x in checked['possibleFindings']['K7']),'external spelling candidate merged into K7')\n"
if anchor not in s: raise SystemExit('browser check anchor missing')
s=s.replace(anchor,insert,1)
old="    scan_svg=b'<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"800\" height=\"1200\"><rect width=\"800\" height=\"1200\" fill=\"white\"/><path d=\"M80 140h640M80 220h640M80 300h640\" stroke=\"black\" stroke-width=\"8\"/></svg>'\n    page.set_input_files('#edemo-essay-scan',files={'name':'essay-scan.svg','mimeType':'image/svg+xml','buffer':scan_svg})\n    check(page.locator('.edemo-scan-open').count()==1,'image preview has zoom opener')\n"
new="    scan_svg=b'<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"800\" height=\"1200\"><rect width=\"800\" height=\"1200\" fill=\"white\"/><path d=\"M80 140h640M80 220h640M80 300h640\" stroke=\"black\" stroke-width=\"8\"/></svg>'\n    check(page.locator('#edemo-essay-scan').get_attribute('multiple') is not None,'scan input supports multiple files')\n    check(page.locator('.edemo-file-pick').is_visible(),'highlighted add-files button visible')\n    page.set_input_files('#edemo-essay-scan',files=[{'name':'essay-page-1.svg','mimeType':'image/svg+xml','buffer':scan_svg},{'name':'essay-page-2.svg','mimeType':'image/svg+xml','buffer':scan_svg}])\n    page.wait_for_function(\"document.querySelectorAll('.edemo-scan-open').length===2\")\n    check(page.locator('.edemo-scan-open').count()==2,'two essay pages previewed')\n"
if old not in s: raise SystemExit('browser scan anchor missing')
s=s.replace(old,new,1)
s=s.replace("PASS real-preview task27 browser: T123-01...06", "PASS real-preview task27 browser: T123-01...07")
p.write_text(s,encoding='utf-8')

# Unit structural assertions for new block.
p=base/'test-russian-task27-v4.2.js'
s=p.read_text(encoding='utf-8')
add="\nconst addon=fs.readFileSync(path.join(__dirname,'ege-russkiy-demoversiya-T123-07.txt'),'utf8');\neq('T123-07 multiple file input enhancement',/input\\.multiple=true/.test(addon),true);\neq('T123-07 explicit text check',/Проверить текст/.test(addon)&&/speller\\.yandex\\.net/.test(addon),true);\neq('T123-07 does not auto-confirm speller findings',/possible\\.K7\\.push/.test(addon)&&!/confirmed\\.K7\\.push/.test(addon),true);\n"
marker="if(fails.length){console.error(fails.join('\\n'));process.exit(1)}"
if marker not in s: raise SystemExit('unit marker missing')
s=s.replace(marker,add+marker,1)
p.write_text(s,encoding='utf-8')

# Current installation/runtime docs.
for name in ['ege-russkiy-demoversiya-INSTALLATION.txt','TASK27-HOTFIX-INSTALLATION.txt','TASK27-HOTFIX-README.txt','ege-russkiy-demoversiya-SUBJECT-SPECIFICATION-2026.txt']:
    p=base/name
    if p.exists():
        t=p.read_text(encoding='utf-8')
        t=t.replace('T123-01 … T123-06','T123-01 … T123-07').replace('T123-01…T123-06','T123-01…T123-07').replace('T123-01...T123-06','T123-01...T123-07')
        if 'T123-07' in t and 'дополнительная проверка орфографии' not in t:
            t+='\nT123-07: несколько фото/сканов рукописного сочинения; явная кнопка проверки текста; дополнительная проверка орфографии после нажатия пользователем.\n'
        p.write_text(t,encoding='utf-8')

# Contracts: add T123-07 to required arrays and describe behavior.
for name in ['SUBJECT-PROFILE-RUSSIAN.json','YEAR-PASSPORT-2026.json','ege-russkiy-demoversiya-INTERACTION-CONTRACT.json']:
    p=base/name
    data=json.loads(p.read_text(encoding='utf-8'))
    def walk(x):
        if isinstance(x,dict):
            for k,v in list(x.items()):
                if k=='required_t123_blocks' and isinstance(v,list) and 'T123-06' in v and 'T123-07' not in v:v.append('T123-07')
                walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(data)
    if name=='YEAR-PASSPORT-2026.json':
        r=data.setdefault('task27_review',{});r['multiple_scan_files']=True;r['explicit_post_exam_text_check']=True;r['spelling_check']='Yandex Speller on explicit user action; candidates remain possible only'
    elif name=='SUBJECT-PROFILE-RUSSIAN.json':
        inv=data.setdefault('invariants',{});inv['task27_multiple_scan_files']=True;inv['task27_spelling_check']='explicit user action; spelling candidates are advisory and never auto-confirmed'
    else:
        task=next((x for x in data.get('tasks',[]) if x.get('number')==27),None)
        if task is not None:task['required_t123']='T123-06 + T123-07';task['multiple_scan_files']=True;task['explicit_spelling_check']=True
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')

# Changelog and publish checklist.
p=base/'CHANGELOG.txt';t=p.read_text(encoding='utf-8');head='ЕГЭ РУССКИЙ ЯЗЫК 2026 — CHANGELOG\n\n';entry='v4.2 — MULTIPAGE SCAN + EXPLICIT TEXT CHECK\n- Добавлен T123-07.\n- В бумажном режиме можно выбрать несколько фото/сканов страниц; кнопка выбора файлов выделена.\n- После завершения есть явная кнопка «Проверить текст» и видимый статус проверки.\n- Орфография дополнительно проверяется Яндекс.Спеллером только после нажатия пользователя; найденное остаётся possible и не ставит балл автоматически.\n- К8–К10 остаются осторожной предварительной проверкой и самостоятельной оценкой по подсказкам.\n\n';
if head in t:t=t.replace(head,head+entry,1)
p.write_text(t,encoding='utf-8')
p=base/'AFTER-PUBLISH-CHECKLIST.txt';t=p.read_text(encoding='utf-8');t+='\n17г. Бумажный режим: кнопка «Добавить фото/сканы» заметна; можно выбрать минимум 2 изображения, обе страницы видны и каждую можно увеличить.\n17д. После завершения: видна кнопка «Проверить текст»; после нажатия появляется понятный статус. Проверочная ошибка типа «карова» попадает в К7 как место для проверки и не становится confirmed автоматически.\n';p.write_text(t,encoding='utf-8')

# Runtime manifest: add T123-07 and refresh all runtime hashes.
p=base/'MANIFEST-SHA256.txt';t=p.read_text(encoding='utf-8');lines=t.splitlines();runtime=['ege-russkiy-demoversiya-HEAD.txt','ege-russkiy-demoversiya-SEO.txt']+[f'ege-russkiy-demoversiya-T123-{i:02d}.txt' for i in range(1,8)];prefix=[]
for line in lines:
    if any(line.endswith('  '+f) for f in runtime):continue
    if line.startswith('Порядок T123 в Tilda:'):line='Порядок T123 в Tilda: 01 → 02 → 03 → 04 → 05 → 06 → 07.'
    prefix.append(line)
# insert hashes before order line
hash_lines=[hashlib.sha256((base/f).read_bytes()).hexdigest()+'  '+f for f in runtime]
idx=next((i for i,x in enumerate(prefix) if x.startswith('Порядок T123 в Tilda:')),len(prefix))
prefix[idx:idx]=hash_lines+['']
p.write_text('\n'.join(prefix).rstrip()+"\n",encoding='utf-8')

print('PATCH READY',addon.stat().st_size,'bytes T123-07')
