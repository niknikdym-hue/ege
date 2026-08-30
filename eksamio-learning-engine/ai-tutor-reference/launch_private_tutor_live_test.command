#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/private_tutor_runtime_gate.zsh"

PYTHON=""
for candidate in python3.12 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
    then
      PYTHON="$candidate"
      break
    fi
  fi
done

if [[ -z "$PYTHON" ]]; then
  osascript -e 'display alert "Eksamio Tutor" message "Для private live test нужен Python 3.12 или новее." as critical'
  exit 2
fi

if ! osascript <<'APPLESCRIPT' >/dev/null
button returned of (display dialog "Будет разрешён приватный реальный текстовый тест AI-Тьютора. Возможны небольшие API-расходы. Публичный сайт, production PEIS и голос остаются выключены. Ключи берутся автоматически из локального защищённого хранилища и не показываются. Продолжить?" buttons {"Отмена", "Разрешаю тест"} default button "Разрешаю тест" cancel button "Отмена" with title "Eksamio Tutor — private live test" with icon caution)
APPLESCRIPT
then
  exit 0
fi

cd "$SCRIPT_DIR"
export PYTHONDONTWRITEBYTECODE=1
exec "$PYTHON" ./private_multi_provider_tutor_live_test_candidate.py --owner-authorized --max-turns 20
