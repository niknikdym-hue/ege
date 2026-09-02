const fs=require('fs'),path=require('path'),vm=require('vm');
const root=process.argv[2]||__dirname;
function block(file){const s=fs.readFileSync(file,'utf8'),m=s.match(/<script[^>]*type="application\/json"[^>]*>([\s\S]*?)<\/script>/);if(!m)throw new Error('JSON block missing: '+file);return JSON.parse(m[1]);}
const shell=fs.readFileSync(path.join(root,'ege-russkiy-trenazher-T123-01.txt'),'utf8');
const meta=JSON.parse(shell.match(/<script type="application\/json" id="er-trainer-meta">\s*([\s\S]*?)\s*<\/script>/)[1]);
const semanticPolicy=JSON.parse(shell.match(/<script type="application\/json" id="er-semantic-bindings">\s*([\s\S]*?)\s*<\/script>/)[1]);
let cards=[],sources={};for(const file of fs.readdirSync(root).filter(x=>/T123-0[2-9]\.txt$/.test(x)).sort()){const data=block(path.join(root,file));cards.push(...(data.cards||[]));Object.assign(sources,data.sources||{});}
let runtime=fs.readFileSync(path.join(root,'ege-russkiy-trenazher-T123-10.txt'),'utf8').replace(/^<script>\s*/,'').replace(/\s*<\/script>\s*$/,'');
const sandbox={window:{},document:{readyState:'loading',addEventListener:()=>{},querySelectorAll:()=>[],getElementById:()=>null},localStorage:{getItem:()=>null,setItem:()=>{},removeItem:()=>{}},console,Set,Math,Date,JSON,Object,Number,String,Array,RegExp};vm.createContext(sandbox);vm.runInContext(runtime,sandbox);const api=sandbox.window.__erTrainerTest;
let failures=[],checks=0;const ok=(condition,message)=>{checks++;if(!condition)failures.push(message);};
ok(cards.length===174,`card count ${cards.length}`);ok(Object.keys(sources).length===9,`source count ${Object.keys(sources).length}`);ok(Object.keys(meta.tasks).length===27,'27 task metadata records');
ok(!/er-confidence|data-confidence|confidences/.test(runtime),'per-card confidence controls and storage are absent');ok(!/result-confidence|точность уверенных ответов/.test(shell),'confidence metric is absent from results');ok(!/Ответ проверен по ключу/.test(runtime),'empty explanations do not produce a generic key-check message');
ok(!/mastered-count|mastered-bar|wins>=2|навыков закреплено/.test(shell+runtime),'two correct answers never become a mastered skill claim');
ok(/createLearnerStateAdapter/.test(runtime)&&/anonymous_browser_cache/.test(runtime)&&/canonicalLearnerState/.test(runtime),'local session cache and canonical learner state have an explicit adapter boundary');
ok(semanticPolicy.canonicalStateOwner==='shared_peis'&&semanticPolicy.browserCanonicalStateWrites===false,'browser is not canonical PEIS state owner');
const bindingCounts={};for(const card of cards){const binding=api.bindingFor(card,semanticPolicy);bindingCounts[binding.status]=(bindingCounts[binding.status]||0)+1;ok(Boolean(binding.status),`${card.id} has machine-readable binding status`);}
ok(bindingCounts.exact_accepted_semantic_binding_available===1,'one current-main exact accepted composite binding is used');
ok(bindingCounts.legacy_archive===9,'nine legacy cards remain explicitly archived');
ok(bindingCounts.exam_practice_semantic_mastery_pending===164,'all other reviewed cards remain exam practice with mastery binding pending');
ok(!bindingCounts.blocked_not_safe_for_current_use,'no current card is silently marked blocked');
const exactBinding=api.bindingFor(cards.find(card=>card.id==='ege-ru-12-2026-12-01'),semanticPolicy);ok(exactBinding.mappingResolution==='COMPOSITE'&&exactBinding.masteryEffect==='NONE_IN_BROWSER','accepted task 12 composite mapping cannot create browser mastery');
ok(JSON.stringify(exactBinding.semanticTargets.map(x=>x.semanticId))===JSON.stringify(['school-verb-personal-ending-conjugation-base','school-participle-vowel-suffix-conjugation-base']),'task 12 uses only current-main canonical IDs');
const adapter=api.createLearnerStateAdapter();ok(adapter.localSessionCache.canonical===false&&adapter.canonicalLearnerState.owner==='shared_peis'&&adapter.canonicalLearnerState.browserPersistence===false,'state adapter preserves canonical ownership boundary');
ok(adapter.canonicalLearnerState.observeCheckedCard({id:'pending-card'},{},api.bindingFor({id:'pending-card'},semanticPolicy))==='SKIPPED_BINDING_PENDING','pending binding produces no PEIS observation');
for(const eventName of ['trainer_open','trainer_session_start','trainer_answer','trainer_error','trainer_session_finish','trainer_constructor_use','trainer_resume'])ok(runtime.includes(`"${eventName}"`),`${eventName} frontend event contract is present`);
ok(/er-task-material/.test(shell)&&/Материал задания/.test(runtime),'paragraph-based task material has a distinct visual block');ok(/card\.task===27/.test(runtime),'essay instructions are excluded from material-block transformation');
const perTask={};cards.forEach(c=>{perTask[c.task]=(perTask[c.task]||0)+1;});for(let n=1;n<=27;n++)ok((perTask[n]||0)>=2,`task ${n} has at least two cards`);
const fieldContract={1:['word'],2:['unordered_digits'],3:['unordered_digits'],4:['unordered_digits','word'],5:['word'],6:['word'],7:['word'],8:['ordered_sequence'],9:['unordered_digits'],10:['unordered_digits'],11:['unordered_digits'],12:['unordered_digits'],13:['unordered_digits','word'],14:['unordered_digits','word_compact'],15:['unordered_digits'],16:['unordered_digits'],17:['unordered_digits'],18:['unordered_digits'],19:['unordered_digits'],20:['unordered_digits'],21:['unordered_digits'],22:['ordered_sequence'],23:['unordered_digits'],24:['unordered_digits'],25:['word','word_compact'],26:['unordered_digits'],27:['essay']};
for(let n=1;n<=27;n++){const actual=[...new Set(cards.filter(c=>c.task===n).map(c=>c.kind))].sort(),expected=fieldContract[n].slice().sort();ok(JSON.stringify(actual)===JSON.stringify(expected),`task ${n} field kinds ${actual.join(',')}`);}
const ids=new Set(),fingerprints=new Set();for(const card of cards){
 ok(!ids.has(card.id),`unique id ${card.id}`);ids.add(card.id);
 const fp=[card.task,card.promptHtml,sources[card.sourceKey]||'',card.answer].join('|');ok(!fingerprints.has(fp),`no duplicate card ${card.id}`);fingerprints.add(fp);
 if(card.kind==='essay')continue;
 let answer;if(card.kind==='ordered_sequence')answer=String(card.answer).split('');else if(card.kind==='unordered_digits')answer=card.answerTokens||String(card.answer).split('');else answer=card.answer;
 ok(api.scoreCard(card,answer)===card.maxScore,`${card.id} correct answer scores max`);
 for(const alternate of card.altAnswers||[])ok(api.scoreCard(card,alternate)===card.maxScore,`${card.id} alternate answer ${alternate} scores max`);
 if(card.kind==='unordered_digits'){
  ok(answer.every(x=>(card.options||[]).map(String).includes(String(x))),`${card.id} answer tokens exposed by control`);
  ok(api.scoreCard(card,answer.slice().reverse())===card.maxScore,`${card.id} set order ignored`);
  ok(api.scoreCard(card,answer.concat(answer[0]))===0,`${card.id} duplicate selection rejected`);
 }
 if(card.kind==='ordered_sequence'){
  const wrong=answer.slice();wrong[0]=String((Number(wrong[0])%9)+1);ok(api.scoreCard(card,wrong)===1,`${card.id} one positional mismatch gets partial score`);
 }
 if(card.kind==='word'||card.kind==='word_compact')ok(api.scoreCard(card,String(card.answer)+'.')===0,`${card.id} punctuation rejected`);
 const material=card.promptHtml+(sources[card.sourceKey]||'');if(/выделен/i.test(card.promptHtml)){const plain=material.replace(/<[^>]+>/g,' '),visible=/<(strong|em|u)\b/i.test(material)||/[А-ЯЁ]{2,}/.test(plain)||/[а-яё][А-ЯЁ][а-яё]/.test(plain);ok(visible,`${card.id} visible emphasis marker`);}
}
for(const file of fs.readdirSync(root).filter(x=>/T123-(?:0[1-9]|10|11)\.txt$/.test(x))){ok(fs.statSync(path.join(root,file)).size<52000,`${file} below T123 size gate`);}
const integration=fs.readFileSync(path.join(root,'ege-russkiy-trenazher-T123-11.txt'),'utf8');
ok(/EKSAMIO_LEARNER_LOOP_CONFIG/.test(integration)&&/__EKSAMIO_PEIS_HOOK__/.test(integration),'bounded T123-11 installs the accepted PEIS hook only under explicit config');
ok(/Прогресс временно не синхронизирован/.test(integration),'backend failure is visible and never reported as success');
ok(!/localStorage/.test(integration)&&!/mastery\s*=/.test(integration),'integration block stores no canonical learner state in the browser');
ok(!/api[_-]?key|bearer\s+[a-z0-9]/i.test(integration),'integration block contains no client secret');
const previewPrefix='<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Тренажёр ЕГЭ по русскому языку — локальный предпросмотр</title></head><body style="margin:0">';
const previewBlocks=['01','02','03','04','05','06','07','08','10'].map(n=>fs.readFileSync(path.join(root,`ege-russkiy-trenazher-T123-${n}.txt`),'utf8').trim());
const expectedPreview=previewPrefix+previewBlocks.join('\n')+'\n</body></html>\n';
ok(fs.readFileSync(path.join(root,'ege-russkiy-trenazher-PREVIEW.html'),'utf8')===expectedPreview,'public local preview stays an exact ordered assembly of the nine deployable T123 blocks');
const publicFiles=['ege-russkiy-trenazher-T123-01.txt','ege-russkiy-trenazher-T123-10.txt','ege-russkiy-trenazher-HEAD.txt','ege-russkiy-trenazher-SEO.txt'];for(const file of publicFiles)ok(!/ФИПИ/i.test(fs.readFileSync(path.join(root,file),'utf8')),`${file} has no public source reference`);
const task26=cards.filter(c=>c.task===26);ok(task26.every(c=>c.answerTokens&&c.answerTokens.every(x=>Number(x)>=10)),`task 26 uses sentence numbers, not separate digits`);
const task4=cards.filter(c=>c.task===4),officialTask4=task4.filter(c=>!c.bankSource),supplementalTask4=task4.filter(c=>c.bankSource==='orthoepic-list-2026');ok(task4.length===40,'task 4 has a substantial forty-card bank');ok(officialTask4.length===4,'task 4 keeps four non-duplicate official examples');ok(supplementalTask4.length===36,'task 4 has thirty-six current supplemental cards');
const task4Keys={2022:'гражданство',2024:'24',2025:'145',2026:'125'};for(const card of officialTask4){ok(card.answer===task4Keys[card.sourceYear],`${card.id} official orthoepic key`);ok((card.promptHtml.match(/<strong>[А-ЯЁ]<\/strong>/g)||[]).length===5,`${card.id} five explicitly highlighted stress letters`);}
ok(task4.find(c=>c.sourceYear===2022).kind==='word','2022 task 4 uses a text answer');ok(task4.filter(c=>!c.legacyFormat).length===38,'control mode has thirty-eight current task 4 cards');ok(task4.filter(c=>!c.legacyFormat).every(c=>c.kind==='unordered_digits'),'current task 4 uses multiple-choice checkboxes');ok(/Отметьте все варианты/.test(runtime),'runtime replaces the obsolete task 4 write-a-word algorithm');
ok(api.pointPhrase(0)==='0 баллов'&&api.pointPhrase(1)==='1 балл'&&api.pointPhrase(2)==='2 балла','feedback uses explicit primary-point units');const task4Diagnostic=api.selectionDiagnostic({kind:'unordered_digits',answerTokens:['2','4','5']},{answer:['1','2','4','5']});ok(/3 из 3/.test(task4Diagnostic)&&/лишних позиций: 1/.test(task4Diagnostic),'multiple-choice feedback separates found and extra positions from the primary score');
const orthoBank=JSON.parse(fs.readFileSync(path.join(root,'ORTHOEPIC-TRAINER-BANK.json'),'utf8'));ok(orthoBank.entries.length===96,'orthoepic source has 96 audited entries');ok(orthoBank.cardCount===36,'orthoepic source requests 36 cards');const retired=['нарОст','пОручни','жилОсь','навралА','совралА','сорИт','кормЯщий','поднЯв','донЕльзя','зАтемно'];ok(retired.every(word=>!orthoBank.entries.some(entry=>entry.correct===word)),'2026 supplemental bank excludes retired words');for(const entry of orthoBank.entries){ok((entry.correct.match(/[АЕЁИОУЫЭЮЯ]/g)||[]).length===1,`${entry.id} one normative stress`);ok((entry.wrong.match(/[АЕЁИОУЫЭЮЯ]/g)||[]).length===1,`${entry.id} one distractor stress`);ok(api.normText(entry.correct)===api.normText(entry.wrong),`${entry.id} distractor keeps the same word form`);}const usedOrthoIds=new Set(supplementalTask4.flatMap(card=>card.bankEntryIds||[]));ok(usedOrthoIds.size===orthoBank.entries.length,'all orthoepic entries are exercised');const orthoPositionCounts={'1':0,'2':0,'3':0,'4':0,'5':0};supplementalTask4.forEach(card=>String(card.answer).split('').forEach(position=>orthoPositionCounts[position]++));ok(Object.values(orthoPositionCounts).every(count=>count===18),'correct task 4 positions are perfectly balanced');
const task2=cards.filter(c=>c.task===2);ok(task2.some(c=>String(c.answer).length>1),'task 2 keeps multiple-answer examples');ok(!/card\.task===2(?!\d)/.test(runtime),'runtime does not force task 2 into single-choice mode');
const compact14=cards.find(c=>c.id==='ege-ru-14-2023-14-01');ok(api.scoreCard(compact14,'навстречувдали')===compact14.maxScore,'compact official task 14 answer accepted');ok(api.scoreCard(compact14,'навстречу вдали')===compact14.maxScore,'spaced task 14 answer accepted');
const legacyCards=cards.filter(c=>c.legacyFormat);ok(legacyCards.length===9&&legacyCards.every(c=>([13,14].includes(c.task)&&c.sourceYear<2024)||(c.task===22&&c.sourceYear<2025)||(c.task===4&&c.sourceYear<2025)),'only superseded task 4/13/14/22 material is marked legacy');
const task25_2025=cards.find(c=>c.id==='ege-ru-25-2025-25-01');ok(api.scoreCard(task25_2025,'насвоёмместе')===task25_2025.maxScore,'compact 2025 phraseological answer accepted');
const task24_2023=cards.find(c=>c.id==='ege-ru-24-2023-23-01');ok(task24_2023&&task24_2023.answer==='35'&&/рассуждение/.test(task24_2023.promptHtml),'2023 task 24 prompt and answer corrected from official material');
for(const id of ['ege-ru-15-2026-15-01','ege-ru-15-2023-15-01','ege-ru-15-2022-15-01','ege-ru-17-2026-17-01','ege-ru-17-2024-17-01','ege-ru-17-2023-17-01']){const card=cards.find(c=>c.id===id);ok(card&&!card.options.includes('5'),`${id} has no phantom option 5`);}
if(failures.length){console.error(failures.join('\n'));console.error(`FAIL ${failures.length}/${checks}`);process.exit(1);}console.log(`PASS trainer data: ${checks} checks, ${cards.length} cards, ${Object.keys(sources).length} source texts`);
