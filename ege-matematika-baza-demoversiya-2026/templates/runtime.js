(function(){
'use strict';
const C=window.EKSAMIO_MATH_BASE,$=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const INPUT_CONTRACTS=__INPUT_CONTRACTS__;
const intro=$('#mb-intro'),exam=$('#mb-exam'),results=$('#mb-results'),taskEl=$('#mb-task'),gridEl=$('#mb-grid');
let timerHandle=null;
function materialize(){C.assets={};for(const [k,v] of Object.entries(C.assetParts||{}))C.assets[k]='data:image/webp;base64,'+v.join('');C.refs={};for(const [k,v] of Object.entries(C.refParts||{}))C.refs[k]='data:image/webp;base64,'+v.join('');}
materialize();
const tasks=[...C.tasks].sort((a,b)=>a.number-b.number),byNumber=n=>tasks.find(t=>t.number===n);
function emptyState(){return {version:C.contentVersion,active:false,finished:false,current:1,attemptId:null,startedAt:null,deadline:null,variants:{},answers:{},marked:{}}}
function load(){try{const x=JSON.parse(localStorage.getItem(C.storageKey)||'null');if(x&&x.version===C.contentVersion)return Object.assign(emptyState(),x)}catch(e){}return emptyState()}
let state=load();
function warning(show){const e=$('#mb-save-warning');if(e)e.classList.toggle('mb-hidden',!show)}
function save(){try{localStorage.setItem(C.storageKey,JSON.stringify(state));warning(false);return true}catch(e){warning(true);return false}}
function clearSaved(){try{localStorage.removeItem(C.storageKey);warning(false);return true}catch(e){warning(true);return false}}
function fixTypography(s){return String(s==null?'':s).replaceAll('ꞏ','·')}
function esc(s){return fixTypography(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function randomInt(max){if(window.crypto&&crypto.getRandomValues){const a=new Uint32Array(1);crypto.getRandomValues(a);return a[0]%max}return Math.floor(Math.random()*max)}
function assignVariants(){state.variants={};for(const t of tasks)state.variants[t.number]=t.variants[randomInt(t.variants.length)].variant}
function variantFor(n){const t=byNumber(n);if(!t)return null;const chosen=Number(state.variants[n]||t.variants[0].variant);return t.variants.find(v=>v.variant===chosen)||t.variants[0]}
function currentVariant(){return variantFor(state.current)}
function answerObj(n){return state.answers[n]||null}
function canonicalCode(v,a){if(!a)return '';if(v.control==='numeric_input')return a.valid?String(a.value||''):'';if(v.control==='matching_selects_4'){const vals=a.values||[];return vals.length===4&&vals.every(Boolean)?vals.join(''):''}if(v.control==='checkboxes'||v.control==='row_checkboxes')return [...new Set((a.selected||[]).map(String))].sort((x,y)=>Number(x)-Number(y)).join('');return ''}
function isAnswered(n){const v=variantFor(n),a=answerObj(n);if(!v||!a)return false;if(v.control==='numeric_input')return !!(a.valid&&String(a.value||'')!=='');if(v.control==='matching_selects_4')return (a.values||[]).length===4&&(a.values||[]).every(Boolean)&&new Set(a.values).size===4;if(v.control==='checkboxes'||v.control==='row_checkboxes')return (a.selected||[]).length>0;return false}
function score(n){const v=variantFor(n),code=canonicalCode(v,answerObj(n));if(!code)return 0;const forms=(v.canonical_forms||[]).map(String);if(v.order_ignored){const sort=x=>[...x].sort().join('');return forms.some(x=>sort(x)===sort(code))?1:0}return forms.includes(code)?1:0}
function total(){return tasks.reduce((s,t)=>s+score(t.number),0)}
function answeredCount(){return tasks.filter(t=>isAnswered(t.number)).length}
function startNew(){state=emptyState();state.active=true;state.attemptId=String(Date.now())+'-'+Math.random().toString(36).slice(2,10);state.startedAt=Date.now();state.deadline=state.startedAt+C.minutes*60000;assignVariants();save();showExam();render()}
function resume(){if(!state.startedAt||!Object.keys(state.variants||{}).length)return startNew();state.active=true;save();showExam();render()}
function resetAll(){if(!confirm('Удалить сохранённую попытку и начать заново?'))return;clearSaved();state=emptyState();showIntro()}
function showIntro(){clearInterval(timerHandle);intro.classList.remove('mb-hidden');exam.classList.remove('is-active');results.classList.remove('is-active');const has=!!(state.startedAt&&!state.finished);$('#mb-continue').classList.toggle('mb-hidden',!has);$('#mb-reset-intro').classList.toggle('mb-hidden',!has)}
function showExam(){intro.classList.add('mb-hidden');results.classList.remove('is-active');exam.classList.add('is-active');startTimer()}
function sourceTag(v){return `<div class="mb-source-tag">ФИПИ 2026 · позиция ${state.current} · официальный пример ${v.variant}</div>`}
function formula(html){return html?`<div class="mb-formula">${html}</div>`:''}
function tableHtml(t,selectable,a){if(!t)return '';const headers=t.headers||[],rows=t.rows||[],selected=new Set((a&&a.selected||[]).map(String));return `<div class="mb-table-wrap"><table class="mb-table"><thead><tr>${headers.map((h,i)=>`<th>${selectable&&i===0?'Выбор · ':''}${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map((r,ri)=>`<tr>${r.map((cell,ci)=>`<td>${selectable&&ci===0?`<label class="mb-row-select"><input type="checkbox" data-row="${esc(cell)}" ${selected.has(String(cell))?'checked':''}><span>${esc(cell)}</span></label>`:esc(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`}
function arrayBlock(title,items,htmlItems){if(!items||!items.length)return '';return `<div class="mb-table-wrap"><table class="mb-table"><thead><tr><th>${title}</th></tr></thead><tbody>${items.map((x,i)=>`<tr><td>${htmlItems&&htmlItems[i]?htmlItems[i]:esc(x)}</td></tr>`).join('')}</tbody></table></div>`}
function bodyHtml(v){let out=v.prompt_html||'';if(v.formula_mathml)out+=formula(v.formula_mathml);if(v.asset_id&&C.assets[v.asset_id])out+=`<div class="mb-figure"><img src="${C.assets[v.asset_id]}" alt="Иллюстрация к заданию ${state.current}" loading="eager"></div>`;if(v.table)out+=tableHtml(v.table,v.control==='row_checkboxes',answerObj(state.current));if(v.continuation_html)out+=v.continuation_html;if(v.instruction)out+=`<p><strong>${esc(v.instruction)}</strong></p>`;return fixTypography(out)}
function matchingPanel(v){const a=answerObj(state.current)||{values:['','','','']},values=a.values||['','','',''];const left=v.left||[],leftHtml=v.left_html||[],right=v.right||[],rightHtml=v.right_html||[];const optionCount=Math.max(right.length,rightHtml.length);const options=Array.from({length:optionCount},(_,i)=>({value:String(i+1),html:rightHtml[i]||esc(right[i]||'')}));const rows=[0,1,2,3].map(i=>{const leftText=leftHtml[i]||esc(left[i]||String.fromCharCode(1040+i));const opts=['<option value="">Не выбрано</option>'].concat(options.map(o=>`<option value="${o.value}" ${String(values[i]||'')===o.value?'selected':''}>${o.value}</option>`)).join('');return `<div class="mb-match-row"><div class="mb-match-label">${leftText}</div><select class="mb-select" data-pos="${i}" aria-label="Позиция ${i+1}">${opts}</select></div>`}).join('');return `<div class="mb-answerbox"><div class="mb-answer-title">Установите соответствие</div><div class="mb-answer-hint">Для каждой позиции выберите один номер. Повтор одного номера в этом задании не допускается. Код ответа соберётся автоматически.</div>${options.length?`<div class="mb-table-wrap"><table class="mb-table"><thead><tr><th>Номер</th><th>Вариант</th></tr></thead><tbody>${options.map(o=>`<tr><td>${o.value}</td><td>${o.html}</td></tr>`).join('')}</tbody></table></div>`:''}<div class="mb-match">${rows}</div><div class="mb-code" id="mb-code">Код для бланка: ${esc(canonicalCode(v,a)||values.map(x=>x||'—').join(' '))}</div><button class="mb-btn mb-btn--secondary" type="button" id="mb-clear">Сбросить ответ</button></div>`}
function checkboxPanel(v){const a=answerObj(state.current)||{selected:[]},sel=new Set((a.selected||[]).map(String)),opts=v.options||[];return `<div class="mb-answerbox"><div class="mb-answer-title">Выберите ответ</div><div class="mb-answer-hint">Отметьте подходящие варианты. Код ответа соберётся автоматически.</div><div class="mb-choice-list">${opts.map((x,i)=>`<label class="mb-choice ${sel.has(String(i+1))?'is-selected':''}"><input type="checkbox" data-choice="${i+1}" ${sel.has(String(i+1))?'checked':''}><span class="mb-choice-text">${esc(x)}</span></label>`).join('')}</div><div class="mb-code" id="mb-code">Код для бланка: ${esc(canonicalCode(v,a)||'—')}</div><button class="mb-btn mb-btn--secondary" type="button" id="mb-clear">Сбросить ответ</button></div>`}
function rowPanel(v){const a=answerObj(state.current)||{selected:[]};return `<div class="mb-answerbox"><div class="mb-answer-title">Ответ</div><div class="mb-answer-hint">Отметьте подходящие номера непосредственно в таблице выше. Итоговый код соберётся автоматически.</div><div class="mb-code" id="mb-code">Код для бланка: ${esc(canonicalCode(v,a)||'—')}</div><button class="mb-btn mb-btn--secondary" type="button" id="mb-clear">Сбросить ответ</button></div>`}
function inputContract(v){const key=String(state.current)+'-'+String(v.variant);const c=INPUT_CONTRACTS[key];if(!c)throw new Error('Missing input contract '+key);return c}
function numericError(c,reason){
if(reason==='space')return 'Пробелы в поле ответа не используются. Введите значение без пробелов.';
if(reason==='plus')return 'Знак «+» в поле ответа не нужен. Введите значение без него.';
if(reason==='percent')return c.percent_error||'Знак «%» в поле ответа не нужен. Введите только числовое значение.';
if(reason==='unit')return c.unit_error||'Буквы и единицы измерения в поле ответа не вводятся. Введите только числовое значение.';
if(reason==='fraction')return 'Обыкновенную дробь через «/» вводить нельзя. Запишите ответ целым числом или конечной десятичной дробью.';
if(reason==='integer')return 'Для этого примера нужно ввести целое число. Запятая, точка и дробная часть не используются.';
if(reason==='digit_count')return `Для этого примера нужно ввести число из ${c.exact_digits} цифр.`;
if(reason==='sign')return 'Знак «−» здесь не используется. Введите неотрицательное значение.';
if(reason==='incomplete_decimal')return 'После десятичного разделителя укажите цифры.';
if(reason==='separator')return 'В числе может быть только один десятичный разделитель.';
return c.mode==='digits'?'Введите только требуемое количество цифр без дополнительных символов.':'Введите только числовое значение без дополнительных символов.'
}
function numericPanel(v){const c=inputContract(v),a=answerObj(state.current)||{value:'',valid:false},value=String(a.value||''),chk=validateNumeric(v,value),invalid=!chk.empty&&!chk.valid,inputMode=c.mode==='number'?'decimal':'numeric';return `<div class="mb-answerbox"><label class="mb-answer-title" for="mb-short">Ответ</label><div class="mb-answer-hint">${esc(c.hint)}</div><input class="mb-input ${invalid?'is-invalid':''}" id="mb-short" inputmode="${inputMode}" autocomplete="off" value="${esc(value)}" aria-describedby="mb-input-error"><div class="mb-error" id="mb-input-error" aria-live="polite">${invalid?esc(numericError(c,chk.reason)):''}</div></div>`}
function answerPanel(v){if(v.control==='matching_selects_4')return matchingPanel(v);if(v.control==='checkboxes')return checkboxPanel(v);if(v.control==='row_checkboxes')return rowPanel(v);return numericPanel(v)}
function renderGrid(){gridEl.innerHTML=tasks.map(t=>`<button class="mb-num ${t.number===state.current?'is-current':''} ${isAnswered(t.number)?'is-filled':''} ${state.marked[t.number]?'is-marked':''}" data-n="${t.number}" aria-label="Задание ${t.number}">${t.number}</button>`).join('');$$('.mb-num').forEach(b=>b.onclick=()=>{state.current=+b.dataset.n;save();render()})}
function validateNumeric(v,value){
const c=inputContract(v),raw=String(value==null?'':value);
if(raw==='')return {empty:true,valid:false,reason:null,normalized:''};
if(/\s/.test(raw))return {empty:false,valid:false,reason:'space',normalized:raw};
if(raw.includes('+'))return {empty:false,valid:false,reason:'plus',normalized:raw};
if(raw.includes('%'))return {empty:false,valid:false,reason:'percent',normalized:raw};
if(/[A-Za-zА-Яа-яЁё°²³]/.test(raw))return {empty:false,valid:false,reason:'unit',normalized:raw};
if(raw.includes('/'))return {empty:false,valid:false,reason:'fraction',normalized:raw};
if(c.mode==='integer'||c.mode==='digits'){
if(/[.,]/.test(raw))return {empty:false,valid:false,reason:'integer',normalized:raw};
if(raw.startsWith('-')&&!c.allow_negative)return {empty:false,valid:false,reason:'sign',normalized:raw};
if(!/^-?\d+$/.test(raw))return {empty:false,valid:false,reason:'format',normalized:raw};
if(c.mode==='digits'&&c.exact_digits&&raw.replace(/^-/,'').length!==Number(c.exact_digits))return {empty:false,valid:false,reason:'digit_count',normalized:raw};
return {empty:false,valid:true,reason:null,normalized:raw};
}
if(c.mode==='number'){
let normalized=raw.replace('−','-');
if(normalized.startsWith('-')&&!c.allow_negative)return {empty:false,valid:false,reason:'sign',normalized:raw};
const seps=(normalized.match(/[.,]/g)||[]).length;
if(seps>1)return {empty:false,valid:false,reason:'separator',normalized:raw};
if(/[.,]$/.test(normalized))return {empty:false,valid:false,reason:'incomplete_decimal',normalized:normalized.replace('.',',')};
if(!/^-?\d+(?:[.,]\d+)?$/.test(normalized))return {empty:false,valid:false,reason:'format',normalized:raw};
normalized=normalized.replace('.',',');
return {empty:false,valid:true,reason:null,normalized};
}
return {empty:false,valid:false,reason:'format',normalized:raw};
}
function updateCode(v){const e=$('#mb-code');if(e)e.textContent='Код для бланка: '+(canonicalCode(v,answerObj(state.current))||'—')}
function bindNumeric(v){const c=inputContract(v),inp=$('#mb-short'),err=$('#mb-input-error');inp.oninput=()=>{let raw=inp.value;const chk=validateNumeric(v,raw);let stored=raw;if(c.mode==='number'&&chk.normalized!==raw&&(chk.valid||chk.reason==='incomplete_decimal')){stored=chk.normalized;inp.value=stored}const finalChk=validateNumeric(v,stored);inp.classList.toggle('is-invalid',!finalChk.empty&&!finalChk.valid);err.textContent=finalChk.empty||finalChk.valid?'':numericError(c,finalChk.reason);state.answers[state.current]={value:stored,valid:finalChk.valid};save();renderGrid()}}
function disableMatchingDuplicates(){const sels=$$('.mb-select[data-pos]'),chosen=sels.map(s=>s.value).filter(Boolean);for(const s of sels)for(const o of [...s.options]){if(!o.value){o.disabled=false;continue}o.disabled=chosen.includes(o.value)&&s.value!==o.value}}
function bindMatching(v){disableMatchingDuplicates();$$('.mb-select[data-pos]').forEach(s=>s.onchange=()=>{const a=answerObj(state.current)||{values:['','','','']},vals=[...(a.values||['','','',''])];vals[+s.dataset.pos]=s.value;state.answers[state.current]={values:vals};save();disableMatchingDuplicates();updateCode(v);renderGrid()});const c=$('#mb-clear');if(c)c.onclick=()=>{state.answers[state.current]={values:['','','','']};save();render()}}
function bindChecks(v,row){const selector=row?'input[data-row]':'input[data-choice]';$$(selector).forEach(cb=>cb.onchange=()=>{const vals=$$(selector).filter(x=>x.checked).map(x=>row?x.dataset.row:x.dataset.choice);state.answers[state.current]={selected:vals};save();render()});const c=$('#mb-clear');if(c)c.onclick=()=>{state.answers[state.current]={selected:[]};save();render()}}
function bindAnswer(v){if(v.control==='numeric_input')bindNumeric(v);else if(v.control==='matching_selects_4')bindMatching(v);else if(v.control==='checkboxes')bindChecks(v,false);else if(v.control==='row_checkboxes')bindChecks(v,true)}
function render(){const v=currentVariant();if(!v)return;$('#mb-progress').style.width=((state.current/21)*100)+'%';taskEl.innerHTML=`<div class="mb-task-head"><div><h2>Задание ${state.current}</h2><div class="mb-task-meta">1 первичный балл · краткий ответ</div></div><button class="mb-mark ${state.marked[state.current]?'is-on':''}" id="mb-mark">${state.marked[state.current]?'★ Вернуться':'☆ Вернуться позже'}</button></div>${sourceTag(v)}<div class="mb-task-body">${bodyHtml(v)}</div>${answerPanel(v)}<div class="mb-task-nav"><button class="mb-btn mb-btn--secondary" id="mb-prev" ${state.current===1?'disabled':''}>← Назад</button><button class="mb-btn mb-btn--primary" id="mb-next">${state.current===21?'Завершить':'Далее →'}</button></div>`;$('#mb-mark').onclick=()=>{state.marked[state.current]=!state.marked[state.current];save();render()};bindAnswer(v);$('#mb-prev').onclick=()=>{if(state.current>1){state.current--;save();render()}};$('#mb-next').onclick=()=>{if(state.current===21)finishAttempt(false);else{state.current++;save();render()}};renderGrid();window.scrollTo({top:0,behavior:'smooth'})}
function finishAttempt(auto){if(!auto&&!confirm('Завершить попытку и открыть проверку? После этого ответы изменить нельзя.'))return;state.active=false;state.finished=true;save();clearInterval(timerHandle);showResults()}
function answerDisplay(v,a){if(v.control==='numeric_input'&&a&&String(a.value||'')!=='')return String(a.value);const code=canonicalCode(v,a);return code||'—'}
function showResults(){clearInterval(timerHandle);intro.classList.add('mb-hidden');exam.classList.remove('is-active');results.classList.add('is-active');$('#mb-score').textContent=`${total()}/21`;$('#mb-answered').textContent=`${answeredCount()}/21`;$('#mb-review').innerHTML=tasks.map(t=>{const v=variantFor(t.number),sc=score(t.number),user=answerDisplay(v,answerObj(t.number)),accepted=(v.canonical_forms||[]).join(' или ');return `<details class="mb-review-item"><summary><span>Задание ${t.number} · пример ${v.variant}</span><span class="mb-pill ${sc?'ok':'bad'}">${sc}/1</span></summary><div class="mb-review-content"><p><strong>Ваш ответ:</strong> ${esc(user)}</p><p><strong>Официально принимаемый ответ:</strong> ${esc(accepted)}</p></div></details>`}).join('');window.scrollTo({top:0})}
function startTimer(){clearInterval(timerHandle);const tick=()=>{const left=Math.max(0,(state.deadline||Date.now())-Date.now()),h=Math.floor(left/3600000),m=Math.floor((left%3600000)/60000),s=Math.floor((left%60000)/1000);$('#mb-timer').textContent=[h,m,s].map(x=>String(x).padStart(2,'0')).join(':');if(left<=0&&state.active)finishAttempt(true)};tick();timerHandle=setInterval(tick,1000)}
function openRefs(){const box=$('#mb-ref-pages');box.innerHTML=[4,5,6,7].map(n=>C.refs[n]?`<div class="mb-ref-page"><img src="${C.refs[n]}" alt="Справочные материалы ФИПИ, страница ${n}"></div>`:'').join('');$('#mb-ref-modal').classList.add('is-open');document.body.style.overflow='hidden'}
function closeRefs(){$('#mb-ref-modal').classList.remove('is-open');document.body.style.overflow=''}
$('#mb-start').onclick=startNew;$('#mb-continue').onclick=resume;$('#mb-reset-intro').onclick=resetAll;$('#mb-finish').onclick=()=>finishAttempt(false);$('#mb-retry').onclick=()=>{clearSaved();state=emptyState();showIntro()};$('#mb-ref').onclick=openRefs;$('#mb-ref-intro').onclick=openRefs;$('#mb-ref-results').onclick=openRefs;$('#mb-ref-close').onclick=closeRefs;$('#mb-ref-modal').onclick=e=>{if(e.target.id==='mb-ref-modal')closeRefs()};document.addEventListener('keydown',e=>{if(e.key==='Escape')closeRefs()});
window.EKSAMIO_MATH_BASE_TEST={tasks,state:()=>state,variantFor,canonicalCode,isAnswered,score,total,answeredCount,validateNumeric,inputContract,fixTypography,startNew,finish:()=>finishAttempt(true),setVariant:(n,k)=>{const t=byNumber(n);if(!t||!t.variants.some(v=>v.variant===k))throw new Error('Unknown variant');state.variants[n]=k;delete state.answers[n];state.current=n;save();render()},setCurrent:n=>{state.current=n;save();render()},resetStorage:()=>{clearSaved();state=emptyState()},render,showResults};
if(state.finished&&state.startedAt&&Object.keys(state.variants||{}).length)showResults();else if(state.active&&state.startedAt&&Object.keys(state.variants||{}).length){showExam();render()}else showIntro();
})();
