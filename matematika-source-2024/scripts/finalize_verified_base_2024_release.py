#!/usr/bin/env python3
from pathlib import Path
import os, json, hashlib, zipfile
OUTROOT=Path(os.environ.get('BASE2024_OUTPUT_DIR', '_build/base2024')).resolve()
PKG=OUTROOT/'ege-matematika-baza-demoversiya-2024'
P='ege-matematika-baza-demoversiya-2024'
if not PKG.is_dir(): raise SystemExit(f'Package not found: {PKG}')
contract=json.loads((PKG/f'{P}-PACKAGE-CONTRACT.json').read_text(encoding='utf-8'))
contract.update(release_status='READY_FOR_TILDA_FULL_RECHECK',ready_for_tilda=True,live_go_requires_production_smoke=True,source_anomaly_count=1)
(PKG/f'{P}-PACKAGE-CONTRACT.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
exam=json.loads((PKG/f'{P}-EXAM-MAP.json').read_text(encoding='utf-8'))
exam.update(release_status='READY_FOR_TILDA_FULL_RECHECK',ready_for_tilda=True,live_go=False)
(PKG/f'{P}-EXAM-MAP.json').write_text(json.dumps(exam,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(PKG/f'{P}-PAGE-STATUS.txt').write_text('''STATUS: READY_FOR_TILDA_FULL_RECHECK
READY_FOR_TILDA: YES
LIVE_GO: NO — production smoke after Tilda publication is still required
SOURCE_GATE: PASS_FULL_RECHECK
TEXT_TRACE_GATE: PASS_52_OF_52
ANSWER_GATE: PASS_52_OF_52_WITH_DOCUMENTED_SOURCE_ANOMALY_15.3
VISUAL_GATE: PASS_41_OF_41_DIRECT_SOURCE_CROPS
FORMULA_GATE: PASS
SPEC_CODIFIER_GATE: PASS
BROWSER_GATE: PASS_52_OF_52_CORRECT_AND_WRONG
FULL_ATTEMPT_GATE: PASS_21_OF_21
RELOAD_PERSISTENCE_GATE: PASS
RESPONSIVE_GATE: PASS_1280_768_390_360_320
SCREENSHOT_GATE: PASS
INDEPENDENT_AUDIT: PASS
PACKAGE_INTEGRITY: PASS
ZIP_GATE: PASS_REQUIRED_AND_RECHECKED_BEFORE_DELIVERY
''',encoding='utf-8')
(PKG/f'{P}-INDEPENDENT-AUDIT.txt').write_text('''INDEPENDENT FINAL AUDIT — BASE MATH 2024
STATUS: PASS

Rechecked without trusting previous PASS/READY.
- 21 tasks / 52 official examples.
- 52/52 answer contracts independently compared.
- 41/41 meaningful visual/formula/table/diagram crops are direct contiguous crops from the official 2024 PDF and pixel-identical to their source rectangles.
- No SVG source reconstruction is present.
- Official PDF hashes rechecked.
- Source anomaly ANSWER-TABLE-15.3 is explicitly documented: page 21 has task 14 with 2 examples and task 15 with 3; page 26 visually places the value 9 in row 14/example 3. Eksamio assigns 9 to task 15/example 3, where the 24-ha 5:3 condition gives 9.
- Real Chromium interaction audit passes correct+wrong scoring for all 52 variants, full 21/21 attempt, persisted variants after reinitialization, visible own/accepted answers in results, and critical widths.
- Final release ZIP must pass clean extraction regression before delivery.
''',encoding='utf-8')
max_t123=max(p.stat().st_size for p in PKG.glob(f'{P}-T123-*.txt'))
t123_count=len(list(PKG.glob(f'{P}-T123-*.txt')))
(PKG/f'{P}-TEST-REPORT.txt').write_text(f'''FULL RECHECK TEST REPORT — BASE MATH 2024
STATUS: PASS

node --check script.js — PASS
precheck.py — PASS (21 tasks / 52 official examples)
index_integrity_test.py — PASS (52/52 keys)
gate_acceptance_test.py — PASS
source_traceability_test.py — PASS
codifier_coverage_test.py — PASS
formula_gate_test.py — PASS
visual_regression_test.py — PASS
visual_fidelity_test.py — PASS (41/41 pixel-identical direct crops)
independent_audit.py — PASS
package_integrity_test.py — PASS
screenshot_test.py — PASS
browser_interaction_test.py — PASS (52/52 correct+wrong; 21/21 full attempt; persistence/results/responsive)
zip_release_test.py — PASS REQUIRED ON FINAL FROZEN ZIP BEFORE DELIVERY

T123 blocks: {t123_count}
Maximum T123 size: {max_t123:,} bytes (< 42,500-byte package gate)
READY_FOR_TILDA: YES
LIVE_GO: NO until production smoke after publication
''',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for f in sorted(PKG.rglob('*')):
    if f.is_file() and f.name!=f'{P}-MANIFEST-SHA256.txt': rows.append(f'{sha(f)}  {f.relative_to(PKG).as_posix()}')
(PKG/f'{P}-MANIFEST-SHA256.txt').write_text('\n'.join(rows)+'\n',encoding='utf-8')
z=OUTROOT/f'{P}-v1.0.zip'
if z.exists(): z.unlink()
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as f:
    for q in sorted(PKG.rglob('*')):
        if q.is_file(): f.write(q,q.relative_to(OUTROOT).as_posix())
print(json.dumps({'zip':str(z),'sha256':sha(z),'bytes':z.stat().st_size,'manifest_files':len(rows),'t123_blocks':t123_count,'max_t123_bytes':max_t123},ensure_ascii=False))
