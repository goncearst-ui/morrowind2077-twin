#!/bin/bash
# Гейт 3: при коммите каждая спецификация обязана иметь разделы про движок (A/B/C) и прецеденты модов.
cmd=$(jq -r '.tool_input.command // empty')
case "$cmd" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac
bad=""
for s in "$CLAUDE_PROJECT_DIR"/specs/*.md; do
  [ -f "$s" ] || continue
  grep -q "Что движок умеет" "$s" || bad="$bad $(basename "$s"):нет-раздела-A/B/C"
  grep -q "Какие моды" "$s" || bad="$bad $(basename "$s"):нет-раздела-прецедентов"
done
if [ -n "$bad" ]; then
  echo "Спецификация не проходит гейт:$bad" >&2
  exit 2
fi
exit 0
