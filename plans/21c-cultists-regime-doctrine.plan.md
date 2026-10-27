# Plan 21c: Культисты, Regime, Идеолог, TF_Doctrine

Spec: specs/21c-cultists-regime-doctrine.spec.md (черновик)
Статус: утверждён 2026-10-27 (Стан: «утверждаю 21c», разрешены правка tests/test_acceptance.py и новый эталон tests/baseline_pre21c.json).

Выполнено: 2026-10-27, см. reports/21c-report.md.

## Шаги
1. Эталон: журналы EV1–EV31 и PL1–PL11 до правок кода → tests/baseline_pre21c.json.
2. twin/params.py: пороги правил 4 и 9, dwell 4 и 9, выходы Культистов и Regime, `doctrine_gap_mult` 2.0, `doctrine_max_factions` 1, `doctrine2_freezes` True; ключи Культисты и Regime в `evo_c_rest`, `archetype_cost_mult`, `share_rate`, `rel_axes`; Идеолог в `succession_arch` и `bribe_profile_mult`. Метки [док 07] / [предл].
3. twin/evolution.py: `RULE_TARGET` 4 и 9, `fires`, `exit_open` (новые уклады, доктрина), `dwell`; walk по полному порядку. twin/model.py: `Faction.doctrine`, проверка «не более одной», доктрина в фазе 5.
4. twin/scenarios.py: CR1–CR5, CR7 (+контроль CR7k), CR8–CR10; обход CR6 как отдельный тест; run.py; обратные R63–R69.
5. tests/test_acceptance.py (только Edit, с вашего разрешения): CR в списки, CR6, CR11, строка в шапку.
6. `python3 -m pytest`, `python3 run.py`; красные строки (CR9 вероятнее всех) — в отчёт, критерии не ослабляются.
7. Отчёт reports/21c-report.md, коммит, push, копии в Project, plans/CURRENT.

## Риски исполнения
- Обход может показать затенение правила 9 правилом 6 или 5; находка идёт в отчёт.
- CR9 может не выполняться (контрабанда или дезертирство не доводят до нуля): красная строка с разбором.

## Твоё время
Утвердить план (строка «Статус: утверждён»), разрешить правку tests/test_acceptance.py и новый эталон tests/baseline_pre21c.json. Допущения 1–5 в spec §3 можно поправить.
