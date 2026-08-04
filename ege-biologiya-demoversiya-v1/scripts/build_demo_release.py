#!/usr/bin/env python3
from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1];out=root.parent/'ege-biologiya-demoversiya-v1.0.2.zip'
if out.exists():out.unlink()
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in sorted(root.rglob('*')):
  if f.is_file() and '__pycache__' not in f.parts and 'evidence' not in f.parts:z.write(f,Path(root.name)/f.relative_to(root))
print(out)
