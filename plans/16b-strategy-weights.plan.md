# Plan 16b: стратегия — таблица (цель × трейт) → множители порогов

Spec: specs/16b-strategy-weights.spec.md
Статус: утверждён 2026-10-27 (общее слово Стана: «Утверждаю все твои решения по подготовке оставшихся модулей и создания новых заявок при необходимости»).
Исполнение: по команде Стана («16b» или «исполняй 16b»); вместе с командой нужны разрешение править tests/test_acceptance.py (только Edit) и на новый эталон tests/baseline_pre16b.json. Общее слово 2026-10-27 покрывает подготовку, а не правку tests/.
Зависит от: 16a, 01.

## Шаги

1. Эталон: tests/baseline_pre16b.json — журналы всех сценариев, включая IN, до правок кода.
2. twin/params.py: `strategy_enabled`, `strategy_table`.
3. twin/objective.py: `strategy_vector(objective, traits, doctrine)` — чистая функция.
4. twin/model.py: применение вектора в `decide_assault` и `war_step`; запись `strategy`; пересчёт на смену цели, вожака, уклада.
5. twin/scenarios.py: IS2–IS8 сценариями (IS1 — чистый тест), REVERSE R120–R124; run.py.
6. tests/test_acceptance.py (только Edit): IS в списки, IS1, IS9 против baseline_pre16b.json, строка в шапку.
7. `python3 -m pytest`, `python3 run.py`; красные строки в отчёт (особенно IS6).
8. Отчёт reports/16b-report.md, коммит, push, копии в Project, plans/CURRENT.


## Риски исполнения

- IS6 и IS7 — самые хрупкие: геометрия мира (силы, запасы, расстояния до цели) подбирается пробами; критерии не меняются.
- Требует 01 и 16a в коде.


## Твоё время
Команда на исполнение + два разрешения (tests/test_acceptance.py, tests/baseline_pre16b.json). Допущения в spec §3 можно поправить до команды.
