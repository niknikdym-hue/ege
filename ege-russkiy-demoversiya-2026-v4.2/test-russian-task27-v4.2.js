const fs=require('fs'),vm=require('vm'),path=require('path');
const file=process.argv[2]||path.join(__dirname,'ege-russkiy-demoversiya-T123-06.txt');
let code=fs.readFileSync(file,'utf8').replace(/^<script>\s*/,'').replace(/\s*<\/script>\s*$/,'');
const sandbox={window:{},document:{readyState:'loading',addEventListener:()=>{},getElementById:()=>null},localStorage:{getItem:()=>null,setItem:()=>{}},console,Math,Number,String,JSON,Object,Array,RegExp,Set,Event:function(){},MutationObserver:function(){}};
vm.createContext(sandbox);vm.runInContext(code,sandbox);
const api=sandbox.window.__edemoRussian2026Task27Review;let fails=[],checks=0;
function eq(name,got,want){checks++;if(got!==want)fails.push(`${name}: got ${got}, want ${want}`)}
function finding(k,n,status='confirmed'){return Array.from({length:n},(_,i)=>({id:`${k}-${status}-${i}`,message:`${status} ${i+1}`}))}
function analysis(confirmed={},possible={}){return{version:'test-v1',confirmed,possible}}
function maxState(){let s=api.applyAnalysisResult({eligibilityConfirmed:true,zeroReasons:{},essayScores:{K1:1,K2:3,K3:2,K4:1,K5:2,K6:1}},analysis());for(const k of ['K7','K8','K9','K10'])s.essayScores[k]=3;return s}

eq('0 confirmed has no cap',api.confirmedCap(0),null);
eq('1 confirmed hard cap',api.confirmedCap(1),2);
eq('2 confirmed hard cap',api.confirmedCap(2),2);
eq('3 confirmed hard cap',api.confirmedCap(3),1);
eq('4 confirmed hard cap',api.confirmedCap(4),1);
eq('5 confirmed hard cap',api.confirmedCap(5),0);
eq('official max without auto score',api.officialEssayScore(maxState()),22);
let empty=api.applyAnalysisResult({eligibilityConfirmed:true,zeroReasons:{},essayScores:{K1:1,K2:3,K3:2,K4:1,K5:2,K6:1}},analysis());
eq('no findings do not auto-award K7',Object.prototype.hasOwnProperty.call(empty.essayScores,'K7'),false);
eq('no findings leave result incomplete',api.officialEssayScore(empty),null);
let possible=maxState();possible=api.applyAnalysisResult(possible,analysis({}, {K7:finding('K7',5,'possible')}));possible.essayScores.K7=3;
eq('possible does not change cap',api.criterionCap(possible,'K7'),null);
eq('possible does not reduce score',api.officialEssayScore(possible),22);
let one=maxState();one=api.applyAnalysisResult(one,analysis({K7:finding('K7',1)}));one.essayScores.K7=2;
eq('1 confirmed cap accepted',api.acceptedErrorScore(one,'K7'),2);
eq('1 confirmed total max',api.officialEssayScore(one),21);
one.essayScores.K7=3;eq('programmatic above cap rejected',api.acceptedErrorScore(one,'K7'),null);
eq('above cap makes result incomplete',api.officialEssayScore(one),null);
let three=maxState();three=api.applyAnalysisResult(three,analysis({K7:finding('K7',3)}));three.essayScores.K7=1;
eq('3 confirmed cap accepted',api.acceptedErrorScore(three,'K7'),1);
eq('3 confirmed total max',api.officialEssayScore(three),20);
let five=maxState();five=api.applyAnalysisResult(five,analysis({K7:finding('K7',5)}));five.essayScores.K7=0;
eq('5 confirmed cap accepted',api.acceptedErrorScore(five,'K7'),0);
eq('5 confirmed total max',api.officialEssayScore(five),19);
let clamped=maxState();clamped=api.applyAnalysisResult(clamped,analysis({K7:finding('K7',1)}));
eq('new analysis removes existing score above cap',Object.prototype.hasOwnProperty.call(clamped.essayScores,'K7'),false);
let dep=maxState();dep.essayScores.K1=0;dep.essayScores.K2=3;dep.essayScores.K3=2;eq('K1 dependency',api.officialEssayScore(dep),16);
let zero=maxState();zero.zeroReasons.under150=true;eq('149-or-less gate',api.officialEssayScore(zero),0);
let gate=maxState();gate.eligibilityConfirmed=false;eq('eligibility gate',api.officialEssayScore(gate),null);
let auto=api.analyzeEssayText('Это это пример без точки');
eq('system analysis creates confirmed finding',auto.confirmed.K10.length,1);
eq('system analysis creates possible finding',auto.possible.K8.length,1);
eq('normalized 0-24 API removed',Object.prototype.hasOwnProperty.call(api,'normalizedScore24'),false);
if(fails.length){console.error(fails.join('\n'));process.exit(1)}
console.log(`PASS task27 v4.2 unit tests: ${checks} assertions`);
