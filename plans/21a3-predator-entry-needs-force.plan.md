# Plan 21a-3: вход в Хищники требует сил для налёта

Spec: specs/21a3-predator-entry-needs-force.spec.md (утверждён 2026-10-27)
Статус: утверждён 2026-10-27 (Стан: ответ на вопрос 2 отчёта 21a-2; на правку tests/ разрешение действует).

Выполнено: 2026-10-27, отчёт reports/21a3-report.md; 913 тестов зелёные, 1 красный (EV13, «X6 жива») с разбором в отчёте.

## Шаги
1. params.py, evolution.py, model.py: `evo_rule5_needs_force`, условие силы в `fires`.
2. scenarios.py: EV18, R48. tests/test_acceptance.py: EV18 в список, строка в шапку.
3. pytest, run.py, отчёт reports/21a3-report.md, коммит, push, Project.
