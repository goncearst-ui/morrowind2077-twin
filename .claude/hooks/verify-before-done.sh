#!/bin/bash
# Гейт 4: агент не заканчивает работу, не прогнав чек-лист.
# Красный прогон допустим только если в reports/ есть отчёт, созданный позже последнего изменения кода.
input=$(cat)
[ "$(echo "$input" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0
cd "$CLAUDE_PROJECT_DIR" || exit 0
if python3 -m pytest -q >/tmp/twin-pytest.txt 2>&1; then
  exit 0
fi
latest_report=$(ls -t reports/*.md 2>/dev/null | head -1)
if [ -n "$latest_report" ] && [ -z "$(find twin run.py -type f -newer "$latest_report" 2>/dev/null)" ]; then
  exit 0
fi
echo "Чек-лист красный, а отчёта о причинах нет или он старше кода. Прогоните python3 -m pytest и объясните каждую красную строку в reports/." >&2
tail -5 /tmp/twin-pytest.txt >&2
exit 2
