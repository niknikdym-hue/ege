const fs=require('fs'),path=require('path');const root=process.argv[2]||__dirname;
function data(n){let s=fs.readFileSync(path.join(root,`ege-russkiy-demoversiya-T123-0${n}.txt`),'utf8');return JSON.parse(s.match(/>(\{.*\})<\/script>/s)[1]);}
let tasks=[...data(2).tasks,...data(3).tasks,...data(4).tasks],by=Object.fromEntries(tasks.map(t=>[t.number,t]));let checks=0;function ck(x,m){checks++;if(!x)throw Error(m)}
const answers={1:'1234',2:'все',3:'2',4:'гражданство',5:'памятные',6:'очень',7:'полутораста',8:'43827',9:'34',10:'134',11:'15',12:'235',13:'неподвижные',14:'навстречувдали',15:'124',16:'125',17:'34',18:'124567',19:'34',20:'23',21:'13',22:'135',23:'145',24:'внезапно',25:'12',26:'2519'};
for(let n=1;n<=26;n++)ck(by[n].answer===answers[n],`answer ${n}`);ck([...Array(26)].reduce((s,_,i)=>s+by[i+1].maxScore,0)===33,'part1 33');
function posScore(expected,got){if(got.length!==expected.length)return 0;let n=0;for(let i=0;i<expected.length;i++)if(expected[i]===got[i])n++;return n}
ck(posScore('43827','43827')===5,'t8 full');ck(posScore('43827','43826')===4,'t8 partial4');ck(posScore('43827','43867')===4,'t8 partial');ck(posScore('2519','2519')===4,'t26 full');ck(posScore('2519','2518')===3,'t26 partial3');ck(by[27].maxScore===25,'essay25');
console.log(`PASS russian-2022: ${checks} checks`);
