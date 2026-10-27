# Plan 16c: наследование цели и вендетта

Spec: specs/16c-inheritance-vendetta.spec.md
Статус: утверждён 2026-10-27 (общее слово Стана: «Утверждаю все твои решения по подготовке оставшихся модулей и создания новых заявок при необходимости»).
Исполнение: по команде Стана («16c» или «исполняй 16c»); вместе с командой нужны разрешение править tests/test_acceptance.py (только Edit) и на новый эталон tests/baseline_pre16c.json. Общее слово 2026-10-27 покрывает подготовку, а не правку tests/.
Зависит от: 16b, 02 (желательно).

## Шаги

1. Эталон: tests/baseline_pre16c.json — журналы всех сценариев (включая IN, IS) до правок кода.
2. twin/params.py: `inheritance_enabled`, `vendetta_max`, `vendetta_w`, таблица исходов.
3. twin/objective.py: `inherit(profile, cause, objective)` — чистая функция таблицы.
4. twin/model.py: поле culprit в событии leader_killed; применение таблицы в `_apply_succession`; счётчик вендетты в фазе 7; потребители в `war_step` и `_persuade`.
5. twin/scenarios.py: IV1–IV10, REVERSE R125–R129; run.py.
6. tests/test_acceptance.py (только Edit): IV в списки, IV10 против baseline_pre16c.json, строка в шапку.
7. `python3 -m pytest`, `python3 run.py`; красные строки в отчёт.
8. Отчёт reports/16c-report.md, коммит, push, копии в Project, plans/CURRENT.


## Риски исполнения

- Порядок внутри ApplySuccession: сначала смена уклада (21b), затем цель (16c), затем вектор стратегии (16b).
- Требует 16a, 16b, 01, желательно 02.


## Твоё время
Команда на исполнение + два разрешения (tests/test_acceptance.py, tests/baseline_pre16c.json). Допущения в spec §3 можно поправить до команды.
