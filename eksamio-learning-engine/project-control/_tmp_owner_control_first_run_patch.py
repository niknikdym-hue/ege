#!/usr/bin/env python3
from pathlib import Path
import json


def replace_exact(path: str, old: str, new: str, count: int = 1) -> None:
    p = Path(path)
    text = p.read_text()
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"{path}: expected {count} occurrences, found {actual}: {old[:120]!r}")
    p.write_text(text.replace(old, new))


panel = 'eksamio-learning-engine/project-control/owner-control.html'
replace_exact(
    panel,
    "if(t.owner_gate_required||t.blocker_type)continue;if(['NOT_STARTED','DESIGNED','INTEGRATION_PENDING'].includes(t.status))return t",
    "if(t.owner_gate_required||(t.blocker_type&&t.blocker_type!=='SUBJECT')||t.executor!=='Codex')continue;if(['NOT_STARTED','DESIGNED','INTEGRATION_PENDING','BLOCKED_SUBJECT'].includes(t.status))return t",
)
replace_exact(
    panel,
    "return state.tasks.find(t=>!t.owner_gate_required&&!t.blocker_type&&!['DONE','PUBLIC_LAUNCH_PASS','VISIBLE_TO_LEARNER'].includes(t.status))||null",
    "return state.tasks.find(t=>!t.owner_gate_required&&(!t.blocker_type||t.blocker_type==='SUBJECT')&&t.executor==='Codex'&&!['DONE','PUBLIC_LAUNCH_PASS','VISIBLE_TO_LEARNER'].includes(t.status))||null",
)
replace_exact(
    panel,
    "function selectTask(t){if(!t||t.owner_gate_required||t.blocker_type){return}",
    "function selectTask(t){if(!t||t.owner_gate_required||(t.blocker_type&&t.blocker_type!=='SUBJECT')||t.executor!=='Codex'){return}",
)
replace_exact(
    panel,
    "const runnable=!t.owner_gate_required&&!t.blocker_type&&!['DONE','PUBLIC_LAUNCH_PASS'].includes(t.status)",
    "const runnable=!t.owner_gate_required&&(!t.blocker_type||t.blocker_type==='SUBJECT')&&t.executor==='Codex'&&!['DONE','PUBLIC_LAUNCH_PASS'].includes(t.status)",
)
replace_exact(
    panel,
    "const task=state.tasks.find(t=>t.task_id===state.selectedTaskId);const lines=",
    "const task=state.tasks.find(t=>t.task_id===state.selectedTaskId);if(paid&&(!task||task.owner_gate_required||(task.blocker_type&&task.blocker_type!=='SUBJECT')||task.executor!=='Codex')){alert('Выбранная задача не допускает автономный платный запуск.');return}const lines=",
)

workflow = '.github/workflows/owner-agent-console-control.yml'
replace_exact(
    workflow,
    '      BOARD: eksamio-learning-engine/project-control/operational-board-v1.json',
    '      BOARD: /tmp/owner-control-authority/operational-board-v1.json',
)
checkout = """      - uses: actions/checkout@v5
        with:
          ref: ${{ inputs.base_ref }}
          fetch-depth: 0
"""
authority = """      - name: Checkout Owner Control authority from main
        uses: actions/checkout@v5
        with:
          ref: main
          path: _owner_control_main
          persist-credentials: false
      - name: Snapshot Owner Control authority before target checkout
        shell: bash
        run: |
          set -euo pipefail
          mkdir -p /tmp/owner-control-authority
          cp _owner_control_main/eksamio-learning-engine/project-control/operational-board-v1.json /tmp/owner-control-authority/operational-board-v1.json
          cp _owner_control_main/eksamio-learning-engine/project-control/owner_control_checkpoint.py /tmp/owner-control-authority/owner_control_checkpoint.py
          python3 - <<'PY'
          import json
          from pathlib import Path
          board=json.loads(Path('/tmp/owner-control-authority/operational-board-v1.json').read_text())
          assert board['version']=='operational-board-v1' and len(board['tasks'])==115
          print('OWNER_CONTROL_MAIN_AUTHORITY=PASS')
          PY
          rm -rf _owner_control_main
      - uses: actions/checkout@v5
        with:
          ref: ${{ inputs.base_ref }}
          fetch-depth: 0
"""
replace_exact(workflow, checkout, authority)
replace_exact(
    workflow,
    "          if task.get('owner_gate_required'): raise SystemExit('OWNER_GATE task: paid autonomous development is refused before API call')\n          if task.get('blocker_type'): raise SystemExit(f\"Blocked task ({task['blocker_type']}): resolve blocker before paid API call\")",
    "          if task.get('owner_gate_required'): raise SystemExit('OWNER_GATE task: paid autonomous development is refused before API call')\n          if task.get('executor')!='Codex': raise SystemExit(f\"NON_CODEX_EXECUTOR task ({task.get('executor')}): paid autonomous development is refused before API call\")\n          blocker=task.get('blocker_type')\n          if blocker and blocker!='SUBJECT': raise SystemExit(f\"Blocked task ({blocker}): resolve external/non-subject blocker before paid API call\")",
)
replace_exact(
    workflow,
    "          sys.path.insert(0,'eksamio-learning-engine/project-control')",
    "          sys.path.insert(0,'/tmp/owner-control-authority')",
    count=2,
)

board_path = Path('eksamio-learning-engine/project-control/operational-board-v1.json')
board = json.loads(board_path.read_text())
cp = board['critical_path']
if 'A2.2' not in cp:
    cp.insert(cp.index('A2.1') + 1, 'A2.2')
by = {t['task_id']: t for t in board['tasks']}
ru = by['A2.2']
ru.update({
    'branch': 'brain/sep1-russian-subject-closure',
    'pr': 164,
    'head_sha': 'cb90377c4ebe00e88e22c39824b7c484651ebcc4',
    'ci_evidence': 'PR #164 exact HEAD cb90377c: Russian semantic acceptance progress run 34624858717 SUCCESS; bounded exact-acceptance runs continue; russian_content remains BLOCKED_SUBJECT / NO-GO.',
    'current_action': 'Continue from the exact current canonical remainder on PR #164; one bounded object at a time; preserve false_exact_mastery=0.',
    'next_action': 'Use the current exact remainder and existing canonical owners/evidence; never infer from title/route/keyword/fuzzy/embedding.',
    'last_evidence_timestamp': '2026-09-11',
    'evidence': ['PR #164', 'workflow 34624858717 Russian semantic acceptance progress = SUCCESS'],
})
for task in board['tasks']:
    if task.get('executor') == 'Owner':
        task['owner_gate_required'] = True
board_path.write_text(json.dumps(board, ensure_ascii=False, indent=2) + '\n')

tests = 'eksamio-learning-engine/tests/test_owner_agent_console.py'
replace_exact(
    tests,
    "self.assertEqual(self.board['critical_path'],['A2.1','A5.1','A4.1','A6.3','A8.1','A9.2','A10.1','A11.1','A11.2','A6.1','A12.1','B1'])",
    "self.assertEqual(self.board['critical_path'],['A2.1','A2.2','A5.1','A4.1','A6.3','A8.1','A9.2','A10.1','A11.1','A11.2','A6.1','A12.1','B1'])\n        self.assertTrue(by['A8.1']['owner_gate_required'])\n        self.assertEqual((by['A2.2']['pr'],by['A2.2']['branch']),(164,'brain/sep1-russian-subject-closure'))",
)
replace_exact(
    tests,
    "        self.assertIn('OWNER_GATE task',yml)\n        self.assertIn(\"'/__pycache__/' not in x[3:]\",yml)",
    "        self.assertIn('OWNER_GATE task',yml)\n        self.assertIn('NON_CODEX_EXECUTOR task',yml)\n        self.assertIn('/tmp/owner-control-authority',yml)\n        self.assertIn(\"t.executor==='Codex'\",html)\n        self.assertIn(\"'/__pycache__/' not in x[3:]\",yml)",
)

print('OWNER_CONTROL_FIRST_RUN_PATCH=APPLIED')
