const fs=require('fs'),vm=require('vm'),path=require('path');
const file=process.argv[2]||path.join(__dirname,'ege-russkiy-demoversiya-T123-06.txt');
const src=fs.readFileSync(file,'utf8');
const m=src.match(/\/\/ TASK27_RESET_GUARD_START([\s\S]*?)\/\/ TASK27_RESET_GUARD_END/);
if(!m)throw new Error('reset guard block not found');
let checks=0,fails=[];
function run(coreRaw,reviewRaw){
  const data={};
  if(coreRaw!==null)data['eksamio_ege_russian_demo_2026_v4_1']=coreRaw;
  if(reviewRaw!==null)data['eksamio_ege_russian_demo_2026_v4_2_task27_review']=reviewRaw;
  const localStorage={getItem:k=>Object.prototype.hasOwnProperty.call(data,k)?data[k]:null,removeItem:k=>{delete data[k];}};
  vm.runInNewContext(m[1],{localStorage,JSON,CORE_STORAGE_KEY:'eksamio_ege_russian_demo_2026_v4_1',REVIEW_STORAGE_KEY:'eksamio_ege_russian_demo_2026_v4_2_task27_review'});
  return data;
}
function eq(name,got,want){checks++;if(got!==want)fails.push(`${name}: got ${got}, want ${want}`)}
const review='{"writingMode":"demo","frozenEssay":"OLD"}';
eq('missing core clears stale review',Object.prototype.hasOwnProperty.call(run(null,review),'eksamio_ege_russian_demo_2026_v4_2_task27_review'),false);
eq('idle core clears stale review',Object.prototype.hasOwnProperty.call(run('{"status":"idle"}',review),'eksamio_ege_russian_demo_2026_v4_2_task27_review'),false);
eq('corrupt core clears stale review',Object.prototype.hasOwnProperty.call(run('{bad json',review),'eksamio_ege_russian_demo_2026_v4_2_task27_review'),false);
eq('running core keeps review',Object.prototype.hasOwnProperty.call(run('{"status":"running"}',review),'eksamio_ege_russian_demo_2026_v4_2_task27_review'),true);
eq('finished core keeps review',Object.prototype.hasOwnProperty.call(run('{"status":"finished"}',review),'eksamio_ege_russian_demo_2026_v4_2_task27_review'),true);
eq('missing review stays missing',Object.prototype.hasOwnProperty.call(run('{"status":"idle"}',null),'eksamio_ege_russian_demo_2026_v4_2_task27_review'),false);
if(fails.length){console.error(fails.join('\n'));process.exit(1)}
console.log(`PASS task27 reset guard: ${checks} assertions`);
