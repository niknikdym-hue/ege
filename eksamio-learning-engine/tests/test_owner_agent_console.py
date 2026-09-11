import json, unittest
from pathlib import Path
import sys
ROOT=Path(__file__).parents[1]; sys.path.insert(0,str(ROOT/'project-control'))
import owner_agent_console as c

class OwnerConsoleTest(unittest.TestCase):
    def setUp(self):
        self.board=json.loads((ROOT/'project-control/operational-board-v1.json').read_text()); self.rows=c.rows()
    def test_exact_inventory_contract(self):
        self.assertEqual(len(self.rows),115); self.assertEqual(len({r['task_id'] for r in self.rows}),115)
        self.assertEqual({s:sum(r['stage']==s for r in self.rows) for s in 'ABCDE'},{'A':74,'B':15,'C':11,'D':8,'E':7})
        fields={'task_id','title','user_visible_outcome','stage','workstream','priority','status','source_status','target_state','dependencies','blocker_type','blocker_detail','branch','pr','head_sha','ci_evidence','visible_to_learner','production_state','executor','owner_gate_required','current_action','next_action','last_evidence_timestamp','evidence'}
        for r in self.rows: self.assertTrue(fields <= r.keys()); self.assertIn(r['status'],c.STATUSES)
    def test_semantics_and_ordered_path(self):
        by={r['task_id']:r for r in self.rows}; self.assertNotEqual(by['A2.1']['status'],'NOT_STARTED')
        self.assertEqual((by['A6.1']['status'],by['A6.1']['visible_to_learner']),('VISIBLE_TO_LEARNER',True))
        self.assertFalse(by['A12.4']['owner_gate_required']); self.assertFalse(by['A12.5']['owner_gate_required'])
        self.assertEqual(self.board['critical_path'],['A2.1','A5.1','A4.1','A6.3','A8.1','A9.2','A10.1','A11.1','A11.2','A6.1','A12.1','B1'])
        self.assertLess(sum(r['executor']=='Astra' for r in self.rows),len(self.rows))
        self.assertTrue(all(not r['visible_to_learner'] for r in self.rows if r['status']=='CODE_READY'))
    def test_fixture_views_conflict_and_safety(self):
        fixture=json.loads((ROOT/'project-control/github-fixture.json').read_text()); out=c.render(ROOT/'project-control/operational-board-v1.json',fixture)
        for x in ['Whole Project','Critical Path','Russian Product (A+B)','Visible Product','Owner Gates','Blockers','History','Astra/API-Codex activity','A1.1','B1','C1','D1','E1','offline PR','NOT_DISPATCHED']: self.assertIn(x,out)
        fixture['facts']['conflict']=True; self.assertIn('STALE/CONFLICT',c.render(ROOT/'project-control/operational-board-v1.json',fixture))
        fixture['unknown_secret']='never-render'; self.assertNotIn('never-render',c.render(ROOT/'project-control/operational-board-v1.json',fixture))

if __name__=='__main__': unittest.main()
