#!/usr/bin/env python3
# temporary probe trigger 2026-08-19
import json, re, html, glob
from pathlib import Path
from collections import Counter, defaultdict

ROOT=Path(__file__).resolve().parent
TRAINER=ROOT/'russkiy-knigi'/'ege-russkiy-trenazher'

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def one(prefix):
    xs=sorted(ROOT.glob(prefix+'*'))
    if len(xs)!=1:
        raise SystemExit(f'expected one {prefix}*, got {[x.name for x in xs]}')
    return xs[0]

def units_from(path):
    d=load(path)
    return d.get('canonical_units',[])

def absorption_ids(d):
    out=set()
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                kl=k.lower()
                if k in {'inactive_source_id','absorbed_unit_id','absorbed_old_unit_id','inactive_id'}:
                    if isinstance(v,str) and v.startswith('school-'): out.add(v)
                elif 'absorbed' in kl and isinstance(v,list):
                    for item in v:
                        if isinstance(item,str) and item.startswith('school-'): out.add(item)
                        elif isinstance(item,dict):
                            for kk,vv in item.items():
                                kkl=kk.lower()
                                if any(t in kkl for t in ('old','source','inactive')) and isinstance(vv,str) and vv.startswith('school-'):
                                    out.add(vv)
                walk(v)
        elif isinstance(x,list):
            for y in x: walk(y)
    walk(d)
    return out

manifest215=load(ROOT/'215-RUSSIAN-SCHOOL-CANONICAL-BANK-MATERIALIZED-COUNT-5-11-v0.1.json')
active={}; provenance={}
for entry in manifest215['bank_files']:
    p=ROOT/entry['file']
    for u in units_from(p): active[u['unit_id']]=u; provenance[u['unit_id']]=p.name
for u in units_from(ROOT/'217-RUSSIAN-SCHOOL-CANONICAL-BANK-CHUNK33-MATERIALIZED-GAPS-v0.1.json'):
    active[u['unit_id']]=u; provenance[u['unit_id']]='217-RUSSIAN-SCHOOL-CANONICAL-BANK-CHUNK33-MATERIALIZED-GAPS-v0.1.json'
assert len(active)==137, len(active)
active.pop('school-adverb-n-nn-source-word-inheritance',None)
p236=one('236-')
for u in units_from(p236): active[u['unit_id']]=u; provenance[u['unit_id']]=p236.name
assert len(active)==137, len(active)
for n in [245,247,248,249,250,252,253,254,255,256,257,258]:
    p=one(str(n)+'-'); d=load(p)
    for rid in absorption_ids(d): active.pop(rid,None)
    for u in d.get('canonical_units',[]): active[u['unit_id']]=u; provenance[u['unit_id']]=p.name
if len(active)!=179: raise SystemExit(f'179 reconstruction failed: {len(active)}')
p263=one('263-')
for u in units_from(p263): active[u['unit_id']]=u; provenance[u['unit_id']]=p263.name
if len(active)!=185: raise SystemExit(f'185 reconstruction failed: {len(active)}')

cards=[]; sources={}
for p in sorted(TRAINER.glob('ege-russkiy-trenazher-T123-0[2-9].txt')):
    s=p.read_text(encoding='utf-8')
    m=re.search(r'<script[^>]*type="application/json"[^>]*>([\s\S]*?)</script>',s)
    if not m: raise SystemExit('JSON block missing '+p.name)
    d=json.loads(m.group(1)); cards.extend(d.get('cards',[])); sources.update(d.get('sources',{}))
if len(cards)!=174: raise SystemExit(f'trainer card count {len(cards)}')
manifest=load(TRAINER/'BANK-MANIFEST.json')
if manifest.get('cards')!=174: raise SystemExit('manifest count mismatch')
per_task=Counter(int(c['task']) for c in cards)

def plain(s):
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip().lower().replace('ё','е')
card_text={c['id']:plain((c.get('promptHtml') or '')+' '+(sources.get(c.get('sourceKey')) or '')) for c in cards}
cards_by_task=defaultdict(list)
for c in cards: cards_by_task[int(c['task'])].append(c)

def candidate_tasks(uid,u):
    dom=(u.get('domain') or '').lower(); typ=(u.get('unit_type') or '').lower(); label=(u.get('canonical_label') or '').lower(); s=' '.join([uid,dom,typ,label]).lower()
    ts=set()
    if any(x in s for x in ['numeral','comparative','morpholog','government','case-ending']): ts.add(7)
    if any(x in s for x in ['government','agreement','syntactic','syntax']): ts.add(8)
    if 'root' in s and not any(x in s for x in ['consonant','double-consonant']): ts.add(9)
    if any(x in s for x in ['prefix','separating-hard','separating-soft','hard-soft-sign','i-y-after']): ts.add(10)
    if any(x in s for x in ['suffix','final-vowel','o-e-after-sibilants','vowels-after-ts']) and not any(x in s for x in ['participle','gerund']): ts.add(11)
    if any(x in s for x in ['verb-personal','conjugation','participle-vowel','gerund-forming','infinitive-past-nonfinite']): ts.add(12)
    if any(x in s for x in ['school-ne-','school-ni-',' ne ',' ni ','negation']): ts.add(13)
    if any(x in s for x in ['solid-hyphen-separate','solid_separate','solid-hyphen','hyphen','preposition','conjunction','particle','pronoun','pol-polu','compound-noun','compound-adjective','numeral-orthography','adverb-solid']): ts.add(14)
    if any(x in s for x in ['n-nn','nn-','-n-nn','denominal-adjective-n','participle-verbal-adjective-n']): ts.add(15)
    if any(x in s for x in ['homogeneous','generalizing-word','paired-conjunction']): ts.add(16)
    if any(x in s for x in ['isolation','isolat','apposition','gerund','clarifying','joining-construction','obosob','definition']): ts.add(17)
    if any(x in s for x in ['introductory','address','interjection','yes-no','exclamatory-word']): ts.add(18)
    if any(x in s for x in ['ssp-','spp-','bsp-','complex-sentence','subordinate','junction','sentence-connection']): ts.update([19,20])
    if 'punct' in dom or any(x in s for x in ['comma','dash','colon','semicolon','quote','direct-speech','dialogue','sentence-punctuation','introductory','address','homogeneous','apposition','isolation','ssp-','spp-','bsp-']): ts.add(21)
    if 'root' in s and 'consonant' in s: ts.discard(9)
    return sorted(t for t in ts if per_task.get(t,0)>0)

def lexical_terms(u):
    vals=[]
    def walk(x,k=''):
        if isinstance(x,dict):
            for kk,v in x.items():
                kl=kk.lower()
                if any(t in kl for t in ['member','exception','pair_branch','canonical_members','source_member']): vals.append(v)
                walk(v,kk)
        elif isinstance(x,list):
            for y in x: walk(y,k)
    walk(u)
    raw=[]
    def flatten(x):
        if isinstance(x,str): raw.append(x)
        elif isinstance(x,list):
            for y in x: flatten(y)
        elif isinstance(x,dict):
            for y in x.values(): flatten(y)
    for v in vals: flatten(v)
    terms=set()
    for r in raw:
        r=plain(r)
        for z in re.split(r'[—–,;/|()]|\s+[-–—]\s+',r):
            z=z.strip(' .:«»"\'')
            if len(z)>=4 and re.search('[а-я]',z) and len(z.split())<=3: terms.add(z)
    return sorted(terms)

coverage=[]
for uid in sorted(active):
    u=active[uid]; tasks=candidate_tasks(uid,u); terms=lexical_terms(u); direct=[]; hit_terms=set()
    for t in tasks:
        for c in cards_by_task[t]:
            txt=card_text[c['id']]; hits=[term for term in terms if term in txt]
            if hits: direct.append(c['id']); hit_terms.update(hits)
    if not tasks:
        status='NOT_COVERED'; reason='No current EGE trainer route requires this school identity as a target decision.'
    else:
        status='PARTIALLY_COVERED'; reason='Current trainer exposes the identity only inside EGE task-number/composite cards; canonical identity is not tagged or independently diagnosed.'
        if len(terms)==1 and direct:
            status='COVERED'; reason='Narrow lexical identity has direct valid-route card evidence for its sole explicit member.'
    coverage.append({'unit_id':uid,'canonical_label':u.get('canonical_label'),'domain':u.get('domain'),'unit_type':u.get('unit_type'),'provenance_file':provenance.get(uid),'status':status,'trainer_tasks':tasks,'task_card_counts':{str(t):per_task[t] for t in tasks},'direct_card_ids':sorted(set(direct)),'direct_lexical_terms':sorted(hit_terms),'reason':reason})
summary=Counter(x['status'] for x in coverage)
assert sum(summary.values())==185
out={'schema_version':'0.1.0-probe','date':'2026-08-19','status':'PROBE_ONLY_NOT_AUTHORITY','canonical_authority':'266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json','canonical_total':185,'trainer_path':'eksamio-learning-engine/russkiy-knigi/ege-russkiy-trenazher/','trainer_cards_total':174,'trainer_cards_per_task':{str(k):per_task[k] for k in sorted(per_task)},'summary':dict(summary),'coverage':coverage}
(ROOT/'267-RUSSIAN-SCHOOL-TRAINER-COVERAGE-PROBE-v0.1.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'active':len(active),'cards':len(cards),'summary':dict(summary)},ensure_ascii=False))
