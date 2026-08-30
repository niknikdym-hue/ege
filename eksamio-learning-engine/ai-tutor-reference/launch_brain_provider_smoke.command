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
button returned of (display dialog "Будут выполнены ровно три коротких реальных API-запроса: Qwen, DeepSeek и Alice AI. Возможны небольшие расходы. Тексты ответов не сохраняются, ученические данные не используются, голос выключен. Продолжить?" buttons {"Отмена", "Разрешаю 3 smoke-запроса"} default button "Разрешаю 3 smoke-запроса" cancel button "Отмена" with title "Eksamio Tutor — provider smoke" with icon caution)
APPLESCRIPT
then
  exit 0
fi
cd "$SCRIPT_DIR"
export PYTHONDONTWRITEBYTECODE=1
"$PYTHON" ./provider_live_preflight.py
if "$PYTHON" ./live_brain_provider_smoke.py --owner-authorized --provider all; then
  osascript -e 'display alert "Eksamio Tutor" message "Qwen, DeepSeek и Alice AI прошли live smoke. Можно переходить к человеческому сравнению." as informational'
else
  osascript -e 'display alert "Eksamio Tutor" message "Один из live smoke не прошёл. Смотрите точную ошибку в Terminal; человеческий тест этого провайдера пока не начинаем." as critical'
  exit 1
fi
