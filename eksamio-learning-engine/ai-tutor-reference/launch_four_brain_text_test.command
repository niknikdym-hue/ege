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
button returned of (display dialog "Будет разрешён приватный реальный текстовый тест AI-Тьютора. Можно выбрать OpenAI, Qwen, DeepSeek или Alice AI. Максимум 20 успешных сообщений в одной сессии. Возможны API-расходы. Публичный сайт, production PEIS и голос выключены. Продолжить?" buttons {"Отмена", "Разрешаю текстовый тест"} default button "Разрешаю текстовый тест" cancel button "Отмена" with title "Eksamio Tutor — four-brain text test" with icon caution)
APPLESCRIPT
then
  exit 0
fi
cd "$SCRIPT_DIR"
export PYTHONDONTWRITEBYTECODE=1
exec "$PYTHON" ./private_four_brain_tutor_test_ui.py --owner-authorized --max-turns 20
