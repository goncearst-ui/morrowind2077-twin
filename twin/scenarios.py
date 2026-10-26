"""Набор «штопор» v0: DS1, DS2, DS4 (11 S2e) и метрики.

Стартовые значения сценариев — [предл], утверждены 2026-10-25.
Раскладка по вёдрам на старте: 30% Steady / 40% Ordinary / 30% Skittish. Armory 50. Запас на 20 суток (DS2 — на 4).
"""
from dataclasses import replace

from .model import BUCKETS_OUT, CACHE, Faction, Site, World
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
    "HD2": ("Контролёры", 100, ("Перевал", "Насосная")),   # spec 05: то же, что RG4, критерии про решения
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
    elif sc in ("DS4", "IC5"):
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
    elif sc in ("RD1", "RD2", "RD3", "RD3S", "RD4"):
        # spec 03c: принудительный налёт A (Хищники 90) на объект B на тике 5; автономные налёты и каналы выключены для чистоты
        p = replace(p, object_raids_enabled=False, smuggling_enabled=False, fees_enabled=False,
                    prisoner_sale_enabled=False, decisions_enabled=False)
        ss = sites()
        if sc == "RD1":
            ss[1].owner = "B"
            b = faction(p, "B", "Хранители", 30, 2, 15)      # запас мал: добыча ограничена запасом
            target = "Насосная"
        else:
            ss[0].owner = "B"
            b = faction(p, "B", "Хищники" if sc == "RD3S" else "Хранители", 60, 20, 40)
            target = "Перевал"
        a = faction(p, "A", "Хищники", 90, 20, 0)
        if sc in ("RD3", "RD3S"):
            a.morale = 20.0                                   # ниже порога «несём своих»
        w = World({"A": a, "B": b}, ss, p)
        w.forced_raids = {5: [("A", target)]}
        horizon = 30
    elif sc in ("RP1", "RP2"):
        # spec 07: один клан Хищников 30 на одном регионе, 200 тиков; каналы и налёты на объект выключены, решения 05 включены
        p = replace(p, smuggling_enabled=False, fees_enabled=False, object_raids_enabled=False)
        a = faction(p, "A", "Хищники", 30, 20, 0)
        w = World({"A": a}, ss, p)
        horizon = 200
    elif sc in ("RT1", "RT2", "RT2R", "RT2b", "RT3", "RT4"):
        # spec 04: ярусы. Чистая обстановка: каналы, решения и налёты на объект выключены; налёты на регион только в RT4
        p = replace(p, smuggling_enabled=False, fees_enabled=False, object_raids_enabled=False,
                    decisions_enabled=False, prisoner_sale_enabled=False, raids_enabled=(sc == "RT4"))
        if sc == "RT1":
            a = faction(p, "A", "Хищники", 90, 20, 0)
            b = faction(p, "B", "Хранители", 60, 20, 0)
            w = World({"A": a, "B": b}, ss, p)
            horizon = 3
        elif sc in ("RT2", "RT2R", "RT2b"):
            a = faction(p, "A", "Хранители", 90, 200, 0)
            w = World({"A": a}, ss, p)
            tier, k = {"RT2": ("off", 3), "RT2R": ("rank", 3), "RT2b": ("off", 6)}[sc]

            def strike(w, tier=tier, k=k):
                f = w.factions["A"]
                w.kill_tier(f, k, tier)
                w.events.append(dict(kind="probe", tick=w.tick, power=w.power(f), off=f.off, manpower=f.manpower))
            w.scheduled = {1: [strike]}
            horizon = 15
        elif sc == "RT3":
            a = faction(p, "A", "Хищники", 60, 20, 0)
            w = World({"A": a}, ss, p)
            horizon = 25
        else:
            a = faction(p, "A", "Хищники", 90, 20, 0)
            w = World({"A": a}, ss, p)
            horizon = 1
    elif sc in ("IC1", "IC2"):
        # spec 06: Дрейфующие 30 без объектов, 200 тиков (контрабанда: потолок рынка, Heat)
        a = faction(p, "A", "Дрейфующие", 30, 20, 0)
        w = World({"A": a}, ss, p)
        horizon = 200
    elif sc == "IC3":
        # spec 06: Хранители и Контролёры без объектов, у каждого свой родной регион — каналы им закрыты
        a = faction(p, "A", "Хранители", 30, 20, 0)
        b = faction(p, "B", "Контролёры", 30, 20, 0)
        a.home, b.home = "RA", "RB"
        w = World({"A": a, "B": b}, ss, p)
        horizon = 100
    elif sc == "HD1":
        # spec 05: Хищники 60 на Насосной, без войны, 100 тиков
        ss[1].owner = "A"
        a = faction(p, "A", "Хищники", 60, 20, 15)
        w = World({"A": a}, ss, p)
        horizon = 100
    elif sc == "HD3":
        # spec 05: Хранители 100 теряют доход Перевала (как DS2), запас на 4 суток, 100 тиков
        ss[0].owner = "A"
        a = faction(p, "A", "Хранители", 100, 4, 40)
        w = World({"A": a}, ss, p)
        w.scheduled = {1: [lambda w: setattr(w.site("Перевал"), "income_disabled", True)]}
        horizon = 100
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
            if w.p.tiers_enabled:   # RT5: сумма ярусов = Manpower, ярусы раненых = раненые (spec 04)
                assert f.rank + f.vet + f.off == f.manpower, f"{n}: ярусы {f.rank}+{f.vet}+{f.off} != Manpower {f.manpower} на тике {w.tick}"
                assert sum(sum(e[3]) for e in f.wounded_queue) == f.wounded, f"{n}: ярусы раненых != раненые на тике {w.tick}"
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
    elif sc == "RP1":
        A = w.factions["A"]
        res.append(("потолок прокорма: на тике 200 людей от 5 до 10", 5 <= A.manpower <= 10, f"людей {A.manpower}"))
        res.append(("угодья выедены: Достаток региона ниже стартового", w.regions[A.home] < w.p.region_start, f"Достаток {w.regions[A.home]:.0f} при старте {w.p.region_start:.0f}"))
    elif sc == "RP2":
        base = [list(r) for r in w.log]
        res.append(("у каждого налёта party = min(Manpower, strike_group_max)",
                    all(e["party"] == min(e["manpower"], w.p.strike_group_max) for e in w.events if e["kind"] == "raid") and any(e["kind"] == "raid" for e in w.events),
                    f"налётов {sum(1 for e in w.events if e['kind'] == 'raid')}"))
        for g in (3, 1):
            w2, _ = run("RP2", replace(w.p, strike_group_max=g))
            res.append((f"журнал состояний при strike_group_max {g} совпадает с журналом при {w.p.strike_group_max}",
                        [list(r) for r in w2.log] == base and all(e["party"] == min(e["manpower"], g) for e in w2.events if e["kind"] == "raid"),
                        f"строк {len(w2.log)} против {len(base)}"))
    elif sc == "RT1":
        d0 = Params()
        w0, _ = build("RT1", p)
        for n, want in (("A", (63, 18, 9)), ("B", (42, 12, 6))):
            f = w0.factions[n]
            res.append((f"{n}: состав 70/20/10 и сумма = Manpower", (f.rank, f.vet, f.off) == want and f.rank + f.vet + f.off == f.manpower,
                        f"{f.rank}/{f.vet}/{f.off} из {f.manpower}"))
            old = w0.fighters(f) * (0.5 + f.armory / 100) * (0.6 + 0.8 * f.steadfast(p) / 100)
            res.append((f"{n}: сила равна прежней формуле", abs(w0.power(f) - old) < 1e-9, f"{w0.power(f):.3f} против {old:.3f}"))
    elif sc == "RT2":
        d0 = Params()
        pr = next(e for e in w.events if e["kind"] == "probe")
        wr, _ = run("RT2R", p)
        pr_r = next(e for e in wr.events if e["kind"] == "probe")
        res.append(("сила после гибели 3 офицеров ниже, чем после 3 рядовых", pr["power"] < pr_r["power"] - 1e-9,
                    f"{pr['power']:.2f} против {pr_r['power']:.2f}"))
        rows = [r for r in w.log if r[3] == "A.off" and r[6] == "REORG"]
        want_tick = 1 + d0.reorg_ticks
        res.append((f"офицеры восстановлены повышением через {d0.reorg_ticks} тиков", bool(rows) and rows[0][0] == want_tick and rows[0][5] == 8,
                    "повышение на тике " + (f"{rows[0][0]} (офицеров {rows[0][4]} → {rows[0][5]})" if rows else "—")))
    elif sc == "RT2b":
        d0 = Params()
        rows = [r for r in w.log if r[3] == "A.off" and r[6] == "REORG"]
        want_tick = 1 + d0.reorg_ticks_urgent
        res.append((f"заполнено меньше 50%: срочная реорганизация через {d0.reorg_ticks_urgent} тика", bool(rows) and rows[0][0] == want_tick and rows[0][5] == 8,
                    "повышение на тике " + (f"{rows[0][0]} (офицеров {rows[0][4]} → {rows[0][5]})" if rows else "—")))
    elif sc == "RT3":
        d0 = Params()
        first = {t: next((r[0] for r in w.log if r[3] == f"A.underpaid.{t}" and r[5] == 1), None) for t in ("rank", "vet", "off")}
        res.append(("недоплата: рядовые на тике 11, ветераны на 16, офицеры не раньше 26",
                    first["rank"] == d0.underpay_ticks[0] + 1 and first["vet"] == d0.underpay_ticks[1] + 1 and (first["off"] is None or first["off"] >= d0.underpay_ticks[2] + 1),
                    f"рядовые {first['rank']}, ветераны {first['vet']}, офицеры {first['off']}"))
        mrows = [r for r in w.log if r[3] == "A.morale" and r[6] == "UNDERPAY"]
        res.append(("мораль падает от недоплаты", bool(mrows) and all(r[5] < r[4] for r in mrows) and mrows[0][0] == first["rank"],
                    f"строк UNDERPAY по морали {len(mrows)}" + (f", первая на тике {mrows[0][0]}" if mrows else "")))
        des = next((r[0] for r in w.log if r[6] == "DESERTION" and r[3] == "A.deserted"), None)
        tr = {t: [r for r in w.log if r[0] == des and r[3] == f"A.{t}" and r[6] == "TIER"] for t in ("rank", "vet", "off")}
        res.append(("первый дезертир — из рядовых", des is not None and bool(tr["rank"]) and not tr["vet"] and not tr["off"],
                    f"дезертирство на тике {des}; строки ярусов: рядовые {len(tr['rank'])}, ветераны {len(tr['vet'])}, офицеры {len(tr['off'])}"))
    elif sc == "RT4":
        ev = next(e for e in w.events if e["kind"] == "raid")
        f0 = w.factions["A"]
        heads = {"rank": 63, "vet": 18, "off": 9}
        def pays(world):
            return {t: next((r[5] - r[4] for r in world.log if r[3] == f"A.paid.{t}"), 0.0) for t in heads}
        pa = pays(w)
        ph = {t: pa[t] / heads[t] for t in heads}
        res.append(("выплата на человека 1 : 2 : 4", ph["rank"] > 0 and abs(ph["vet"] / ph["rank"] - 2) < 1e-6 and abs(ph["off"] / ph["rank"] - 4) < 1e-6,
                    f"на человека: рядовой {ph['rank']:.3f}, ветеран {ph['vet']:.3f}, офицер {ph['off']:.3f}"))
        share = p.share_rate["Хищники"]
        res.append(("сумма выплат = добыча × ShareRate", abs(sum(pa.values()) - ev["loot"] * share) < 1e-6, f"{sum(pa.values()):.2f} против {ev['loot'] * share:.2f}"))
        w2, _ = run("RT4", replace(p, share_rate=dict(p.share_rate, Хищники=0.10)))
        ph2 = {t: pays(w2)[t] / heads[t] for t in heads}
        drop = {t: ph[t] - ph2[t] for t in heads}
        res.append(("при доле 0.10 вместо 0.35 выплата на человека падает у всех, у офицеров сильнее, чем у ветеранов, у ветеранов сильнее, чем у рядовых",
                    0 < drop["rank"] < drop["vet"] < drop["off"], f"падение на человека: рядовой {drop['rank']:.2f}, ветеран {drop['vet']:.2f}, офицер {drop['off']:.2f}"))
    elif sc in ("RD1", "RD2", "RD3", "RD3S", "RD4"):
        ev = next(e for e in w.events if e["kind"] == "raid_object" and e["forced"])
        A, B = w.factions["A"], w.factions["B"]
        load = p.wounded_load * p.carry_unit
        if sc == "RD1":
            res.append(("сценарий валиден: налётчики победили без потерь", ev["attacker_wins"] and ev["casualties"]["A"] == 0 and ev["stock"] < ev["capacity"],
                        f"потери A {ev['casualties']['A']}, запас цели {ev['stock']:.0f}, ёмкость {ev['capacity']:.0f}"))
            res.append(("добыча = min(запас объекта, ёмкость)", abs(ev["loot"] - min(ev["stock"], ev["capacity"])) < 1e-6, f"добыча {ev['loot']:.0f}"))
            row = next((r for r in w.log if r[6] == "RAID_OBJECT" and r[3] == "B.supply"), None)
            res.append(("запас обороны убыл ровно на добычу", row is not None and abs((row[4] - row[5]) - ev["loot"]) < 1e-3,
                        f"запас B {row[4]:.0f} → {row[5]:.0f}" if row else "строки нет"))
        elif sc == "RD2":
            res.append(("сценарий валиден: у налётчиков есть раненые, мораль ≥ порога", ev["wounded"] > 0 and ev["morale_high"], f"раненых {ev['wounded']}, мораль высокая: {ev['morale_high']}"))
            res.append(("раненых несут всех, брошенных нет", ev["carried"] == ev["wounded"] and ev["abandoned"] == 0 and A.captured == 0 and A.sold == 0,
                        f"унесено {ev['carried']} из {ev['wounded']}, брошено {ev['abandoned']}, пленных {A.captured + A.sold}"))
            res.append(("добыча = min(запас, ёмкость − место под раненых)", abs(ev["loot"] - min(ev["stock"], ev["capacity"] - ev["carried"] * load)) < 1e-6, f"добыча {ev['loot']:.0f}"))
            w2, _ = run("RD3", p)
            lo = next(e for e in w2.events if e["kind"] == "raid_object")
            res.append(("добыча меньше, чем у низкоморальной группы", ev["loot"] < lo["loot"], f"{ev['loot']:.0f} против {lo['loot']:.0f}"))
        elif sc in ("RD3", "RD3S"):
            res.append(("сценарий валиден: мораль ниже порога, раненые есть", (not ev["morale_high"]) and ev["wounded"] > 0, f"мораль высокая: {ev['morale_high']}, раненых {ev['wounded']}"))
            res.append(("добыча = min(запас, ёмкость), раненые брошены", abs(ev["loot"] - min(ev["stock"], ev["capacity"])) < 1e-6 and ev["abandoned"] > 0,
                        f"добыча {ev['loot']:.0f}, брошено {ev['abandoned']}"))
            if sc == "RD3":
                res.append(("пленит Хранитель: люди приняты в skittish обороны", ev["fate"] == "absorbed" and B.absorbed == ev["abandoned"] and A.captured == ev["abandoned"] and B.sold == 0 and A.sold == 0,
                            f"судьба {ev['fate']}, принято {B.absorbed}, захвачено у A {A.captured}"))
                w2, _ = run("RD2", p)
                hi = next(e for e in w2.events if e["kind"] == "raid_object")
                res.append(("добыча больше, чем у высокоморальной группы", ev["loot"] > hi["loot"], f"{ev['loot']:.0f} против {hi['loot']:.0f}"))
            else:
                res.append(("пленит Хищник: люди проданы", ev["fate"] == "sold" and A.sold == ev["abandoned"] and A.captured == 0 and B.absorbed == 0,
                            f"судьба {ev['fate']}, продано {A.sold}"))
                row = next((r for r in w.log if r[6] == "PRISONER_SALE" and r[3] == "B.supply"), None)
                res.append(("продавцу идёт цена за каждого", row is not None and abs((row[5] - row[4]) - p.prisoner_price * ev["abandoned"]) < 1e-3,
                            f"+{row[5] - row[4]:.0f} запаса" if row else "строки нет"))
            mrow = next((r for r in w.log if r[6] == "ABANDON" and r[3] == "A.morale"), None)
            res.append(("мораль налётчиков упала за каждого брошенного",
                        mrow is not None and abs((mrow[4] - mrow[5]) - min(mrow[4], p.abandon_morale_cost * ev["abandoned"])) < 1e-9,
                        f"мораль A {mrow[4]:.1f} → {mrow[5]:.1f} за {ev['abandoned']} брошенных" if mrow else "строки нет"))
        else:
            mp = dict(series["A"])
            t0 = ev["tick"]
            res.append(("сценарий валиден: раненый унесён", ev["wounded"] > 0 and ev["carried"] > 0, f"раненых {ev['wounded']}, унесено {ev['carried']}"))
            res.append(("раненые не входят в Manpower", mp[t0 + 1] == mp[t0 - 1] - ev["casualties"]["A"], f"Manpower A: {mp[t0 - 1]} → {mp[t0 + 1]}, выбыло {ev['casualties']['A']}"))
            rec = [r for r in w.log if r[6] == "RECOVERY" and r[3] == "A.wounded"]
            res.append(("возвращаются ровно через recovery_ticks", bool(rec) and rec[0][0] == t0 + p.recovery_ticks, "возврат на тике " + (str(rec[0][0]) if rec else "—")))
            res.append(("вернулись в Manpower, ведро пусто", mp[t0 + p.recovery_ticks] == mp[t0 + p.recovery_ticks - 1] + ev["carried"] and A.wounded == 0,
                        f"Manpower {mp[t0 + p.recovery_ticks - 1]} → {mp[t0 + p.recovery_ticks]}, раненых в конце {A.wounded}"))
            e0 = w.expense(A)
            A.wounded += 1
            e1 = w.expense(A)
            A.wounded -= 1
            want = p.per_head_cost * p.archetype_cost_mult[A.archetype]
            res.append(("раненый ест", abs((e1 - e0) - want) < 1e-9, f"+{e1 - e0:.2f} расхода за раненого, ожидалось {want:.2f}"))
    elif sc in ("IC1", "IC2"):
        rows = [r for r in w.log if r[6] == "SMUGGLING" and r[3] == "A.supply"]
        mp = dict(series["A"])
        cap0 = Params().market_cap   # потолок из спецификации, а не из проверяемых параметров (иначе R7 не заметит)
        if sc == "IC1":
            res.append(("сценарий валиден: контрабанда была", len(rows) > 0, f"сделок {len(rows)}"))
            over = [r for r in rows if r[5] - r[4] > cap0 + 1e-6]
            res.append(("доход за тик не выше потолка рынка", not over, f"макс. доход за тик {max([r[5] - r[4] for r in rows] or [0]):.1f}, потолок {cap0:.0f}"))
            bad = [r for r in rows if abs((r[5] - r[4]) - min(p.smuggling_yield * min(mp[r[0] - 1], p.smuggling_cap_people), cap0)) > 1e-3]
            res.append(("доход = ставка × занятые до потолка", not bad, f"расхождений {len(bad)} из {len(rows)}"))
            few = [r for r in rows if mp[r[0] - 1] < 3]
            res.append(("при нуле свободных людей дохода нет", not few, f"сделок при < 3 людях: {len(few)}"))
        else:
            busts = [e for e in w.events if e["kind"] == "bust"]
            res.append(("сценарий валиден: был срыв", len(busts) > 0, f"срывов {len(busts)}"))
            heat = [r for r in w.log if r[3] == "A.heat"]
            inc_ticks = {r[0] for r in rows}
            up_bad = [r for r in heat if r[5] > r[4] and not (r[6] == "SMUGGLING" and r[0] in inc_ticks)]
            down_bad = [r for r in heat if r[5] < r[4] and r[6] not in ("HEAT_DECAY", "BUST")]
            res.append(("Heat растёт только от дохода и спадает сам", not up_bad and not down_bad,
                        f"нарушений роста {len(up_bad)}, спада {len(down_bad)}"))
            bust_ticks = {e["tick"] for e in busts}
            final = {}   # Heat к концу расчёта тика, до сброса срывом
            for r in heat:
                if r[6] != "BUST":
                    final[r[0]] = r[5]
            at_thr = {t for t, v in final.items() if v >= p.heat_threshold}
            res.append(("срыв строго на пороге: тик с Heat ≥ порога — срыв, и наоборот",
                        at_thr == bust_ticks, f"тиков на пороге {len(at_thr)}, срывов {len(bust_ticks)}"))
            res.append(("срыв стоит людей: задержанные = сумма срывов", w.factions["A"].detained == sum(e["n"] for e in busts),
                        f"задержано {w.factions['A'].detained}"))
    elif sc == "IC3":
        for n, kind in (("A", "SMUGGLING"), ("B", "SMUGGLING"), ("A", "PROTECTION_FEE"), ("B", "PROTECTION_FEE")):
            got = [r for r in w.log if r[6] == kind and r[3].startswith(n + ".")]
            who = "Хранители" if n == "A" else "Контролёры"
            res.append((f"{who}: нет строк {kind}", not got, f"строк {len(got)}"))
    elif sc == "IC5":
        from dataclasses import replace as _r
        base_p = _r(p, smuggling_enabled=False, fees_enabled=False, prisoner_sale_enabled=False)
        wb, sb = run("DS4", base_p)
        def death(s):
            return next((t for t, mp in s if mp == 0), None)
        d_base, d_with = death(sb["B"]), death(series["B"])
        ok = d_base is not None and (d_with is None or d_with > d_base)
        res.append(("B живёт дольше, чем без каналов", ok,
                    f"без каналов B вымирает на тике {d_base}; с каналами: " + (f"на тике {d_with}" if d_with else f"жива, {series['B'][-1][1]} чел.")))
    elif sc in ("HD1", "HD2", "HD3"):
        f = w.factions["A"]
        exp_rows = [r for r in w.log if r[6] == "EXPEL" and r[3] == "A.expelled"]
        forced_ticks = {r[0] for r in w.log if r[6] == "FORCED_LABOR" and r[3] == "A.supply"}
        if sc == "HD1":
            des = [r[0] for r in w.log if r[6] == "DESERTION" and r[3] == "A.deserted"]
            res.append(("изгнанные есть", f.expelled > 0, f"изгнано {f.expelled}"))
            first_e = exp_rows[0][0] if exp_rows else None
            ok = first_e is not None and (not des or first_e <= des[0])
            res.append(("первое изгнание не позже первого дезертирства", ok,
                        f"изгнание: тик {first_e}, дезертирство: " + (f"тик {des[0]}" if des else "не было")))
            tot = f.manpower + sum(getattr(f, b) for b in BUCKETS_OUT)
            res.append(("изгнанные взяты из живых: люди сохранены", tot == m["A"]["start"], f"{tot} из {m['A']['start']}"))
        elif sc == "HD2":
            res.append(("нет дезертиров", f.deserted == 0, f"дезертировало {f.deserted}"))
            res.append(("принуждение работало не меньше 10 тиков", len(forced_ticks) >= 10, f"тиков с принуждением {len(forced_ticks)}"))
            res.append(("цена видна: мораль ниже порога решения", f.morale < p.decision_morale_threshold,
                        f"мораль {f.morale:.1f}, порог {p.decision_morale_threshold:.0f}"))
        else:
            res.append(("Хранители не изгоняют", f.expelled == 0, f"изгнано {f.expelled}"))
            res.append(("Хранители не принуждают", not forced_ticks and not f.forced_mode, f"тиков с принуждением {len(forced_ticks)}"))
    elif sc in SOLO:
        a, f = m["A"], w.factions["A"]
        if sc in ("RG2", "RG3"):
            res.append(("нет дезертиров при ёмкости объекта", a["deserted"] == 0, f"дезертировало {a['deserted']}, в конце {a['end']} чел."))
        if sc == "RG2":
            res.append(("запас на тике 200 не ниже порога голода", f.days_supply >= p.hunger_threshold,
                        f"запас {f.days_supply:.1f} суток, порог {p.hunger_threshold:.0f}"))
        if sc == "RG4":
            res.append(("люди не худеют (≥ 95), цена видна в морали (< порога решения)",
                        a["end"] >= 95 and f.morale < p.decision_morale_threshold,
                        f"в конце {a['end']} чел., мораль {f.morale:.1f}, порог {p.decision_morale_threshold:.0f}"))
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
    "R5": (replace(Params(), decisions_enabled=False), ("HD1",), "решения при голоде выключены"),
    "R7": (replace(Params(), market_cap=1e9), ("IC1",), "потолок внешнего рынка выключен"),
    "R8": (replace(Params(), heat_per_income=0.0), ("IC2",), "Heat не растёт (внимание выключено)"),
    "R9": (replace(Params(), wounded_share=0.0), ("RD2",), "раненых нет: все выбывшие гибнут"),
    "R10": (replace(Params(), carry_morale_threshold=0.0), ("RD3",), "порядок «что несут» не зависит от морали (всегда высокая)"),
    "R11": (replace(Params(), region_recovery=3.0), ("RP1",), "восстановление региона 3.0: угодья не выедаются, потолок вдвое выше"),
    "R6": (replace(Params(), peaceful_decide=("Хищники", "Контролёры", "Хранители")), ("HD3",), "Хранители принимают решения как Хищники"),
    "R12": (replace(Params(), tier_power_weight=(1.0, 1.0, 1.0)), ("RT2",), "веса силы по ярусам 1 / 1 / 1"),
    "R13": (replace(Params(), underpay_morale=0.0), ("RT3",), "недоплата не роняет мораль"),
    "R14": (replace(Params(), tier_pay_weight=(1.0, 1.0, 1.0)), ("RT4",), "веса выплаты по ярусам 1 / 1 / 1"),
    "R15": (replace(Params(), reorg_ticks_urgent=10), ("RT2b",), "срочной реорганизации нет (3 тика заменены на 10)"),
}
