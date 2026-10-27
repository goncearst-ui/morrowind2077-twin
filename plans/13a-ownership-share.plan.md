# Plan 13a: доля фракции в регионе

Spec: specs/13a-ownership-share.spec.md
Статус: утверждён 2026-10-27 (общее слово Стана: «Утверждаю все твои решения по подготовке оставшихся модулей и создания новых заявок при необходимости»).
Исполнение: по команде Стана («13a» или «исполняй 13a»); вместе с командой нужны разрешение править tests/test_acceptance.py (только Edit) и на новый эталон tests/baseline_pre13a.json. Общее слово 2026-10-27 покрывает подготовку, а не правку tests/.
Зависит от: нет (первая в очереди plans/QUEUE.md).

## Шаги

1. Эталон: tests/baseline_pre13a.json — журналы всех сценариев (EV, PL, CR и 70 прежних) до правок кода.
2. twin/params.py: `region_share_enabled` False, `share_income_k` 0.0 с метками [док 13] / [предл].
3. twin/model.py: `World.region_share` (производная), `_publish_shares()` в конце фазы 8; `dominant(region)`; множитель дохода в work_plan и expected_income при k > 0.
4. twin/scenarios.py: OS1, OS1b–OS7 (чистая обстановка по образцу PL_SIMPLE), REVERSE R70–R74; run.py.
5. tests/test_acceptance.py (только Edit): OS в списки, OS7 против baseline_pre13a.json, строка в шапку.
6. `python3 -m pytest`, `python3 run.py`; красные строки в отчёт, критерии не ослаблять.
7. Отчёт reports/13a-report.md, коммит, push, копии в Project, plans/CURRENT.


## Риски исполнения

- Пересчёт в фазе 8 после war_step: порядок фаз не меняется, новая фаза не добавляется.
- При k > 0 доход меняется там, где регион общий; проверять только OS5, остальные сценарии идут с k = 0.


## Твоё время
Команда на исполнение + два разрешения (tests/test_acceptance.py, tests/baseline_pre13a.json). Допущения в spec §3 можно поправить до команды.
