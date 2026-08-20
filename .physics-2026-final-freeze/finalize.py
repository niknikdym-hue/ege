#!/usr/bin/env python3
from pathlib import Path
import base64,zlib,re,hashlib
ROOT=Path("ege-fizika-demoversiya-v3-1-fixed")
TMP=Path(".physics-2026-final-freeze")
TARGET=38000
HARD_LIMIT=42500
PREFIX='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ЕГЭ Физика 2026 — preview</title></head><body>'
SUFFIX='</body></html>'
EXPECTED={'01': (22991, '6b2a08321bedbe9ea23268f66dc9f0e2e8482476b84e0668b8a95a4bd3ef9947'), '02': (38000, '513e764f8b52f4b049e6197540ca094008257f81b3c3c0242bcbfae652b93434'), '03': (7295, '22e1fea8b6cb08886f55620f7b63a856c07275080d1e16d1640b07c0942cfc27'), '04': (38000, 'b84791c6bd9bc8d449c2b9b9924f68f6101f293663fc86e6098bebddec6a459d'), '05': (38000, 'fd0478384c236dfc4f0955bf833444783a7d55db98991a07faeccccd8eaadc72'), '06': (13130, '2cef46ee30ef8ded1a1d8ecc8c97836cfd68b005669d0078fdc7aae516e5af6b'), '07': (38000, '5f1da29a1561ca417714772ab17c6c538cedfc227413e32c2d87873e006d63bc'), '08': (37999, '921aef11ffb9626658e0ac1403db2f5a77180cbdb4bd52178ccaf695ac9930dc'), '09': (38000, 'bcc8292bbcbcb5607617f84ab238493859124b810c3ed3142f33add5aa76341e'), '10': (15865, 'adc0492be49a72269c4c2b9630990c841f2b09d9512a873d0a3b9fa80cedb826'), '11': (38000, '5570e1954a38c4ee1e6561160e2af45c15d8796f99b63e3bd3f3c51bbac15aab'), '12': (38000, '9ff71ed8661af960e65436d5e26c2ae2717b74b262000779d4d07177af75b9fb'), '13': (38000, 'b8ecfb82404765098f866f794dc451bef2907c45fc8228d4a17178f451d6911b'), '14': (38000, '9a9c4b538ace6e37d86ff979169cc26f44d6c61fe7e3ad9ef20a9047804a23be'), '15': (38000, 'b85a3b35aa56ea5552dcef58ee05ddc14564fbc691392c94c8085820731a8d19'), '16': (18481, '324c39f841732c56c2b876955c239291d54912d6b526c85c659c3a61650d5115'), '17': (35499, 'c3d2e24233759508125c53baef682c5c99b1419cabd869e206c89a4f5b274297')}
EXPECTED_PREVIEW_SHA='d2970d9abd721304fc15e21fabc1cf5973c6661e4ef470c04cbb1b5c6b61c447'

def inflate_file(name):
    return zlib.decompress(base64.b64decode((TMP/name).read_text(encoding="ascii")))

def extract_inner(path,eid):
    s=path.read_text(encoding="utf-8")
    for pat in [rf'^<script type="application/json" id="{re.escape(eid)}">(.*)</script>\s*$',rf'^<script type="application/json" data-ephys-id="{re.escape(eid)}"(?: data-part="\d+")?>(.*)</script>\s*$']:
        m=re.match(pat,s,re.S)
        if m:return m.group(1)
    raise SystemExit(f"cannot parse {path} for {eid}")

def split_inner(inner,eid):
    out=[];pos=0;idx=1
    while pos<len(inner):
        op=f'<script type="application/json" data-ephys-id="{eid}" data-part="{idx:03d}">';cl='</script>\n'
        budget=TARGET-len(op.encode())-len(cl.encode())
        b=inner[pos:].encode('utf-8');take=min(budget,len(b))
        while take>0 and take<len(b) and (b[take]&0xC0)==0x80:take-=1
        chunk=b[:take].decode('utf-8');out.append((op+chunk+cl).encode('utf-8'));pos+=len(chunk);idx+=1
    return out

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    logical=[]
    for num,eid in [(2,'ephys-data-1'),(3,'ephys-data-2'),(4,'ephys-data-3'),(5,'ephys-data-4')]:logical.append((eid,extract_inner(ROOT/f'ege-fizika-demoversiya-T123-{num:02d}.txt',eid)))
    files=[inflate_file('payload01.b64')]
    for eid,inner in logical:files.extend(split_inner(inner,eid))
    files.append(inflate_file('payload17.b64'))
    if len(files)!=17:raise SystemExit(f"expected 17 T123 files, got {len(files)}")
    for i,b in enumerate(files,1):
        k=f'{i:02d}';size,digest=EXPECTED[k]
        if (len(b),sha(b))!=(size,digest):raise SystemExit(f"T123-{k} mismatch size={len(b)} sha={sha(b)} expected={size}/{digest}")
        if len(b)>=HARD_LIMIT:raise SystemExit(f"T123-{k} violates hard limit")
        (ROOT/f'ege-fizika-demoversiya-T123-{k}.txt').write_bytes(b)
    preview=PREFIX.encode()+b''.join(files)+SUFFIX.encode()
    if sha(preview)!=EXPECTED_PREVIEW_SHA:raise SystemExit(f"preview mismatch {sha(preview)}")
    (ROOT/'ege-fizika-demoversiya-PREVIEW.html').write_bytes(preview)
    lines=['EKSAMIO PHYSICS 2026 — T123 MANIFEST','PROFILE_MATH_UI_PARITY=YES','TILDA_INTERNAL_LIMIT_BYTES=42500','TARGET_HEADROOM_BYTES=38000','']
    lines += [f'T123-{i:02d} | {len(b)} bytes | sha256 {sha(b)}' for i,b in enumerate(files,1)]
    lines += ['','TILDA_SIZE_GATE=PASS','TILDA_T123_ATOMIC_GATE=PASS','ORDER=01..17','']
    (ROOT/'ege-fizika-demoversiya-T123-MANIFEST.txt').write_text('\n'.join(lines),encoding='utf-8')
    print('PHYSICS_2026_T123_COUNT=17')
    print('TILDA_SIZE_GATE=PASS')
    print('TILDA_T123_ATOMIC_GATE=PASS')
    print('PROFILE_MATH_UI_PARITY_FILES=PASS_EXACT_HASHES')
    print('PREVIEW_SHA256='+sha(preview))
if __name__=='__main__':main()
