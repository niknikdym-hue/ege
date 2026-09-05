(function(){
  'use strict';

  const routeLabels={school:'Школьная программа',oge:'ОГЭ',ege:'ЕГЭ',diagnostic:'Диагностика',thematic_trainer:'Тематические тренажёры',homework:'Домашняя работа',tutor:'Tutor'};
  const state={adapters:null,runtime:null,program:null,identity:{authenticated:false},entitlement:{active:false},grade:10,route:'ege',profile:null,plan:[],practice:null,history:[],diagnostics:null,progressEvents:[],pendingAttempt:null,tutorSession:'tutor:browser-client-001'};
  const $=selector=>document.querySelector(selector);
  const $$=selector=>Array.from(document.querySelectorAll(selector));
  const text=value=>String(value==null?'':value);
  const escapeHtml=value=>text(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const opaqueId=prefix=>`${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;

  function resolveAdapterRuntime(){
    const host=String(window.location.hostname||'').toLowerCase();
    const localHost=host==='127.0.0.1'||host==='localhost'||host==='[::1]';
    const raw=window.EKSAMIO_PRO_RUNTIME_CONFIG;
    if(raw==null){
      if(localHost) return {mode:'mock',ownerTest:false};
      throw new Error('EKSAMIO_PRO_RUNTIME_CONFIG is required outside localhost');
    }
    if(typeof raw!=='object'||Array.isArray(raw)) throw new Error('invalid EKSAMIO_PRO_RUNTIME_CONFIG');
    const mode=String(raw.mode||'');
    if(mode==='mock'){
      if(!localHost) throw new Error('mock Pro adapters are forbidden outside localhost');
      return {mode:'mock',ownerTest:false};
    }
    if(mode!=='http') throw new Error('unsupported Pro runtime mode');
    if(!localHost&&window.location.protocol!=='https:') throw new Error('production Pro client requires HTTPS');
    const baseUrl=String(raw.baseUrl||'').trim().replace(/\/$/,'');
    if(baseUrl){
      let parsed;
      try{parsed=new URL(baseUrl,window.location.href);}catch(_error){throw new Error('invalid Pro backend base URL');}
      if(parsed.username||parsed.password) throw new Error('credentials are forbidden in Pro backend URL');
      if(!localHost&&parsed.protocol!=='https:') throw new Error('production Pro backend requires HTTPS');
    }
    return {mode:'http',baseUrl,ownerTest:raw.ownerTest===true};
  }

  async function init(){
    state.runtime=resolveAdapterRuntime();
    state.adapters=window.EksamioProAdapters.createAdapters(state.runtime);
    state.program=await state.adapters.learning.program();
    populateGoalControls();renderProgram();
    state.identity=await state.adapters.identity.status();
    bindEvents();renderIdentity();configurePaymentUi();
    if(state.identity.authenticated) await loadAuthenticatedState();else renderGuestState();
    document.documentElement.dataset.appReady='true';
  }

  function populateGoalControls(){
    $('#gradeSelect').innerHTML=state.program.grades.map(value=>`<option value="${value}" ${value===state.grade?'selected':''}>${value}</option>`).join('');
    $('#routeSelect').innerHTML=state.program.routes.filter(item=>item!=='tutor').map(value=>`<option value="${escapeHtml(value)}" ${value===state.route?'selected':''}>${escapeHtml(routeLabels[value])}</option>`).join('');
    $('#routeStrip').innerHTML=state.program.routes.map(value=>`<span class="route-chip" data-route-chip="${escapeHtml(value)}">${escapeHtml(routeLabels[value])}</span>`).join('');
  }

  function renderProgram(){
    $('#programGrid').innerHTML=state.program.modules.map((module,index)=>{
      const routeText=module.routes.map(route=>routeLabels[route]).join(' · ');
      return `<article class="module-card" data-module-id="${escapeHtml(module.module_id)}"><span class="module-number">${String(index+1).padStart(2,'0')} · ${escapeHtml(module.module_id)}</span><h2>${escapeHtml(module.title_ru)}</h2><p>Модуль единой программы русского языка.</p><div class="module-routes">${escapeHtml(routeText)}</div></article>`;
    }).join('');
  }

  async function loadAuthenticatedState(){
    const values=await Promise.all([state.adapters.payment.entitlement(),state.adapters.learning.nextPractice()]);
    [state.entitlement,state.practice]=values;
    await refreshLearningState();renderPractice();renderEntitlement();
  }

  async function refreshLearningState(){
    if(!state.identity.authenticated){renderGuestState();return;}
    const requests=[state.adapters.learning.profile({grade:state.grade,route:state.route}),state.adapters.learning.plan({grade:state.grade,route:state.route}),state.adapters.learning.history()];
    if(state.runtime.ownerTest===true) requests.push(state.adapters.learning.diagnostics());
    const values=await Promise.all(requests);
    [state.profile,state.plan,state.history]=values;state.diagnostics=values[3]||null;renderProfile();
  }

  function renderGuestState(){
    state.profile=null;state.plan=[];state.history=[];state.diagnostics=null;
    ['todaySolved','todayCorrect','todayErrors','todayReview'].forEach(id=>$('#'+id).textContent='—');
    $('#nbaTitle').textContent='Войдите, чтобы открыть личный план';
    $('#nbaReason').textContent='Анонимная попытка остаётся доступной в тренажёре; серверный профиль появится только после входа.';
    $('#planList').innerHTML='<li><span><strong>Выполнить попытку</strong><small>Ответ можно отправить из тренажёра без входа.</small></span><span class="plan-state">доступно</span></li><li><span><strong>Войти в «Мой Eksamio»</strong><small>Тестовый вход свяжет попытку с серверным профилем.</small></span><span class="plan-state">далее</span></li>';
    $('#skillList').innerHTML='<div class="empty-state">Навыки появятся после входа.</div>';
    $('#latestChanges').innerHTML='<div class="empty-state">Изменения появятся после принятого сервером evidence.</div>';
    $('#progressPercent').textContent='Вход не выполнен';$('#progressBar').style.width='0';
    $('#historyList').innerHTML='<div class="empty-state">История хранится на сервере и доступна после входа.</div>';
    $('#ownerDiagnostics').hidden=true;renderProgressEvents();
  }

  function renderProfile(){
    const today=state.profile.today;
    $('#todaySolved').textContent=text(today.solved);$('#todayCorrect').textContent=text(today.correct);$('#todayErrors').textContent=text(today.errors);$('#todayReview').textContent=text(today.review);
    $('#nbaTitle').textContent=state.profile.next_best_action.title;$('#nbaReason').textContent=state.profile.next_best_action.reason;
    $('#progressPercent').textContent=state.profile.readiness_label;$('#progressBar').style.width=state.profile.readiness==null?'0':`${state.profile.readiness}%`;
    $('#planList').innerHTML=state.plan.map(item=>`<li><span><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.detail)}</small></span><span class="plan-state">${escapeHtml(item.state)}</span></li>`).join('');
    $('#skillList').innerHTML=state.profile.skills.map(item=>`<div class="list-row"><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.status)}</span></div>`).join('')||'<div class="empty-state">Недостаточно данных.</div>';
    $('#latestChanges').innerHTML=state.profile.latest_changes.map(item=>`<div class="list-row"><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.timestamp)}</small></div>`).join('')||'<div class="empty-state">Пока нет изменений.</div>';
    $('#historyList').innerHTML=state.history.map(item=>`<div class="history-row"><strong>${escapeHtml(item.kind)}</strong><span>Решено: ${item.solved} · Верно: ${item.correct} · Ошибки: ${item.errors}</span><small>Дальше: ${escapeHtml(item.next)}</small></div>`).join('')||'<div class="empty-state">Пока нет завершённых действий.</div>';
    renderDiagnostics();renderProgressEvents();
  }

  function renderDiagnostics(){
    const panel=$('#ownerDiagnostics');
    if(state.runtime.ownerTest!==true||!state.diagnostics){panel.hidden=true;return;}
    panel.hidden=false;
    $('#diagnosticSteps').innerHTML=state.diagnostics.steps.map(step=>`<div class="diagnostic-step"><span>${escapeHtml(step.label)}</span><strong data-status="${escapeHtml(step.status)}">${escapeHtml(step.status)}</strong></div>`).join('');
    $('#diagnosticDetail').textContent=JSON.stringify(state.diagnostics.detail,null,2);
  }

  function renderIdentity(){
    if(state.identity.authenticated){$('#identityStatus').textContent=state.identity.display_label||'Вход выполнен';$('#identityButton').textContent='Мой план';$('#logoutButton').hidden=false;$('#entryContinue').textContent='Открыть мой план';}
    else{$('#identityStatus').textContent='Гостевой режим';$('#identityButton').textContent='Войти';$('#logoutButton').hidden=true;$('#entryContinue').textContent='Войти в Мой Eksamio';}
    document.body.dataset.auth=state.identity.authenticated?'authenticated':'anonymous';
  }

  function renderEntitlement(){
    const active=state.entitlement&&state.entitlement.active===true;
    $('#tutorLocked').hidden=active;$('#tutorAvailable').hidden=!active;$('#tutorNavLock').hidden=active;document.body.dataset.entitlement=active?'active':'locked';
    if(active&&!$('#tutorThread').children.length) addTutorMessage('tutor','Tutor готов. Сначала выполните проверенную карточку; контекст ошибки будет взят с сервера.');
  }

  function configurePaymentUi(){
    const button=$('#purchaseButton');
    if(state.adapters.mode==='mock'){button.hidden=false;button.disabled=false;return;}
    button.hidden=true;button.disabled=true;$('#paymentStatus').textContent='Production checkout будет доступен только после допуска server-owned SKU и trusted payment boundary.';
  }

  function renderPractice(){
    if(!state.practice)return;
    $('#practiceSemantic').textContent='Проверенный навык';$('#practiceRuleTitle').textContent=state.practice.rule_title;$('#practiceExplanation').textContent=state.practice.explanation;$('#practiceWorked').textContent=state.practice.worked;$('#practicePrompt').textContent=state.practice.prompt;
  }

  function renderProgressEvents(){
    const root=$('#progressEvents');
    if(!state.progressEvents.length){root.innerHTML='<div class="progress-event"><strong>Пока нет нового действия в этой вкладке</strong><small>История выше загружается из server-owned PEIS.</small></div>';return;}
    root.innerHTML=state.progressEvents.slice().reverse().map(event=>`<div class="progress-event"><strong>${escapeHtml(event.title)}</strong><small>${escapeHtml(event.detail)}</small></div>`).join('');
  }

  function switchView(view){
    $$('.view').forEach(panel=>panel.classList.toggle('is-active',panel.dataset.viewPanel===view));$$('.nav-item').forEach(button=>button.classList.toggle('is-active',button.dataset.view===view));location.hash=view;$('#main')?.focus({preventScroll:true});
  }

  function showFailure(message){const alert=$('#syncAlert');alert.textContent=message||'Данные временно не синхронизированы. Повторите действие.';alert.hidden=false;}
  function clearFailure(){$('#syncAlert').hidden=true;}

  async function continueIdentity(){
    clearFailure();
    try{
      if(!state.identity.authenticated){state.identity=await state.adapters.identity.continuePasswordless();renderIdentity();state.progressEvents.push({title:'Вход выполнен',detail:'Анонимная попытка связана с server-owned профилем.'});await loadAuthenticatedState();}
      switchView('plan');
    }catch(_error){showFailure('Не удалось выполнить вход или загрузить серверный прогресс. Попробуйте ещё раз.');}
  }

  async function logout(){
    clearFailure();
    try{await state.adapters.identity.logout();state.identity={authenticated:false};state.entitlement={active:false};state.practice=null;state.progressEvents=[];$('#tutorThread').replaceChildren();renderIdentity();renderEntitlement();renderGuestState();switchView('plan');}
    catch(_error){showFailure('Не удалось завершить серверную сессию. Попробуйте ещё раз.');}
  }

  async function handleCheck(){
    if(!state.identity.authenticated){await continueIdentity();if(!state.identity.authenticated)return;switchView('practice');}
    const answer=$('#practiceAnswer').value;
    if(!state.pendingAttempt||state.pendingAttempt.answer!==answer) state.pendingAttempt={card_id:state.practice.card_id,answer,attempt_started_at_ms:Date.now(),client_request_id:opaqueId('practice')};
    const button=$('#checkAnswer');button.disabled=true;clearFailure();
    try{
      const result=await state.adapters.learning.submitPractice(state.pendingAttempt);state.pendingAttempt=null;
      const feedback=$('#practiceFeedback');feedback.textContent=result.feedback;feedback.className=`feedback ${result.correct?'is-correct':'is-wrong'}`;
      state.progressEvents.push({title:result.correct?'Независимая проверка: верно':'Независимая проверка: нужна доработка',detail:`Evidence принят сервером · ${result.next_best_action}`});await refreshLearningState();
    }catch(_error){showFailure('Ответ не синхронизирован с сервером. Он не показан как принятый; нажмите «Проверить» для безопасного повтора.');}
    finally{button.disabled=false;}
  }

  async function purchaseSandbox(){
    if(!state.adapters||state.adapters.mode!=='mock')throw new Error('sandbox purchase is localhost/mock only');
    if(!state.identity.authenticated)await continueIdentity();
    const button=$('#purchaseButton');button.disabled=true;$('#paymentStatus').textContent='Создаём тестовый SBP-заказ…';
    try{const order=await state.adapters.payment.createSandboxOrder({offer_code:'RU_PRO_30_TEST',payment_method:'SBP'});if(order.test_mode!==true||order.is_test!=='1')throw new Error('test mode not enforced');state.entitlement=await state.adapters.payment.confirmSandboxOrder(order);$('#paymentStatus').textContent=`Sandbox order ${order.order_id}: entitlement ACTIVE`;renderEntitlement();}finally{button.disabled=false;}
  }

  function addTutorMessage(role,value){const el=document.createElement('div');el.className=`message ${role}`;el.textContent=value;$('#tutorThread').appendChild(el);}

  async function handleTutor(event){
    event.preventDefault();const input=$('#tutorInput'),message=input.value.trim();if(!message||!state.practice)return;
    addTutorMessage('learner',message);input.value='';clearFailure();
    try{const result=await state.adapters.tutor.ask({card_id:state.practice.card_id,message});addTutorMessage('tutor',result.text);state.progressEvents.push({title:'Tutor: помощь записана отдельно',detail:'Независимая проверка обязательна; помощь сама по себе не повышает уровень.'});await refreshLearningState();}
    catch(_error){showFailure('Tutor не смог получить серверный контекст ошибки. Ответ не был сгенерирован.');}
  }

  function bindEvents(){
    $('#mainNav').addEventListener('click',event=>{const button=event.target.closest('[data-view]');if(button)switchView(button.dataset.view);});
    document.addEventListener('click',event=>{const go=event.target.closest('[data-go]');if(go)switchView(go.dataset.go);});
    $('#entryContinue').addEventListener('click',continueIdentity);$('#identityButton').addEventListener('click',continueIdentity);$('#logoutButton').addEventListener('click',logout);
    $('#gradeSelect').addEventListener('change',async event=>{state.grade=Number(event.target.value);await refreshLearningState();});$('#routeSelect').addEventListener('change',async event=>{state.route=event.target.value;await refreshLearningState();});
    $('#checkAnswer').addEventListener('click',handleCheck);if(state.adapters.mode==='mock') $('#purchaseButton').addEventListener('click',purchaseSandbox);$('#tutorForm').addEventListener('submit',handleTutor);
    window.addEventListener('hashchange',()=>{const view=location.hash.replace('#','');if(['plan','program','practice','tutor','progress'].includes(view))switchView(view);});
  }

  init().catch(error=>{console.error(error);document.documentElement.dataset.appReady='error';document.body.insertAdjacentHTML('afterbegin','<div role="alert" style="padding:12px;background:#fee;color:#700">Мой Eksamio временно недоступен: серверный контур не подключён.</div>');});
})();
