import json, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1] / 'project-control'))
import owner_agent_console as c

class OwnerConsoleTest(unittest.TestCase):
    def setUp(self): self.rows=c.rows()
    def test_a_to_e_unique_and_required_views(self):
        ids=[r['task_id'] for r in self.rows]
        self.assertEqual(len(ids),len(set(ids))); self.assertEqual(set(r['stage'] for r in self.rows),set('ABCDE'))
        b=json.loads((Path(__file__).parents[1]/'project-control/operational-board-v1.json').read_text())
        out=c.render(b,{'facts':{'conflict':True},'corrections':['x']})
        for x in ['Whole Project','Critical Path','Russian Product (A+B)','Visible Product','Owner Gates','Blockers','History','Astra/API-Codex activity','STALE/CONFLICT','NOT_DISPATCHED']: self.assertIn(x,out)
        self.assertIn('A1.1',out); self.assertIn('B1',out); self.assertIn('C1',out); self.assertIn('D1',out); self.assertIn('E1',out)
    def test_safety_semantics(self):
        self.assertTrue(all(not r['visible_to_learner'] for r in self.rows if r['status']=='CODE_READY'))
        rendered=c.render(json.loads((Path(__file__).parents[1]/'project-control/operational-board-v1.json').read_text()), {'unknown_secret':'never-render','facts':{}})
        self.assertNotIn('never-render', rendered)
        self.assertTrue(all(r['owner_gate_required'] for r in self.rows if r['task_id'].startswith('A12.')))

if __name__=='__main__': unittest.main()
