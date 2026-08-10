#!/usr/bin/env python3
import hashlib
import json
import re
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "source-evidence" / "printed-pages"
COORD = ROOT / "source-diagnostics" / "canonical-coordinates"
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

# Exact official-example bands derived from CANONICAL-SOURCE-MARKERS.txt.
# Start is after TASK_NUMBER/ИЛИ; end is before the example's own Ответ: line.
SPECS = [
    ("base-03-v1-temperature-chart",10,74,270,1),("base-03-v3-nickel-chart",11,71,309,1),
    ("base-07-v1-derivative-graph",14,277,522,1),("base-07-v2-torque-chart",15,72,397,1),("base-07-v3-function-graphs",16,71,388,8),
    ("base-09-v1-lake-plan",18,77,300,1),("base-09-v2-grid-plan",18,337,427,1),
    ("base-10-v1-dacha-plan",19,73,148,1),("base-10-v2-wheel",19,185,249,1),("base-10-v3-fence-plan",19,285,356,3),
    ("base-11-v1-tank",20,73,136,1),("base-11-v2-cut-prism",20,172,232,1),("base-11-v3-polyhedron",20,268,395,1),("base-11-v4-boxes",20,431,506,2),
    ("base-12-v1-triangle-median",21,73,120,1),("base-12-v2-circle-chord",21,159,209,1),("base-12-v3-right-triangle",21,247,291,1),("base-12-v4-midline",21,327,387,1),
    ("base-13-v1-cone",22,76,124,1),("base-13-v2-pyramid",22,159,215,1),("base-13-v3-cylinders",22,251,317,2),("base-13-v4-spheres",22,353,400,2),
    ("base-18-v1-number-line",25,73,245,1),("base-18-v3-number-line",26,71,294,1),("base-21-v2-rectangle-partition",28,163,229,1),
]

MONTHS={"янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"}
LABEL_WORDS=MONTHS|{"x","y","A","B","C","D","А","Б","В","Г","M","N","K","м","км","см","м²","м³","°"}


def mask_text(rgb, words, sx, sy):
    out=rgb.copy()
    for w in words:
        x0=max(0,int(w['x0']*sx)-4);x1=min(out.shape[1],int(w['x1']*sx)+5)
        y0=max(0,int(w['y0']*sy)-4);y1=min(out.shape[0],int(w['y1']*sy)+5)
        if x1>x0 and y1>y0: out[y0:y1,x0:x1]=255
    return out


def detect_components(img, words, sx, sy, y0_pt, y1_pt):
    rgb=np.array(img)
    masked=mask_text(rgb,words,sx,sy)
    gray=cv2.cvtColor(masked,cv2.COLOR_RGB2GRAY)
    binary=np.zeros_like(gray,dtype=np.uint8)
    top=max(0,int(y0_pt*sy));bottom=min(img.height,int(y1_pt*sy))
    binary[top:bottom,:]=(gray[top:bottom,:]<225).astype(np.uint8)*255
    binary[:,:int(18*sx)]=0; binary[:,int((img.width/sx-18)*sx):]=0
    binary=cv2.morphologyEx(binary,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_RECT,(3,3)),iterations=1)
    binary=cv2.dilate(binary,cv2.getStructuringElement(cv2.MORPH_RECT,(5,5)),iterations=1)
    n,_,stats,_=cv2.connectedComponentsWithStats(binary,8)
    comps=[]
    for i in range(1,n):
        x,y,w,h,area=[int(v) for v in stats[i]]
        if area<45 or (w<8 and h<8): continue
        # Exclude answer/separator rules and isolated page furniture.
        if h<=7 and w>=100: continue
        if w<=7 and h>=100: continue
        comps.append({'x':x,'y':y,'w':w,'h':h,'area':area,'bbox_area':w*h})
    comps.sort(key=lambda c:(c['area'],c['bbox_area']),reverse=True)
    return comps,binary


def near(word,bbox,pad=16):
    x0,y0,x1,y1=bbox
    return not (word['x1']<x0-pad or word['x0']>x1+pad or word['y1']<y0-pad or word['y0']>y1+pad)


def is_diagram_label(text):
    t=text.strip().strip('.,:;()')
    if not t:return False
    if t in LABEL_WORDS:return True
    if re.fullmatch(r'[−–-]?\d+(?:[,.]\d+)?',t):return True
    if re.fullmatch(r'[A-Za-zА-ЯЁ]',t):return True
    return False


def ascii_preview(crop,columns=56):
    rows=max(6,int(crop.height/max(1,crop.width)*columns*.45))
    small=np.array(crop.convert('L').resize((columns,rows),Image.Resampling.LANCZOS))
    return '\n'.join(''.join('█' if v<130 else ('▓' if v<190 else ('·' if v<235 else ' ')) for v in row) for row in small)

records=[];preview=[];errors=[]
for asset_id,page,y0_pt,y1_pt,expected_count in SPECS:
    img=Image.open(PAGES/f'page-{page:02d}.webp').convert('RGB')
    coord=json.loads((COORD/f'page-{page:02d}.json').read_text(encoding='utf-8'))
    sx=img.width/coord['visual_width_pt'];sy=img.height/coord['visual_height_pt']
    comps,binary=detect_components(img,coord['words'],sx,sy,y0_pt,y1_pt)
    if len(comps)<expected_count:
        raise RuntimeError(f'{asset_id}: need {expected_count} visual components, found {len(comps)}')
    chosen=comps[:expected_count]
    px0=min(c['x'] for c in chosen);py0=min(c['y'] for c in chosen)
    px1=max(c['x']+c['w'] for c in chosen);py1=max(c['y']+c['h'] for c in chosen)
    bbox=[px0/sx,py0/sy,px1/sx,py1/sy]

    # Restore only compact labels belonging to the diagram; do not pull prose into the crop.
    labels=[]
    for w in coord['words']:
        cy=(w['y0']+w['y1'])/2
        if y0_pt<=cy<=y1_pt and is_diagram_label(w['text']) and near(w,bbox,16): labels.append(w)
    if labels:
        bbox=[min(bbox[0],min(w['x0'] for w in labels)),min(bbox[1],min(w['y0'] for w in labels)),max(bbox[2],max(w['x1'] for w in labels)),max(bbox[3],max(w['y1'] for w in labels))]

    # Generous four-edge margin, hard-capped inside the official example segment.
    pad=12
    bbox=[max(18,bbox[0]-pad),max(y0_pt,bbox[1]-pad),min(coord['visual_width_pt']-18,bbox[2]+pad),min(y1_pt,bbox[3]+pad)]
    crop_px=[max(0,int(bbox[0]*sx)),max(0,int(bbox[1]*sy)),min(img.width,int(np.ceil(bbox[2]*sx))),min(img.height,int(np.ceil(bbox[3]*sy)))]
    crop=img.crop(tuple(crop_px))

    # Four-edge proof uses the non-text geometry mask.
    local=binary[crop_px[1]:crop_px[3],crop_px[0]:crop_px[2]]>0
    edge=min(5,max(1,min(local.shape)//4))
    edge_ink=int(local[:edge,:].sum()+local[-edge:,:].sum()+local[:,:edge].sum()+local[:,-edge:].sum()) if local.size else 999999
    if edge_ink>12: errors.append(f'{asset_id}: non-text geometry touches crop edge ({edge_ink})')

    path=ASSETS/f'{asset_id}.webp';crop.save(path,'WEBP',lossless=True,method=6);blob=path.read_bytes()
    included=[w['text'] for w in coord['words'] if not (w['x1']<bbox[0] or w['x0']>bbox[2] or w['y1']<bbox[1] or w['y0']>bbox[3])]
    prose=[x for x in included if len(x.strip('.,:;()'))>14]
    if prose: errors.append(f'{asset_id}: crop contains likely prose tokens {prose[:5]}')
    rec={
        'id':asset_id,'source_page':page,'official_segment_pt':[y0_pt,y1_pt],
        'expected_components':expected_count,'selected_components':chosen,
        'crop_pt':[round(v,2) for v in bbox],'crop_px':crop_px,'width_px':crop.width,'height_px':crop.height,
        'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),'lossless_webp':True,
        'edge_nontext_ink_px':edge_ink,'included_source_words':included,
        'status':'PASS' if edge_ink<=12 and not prose else 'FAIL'
    }
    records.append(rec)
    preview += [f'===== {asset_id} | page {page} | crop={rec["crop_pt"]} | edgeInk={edge_ink} | {rec["status"]} =====','WORDS: '+' '.join(included),ascii_preview(crop),'']

status='PASS' if not errors and len(records)==25 else 'FAIL'
evidence={'status':status,'source':'official FIPI 2026 base mathematics PDF via canonical printed-page render','method':'exact official-example segment + text-masked component detection + compact diagram labels + 12pt edge padding','asset_count':len(records),'errors':errors,'records':records}
(ROOT/'source-evidence'/'ASSET-CROP-EVIDENCE.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'source-diagnostics'/'ASSET-CROP-PREVIEWS.txt').write_text('\n'.join(preview)+'\n',encoding='utf-8')
print(json.dumps({'status':status,'assets':len(records),'errors':errors},ensure_ascii=False,indent=2))
if status!='PASS':raise SystemExit(1)
