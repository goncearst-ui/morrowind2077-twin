# Plan 23e: простая сумма вместо встроенной

Spec: specs/23e-plain-sum.spec.md
Статус: утверждён 2026-10-28 (Стан: «исполняй 23e», разрешена правка tests/test_acceptance.py, только Edit; tests/golden/ не разрешено, при изменении золотых файлов остановиться).

## Шаги
1. twin/arith.py: `fsum`.
2. Заменить `sum(` на `fsum(` в модельных модулях; добавить импорт.
3. twin/params.py: sm_bug_builtin_sum, sm_bug_leftover (по умолчанию False, метка «только для R163/R164»).
4. twin/x23e.py: SM1–SM3, обратные R163–R164; импорт в twin/extra.py.
5. tests/test_acceptance.py (только Edit): строка в шапку.
6. Сверить: `python3 -m pytest` (3800 + новые), сравнить MANIFEST.json и золотые файлы с заново сгенерированными.
7. reports/23-formula-order.md (пункт 4), reports/23e-report.md, plans/CURRENT, plans/QUEUE.md; коммит в ветку, push, копии в Project.

## Риски исполнения
Любое расхождение журналов или снимков после замены: остановка, отчёт, решение Стана.

## Твоё время
Нет: утверждение дано командой «исполняй 23e».
