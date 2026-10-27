# Plan 18: личная арка

Spec: specs/18-personal-arc.spec.md
Статус: утверждён 2026-10-27 (общее слово Стана: «Утверждаю все твои решения по подготовке оставшихся модулей и создания новых заявок при необходимости»).
Исполнение: по команде Стана («18» или «исполняй 18»); вместе с командой нужны разрешение править tests/test_acceptance.py (только Edit) и на новый эталон tests/baseline_pre18.json. Общее слово 2026-10-27 покрывает подготовку, а не правку tests/.
Зависит от: 01 (для именных), 13 (есть).

## Шаги

1. Эталон: tests/baseline_pre18.json — журналы всех сценариев до правок кода.
2. twin/params.py: параметры п. 8 spec.
3. twin/arc.py (новый): чистая `arc_after_event(before, after, arc_state, params)`; клэмп; ratios.
4. twin/model.py: поля арки на Faction, хук после assault() для обеих сторон, множитель в power(), ApplyArc для именных, пакеты Broken_Drink_Pkg/Hardened_Train_Pkg в `package_for` (01).
5. twin/scenarios.py: AR6–AR9 сценариями (AR1–AR5 — чистые тесты), метрика насыщения как функция для отчёта, REVERSE R103–R108; run.py.
6. tests/test_acceptance.py (только Edit): AR в списки, чистые тесты AR1–AR5, AR10 против baseline_pre18.json, строка в шапку.
7. `python3 -m pytest`, `python3 run.py`; красные строки в отчёт.
8. Отчёт reports/18-report.md (с кривой насыщения), коммит, push, копии в Project, plans/CURRENT.


## Риски исполнения

- Именная часть требует 01 в коде; без неё исполнить рядовую часть (AR1–AR6, AR9, AR10), именную (AR7–AR8) отложить, и сказать это в отчёте.
- Гонка в assault(): потери считаются в kill_many, tier-снимок до и после делается вокруг вызовов, не внутри.


## Твоё время
Команда на исполнение + два разрешения (tests/test_acceptance.py, tests/baseline_pre18.json). Допущения в spec §3 можно поправить до команды.
