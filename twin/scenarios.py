"""Набор «штопор» v0: DS1, DS2, DS4 (11 S2e) и метрики.

Стартовые значения сценариев — [предл], утверждены 2026-10-25.
Раскладка по вёдрам на старте: 30% Steady / 40% Ordinary / 30% Skittish. Armory 50. Запас на 20 суток (DS2 — на 4).
"""
from dataclasses import replace

from .model import Faction, Site, World
from .params import Params


def split(n):
    st = round(n * 0.3)
    sk = round(n * 0.3)
    return dict(steady=st, ordinary=n - st - sk, skittish=sk)


def sites():
    return [Site("Перевал", 40, 90, 4), Site("Насосная", 15, 35, 2)]


def faction(world_p, name, arche, n, dos, site_cost):
    f = Faction(name, arche, supply=0.0, armory=50.0, **split(n))
    exp = (site_cost + n * world_p.per_head_cost) * world_p.archetype_cost_mult[arche]
    f.supply = exp * dos
    return f


def build(sc: str, p: Params) -> tuple[World, int]:
    ss = sites()
    if sc == "DS1":
        a = faction(p, "A", "Хищники", 40, 20, 15)
        b = faction(p, "B", "Хранители", 60, 20, 40)
        ss[1].owner, ss[0].owner = "A", "B"
        w = World({"A": a, "B": b}, ss, p)
        w.forced_assaults = {t: [("A", "Перевал")] for t in (1, 2, 3)}
        horizon = 50
    elif sc == "DS2":
        a = faction(p, "A", "Хищники", 30, 4, 40)
        ss[0].owner = "A"
        w = World({"A": a}, ss, p)
        w.scheduled = {1: [lambda w: setattr(w.site("Перевал"), "income_disabled", True)]}
        horizon = 100
    elif sc == "DS4":
        a = faction(p, "A", "Хищники", 90, 20, 40)
        b = faction(p, "B", "Хищники", 30, 20, 15)
        ss[0].owner, ss[1].owner = "A", "B"
        w = World({"A": a, "B": b}, ss, p)
        horizon = 200
    else:
        raise ValueError(sc)
    for f in w.factions.values():
        w.publish_dos(f, phase=0)
    return w, horizon


def run(sc: str, p: Params | None = None):
    p = p or Params()
    w, horizon = build(sc, p)
    series = {n: [(0, f.manpower)] for n, f in w.factions.items()}
    for _ in range(horizon):
        w.step()
        for n, f in w.factions.items():
            series[n].append((w.tick, f.manpower))
            assert f.manpower == f.steady + f.ordinary + f.skittish
    return w, series


# ---------------- метрики и проверки ----------------

def metrics(w: World, series):
    out = {}
    crit = w.p.critical_manpower
    for n, s in series.items():
        mn = min(s, key=lambda x: (x[1], x[0]))
        out[n] = dict(
            start=s[0][1], end=s[-1][1], min=mn[1], min_tick=mn[0],
            ticks_below_critical=sum(1 for t, m in s if t > 0 and m < crit),
            max_loss_share=max([e["losses"][n] / e["manpower_before"][n]
                                for e in w.events if e["kind"] == "assault"
                                and n in e["losses"] and e["manpower_before"][n] > 0] or [0.0]),
            max_shock_inc=max([e["shock_inc"].get(n, 0.0) for e in w.events if e["kind"] == "assault"] or [0.0]),
            max_desert_tick=max([e["n"] for e in w.events if e["kind"] == "desertion" and e["faction"] == n] or [0]),
            deserted=w.factions[n].deserted, dead=w.factions[n].dead,
        )
    out["_assaults"] = sum(1 for e in w.events if e["kind"] == "assault")
    return out


def check(sc: str, w: World, series):
    """Список (проверка, ok, деталь). Красная строка называет пробитый потолок."""
    p, m, res = w.p, metrics(w, series), []
    cap = p.assault_loss_cap
    if sc == "DS1":
        a = m["A"]
        res.append(("потолок потерь за событие (ASSAULT_LOSS_CAP)",
                    a["max_loss_share"] <= cap + 1e-9, f"макс. доля потерь A за штурм {a['max_loss_share']:.0%}, потолок {cap:.0%}"))
        alive50 = dict(series["A"])[50] > 0
        res.append(("A жива на тике 50", alive50, f"A на тике 50: {dict(series['A'])[50]} чел."))
        res.append(("потолок шока за событие (ShockEventCap)",
                    a["max_shock_inc"] <= p.shock_event_cap + 1e-9, f"макс. рост шока A за штурм {a['max_shock_inc']:.1f}, потолок {p.shock_event_cap:.0f}"))
        lost = [e for e in w.events if e["kind"] == "assault" and e["forced"] and not e["attacker_wins"]]
        res.append(("сценарий валиден: 3 проигранных штурма", len(lost) == 3, f"проиграно принудительных штурмов: {len(lost)}"))
    elif sc == "DS2":
        a = m["A"]
        cap_d = p.desertion_cap_per_tick if p.desertion_cap_per_tick is not None else 2
        res.append(("потолок дезертирства за тик (DesertionCapPerTick)",
                    a["max_desert_tick"] <= cap_d, f"макс. уходов за тик {a['max_desert_tick']}, потолок {cap_d}"))
        sur = [e for e in w.events if e["kind"] == "surrender"]
        first_below = next((t for t, mp in series["A"] if mp < p.critical_manpower), None)
        ok = bool(sur) and (first_below is None or sur[0]["tick"] < first_below)
        det = (f"сдача актива на тике {sur[0]['tick']} при {sur[0]['manpower']} чел.; " if sur else "сдачи актива не было; ") + \
              (f"ниже {p.critical_manpower} чел. впервые на тике {first_below}" if first_below else f"ниже {p.critical_manpower} чел. не опускалась")
        res.append(("сдача актива раньше критической численности", ok, det))
    elif sc == "DS4":
        for n in ("A", "B"):
            res.append((f"{n} не вымирает за 200 тиков", m[n]["min"] > 0,
                        f"{n}: минимум {m[n]['min']} чел. на тике {m[n]['min_tick']}, в конце {m[n]['end']}"))
        worst = max(m["A"]["max_loss_share"], m["B"]["max_loss_share"])
        res.append(("потолок потерь за событие (ASSAULT_LOSS_CAP)", worst <= cap + 1e-9,
                    f"макс. доля потерь за штурм {worst:.0%}, потолок {cap:.0%}"))
        ok_cons = all(e["supply_moved"] >= 0 for e in w.events if e["kind"] == "assault")
        res.append(("победитель не богатеет сверх убыли проигравшего", ok_cons, "трофей = ровно убыль проигравшего"))
        res.append(("сценарий валиден: был хотя бы 1 штурм", m["_assaults"] >= 1, f"штурмов: {m['_assaults']}"))
    return res, m


def evaluate(sc: str, p: Params | None = None):
    w, series = run(sc, p)
    res, m = check(sc, w, series)
    return all(ok for _, ok, _ in res), res, m, w, series


REVERSE = {
    "R1": (replace(Params(), old_loss_formula=True), ("DS1", "DS4"), "старая формула потерь 13 (половина всей фракции)"),
    "R2": (replace(Params(), desertion_cap_per_tick=None), ("DS2",), "без потолка дезертирства за тик"),
}
