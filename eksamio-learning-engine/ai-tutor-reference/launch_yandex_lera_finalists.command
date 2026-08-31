#!/bin/zsh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
if [[ "${OSTYPE:-}" != darwin* ]]; then
  echo "YANDEX_LERA_FINALISTS=BLOCKED_MACOS_REQUIRED"
  exit 2
fi
if ! command -v osascript >/dev/null 2>&1; then
  echo "YANDEX_LERA_FINALISTS=BLOCKED_OSASCRIPT_REQUIRED"
  exit 2
fi
answer="$(osascript -e 'button returned of (display dialog "Запустить финальное сравнение Леры A и D? Будут только короткие платные запросы Yandex SpeechKit. OpenAI и Tutor-мозг не вызываются." buttons {"Отмена", "Разрешаю тест"} default button "Разрешаю тест" cancel button "Отмена")' 2>/dev/null || true)"
if [[ "$answer" != "Разрешаю тест" ]]; then
  echo "YANDEX_LERA_FINALISTS=BLOCKED_OWNER_AUTHORIZATION"
  exit 2
fi
exec python3 "$HERE/yandex_lera_finalists_ui.py" --owner-authorized
