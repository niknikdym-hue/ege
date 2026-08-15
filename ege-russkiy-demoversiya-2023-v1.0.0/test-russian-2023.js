const fs=require('fs'),vm=require('vm'),path=require('path');
const root=process.argv[2]||__dirname;
function block(i){const s=fs.readFileSync(path.join(root,`ege-russkiy-demoversiya-T123-0${i}.txt`),'utf8');const m=s.match(/<script[^>]*type="application\/json"[^>]*>([\s\S]*?)<\/script>/);return JSON.parse(m[1]);}
let tasks=[...block(2).tasks,...block(3).tasks,...block(4).tasks].sort((a,b)=>a.number-b.number);
let code=fs.readFileSync(path.join(root,'ege-russkiy-demoversiya-T123-05.txt'),'utf8').replace(/^<script>\s*/,'').replace(/\s*<\/script>\s*$/,'');
const sandbox={window:{confirm:()=>true},document:{readyState:'loading',addEventListener:()=>{},getElementById:()=>null},localStorage:{getItem:()=>null,setItem:()=>{},removeItem:()=>{}},console,Set,Math,Date,JSON,Object,Number,String,Array,RegExp,setInterval:()=>0,clearInterval:()=>{}};
vm.createContext(sandbox);vm.runInContext(code,sandbox);const api=sandbox.window.__edemoRussian2023v100;
let fail=[],checks=0;function ok(c,m){checks++;if(!c)fail.push(m)}
ok(tasks.length===27,'27 tasks');
ok(tasks.map(x=>x.number).join(',')===Array.from({length:27},(_,i)=>i+1).join(','),'numbering');
let total=0;
for(const t of tasks){
  if(t.kind==='essay')continue;
  let good=t.number===25?['21']:(['unordered_digits','ordered_sequence'].includes(t.kind)?String(t.answer).split(''):t.answer);
  ok(api.scoreTask(t,good)===t.maxScore,`task ${t.number} positive`);
  if(t.kind==='unordered_digits'&&t.number!==25){
    ok(api.scoreTask(t,String(t.answer).split('').reverse())===t.maxScore,`task ${t.number} orderless`);
    ok(api.scoreTask(t,String(t.answer)+String(t.answer)[0])===0,`task ${t.number} duplicate`);
  }
  total+=api.scoreTask(t,good);
}
ok(total===30,`part1 total ${total}`);
// task8 3/2/1/0
let t8=tasks.find(t=>t.number===8),a8=String(t8.answer).split('');
let d1=a8.slice();d1[0]='9';ok(api.scoreTask(t8,d1)===2,'task8 one mismatch=>2');
let d2=a8.slice();d2[0]='9';d2[1]='9';ok(api.scoreTask(t8,d2)===2,'task8 two mismatches=>2');
let d3=a8.slice();d3[0]='9';d3[1]='9';d3[2]='9';ok(api.scoreTask(t8,d3)===1,'task8 three mismatches=>1');
let d4=a8.slice();for(let i=0;i<4;i++)d4[i]='9';ok(api.scoreTask(t8,d4)===1,'task8 four mismatches=>1');
// task26 3/2/1/0
let t26=tasks.find(t=>t.number===26),a26=String(t26.answer).split('');
let q1=a26.slice();q1[0]='8';ok(api.scoreTask(t26,q1)===2,'task26 one mismatch=>2');
let q2=a26.slice();q2[0]='8';q2[1]='8';ok(api.scoreTask(t26,q2)===1,'task26 two mismatch=>1');
let q3=a26.slice();q3[0]='8';q3[1]='8';q3[2]='8';ok(api.scoreTask(t26,q3)===1,'task26 three mismatch=>1');
ok(api.storageKey==='eksamio_ege_russian_demo_2023_v1_0_0','storage key');
let full={essayScores:{K1:1,K2:5,K3:1,K4:1,K5:2,K6:2,K7:3,K8:3,K9:2,K10:2,K11:1,K12:1},essayZeroReasons:{},essayEligibilityConfirmed:true,essayShortBand:false};
ok(api.computeEssayScore(full)===24,'essay full 24');
let k6=JSON.parse(JSON.stringify(full));k6.essayScores.K10=1;ok(api.computeEssayScore(k6)===22,'K6 capped when K10<2');
let short=JSON.parse(JSON.stringify(full));short.essayShortBand=true;short.essayScores.K10=1;ok(api.computeEssayScore(short)===17,'essay short band 17 max');
let zero=JSON.parse(JSON.stringify(full));zero.essayZeroReasons={under70:true};ok(api.computeEssayScore(zero)===0,'under70 zero');
let dep=JSON.parse(JSON.stringify(full));dep.essayScores.K1=0;ok(api.computeEssayScore(dep)<=17,'K1 dependency');
if(fail.length){console.error(fail.join('\n'));console.error(`FAIL ${fail.length}/${checks}`);process.exit(1)}
console.log(`PASS russian-2023: ${checks} checks; part1 30/30; task8/task26 partial scoring; essay 24 and bands verified`);
