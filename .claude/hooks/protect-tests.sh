#!/bin/bash
# Гейт 1: чек-лист приёмки (tests/) нельзя менять во время задачи.
# Разблокировка — только Стан: запустить сессию с ALLOW_TEST_EDIT=1.
f=$(jq -r '.tool_input.file_path // empty')
case "$f" in
  */tests/*|tests/*)
    if [ "$ALLOW_TEST_EDIT" != "1" ]; then
      echo "Чек-лист приёмки (tests/) меняет только Стан. Запустите с ALLOW_TEST_EDIT=1." >&2
      exit 2
    fi ;;
esac
exit 0
