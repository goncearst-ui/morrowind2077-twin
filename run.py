"""Прогон набора «штопор» v0 и вывод результатов: python3 run.py"""
from twin.scenarios import REVERSE, evaluate

for sc in ("DS1", "DS2", "DS4", "RG1", "RG2", "RG3", "RG4", "RG5", "OB1", "OB2", "RG6", "HD1", "HD2", "HD3"):
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
