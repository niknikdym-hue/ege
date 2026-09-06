#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PYTHON=""
for candidate in python3.12 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
  then
    PYTHON="$candidate"
    break
  fi
done

if [[ -z "$PYTHON" ]]; then
  osascript -e 'display alert "Eksamio Tutor" message "Нужен Python 3.12 или новее." as critical'
  exit 2
fi

CANDIDATE_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || true)"
if [[ ${#CANDIDATE_SHA} -ne 40 || "$CANDIDATE_SHA" == *[^0-9a-f]* ]]; then
  osascript -e 'display alert "Eksamio Tutor" message "Не удалось определить exact candidate SHA." as critical'
  exit 2
fi

if ! osascript <<'APPLESCRIPT' >/dev/null
button returned of (display dialog "Запускается приватный OpenAI VOICE benchmark. Мозг — OpenAI gpt-5.6-sol; речь — Yandex SpeechKit; ответ — Lera. Yandex AI и YANDEX_FOLDER_ID для этого прогона не используются. Возможны небольшие API-расходы. Продолжить?" buttons {"Отмена", "Разрешаю тест"} default button "Разрешаю тест" cancel button "Отмена" with title "Eksamio Tutor — OpenAI VOICE" with icon caution)
APPLESCRIPT
then
  exit 0
fi

cd "$SCRIPT_DIR"
export PYTHONDONTWRITEBYTECODE=1
export EKSAMIO_TUTOR_CANDIDATE_SHA="$CANDIDATE_SHA"
exec "$PYTHON" ./private_openai_voice_no_folder_ui.py --owner-authorized --port 8767
