from pathlib import Path
from io import BytesIO
import base64, hashlib, json, re, sys
import pymupdf
from PIL import Image, ImageOps, ImageDraw

ROOT=Path(__file__).resolve().parent
PKG=ROOT/'ege-fizika-demoversiya-v3-1-fixed'
PDF=PKG/'source/ege-2026-fizika-demoversiya.pdf'
EXPECTED_PDF_SHA='e93318f05b38a664a09a7b154a24710930b833c7a18110f81470398f34fa716a'
REF_W,REF_H=969,1370
# Manually verified portrait-page boxes on exact official FIPI logical pages.
# These replace only crops that failed human four-edge inspection after the automated V3.3 gate.
FIXES={
 't02':(6,(605,855,880,938)),
 't06a':(8,(140,505,390,945)),
 't21s':(22,(395,165,640,360)),
 't22s':(23,(615,704,885,925)),
 't24sb':(27,(680,495,845,770)),
 't25p':(16,(690,700,890,860)),
 't25s':(29,(255,965,795,1175)),
 't26v2p':(17,(560,495,850,625)),
 't26v2s':(35,(570,1095,890,1255)),
}
JSON_SCRIPTS=[
 (PKG/'ege-fizika-demoversiya-T123-02.txt','ephys-data-1','tasks'),
 (PKG/'ege-fizika-demoversiya-T123-03.txt','ephys-data-2','tasks'),
 (PKG/'ege-fizika-demoversiya-T123-04.txt','ephys-data-3','tasks'),
 (PKG/'ege-fizika-demoversiya-T123-05.txt','ephys-data-4','variants26'),
]

def sha(path):
 h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def logical_page_image(doc,logical,scale=3.0):
 physical=(logical+1)//2; slot=1 if logical%2 else 2
 page=doc[physical-1]; old=page.rotation; page.set_rotation(0); r=page.rect; half=r.height/2
 clip=pymupdf.Rect(0,0,r.width,half) if slot==1 else pymupdf.Rect(0,half,r.width,r.height)
 pix=page.get_pixmap(matrix=pymupdf.Matrix(scale,scale),clip=clip,alpha=False)
 im=Image.open(BytesIO(pix.tobytes('png'))).convert('RGB').rotate(90,expand=True)
 page.set_rotation(old)
 return im

def render_fix_crops():
 if sha(PDF)!=EXPECTED_PDF_SHA: raise RuntimeError('official FIPI PDF byte lock mismatch')
 doc=pymupdf.open(PDF); out={}; meta={}; cards=[]
 for cid,(logical,box) in FIXES.items():
  full=logical_page_image(doc,logical)
  sx=full.width/REF_W; sy=full.height/REF_H
  x0,y0,x1,y1=box
  actual=(round(x0*sx),round(y0*sy),round(x1*sx),round(y1*sy))
  crop=full.crop(actual)
  bio=BytesIO(); crop.save(bio,'WEBP',lossless=True,method=6); raw=bio.getvalue()
  out[cid]=base64.b64encode(raw).decode('ascii')
  meta[cid]={'id':cid,'logical_page':logical,'manual_reference_box_px_969x1370':list(box),'rendered_pixel_width':crop.width,'rendered_pixel_height':crop.height,'webp_sha256':hashlib.sha256(raw).hexdigest(),'four_edge_human_gate':'CANDIDATE'}
  thumb=ImageOps.contain(crop,(460,280)); card=Image.new('RGB',(480,320),'white'); card.paste(thumb,((480-thumb.width)//2,8)); ImageDraw.Draw(card).text((10,295),cid,fill='black'); cards.append(card)
 sheet=Image.new('RGB',(960,((len(cards)+1)//2)*320),(235,235,235))
 for i,c in enumerate(cards): sheet.paste(c,((i%2)*480,(i//2)*320))
 return out,meta,sheet

def load_script(path,sid):
 text=path.read_text(encoding='utf-8')
 pat=re.compile(r'(<script\s+type="application/json"\s+id="'+re.escape(sid)+r'">)(.*?)(</script>)',re.S)
 m=pat.search(text)
 if not m: raise RuntimeError(f'JSON block {sid} not found')
 return text,pat,json.loads(m.group(2))

def replace_crop(html,cid,b64):
 pat=re.compile(r'(<img\b[^>]*data-source-crop="'+re.escape(cid)+r'"[^>]*\bsrc=")data:image/webp;base64,[^"]+("[^>]*>)')
 new,n=pat.subn(lambda m:m.group(1)+'data:image/webp;base64,'+b64+m.group(2),html,count=1)
 return new,n

def apply(mark_pass=False):
 crops,meta,sheet=render_fix_crops()
 seen={k:0 for k in FIXES}
 for path,sid,key in JSON_SCRIPTS:
  text,pat,obj=load_script(path,sid)
  for row in obj.get(key,[]):
   for field in ('promptHtml','solutionHtml'):
    h=row.get(field)
    if not h: continue
    for cid,b64 in crops.items():
     h,n=replace_crop(h,cid,b64); seen[cid]+=n
    row[field]=h
  body=json.dumps(obj,ensure_ascii=False,separators=(',',':'))
  text,n=pat.subn(lambda m:m.group(1)+body+m.group(3),text,count=1)
  if n!=1: raise RuntimeError(f'failed saving {sid}')
  path.write_text(text,encoding='utf-8')
 if any(v!=1 for v in seen.values()): raise RuntimeError(f'crop replacement counts invalid: {seen}')

 amap=PKG/'PHYSICS-2026-V3.3-VISUAL-ASSET-MAP.json'
 data=json.loads(amap.read_text(encoding='utf-8'))
 byid={x['id']:x for x in data['assets']}
 for cid,m in meta.items():
  if cid not in byid: raise RuntimeError(f'{cid} missing from visual asset map')
  byid[cid].update(m)
  if mark_pass: byid[cid]['four_edge_human_gate']='PASS'
 data['manual_visual_correction']='PASS' if mark_pass else 'CANDIDATE_FOR_HUMAN_REVIEW'
 data['manual_visual_correction_date']='2026-08-20'
 amap.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

 parts=[(PKG/f'ege-fizika-demoversiya-T123-0{i}.txt').read_text(encoding='utf-8') for i in range(1,7)]
 preview='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ЕГЭ физика 2026 — preview</title></head><body>'+('\n'.join(parts))+'</body></html>'
 (PKG/'ege-fizika-demoversiya-PREVIEW.html').write_text(preview,encoding='utf-8')
 out=Path('/tmp/physics-manual-crop-review'); out.mkdir(parents=True,exist_ok=True); sheet.save(out/'CONTACT-SHEET.jpg',quality=93)
 (out/'manual-crop-map.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 if mark_pass:
  ev=PKG/'PHYSICS-2026-V3.3-ACCEPTANCE-EVIDENCE.json'; e=json.loads(ev.read_text(encoding='utf-8')); e['manual_four_edge_visual_gate']='PASS'; e['manual_four_edge_visual_gate_date']='2026-08-20'; e['manual_correction_ids']=sorted(FIXES); ev.write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  cur=PKG/'PHYSICS-2026-CURRENT-ACCEPTANCE-EVIDENCE.json'; c=json.loads(cur.read_text(encoding='utf-8')); c['manual_four_edge_visual_gate']='PASS'; cur.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  gate=PKG/'ege-fizika-demoversiya-SOURCE-GATE.txt'; g=gate.read_text(encoding='utf-8');
  if 'MANUAL_FOUR_EDGE_VISUAL_GATE=' in g: g=re.sub(r'MANUAL_FOUR_EDGE_VISUAL_GATE=.*', 'MANUAL_FOUR_EDGE_VISUAL_GATE=PASS', g)
  else: g=g.replace('VISUAL_SIZE_GATE=PASS_PER_ASSET_LIMITS\n','VISUAL_SIZE_GATE=PASS_PER_ASSET_LIMITS\nMANUAL_FOUR_EDGE_VISUAL_GATE=PASS\n')
  gate.write_text(g,encoding='utf-8')
  freeze=PKG/'ACCEPTED-TECHNICAL-REFERENCE-2026-08-20.txt'; f=freeze.read_text(encoding='utf-8');
  if 'MANUAL_FOUR_EDGE_VISUAL_GATE=' not in f: f=f.replace('VISUAL_SIZE_GATE=PASS\n','VISUAL_SIZE_GATE=PASS\nMANUAL_FOUR_EDGE_VISUAL_GATE=PASS\n')
  freeze.write_text(f,encoding='utf-8')
 print('MANUAL_CROP_APPLY_PASS',mark_pass)

if __name__=='__main__': apply(mark_pass=(len(sys.argv)>1 and sys.argv[1]=='pass'))
