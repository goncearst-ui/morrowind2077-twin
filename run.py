"""Прогон набора «штопор» v0 и вывод результатов: python3 run.py"""
from twin.scenarios import REVERSE, evaluate

for sc in ("DS1", "DS2", "DS4", "RG1", "RG2", "RG3", "RG4", "RG5", "OB1", "OB2", "RG6", "HD1", "HD2", "HD3", "IC1", "IC2", "IC3", "IC5", "RD1", "RD2", "RD3", "RD3S", "RD4", "RP1", "RP2", "RT1", "RT2", "RT2b", "RT3", "RT4", "RL1", "RL2", "RL3", "RL4a", "RL4b", "RL5", "RL6", "MK1", "MK2", "MK3", "MK4", "MK5", "MK6", "WR1", "WR2", "WR3", "WR4", "WR5", "WR6", "WR7a", "WR7b", "WR7c", "WR7d", "WS1", "WS2", "WS3"):
    ok, res, m, w, s = evaluate(sc)
    print(f"{sc}: {'ЗЕЛЁНЫЙ' if ok else 'КРАСНЫЙ'}")
    for name, k, det in res:
        print(f"   {'OK ' if k else 'RED'} {name} — {det}")
    for n in w.factions:
        x = m[n]
        print(f"   {n}: {x['start']}→{x['end']} чел., минимум {x['min']} на тике {x['min_tick']}, "
              f"погибло {x['dead']}, дезертировало {x['deserted']}, тиков ниже критической {x['ticks_below_critical']}")
for key, (p, scs, desc) in REVERSE.items():
    red = [sc for sc in scs if not evaluate(sc, p)[0]]
    print(f"{key} ({desc}): {'валит ' + ', '.join(red) if red else 'НЕ валит ничего — проверка слабая'}")

# spec 08c: слепые нападения в прежних сценариях при включённом знании (для отчёта, не проверка)
from dataclasses import replace
from twin.params import Params
from twin.scenarios import run

print("слепые нападения (знание включено, на старте никто ничего не знает):")
for sc in ("DS1", "DS2", "DS4", "OB1", "OB2", "IC5", "RD1", "RD3S", "RP1", "RP2", "RT1", "RT4", "RL2", "RL6"):
    w, _ = run(sc, replace(Params(), knowledge_enabled=True))
    att = [e for e in w.events if e["kind"] in ("raid_object", "assault")]
    bl = [e for e in w.events if e["kind"] == "blind_attack"]
    print(f"   {sc}: нападений {len(att)}, слепых {len(bl)} (принудительных слепых {sum(1 for e in bl if e['forced'])})")
