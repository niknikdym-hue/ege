#!/bin/zsh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=""
for candidate in python3.12 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
  then PYTHON="$candidate"; break; fi
done
if [[ -z "$PYTHON" ]]; then
  osascript -e 'display alert "Eksamio Tutor" message "Нужен Python 3.12 или новее." as critical'
  exit 2
fi
cd "$SCRIPT_DIR"
export PYTHONDONTWRITEBYTECODE=1
"$PYTHON" ./provider_live_preflight.py
printf '\nPreflight завершён. Здесь нет сетевых/API-вызовов и расходов.\n'
read -k 1 '?Нажмите любую клавишу, чтобы закрыть окно. '
printf '\n'
