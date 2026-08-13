#!/usr/bin/env python3
from pathlib import Path
import json, hashlib
import fitz
from PIL import Image

ROOT=Path(__file__).resolve().parent
PDF=ROOT/'ege-2024-matematika-baza-demoversiya.pdf'
OUT=ROOT/'diagnostic-render-base'
OUT.mkdir(parents=True,exist_ok=True)
for p in OUT.glob('*'):
    if p.is_file(): p.unlink()

doc=fitz.open(PDF)
rows=[]; printed=0
for physical,page in enumerate(doc,1):
    pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
    im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
    mid=im.width//2
    for half,box in [('left',(0,0,mid,im.height)),('right',(mid,0,im.width,im.height))]:
        printed+=1
        crop=im.crop(box)
        out=OUT/f'page-{printed:02d}.webp'
        crop.save(out,'WEBP',quality=94,method=6)
        rows.append({'printed_page':printed,'physical_pdf_page':physical,'half':half,'width':crop.width,'height':crop.height,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
(OUT/'PAGE-MAP.json').write_text(json.dumps({'source':PDF.name,'physical_pages':len(doc),'render_scale':2,'printed_halves':printed,'pages':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'physical_pages':len(doc),'printed_halves':printed,'out':str(OUT)},ensure_ascii=False))
