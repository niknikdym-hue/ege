from pathlib import Path
import fitz, json, math

PDF=Path('ege-fizika-demoversiya-v3-1-fixed/source/ege-2026-fizika-demoversiya.pdf')
OUT=Path('tmp-physics-2026-visual-audit/official-figure-clusters-clean.json')

def dist(a,b):
    dx=max(a.x0-b.x1,b.x0-a.x1,0);dy=max(a.y0-b.y1,b.y0-a.y1,0);return math.hypot(dx,dy)
def uni(rs):
    r=fitz.Rect(rs[0])
    for x in rs[1:]:r|=fitz.Rect(x)
    return r
def groups(rects,gap=4):
    gs=[]
    for r in rects:
        hits=[i for i,g in enumerate(gs) if any(dist(r,x)<=gap for x in g)]
        if not hits:gs.append([r]);continue
        b=hits[0];gs[b].append(r)
        for i in reversed(hits[1:]):gs[b].extend(gs.pop(i))
    changed=True
    while changed:
        changed=False
        for i in range(len(gs)):
            for j in range(i+1,len(gs)):
                if dist(uni(gs[i]),uni(gs[j]))<=gap:
                    gs[i].extend(gs.pop(j));changed=True;break
            if changed:break
    return gs

doc=fitz.open(PDF);rows=[];logical=1
for physical,page in enumerate(doc,1):
    rot=page.rotation;page.set_rotation(0);pr=page.rect
    halves=[fitz.Rect(pr.x0,pr.y0,pr.x1,pr.y0+pr.height/2),fitz.Rect(pr.x0,pr.y0+pr.height/2,pr.x1,pr.y1)]
    drawings=page.get_drawings();dct=page.get_text('dict');imgs=[fitz.Rect(b['bbox']) for b in dct['blocks'] if b.get('type')==1]
    texts=[(fitz.Rect(b['bbox']),' '.join(span.get('text','') for line in b.get('lines',[]) for span in line.get('spans',[])).strip()) for b in dct['blocks'] if b.get('type')==0]
    for slot,clip in enumerate(halves,1):
        rs=[]
        for d in drawings:
            r=d.get('rect')
            if not r or not r.intersects(clip):continue
            x=r&clip
            if x.width>clip.width*.96 and x.height>clip.height*.96:continue
            # Drop long hairlines/separators that glue unrelated visual groups.
            if min(x.width,x.height)<1.2 and max(x.width,x.height)>75:continue
            if x.width<2 and x.height<2:continue
            rs.append(x)
        for r in imgs:
            if r.intersects(clip):rs.append(r&clip)
        cs=[]
        for g in groups(rs,4):
            u=uni(g)
            if u.get_area()<60:continue
            ex=fitz.Rect(u.x0-14,u.y0-14,u.x1+14,u.y1+14);near=[txt[:180] for tr,txt in texts if txt and tr.intersects(ex)]
            cs.append({'bbox_relative':[round(u.x0-clip.x0,2),round(u.y0-clip.y0,2),round(u.x1-clip.x0,2),round(u.y1-clip.y0,2)],'width':round(u.width,2),'height':round(u.height,2),'area':round(u.get_area(),2),'object_count':len(g),'nearby_text':near[:10]})
        cs.sort(key=lambda x:x['area'],reverse=True)
        rows.append({'logical_page':logical,'physical_page':physical,'slot':slot,'clusters':cs[:25]});logical+=1
    page.set_rotation(rot)
OUT.write_text(json.dumps({'authority':'exact byte-locked FIPI 2026 demo PDF','filters':'long hairlines removed; gap 4pt','pages':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('clusters',sum(len(x['clusters']) for x in rows))
