# Очередь исполнения (подготовлено 2026-10-27)

Статус: документы intent / spec / plan готовы по всем модулям ниже. В каждом плане стоит «Статус: утверждён» по общему слову Стана 2026-10-27. Код не менялся, tests/ не тронуты, эталоны не сняты.
Чтобы запустить задачу, нужна команда Стана («исполняй NN») и вместе с ней: разрешение править tests/test_acceptance.py (только Edit) и разрешение снять новый эталон tests/baseline_preNN.json (где он указан в плане).

Нумерация обратных проверок (R) закреплена за задачами и не пересекается: 13a R70–74; 15 R75–78; 14 R79–83; 01 R84–90; 02 R91–96; 03d R97–102; 18 R103–108; 09 R109–113; 16a R114–119; 16b R120–124; 16c R125–129; 19 R130–135; 10 R136–140; 17 R141–144; 22 R145+. 08f — без R.

| # | Задача | Зависит от | Флаг | Эталон | Plan |
|---|---|---|---|---|---|
| 1 | 13a доля владения регионом | — | region_share_enabled | baseline_pre13a | plans/13a-ownership-share.plan.md |
| 2 | 15 реестр активов | — | asset_cap (по умолчанию выкл.) | baseline_pre15 | plans/15-asset-registry.plan.md |
| 3 | 14 гегемон планеты | 15 | planet_hegemon_enabled | baseline_pre14 | plans/14-planet-hegemon.plan.md |
| 4 | 08f мульти-фракционный стенд | — | нет | нет | plans/08f-multi-faction-bench.plan.md |
| 5 | 01 личное состояние именных | 21b, 21d | npc_state_enabled | baseline_pre01n | plans/01-npc-personal-state.plan.md |
| 6 | 02 репутация и узнаваемость | 21d, 08c, желательно 01 | reputation_enabled | baseline_pre02 | plans/02-reputation-recognition.plan.md |
| 7 | 03d общий регион и посланники | 02 желательно, 08c | envoys_enabled | baseline_pre03d | plans/03d-common-region-envoys.plan.md |
| 8 | 18 личная дуга | 01 | arc_enabled | baseline_pre18 | plans/18-personal-arc.plan.md |
| 9 | 09 хроника | — | нет | нет | plans/09-chronicle-summary.plan.md |
| 10 | 16a цель и этап | 21b, 21c | obj_enabled | baseline_pre16a | plans/16a-objective-stage.plan.md |
| 11 | 16b стратегия | 16a, 01 | strategy_enabled | baseline_pre16b | plans/16b-strategy-weights.plan.md |
| 12 | 16c наследование и вендетта | 16b, желательно 02 | inheritance_enabled | baseline_pre16c | plans/16c-inheritance-vendetta.plan.md |
| 13 | 17 триада | 16c, 01 | нет | нет | plans/17-triad-profiles.plan.md |
| 14 | 19 допрос (двойник) | 01, желательно 02 | interrogation_enabled | baseline_pre19 | plans/19-interrogation.plan.md |
| 15 | 10 стенд сверки озвучки | 09 | нет | нет | plans/10-llm-harness.plan.md |
| 16 | 22 мир «всё включено» | всё выше | нет | нет | plans/22-integration-world.plan.md |

Порядок — по зависимостям и по росту риска. Задачи 4, 9, 15 ничего в мир не пишут и могут идти в любой момент.

Не подготовлены намеренно: 12 и 12a — работа только в Creation Kit (фасад и вертикальный срез); двойник не утверждает ничего о Creation Kit, а подготовка таких документов выходит за правило «двойник — только двойник». Если нужна заявка и на них, это отдельное решение Стана.

## Задача 23 (добавлено 2026-10-28)
Масштаб в двойнике: выполнено 2026-10-28 (23a–23d), статус плана «утверждён». R-номера: 23a R150–R152, 23b R153–R154, 23c R155–R160, 23d R161–R162 (R163–R169 свободны). Отчёты reports/23*-report.md. Дальше заявка 24 (слой сцены, межпланетный уровень), спайки 1–3 и C++-ядро.

| # | Задача | Зависит от | Флаг | Эталон | Plan |
|---|---|---|---|---|---|
| 17 | 23a журнал в два уровня | 22 | log_two_level_enabled | baseline_pre23a | plans/23-scale.plan.md |
| 18 | 23b именные до сотен | 22 | named_max (по умолчанию 10) | baseline_pre23b | plans/23-scale.plan.md |
| 19 | 23c несколько планет, ленивые «тихие» | 23a | multi_planet_enabled | baseline_pre23c | plans/23-scale.plan.md |
| 20 | 23d снимок и эталонные миры | 23a, 23b, 23c | нет | tests/golden/ | plans/23-scale.plan.md |

## Заявки после 23 (добавлено 2026-10-28)
| # | Задача | Зависит от | Статус |
|---|---|---|---|
| 21 | 23e простая сумма вместо встроенной (intent/23e-plain-sum.md) | 23d | выполнено 2026-10-28 (reports/23e-report.md); R163–R164 |
| 22 | 24 слой сцены и межпланетный уровень (intent/24-scene-layer.md; 24a сцена в двойнике, 24b межпланетный уровень) | 23 | 24a выполнено 2026-10-28 (reports/24a-report.md; SC1–SC17, R165–R174; tests/golden пересозданы один раз); 24b не начат |
