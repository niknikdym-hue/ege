#!/usr/bin/env python3
import csv, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/'content'
parts=[json.loads((CONTENT/x).read_text(encoding='utf-8')) for x in ('tasks-01-07.json','tasks-08-14.json','tasks-15-21.json')]
asset_map=json.loads((ROOT/'ege-matematika-baza-demoversiya-2026-ASSET-MAP.json').read_text(encoding='utf-8'))
assets={x['id']:x for x in asset_map['assets']}
rows=[]
for part in parts:
    for task in part['tasks']:
        for v in task['variants']:
            formula_fields=any(k in v for k in ('formula_latex','left_latex','right_latex'))
            if formula_fields:
                formula=v.get('formula_status','CAPTURED_PENDING_INDEPENDENT_VISUAL_COMPARE')
            else:
                formula='N/A'
            if v.get('asset_id'):
                visual=assets[v['asset_id']]['status']
            elif formula_fields:
                visual='FORMULA_RENDER_PENDING_VISUAL_GATE'
            else:
                visual='N/A'
            rows.append({
                'year':2026,'level':'base','task':task['number'],'variant':v['variant'],
                'source_pdf':'МА-11 ЕГЭ 2026 ДЕМО_базовый.pdf','source_page':v['source_page'],
                'literal_text':'CAPTURED_PENDING_INDEPENDENT_COMPARE',
                'formula':formula,'visual':visual,'control':v['control'],
                'interaction':'NOT_RUN','scorer':'NOT_RUN','state_reload':'NOT_RUN',
                'browser_evidence':'NONE','final_status':'UNVERIFIED'
            })
assert len(rows)==70
path=ROOT/'AUDIT-MATRIX-2026-base.csv'
with path.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
summary={
    'rows':len(rows),'final_pass':sum(r['final_status']=='PASS' for r in rows),
    'unverified':sum(r['final_status']=='UNVERIFIED' for r in rows),
    'visual_pending':sum('PENDING' in r['visual'] for r in rows),
    'interaction_not_run':sum(r['interaction']=='NOT_RUN' for r in rows),
    'status':'AUDIT_IN_PROGRESS'
}
(ROOT/'AUDIT-MATRIX-2026-base-SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
