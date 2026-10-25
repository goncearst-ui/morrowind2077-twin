"""Набор «штопор» v0: DS1, DS2, DS4 (11 S2e) и метрики.

Стартовые значения сценариев — [предл], утверждены 2026-10-25.
Раскладка по вёдрам на старте: 30% Steady / 40% Ordinary / 30% Skittish. Armory 50. Запас на 20 суток (DS2 — на 4).
"""
from dataclasses import replace

from .model import CACHE, Faction, Site, World
from .params import Params


def split(n):
    st = round(n * 0.3)
    sk = round(n * 0.3)
    return dict(steady=st, ordinary=n - st - sk, skittish=sk)


def sites():
    return [Site("Перевал", 40, 90, 4), Site("Насосная", 15, 35, 2)]


def sites3():
    """Три объекта: третий — «Жила» (06: КоштБазы 20; доход 60, MinCrew 3 — [предл], spec 03b)."""
    return sites() + [Site("Жила", 20, 60, 3)]


def faction(world_p, name, arche, n, dos, site_cost):
    f = Faction(name, arche, supply=0.0, armory=50.0, **split(n))
    exp = (site_cost + n * world_p.per_head_cost) * world_p.archetype_cost_mult[arche]
    f.supply = exp * dos
    return f


SOLO = {  # spec 03a: (уклад, численность, объекты)
    "RG2": ("Контролёры", 60, ("Перевал",)),
    "RG3": ("Хранители", 100, ("Перевал", "Насосная")),
    "RG4": ("Контролёры", 100, ("Перевал", "Насосная")),
    "RG5": ("Хранители", 30, ()),
}


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
        a.hunger_debt = 300.0   # накопленный долг = 10 уходов; решение Стана 2026-10-25 (отчёт 00, решение 2а)
        w = World({"A": a}, ss, p)
        w.scheduled = {1: [lambda w: setattr(w.site("Перевал"), "income_disabled", True)]}
        horizon = 100
    elif sc == "DS4":
        a = faction(p, "A", "Хищники", 90, 20, 40)
        b = faction(p, "B", "Хищники", 30, 20, 15)
        ss[0].owner, ss[1].owner = "A", "B"
        w = World({"A": a, "B": b}, ss, p)
        horizon = 200
    elif sc == "RG1":
        # один клан Хищников 30 чел. без площадки, 200 тиков (spec 01)
        a = faction(p, "A", "Хищники", 30, 20, 0)
        w = World({"A": a}, ss, p)
        horizon = 200
    elif sc in ("OB1", "OB2"):
        # spec 03b: A (Хищники 90) принудительно штурмует Перевал Хранителей B на тике 5.
        # OB1: у B два объекта (Перевал со складом, Насосная), у A — «Жила». OB2: у B один объект.
        ss = sites3()
        two = sc == "OB1"
        ss[0].owner = "B"
        if two:
            ss[1].owner = "B"
        ss[2].owner = "A"
        b = faction(p, "B", "Хранители", 40 if two else 30, 20, sum(x.base_cost for x in ss if x.owner == "B"))
        a = faction(p, "A", "Хищники", 90, 20, ss[2].base_cost)
        w = World({"A": a, "B": b}, ss, p)
        w.forced_assaults = {5: [("A", "Перевал")]}
        horizon = 55
    elif sc == "RG6":
        # spec 03b: два Хищника без объектов, каждый в своём родном регионе
        a = faction(p, "A", "Хищники", 30, 20, 0)
        b = faction(p, "B", "Хищники", 30, 20, 0)
        a.home, b.home = "RA", "RB"
        w = World({"A": a, "B": b}, sites(), p)
        horizon = 200
    elif sc in SOLO:
        # spec 03a: одна фракция, без войны, 200 тиков; запас на 20 суток
        arche, n, names = SOLO[sc]
        ss = sites()
        for x in ss:
            if x.name in names:
                x.owner = "A"
        a = faction(p, "A", arche, n, 20, sum(x.base_cost for x in ss if x.name in names))
        w = World({"A": a}, ss, p)
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
    elif sc == "RG1":
        raids = [e for e in w.events if e["kind"] == "raid"]
        end_p = w.regions[w.factions["A"].home]
        res.append(("угодья выедаются: Достаток на тике 200 ниже стартового", end_p < p.region_start,
                    f"Достаток {p.region_start:.0f} → {end_p:.1f}"))
        ok = len(raids) >= 10
        first = sum(e["loot"] for e in raids[:5]) / 5 if ok else 0
        last = sum(e["loot"] for e in raids[-5:]) / 5 if ok else 0
        res.append(("добыча падает: последние 5 налётов беднее первых 5", ok and last < first,
                    f"налётов {len(raids)}; средняя добыча первых 5 — {first:.0f}, последних 5 — {last:.0f}"))
    elif sc in ("OB1", "OB2"):
        st = [e for e in w.events if e["kind"] == "depot_strike"]
        ok_strike = len(st) == 1 and st[0]["faction"] == "B" and st[0]["site"] == "Перевал"
        res.append(("удар по складу B при захвате Перевала", ok_strike, f"ударов по складу: {len(st)}"))
        if ok_strike:
            e = st[0]
            rows = {r[3]: r for r in w.log if r[6] == "DEPOT_STRIKE" and r[0] == e["tick"]}
            sup, arm = rows.get("B.supply"), rows.get("B.armory")
            if sup is None:
                res.append(("запас после удара = (1 − DepotLossRate) × до", False, "запас B при ударе не изменился"))
            else:
                res.append(("запас после удара = (1 − DepotLossRate) × до", abs(sup[5] - sup[4] * (1 - p.depot_loss_rate)) < 1e-3 and sup[4] > 0,
                            f"запас B {sup[4]:.0f} → {sup[5]:.0f}, доля потери {1 - sup[5] / sup[4]:.0%}, ожидалось {p.depot_loss_rate:.0%}"))
            if arm is None:
                res.append(("снаряжение после удара = (1 − DepotArmoryRate) × до", False, "снаряжение B при ударе не изменилось"))
            else:
                res.append(("снаряжение после удара = (1 − DepotArmoryRate) × до", abs(arm[5] - arm[4] * (1 - p.depot_armory_rate)) < 1e-3,
                            f"снаряжение B {arm[4]:.1f} → {arm[5]:.1f}"))
            mv = [r for r in w.log if r[6] == "DEPOT_MOVE" and r[3] == "B.depot"]
            want = "Насосная" if sc == "OB1" else CACHE
            res.append((f"склад переехал: {want}", len(mv) == 1 and mv[0][5] == want and mv[0][1] == 7 and mv[0][0] == e["tick"],
                        f"переездов: {len(mv)}" + (f", {mv[0][4]} → {mv[0][5]}" if mv else "")))
            idx = {r[6]: i for i, r in enumerate(w.log) if r[0] == e["tick"] and r[6] in ("DEPOT_STRIKE", "DEPOT_MOVE", "TROPHY")}
            res.append(("порядок: удар и переезд до трофея", idx.get("DEPOT_MOVE", 9e9) < idx.get("TROPHY", -1) and idx.get("DEPOT_STRIKE", 9e9) < idx.get("TROPHY", -1),
                        "строки журнала DEPOT_STRIKE, DEPOT_MOVE, затем TROPHY"))
        bser = dict(series["B"])
        if sc == "OB1":
            res.append(("B жива спустя 50 тиков после удара", bser[55] > 0, f"B на тике 55: {bser[55]} чел."))
        else:
            t0 = st[0]["tick"] if st else 0
            early = [(e["tick"], e["n"]) for e in w.events if e["kind"] == "desertion" and e["faction"] == "B" and e["tick"] <= t0 + 10]
            res.append(("люди B не дезертируют от голода в первые 10 тиков после удара (spec 03b, OB2)", not early,
                        f"удар на тике {t0}; дезертирство B в окне: " + (f"первое на тике {early[0][0]}" if early else "нет")))
    elif sc == "RG6":
        base, _ = run("RG1")
        solo_end = base.regions["common"]
        ra, rb = w.regions["RA"], w.regions["RB"]
        res.append(("налёты A не меняют регион B (Достаток как у одиночки)", abs(rb - solo_end) < 1e-6 and abs(ra - solo_end) < 1e-6,
                    f"Достаток RA {ra:.1f}, RB {rb:.1f}, одиночка (RG1) {solo_end:.1f}"))
        raids = [e for e in w.events if e["kind"] == "raid"]
        res.append(("грабили обе фракции", {e["faction"] for e in raids} == {"A", "B"}, f"налётов: {len(raids)}"))
    elif sc in SOLO:
        a, f = m["A"], w.factions["A"]
        if sc in ("RG2", "RG3"):
            res.append(("нет дезертиров при ёмкости объекта", a["deserted"] == 0, f"дезертировало {a['deserted']}, в конце {a['end']} чел."))
        if sc == "RG2":
            res.append(("запас на тике 200 не ниже порога голода", f.days_supply >= p.hunger_threshold,
                        f"запас {f.days_supply:.1f} суток, порог {p.hunger_threshold:.0f}"))
        if sc == "RG4":
            res.append(("худеют до ёмкости, но не ниже (80–90 чел.)", 80 <= a["end"] <= 90, f"в конце {a['end']} чел."))
        if sc == "RG5":
            res.append(("голод не отменён: без объектов фракция тает", a["end"] < a["start"], f"{a['start']} → {a['end']} чел."))
    return res, m


def evaluate(sc: str, p: Params | None = None):
    w, series = run(sc, p)
    res, m = check(sc, w, series)
    return all(ok for _, ok, _ in res), res, m, w, series


REVERSE = {
    "R1": (replace(Params(), old_loss_formula=True), ("DS1", "DS4"), "старая формула потерь 13 (половина всей фракции)"),
    "R2": (replace(Params(), desertion_cap_per_tick=None), ("DS2",), "без потолка дезертирства за тик"),
    "R3": (replace(Params(), worker_yield=0.0), ("RG2",), "доход за работника 0 (как до 03a)"),
    "R4": (replace(Params(), depot_loss_rate=0.0), ("OB1",), "удар по складу ничего не уничтожает (DepotLossRate 0)"),
}
