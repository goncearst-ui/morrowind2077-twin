# Plan 21b: именные персонажи, вожак, преемник и мгновенная смена уклада

Spec: specs/21b-leader-successor.spec.md (черновик, ред. 2)
Статус: ждёт утверждения Стана. Код не менять.

## Шаги
1. Эталон: снять журналы EV1–EV19 до правок кода в tests/baseline_pre21b.json (70 прежних — в baseline_pre21a.json).
2. twin/params.py: `leader_enabled` (False), `evo_c_leader_loss` 30, `evo_m_leader_loss` 10, `succession_arch` {Осторожный: Хранители, Радикальный: Хищники}, `leader_kill_seat` False, `leader_kill_broken` False (вожак «заперт», как в enRAGE), `named_max` 10; метки [док 05] / [предл].
3. twin/model.py: поля Faction `named` (список записей: имя, роль, профиль, место, жив), `leader`; `player_script` в World (список тик/действие/цель), действие `kill` в фазе 7 до решений; событие `seat_lost` в assault() (только при leader_enabled, до depot_strike); `kill_named(f, имя, reason)` (вожак → событие; офицер → `kill_tier`); чтение событий в `_evo_events` (seat_lost, war_end с BROKEN → гибель вожака, C и M); очередь succession, применение в фазе 6 до стека (`apply_succession`: правила 1–2, сброс pending, пауза, ΔM); зачистка базы убивает преемника; `rule_hits[1]`, `rule_hits[2]`.
4. twin/scenarios.py: EV20–EV27, EV30, EV31 (EV_LEADER), `player_script` и именные в build; run.py: список; обратные R50–R54.
5. tests/test_acceptance.py (только Edit, с вашего разрешения): EV20–EV27, EV30, EV31 в списки, EV28 (выключен = эталоны), EV29 (люди), строка в шапку.
6. `python3 -m pytest`, `python3 run.py`; красные строки — в отчёт, критерии не ослабляются.
7. Отчёт reports/21b-report.md, коммит, push, копии в Project (claude/twin/), plans/CURRENT.

## Риски исполнения
- EV26 нужна настоящая война до BROKEN (основа WR7a); при невозможности — отдельная подвязка, в отчёт.
- Переключатель выключен: любая сломанная эталонная строка — стоп.

## Твоё время
Утвердить план (строка «Статус: утверждён»), разрешить правку tests/test_acceptance.py и новый эталон. Допущения 1–5 в spec §3 можно поправить.
