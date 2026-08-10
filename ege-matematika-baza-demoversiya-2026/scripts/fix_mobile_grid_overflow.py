#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'templates'/'T123-shell.html'
s=p.read_text(encoding='utf-8')
repls={
'.mb-wrap{max-width:1180px;margin:0 auto}':'.mb-wrap{max-width:1180px;min-width:0;margin:0 auto}',
'.mb-layout{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:18px;align-items:start}':'.mb-layout{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:18px;align-items:start;min-width:0}',
'.mb-card{border-radius:22px;padding:26px}':'.mb-card{border-radius:22px;padding:26px;min-width:0}',
'.mb-task-body{font-size:17px}':'.mb-task-body{font-size:17px;min-width:0}',
'.mb-table-wrap{overflow-x:auto;margin:16px 0;border:1px solid var(--mb-line);border-radius:14px}':'.mb-table-wrap{max-width:100%;min-width:0;overflow-x:auto;margin:16px 0;border:1px solid var(--mb-line);border-radius:14px}',
'.mb-answerbox{margin-top:24px;padding-top:20px;border-top:1px solid var(--mb-line)}':'.mb-answerbox{margin-top:24px;padding-top:20px;border-top:1px solid var(--mb-line);min-width:0}',
'.mb-match{display:grid;gap:10px;margin:14px 0}':'.mb-match{display:grid;gap:10px;margin:14px 0;min-width:0}',
'.mb-match-row{display:grid;grid-template-columns:minmax(0,1fr) minmax(180px,.7fr);gap:12px;align-items:center;border:1px solid var(--mb-line);border-radius:14px;padding:12px;background:#fff}':'.mb-match-row{display:grid;grid-template-columns:minmax(0,1fr) minmax(180px,.7fr);gap:12px;align-items:center;border:1px solid var(--mb-line);border-radius:14px;padding:12px;background:#fff;min-width:0}'
}
for old,new in repls.items():
    if old not in s: raise SystemExit(f'CSS target not found: {old[:50]}')
    s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('mobile grid/table overflow constraints applied')
