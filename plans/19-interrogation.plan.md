# Plan 19: допрос — сторона двойника

Spec: specs/19-interrogation.spec.md
Статус: утверждён 2026-10-27 (общее слово Стана: «Утверждаю все твои решения по подготовке оставшихся модулей и создания новых заявок при необходимости»).
Исполнение: по команде Стана («19» или «исполняй 19»); вместе с командой нужны разрешение править tests/test_acceptance.py (только Edit) и на новый эталон tests/baseline_pre19.json. Общее слово 2026-10-27 покрывает подготовку, а не правку tests/.
Зависит от: 01; желательно 02.

## Шаги

1. Эталон: tests/baseline_pre19.json — журналы всех сценариев до правок кода.
2. twin/params.py: параметры п. 7 spec.
3. twin/interrogation.py (новый): чистые функции страха и исхода.
4. twin/model.py: `prisoners`, действия capture / interrogate / release / hand_over / execute в `player_action`, ловушки в `assault`, учёт людей.
5. twin/scenarios.py: ID2–ID10 сценариями (ID1 — чистый тест), REVERSE R130–R135; run.py.
6. tests/test_acceptance.py (только Edit): ID в списки, ID11 против baseline_pre19.json, строка в шапку.
7. `python3 -m pytest`, `python3 run.py`; красные строки в отчёт.
8. Отчёт reports/19-report.md, коммит, push, копии в Project, plans/CURRENT.


## Риски исполнения

- Закон сохранения людей с пленными: проверка суммы на каждом тике в сценариях ID.
- CK-стадии S1–S6 docs/19 не входят и не готовятся до G6.


## Твоё время
Команда на исполнение + два разрешения (tests/test_acceptance.py, tests/baseline_pre19.json). Допущения в spec §3 можно поправить до команды.
