#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
PAGES = ROOT / "source-evidence" / "printed-pages"
COORD = ROOT / "source-diagnostics" / "canonical-coordinates"
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

# Search bands are in canonical printed-page points. They deliberately end
# before the official answer line / next ИЛИ marker whenever possible.
SPECS = [
    ("base-03-v1-temperature-chart",10,60,248),
    ("base-03-v3-nickel-chart",11,60,305),
    ("base-07-v1-derivative-graph",14,265,515),
    ("base-07-v2-torque-chart",15,60,390),
    ("base-07-v3-function-graphs",16,60,382),
    ("base-09-v1-lake-plan",18,60,295),
    ("base-09-v2-grid-plan",18,325,420),
    ("base-10-v1-dacha-plan",19,60,145),
    ("base-10-v2-wheel",19,175,245),
    ("base-10-v3-fence-plan",19,275,350),
    ("base-11-v1-tank",20,60,132),
    ("base-11-v2-cut-prism",20,160,228),
    ("base-11-v3-polyhedron",20,256,390),
    ("base-11-v4-boxes",20,419,500),
    ("base-12-v1-triangle-median",21,60,118),
    ("base-12-v2-circle-chord",21,147,205),
    ("base-12-v3-right-triangle",21,235,288),
    ("base-12-v4-midline",21,315,383),
    ("base-13-v1-cone",22,60,120),
    ("base-13-v2-pyramid",22,148,210),
    ("base-13-v3-cylinders",22,239,313),
    ("base-13-v4-spheres",22,341,395),
    ("base-18-v1-number-line",25,60,240),
    ("base-18-v3-number-line",26,60,288),
    ("base-21-v2-rectangle-partition",28,151,226),
]


def mask_text(rgb, words, sx, sy):
    masked = rgb.copy()
    for w in words:
        x0=max(0,int(w['x0']*sx)-3); x1=min(masked.shape[1],int(w['x1']*sx)+4)
        y0=max(0,int(w['y0']*sy)-3); y1=min(masked.shape[0],int(w['y1']*sy)+4)
        if x1>x0 and y1>y0:
            masked[y0:y1,x0:x1]=255
    return masked


def ascii_preview(crop, columns=56):
    gray=np.array(crop.convert('L'))
    h,w=gray.shape
    if w==0 or h==0:
        return ''
    rows=max(6,int(h/w*columns*0.45))
    small=crop.convert('L').resize((columns,rows),Image.Resampling.LANCZOS)
    arr=np.array(small)
    chars=[]
    for row in arr:
        chars.append(''.join('█' if v<130 else ('▓' if v<190 else ('·' if v<235 else ' ')) for v in row))
    return '\n'.join(chars)


def intersects_or_near(word, bbox_pt, pad=13):
    x0,y0,x1,y1=bbox_pt
    wx0,wy0,wx1,wy1=word['x0'],word['y0'],word['x1'],word['y1']
    return not (wx1 < x0-pad or wx0 > x1+pad or wy1 < y0-pad or wy0 > y1+pad)

records=[]
preview=[]
for asset_id,page,y0_pt,y1_pt in SPECS:
    img=Image.open(PAGES/f'page-{page:02d}.webp').convert('RGB')
    rgb=np.array(img)
    coord=json.loads((COORD/f'page-{page:02d}.json').read_text(encoding='utf-8'))
    page_w=coord['visual_width_pt']; page_h=coord['visual_height_pt']
    sx=img.width/page_w; sy=img.height/page_h
    words=coord['words']
    masked=mask_text(rgb,words,sx,sy)
    gray=np.mean(masked,axis=2)
    ink=gray<225

    # Keep source geometry only inside the official-example search band.
    band_top=max(0,int(y0_pt*sy)); band_bottom=min(img.height,int(y1_pt*sy))
    band=np.zeros_like(ink)
    band[band_top:band_bottom,:]=ink[band_top:band_bottom,:]

    # Ignore very left task-number gutter and very right page-edge furniture.
    band[:, :int(18*sx)] = False
    band[:, int((page_w-18)*sx):] = False

    ys,xs=np.where(band)
    if not len(xs):
        raise RuntimeError(f'{asset_id}: no non-text source ink found in search band')

    # Initial geometry bounds. Percentile trimming ignores isolated antialias specks,
    # then a second pass below proves that no substantial source geometry was cut.
    gx0=int(np.percentile(xs,0.5)); gx1=int(np.percentile(xs,99.5))+1
    gy0=int(np.percentile(ys,0.5)); gy1=int(np.percentile(ys,99.5))+1

    # Convert to points and attach only source text labels physically adjacent to geometry.
    bbox_pt=[gx0/sx,gy0/sy,gx1/sx,gy1/sy]
    label_words=[w for w in words if y0_pt <= (w['y0']+w['y1'])/2 <= y1_pt and intersects_or_near(w,bbox_pt,13)]
    if label_words:
        bbox_pt[0]=min(bbox_pt[0],min(w['x0'] for w in label_words))
        bbox_pt[1]=min(bbox_pt[1],min(w['y0'] for w in label_words))
        bbox_pt[2]=max(bbox_pt[2],max(w['x1'] for w in label_words))
        bbox_pt[3]=max(bbox_pt[3],max(w['y1'] for w in label_words))

    # Final 8 pt safety padding, capped inside the official-example band.
    bbox_pt=[
        max(18,bbox_pt[0]-8),
        max(y0_pt,bbox_pt[1]-8),
        min(page_w-18,bbox_pt[2]+8),
        min(y1_pt,bbox_pt[3]+8),
    ]
    px=[int(bbox_pt[0]*sx),int(bbox_pt[1]*sy),int(bbox_pt[2]*sx),int(bbox_pt[3]*sy)]
    crop=img.crop(tuple(px))

    # Geometry edge proof: substantial non-text source ink must not touch 5 px border.
    local_mask=band[px[1]:px[3],px[0]:px[2]]
    edge=5
    edge_ink=int(local_mask[:edge,:].sum()+local_mask[-edge:,:].sum()+local_mask[:,:edge].sum()+local_mask[:,-edge:].sum())

    path=ASSETS/f'{asset_id}.webp'
    crop.save(path,'WEBP',lossless=True,method=6)
    blob=path.read_bytes()
    included_words=[w['text'] for w in words if not (w['x1']<bbox_pt[0] or w['x0']>bbox_pt[2] or w['y1']<bbox_pt[1] or w['y0']>bbox_pt[3])]
    rec={
        'id':asset_id,'source_page':page,'search_band_pt':[y0_pt,y1_pt],
        'crop_pt':[round(v,2) for v in bbox_pt],'crop_px':px,
        'width_px':crop.width,'height_px':crop.height,'bytes':len(blob),
        'sha256':hashlib.sha256(blob).hexdigest(),'lossless_webp':True,
        'edge_nontext_ink_px':edge_ink,
        'included_source_words':included_words,
        'status':'CANDIDATE_PENDING_INDEPENDENT_VISUAL_REVIEW'
    }
    records.append(rec)
    preview.append(f'===== {asset_id} | page {page} | crop {rec["crop_pt"]} | edgeInk={edge_ink} =====')
    preview.append('WORDS: '+' '.join(included_words))
    preview.append(ascii_preview(crop))
    preview.append('')

(ROOT/'source-evidence'/'ASSET-CROP-EVIDENCE.json').write_text(json.dumps({
    'source':'official FIPI 2026 base mathematics PDF via canonical printed-page render',
    'asset_count':len(records),'records':records
},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'source-diagnostics'/'ASSET-CROP-PREVIEWS.txt').write_text('\n'.join(preview)+'\n',encoding='utf-8')
assert len(records)==25
print('Built',len(records),'candidate official source crops')
