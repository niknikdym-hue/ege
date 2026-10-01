from pathlib import Path
import base64,json,hashlib,zipfile,re,sys
root=Path(__file__).resolve().parents[1]
prefix='ege-obshchestvoznaniye-demoversiya'
data=json.loads((root/f'{prefix}-EXAM-DATA.json').read_text('utf-8'))
asset_pattern=re.compile(r'src="(assets/[^"]+\.webp)"')
def inline_assets(html):
 def repl(match):
  path=root/match.group(1)
  return 'src="data:image/webp;base64,'+base64.b64encode(path.read_bytes()).decode('ascii')+'"'
 return asset_pattern.sub(repl,html)
for task in data['tasks']:task['body']=inline_assets(task['body'])
tasks=sorted(data['tasks'],key=lambda x:x['n'])
def compact(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
blocks={2:f'<script>window.EKSAMIO_SOC.tasks.push(...{compact(tasks[:8])});</script>\n',3:f'<script>window.EKSAMIO_SOC.tasks.push(...{compact(tasks[8:12])});</script>\n',4:f'<script>window.EKSAMIO_SOC.sourceText={compact(data["sourceText"])};window.EKSAMIO_SOC.tasks.push(...{compact(tasks[12:20])});</script>\n',5:f'<script>window.EKSAMIO_SOC.tasks.push(...{compact(tasks[20:])});</script>\n'}
for n,s in blocks.items():(root/f'{prefix}-T123-{n:02d}.txt').write_text(s,'utf-8')
head=(root/f'{prefix}-HEAD.txt').read_text('utf-8')
body='\n'.join((root/f'{prefix}-T123-{i:02d}.txt').read_text('utf-8') for i in range(1,7))
preview='<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+head+'</head><body>'+body+'</body></html>\n'
(root/f'{prefix}-PREVIEW.html').write_text(preview,'utf-8')
manifest=root/f'{prefix}-MANIFEST-SHA256.txt'
if manifest.exists():manifest.unlink()
files=sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!=manifest.name)
manifest.write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}\n' for p in files),'utf-8')
out=root.parent/'ege-obshchestvoznaniye-demoversiya-v1.0.5.zip'
if out.exists():out.unlink()
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(root.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
   arc=(Path(root.name)/p.relative_to(root)).as_posix()
   info=zipfile.ZipInfo(arc,date_time=(1980,1,1,0,0,0))
   info.compress_type=zipfile.ZIP_DEFLATED
   info.external_attr=0o100644<<16
   z.writestr(info,p.read_bytes())
print(out)
