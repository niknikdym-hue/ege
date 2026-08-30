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
if ! osascript <<'APPLESCRIPT' >/dev/null
button returned of (display dialog "Слепой голосовой тест сравнит четыре AI-мозга как A/B/C/D. Для всех один голосовой слой: Yandex SpeechKit STT + Lera TTS, поэтому сравнивается именно мозг. Максимум 20 успешных реплик; возможны AI/SpeechKit расходы. Аудио не сохраняется. Продолжить?" buttons {"Отмена", "Разрешаю слепой голосовой тест"} default button "Разрешаю слепой голосовой тест" cancel button "Отмена" with title "Eksamio Tutor — blind voice test" with icon caution)
APPLESCRIPT
then
  exit 0
fi
cd "$SCRIPT_DIR"
export PYTHONDONTWRITEBYTECODE=1
exec "$PYTHON" ./private_four_brain_blind_test_ui.py --owner-authorized --enable-speech --max-turns 20
