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
QWEN_URL="$(osascript -e 'text returned of (display dialog "Qwen: вставьте НЕСЕКРЕТНЫЙ Model Studio Base URL. Если он уже сохранён, оставьте поле пустым." default answer "" buttons {"Отмена", "Далее"} default button "Далее" cancel button "Отмена" with title "Eksamio Tutor — Qwen config")')"
YANDEX_FOLDER="$(osascript -e 'text returned of (display dialog "Yandex: укажите НЕСЕКРЕТНЫЙ Folder ID. Если он уже сохранён, оставьте поле пустым." default answer "" buttons {"Отмена", "Сохранить"} default button "Сохранить" cancel button "Отмена" with title "Eksamio Tutor — Yandex config")')"
cd "$SCRIPT_DIR"
"$PYTHON" ./configure_private_provider_config.py --qwen-base-url "$QWEN_URL" --yandex-folder-id "$YANDEX_FOLDER"
"$PYTHON" ./provider_live_preflight.py
osascript -e 'display alert "Eksamio Tutor" message "Несекретная конфигурация сохранена. Результат preflight показан в окне Terminal." as informational'
