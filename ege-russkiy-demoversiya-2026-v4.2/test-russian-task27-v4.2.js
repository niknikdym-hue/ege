const fs=require('fs'),vm=require('vm'),path=require('path');
const file=process.argv[2]||path.join(__dirname,'ege-russkiy-demoversiya-T123-06.txt');
let code=fs.readFileSync(file,'utf8').replace(/^<script>\s*/,'').replace(/\s*<\/script>\s*$/,'');
const sandbox={window:{},document:{readyState:'loading',addEventListener:()=>{},getElementById:()=>null},localStorage:{getItem:()=>null,setItem:()=>{}},console,Math,Number,String,JSON,Object,Array,RegExp,Set,Event:function(){},MutationObserver:function(){}};
vm.createContext(sandbox);vm.runInContext(code,sandbox);
const api=sandbox.window.__edemoRussian2026Task27Review;let fails=[];
function eq(name,got,want){if(got!==want)fails.push(`${name}: got ${got}, want ${want}`)}
for(const [n,w] of [[0,3],[1,2],[2,2],[3,1],[4,1],[5,0],[12,0]])eq(`K7-K10 ${n}`,api.scoreByConfirmedErrors(n),w);
eq('no data is unknown',api.scoreByConfirmedErrors(null),null);
const base={eligibilityConfirmed:true,zeroReasons:{},essayScores:{K1:1,K2:3,K3:2,K4:1,K5:2,K6:1},confirmedErrors:{K7:0,K8:0,K9:0,K10:0}};
eq('official max',api.officialEssayScore(base),22);
eq('normalized max',api.normalizedScore24(22),24);
let missing=JSON.parse(JSON.stringify(base));missing.confirmedErrors.K8=null;eq('missing confirmed does not become error',api.officialEssayScore(missing),null);
let possible=JSON.parse(JSON.stringify(base));possible.possibleErrors={K7:5,K8:5,K9:5,K10:5};eq('possible errors do not lower score',api.officialEssayScore(possible),22);
let dep=JSON.parse(JSON.stringify(base));dep.essayScores.K1=0;dep.essayScores.K2=3;dep.essayScores.K3=2;eq('K1 dependency',api.officialEssayScore(dep),16);
let zero=JSON.parse(JSON.stringify(base));zero.zeroReasons.under150=true;eq('149-or-less gate',api.officialEssayScore(zero),0);
let gate=JSON.parse(JSON.stringify(base));gate.eligibilityConfirmed=false;eq('eligibility gate',api.officialEssayScore(gate),null);
if(fails.length){console.error(fails.join('\n'));process.exit(1)}
console.log('PASS task27 hotfix unit tests: 17 assertions');
