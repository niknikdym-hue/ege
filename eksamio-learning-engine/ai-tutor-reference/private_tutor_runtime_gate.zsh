# Common sourced gate for private live Tutor launchers. No provider execution.
if [[ -z "${SCRIPT_DIR:-}" ]]; then
  echo "EKSAMIO_TUTOR_RUNTIME_GATE=BLOCKED_MISSING_SCRIPT_DIR" >&2
  return 2 2>/dev/null || exit 2
fi

REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$REPO_ROOT" ]]; then
  osascript -e 'display alert "Eksamio Tutor" message "Тест должен запускаться из Git checkout Eksamio." as critical'
  return 2 2>/dev/null || exit 2
fi

if ! git -C "$REPO_ROOT" diff --quiet -- || ! git -C "$REPO_ROOT" diff --cached --quiet --; then
  osascript -e 'display alert "Eksamio Tutor" message "В checkout есть незакоммиченные изменения. Для честного теста нужен чистый exact build." as critical'
  return 2 2>/dev/null || exit 2
fi

EKSAMIO_TUTOR_CANDIDATE_SHA="$(git -C "$REPO_ROOT" rev-parse --verify HEAD)"
if [[ ${#EKSAMIO_TUTOR_CANDIDATE_SHA} -ne 40 || "$EKSAMIO_TUTOR_CANDIDATE_SHA" == *[^0-9a-f]* ]]; then
  osascript -e 'display alert "Eksamio Tutor" message "Не удалось определить exact Git build." as critical'
  return 2 2>/dev/null || exit 2
fi
export EKSAMIO_TUTOR_CANDIDATE_SHA
print -r -- "EKSAMIO_TUTOR_CANDIDATE_SHA=$EKSAMIO_TUTOR_CANDIDATE_SHA"
print -r -- "EKSAMIO_TUTOR_WORKTREE_CLEAN=1"
