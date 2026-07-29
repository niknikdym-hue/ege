#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "try{const r1=JSON.parse(document.getElementById('chem-ref-solubility-data').textContent),r2=JSON.parse(document.getElementById('chem-ref-periodic-data').textContent);$('#chem-ref-solubility').src=r1.data;$('#chem-ref-periodic').src=r2.data}catch(e){console.error('Reference assets failed',e)}"
new = "window.addEventListener('DOMContentLoaded',()=>{try{const r1=JSON.parse(document.getElementById('chem-ref-solubility-data').textContent),r2=JSON.parse(document.getElementById('chem-ref-periodic-data').textContent);$('#chem-ref-solubility').src=r1.data;$('#chem-ref-periodic').src=r2.data}catch(e){console.error('Reference assets failed',e)}})"
if old not in text:
    raise SystemExit("reference loader pattern not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("patched reference loading")
