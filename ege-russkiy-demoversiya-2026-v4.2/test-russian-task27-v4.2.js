const fs=require('fs'),vm=require('vm'),path=require('path');
const file=process.argv[2]||path.join(__dirname,'ege-russkiy-demoversiya-T123-06.txt');
let code=fs.readFileSync(file,'utf8').replace(/^<script>\s*/,'').replace(/\s*<\/script>\s*$/,'');
const sandbox={window:{},document:{readyState:'loading',addEventListener:()=>{},getElementById:()=>null},localStorage:{getItem:()=>null,setItem:()=>{}},console,Math,Number,String,JSON,Object,Array,RegExp,Set,Event:function(){},MutationObserver:function(){}};
vm.createContext(sandbox);vm.runInContext(code,sandbox);
const api=sandbox.window.__edemoRussian2026Task27Review;let fails=[],checks=0;
function eq(name,got,want){checks++;if(got!==want)fails.push(`${name}: got ${got}, want ${want}`)}
function finding(k,n,status='confirmed'){return Array.from({length:n},(_,i)=>({id:`${k}-${status}-${i}`,message:`${status} ${i+1}`}))}
function analysis(confirmed={},possible={},technical=[]){return{version:'test-v1',confirmed,possible,technical}}
function confirmedTotal(result){return ['K7','K8','K9','K10'].reduce((sum,k)=>sum+result.confirmed[k].length,0)}
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
let possibleK10=maxState();possibleK10=api.applyAnalysisResult(possibleK10,analysis({}, {K10:finding('K10',5,'possible')}));possibleK10.essayScores.K10=3;
eq('possible K10 has no hard cap',api.criterionCap(possibleK10,'K10'),null);
eq('possible K10 keeps full score',api.officialEssayScore(possibleK10),22);
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
let adjacent=api.analyzeEssayText('Это это было важно');
eq('adjacent duplicate is not confirmed K10',adjacent.confirmed.K10.length,0);
eq('adjacent duplicate is possible K10',adjacent.possible.K10.length,1);
let adjacentState=api.applyAnalysisResult(maxState(),adjacent);adjacentState.essayScores.K10=3;
eq('adjacent possible K10 has no cap',api.criterionCap(adjacentState,'K10'),null);
eq('adjacent possible K10 keeps 22',api.officialEssayScore(adjacentState),22);
let spacing=api.analyzeEssayText('Это пример , текста.');
eq('space before punctuation is not confirmed K8',spacing.confirmed.K8.length,0);
eq('space before punctuation is not possible K8',spacing.possible.K8.length,0);
eq('space before punctuation is technical only',spacing.technical.length,1);
let spacingState=api.applyAnalysisResult(maxState(),spacing);spacingState.essayScores.K8=3;
eq('technical spacing has no K8 cap',api.criterionCap(spacingState,'K8'),null);
eq('technical spacing keeps 22',api.officialEssayScore(spacingState),22);
let builtinAudit=api.analyzeEssayText('Вообщем какбудто изза ихний. Это это слово , текст без точки');
eq('built-in preliminary analyzer creates no confirmed findings',confirmedTotal(builtinAudit),0);
eq('spelling candidates are possible',builtinAudit.possible.K7.length,3);
eq('grammar candidate is possible',builtinAudit.possible.K9.length,1);
eq('speech repetition candidate is possible',builtinAudit.possible.K10.length,1);
eq('technical spacing stays separate',builtinAudit.technical.length,1);
let stylistic=api.analyzeEssayText('Далеко, далеко за рекой мерцал свет.');
eq('potential stylistic repetition is never confirmed',stylistic.confirmed.K10.length,0);
let keyLexis=api.analyzeEssayText('Герой думает. Герой действует. Герой меняется.');
eq('key lexical repetition is not confirmed',keyLexis.confirmed.K10.length,0);
eq('three repetitions in one paragraph are possible',keyLexis.possible.K10.length,1);
let paragraphs=api.analyzeEssayText('Герой принимает решение.\n\nГерой отвечает за него.');
eq('repetition across paragraph boundary is not confirmed',paragraphs.confirmed.K10.length,0);
eq('repetition across paragraph boundary is not aggregated',paragraphs.possible.K10.length,0);
let quoted=api.analyzeEssayText('Автор поясняет, что написание «вообщем» ошибочно.');
eq('quoted spelling candidate is not confirmed',quoted.confirmed.K7.length,0);
eq('quoted spelling candidate remains possible',quoted.possible.K7.length,1);
let noEnding=api.analyzeEssayText('Текст без завершающего знака');
eq('missing terminal punctuation is possible K8',noEnding.possible.K8.length,1);
eq('missing terminal punctuation is not confirmed K8',noEnding.confirmed.K8.length,0);
eq('normalized 0-24 API removed',Object.prototype.hasOwnProperty.call(api,'normalizedScore24'),false);

const addon=fs.readFileSync(path.join(__dirname,'ege-russkiy-demoversiya-T123-07.txt'),'utf8');
eq('T123-07 multiple file input enhancement',/input\.multiple=true/.test(addon),true);
eq('T123-07 explicit text check',/Проверить текст/.test(addon)&&/speller\.yandex\.net/.test(addon),true);
eq('T123-07 does not auto-confirm speller findings',/possible\.K7\.push/.test(addon)&&!/confirmed\.K7\.push/.test(addon),true);
if(fails.length){console.error(fails.join('\n'));process.exit(1)}

eq('displayed demo total formula',/shortScore\+score/.test(code),true);
eq('K1-K10 optional scoring help wired',/criterionHelp\(c\.id\)/.test(code)&&/criterionHelp\(k\)/.test(code),true);
console.log(`PASS task27 v4.2 unit tests: ${checks} assertions`);
