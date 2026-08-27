(function(global){
  'use strict';

  const REVIEWED_PRACTICE = Object.freeze({
    card_id: 'ex-practice-alt-sochetat-001',
    semantic_id: 'school-i-e-alternating-verb-roots-stressed-a',
    rule_title: 'Чередование Е/И: исключение «сочетать»',
    explanation: 'СОЧЕТАТЬ/СОЧЕТАНИЕ — исключения в группе ЧЕТ-/ЧИТ-: сохраняется Е.',
    prompt: 'Восстановите букву и запишите слово целиком: соч..тание.',
    answer: 'сочетание',
    worked: 'Проверяйте конкретную лексему и не переносите механически модель ЧИТ- на слово «сочетание».',
    source_ref: 'source:russian-reviewed-card:ex-practice-alt-sochetat-001'
  });

  const clone = value => JSON.parse(JSON.stringify(value));
  const normalize = value => String(value || '').trim().toLocaleLowerCase('ru-RU').replace(/\s+/g,' ');

  class MockIdentityAdapter {
    constructor(){ this.identity = null; }
    async status(){ return this.identity ? clone(this.identity) : {authenticated:false}; }
    async continuePasswordless(){
      this.identity = {
        authenticated: true,
        user_identity_ref: 'user:browser-fixture-opaque',
        learner_profile_id: 'learner:browser-fixture-opaque',
        display_label: 'Ученик Pro'
      };
      return clone(this.identity);
    }
  }

  class MockLearningAdapter {
    constructor(){
      this.readiness = 42;
      this.events = [];
      this.practice = REVIEWED_PRACTICE;
    }
    async program(){
      const response = await fetch('program-catalog.json', {cache:'no-store'});
      if(!response.ok) throw new Error('program catalog unavailable');
      return response.json();
    }
    async profile({grade,route}){
      return {
        grade, route, readiness: this.readiness,
        focus_count: 1,
        retention_due: 2,
        weakness: this.practice.semantic_id,
        next_best_action: {
          action_type: 'PRACTICE_AND_VERIFY',
          title: this.readiness > 42 ? 'Закрепить результат через интервальное повторение' : 'Закрепить правило на независимом ответе',
          reason: this.readiness > 42 ? 'Правильный независимый ответ добавлен в evidence; следующий шаг — удержание.' : 'Текущая цель требует независимого evidence после объяснения.',
          canonical_state_owner: 'shared_peis'
        }
      };
    }
    async plan({grade,route}){
      return [
        {title:'Разобрать правило', detail:`${grade} класс · ${route.toUpperCase()}`, state:'готово'},
        {title:'Выполнить независимую проверку', detail:'Проверенная карточка русского', state:'сейчас'},
        {title:'Вернуться к теме по расписанию', detail:'Retention после evidence', state:'далее'}
      ];
    }
    async nextPractice(){ return clone(this.practice); }
    async submitPractice({card_id,answer}){
      if(card_id !== this.practice.card_id) throw new Error('unknown practice card');
      const correct = normalize(answer) === normalize(this.practice.answer);
      const event_id = `mock-peis-${this.events.length+1}`;
      const event = {
        event_id,
        card_id,
        semantic_id:this.practice.semantic_id,
        correctness:correct,
        canonical_state_owner:'shared_peis'
      };
      this.events.push(event);
      if(correct) this.readiness = Math.max(this.readiness,48);
      return {
        status:'ACCEPTED',
        correct,
        score:correct?1:0,
        max_score:1,
        feedback: correct ? 'Верно. Ответ принят как независимая проверка.' : `Пока неверно. Проверенный ответ: ${this.practice.answer}. ${this.practice.explanation}`,
        event,
        readiness:this.readiness,
        next_best_action: correct ? 'RETENTION_REVIEW' : 'TARGETED_REPAIR'
      };
    }
  }

  class MockPaymentAdapter {
    constructor(){ this.currentEntitlement = null; this.orderCounter = 0; }
    async entitlement(){ return clone(this.currentEntitlement || {active:false}); }
    async createSandboxOrder({offer_code,payment_method}){
      if(!['RU_PRO_30_TEST','RU_PRO_90_TEST'].includes(offer_code)) throw new Error('unknown offer');
      if(!['BankCard','SBP'].includes(payment_method)) throw new Error('unsupported method');
      this.orderCounter += 1;
      return {
        order_id:`ord:client-sandbox-${this.orderCounter}`,
        inv_id:900000+this.orderCounter,
        offer_code,
        payment_method,
        provider:'ROBOKASSA',
        test_mode:true,
        is_test:'1'
      };
    }
    async confirmSandboxOrder(order){
      if(!order || order.test_mode !== true || order.is_test !== '1') throw new Error('unsafe payment mode');
      const days = order.offer_code === 'RU_PRO_90_TEST' ? 90 : 30;
      this.currentEntitlement = {
        active:true,
        product_code:'EKSAMIO_PRO_RUSSIAN',
        duration_days:days,
        source_order_id:order.order_id,
        state:'ACTIVE'
      };
      return clone(this.currentEntitlement);
    }
  }

  class MockTutorAdapter {
    async ask({session_ref,semantic_id,message,source_ref,entitlement}){
      if(!entitlement || entitlement.active !== true) throw new Error('Tutor requires active entitlement');
      if(!session_ref || !semantic_id || !message || !String(source_ref).startsWith('source:')) throw new Error('grounded Tutor request incomplete');
      return {
        status:'TUTOR_ADVISORY',
        session_ref,
        semantic_id,
        accepted_source_refs:[source_ref],
        verification_required:true,
        text:`По проверенному материалу Eksamio: ${REVIEWED_PRACTICE.explanation} Проверь слово «${REVIEWED_PRACTICE.answer}», а затем выполни независимое задание без подсказки.`
      };
    }
  }

  class HttpAdapters {
    constructor(baseUrl){ this.baseUrl=String(baseUrl||'').replace(/\/$/,''); }
    async request(path,options={}){
      const response=await fetch(this.baseUrl+path,{credentials:'include',headers:{'Content-Type':'application/json',...(options.headers||{})},...options});
      if(!response.ok) throw new Error(`adapter HTTP ${response.status}`);
      return response.json();
    }
    get identity(){ return {status:()=>this.request('/api/identity/session'),continuePasswordless:()=>this.request('/api/identity/demo-continuity',{method:'POST',body:'{}'})}; }
    get learning(){ return {
      program:()=>this.request('/api/russian/program'),
      profile:args=>this.request(`/api/russian/profile?grade=${encodeURIComponent(args.grade)}&route=${encodeURIComponent(args.route)}`),
      plan:args=>this.request(`/api/russian/plan?grade=${encodeURIComponent(args.grade)}&route=${encodeURIComponent(args.route)}`),
      nextPractice:()=>this.request('/api/russian/practice/next'),
      submitPractice:args=>this.request('/api/russian/practice/submit',{method:'POST',body:JSON.stringify(args)})
    }; }
    get payment(){ return {
      entitlement:()=>this.request('/api/payments/entitlement'),
      createSandboxOrder:args=>this.request('/api/payments/orders',{method:'POST',body:JSON.stringify(args)}),
      confirmSandboxOrder:args=>this.request('/api/payments/sandbox/confirm',{method:'POST',body:JSON.stringify(args)})
    }; }
    get tutor(){ return {ask:args=>this.request('/api/tutor/turn',{method:'POST',body:JSON.stringify(args)})}; }
  }

  function createAdapters(config={}){
    if(config.mode==='http'){
      const http=new HttpAdapters(config.baseUrl||'');
      return {identity:http.identity,learning:http.learning,payment:http.payment,tutor:http.tutor,mode:'http'};
    }
    return {
      identity:new MockIdentityAdapter(),
      learning:new MockLearningAdapter(),
      payment:new MockPaymentAdapter(),
      tutor:new MockTutorAdapter(),
      mode:'mock'
    };
  }

  global.EksamioProAdapters={createAdapters,REVIEWED_PRACTICE};
})(window);
