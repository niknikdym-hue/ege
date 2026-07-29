import base64,hashlib,json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P='ege-khimiya-demoversiya'
class ChemistryPackageTests(unittest.TestCase):
 def setUp(self):
  self.tasks=json.loads((ROOT/f'{P}-TASK-MAP.json').read_text(encoding='utf-8'))['tasks']
  self.exam=json.loads((ROOT/f'{P}-EXAM-MAP.json').read_text(encoding='utf-8'))
 def test_structure(self):
  self.assertEqual(self.exam['task_positions'],34);self.assertEqual(self.exam['duration_minutes'],210);self.assertEqual(self.exam['primary_max'],56);self.assertEqual(len(self.tasks),40)
 def test_maxima(self):
  by={}
  for t in self.tasks:by[t['number']]=t['max_score']
  self.assertEqual(sum(by.values()),56);self.assertEqual(sum(by[i] for i in range(1,29)),36);self.assertEqual(sum(by[i] for i in range(29,35)),20)
 def test_official_answers(self):
  exp={1:'12',2:'135',3:'13',4:'34',5:'128',6:'45',7:'2352',8:'4215',9:'34',10:'124',11:'25',12:'15',13:'15',14:'4236',15:'4651',16:'45',17:'123',18:'345',19:['344','234'],20:['321','144'],21:'4321',22:'1222',23:'53',24:['1515','2315'],25:['342','243','313'],26:'25',27:'68,7',28:['2,24','4']}
  got={}
  for t in self.tasks:
   if t['kind']=='short':got.setdefault(t['number'],[]).append(t['answer']['canonical'])
  for n,v in exp.items():self.assertEqual(got[n],v if isinstance(v,list) else [v])
 def test_no_permissive_normalization(self):
  for t in self.tasks:
   if t['kind']=='short':
    norm=t['answer']['normalization'];self.assertFalse(norm['trim']);self.assertFalse(norm['remove_non_digits']);self.assertFalse(norm['remove_punctuation']);self.assertFalse(norm['remove_internal_spaces'])
 def test_embedded_asset_hashes(self):
  for idx,name in [(7,'reference-solubility.webp'),(8,'reference-periodic.webp')]:
   text=(ROOT/f'{P}-T123-{idx:02d}.txt').read_text(encoding='utf-8');payload=json.loads(re.search(r'>(\{.*\})</script>',text).group(1));raw=base64.b64decode(payload['data'].split(',',1)[1]);self.assertEqual(hashlib.sha256(raw).hexdigest(),hashlib.sha256((ROOT/'assets'/name).read_bytes()).hexdigest())
 def test_evergreen_metadata(self):
  self.assertNotIn('2026',(ROOT/f'{P}-SEO.txt').read_text(encoding='utf-8'));self.assertNotIn('2026',(ROOT/f'{P}-HEAD.txt').read_text(encoding='utf-8'))
 def test_acceptance_coverage(self):
  cases=json.loads((ROOT/f'{P}-ACCEPTANCE-CASES.json').read_text(encoding='utf-8'))['cases']
  self.assertGreaterEqual(len(cases),380)
  cats={c['category'] for c in cases}
  for cat in ['negative-leading-space','negative-trailing-space','negative-internal-space','negative-punctuation','negative-foreign-character','negative-missing-symbol','negative-extra-symbol','negative-repeated-symbol','negative-plausible-unofficial','negative-partial-boundary','criterion-special-branch']:
   self.assertIn(cat,cats)
 def test_extended_source_fidelity(self):
  by={t['number']:t for t in self.tasks if t['kind']=='extended'}
  self.assertIn('К полученному при этом раствору добавили раствор сульфита натрия',by[31]['prompt_html'])
  self.assertIn('кат., t°',by[32]['model_answer_html']);self.assertIn('Ni, t°',by[32]['model_answer_html']);self.assertIn('—H<sub>2</sub>O→',by[32]['model_answer_html'])
  self.assertEqual(by[34]['special_assessment_options'][0]['score'],3)
  self.assertIn('снижается только на 1 балл',by[34]['criteria'][2]['text'])
 def test_no_service_text(self):
  joined=''.join((ROOT/f'{P}-T123-{i:02d}.txt').read_text(encoding='utf-8') for i in range(1,9));self.assertNotIn('Локальный пакет проверен',joined);self.assertNotIn('/mnt/data/',joined)
if __name__=='__main__':unittest.main()
