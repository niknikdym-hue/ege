#!/bin/zsh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/private_tutor_runtime_gate.zsh"
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
if ! "$PYTHON" ./provider_live_preflight.py --require-four-brain; then
  osascript -e 'display alert "Eksamio Tutor" message "Слепой тест не начат: не все четыре AI-мозга локально готовы. Сначала завершите provider preflight/configuration." as critical'
  exit 3
fi
if ! osascript <<'APPLESCRIPT' >/dev/null
button returned of (display dialog "Слепой текстовый тест сравнит четыре AI-мозга как варианты A/B/C/D. Названия OpenAI, Qwen, DeepSeek и Alice AI будут скрыты до отдельного раскрытия после оценки. Максимум 20 успешных сообщений в одной сессии; возможны API-расходы. Продолжить?" buttons {"Отмена", "Разрешаю слепой тест"} default button "Разрешаю слепой тест" cancel button "Отмена" with title "Eksamio Tutor — blind text test" with icon caution)
APPLESCRIPT
then
  exit 0
fi
exec "$PYTHON" ./private_four_brain_blind_test_ui.py --owner-authorized --max-turns 20
