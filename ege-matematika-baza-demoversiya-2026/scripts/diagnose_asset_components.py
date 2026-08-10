#!/usr/bin/env python3
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
PAGES=ROOT/'source-evidence'/'printed-pages'
COORD=ROOT/'source-diagnostics'/'canonical-coordinates'

# Exact official-example bands derived from CANONICAL-SOURCE-MARKERS.txt.
# Each band starts after TASK_NUMBER/ИЛИ and ends before its own Ответ: line.
SPECS = [
    ("base-03-v1-temperature-chart",10,74,270),("base-03-v3-nickel-chart",11,71,309),
    ("base-07-v1-derivative-graph",14,277,522),("base-07-v2-torque-chart",15,72,397),("base-07-v3-function-graphs",16,71,388),
    ("base-09-v1-lake-plan",18,77,300),("base-09-v2-grid-plan",18,337,427),
    ("base-10-v1-dacha-plan",19,73,148),("base-10-v2-wheel",19,185,249),("base-10-v3-fence-plan",19,285,356),
    ("base-11-v1-tank",20,73,136),("base-11-v2-cut-prism",20,172,232),("base-11-v3-polyhedron",20,268,395),("base-11-v4-boxes",20,431,506),
    ("base-12-v1-triangle-median",21,73,120),("base-12-v2-circle-chord",21,159,209),("base-12-v3-right-triangle",21,247,291),("base-12-v4-midline",21,327,387),
    ("base-13-v1-cone",22,76,124),("base-13-v2-pyramid",22,159,215),("base-13-v3-cylinders",22,251,317),("base-13-v4-spheres",22,353,400),
    ("base-18-v1-number-line",25,73,245),("base-18-v3-number-line",26,71,294),("base-21-v2-rectangle-partition",28,163,229),
]

def mask_text(rgb,words,sx,sy):
    out=rgb.copy()
    for w in words:
        x0=max(0,int(w['x0']*sx)-4);x1=min(out.shape[1],int(w['x1']*sx)+5)
        y0=max(0,int(w['y0']*sy)-4);y1=min(out.shape[0],int(w['y1']*sy)+5)
        out[y0:y1,x0:x1]=255
    return out

records=[]
for asset,page,y0_pt,y1_pt in SPECS:
    img=Image.open(PAGES/f'page-{page:02d}.webp').convert('RGB')
    rgb=np.array(img)
    coord=json.loads((COORD/f'page-{page:02d}.json').read_text(encoding='utf-8'))
    sx=img.width/coord['visual_width_pt']; sy=img.height/coord['visual_height_pt']
    masked=mask_text(rgb,coord['words'],sx,sy)
    gray=cv2.cvtColor(masked,cv2.COLOR_RGB2GRAY)
    binary=np.zeros_like(gray,dtype=np.uint8)
    top=int(y0_pt*sy);bottom=int(y1_pt*sy)
    binary[top:bottom,:]=(gray[top:bottom,:]<225).astype(np.uint8)*255
    binary[:,:int(18*sx)]=0; binary[:,int((coord['visual_width_pt']-18)*sx):]=0

    closed=cv2.morphologyEx(binary,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_RECT,(3,3)),iterations=1)
    dil=cv2.dilate(closed,cv2.getStructuringElement(cv2.MORPH_RECT,(5,5)),iterations=1)
    n,labels,stats,_=cv2.connectedComponentsWithStats(dil,8)
    comps=[]
    for i in range(1,n):
        x,y,w,h,area=[int(v) for v in stats[i]]
        if area<45 or (w<8 and h<8): continue
        if h<=7 and w>=100: continue
        if w<=7 and h>=100: continue
        comps.append({'x':x,'y':y,'w':w,'h':h,'area':area,'bbox_area':w*h,'aspect':round(w/max(1,h),2)})
    comps.sort(key=lambda c:(c['area'],c['bbox_area']),reverse=True)
    max_area=comps[0]['area'] if comps else 1
    for c in comps:
        c['area_ratio_to_max']=round(c['area']/max_area,3)
    records.append({'id':asset,'page':page,'search_band_pt':[y0_pt,y1_pt],'components':comps[:20]})

(ROOT/'source-diagnostics'/'ASSET-COMPONENTS.json').write_text(json.dumps({'records':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=[]
for r in records:
    lines.append(f"===== {r['id']} page={r['page']} band={r['search_band_pt']} =====")
    for i,c in enumerate(r['components'][:10],1):
        lines.append(f"{i:02d} x={c['x']} y={c['y']} w={c['w']} h={c['h']} area={c['area']} ratio={c['area_ratio_to_max']} aspect={c['aspect']}")
    lines.append('')
(ROOT/'source-diagnostics'/'ASSET-COMPONENTS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Component diagnostics built for',len(records),'assets')
