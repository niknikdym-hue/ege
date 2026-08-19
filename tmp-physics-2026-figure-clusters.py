from pathlib import Path
import fitz, json, math

PDF = Path('ege-fizika-demoversiya-v3-1-fixed/source/ege-2026-fizika-demoversiya.pdf')
OUT = Path('tmp-physics-2026-visual-audit/official-figure-clusters.json')

def dist(a,b):
    dx=max(a.x0-b.x1,b.x0-a.x1,0); dy=max(a.y0-b.y1,b.y0-a.y1,0)
    return math.hypot(dx,dy)

def union(rects):
    r=fitz.Rect(rects[0])
    for x in rects[1:]: r |= fitz.Rect(x)
    return r

def cluster(rects, gap=16):
    groups=[]
    for r in rects:
        hits=[]
        for i,g in enumerate(groups):
            if any(dist(r,x)<=gap for x in g): hits.append(i)
        if not hits: groups.append([r]); continue
        base=hits[0]; groups[base].append(r)
        for i in reversed(hits[1:]): groups[base].extend(groups.pop(i))
    changed=True
    while changed:
        changed=False
        for i in range(len(groups)):
            for j in range(i+1,len(groups)):
                if dist(union(groups[i]),union(groups[j]))<=gap:
                    groups[i].extend(groups.pop(j)); changed=True; break
            if changed: break
    return groups

doc=fitz.open(PDF); rows=[]; logical=1
for physical,page in enumerate(doc,1):
    rot=page.rotation; page.set_rotation(0); pr=page.rect
    halves=[fitz.Rect(pr.x0,pr.y0,pr.x1,pr.y0+pr.height/2),fitz.Rect(pr.x0,pr.y0+pr.height/2,pr.x1,pr.y1)]
    drawings=page.get_drawings()
    dct=page.get_text('dict')
    img_rects=[fitz.Rect(b['bbox']) for b in dct['blocks'] if b.get('type')==1]
    text_blocks=[(fitz.Rect(b['bbox']), ' '.join((span.get('text','') for line in b.get('lines',[]) for span in line.get('spans',[]))).strip()) for b in dct['blocks'] if b.get('type')==0]
    for slot,clip in enumerate(halves,1):
        rects=[]; kinds=[]
        for d in drawings:
            rr=d.get('rect')
            if not rr or not rr.intersects(clip): continue
            inter=rr & clip
            if inter.width>clip.width*.96 and inter.height>clip.height*.96: continue
            if inter.width<2 and inter.height<2: continue
            rects.append(inter); kinds.append('vector')
        for rr in img_rects:
            if rr.intersects(clip): rects.append(rr & clip); kinds.append('image')
        groups=cluster(rects,18)
        clusters=[]
        for g in groups:
            u=union(g)
            if u.get_area()<70: continue
            # nearby text blocks can include labels belonging to the figure.
            expanded=fitz.Rect(u.x0-18,u.y0-18,u.x1+18,u.y1+18)
            nearby=[]
            for tr,txt in text_blocks:
                if txt and tr.intersects(expanded): nearby.append(txt[:180])
            rel=[round(u.x0-clip.x0,2),round(u.y0-clip.y0,2),round(u.x1-clip.x0,2),round(u.y1-clip.y0,2)]
            clusters.append({'bbox_relative':rel,'width':round(u.width,2),'height':round(u.height,2),'area':round(u.get_area(),2),'object_count':len(g),'nearby_text':nearby[:12]})
        clusters.sort(key=lambda x:x['area'], reverse=True)
        rows.append({'logical_page':logical,'physical_page':physical,'slot':slot,'clip':[round(x,2) for x in clip],'clusters':clusters[:20]})
        logical+=1
    page.set_rotation(rot)
OUT.write_text(json.dumps({'authority':'exact byte-locked FIPI 2026 demo PDF','gap_points':18,'pages':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('pages',len(rows),'clusters',sum(len(x['clusters']) for x in rows))
