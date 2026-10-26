"""Набор «штопор» v0: DS1, DS2, DS4 (11 S2e) и метрики.

Стартовые значения сценариев — [предл], утверждены 2026-10-25.
Раскладка по вёдрам на старте: 30% Steady / 40% Ordinary / 30% Skittish. Armory 50. Запас на 20 суток (DS2 — на 4).
"""
from dataclasses import replace
from math import floor

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


# spec 08e: старые значения 08b закреплены в WR и WS, чтобы их критерии не менялись; подставляются, только если параметр равен новому значению по умолчанию
OLD_WAR = dict(war_chance_base=4.0, war_chance_slope=3.0, war_chance_cap=15.0, war_truce=4, war_max_days=20,
               war_cost=5.0, war_cost_share_of_expense=False, war_reparation_share=0.0)


def pin_old_war(p, only=None):
    d = Params()
    return replace(p, **{k: v for k, v in OLD_WAR.items() if (only is None or k in only) and getattr(p, k) == getattr(d, k)})


RL_SCENARIOS = ("RL1", "RL2", "RL3", "RL4a", "RL4b", "RL5", "RL6")
MK_SCENARIOS = ("MK1", "MK2", "MK3", "MK4", "MK5", "MK6")
WS_SCENARIOS = ("WS1", "WS2", "WS3")
# spec 08e: сценарии WE строятся на обстановке WR; WE_PINS — какие старые значения закреплены (остальные новые)
WE_BASE = {"WE1": "WR1", "WE2": "WR5", "WE3a": "WR7a", "WE3b": "WR7b", "WE3c": "WR7c", "WE3d": "WR6", "WE3e": "WR7d"}
_CH = ("war_chance_base", "war_chance_slope", "war_chance_cap")
WE_PINS = {"WE1": (), "WE2": _CH, "WE3a": _CH, "WE3b": _CH, "WE3c": _CH, "WE3d": _CH + ("war_max_days",), "WE3e": _CH}
WE_SCENARIOS = tuple(WE_BASE)
WR_SCENARIOS = ("WR1", "WR2", "WR3", "WR4", "WR5", "WR6", "WR7a", "WR7b", "WR7c", "WR7d")


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
    elif sc in RL_SCENARIOS:
        # spec 08a: чистая обстановка как у RD и RT, отношения включены; налёты и штурмы только принудительные
        p = replace(p, object_raids_enabled=False, smuggling_enabled=False, fees_enabled=False,
                    prisoner_sale_enabled=False, decisions_enabled=False, relations_enabled=True,
                    archetype_assault_threshold={})   # автономных штурмов нет, только принудительные
        if sc == "RL1":
            # по две фракции на каждый уклад: 16 ячеек таблицы 08, включая диагональ
            fs = {}
            for arche, pre in (("Хранители", "Хр"), ("Хищники", "Хщ"), ("Контролёры", "К"), ("Дрейфующие", "Д")):
                for k in (1, 2):
                    n = f"{pre}{k}"
                    fs[n] = faction(p, n, arche, 30, 20, 0)
            w = World(fs, [], p)
            horizon = 1
        elif sc == "RL6":
            ss = sites3()
            ss[0].owner, ss[1].owner, ss[2].owner = "К", "Х", "П"
            fs = {"Х": faction(p, "Х", "Хранители", 60, 60, 20),
                  "К": faction(p, "К", "Контролёры", 60, 60, 40),
                  "П": faction(p, "П", "Хищники", 90, 60, 20)}
            w = World(fs, ss, p)
            w.forced_raids = {5: [("Х", "Перевал")], 40: [("П", "Насосная")], 90: [("К", "Жила")],
                              120: [("Х", "Перевал")]}
            horizon = 200
        else:
            ss = sites3()
            for x in ss:
                x.owner = "B"
            a = faction(p, "A", "Хищники", 90, 60, 0)
            b = faction(p, "B", "Хранители", 100 if sc == "RL3" else 60, 60, 40)
            w = World({"A": a, "B": b}, ss, p)
            if sc in ("RL2", "RL5"):
                w.forced_raids = {5: [("A", "Перевал"), ("A", "Насосная"), ("A", "Жила")]}
                horizon = 9
            elif sc == "RL3":
                w.forced_raids = {t: [("A", "Перевал")] for t in (2, 6, 10, 14, 18)}
                w.scheduled = {20: [lambda w: w.betray("A", "B")]}
                horizon = 200
            elif sc == "RL4a":
                w.forced_raids = {5: [("A", "Перевал")]}
                horizon = 80
            else:  # RL4b: штурм с захватом на тике 5, сценарный возврат на тике 101 (после затухания тика 100)
                w.forced_assaults = {5: [("A", "Перевал")]}
                w.scheduled = {101: [lambda w: setattr(w.site("Перевал"), "owner", "B")]}
                horizon = 130
    elif sc in MK_SCENARIOS:
        # spec 08c: чистая обстановка как у RL; знание и мотив включены; события только принудительные
        p = replace(p, object_raids_enabled=False, smuggling_enabled=False, fees_enabled=False,
                    prisoner_sale_enabled=False, decisions_enabled=False, knowledge_enabled=True,
                    archetype_assault_threshold={})   # автономных штурмов нет, только принудительные
        ss = sites()
        ss[0].owner = "B"
        if sc == "MK4":
            fs = {"B": faction(p, "B", "Хранители", 60, 60, 40),
                  "H": faction(p, "H", "Хранители", 40, 3, 0),     # голодает и знает объект
                  "F": faction(p, "F", "Хранители", 40, 60, 0),    # сыта и знает объект
                  "U": faction(p, "U", "Хранители", 40, 3, 0)}     # голодает и не знает
            w = World(fs, ss, p)
            w.known_at_start = {"H": ("Перевал",), "F": ("Перевал",)}
            horizon = 3
        else:
            fs = {"A": faction(p, "A", "Хищники", 90, 60, 0),
                  "B": faction(p, "B", "Хранители", 60, 60, 40)}
            if sc == "MK5":
                fs["C"] = faction(p, "C", "Хищники", 90, 60, 0)
                fs["D"] = faction(p, "D", "Дрейфующие", 30, 60, 0)
            else:
                fs["C"] = faction(p, "C", "Хранители", 60, 60, 0)
            w = World(fs, ss, p)
            if sc == "MK1":
                horizon = 4
            elif sc == "MK2":
                w.forced_raids = {5: [("A", "Перевал")]}
                horizon = 14
            elif sc == "MK3":
                w.known_at_start = {"C": ("Перевал",)}
                w.forced_assaults = {5: [("A", "Перевал")]}
                w.scheduled = {30: [lambda w: setattr(w.site("Перевал"), "owner", "B")]}
                horizon = 40
            elif sc == "MK5":
                w.forced_raids = {5: [("A", "Перевал")]}
                w.forced_assaults = {8: [("C", "Перевал")]}
                horizon = 16
            else:  # MK6
                w.forced_raids = {5: [("A", "Перевал")], 12: [("A", "Перевал")]}
                horizon = 14
    elif sc in WR_SCENARIOS or sc in WE_BASE:
        wsc, sc = sc, WE_BASE.get(sc, sc)   # spec 08e: WE = обстановка WR с другими закреплениями
        # spec 08b: чистая обстановка как у RL и MK; отношения, знание и война включены; события только принудительные.
        # Карту порогов уклада не обнуляем: она нужна самой войне (список «штурмовых» укладов). Автономные штурмы отключены
        # порогом запаса assault_dos = 0 (по умолчанию он равен 10 суткам и совпадает с порогом нужды: нужда запускала бы штурм).
        # Уточнение обстановки против spec §2 (plan 08b, «Риски»): порог нужды 10 суток не поднимается — тот же порог запускает голодный долг.
        # Вместо этого у A есть свой объект «Рудник» (доход = расход A), запас держится на 9.9 суток, нужда есть всё время, долг копится по 0.1 в сутки.
        p = replace(p, object_raids_enabled=False, smuggling_enabled=False, fees_enabled=False,
                    prisoner_sale_enabled=False, decisions_enabled=False, relations_enabled=True,
                    knowledge_enabled=True, wars_enabled=True, assault_dos=0.0, raids_enabled=False)
        p = pin_old_war(p, WE_PINS[wsc]) if wsc in WE_BASE else pin_old_war(p)
        arche = "Контролёры" if sc == "WR2" else "Хищники"
        a = faction(p, "A", arche, 90, 9.9, 0)
        rudnik = Site("Рудник", 0, 90 * p.per_head_cost * p.archetype_cost_mult[arche], 1)
        rudnik.owner = "A"
        if sc == "WR4":
            ss = [rudnik] + sites3()
            ss[1].owner, ss[2].owner, ss[3].owner = "B", "C", "D"
            fs = {"A": a, "B": faction(p, "B", "Хранители", 60, 60, 40),
                  "C": faction(p, "C", "Хранители", 60, 60, 15), "D": faction(p, "D", "Хранители", 60, 60, 20)}
            w = World(fs, ss, p)
            w.known_at_start = {"A": ("Перевал", "Насосная", "Жила")}
            horizon = 30
        else:
            ss = [rudnik] + sites()
            ss[1].owner = "B"
            fs = {"A": a, "B": faction(p, "B", "Хранители", 60, 60, 40)}
            if sc == "WR7d":
                fs["C"] = faction(p, "C", "Хищники", 90, 60, 0)
            w = World(fs, ss, p)
            if sc != "WR3":
                w.known_at_start = {"A": ("Перевал",)}
            horizon = {"WR1": 20, "WR2": 40, "WR3": 40, "WR5": 25, "WR6": 45}.get(sc, 26)
            if sc == "WR7a":
                w.scheduled = {25: [lambda w: w.kill_many(w.factions["B"], w.factions["B"].manpower - floor(0.25 * w.wars[("A", "B")]["mp0"]["B"]), 7, "SCENARIO_KILL")]}
            elif sc == "WR7b":
                w.scheduled = {25: [lambda w: w.kill_many(w.factions["A"], w.factions["A"].manpower - floor(0.40 * w.wars[("A", "B")]["mp0"]["A"]), 7, "SCENARIO_KILL")]}
            elif sc == "WR7c":
                w.forced_assaults = {25: [("A", "Перевал")]}
            elif sc == "WR7d":
                w.forced_assaults = {25: [("C", "Перевал")]}
            if wsc == "WE1":
                horizon = 101
    elif sc in WS_SCENARIOS:
        # spec 08d: обстановка WR; до тика 20 автономные нападения выключены, на тике 20 сценарная команда их включает.
        # war_steers_attacks включает run() (для WS по умолчанию True); обратные проверки передают False явно.
        p = replace(p, object_raids_enabled=False, smuggling_enabled=False, fees_enabled=False,
                    prisoner_sale_enabled=False, decisions_enabled=False, relations_enabled=True,
                    knowledge_enabled=True, wars_enabled=True, assault_dos=0.0, raids_enabled=False)
        p = pin_old_war(p)
        a = faction(p, "A", "Хищники", 90, 9.9, 0)
        rudnik = Site("Рудник", 0, 90 * p.per_head_cost * p.archetype_cost_mult["Хищники"], 1)
        rudnik.owner = "A"
        ss = [rudnik] + sites()
        if sc == "WS2":
            ss[1].owner, ss[2].owner = "B", "C"
            fs = {"A": a, "B": faction(p, "B", "Хранители", 150, 60, 40), "C": faction(p, "C", "Хранители", 30, 60, 15)}
            known = ("Перевал",)
            on = dict(assault_dos=10.0)
        else:
            ss[1].owner = ss[2].owner = "B"
            fs = {"A": a, "B": faction(p, "B", "Хранители", 60, 60, 55)}
            known = ("Насосная",)
            on = dict(assault_dos=10.0) if sc == "WS1" else dict(raids_enabled=True, object_raids_enabled=True)
        w = World(fs, ss, p)
        w.known_at_start = {"A": known}
        w.scheduled = {20: [lambda w: setattr(w, "p", replace(w.p, **on))]}
        horizon = 21
    else:
        raise ValueError(sc)
    for f in w.factions.values():
        w.publish_dos(f, phase=0)
    return w, horizon


def run(sc: str, p: Params | None = None):
    if p is None:
        p = Params()
        if sc in WS_SCENARIOS:
            p = replace(p, war_steers_attacks=True)   # spec 08d: по умолчанию сценарии WS идут с управлением; обратные проверки передают False явно
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
    elif sc in RL_SCENARIOS:
        def rows(target):
            return [(r[0], r[4], r[5]) for r in w.log if r[3] == target]
        lv = w.level_of
        if sc == "RL1":
            table = {"Хранители": {"Хранители": -2.0, "Хищники": 2.0, "Контролёры": -2.0, "Дрейфующие": 2.0},
                     "Хищники": {k: 5.5 for k in ("Хранители", "Хищники", "Контролёры", "Дрейфующие")},
                     "Контролёры": {"Хранители": 2.5, "Хищники": 5.5, "Контролёры": 2.5, "Дрейфующие": 5.5},
                     "Дрейфующие": {k: 0.0 for k in ("Хранители", "Хищники", "Контролёры", "Дрейфующие")}}
            pre = {"Хранители": "Хр", "Хищники": "Хщ", "Контролёры": "К", "Дрейфующие": "Д"}
            bad = []
            for a, row in table.items():
                for b, exp in row.items():
                    fa = pre[a] + "1"
                    fb = pre[b] + ("2" if a == b else "1")
                    got = w.rel_h(fa, fb)
                    if abs(got - exp) > 1e-9:
                        bad.append(f"{a}→{b}: {got} вместо {exp}")
            res.append(("16 ячеек слоя 1 совпадают с таблицей 08", not bad, "расхождения: " + "; ".join(bad) if bad else "все 16 ячеек совпали"))
            res.append(("до первого события записей обиды нет", not w.rel and not [r for r in w.log if r[2] == "08"], f"пар {len(w.rel)}"))
        elif sc == "RL2":
            ev = [e for e in w.events if e["kind"] == "raid_object"]
            res.append(("сценарий валиден: три налёта на тике 5", len(ev) == 3 and all(e["tick"] == 5 for e in ev), f"налётов {len(ev)}"))
            gt = rows("rel.B>A.g_target")
            res.append(("g_target = 4.0 (потолок), а не 9.0", gt and max(x[2] for x in gt) == 4.0, f"g_target макс. {max([x[2] for x in gt] or [0])}"))
            g = {t: new for t, old, new in rows("rel.B>A.g")}
            seq = [g.get(t) for t in (5, 6, 7, 8)]
            res.append(("g на тиках события и следующих трёх = 1 / 2 / 3 / 4", seq == [1.0, 2.0, 3.0, 4.0], f"g: {seq}"))
            jump = max([abs(new - old) for t, old, new in rows("rel.B>A.g")] or [0])
            res.append(("ни в одном тике |Δg| не больше 1.0", jump <= p.grudge_push + 1e-9, f"максимальный сдвиг {jump}"))
        elif sc == "RL3":
            ev = [e for e in w.events if e["kind"] == "raid_object"]
            res.append(("сценарий валиден: пять налётов за 20 тиков", len(ev) == 5 and max(e["tick"] for e in ev) <= 20, f"налётов {len(ev)}"))
            gt = rows("rel.B>A.g_target")
            top = max([x[2] for x in gt] or [0])
            res.append(("g_target ≤ 4.0 на каждом тике", top <= 4.0 + 1e-9, f"максимум {top}"))
            res.append(("потолок действительно сработал (проверка не пустая)", top == 4.0, f"максимум {top}"))
            b = rows("rel.B>A.b")
            res.append(("после betray b = 6.0 сразу", b[:1] == [(20, 0.0, 6.0)], f"строки b: {b}"))
            res.append(("b = 6.0 на тике 200, не затухало", len(b) == 1 and w.rel[("B", "A")].b == 6.0 and w.tick == 200, f"b на тике {w.tick}: {w.rel[('B', 'A')].b}"))
        elif sc == "RL4a":
            ev = [e for e in w.events if e["kind"] == "raid_object"]
            res.append(("сценарий валиден: один налёт без захвата", len(ev) == 1 and ev[0]["tick"] == 5 and not [e for e in w.events if e["kind"] == "assault"], f"налётов {len(ev)}"))
            got = {t: new for t, old, new in rows("rel.B>A.g_target") if t > 5}
            exp = {10: 2.5, 20: 2.0, 30: 1.5, 40: 1.0, 50: 0.5, 60: 0.0}
            res.append(("g_target 3.0 → 0 шагами по 0.5 на тиках 10, 20, … 60", got == exp and rows("rel.B>A.g_target")[0][2] == 3.0, f"шаги: {got}"))
        elif sc == "RL4b":
            ev = [e for e in w.events if e["kind"] == "assault"]
            res.append(("сценарий валиден: штурм с захватом на тике 5", len(ev) == 1 and ev[0]["attacker_wins"] and ev[0]["tick"] == 5, f"штурмов {len(ev)}"))
            gt = rows("rel.B>A.g_target")
            res.append(("g_target = 3.0 на всех тиках 5…100", [x for x in gt if x[0] <= 100] == [(5, 0.0, 3.0)], f"строки до тика 100: {[x for x in gt if x[0] <= 100]}"))
            skipped = [e for e in w.events if e["kind"] == "grudge_decay" and not e["applied"]]
            res.append(("шаги затухания на тиках 10…100 пропущены паузой", len(skipped) == 10 and skipped[-1]["tick"] == 100, f"пропущено шагов {len(skipped)}"))
            after = [x for x in gt if x[0] > 100]
            res.append(("после возврата объекта затухание возобновилось на тике 110 (−0.5)", after[:1] == [(110, 3.0, 2.5)], f"после тика 100: {after}"))
        elif sc == "RL5":
            res.append(("сценарий валиден: три налёта X на объекты D", len([e for e in w.events if e["kind"] == "raid_object"]) == 3, ""))
            hb, ha = w.rel_h("B", "A"), w.rel_h("A", "B")
            res.append(("H(пострадавший→обидчик) = база + g", abs(hb - (w.base_h("B", "A") + w.rel[("B", "A")].g)) < 1e-9 and w.rel[("B", "A")].g == 4.0,
                        f"H(B→A) = {hb}, база {w.base_h('B', 'A')}, g {w.rel[('B', 'A')].g}"))
            res.append(("H(обидчик→пострадавший) равен базе, записи пары нет", abs(ha - w.base_h("A", "B")) < 1e-9 and ("A", "B") not in w.rel and not rows("rel.A>B.H"),
                        f"H(A→B) = {ha}, база {w.base_h('A', 'B')}"))
        elif sc == "RL6":
            names = list(w.factions)
            pairs = [(a, b) for a in names for b in names if a != b]
            hend = {pr: w.rel_h(*pr) for pr in pairs}
            res.append(("на тике 200 есть направленная пара с H < 5", any(h < 5.0 for h in hend.values()), f"пар с H < 5: {sum(1 for h in hend.values() if h < 5.0)} из {len(pairs)}"))
            crossed = []
            for a, b in pairs:
                seq = rows(f"rel.{a}>{b}.H")
                up = next((t for t, old, new in seq if new >= 5.0), None)
                if up is None:
                    continue
                down = next((t for t, old, new in seq if t > up and new < 5.0), None)
                if down is None:
                    continue
                dec = [e for e in w.events if e["kind"] == "grudge_decay" and e["victim"] == a and e["offender"] == b and e["applied"] and up < e["tick"] <= down]
                if dec:
                    crossed.append(f"{a}→{b}: выше линии на тике {up}, ниже на тике {down}")
            res.append(("пара поднялась через H = 5 и вернулась ниже линии затуханием", bool(crossed), "; ".join(crossed) or "таких пар нет"))
            diff = [f"{a}→{b} {lv(hend[(a, b)])} / {b}→{a} {lv(hend[(b, a)])}" for a, b in pairs if a < b and lv(hend[(a, b)]) != lv(hend[(b, a)])]
            res.append(("есть пара с H(A→B) и H(B→A) в разных уровнях", bool(diff), "; ".join(diff) or "таких пар нет"))
    elif sc in MK_SCENARIOS:
        def mrows(target):
            return [(r[0], r[4], r[5], r[6]) for r in w.log if r[3] == target]
        blind = [e for e in w.events if e["kind"] == "blind_attack"]
        if sc == "MK1":
            res.append(("до события знания нет: ни одной строки know, rumor, motive",
                        not [r for r in w.log if r[2] == "08c"], f"строк модуля 08c: {len([r for r in w.log if r[2] == '08c'])}"))
        elif sc == "MK2":
            ev = [e for e in w.events if e["kind"] == "raid_object"]
            res.append(("сценарий валиден: один налёт A на объект B на тике 5", len(ev) == 1 and ev[0]["tick"] == 5, f"налётов {len(ev)}"))
            a, c = mrows("know.A>Перевал"), mrows("know.C>Перевал")
            res.append(("участник A знает с тика 5", a == [(5, None, "B", "KNOW_DIRECT")], f"строки A: {a}"))
            res.append(("третья фракция C узнаёт на тике 12 (5 + 7), не раньше", c == [(12, None, "B", "KNOW_RUMOR")], f"строки C: {c}"))
            r = mrows("rumor.Перевал.5")
            res.append(("слух рождён на тике 5 и доставлен на тике 12", r == [(5, 0, 1, "RUMOR_NEW"), (12, 1, 0, "RUMOR_DELIVERED")], f"строки слуха: {r}"))
        elif sc == "MK3":
            ev = [e for e in w.events if e["kind"] == "assault"]
            res.append(("сценарий валиден: штурм A с захватом на тике 5", len(ev) == 1 and ev[0]["attacker_wins"] and ev[0]["tick"] == 5, f"штурмов {len(ev)}"))
            c = mrows("know.C>Перевал")
            exp = [(1, None, "B", "KNOW_START"), (5, "B", None, "KNOW_LOST"), (12, None, "A", "KNOW_RUMOR"), (30, "A", None, "KNOW_LOST")]
            res.append(("знание C: старт «B» → гаснет на тике 5 → слух о захвате на тике 12 даёт «A» → гаснет на тике 30 при возврате без события и не возвращается", c == exp, f"строки C: {c}"))
        elif sc == "MK4":
            res.append(("сценарий валиден: H и U голодают, F сыта", w.factions["H"].days_supply < p.hunger_threshold and w.factions["U"].days_supply < p.hunger_threshold
                        and w.factions["F"].days_supply >= p.hunger_threshold,
                        f"запас H {w.factions['H'].days_supply:.1f}, U {w.factions['U'].days_supply:.1f}, F {w.factions['F'].days_supply:.1f} суток, порог {p.hunger_threshold:.0f}"))
            res.append(("мотив только у H (голод и знание)", w.motive == {("H", "Перевал")}, f"мотивы в конце: {sorted(w.motive)}"))
            res.append(("у F (сыта) и U (не знает) мотива не было ни разу", not mrows("motive.F>Перевал") and not mrows("motive.U>Перевал"), ""))
        elif sc == "MK5":
            ev = [e for e in w.events if e["kind"] in ("raid_object", "assault")]
            res.append(("сценарий валиден: налёт A на тике 5 и штурм C с захватом на тике 8", [(e["kind"], e["tick"]) for e in ev] == [("raid_object", 5), ("assault", 8)] and ev[1]["attacker_wins"],
                        f"события: {[(e['kind'], e['tick']) for e in ev]}"))
            r1, r2, d = mrows("rumor.Перевал.5"), mrows("rumor.Перевал.8"), mrows("know.D>Перевал")
            res.append(("слух тика 5 на тике 12 отброшен как устаревший", r1 == [(5, 0, 1, "RUMOR_NEW"), (12, 1, 0, "RUMOR_STALE")], f"строки слуха: {r1}"))
            res.append(("слух тика 8 доставлен на тике 15", r2 == [(8, 0, 1, "RUMOR_NEW"), (15, 1, 0, "RUMOR_DELIVERED")], f"строки слуха: {r2}"))
            res.append(("D ничего не знает на тике 12 и узнаёт «C» на тике 15", d == [(15, None, "C", "KNOW_RUMOR")], f"строки D: {d}"))
        elif sc == "MK6":
            ev = [e for e in w.events if e["kind"] == "raid_object"]
            res.append(("сценарий валиден: два налёта A на объект B, тики 5 и 12", [e["tick"] for e in ev] == [5, 12], f"налёты на тиках {[e['tick'] for e in ev]}"))
            res.append(("слепое нападение одно: первый налёт; второй A уже знает объект", [(e["tick"], e["attacker"]) for e in blind] == [(5, "A")], f"слепые: {[(e['tick'], e['attacker']) for e in blind]}"))
    elif sc in WR_SCENARIOS:
        def wrows(target):
            return [(r[0], r[4], r[5], r[6]) for r in w.log if r[3] == target]
        near = lambda x, y: x is not None and abs(x - y) < 1e-6
        if sc == "WR1":
            acc = wrows("war.A>B.acc")
            up = [(t, new) for t, old, new, rs in acc if t <= 18]
            ok_up = len(up) == 18 and all(t == i + 1 and near(v, 5.5 * (i + 1)) for i, (t, v) in enumerate(up))
            res.append(("счётчик A→B растёт 5.5, 11.0, …, 99.0 на тиках 1…18", ok_up, f"значения: {[v for _, v in up]}"))
            st, gl = wrows("war.A>B.state"), wrows("war.A>B.goal")
            res.append(("война объявлена на тике 19, и до него строк state нет", st == [(19, 0, 1, "WAR_DECLARED")], f"строки state: {st}"))
            res.append(("цель — «Перевал», записана на тике 19", gl == [(19, None, "Перевал", "WAR_DECLARED")], f"строки goal: {gl}"))
            res.append(("после объявления счётчик 4.5", near(w.war_acc.get(("A", "B")), 4.5), f"acc в конце: {w.war_acc.get(('A', 'B'))}"))
            res.append(("запас A всё время между 1 и 10 сутками (нужда без побочного голода)", all(1.0 <= dos < p.hunger_threshold for dos in [w.factions['A'].days_supply]),
                        f"запас A в конце: {w.factions['A'].days_supply:.2f} суток"))
        elif sc in ("WR2", "WR3"):
            rows08b = [r for r in w.log if r[2] == "08b"]
            res.append(("ни одной строки модуля 08b за 40 тиков (ни acc, ни state)", not rows08b, f"строк 08b: {len(rows08b)}"))
            if sc == "WR2":
                res.append(("сценарий валиден: H(A→B) ниже линии Enemy", w.rel_h("A", "B") < p.rel_level_cuts[2], f"H = {w.rel_h('A', 'B'):.1f}, линия {p.rel_level_cuts[2]}"))
            else:
                res.append(("сценарий валиден: A нуждается, но ничего не знает", w.factions["A"].days_supply < p.hunger_threshold and not w.know,
                            f"запас A {w.factions['A'].days_supply:.1f} суток, записей знания {len(w.know)}"))
        elif sc == "WR4":
            b, c, d = wrows("war.A>B.state"), wrows("war.A>C.state"), wrows("war.A>D.state")
            res.append(("война с B объявлена на тике 19", b == [(19, 0, 1, "WAR_DECLARED")], f"строки: {b}"))
            res.append(("война с C объявлена на тике 22 (через 3 тика)", c == [(22, 0, 1, "WAR_DECLARED")], f"строки: {c}"))
            res.append(("с D не объявлена до тика 30 (у A уже две войны)", d == [], f"строки: {d}"))
            res.append(("счётчик A→D стоит на 104.5", near(w.war_acc.get(("A", "D")), 104.5), f"acc(A→D): {w.war_acc.get(('A', 'D'))}"))
            res.append(("запас A не упал ниже 1 суток", w.factions["A"].days_supply >= p.war_min_dos, f"запас A: {w.factions['A'].days_supply:.2f} суток"))
        elif sc == "WR5":
            cost = [r for r in w.log if r[6] == "WAR_COST"]
            ok = True
            for who in ("A", "B"):
                mine = [r for r in cost if r[3] == f"{who}.supply"]
                ok = ok and [r[0] for r in mine] == list(range(20, 26)) and all(abs((r[4] - r[5]) - 5.0) < 1e-6 for r in mine)
            res.append(("строки WAR_COST у A и у B на тиках 20…25, по 6, каждая со снижением ровно на 5.0", ok and len(cost) == 12,
                        f"строк {len(cost)}, тики {sorted({r[0] for r in cost})}"))
            res.append(("на тике 19 списания нет", not [r for r in cost if r[0] == 19], ""))
        elif sc == "WR6":
            st, tr = wrows("war.A>B.state"), wrows("truce.A-B")
            res.append(("война закрыта на тике 39 по сроку, других строк state нет", st == [(19, 0, 1, "WAR_DECLARED"), (39, 1, 0, "WAR_END_TIMEOUT")], f"строки state: {st}"))
            res.append(("перемирие с тика 39 до 43, TRUCE_END на тике 43", tr == [(39, 0, 43, "TRUCE"), (43, 43, 0, "TRUCE_END")], f"строки truce: {tr}"))
            res.append(("новой войны до тика 45 нет", len([x for x in st if x[2] == 1]) == 1, f"объявлений: {len([x for x in st if x[2] == 1])}"))
        else:
            reason = {"WR7a": "WAR_END_BROKEN", "WR7b": "WAR_END_EXHAUSTED", "WR7c": "WAR_END_GOAL", "WR7d": "WAR_END_GOAL_LOST"}[sc]
            st = wrows("war.A>B.state")
            if sc == "WR7a":
                res.append(("сценарий валиден: у B остаётся ровно 25% от 60", w.factions["B"].manpower == floor(0.25 * 60), f"у B {w.factions['B'].manpower} из 60"))
            elif sc == "WR7b":
                res.append(("сценарий валиден: у A остаётся ровно 40% от 90", w.factions["A"].manpower == floor(0.40 * 90), f"у A {w.factions['A'].manpower} из 90"))
            else:
                att = [e for e in w.events if e["kind"] == "assault"]
                res.append(("сценарий валиден: принудительный штурм на тике 25 с победой атакующего", len(att) == 1 and att[0]["tick"] == 25 and att[0]["attacker_wins"],
                            f"штурмы: {[(e['tick'], e['attacker'], e['attacker_wins']) for e in att]}"))
            res.append((f"война закрыта на тике 25, {reason}", st == [(19, 0, 1, "WAR_DECLARED"), (25, 1, 0, reason)], f"строки state: {st}"))
    elif sc in WS_SCENARIOS:
        wa = [e for e in w.events if e["kind"] == "war_attack"]
        st = [(r[0], r[4], r[5], r[6]) for r in w.log if r[3] == "war.A>B.state"]
        if sc == "WS1":
            asl = [e for e in w.events if e["kind"] == "assault"]
            res.append(("первый автономный штурм: тик 20, «Насосная», победа A",
                        bool(asl) and (asl[0]["tick"], asl[0]["site"], asl[0]["attacker_wins"], asl[0]["forced"]) == (20, "Насосная", True, False),
                        f"штурмы: {[(e['tick'], e['site'], e['attacker_wins']) for e in asl]}"))
            res.append(("война закрыта на тике 20 причиной WAR_END_GOAL", st == [(19, 0, 1, "WAR_DECLARED"), (20, 1, 0, "WAR_END_GOAL")], f"строки state: {st}"))
        elif sc == "WS2":
            asl = [e for e in w.events if e["kind"] == "assault"]
            res.append(("первый автономный штурм A: тик 20, «Насосная» у C (цель «Перевал» не по силам)",
                        bool(asl) and (asl[0]["tick"], asl[0]["site"], asl[0]["defender"]) == (20, "Насосная", "C"),
                        f"штурмы: {[(e['tick'], e['site'], e['defender']) for e in asl]}"))
            res.append(("управление не сработало: событий war_attack нет", not wa, f"war_attack: {len(wa)}"))
            res.append(("война A→B действует на тике 21, цель «Перевал»", ("A", "B") in w.wars and w.wars[("A", "B")]["goal"] == "Перевал", f"войны: {sorted(w.wars)}"))
        else:
            rd = [e for e in w.events if e["kind"] == "raid_object"]
            res.append(("первый налёт на объект: тик 20, «Насосная» (цель войны)",
                        bool(rd) and (rd[0]["tick"], rd[0]["site"], rd[0]["forced"]) == (20, "Насосная", False),
                        f"налёты: {[(e['tick'], e['site']) for e in rd]}"))
            res.append(("событие war_attack вида «налёт» на тике 20", [(e["tick"], e["attack"]) for e in wa] == [(20, "raid")], f"war_attack: {[(e['tick'], e['attack']) for e in wa]}"))
    elif sc in WE_BASE:
        def wrows(target):
            return [(r[0], r[4], r[5], r[6]) for r in w.log if r[3] == target]
        rep_rows = [r for r in w.log if r[6] == "REPARATIONS"]
        near = lambda x, y, tol=1e-3: x is not None and abs(x - y) < tol
        if sc == "WE1":
            st, acc = wrows("war.A>B.state"), wrows("war.A>B.acc")
            res.append(("счётчик A→B растёт по 1.0 за тик с тика 1", bool(acc) and acc[0] == (1, 0.0, 1.0, "WAR_ACC") and acc[98][:3] == (99, 98.0, 99.0), f"первые строки: {acc[:2]}, строка 99: {acc[98:99]}"))
            res.append(("война объявлена на тике 100, не раньше", st == [(100, 0, 1, "WAR_DECLARED")], f"строки state: {st}"))
            res.append(("после объявления счётчик 0.0", near(w.war_acc.get(("A", "B")), 0.0), f"acc: {w.war_acc.get(('A', 'B'))}"))
        elif sc == "WE2":
            cost = [r for r in w.log if r[6] == "WAR_COST"]
            ok = True
            det = []
            for who in ("A", "B"):
                mine = [r for r in cost if r[3] == f"{who}.supply"]
                exp = 0.25 * w.expense(w.factions[who])
                det.append(f"{who}: {len(mine)} строк, ожидалось {exp:.2f}, первая {round(mine[0][4] - mine[0][5], 2) if mine else None}")
                ok = ok and [r[0] for r in mine] == list(range(20, 26)) and all(near(r[4] - r[5], exp, 0.01) for r in mine)
            res.append(("WAR_COST у A и у B на тиках 20…25, каждая ровно 25% расхода фракции", ok, "; ".join(det)))
        elif sc == "WE3d":
            st, tr = wrows("war.A>B.state"), wrows("truce.A-B")
            res.append(("конец по сроку на тике 39 (срок закреплён 20)", st == [(19, 0, 1, "WAR_DECLARED"), (39, 1, 0, "WAR_END_TIMEOUT")], f"строки state: {st}"))
            res.append(("репараций нет", not rep_rows, f"строк REPARATIONS: {len(rep_rows)}"))
            res.append(("перемирие с тика 39 до тика 54 (15 суток)", tr == [(39, 0, 54, "TRUCE")], f"строки truce: {tr}"))
        elif sc == "WE3e":
            st = wrows("war.A>B.state")
            res.append(("цель ушла: WAR_END_GOAL_LOST на тике 25", st == [(19, 0, 1, "WAR_DECLARED"), (25, 1, 0, "WAR_END_GOAL_LOST")], f"строки state: {st}"))
            res.append(("репараций нет", not rep_rows, f"строк REPARATIONS: {len(rep_rows)}"))
        else:
            reason, loser, winner = {"WE3a": ("WAR_END_BROKEN", "B", "A"), "WE3b": ("WAR_END_EXHAUSTED", "A", "B"), "WE3c": ("WAR_END_GOAL", "B", "A")}[sc]
            st = wrows("war.A>B.state")
            res.append((f"война закрыта на тике 25, {reason}", st == [(19, 0, 1, "WAR_DECLARED"), (25, 1, 0, reason)], f"строки state: {st}"))
            lr = [r for r in rep_rows if r[3] == f"{loser}.supply"]
            wr = [r for r in rep_rows if r[3] == f"{winner}.supply"]
            ok = len(rep_rows) == 2 and len(lr) == 1 and len(wr) == 1 and lr[0][0] == wr[0][0] == 25
            res.append(("две строки REPARATIONS на тике 25: у проигравшего убыль, у победителя рост", ok, f"строки: {[(r[0], r[3], r[4], r[5]) for r in rep_rows]}"))
            if ok:
                drop, gain = lr[0][4] - lr[0][5], wr[0][5] - wr[0][4]
                res.append(("проигравший отдал 40% своего запаса", near(drop / lr[0][4], 0.40), f"отдано {drop:.2f} из {lr[0][4]:.2f}"))
                res.append(("WE4: победитель получил ровно столько, сколько отдал проигравший", near(drop, gain, 0.01), f"отдано {drop:.4f}, получено {gain:.4f}"))
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
    "R16": (replace(Params(), grudge_push=1e9), ("RL2",), "лимит толчка обиды выключен"),
    "R17": (replace(Params(), grudge_cap=1e9), ("RL3",), "потолок обиды выключен"),
    "R18": (replace(Params(), grudge_pause=False), ("RL4b",), "пауза затухания выключена"),
    "R19": (replace(Params(), rumor_delay=0), ("MK2",), "слух доходит мгновенно (задержка 0)"),
    "R20": (replace(Params(), knowledge_expires_on_owner_change=False), ("MK3",), "знание не гаснет при смене владельца"),
    "R21": (replace(Params(), hunger_threshold=1e9), ("MK4",), "порог нужды выключен (нуждаются все)"),
    "R22": (replace(Params(), rumor_drop_stale=False), ("MK5",), "устаревший слух не отбрасывается"),
    "R23": (replace(Params(), war_needs_motive=False), ("WR3",), "война без мотива (объявление не требует нужды и знания)"),
    "R24": (replace(Params(), war_world_gap=0), ("WR4",), "в мире нет паузы между объявлениями"),
    "R25": (replace(Params(), war_max_per_faction=99), ("WR4",), "число войн у фракции не ограничено"),
    "R26": (replace(Params(), war_cost=0.0), ("WR5",), "война ничего не стоит"),
    "R27": (replace(Params(), war_max_days=1000), ("WR6",), "срок войны не ограничен"),
    "R28": (replace(Params(), war_broken_share=0.0), ("WR7a",), "конец «сломлены» выключен"),
    "R29": (replace(Params(), war_exhausted_share=0.0), ("WR7b",), "конец «выдохлись» выключен"),
    "R30": (replace(Params(), war_steers_attacks=False), ("WS1",), "война не направляет штурм (выбор цели как до 08d)"),
    "R31": (replace(Params(), war_steers_attacks=False), ("WS3",), "война не направляет налёт (выбор цели как до 08d)"),
    "R32": (replace(Params(), war_reparation_share=0.0), ("WE3a",), "репараций нет"),
    "R33": (replace(Params(), war_cost=0.0), ("WE2",), "война ничего не стоит (цена 0)"),
    "R34": (replace(Params(), war_chance_base=4.0, war_chance_slope=3.0, war_chance_cap=15.0), ("WE1",), "старый быстрый накопитель 4.0 / 3.0 / 15"),
}
