#!/bin/bash
# Гейт 2: код двойника (twin/, run.py) не меняется без утверждённого плана.
# Утверждённый план — файл в plans/ со строкой «Статус: утверждён», помеченный как текущий в plans/CURRENT.
f=$(jq -r '.tool_input.file_path // empty')
case "$f" in
  */twin/*|*/run.py)
    cur="$CLAUDE_PROJECT_DIR/plans/CURRENT"
    plan="$CLAUDE_PROJECT_DIR/plans/$(cat "$cur" 2>/dev/null)"
    if [ ! -f "$cur" ] || ! grep -q "^Статус: утверждён" "$plan" 2>/dev/null; then
      echo "Нет утверждённого текущего плана (plans/CURRENT → план со «Статус: утверждён»). Сначала план, потом код." >&2
      exit 2
    fi ;;
esac
exit 0
