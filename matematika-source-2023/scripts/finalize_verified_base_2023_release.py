#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import os
import zipfile
from pathlib import Path

OUTROOT=Path(os.environ.get('BASE2023_OUTPUT_DIR','/tmp/base2023-release'))
P='ege-matematika-baza-demoversiya-2023'
ROOT=OUTROOT/P
ZIP=OUTROOT/f'{P}-v1.0.zip'
MANIFEST=ROOT/f'{P}-MANIFEST-SHA256.txt'


def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

rows=[]
for f in sorted(p for p in ROOT.rglob('*') if p.is_file()):
    rel=f.relative_to(ROOT).as_posix()
    if rel==MANIFEST.name or rel.startswith('source-diagnostics/'):
        continue
    rows.append(f'{sha(f)}  {rel}')
MANIFEST.write_text('\n'.join(rows)+'\n',encoding='utf-8')

if ZIP.exists(): ZIP.unlink()
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for f in sorted(p for p in ROOT.rglob('*') if p.is_file()):
        z.write(f,f.relative_to(OUTROOT).as_posix())
print(f'FINAL ZIP: {ZIP}')
print(f'SHA256: {sha(ZIP)}')
print(f'BYTES: {ZIP.stat().st_size}')
