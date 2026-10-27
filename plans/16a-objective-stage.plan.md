# Plan 16a: цель лидера, KR, этап, жизненный цикл

Spec: specs/16a-objective-stage.spec.md
Статус: утверждён 2026-10-27 (общее слово Стана: «Утверждаю все твои решения по подготовке оставшихся модулей и создания новых заявок при необходимости»).
Исполнение: по команде Стана («16a» или «исполняй 16a»); вместе с командой нужны разрешение править tests/test_acceptance.py (только Edit) и на новый эталон tests/baseline_pre16a.json. Общее слово 2026-10-27 покрывает подготовку, а не правку tests/.
Зависит от: 21b, 21c (есть).

## Шаги

1. Эталон: tests/baseline_pre16a.json — журналы всех сценариев до правок кода.
2. twin/params.py: параметры п. 6 spec; `obj_kr` как данные.
3. twin/objective.py (новый): вычисление KR по миру (чистые функции), таблицы целей.
4. twin/model.py: поля цели на Faction, `objective_step()` в фазе 7 до решений, хук коллапса в `_apply_succession`, проверка потолков.
5. twin/scenarios.py: IN1–IN10 (чистая обстановка по образцу EV), REVERSE R114–R119; run.py.
6. tests/test_acceptance.py (только Edit): IN в списки, IN10 против baseline_pre16a.json, строка в шапку.
7. `python3 -m pytest`, `python3 run.py`; красные строки в отчёт.
8. Отчёт reports/16a-report.md, коммит, push, копии в Project, plans/CURRENT.


## Риски исполнения

- Порядок внутри фазы 7: objective_step до player_script и решений, чтобы действие игрока на этом тике видело новый этап.
- Метрика C (ctl) может быть None до первого evolution_step: условия hold ждут, пока C задан.


## Твоё время
Команда на исполнение + два разрешения (tests/test_acceptance.py, tests/baseline_pre16a.json). Допущения в spec §3 можно поправить до команды.
