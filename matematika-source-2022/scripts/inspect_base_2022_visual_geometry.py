#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import fitz

ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'ege-2022-matematika-baza-demoversiya.pdf'
OUT=Path('/tmp/base2022-source-analysis/VISUAL-GEOMETRY.json')


def tr_rect(rect, matrix):
    r=fitz.Rect(rect)
    pts=[fitz.Point(r.x0,r.y0)*matrix,fitz.Point(r.x1,r.y0)*matrix,fitz.Point(r.x0,r.y1)*matrix,fitz.Point(r.x1,r.y1)*matrix]
    xs=[p.x for p in pts]; ys=[p.y for p in pts]
    return fitz.Rect(min(xs),min(ys),max(xs),max(ys))

def local_rect(vr, visual, mid, half):
    ox=visual.x0 if half=='left' else mid
    return [round(vr.x0-ox,1),round(vr.y0-visual.y0,1),round(vr.x1-ox,1),round(vr.y1-visual.y0,1)]

def near(a,b,pad=5):
    return not (a[2]+pad<b[0] or b[2]+pad<a[0] or a[3]+pad<b[1] or b[3]+pad<a[1])

def union(a,b): return [min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),max(a[3],b[3])]

def clusters(rects):
    work=[r[:] for r in rects if (r[2]-r[0])>1 and (r[3]-r[1])>1]
    changed=True
    while changed:
        changed=False; out=[]
        while work:
            a=work.pop(); merged=False
            for i,b in enumerate(work):
                if near(a,b,7):
                    work[i]=union(a,b); changed=True; merged=True; break
            if not merged: out.append(a)
        work=out
    return sorted(work,key=lambda r:(r[1],r[0]))

doc=fitz.open(PDF)
printed=0; pages=[]
for pi,page in enumerate(doc,1):
    matrix=page.rotation_matrix
    visual=tr_rect(page.mediabox,matrix); mid=(visual.x0+visual.x1)/2
    words_raw=[]
    for w in page.get_text('words',sort=False):
        vr=tr_rect((w[0],w[1],w[2],w[3]),matrix); cx=(vr.x0+vr.x1)/2
        half='left' if cx<mid else 'right'
        words_raw.append((half,w[4],local_rect(vr,visual,mid,half)))
    draw_rects={'left':[],'right':[]}
    for d in page.get_drawings():
        vr=tr_rect(d['rect'],matrix); cx=(vr.x0+vr.x1)/2
        half='left' if cx<mid else 'right'
        # only drawings fully inside one half; cross-spread artifacts are ignored
        if vr.x0 < mid < vr.x1: continue
        draw_rects[half].append(local_rect(vr,visual,mid,half))
    img_rects={'left':[],'right':[]}
    for im in page.get_image_info(xrefs=True):
        vr=tr_rect(im['bbox'],matrix); cx=(vr.x0+vr.x1)/2
        half='left' if cx<mid else 'right'
        if vr.x0 < mid < vr.x1: continue
        img_rects[half].append(local_rect(vr,visual,mid,half))
    for half in ('left','right'):
        ws=[(t,r) for h,t,r in words_raw if h==half]
        if not ws: continue
        printed+=1
        task_marks=[]
        for t,r in ws:
            if t.isdigit() and 1<=int(t)<=21 and r[0]<100:
                task_marks.append({'task':int(t),'rect':r})
        or_marks=[r for t,r in ws if t=='ИЛИ']
        # expose label-bearing words useful for crop verification
        keywords=[]
        wanted={'Амур','Вилюй','Волга','Енисей','Иртыш','Лена','Обь','Тунгуска','февраля','A','B','C','D','x','y','0','1','2','3','4','5','6','7','8','9','10'}
        for t,r in ws:
            if t in wanted: keywords.append({'text':t,'rect':r})
        pages.append({
            'printed_page':printed,'physical_pdf_page':pi,'half':half,
            'task_marks':task_marks,'or_marks':or_marks,
            'drawing_clusters':clusters(draw_rects[half]),
            'image_rects':sorted(img_rects[half],key=lambda r:(r[1],r[0])),
            'keywords':keywords,
        })
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'source':PDF.name,'pages':pages},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('VISUAL GEOMETRY pages',len(pages),'->',OUT)
