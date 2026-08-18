(function (root) {
  'use strict';
  const API = root.EksamioRussianExceptions;
  if (!API) return;

  const APP_ID = 'rex-trainer';
  const SESSION_COUNT = 10;
  const SOURCE_MAP = { all_exceptions:'exceptions_all', my_exceptions:'my_exceptions', work_on_errors:'retry', handoff:'main_trainer_handoff' };

  function el(tag, className, text) { const node=document.createElement(tag); if(className) node.className=className; if(text!=null) node.textContent=text; return node; }
  function button(text, className, action) { const b=el('button',`rex-button ${className||''}`,text); b.type='button'; if(action) b.dataset.action=action; return b; }
  function uuid() { return (root.crypto&&crypto.randomUUID)?crypto.randomUUID():`${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`; }
  function topicMap(runtime) { return Object.fromEntries(runtime.topics.map((x)=>[x.topic_id,x.label])); }
  function topicLabel(app, id) { return app.topicLabels[id] || 'Русский язык'; }
  function isPersonalExceptionState(x){ return !!x && (Number(x.wrong_count||0)>0 || Number(x.active_error_count||0)>0 || x.last_result==='wrong' || x.status==='due' || x.origin==='main_trainer_exact_error' || x.origin==='retention_failure'); }
  function personalRows(profile){ return Object.values((profile&&profile.exceptions)||{}).filter(isPersonalExceptionState); }
  function hasPersonalState(profile){ return personalRows(profile).length>0; }
  function profileStats(profile){
    const rows=personalRows(profile); const now=Date.now();
    return {
      due:rows.filter((x)=>x.next_due_at&&Date.parse(x.next_due_at)<=now).length,
      active:rows.filter((x)=>['active','due','stabilizing'].includes(x.status)||Number(x.active_error_count||0)>0).length,
      stabilized:rows.filter((x)=>x.status==='stabilized').length,
    };
  }
  function filteredRuntime(runtime, topicId){
    if(!topicId) return runtime;
    const exceptions={}; const practice_items={};
    for(const [id,x] of Object.entries(runtime.exceptions)){
      if(x.topic_id!==topicId) continue;
      exceptions[id]=x;
      for(const pid of x.practice_item_ids||[]) if(runtime.practice_items[pid]) practice_items[pid]=runtime.practice_items[pid];
    }
    return {...runtime,exceptions,practice_items};
  }
  function announce(app,text){ app.live.textContent=''; setTimeout(()=>{app.live.textContent=text;},10); }
  function renderInto(app,node){ app.shell.replaceChildren(node); root.scrollTo&&root.scrollTo({top:Math.max(0,app.root.offsetTop-20),behavior:'smooth'}); }

  function makeNotice(app){
    if(app.storageStatus==='corrupt') return el('div','rex-notice','Личный прогресс временно недоступен: сохранённые данные имеют повреждённый формат. Общая тренировка работает, исходные данные не изменены.');
    if(app.storageStatus==='unsupported_schema') return el('div','rex-notice','Личный прогресс сохранён в другой версии формата. Мы его не перезаписываем; общая тренировка доступна без сохранения новых результатов.');
    if(app.storageStatus==='unavailable') return el('div','rex-notice','Сохранение прогресса недоступно в этом браузере. Тренировка работает в текущем сеансе.');
    return null;
  }

  function renderHome(app){
    app.screen='home';
    const panel=el('div','rex-screen rex-panel rex-hero');
    panel.append(el('p','rex-eyebrow','Русский язык · точечная практика'));
    const h=el('h1','', 'Тренажёр исключений'); h.id='rex-title'; panel.append(h);
    panel.append(el('p','rex-lead','Здесь собраны исключения, трудные формы и похожие случаи, которые легко перепутать. Решайте самостоятельно, а то, что оказалось сложным, позже встретится снова в новом контексте.'));
    const notice=makeNotice(app); if(notice) panel.append(notice);
    const actions=el('div','rex-actions');
    const start=button('Начать тренировку','rex-button-primary','start-all'); actions.append(start);
    if(hasPersonalState(app.profile)) actions.append(button('Мои исключения','rex-button-secondary','my'));
    panel.append(actions);

    if(hasPersonalState(app.profile)){
      const s=profileStats(app.profile), stats=el('div','rex-stats');
      for(const [value,label] of [[s.due,'Повторить сегодня'],[s.active,'В работе'],[s.stabilized,'Закреплено']]){const c=el('div','rex-stat');c.append(el('span','rex-stat-value',String(value)),el('span','rex-stat-label',label));stats.append(c);} panel.append(stats);
    }

    const tb=el('div','rex-topic-block'); tb.append(el('div','rex-topic-label','Тема тренировки'));
    const chips=el('div','rex-chips');
    const all=el('button','rex-chip','Все темы'); all.type='button'; all.dataset.topic=''; all.setAttribute('aria-pressed',String(!app.topicFilter)); chips.append(all);
    for(const t of app.runtime.topics){const c=el('button','rex-chip',t.label);c.type='button';c.dataset.topic=t.topic_id;c.setAttribute('aria-pressed',String(app.topicFilter===t.topic_id));chips.append(c);} tb.append(chips); panel.append(tb);
    const method=el('div','rex-method');method.innerHTML='<strong>Как работает:</strong> сначала разбираемся, какое правило здесь действует, затем отвечаем самостоятельно. Сложные случаи и ошибки позже появятся снова — уже в других примерах.';panel.append(method);
    renderInto(app,panel);
  }

  function startSession(app,source,handoffIds){
    const effectiveTopic=(source==='all_exceptions'||source==='my_exceptions')?app.topicFilter:null;
    const view=filteredRuntime(app.runtime,effectiveTopic);
    let selectorProfile=app.profile;
    if(source==='my_exceptions'){ selectorProfile={...app.profile,exceptions:Object.fromEntries(Object.entries(app.profile.exceptions||{}).filter(([,x])=>isPersonalExceptionState(x)))}; }
    const items=API.selectSession(view,selectorProfile,{source,count:SESSION_COUNT,handoff_exception_ids:handoffIds||[]});
    if(!items.length){
      if(source==='my_exceptions') return renderMy(app,true);
      const panel=el('div','rex-panel');panel.append(el('h2','', 'Сейчас нет подходящих карточек'),el('p','rex-lead','Попробуйте выбрать все темы или начать общую тренировку.'));
      const a=el('div','rex-actions');a.append(button('Все темы','rex-button-primary','clear-topic'),button('На главную','rex-button-secondary','home'));panel.append(a);return renderInto(app,panel);
    }
    app.session={id:`rex-${uuid()}`,source,items,index:0,started_at:new Date().toISOString(),answers:[],wrong_ids:new Set(),strong_correct:new Set(),current_started_at:null};
    renderCard(app);
  }

  function renderCard(app){
    const s=app.session, route=s.items[s.index], practice=app.runtime.practice_items[route.practice_item_id], exception=app.runtime.exceptions[route.exception_id];
    if(!practice||!exception) return renderFatal(app,'Не удалось открыть карточку. Обновите страницу.');
    s.current_started_at=new Date().toISOString();
    const wrap=el('div','rex-screen');
    const top=el('div','rex-session-top'); const pw=el('div','rex-progress-wrap');
    const meta=el('div','rex-progress-meta');meta.append(el('span','',`${s.index+1} из ${s.items.length}`),el('span','',topicLabel(app,exception.topic_id)));pw.append(meta);
    const bar=el('div','rex-progress');bar.setAttribute('role','progressbar');bar.setAttribute('aria-valuemin','0');bar.setAttribute('aria-valuemax',String(s.items.length));bar.setAttribute('aria-valuenow',String(s.index+1));const fill=el('span');fill.style.width=`${((s.index+1)/s.items.length)*100}%`;bar.append(fill);pw.append(bar);top.append(pw,button('Завершить','rex-button-secondary','finish'));wrap.append(top);
    const card=el('div','rex-panel rex-card');card.dataset.practiceId=practice.practice_item_id;card.append(el('div','rex-topic',topicLabel(app,exception.topic_id)),el('div','rex-prompt',practice.prompt&&practice.prompt.text?practice.prompt.text:''));
    const answerBox=el('div','rex-answer-box');
    if(practice.response_kind==='single_choice'||practice.response_kind==='classification'){
      const options=el('div','rex-options');(practice.prompt.options||[]).forEach((text,i)=>{const b=el('button','rex-option');b.type='button';b.dataset.option=String(i);b.setAttribute('aria-pressed','false');b.append(el('span','rex-option-index',String(i+1)),el('span','',text));options.append(b);});answerBox.append(options);
    }else{
      const input=el('input','rex-input');input.type='text';input.autocomplete='off';input.spellcheck=false;input.dataset.rexInput='1';input.setAttribute('aria-label','Ваш ответ');answerBox.append(input);
    }
    card.append(answerBox);
    const actions=el('div','rex-card-actions');const check=button('Проверить','rex-button-primary','check');check.disabled=true;actions.append(check);card.append(actions);wrap.append(card);renderInto(app,wrap);
    const first=card.querySelector('.rex-option,.rex-input');if(first) first.focus();
  }

  function responseFromCard(card,practice){
    if(practice.response_kind==='single_choice'||practice.response_kind==='classification'){
      const selected=card.querySelector('.rex-option[aria-pressed="true"]');return selected?{option_index:Number(selected.dataset.option)}:{option_index:null};
    }
    const input=card.querySelector('[data-rex-input]');return {text:input?input.value:''};
  }

  function persistProfile(app){if(!app.persistable) return;try{API.saveProfile(root.localStorage,app.profile);}catch(e){app.persistable=false;app.storageStatus='unavailable';}}
  function checkCard(app){
    const s=app.session,route=s.items[s.index],practice=app.runtime.practice_items[route.practice_item_id],card=app.root.querySelector('.rex-card');if(!card)return;
    const response=responseFromCard(card,practice), result=API.evaluatePractice(practice,response), answeredAt=new Date().toISOString();
    const event={event_id:`rex-event-${uuid()}`,practice_item_id:practice.practice_item_id,exception_id:practice.exception_id,mode:practice.mode,started_at:s.current_started_at||answeredAt,answered_at:answeredAt,response_time_ms:Math.max(0,Date.parse(answeredAt)-Date.parse(s.current_started_at||answeredAt)),response:result.normalized_response,is_correct:result.is_correct,source:SOURCE_MAP[s.source]||'exceptions_all',transfer_level:practice.transfer_level||'recognition',context_signature:practice.context_signature||'',was_repeated_in_session:false,previous_wrong_same_exception:s.wrong_ids.has(practice.exception_id),session_id:s.id,created_at:answeredAt};
    const updated=API.applyAttemptEvent(app.profile,event);app.profile=updated.profile;persistProfile(app);
    s.answers.push({practice_item_id:practice.practice_item_id,exception_id:practice.exception_id,is_correct:result.is_correct,transfer_level:practice.transfer_level});
    if(!result.is_correct)s.wrong_ids.add(practice.exception_id);else if(['independent_context','transfer'].includes(practice.transfer_level)&&!s.wrong_ids.has(practice.exception_id))s.strong_correct.add(practice.exception_id);
    card.querySelectorAll('button,input').forEach((x)=>x.disabled=true);
    const fb=el('div',`rex-feedback ${result.is_correct?'rex-feedback-good':'rex-feedback-bad'}`);fb.setAttribute('role','status');fb.append(el('div','rex-feedback-title',result.is_correct?'✓ Верно':'Неверно'));
    if(!result.is_correct)fb.append(el('p','rex-answer',`Правильный ответ: ${practice.feedback.correct_answer||''}`));
    if(practice.feedback&&practice.feedback.why)fb.append(el('p','',practice.feedback.why));
    const a=el('div','rex-card-actions');a.append(button('Правило и пример','rex-button-secondary','rule'),button(s.index+1<s.items.length?'Дальше':'Результат','rex-button-primary','next'));fb.append(a);card.append(fb);announce(app,result.is_correct?'Верно.':'Неверно. Показан правильный ответ.');a.querySelector('[data-action="next"]').focus();
  }

  function finishSession(app){
    const s=app.session;if(!s)return renderHome(app);const completed=s.answers.length,correct=s.answers.filter((x)=>x.is_correct).length,wrong=Array.from(s.wrong_ids),strong=Array.from(s.strong_correct).filter((id)=>!s.wrong_ids.has(id));
    if(app.profile&&Array.isArray(app.profile.session_history)){app.profile.session_history.push({session_id:s.id,started_at:s.started_at,completed_at:new Date().toISOString(),items_seen:completed,first_attempt_correct:correct,wrong_exception_ids:wrong,stabilizing_exception_ids:strong,source:s.source,schema_version:1});app.profile.session_history=app.profile.session_history.slice(-30);persistProfile(app);}
    const panel=el('div','rex-panel');panel.append(el('p','rex-eyebrow','Тренировка завершена'),el('h2','', 'Что получилось'));
    const grid=el('div','rex-result-grid');for(const [v,l] of [[completed,'Выполнено'],[correct,'Верно с первой попытки'],[wrong.length,'Нужно повторить']]){const c=el('div','rex-result-card');c.append(el('strong','',String(v)),el('span','',l));grid.append(c);}panel.append(grid);
    if(strong.length)panel.append(el('p','',`Закрепили сегодня: ${strong.length}. Это результат текущей сессии, а не отметка «освоено навсегда».`));
    const actions=el('div','rex-actions');if(wrong.length)actions.append(button('Повторить ошибки','rex-button-primary','repeat-errors'));actions.append(button('Ещё одна короткая тренировка',wrong.length?'rex-button-secondary':'rex-button-primary','start-all'));if(hasPersonalState(app.profile))actions.append(button('Мои исключения','rex-button-secondary','my'));const back=el('a','rex-button rex-button-quiet','Вернуться к тренажёрам');back.href='/trenazhery/';actions.append(back);panel.append(actions);s.final_wrong_ids=wrong;renderInto(app,panel);
  }

  function renderMy(app,fromEmpty){
    app.screen='my';const panel=el('div','rex-panel');panel.append(el('p','rex-eyebrow','Личный список'),el('h2','', 'Мои исключения'));
    const rows=personalRows(app.profile);if(!rows.length){const e=el('div','rex-empty','Мои исключения появятся здесь после тренировок.');panel.append(e);const a=el('div','rex-actions');a.append(button('Начать с основных','rex-button-primary','start-all'),button('На главную','rex-button-secondary','home'));panel.append(a);return renderInto(app,panel);}
    const groups=[['due','Повторить сегодня',(x)=>x.next_due_at&&Date.parse(x.next_due_at)<=Date.now()],['active','В работе',(x)=>!x.next_due_at||Date.parse(x.next_due_at)>Date.now()?(['active','due','stabilizing'].includes(x.status)||Number(x.active_error_count||0)>0):false],['stable','Закреплено',(x)=>x.status==='stabilized']];
    let shown=0;for(const [,label,pred] of groups){const listRows=rows.filter(pred);if(!listRows.length)continue;shown+=listRows.length;panel.append(el('h3','',label));const list=el('div','rex-list');for(const st of listRows){const ex=app.runtime.exceptions[st.exception_id];if(!ex)continue;const item=el('div','rex-list-item');const main=el('div','rex-list-main');main.append(el('div','rex-list-title',ex.label),el('div','rex-list-meta',`${topicLabel(app,ex.topic_id)} · ${st.last_result==='wrong'?'последний ответ неверный':'есть история тренировок'}`));const b=button('Потренировать','rex-button-secondary','practice-one');b.dataset.exceptionId=st.exception_id;item.append(main,b);list.append(item);}panel.append(list);}
    if(!shown)panel.append(el('div','rex-empty','На сегодня обязательных повторений нет. Можно взять новый материал.'));
    const actions=el('div','rex-actions');actions.style.marginTop='22px';actions.append(button('Общая тренировка','rex-button-primary','start-all'),button('На главную','rex-button-secondary','home'));panel.append(actions);renderInto(app,panel);
  }

  function openRule(app){
    const s=app.session;if(!s)return;const route=s.items[s.index],practice=app.runtime.practice_items[route.practice_item_id],ex=app.runtime.exceptions[route.exception_id],body=app.dialogBody;body.replaceChildren();const ref=el('div','rex-reference');
    const add=(label,text)=>{if(text==null||text==='')return;const row=el('div','rex-reference-row');row.append(el('div','rex-reference-label',label),el('div','rex-reference-text',String(text)));ref.append(row);};
    add('Коротко',ex.canonical_form||ex.label);add('Почему это особый случай',ex.why_exception);add('Как запомнить',ex.memory_cue);add('Разбор этой карточки',practice.feedback&&practice.feedback.why);ref.append(el('div','rex-reference-row rex-reference-text','После правила нужен новый самостоятельный пример — чтение подсказки само по себе не считается усвоением.'));body.append(ref);if(typeof app.dialog.showModal==='function')app.dialog.showModal();else app.dialog.setAttribute('open','');
  }

  function renderFatal(app,message){const panel=el('div','rex-error-panel');panel.append(el('h2','', 'Тренажёр не загрузился'),el('p','',message),el('p','', 'Личный прогресс не удалён. Можно обновить страницу и попробовать снова.'));renderInto(app,panel);}

  function bind(app){
    app.root.addEventListener('click',(event)=>{const option=event.target.closest('.rex-option');if(option&&!option.disabled){option.parentElement.querySelectorAll('.rex-option').forEach((x)=>x.setAttribute('aria-pressed','false'));option.setAttribute('aria-pressed','true');const check=app.root.querySelector('[data-action="check"]');if(check)check.disabled=false;return;}const chip=event.target.closest('.rex-chip');if(chip){app.topicFilter=chip.dataset.topic||null;renderHome(app);return;}const target=event.target.closest('[data-action]');if(!target)return;const action=target.dataset.action;if(action==='start-all')startSession(app,'all_exceptions',[]);else if(action==='my')renderMy(app);else if(action==='home')renderHome(app);else if(action==='clear-topic'){app.topicFilter=null;renderHome(app);}else if(action==='check')checkCard(app);else if(action==='next'){if(app.session.index+1<app.session.items.length){app.session.index+=1;renderCard(app);}else finishSession(app);}else if(action==='finish')finishSession(app);else if(action==='rule')openRule(app);else if(action==='repeat-errors'){const ids=(app.session&&app.session.final_wrong_ids)||[];startSession(app,'work_on_errors',ids);}else if(action==='practice-one')startSession(app,'work_on_errors',[target.dataset.exceptionId]);});
    app.root.addEventListener('input',(event)=>{if(event.target.matches('[data-rex-input]')){const check=app.root.querySelector('[data-action="check"]');if(check)check.disabled=!event.target.value.trim();}});
    app.root.addEventListener('keydown',(event)=>{if(event.key==='Enter'&&event.target.matches('[data-rex-input]')){const check=app.root.querySelector('[data-action="check"]');if(check&&!check.disabled){event.preventDefault();check.click();}}});
  }

  function init(options){
    const opts=options||{},rootNode=document.getElementById(opts.rootId||APP_ID);if(!rootNode)return null;const shell=rootNode.querySelector('.rex-shell'),live=rootNode.querySelector('.rex-live'),dialog=rootNode.querySelector('[data-rex-dialog]'),dialogBody=rootNode.querySelector('[data-rex-dialog-body]');
    const app={root:rootNode,shell,live,dialog,dialogBody,runtime:null,topicLabels:{},topicFilter:null,profile:null,persistable:false,storageStatus:'unavailable',session:null,screen:'boot'};bind(app);
    try{app.runtime=API.runtimeFromDocument(document,{expectedProductId:'russian_exceptions'});app.topicLabels=topicMap(app.runtime);}catch(error){renderFatal(app,'Не удалось проверить комплект данных.');console.error('[REX] runtime boot failed',error);return app;}
    const loaded=API.loadProfile(root.localStorage);app.storageStatus=loaded.status;app.persistable=loaded.persistable;app.profile=loaded.profile||API.createProfile();if(loaded.status==='new')persistProfile(app);renderHome(app);rootNode.dataset.rexReady='1';return app;
  }

  API.initRussianExceptionsTrainer=init;
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>init());else init();
})(typeof globalThis!=='undefined'?globalThis:this);
