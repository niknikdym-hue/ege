#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "source-evidence" / "printed-pages"
COORD = ROOT / "source-diagnostics" / "canonical-coordinates"
COMPONENTS = ROOT / "source-diagnostics" / "ASSET-COMPONENTS.json"
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

# Search bands are retained as a second guard against neighbouring official examples.
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

# 1-based component numbers from ASSET-COMPONENTS.txt.  Most official drawings are
# one connected component after masking text.  Explicit multi-component selections
# are recorded here rather than inferred by a changing heuristic.
SELECT = {
    "base-07-v3-function-graphs": list(range(1, 9)),
    "base-10-v3-fence-plan": [1, 2, 3],
    "base-13-v3-cylinders": [1, 2],
    "base-13-v4-spheres": [1, 2],
}

component_data = json.loads(COMPONENTS.read_text(encoding="utf-8"))
component_by_id = {r["id"]: r for r in component_data["records"]}


def intersects_or_near(word, bbox_pt, pad=14):
    x0,y0,x1,y1=bbox_pt
    wx0,wy0,wx1,wy1=word["x0"],word["y0"],word["x1"],word["y1"]
    return not (wx1 < x0-pad or wx0 > x1+pad or wy1 < y0-pad or wy0 > y1+pad)


def mask_text(rgb, words, sx, sy):
    out=rgb.copy()
    for w in words:
        x0=max(0,int(w["x0"]*sx)-4); x1=min(out.shape[1],int(w["x1"]*sx)+5)
        y0=max(0,int(w["y0"]*sy)-4); y1=min(out.shape[0],int(w["y1"]*sy)+5)
        if x1>x0 and y1>y0:
            out[y0:y1,x0:x1]=255
    return out


def ascii_preview(crop, columns=56):
    if crop.width == 0 or crop.height == 0:
        return ""
    rows=max(6,int(crop.height/crop.width*columns*0.45))
    small=np.array(crop.convert("L").resize((columns,rows),Image.Resampling.LANCZOS))
    result=[]
    for row in small:
        result.append("".join("█" if v<130 else ("▓" if v<190 else ("·" if v<235 else " ")) for v in row))
    return "\n".join(result)


records=[]
preview=[]
for asset_id,page,y0_pt,y1_pt in SPECS:
    img=Image.open(PAGES/f"page-{page:02d}.webp").convert("RGB")
    coord=json.loads((COORD/f"page-{page:02d}.json").read_text(encoding="utf-8"))
    sx=img.width/coord["visual_width_pt"]
    sy=img.height/coord["visual_height_pt"]
    comps=component_by_id[asset_id]["components"]
    indices=SELECT.get(asset_id,[1])
    chosen=[]
    for idx in indices:
        if idx < 1 or idx > len(comps):
            raise RuntimeError(f"{asset_id}: component {idx} unavailable")
        chosen.append(comps[idx-1])

    # ASSET-COMPONENTS coordinates are pixel coordinates on the same canonical
    # printed-page render as img.
    px0=min(c["x"] for c in chosen)
    py0=min(c["y"] for c in chosen)
    px1=max(c["x"]+c["w"] for c in chosen)
    py1=max(c["y"]+c["h"] for c in chosen)
    bbox_pt=[px0/sx,py0/sy,px1/sx,py1/sy]

    # Attach only labels physically adjacent to the chosen official geometry.
    adjacent=[]
    for w in coord["words"]:
        cy=(w["y0"]+w["y1"])/2
        if y0_pt <= cy <= y1_pt and intersects_or_near(w,bbox_pt,14):
            adjacent.append(w)
    if adjacent:
        bbox_pt=[
            min(bbox_pt[0],min(w["x0"] for w in adjacent)),
            min(bbox_pt[1],min(w["y0"] for w in adjacent)),
            max(bbox_pt[2],max(w["x1"] for w in adjacent)),
            max(bbox_pt[3],max(w["y1"] for w in adjacent)),
        ]

    # 8pt four-edge safety margin, still hard-capped inside this official example.
    bbox_pt=[
        max(18,bbox_pt[0]-8),
        max(y0_pt,bbox_pt[1]-8),
        min(coord["visual_width_pt"]-18,bbox_pt[2]+8),
        min(y1_pt,bbox_pt[3]+8),
    ]
    crop_px=[
        max(0,int(bbox_pt[0]*sx)),
        max(0,int(bbox_pt[1]*sy)),
        min(img.width,int(np.ceil(bbox_pt[2]*sx))),
        min(img.height,int(np.ceil(bbox_pt[3]*sy))),
    ]
    crop=img.crop(tuple(crop_px))

    # Prove that substantial NON-TEXT source geometry does not touch the crop edge.
    rgb=np.array(img)
    masked=mask_text(rgb,coord["words"],sx,sy)
    gray=np.mean(masked,axis=2)
    ink=gray<225
    local=ink[crop_px[1]:crop_px[3],crop_px[0]:crop_px[2]]
    edge=min(5,max(1,min(local.shape)//4))
    edge_ink=int(local[:edge,:].sum()+local[-edge:,:].sum()+local[:,:edge].sum()+local[:,-edge:].sum()) if local.size else 999999

    path=ASSETS/f"{asset_id}.webp"
    crop.save(path,"WEBP",lossless=True,method=6)
    blob=path.read_bytes()
    included=[w["text"] for w in coord["words"] if not (
        w["x1"]<bbox_pt[0] or w["x0"]>bbox_pt[2] or w["y1"]<bbox_pt[1] or w["y0"]>bbox_pt[3]
    )]
    rec={
        "id":asset_id,"source_page":page,"search_band_pt":[y0_pt,y1_pt],
        "selected_components":indices,"component_bounds_px":[px0,py0,px1,py1],
        "crop_pt":[round(v,2) for v in bbox_pt],"crop_px":crop_px,
        "width_px":crop.width,"height_px":crop.height,"bytes":len(blob),
        "sha256":hashlib.sha256(blob).hexdigest(),"lossless_webp":True,
        "edge_nontext_ink_px":edge_ink,"included_source_words":included,
        "status":"COMPONENT_CROP_PENDING_INDEPENDENT_VISUAL_REVIEW"
    }
    records.append(rec)
    preview += [
        f"===== {asset_id} | page {page} | components={indices} | crop={rec['crop_pt']} | edgeInk={edge_ink} =====",
        "WORDS: "+" ".join(included),ascii_preview(crop),""
    ]

(ROOT/"source-evidence"/"ASSET-CROP-EVIDENCE.json").write_text(json.dumps({
    "source":"official FIPI 2026 base mathematics PDF via canonical printed-page render",
    "method":"explicit connected-component selection + adjacent source labels + 8pt four-edge padding",
    "asset_count":len(records),"records":records
},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(ROOT/"source-diagnostics"/"ASSET-CROP-PREVIEWS.txt").write_text("\n".join(preview)+"\n",encoding="utf-8")
assert len(records)==25
print("Built",len(records),"component-based official source crops")
