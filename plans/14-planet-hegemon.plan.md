# Plan 14: хозяин планеты

Spec: specs/14-planet-hegemon.spec.md
Статус: утверждён 2026-10-27 (общее слово Стана: «Утверждаю все твои решения по подготовке оставшихся модулей и создания новых заявок при необходимости»).
Исполнение: по команде Стана («14» или «исполняй 14»); вместе с командой нужны разрешение править tests/test_acceptance.py (только Edit) и на новый эталон tests/baseline_pre14.json. Общее слово 2026-10-27 покрывает подготовку, а не правку tests/.
Зависит от: 15 (реестр активов).

## Шаги

1. Эталон: tests/baseline_pre14.json — журналы всех сценариев до правок кода.
2. twin/params.py: `planet_hegemon_enabled` False, `hegemon_margin` 1, `hegemon_cooldown` 7 [док 14].
3. twin/model.py: поля World `hegemon`, `hegemon_tick`; `_hegemon_step()` в конце фазы 8; событие `hegemon_change`.
4. twin/scenarios.py: PH1–PH10 (чистая обстановка, 4–6 активов с одной станцией), REVERSE R79–R83; run.py.
5. tests/test_acceptance.py (только Edit): PH в списки, PH10 против baseline_pre14.json, строка в шапку.
6. `python3 -m pytest`, `python3 run.py`; красные строки в отчёт.
7. Отчёт reports/14-report.md, коммит, push, копии в Project, plans/CURRENT.


## Риски исполнения

- Требует 15 (registry()): до её исполнения 14 не начинать.
- Отложенная смена: хранить желаемого кандидата не нужно, достаточно сравнивать статус с кандидатом каждый тик.


## Твоё время
Команда на исполнение + два разрешения (tests/test_acceptance.py, tests/baseline_pre14.json). Допущения в spec §3 можно поправить до команды.
