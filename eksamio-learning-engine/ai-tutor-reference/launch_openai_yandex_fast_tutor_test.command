#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

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
  osascript -e 'display alert "Eksamio Tutor" message "Для private Tutor benchmark нужен Python 3.12 или новее." as critical'
  exit 2
fi

if ! command -v git >/dev/null 2>&1; then
  osascript -e 'display alert "Eksamio Tutor" message "git недоступен: exact candidate identity не подтверждена." as critical'
  exit 2
fi

CANDIDATE_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || true)"
if [[ ${#CANDIDATE_SHA} -ne 40 || "$CANDIDATE_SHA" == *[^0-9a-f]* ]]; then
  osascript -e 'display alert "Eksamio Tutor" message "Не удалось определить exact candidate SHA." as critical'
  exit 2
fi

if [[ -z "${YANDEX_FOLDER_ID:-}" ]] && command -v yc >/dev/null 2>&1; then
  folder="$(yc config get folder-id 2>/dev/null || true)"
  if [[ -n "$folder" ]]; then
    export YANDEX_FOLDER_ID="$folder"
  fi
fi

if ! osascript <<'APPLESCRIPT' >/dev/null
button returned of (display dialog "Запускается приватное слепое сравнение Eksamio Tutor: четыре TEXT-мозга, одинаковый сценарий из 10 шагов. Возможны небольшие расходы OpenAI, Qwen, DeepSeek и Yandex AI только после фактических запросов. Voice в этот рейтинг не входит. Публичный сайт и production PEIS остаются выключены; диалоги и оценки не записываются на диск. Продолжить?" buttons {"Отмена", "Разрешаю тест"} default button "Разрешаю тест" cancel button "Отмена" with title "Eksamio Tutor — four-brain TEXT benchmark" with icon caution)
APPLESCRIPT
then
  exit 0
fi

cd "$SCRIPT_DIR"
export PYTHONDONTWRITEBYTECODE=1
export EKSAMIO_TUTOR_CANDIDATE_SHA="$CANDIDATE_SHA"
exec "$PYTHON" ./private_four_brain_text_benchmark_ui.py --owner-authorized
