#!/usr/bin/env python3
from __future__ import annotations
import base64, collections, hashlib, io, json, re
from pathlib import Path
import fitz
from PIL import Image, ImageChops

R=Path(__file__).resolve().parent
P='ege-matematika-baza-demoversiya-2023'
SOURCE_SHA='a43815ea02387b0c6df15d474c73e3f51f2ee7b0741d37ed4a6efa76d84371ab'


def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def same(a,b):
    if a.size != b.size: return False
    return ImageChops.difference(a.convert('RGB'),b.convert('RGB')).getbbox() is None

def fresh_printed(pdf:Path):
    doc=fitz.open(pdf); assert len(doc)==13, len(doc)
    out={}
    for i,page in enumerate(doc,1):
        pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
        im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        assert im.width%2==0
        m=im.width//2
        out[i*2-1]=im.crop((0,0,m,im.height)); out[i*2]=im.crop((m,0,im.width,im.height))
    return out

def parse_parts(files,bucket):
    d=collections.defaultdict(list)
    pat=re.compile(rf'{re.escape(bucket)}\["([^"]+)"\].*?\.push\("([A-Za-z0-9+/=]+)"\)')
    for f in files:
        text=f.read_text(encoding='utf-8')
        for m in pat.finditer(text): d[m.group(1)].append(m.group(2))
    return dict(d)

pdf=R/'source-evidence/official-pdf/ege-2023-matematika-baza-demoversiya.pdf'
assert sha(pdf)==SOURCE_SHA
printed=fresh_printed(pdf)
for n in range(4,27):
    e=Image.open(R/f'source-evidence/printed-pages/page-{n:02d}.webp')
    assert same(printed[n],e), f'printed page {n}'

am=json.loads((R/f'{P}-ASSET-MAP.json').read_text(encoding='utf-8'))['assets']
assert len(am)==41
ids=[]
for a in am:
    aid=a['id']; ids.append(aid)
    assert a['source_pdf_sha256']==SOURCE_SHA, aid
    assert 'direct contiguous crop' in a['source_transform'], aid
    box=tuple(map(int,a['crop_px']))
    direct=printed[int(a['printed_page'])].crop(box)
    img=Image.open(R/a['file'])
    assert same(direct,img), aid
    assert sha(R/a['file'])==a['sha256'], aid
assert len(set(ids))==41

t123=sorted(R.glob(f'{P}-T123-*.txt'))
contract=json.loads((R/f'{P}-PACKAGE-CONTRACT.json').read_text(encoding='utf-8'))
assert len(t123)==contract['t123_block_count'], (len(t123),contract['t123_block_count'])
parts=parse_parts(t123,'assetParts')
assert set(parts)==set(ids), (set(ids)-set(parts),set(parts)-set(ids))
byid={a['id']:a for a in am}
for aid in ids:
    raw=base64.b64decode(''.join(parts[aid]),validate=True)
    assert raw==(R/byid[aid]['file']).read_bytes(), aid

refs=parse_parts(t123,'refParts')
assert set(refs)=={'4','5','6','7'}, set(refs)
for n in (4,5,6,7):
    ref=R/f'reference-pages/ref-{n:02d}.webp'
    assert same(printed[n],Image.open(ref)), n
    assert base64.b64decode(''.join(refs[str(n)]),validate=True)==ref.read_bytes(), n

tasks=json.loads((R/'content/tasks.json').read_text(encoding='utf-8'))['tasks']
refs_used=[]
for t in tasks:
    for v in t['variants']: refs_used.extend(v.get('asset_ids',[]))
c=collections.Counter(refs_used)
assert set(c)==set(ids) and all(v==1 for v in c.values()), c

for f in t123+[R/'index.html',R/'script.js',R/'content/tasks.json']:
    s=f.read_text(encoding='utf-8',errors='ignore').lower()
    for marker in ('<svg','<canvas','canvas.getcontext',"getcontext('2d",'getcontext("2d'):
        assert marker not in s, (f.name,marker)
print('VISUAL SOURCE CHAIN PASS')
print(' fresh source-evidence pages: 23/23 exact')
print(' official task visuals: 41/41 exact direct crops')
print(' T123 embedded task visuals: 41/41 byte-identical')
print(' reference pages: 4/4 exact and byte-identical in T123')
print(' reconstructed SVG/Canvas source visuals: 0')
