#!/usr/bin/env python3
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
PAGES=ROOT/'source-evidence'/'printed-pages'
COORD=ROOT/'source-diagnostics'/'canonical-coordinates'

SPECS = [
    ("base-03-v1-temperature-chart",10,60,248),("base-03-v3-nickel-chart",11,60,305),
    ("base-07-v1-derivative-graph",14,265,515),("base-07-v2-torque-chart",15,60,390),("base-07-v3-function-graphs",16,60,382),
    ("base-09-v1-lake-plan",18,60,295),("base-09-v2-grid-plan",18,325,420),
    ("base-10-v1-dacha-plan",19,60,145),("base-10-v2-wheel",19,175,245),("base-10-v3-fence-plan",19,275,350),
    ("base-11-v1-tank",20,60,132),("base-11-v2-cut-prism",20,160,228),("base-11-v3-polyhedron",20,256,390),("base-11-v4-boxes",20,419,500),
    ("base-12-v1-triangle-median",21,60,118),("base-12-v2-circle-chord",21,147,205),("base-12-v3-right-triangle",21,235,288),("base-12-v4-midline",21,315,383),
    ("base-13-v1-cone",22,60,120),("base-13-v2-pyramid",22,148,210),("base-13-v3-cylinders",22,239,313),("base-13-v4-spheres",22,341,395),
    ("base-18-v1-number-line",25,60,240),("base-18-v3-number-line",26,60,288),("base-21-v2-rectangle-partition",28,151,226),
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

    # Connect strokes within one diagram, but not whole paragraphs or distant objects.
    closed=cv2.morphologyEx(binary,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_RECT,(3,3)),iterations=1)
    dil=cv2.dilate(closed,cv2.getStructuringElement(cv2.MORPH_RECT,(5,5)),iterations=1)
    n,labels,stats,_=cv2.connectedComponentsWithStats(dil,8)
    comps=[]
    for i in range(1,n):
        x,y,w,h,area=[int(v) for v in stats[i]]
        if area<45 or (w<8 and h<8): continue
        # Source answer lines / separator rules are not diagrams.
        if h<=7 and w>=100: continue
        if w<=7 and h>=100: continue
        comps.append({'x':x,'y':y,'w':w,'h':h,'area':area,'bbox_area':w*h,'aspect':round(w/max(1,h),2)})
    comps.sort(key=lambda c:(c['area'],c['bbox_area']),reverse=True)
    max_area=comps[0]['area'] if comps else 1
    for c in comps:
        c['area_ratio_to_max']=round(c['area']/max_area,3)
    records.append({'id':asset,'page':page,'search_band_pt':[y0_pt,y1_pt],'components':comps[:20]})

(ROOT/'source-diagnostics'/'ASSET-COMPONENTS.json').write_text(json.dumps({'records':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# compact human/model-readable report
lines=[]
for r in records:
    lines.append(f"===== {r['id']} page={r['page']} band={r['search_band_pt']} =====")
    for i,c in enumerate(r['components'][:10],1):
        lines.append(f"{i:02d} x={c['x']} y={c['y']} w={c['w']} h={c['h']} area={c['area']} ratio={c['area_ratio_to_max']} aspect={c['aspect']}")
    lines.append('')
(ROOT/'source-diagnostics'/'ASSET-COMPONENTS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Component diagnostics built for',len(records),'assets')
