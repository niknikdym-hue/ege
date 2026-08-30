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
SCENARIO="$(osascript <<'APPLESCRIPT'
set variants to {"1 — OpenAI недоступен → должен ответить Qwen", "2 — OpenAI и Qwen недоступны → должен ответить DeepSeek", "3 — OpenAI, Qwen и DeepSeek недоступны → контрольный Alice AI"}
set picked to choose from list variants with title "Eksamio Tutor — failover" with prompt "Выберите контролируемый сценарий. Отключённые backend'ы НЕ вызываются по сети." default items {item 1 of variants} OK button name "Проверить" cancel button name "Отмена"
if picked is false then return ""
return item 1 of picked
APPLESCRIPT
)"
[[ -n "$SCENARIO" ]] || exit 0
case "$SCENARIO" in
  1*) SIMULATED="openai" ;;
  2*) SIMULATED="openai,qwen" ;;
  3*) SIMULATED="openai,qwen,deepseek" ;;
  *) exit 2 ;;
esac
if ! osascript <<APPLESCRIPT >/dev/null
button returned of (display dialog "Будет выполнен реальный failover-тест. Намеренно отключённые backend'ы: ${SIMULATED}. Следующий backend будет вызван реально; возможны небольшие API-расходы. AUTO зафиксирован и не может быть случайно изменён. Продолжить?" buttons {"Отмена", "Разрешаю failover-тест"} default button "Разрешаю failover-тест" cancel button "Отмена" with title "Eksamio Tutor — controlled failover" with icon caution)
APPLESCRIPT
then
  exit 0
fi
cd "$SCRIPT_DIR"
export PYTHONDONTWRITEBYTECODE=1
exec "$PYTHON" ./private_four_brain_tutor_test_ui.py --owner-authorized --max-turns 20 --default-provider auto --lock-provider --simulate-unavailable "$SIMULATED"
