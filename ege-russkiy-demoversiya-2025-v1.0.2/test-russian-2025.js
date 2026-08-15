const fs=require('fs'),vm=require('vm'),path=require('path');
const root=process.argv[2]||'.';
function block(i){const s=fs.readFileSync(path.join(root,`ege-russkiy-demoversiya-T123-0${i}.txt`),'utf8');return JSON.parse(s.match(/<script[^>]*>([\s\S]*)<\/script>/)[1]);}
let tasks=[...block(2).tasks,...block(3).tasks,...block(4).tasks].sort((a,b)=>a.number-b.number);
let code=fs.readFileSync(path.join(root,'ege-russkiy-demoversiya-T123-05.txt'),'utf8').replace(/^<script>\s*/,'').replace(/\s*<\/script>\s*$/,'');
const sandbox={window:{},document:{readyState:'loading',addEventListener:()=>{},getElementById:()=>null},localStorage:{getItem:()=>null,setItem:()=>{},removeItem:()=>{}},console,Set,Math,Date,JSON,Object,Number,String,Array,RegExp};vm.createContext(sandbox);vm.runInContext(code,sandbox);const api=sandbox.window.__edemoRussian2025v100;
let fail=[],checks=0;function ok(c,m){checks++;if(!c)fail.push(m)}
ok(tasks.length===27,'27 tasks');ok(tasks.map(x=>x.number).join(',')===Array.from({length:27},(_,i)=>i+1).join(','),'numbering');
let total=0;
for(const base of tasks){const variants=base.variants?.length?base.variants:[{}];for(const [idx,v] of variants.entries()){const t={...base,...v};if(t.kind==='essay')continue;let good;if(t.number===26)good=['35'];else if(['unordered_digits','ordered_sequence'].includes(t.kind))good=String(t.answer).split('');else good=t.answer;ok(api.scoreTask(t,good)===t.maxScore,`task ${t.number} var ${idx+1} positive`);if(t.kind==='unordered_digits'&&t.number!==26){ok(api.scoreTask(t,String(t.answer).split('').reverse())===t.maxScore,`task ${t.number} orderless`);ok(api.scoreTask(t,String(t.answer)+String(t.answer)[0])===0,`task ${t.number} duplicate`);}if(t.kind==='ordered_sequence'){let a=String(t.answer).split('');let one=a.slice();one[0]=one[0]==='9'?'8':String(Number(one[0])+1);ok(api.scoreTask(t,one)===1,`task ${t.number} partial1`);let three=a.slice();for(let i=0;i<3;i++)three[i]=three[i]==='9'?'8':String(Number(three[i])+1);ok(api.scoreTask(t,three)===0,`task ${t.number} partial3`);}}
 const t={...base,...variants[0]};if(t.number<=26){let good=t.number===26?['35']:(['unordered_digits','ordered_sequence'].includes(t.kind)?String(t.answer).split(''):t.answer);total+=api.scoreTask(t,good);}}
ok(total===28,`short total ${total}`);ok(api.storageKey==='eksamio_ege_russian_demo_2025_v1_0_0','storage key');
let full={essayScores:{K1:1,K2:3,K3:2,K4:1,K5:2,K6:1,K7:3,K8:3,K9:3,K10:3},essayZeroReasons:{},essayEligibilityConfirmed:true,essayShortBand:false};ok(api.computeEssayScore(full)===22,'essay full 22');
let short=JSON.parse(JSON.stringify(full));short.essayShortBand=true;ok(api.computeEssayScore(short)===18,'100-149 cap gives 18 max');
let zero=JSON.parse(JSON.stringify(full));zero.essayZeroReasons.under100=true;ok(api.computeEssayScore(zero)===0,'<=99 zero');
let dep=JSON.parse(JSON.stringify(full));dep.essayScores.K1=0;ok(api.computeEssayScore(dep)===16,'K1 dependency');
const pp=JSON.parse(fs.readFileSync(path.join(root,'YEAR-PASSPORT-2025.json'),'utf8'));ok(pp.public_url==='/ege/russkiy/demoversiya/2025/','url');ok(pp.essay_word_rules['99_or_less']==='0/22','word rule passport');
const runtime=fs.readFileSync(path.join(root,'ege-russkiy-demoversiya-T123-05.txt'),'utf8');ok(!runtime.includes('replace(/\\D/g'),'no permissive digit stripping');ok(runtime.includes('options:["33","34","35","36","37","38","39","40","41"]'),'task26 typed sentence options');
if(fail.length){console.error(fail.join('\n'));console.error(`FAIL ${fail.length}/${checks}`);process.exit(1)}console.log(`PASS russian-2025: ${checks} checks; part1 28/28; essay bands verified`);
