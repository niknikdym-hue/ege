(function(){
  'use strict';

  const routeLabels={school:'Школьная программа',oge:'ОГЭ',ege:'ЕГЭ',diagnostic:'Диагностика',thematic_trainer:'Тематические тренажёры',homework:'Домашняя работа',tutor:'Tutor'};
  const state={
    adapters:null,
    program:null,
    identity:{authenticated:false},
    entitlement:{active:false},
    grade:10,
    route:'ege',
    profile:null,
    plan:[],
    practice:null,
    progressEvents:[],
    tutorSession:'tutor:browser-client-001'
  };

  const $=selector=>document.querySelector(selector);
  const $$=selector=>Array.from(document.querySelectorAll(selector));

  function resolveAdapterRuntime(){
    const host=String(window.location.hostname||'').toLowerCase();
    const localHost=host==='127.0.0.1'||host==='localhost'||host==='[::1]';
    const raw=window.EKSAMIO_PRO_RUNTIME_CONFIG;

    // Local browser/CI fixtures may use the deterministic mock when no runtime
    // config is injected. A deployed/non-local client must never silently do so.
    if(raw==null){
      if(localHost) return {mode:'mock'};
      throw new Error('EKSAMIO_PRO_RUNTIME_CONFIG is required outside localhost');
    }
    if(typeof raw!=='object'||Array.isArray(raw)) throw new Error('invalid EKSAMIO_PRO_RUNTIME_CONFIG');

    const mode=String(raw.mode||'');
    if(mode==='mock'){
      if(!localHost) throw new Error('mock Pro adapters are forbidden outside localhost');
      return {mode:'mock'};
    }
    if(mode!=='http') throw new Error('unsupported Pro runtime mode');
    if(!localHost&&window.location.protocol!=='https:') throw new Error('production Pro client requires HTTPS');

    const baseUrl=String(raw.baseUrl||'').trim().replace(/\/$/,'');
    if(baseUrl){
      let parsed;
      try{ parsed=new URL(baseUrl,window.location.href); }
      catch(_error){ throw new Error('invalid Pro backend base URL'); }
      if(parsed.username||parsed.password) throw new Error('credentials are forbidden in Pro backend URL');
      if(!localHost&&parsed.protocol!=='https:') throw new Error('production Pro backend requires HTTPS');
    }
    return {mode:'http',baseUrl};
  }

  async function init(){
    state.adapters=window.EksamioProAdapters.createAdapters(resolveAdapterRuntime());
    state.program=await state.adapters.learning.program();
    populateGoalControls();
    renderProgram();
    state.identity=await state.adapters.identity.status();
    state.entitlement=await state.adapters.payment.entitlement();
    state.practice=await state.adapters.learning.nextPractice();
    await refreshLearningState();
    renderIdentity();
    renderPractice();
    renderEntitlement();
    configurePaymentUi();
    bindEvents();
    document.documentElement.dataset.appReady='true';
  }

  function populateGoalControls(){
    const grade=$('#gradeSelect');
    grade.innerHTML=state.program.grades.map(value=>`<option value="${value}" ${value===state.grade?'selected':''}>${value}</option>`).join('');
    const route=$('#routeSelect');
    route.innerHTML=state.program.routes.filter(item=>item!=='tutor').map(value=>`<option value="${value}" ${value===state.route?'selected':''}>${routeLabels[value]}</option>`).join('');
    $('#routeStrip').innerHTML=state.program.routes.map(value=>`<span class="route-chip" data-route-chip="${value}">${routeLabels[value]}</span>`).join('');
  }

  function renderProgram(){
    const grid=$('#programGrid');
    grid.innerHTML=state.program.modules.map((module,index)=>{
      const routeText=module.routes.map(route=>routeLabels[route]).join(' · ');
      return `<article class="module-card" data-module-id="${module.module_id}"><span class="module-number">${String(index+1).padStart(2,'0')} · ${module.module_id}</span><h2>${module.title_ru}</h2><p>Модуль единой программы русского языка.</p><div class="module-routes">${routeText}</div></article>`;
    }).join('');
  }

  async function refreshLearningState(){
    state.profile=await state.adapters.learning.profile({grade:state.grade,route:state.route});
    state.plan=await state.adapters.learning.plan({grade:state.grade,route:state.route});
    renderProfile();
  }

  function renderProfile(){
    $('#readinessValue').textContent=`${state.profile.readiness}%`;
    $('#focusValue').textContent=`${state.profile.focus_count} тема`;
    $('#retentionValue').textContent=String(state.profile.retention_due);
    $('#nbaTitle').textContent=state.profile.next_best_action.title;
    $('#nbaReason').textContent=state.profile.next_best_action.reason;
    $('#progressPercent').textContent=`${state.profile.readiness}%`;
    $('#progressBar').style.width=`${state.profile.readiness}%`;
    $('#planList').innerHTML=state.plan.map(item=>`<li><span><strong>${item.title}</strong><small>${item.detail}</small></span><span class="plan-state">${item.state}</span></li>`).join('');
    renderProgressEvents();
  }

  function renderIdentity(){
    const status=$('#identityStatus');
    const button=$('#identityButton');
    if(state.identity.authenticated){
      status.textContent=state.identity.display_label||'Вход выполнен';
      button.textContent='Профиль';
      $('#entryContinue').textContent='Открыть мой план';
    }else{
      status.textContent='Гостевой режим';
      button.textContent='Продолжить';
      $('#entryContinue').textContent='Продолжить в Pro';
    }
    document.body.dataset.auth=state.identity.authenticated?'authenticated':'anonymous';
  }

  function renderEntitlement(){
    const active=state.entitlement&&state.entitlement.active===true;
    $('#tutorLocked').hidden=active;
    $('#tutorAvailable').hidden=!active;
    $('#tutorNavLock').hidden=active;
    document.body.dataset.entitlement=active?'active':'locked';
    if(active && !$('#tutorThread').children.length){
      addTutorMessage('tutor','Tutor готов. Ответы в этом launch-срезе привязаны к проверенному русскому grounding.');
    }
  }

  function configurePaymentUi(){
    const button=$('#purchaseButton');
    if(state.adapters.mode==='mock'){
      button.hidden=false;
      button.disabled=false;
      return;
    }
    button.hidden=true;
    button.disabled=true;
    $('#paymentStatus').textContent='Production checkout будет доступен только после допуска server-owned SKU и trusted payment boundary.';
  }

  function renderPractice(){
    const p=state.practice;
    $('#practiceSemantic').textContent=p.semantic_id;
    $('#practiceRuleTitle').textContent=p.rule_title;
    $('#practiceExplanation').textContent=p.explanation;
    $('#practiceWorked').textContent=p.worked;
    $('#practicePrompt').textContent=p.prompt;
  }

  function renderProgressEvents(){
    const root=$('#progressEvents');
    if(!state.progressEvents.length){
      root.innerHTML='<div class="progress-event"><strong>Пока нет нового evidence</strong><small>Выполните независимую проверку в разделе «Практика».</small></div>';
      return;
    }
    root.innerHTML=state.progressEvents.slice().reverse().map(event=>`<div class="progress-event"><strong>${event.title}</strong><small>${event.detail}</small></div>`).join('');
  }

  function switchView(view){
    $$('.view').forEach(panel=>panel.classList.toggle('is-active',panel.dataset.viewPanel===view));
    $$('.nav-item').forEach(button=>button.classList.toggle('is-active',button.dataset.view===view));
    location.hash=view;
    const main=$('#main');
    if(main) main.focus({preventScroll:true});
  }

  async function continueIdentity(){
    if(!state.identity.authenticated){
      state.identity=await state.adapters.identity.continuePasswordless();
      renderIdentity();
      state.progressEvents.push({title:'Профиль продолжен',detail:'Анонимная демоверсия осталась вне Pro; создана server-owned continuity identity.'});
      renderProgressEvents();
    }
    switchView('plan');
  }

  async function handleCheck(){
    if(!state.identity.authenticated){
      await continueIdentity();
      switchView('practice');
    }
    const answer=$('#practiceAnswer').value;
    const result=await state.adapters.learning.submitPractice({card_id:state.practice.card_id,answer});
    const feedback=$('#practiceFeedback');
    feedback.textContent=result.feedback;
    feedback.className=`feedback ${result.correct?'is-correct':'is-wrong'}`;
    state.progressEvents.push({
      title:result.correct?'Независимая проверка: верно':'Независимая проверка: нужна доработка',
      detail:`${state.practice.semantic_id} · evidence ${result.event.event_id} · ${result.next_best_action}`
    });
    await refreshLearningState();
  }

  async function purchaseSandbox(){
    if(!state.adapters||state.adapters.mode!=='mock') throw new Error('sandbox purchase is localhost/mock only');
    if(!state.identity.authenticated) await continueIdentity();
    const button=$('#purchaseButton');
    button.disabled=true;
    $('#paymentStatus').textContent='Создаём тестовый SBP-заказ…';
    try{
      const order=await state.adapters.payment.createSandboxOrder({offer_code:'RU_PRO_30_TEST',payment_method:'SBP'});
      if(order.test_mode!==true||order.is_test!=='1') throw new Error('test mode not enforced');
      state.entitlement=await state.adapters.payment.confirmSandboxOrder(order);
      $('#paymentStatus').textContent=`Sandbox order ${order.order_id}: entitlement ACTIVE`;
      state.progressEvents.push({title:'Pro-доступ открыт в sandbox',detail:`${order.provider} · ${order.payment_method} · IsTest=1 · ${state.entitlement.duration_days} дней`});
      renderEntitlement();
      renderProgressEvents();
    }finally{
      button.disabled=false;
    }
  }

  function addTutorMessage(role,text){
    const el=document.createElement('div');
    el.className=`message ${role}`;
    el.textContent=text;
    $('#tutorThread').appendChild(el);
  }

  async function handleTutor(event){
    event.preventDefault();
    const input=$('#tutorInput');
    const message=input.value.trim();
    if(!message) return;
    addTutorMessage('learner',message);
    input.value='';
    const result=await state.adapters.tutor.ask({
      session_ref:state.tutorSession,
      semantic_id:state.practice.semantic_id,
      message,
      source_ref:state.practice.source_ref,
      entitlement:state.entitlement
    });
    addTutorMessage('tutor',result.text);
    state.progressEvents.push({title:'Tutor: помощь записана отдельно',detail:`${result.status} · verification_required=${result.verification_required} · source=${result.accepted_source_refs[0]}`});
    renderProgressEvents();
  }

  function bindEvents(){
    $('#mainNav').addEventListener('click',event=>{
      const button=event.target.closest('[data-view]');
      if(button) switchView(button.dataset.view);
    });
    document.addEventListener('click',event=>{
      const go=event.target.closest('[data-go]');
      if(go) switchView(go.dataset.go);
    });
    $('#entryContinue').addEventListener('click',continueIdentity);
    $('#identityButton').addEventListener('click',continueIdentity);
    $('#gradeSelect').addEventListener('change',async event=>{state.grade=Number(event.target.value);await refreshLearningState();});
    $('#routeSelect').addEventListener('change',async event=>{state.route=event.target.value;await refreshLearningState();});
    $('#checkAnswer').addEventListener('click',handleCheck);
    if(state.adapters.mode==='mock') $('#purchaseButton').addEventListener('click',purchaseSandbox);
    $('#tutorForm').addEventListener('submit',handleTutor);
    window.addEventListener('hashchange',()=>{
      const view=location.hash.replace('#','');
      if(['plan','program','practice','tutor','progress'].includes(view)) switchView(view);
    });
  }

  init().catch(error=>{
    console.error(error);
    document.documentElement.dataset.appReady='error';
    document.body.insertAdjacentHTML('afterbegin','<div role="alert" style="padding:12px;background:#fee;color:#700">Pro client failed to initialize.</div>');
  });
})();
