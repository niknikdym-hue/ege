const fs=require('fs'),vm=require('vm'),path=require('path');
const root=process.argv[2]||__dirname;
function block(i){const s=fs.readFileSync(path.join(root,`ege-russkiy-demoversiya-T123-0${i}.txt`),'utf8');const m=s.match(/<script[^>]*type="application\/json"[^>]*>([\s\S]*?)<\/script>/);return JSON.parse(m[1]);}
let tasks=[...block(2).tasks,...block(3).tasks,...block(4).tasks].sort((a,b)=>a.number-b.number);
let code=fs.readFileSync(path.join(root,'ege-russkiy-demoversiya-T123-05.txt'),'utf8').replace(/^<script>\s*/,'').replace(/\s*<\/script>\s*$/,'');
const sandbox={window:{confirm:()=>true},document:{readyState:'loading',addEventListener:()=>{},getElementById:()=>null},localStorage:{getItem:()=>null,setItem:()=>{},removeItem:()=>{}},console,Set,Math,Date,JSON,Object,Number,String,Array,RegExp,setInterval:()=>0,clearInterval:()=>{}};vm.createContext(sandbox);vm.runInContext(code,sandbox);const api=sandbox.window.__edemoRussian2024v100;
let fail=[],checks=0;function ok(c,m){checks++;if(!c)fail.push(m)}
ok(tasks.length===27,'27 tasks');ok(tasks.map(x=>x.number).join(',')===Array.from({length:27},(_,i)=>i+1).join(','),'numbering');
let total=0;
for(const base of tasks){const variants=base.variants?.length?base.variants:[{}];for(const [idx,v] of variants.entries()){const t={...base,...v};if(t.kind==='essay')continue;let good=t.number===25?['21']:(['unordered_digits','ordered_sequence'].includes(t.kind)?String(t.answer).split(''):t.answer);ok(api.scoreTask(t,good)===t.maxScore,`task ${t.number} var ${idx+1} positive`);if(t.kind==='unordered_digits'&&t.number!==25){ok(api.scoreTask(t,String(t.answer).split('').reverse())===t.maxScore,`task ${t.number} orderless`);ok(api.scoreTask(t,String(t.answer)+String(t.answer)[0])===0,`task ${t.number} duplicate`);}if(t.kind==='ordered_sequence'){let a=String(t.answer).split('');let one=a.slice();one[0]=one[0]==='9'?'8':String(Number(one[0])+1);const exp=t.number===8?1:(t.number===26?2:null);if(exp!==null)ok(api.scoreTask(t,one)===exp,`task ${t.number} one mismatch partial`);let two=a.slice();for(let i=0;i<2;i++)two[i]=two[i]==='9'?'8':String(Number(two[i])+1);if(t.number===26)ok(api.scoreTask(t,two)===1,'task26 two mismatches =>1');if(t.number===8)ok(api.scoreTask(t,two)===1,'task8 two mismatches =>1');}}
 const t={...base,...variants[0]};if(t.number<=26){let good=t.number===25?['21']:(['unordered_digits','ordered_sequence'].includes(t.kind)?String(t.answer).split(''):t.answer);total+=api.scoreTask(t,good);}}
ok(total===29,`part1 total ${total}`);ok(api.storageKey==='eksamio_ege_russian_demo_2024_v1_0_1','storage key 2024 v1.0.1');
let full={essayScores:{K1:1,K2:3,K3:2,K4:1,K5:2,K6:1,K7:3,K8:3,K9:2,K10:2,K11:1,K12:1},essayZeroReasons:{},essayEligibilityConfirmed:true,essayShortBand:false};ok(api.computeEssayScore(full)===21,'essay full 21');
let short=JSON.parse(JSON.stringify(full));short.essayShortBand=true;ok(api.computeEssayScore(short)===15,'70-149 reduced max 15');
let zero=JSON.parse(JSON.stringify(full));zero.essayZeroReasons.under70=true;ok(api.computeEssayScore(zero)===0,'<=69 zero');
let dep=JSON.parse(JSON.stringify(full));dep.essayScores.K1=0;ok(api.computeEssayScore(dep)<=21-1,'K1 dependency applied');
const runtime=fs.readFileSync(path.join(root,'ege-russkiy-demoversiya-T123-05.txt'),'utf8');ok(!runtime.includes('replace(/\\D/g'),'no permissive digit stripping');
if(fail.length){console.error(fail.join('\n'));console.error(`FAIL ${fail.length}/${checks}`);process.exit(1)}console.log(`PASS russian-2024: ${checks} checks; part1 29/29; partial scoring; essay bands verified`);
