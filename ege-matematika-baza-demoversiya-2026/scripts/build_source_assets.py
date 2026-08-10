#!/usr/bin/env python3
import hashlib,json,re
from pathlib import Path
import cv2,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];PAGES=ROOT/'source-evidence'/'printed-pages';COORD=ROOT/'source-diagnostics'/'canonical-coordinates';ASSETS=ROOT/'assets';ASSETS.mkdir(parents=True,exist_ok=True)
SPECS=[("base-03-v1-temperature-chart",10,59,271,1),("base-03-v3-nickel-chart",11,56,310,1),("base-07-v1-derivative-graph",14,262,523,1),("base-07-v2-torque-chart",15,57,398,1),("base-07-v3-function-graphs",16,56,389,8),("base-09-v1-lake-plan",18,63,302,1),("base-09-v2-grid-plan",18,322,429,1),("base-10-v1-dacha-plan",19,59,150,1),("base-10-v2-wheel",19,170,251,1),("base-10-v3-fence-plan",19,271,357,3),("base-11-v1-tank",20,59,137,1),("base-11-v2-cut-prism",20,157,233,1),("base-11-v3-polyhedron",20,253,396,1),("base-11-v4-boxes",20,416,507,1),("base-12-v1-triangle-median",21,59,121,1),("base-12-v2-circle-chord",21,144,210,1),("base-12-v3-right-triangle",21,232,292,1),("base-12-v4-midline",21,312,388,1),("base-13-v1-cone",22,62,125,1),("base-13-v2-pyramid",22,145,216,1),("base-13-v3-cylinders",22,236,318,2),("base-13-v4-spheres",22,338,401,2),("base-18-v1-number-line",25,59,247,1),("base-18-v3-number-line",26,56,295,1),("base-21-v2-rectangle-partition",28,148,231,1)]
MONTHS={"янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"};LABELS=MONTHS|{"x","y","A","B","C","D","А","Б","В","Г","M","N","K","м","км","см","м²","м³","°"}
def mask_text(rgb,words,sx,sy):
 out=rgb.copy()
 for w in words:
  x0=max(0,int(w['x0']*sx)-4);x1=min(out.shape[1],int(w['x1']*sx)+5);y0=max(0,int(w['y0']*sy)-4);y1=min(out.shape[0],int(w['y1']*sy)+5)
  if x1>x0 and y1>y0:out[y0:y1,x0:x1]=255
 return out
def detect(img,words,sx,sy,y0,y1):
 masked=mask_text(np.array(img),words,sx,sy);gray=cv2.cvtColor(masked,cv2.COLOR_RGB2GRAY);raw=np.zeros_like(gray,dtype=np.uint8);top=int(y0*sy);bottom=int(y1*sy);left=int(18*sx);right=int((img.width/sx-18)*sx);raw[top:bottom,:]=(gray[top:bottom,:]<225).astype(np.uint8)*255;raw[:,:left]=0;raw[:,right:]=0;binary=cv2.morphologyEx(raw,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_RECT,(3,3)),iterations=1);binary=cv2.dilate(binary,cv2.getStructuringElement(cv2.MORPH_RECT,(5,5)),iterations=1);n,_,stats,_=cv2.connectedComponentsWithStats(binary,8);c=[]
 for i in range(1,n):
  x,y,w,h,a=[int(v) for v in stats[i]]
  if a<45 or (w<8 and h<8) or (h<=7 and w>=100) or (w<=7 and h>=100):continue
  c.append({'x':x,'y':y,'w':w,'h':h,'area':a,'bbox_area':w*h})
 c.sort(key=lambda z:(z['area'],z['bbox_area']),reverse=True);return c,raw,binary,top,bottom,left,right
def near(w,b,p=16):return not(w['x1']<b[0]-p or w['x0']>b[2]+p or w['y1']<b[1]-p or w['y0']>b[3]+p)
def label(t):
 s=t.strip().strip('.,:;()');return bool(s and (s in LABELS or re.fullmatch(r'[−–-]?\d+(?:[,.]\d+)?',s) or re.fullmatch(r'[A-Za-zА-ЯЁ]',s)))
def ascii_preview(crop,cols=56):
 rows=max(6,int(crop.height/max(1,crop.width)*cols*.45));a=np.array(crop.convert('L').resize((cols,rows),Image.Resampling.LANCZOS));return '\n'.join(''.join('█' if v<130 else('▓' if v<190 else('·' if v<235 else' '))for v in row)for row in a)
records=[];pre=[];errors=[]
for aid,page,y0,y1,count in SPECS:
 img=Image.open(PAGES/f'page-{page:02d}.webp').convert('RGB');coord=json.loads((COORD/f'page-{page:02d}.json').read_text(encoding='utf-8'));sx=img.width/coord['visual_width_pt'];sy=img.height/coord['visual_height_pt'];comps,raw,binary,bt,bb,bl,br=detect(img,coord['words'],sx,sy,y0,y1)
 if len(comps)<count:raise RuntimeError(f'{aid}: need {count} components, found {len(comps)}')
 chosen=comps[:count];px0=min(c['x']for c in chosen);py0=min(c['y']for c in chosen);px1=max(c['x']+c['w']for c in chosen);py1=max(c['y']+c['h']for c in chosen);gaps={'top_dilated':py0-bt,'bottom_dilated':bb-py1,'left_dilated':px0-bl,'right_dilated':br-px1};boundary_ink=int(raw[bt:bt+1,bl:br].sum()/255+raw[max(bt,bb-1):bb,bl:br].sum()/255+raw[bt:bb,bl:bl+1].sum()/255+raw[bt:bb,max(bl,br-1):br].sum()/255);clipped=boundary_ink>0
 if clipped:errors.append(f'{aid}: real source ink intersects official segment boundary ({boundary_ink}px)')
 bbox=[px0/sx,py0/sy,px1/sx,py1/sy];labs=[w for w in coord['words'] if y0<=(w['y0']+w['y1'])/2<=y1 and label(w['text']) and near(w,bbox)]
 if labs:bbox=[min(bbox[0],min(w['x0']for w in labs)),min(bbox[1],min(w['y0']for w in labs)),max(bbox[2],max(w['x1']for w in labs)),max(bbox[3],max(w['y1']for w in labs))]
 pad=12;bbox=[max(18,bbox[0]-pad),max(y0,bbox[1]-pad),min(coord['visual_width_pt']-18,bbox[2]+pad),min(y1,bbox[3]+pad)];cp=[int(bbox[0]*sx),int(bbox[1]*sy),int(np.ceil(bbox[2]*sx)),int(np.ceil(bbox[3]*sy))];crop=img.crop(tuple(cp));local=raw[cp[1]:cp[3],cp[0]:cp[2]]>0;e=min(5,max(1,min(local.shape)//4));edge=int(local[:e,:].sum()+local[-e:,:].sum()+local[:,:e].sum()+local[:,-e:].sum())if local.size else999999;path=ASSETS/f'{aid}.webp';crop.save(path,'WEBP',lossless=True,method=6);blob=path.read_bytes();included=[w['text']for w in coord['words']if not(w['x1']<bbox[0]or w['x0']>bbox[2]or w['y1']<bbox[1]or w['y0']>bbox[3])];prose=[x for x in included if len(x.strip('.,:;()'))>14]
 if prose:errors.append(f'{aid}: likely prose in crop {prose[:5]}')
 status='PASS' if not clipped and not prose else'FAIL';rec={'id':aid,'source_page':page,'official_segment_pt':[y0,y1],'expected_components':count,'selected_components':chosen,'dilated_component_gap_px_diagnostic_only':gaps,'source_boundary_ink_px':boundary_ink,'geometry_clipped':clipped,'crop_pt':[round(v,2)for v in bbox],'crop_px':cp,'width_px':crop.width,'height_px':crop.height,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),'lossless_webp':True,'crop_edge_source_ink_px_diagnostic_only':edge,'included_source_words':included,'status':status};records.append(rec);pre += [f'===== {aid} page={page} boundaryInk={boundary_ink} dilatedGaps={gaps} cropEdgeDiagnostic={edge} {status} =====','WORDS: '+' '.join(included),ascii_preview(crop),'']
status='PASS' if not errors and len(records)==25 else'FAIL';ev={'status':status,'source':'official FIPI 2026 base mathematics PDF via canonical printed-page render','method':'marker-to-answer segment; connected components locate geometry; clipping proof uses undilated text-masked source ink at the segment boundary','asset_count':len(records),'errors':errors,'records':records};(ROOT/'source-evidence'/'ASSET-CROP-EVIDENCE.json').write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'source-diagnostics'/'ASSET-CROP-PREVIEWS.txt').write_text('\n'.join(pre)+'\n',encoding='utf-8');print(json.dumps({'status':status,'assets':len(records),'errors':errors},ensure_ascii=False,indent=2));raise SystemExit(0 if status=='PASS' else 1)
