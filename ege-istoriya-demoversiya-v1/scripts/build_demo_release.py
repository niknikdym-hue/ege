#!/usr/bin/env python3
from pathlib import Path
import hashlib,zipfile
root=Path(__file__).resolve().parents[1]
out=root.parent/"ege-istoriya-demoversiya-v1.0.1.zip"
with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for f in sorted(root.rglob("*")):
        if f.is_file(): z.write(f,Path(root.name)/f.relative_to(root))
print(out)
print(hashlib.sha256(out.read_bytes()).hexdigest())
