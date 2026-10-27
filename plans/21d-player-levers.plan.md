# Plan 21d: рычаги игрока — убедить, подкупить, подсказать

Spec: specs/21d-player-levers.spec.md (черновик)
Статус: утверждён 2026-10-27 (Стан: «утверждаю 21d», разрешены правка tests/test_acceptance.py и новый эталон tests/baseline_pre21d.json).

Выполнено: 2026-10-27, отчёт reports/21d-report.md; 1038 тестов зелёные.

## Шаги
1. Эталон: снять журналы EV20–EV31 (и PL-базу WR2, WR1) до правок кода в tests/baseline_pre21d.json (EV1–EV19 и 70 прежних уже под эталонами).
2. twin/params.py: `player_levers_enabled` (False), `bribe_price_h` 100, `bribe_profile_mult`, `incite_cap` 6, `incite_decay` 1, `incite_decay_every` 10, `bribe_cooldown` 10, `persuade_min_shock` 25, `persuade_min_rep` 40, `persuade_cooldown` 10, `rep_default` 50, `rep_kill_loss` 30, `persuade_block_archnemesis` True, `tip_needed_for_motive` (только для обратной проверки) — с метками [док 08] / [предл].
3. twin/model.py: `Relation.i`; H включает `i` (rel_h и конец relations_step); затухание `i`; World `player_funds`, `player_rep`, `bribe_last`, `persuade_last`; действия bribe, tip, persuade в `player_action`; события `player_failed`, `player_truce`; `_war_end(..., "WAR_END_PLAYER")` без победителя; штраф репутации в `kill_named`.
4. twin/scenarios.py: PL1–PL12 (PL_SCENARIOS) на обстановке WR (PL8 — на WR2), хуки состояния для PL10; run.py: список; обратные R55–R62.
5. tests/test_acceptance.py (только Edit, с вашего разрешения): PL в списки, PL12 против baseline_pre21d.json, строка в шапку.
6. `python3 -m pytest`, `python3 run.py`; красные строки — в отчёт, критерии не ослабляются.
7. Отчёт reports/21d-report.md, коммит, push, копии в Project, plans/CURRENT.

## Риски исполнения
- PL8/PL9 требуют, чтобы война реально объявлялась на обстановке WR за разумное число тиков; обстановка подбирается пробами, критерии не меняются.
- Выключатель выключен: любая сломанная эталонная строка — стоп.

## Твоё время
Утвердить план (строка «Статус: утверждён»), разрешить правку tests/test_acceptance.py и новый эталон tests/baseline_pre21d.json. Допущения 1–6 в spec §3 можно поправить.
