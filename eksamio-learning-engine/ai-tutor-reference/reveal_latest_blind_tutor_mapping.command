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
if ! osascript <<'APPLESCRIPT' >/dev/null
button returned of (display dialog "Раскрывайте A/B/C/D только ПОСЛЕ того, как оценки всех вариантов зафиксированы. Сейчас показать, какой AI скрывался под каждой буквой?" buttons {"Отмена", "Раскрыть A/B/C/D"} default button "Раскрыть A/B/C/D" cancel button "Отмена" with title "Eksamio Tutor — reveal blind test" with icon caution)
APPLESCRIPT
then
  exit 0
fi
cd "$SCRIPT_DIR"
"$PYTHON" ./reveal_blind_tutor_mapping.py --latest
printf '\nНажмите любую клавишу, чтобы закрыть окно.\n'
read -k 1
