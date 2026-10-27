# Plan 15: реестр активов планеты

Spec: specs/15-asset-registry.spec.md
Статус: утверждён 2026-10-27 (общее слово Стана: «Утверждаю все твои решения по подготовке оставшихся модулей и создания новых заявок при необходимости»).
Исполнение: по команде Стана («15» или «исполняй 15»); вместе с командой нужны разрешение править tests/test_acceptance.py (только Edit) и на новый эталон tests/baseline_pre15.json. Общее слово 2026-10-27 покрывает подготовку, а не правку tests/.
Зависит от: 13a не требуется (можно параллельно).

## Шаги

1. Эталон: tests/baseline_pre15.json — журналы всех сценариев до правок кода.
2. twin/params.py: `asset_cap` (None) [док 15].
3. twin/model.py: `Site.kind`, `World.registry()`, проверка потолка в `__post_init__`, регион «orbit» для станции по умолчанию.
4. twin/scenarios.py: RE1–RE6, REVERSE R75–R78; run.py.
5. tests/test_acceptance.py (только Edit): RE в списки, RE6 против baseline_pre15.json, строка в шапку.
6. `python3 -m pytest`, `python3 run.py`; красные строки в отчёт.
7. Отчёт reports/15-report.md, коммит, push, копии в Project, plans/CURRENT.


## Риски исполнения

- Поле `kind` по умолчанию 0, `Site(...)` во всех прежних сценариях создаётся позиционно: добавлять поле строго в конец dataclass.


## Твоё время
Команда на исполнение + два разрешения (tests/test_acceptance.py, tests/baseline_pre15.json). Допущения в spec §3 можно поправить до команды.
