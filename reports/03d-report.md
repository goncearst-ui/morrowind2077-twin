# Отчёт 03d: общий регион и представители

Дата: 2026-10-27. Plan: plans/03d-common-region-envoys.plan.md. Spec: specs/03d-common-region-envoys.spec.md.
Результат: `python3 -m pytest` — 2183 passed, красных нет.

## Что сделано
- Представитель у каждой фракции (World.envoys, регион «hub», вне Manpower и вне ростера), доска слухов хаба с задержкой 3 тика (только при живом представителе), убийство представителя через 02 (инцидент envoy_killed), действие frame: подстава в маске даёт +5 к H через общий потолок 21d, без маски — frame_exposed и штраф по 02; отказы NO_ENVOY, SAME, NO_FACTION.
- envoys_enabled по умолчанию False (требует reputation_enabled, player_levers_enabled, leader_enabled); журналы 179 сценариев совпадают с tests/baseline_pre03d.json; frame без выключателя — ValueError (отдельный тест).
- ED1–ED9 (ED5b — подстава после подкупа до общего потолка) зелёные; R97–R102 каждая валит свой сценарий.

## Допущения
Хаб не входит в regions (без экономики и без строк восстановления региона); «Contested» из hegemon_change на доску не идёт.
