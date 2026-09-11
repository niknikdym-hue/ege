import json, unittest
from pathlib import Path
import sys
ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'project-control'))
import owner_agent_console as c
from owner_control_checkpoint import build_resume_manifest, validate_resume_manifest

class OwnerConsoleTest(unittest.TestCase):
    def setUp(self):
        self.board=json.loads((ROOT/'project-control/operational-board-v1.json').read_text())
        self.rows=c.rows()

    def test_exact_inventory_contract(self):
        self.assertEqual(len(self.rows),115)
        self.assertEqual(len({r['task_id'] for r in self.rows}),115)
        self.assertEqual({s:sum(r['stage']==s for r in self.rows) for s in 'ABCDE'},{'A':74,'B':15,'C':11,'D':8,'E':7})
        fields={'task_id','title','user_visible_outcome','stage','workstream','priority','status','source_status','target_state','dependencies','blocker_type','blocker_detail','branch','pr','head_sha','ci_evidence','visible_to_learner','production_state','executor','owner_gate_required','current_action','next_action','last_evidence_timestamp','evidence'}
        for r in self.rows:
            self.assertTrue(fields <= r.keys())
            self.assertIn(r['status'],c.STATUSES)
            self.assertFalse(r['title'].startswith(r['task_id']))

    def test_semantics_and_ordered_path(self):
        by={r['task_id']:r for r in self.rows}
        self.assertNotEqual(by['A2.1']['status'],'NOT_STARTED')
        self.assertEqual(c.normalize_status('FUTURE'),'NOT_STARTED')
        self.assertEqual(c.normalize_status('PARTIAL / accepted historical assets exist'),'DESIGNED')
        self.assertTrue(all(r['status']==c.normalize_status(r['source_status']) for r in self.rows))
        self.assertEqual((by['A6.1']['status'],by['A6.1']['visible_to_learner']),('VISIBLE_TO_LEARNER',True))
        self.assertEqual(by['B1']['status'],'BLOCKED_SUBJECT')
        for task_id in ('C11','D6','D8','E1','E2','E3','E4','E5','E6','E7'):
            self.assertEqual(by[task_id]['status'],'NOT_STARTED')
        self.assertFalse(by['D1']['visible_to_learner'])
        self.assertFalse(by['D2']['visible_to_learner'])
        self.assertFalse(by['A12.4']['owner_gate_required'])
        self.assertFalse(by['A12.5']['owner_gate_required'])
        self.assertEqual(self.board['critical_path'],['A2.1','A5.1','A4.1','A6.3','A8.1','A9.2','A10.1','A11.1','A11.2','A6.1','A12.1','B1'])
        self.assertLess(sum(r['executor']=='Astra' for r in self.rows),len(self.rows))
        self.assertTrue(all(not r['visible_to_learner'] for r in self.rows if r['status']=='CODE_READY'))

    def test_fixture_views_conflict_and_safety(self):
        fixture=json.loads((ROOT/'project-control/github-fixture.json').read_text())
        out=c.render(ROOT/'project-control/operational-board-v1.json',fixture)
        for x in ['Whole Project','Critical Path','Russian Product (A+B)','Visible Product','Owner Gates','Blockers','History','Astra/API-Codex activity','A1.1','B1','C1','D1','E1','offline PR','checks 1/1 complete','NOT_DISPATCHED']:
            self.assertIn(x,out)
        self.assertNotIn('statusCheckRollup',out)
        self.assertNotIn('__typename',out)
        fixture['facts']['conflict']=True
        self.assertIn('STALE/CONFLICT',c.render(ROOT/'project-control/operational-board-v1.json',fixture))
        fixture['unknown_secret']='never-render'
        self.assertNotIn('never-render',c.render(ROOT/'project-control/operational-board-v1.json',fixture))

    def test_owner_control_panel_and_controller_contract(self):
        repo=ROOT.parent
        panel=ROOT/'project-control/owner-control.html'
        workflow=repo/'.github/workflows/owner-agent-console-control.yml'
        bootstrap=repo/'.github/workflows/api-codex-owner-control-build.yml'
        checkpoint=ROOT/'project-control/owner_control_checkpoint.py'
        self.assertTrue(panel.is_file())
        self.assertTrue(workflow.is_file())
        self.assertTrue(checkpoint.is_file())
        self.assertFalse(bootstrap.exists())
        html=panel.read_text(); yml=workflow.read_text()
        for x in ['Запустить следующую задачу','Пауза после текущего шага','Продолжить','Остановить','Обновить статус','Critical Path','Whole Project','Russian A+B','Visible Product','Owner Gates','Blockers']:
            self.assertIn(x,html)
        self.assertIn('operational-board-v1.json',html)
        self.assertIn('tasks.length!==115',html)
        self.assertIn("expected={A:74,B:15,C:11,D:8,E:7}",html)
        self.assertIn('pulls/${PR_NUMBER}',html)
        self.assertIn('check-runs?per_page=100',html)
        self.assertIn('owner-agent-console-control.yml',html)
        self.assertIn('confirm(',html)
        self.assertNotIn('OPENAI_API_KEY',html)
        self.assertNotIn('GITHUB_TOKEN',html)
        self.assertNotIn('innerHTML',html)
        for x in ['workflow_dispatch:','resume_run_id:','gpt-6-astra','gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol','openai/codex-action@v1','PAUSE_REQUESTED','STOP_REQUESTED','resume-manifest','--draft']:
            self.assertIn(x,yml)
        self.assertNotIn('model: gpt-5.3-codex-spark',yml)
        for bad in ['gh pr merge','markPullRequestReadyForReview','git push origin HEAD:main','deploy-pages']:
            self.assertNotIn(bad,yml)
        self.assertGreaterEqual(yml.count('actions/upload-artifact@v4'),8)
        self.assertIn('task_id is required for start/resume before any paid API call',yml)
        self.assertIn('resume requires exact numeric resume_run_id before any paid API call',yml)
        self.assertIn('Blocked task',yml)
        self.assertIn('OWNER_GATE task',yml)
        self.assertIn("'/__pycache__/' not in x[3:]",yml)

    def test_paid_model_calls_are_structured_fail_closed_and_not_high(self):
        yml=(ROOT.parent/'.github/workflows/owner-agent-console-control.yml').read_text()
        self.assertGreaterEqual(yml.count("'type':'json_schema'"),2)
        self.assertGreaterEqual(yml.count("'strict':True"),2)
        self.assertGreaterEqual(yml.count("body.get('status')!='completed'"),2)
        self.assertGreaterEqual(yml.count('raw provider response persisted; no automatic retry'),2)
        self.assertGreaterEqual(yml.count("'reasoning':{'effort':'medium'}"),2)
        self.assertNotIn("'reasoning':{'effort':'high'}",yml)
        self.assertGreaterEqual(yml.count("'max_output_tokens':12000"),2)
        self.assertIn('/tmp/astra-plan-provider-response.json',yml)
        self.assertIn('/tmp/astra-review-provider-response.json',yml)
        self.assertNotIn('rerun-failed-jobs',yml)
        self.assertNotIn('rerun workflow',yml.lower())

    def test_resume_manifest_prevents_repeating_completed_paid_stages(self):
        request={
            'schema_version':'0.1','repository':'niknikdym-hue/ege','base_ref':'main','base_sha':'abc123',
            'task':{'task_id':'A1.1'},'command':'start','owner':'niknikdym-hue','run_id':'100'
        }
        m1=build_resume_manifest(request,'100','executor')
        self.assertEqual(m1['completed_paid_stages'],['astra_plan'])
        self.assertEqual(validate_resume_manifest(m1,request,repository='niknikdym-hue/ege',source_run_id='100',task_id='A1.1',base_ref='main',base_sha='abc123',owner='niknikdym-hue'),'executor')
        m2=build_resume_manifest(request,'101','acceptance')
        self.assertEqual(m2['completed_paid_stages'],['astra_plan','executor','tests'])
        self.assertEqual(validate_resume_manifest(m2,request,repository='niknikdym-hue/ege',source_run_id='101',task_id='A1.1',base_ref='main',base_sha='abc123',owner='niknikdym-hue'),'acceptance')
        broken=dict(m2); broken['base_sha']='moved'
        with self.assertRaisesRegex(ValueError,'base_sha mismatch'):
            validate_resume_manifest(broken,request,repository='niknikdym-hue/ege',source_run_id='101',task_id='A1.1',base_ref='main',base_sha='abc123',owner='niknikdym-hue')
        broken=dict(m2); broken['completed_paid_stages']=['astra_plan']
        with self.assertRaisesRegex(ValueError,'paid-stage history mismatch'):
            validate_resume_manifest(broken,request,repository='niknikdym-hue/ege',source_run_id='101',task_id='A1.1',base_ref='main',base_sha='abc123',owner='niknikdym-hue')

    def test_resume_workflow_restores_only_proven_checkpoints(self):
        yml=(ROOT.parent/'.github/workflows/owner-agent-console-control.yml').read_text()
        for x in [
            "d['path']=='.github/workflows/owner-agent-console-control.yml'",
            'Missing required resume artifact',
            'validate_resume_manifest',
            "resume_stage=executor",
            "resume_stage=acceptance",
            "need_plan=false",
            "need_executor=false",
            'git apply --binary /tmp/codex-workspace.patch',
            'completed paid stages will not be repeated',
        ]:
            self.assertIn(x,yml)
        self.assertIn("if [ '${{ inputs.command }}' = start ]",yml)
        self.assertIn("steps.route.outputs.need_plan == 'true'",yml)
        self.assertIn("steps.route.outputs.need_executor == 'true'",yml)

if __name__=='__main__':
    unittest.main()
