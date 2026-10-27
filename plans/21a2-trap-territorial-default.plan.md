# Plan 21a-2: правка 21a — ловушка Дрейфующих, территориальный шок, включение по умолчанию

Spec: specs/21a2-trap-territorial-default.spec.md (утверждён 2026-10-27)
Статус: утверждён 2026-10-27 (Стан: ответы на вопросы отчёта 21a; блочное утверждение «до следующего модуля»; на правку tests/ и эталона разрешение действует).

Выполнено: 2026-10-27, отчёт reports/21a2-report.md; 909 тестов зелёные, 1 красный (EV13, «X6 жива») с разбором в отчёте.

## Шаги
1. params.py: `evo_drifter_needs_site` True, `evo_t_site` 25, `evolution_enabled` True. evolution.py: `fires`/`first_rule` с владением объектом; `axis_p` с территориальным шоком. model.py: `tshock`, события assault/surrender, затухание, журнал module 04.
2. scenarios.py: `run()` — прежние сценарии по умолчанию с `evolution_enabled` = False, параметр `evo`; ev11 с `evo=True`; EV7 переписан, EV16, EV17, усиление EV13; обратные R46, R47.
3. tests/test_acceptance.py: EV16, EV17 в список, тест значения по умолчанию, строка в шапку; прежние проверки не меняются.
4. pytest, run.py, отчёт reports/21a2-report.md, коммит, push, Project.
