#!/bin/zsh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=""
for candidate in python3.12 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
    then PYTHON="$candidate"; break; fi
  fi
done
if [[ -z "$PYTHON" ]]; then
  osascript -e 'display alert "Кастинг Леры" message "Нужен Python 3.12 или новее." as critical'
  exit 2
fi
if ! osascript <<'APPLESCRIPT' >/dev/null
button returned of (display dialog "Открывается локальный кастинг голоса Lera в Yandex SpeechKit v3. OpenAI и Tutor-мозг не вызываются. Каждый Play делает один короткий платный TTS-запрос; максимум 30 проб. Аудио не сохраняется. Продолжить?" buttons {"Отмена", "Разрешаю кастинг"} default button "Разрешаю кастинг" cancel button "Отмена" with title "Eksamio — кастинг Леры" with icon caution)
APPLESCRIPT
then exit 0; fi
cd "$SCRIPT_DIR"
export PYTHONDONTWRITEBYTECODE=1
exec "$PYTHON" ./yandex_lera_casting_ui.py --owner-authorized
