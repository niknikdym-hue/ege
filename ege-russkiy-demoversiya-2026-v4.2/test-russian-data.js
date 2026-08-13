const fs=require('fs'),vm=require('vm'),path=require('path');
const root=process.argv[2]||__dirname;
function jsonBlock(file){const s=fs.readFileSync(file,'utf8');const m=s.match(/<script[^>]*>([\s\S]*)<\/script>/);if(!m)throw new Error('No JSON script '+file);return JSON.parse(m[1]);}
let tasks=[];for(const n of [2,3,4])tasks=tasks.concat(jsonBlock(path.join(root,`ege-russkiy-demoversiya-T123-0${n}.txt`)).tasks||[]);tasks.sort((a,b)=>a.number-b.number);
let code=fs.readFileSync(path.join(root,'ege-russkiy-demoversiya-T123-05.txt'),'utf8').replace(/^<script>\s*/,'').replace(/\s*<\/script>\s*$/,'');
const sandbox={window:{},document:{readyState:'loading',addEventListener:()=>{},getElementById:()=>null},localStorage:{getItem:()=>null,setItem:()=>{},removeItem:()=>{}},console,Set,Math,Date,JSON,Object,Number,String,Array,RegExp};vm.createContext(sandbox);vm.runInContext(code,sandbox);const api=sandbox.window.__edemoRussian2026v41;
let failures=[],checks=0;const assert=(cond,msg)=>{checks++;if(!cond)failures.push(msg)};
assert(tasks.length===27,`tasks ${tasks.length}`);assert(tasks.map(t=>t.number).join(',')===Array.from({length:27},(_,i)=>i+1).join(','),'task numbering');
let defaultTotal=0,variantChecks=0;
for(const base of tasks){
 const variants=base.variants?.length?base.variants:[{}];
 variants.forEach((v,idx)=>{
  const t={...base,...v};let good;
  if(t.number===26)good=['21'];else if(t.kind==='unordered_digits'||t.kind==='ordered_sequence')good=String(t.answer).split('');else good=t.answer;
  if(t.kind!=='essay'){const got=api.scoreTask(t,good);assert(got===t.maxScore,`task ${t.number} variant ${idx+1} good got ${got}/${t.maxScore}`);variantChecks++;}
  if(t.kind==='unordered_digits'&&t.number!==26){
    assert(api.scoreTask(t,String(t.answer).split('').reverse())===t.maxScore,`task ${t.number} unordered reversed`);
    assert(api.scoreTask(t,String(t.answer)+String(t.answer)[0])===0,`task ${t.number} duplicate rejected`);
    if(String(t.answer).length>1)assert(api.scoreTask(t,String(t.answer).split('').join(','))===0,`task ${t.number} commas rejected`);
    const lis=(String(t.promptHtml).match(/<li(?:\s[^>]*)?>/gi)||[]).length;const markers=[...String(t.promptHtml).matchAll(/\((\d+)\)/g)].map(m=>Number(m[1]));const count=lis||Math.max(0,...markers);if(count>0)for(const d of String(t.answer))assert(Number(d)>=1&&Number(d)<=count,`task ${t.number} digit ${d} within ${count}`);
  }
  if(t.kind==='ordered_sequence'){
    const a=String(t.answer).split('');const change=(arr,i)=>{let n=String((Number(arr[i])%9)+1);if(n===arr[i])n=String((Number(n)%9)+1);arr[i]=n;};
    let one=a.slice();change(one,0);assert(api.scoreTask(t,one)===1,`task ${t.number} one mismatch`);
    let two=a.slice();change(two,0);change(two,1);assert(api.scoreTask(t,two)===1,`task ${t.number} two mismatch`);
    let three=a.slice();change(three,0);change(three,1);change(three,2);assert(api.scoreTask(t,three)===0,`task ${t.number} three mismatch`);
  }
  if(t.kind==='word'||t.kind==='word_compact')assert(api.scoreTask(t,String(t.answer)+'.')===0,`task ${t.number} punctuation rejected`);
 });
 const t={...base,...variants[0]};if(t.number<=26){let good=t.number===26?['21']:(t.kind==='unordered_digits'||t.kind==='ordered_sequence')?String(t.answer).split(''):t.answer;defaultTotal+=api.scoreTask(t,good);}
}
assert(defaultTotal===28,`default short total ${defaultTotal}`);
const passport=JSON.parse(fs.readFileSync(path.join(root,'YEAR-PASSPORT-2026.json'),'utf8'));
const actual={};for(const t of tasks)if(t.variants?.length)actual[t.number]=t.variants.length;assert(JSON.stringify(actual)===JSON.stringify(passport.or_variant_tasks),'variant counts match passport');
const profile=JSON.parse(fs.readFileSync(path.join(root,'SUBJECT-PROFILE-RUSSIAN.json'),'utf8'));assert(profile.invariants.technical_word_counter==='advisory_only','word counter advisory');
const js=fs.readFileSync(path.join(root,'ege-russkiy-demoversiya-T123-05.txt'),'utf8');assert(!js.includes('replace(/\\D/g'), 'no permissive digit stripping');assert(js.includes('variantChoices'),'variant choices present');assert(js.includes('essayEligibilityConfirmed'),'essay gate present');
const seo=fs.readFileSync(path.join(root,'ege-russkiy-demoversiya-SEO.txt'),'utf8');const head=fs.readFileSync(path.join(root,'ege-russkiy-demoversiya-HEAD.txt'),'utf8');assert(!/2026/.test(seo),'SEO evergreen');assert(!/2026/.test(head),'HEAD evergreen');
if(failures.length){console.error(failures.join('\n'));console.error(`FAIL ${failures.length}/${checks}`);process.exit(1)}console.log(`PASS data/regression: ${checks} checks, ${variantChecks} task-variant positives, total 28/28`);
