#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

DRAFT_BRANCH = "const BRANCH='codex/owner-agent-control-page-v1-api';"
MAIN_BRANCH = "const BRANCH='main';"
BOOT_MARKER = "async function boot(){"

OVERRIDE = r"""
// Deployed Owner Control binding. The static page is built from one exact main SHA.
loadGithubFacts=async function(){
  try{
    const main=await fetchJson(`${API}/branches/main`);
    state.mainSha=main.commit.sha;
    state.prHead=state.mainSha;
    $('mainSha').textContent=state.mainSha;
    $('prSha').textContent=state.mainSha;
    try{
      const cr=await fetchJson(`${API}/commits/${state.mainSha}/check-runs?per_page=100`);
      const checks=cr.check_runs||[];
      const finished=checks.filter(c=>c.status==='completed');
      const failed=finished.filter(c=>!['success','neutral','skipped'].includes(c.conclusion));
      state.checks=checks.length===0?'no checks reported':failed.length?`${failed.length} failing / ${checks.length}`:`${finished.length}/${checks.length} complete`;
      $('checks').textContent=state.checks;
    }catch(_err){$('checks').textContent='unavailable'}
    $('syncTime').textContent=new Date().toLocaleString('ru-RU');
    recomputeTruth();
    loadActivity();
  }catch(err){
    $('mainSha').textContent='unavailable';
    $('prSha').textContent='unavailable';
    setTruth('STALE/UNVERIFIED','warn');
    showError(`GitHub main недоступен: ${err.message}`);
  }
};
recomputeTruth=function(){
  if(!state.board)return;
  if(state.boardSource!=='LIVE_BRANCH'){setTruth('STALE/CACHED','warn');return}
  if(!state.mainSha){setTruth('STALE/UNVERIFIED','warn');return}
  if(state.mainSha!==DEPLOYED_MAIN){setTruth('STALE/CONFLICT','bad');return}
  setTruth('SOURCE OF TRUTH OK','ok');
};
"""


def build(source: Path, destination: Path, deployed_main: str) -> None:
    html = source.read_text()
    if html.count(DRAFT_BRANCH) != 1:
        raise SystemExit('expected exactly one Draft branch binding in source HTML')
    if html.count(BOOT_MARKER) != 1:
        raise SystemExit('expected exactly one boot marker in source HTML')
    if len(deployed_main) != 40 or any(ch not in '0123456789abcdef' for ch in deployed_main.lower()):
        raise SystemExit('deployed main must be an exact 40-character commit SHA')

    html = html.replace(
        DRAFT_BRANCH,
        MAIN_BRANCH + "\nconst DEPLOYED_MAIN='" + deployed_main + "';",
        1,
    )
    html = html.replace('<b>PR #193:</b>', '<b>Controller main:</b>', 1)
    html = html.replace(BOOT_MARKER, OVERRIDE + '\n' + BOOT_MARKER, 1)

    required = [
        MAIN_BRANCH,
        "const DEPLOYED_MAIN='" + deployed_main + "';",
        'Запустить следующую задачу',
        'Пауза после текущего шага',
        'Продолжить',
        'Остановить',
        'Обновить статус',
        'Critical Path',
        'Whole Project',
        'Russian A+B',
        'Visible Product',
        'Owner Gates',
        'Blockers',
        'SOURCE OF TRUTH OK',
    ]
    for token in required:
        if token not in html:
            raise SystemExit(f'missing deployed panel invariant: {token}')
    for forbidden in [
        'codex/owner-agent-control-page-v1-api',
        'OPENAI_API_KEY',
        'GITHUB_TOKEN',
    ]:
        if forbidden in html:
            raise SystemExit(f'forbidden deployed panel token: {forbidden}')

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True)
    p.add_argument('--destination', required=True)
    p.add_argument('--main-sha', required=True)
    args = p.parse_args()
    build(Path(args.source), Path(args.destination), args.main_sha.lower())
    print('OWNER_CONTROL_STATIC_BUILD=PASS')


if __name__ == '__main__':
    main()
