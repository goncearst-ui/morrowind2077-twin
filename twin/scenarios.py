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
RB_RUDNIK = 0.85  # доход «Рудника» A в RB как доля её расхода: запас A держится ниже 10 суток при налётах на свой регион (подбор обстановки, plan 20 шаг 4)
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
RB_SCENARIOS = ("RB1", "RB2", "RB3", "RB4", "RB5")
SW_SCENARIOS = ("SW1", "SW2")
EV_PIN = ("EV1", "EV2", "EV3", "EV4", "EV5", "EV6", "EV7", "EV8", "EV9", "EV18")   # spec 21a: оси задаёт подвязка сценария
EV_WORLD = ("EV12", "EV13")                                                  # spec 21a: мир SW со сменой уклада
EV_MECH = ("EV14", "EV15", "EV16", "EV17", "EV19")
EV_OLD = EV_PIN + EV_WORLD + EV_MECH                                      # сценарии 21a: журналы при leader_enabled = False совпадают с tests/baseline_pre21b.json
EV_LEADER = ("EV20", "EV21", "EV22", "EV23", "EV24", "EV25", "EV26", "EV26b", "EV26c", "EV27", "EV30", "EV31")   # spec 21b
EV_SCENARIOS = EV_OLD + EV_LEADER
PL_SIMPLE = ("PL1", "PL2", "PL3", "PL4", "PL5", "PL6", "PL7")      # spec 21d: чистый мир без войн, подкуп и подсказка
PL_WAR = ("PL8", "PL8b", "PL8c", "PL9", "PL10", "PL11")              # spec 21d: обстановка WR
PL_SCENARIOS = PL_SIMPLE + PL_WAR
CR_PIN = ("CR1", "CR2", "CR3", "CR4", "CR7", "CR7k", "CR8", "CR9")   # spec 21c: оси задаёт подвязка
CR_SCENARIOS = CR_PIN + ("CR5",)
CR_ORDER = (3, 4, 5, 6, 7, 8, 9)


def roster(fname, successors=(), officers=0, leader=True):
    """Именные фракции (spec 21b): вожак, преемники по порядку (профили), офицеры."""
    out = []
    if leader:
        out.append(dict(name=f"{fname}:вожак", role="вожак", profile="Основатель", alive=True))
    for i, prof in enumerate(successors, 1):
        out.append(dict(name=f"{fname}:преемник{i}", role="преемник", profile=prof, alive=True))
    for i in range(1, officers + 1):
        out.append(dict(name=f"{fname}:офицер{i}", role="офицер", profile="—", alive=True))
    return out


def give_named(w, fname, successors=(), officers=0, profile="Основатель"):
    f = w.factions[fname]
    f.named = roster(fname, successors, officers)
    f.named[0]["profile"] = profile
    f.leader = f"{fname}:вожак"


def ev_pins(f_name, segs):
    """Подвязка осей на каждый тик: segs = [(последний тик сегмента, dos, шок (после затухания), мораль, C)]. None = не трогать."""
    def hook(w):
        f = w.factions[f_name]
        for until, dos, shock, morale, ctl in segs:
            if w.tick <= until:
                break
        e = w.expense(f)
        if dos is not None:
            f.supply = (dos + 1) * e      # фаза 2 спишет сутки расхода: к фазе 4 запас ровно dos суток
        if shock is not None:
            f.shock = shock + w.p.shock_decay_per_tick   # фаза 1 вычтет затухание: к фазе 4 шок ровно shock
        if morale is not None:
            f.morale = morale
        if ctl is not None:
            f.ctl = ctl
        f.hunger_debt = 0.0
    return hook
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
    elif sc in RB_SCENARIOS:
        # spec 20: чистая обстановка; налёты на объекты автономные, штурмов нет; дисциплина налётов включает run() (для RB по умолчанию True)
        p = replace(p, smuggling_enabled=False, fees_enabled=False, prisoner_sale_enabled=False, decisions_enabled=False,
                    relations_enabled=True, knowledge_enabled=True, assault_dos=0.0)
        a = faction(p, "A", "Хищники", 90, 60 if sc == "RB1" else 9.9, 0)
        rudnik = Site("Рудник", 0, 90 * p.per_head_cost * p.archetype_cost_mult["Хищники"] * RB_RUDNIK, 1)
        rudnik.owner = "A"
        if sc == "RB5":
            ss = [rudnik] + [Site(f"Пустошь-{k}", 10, 1, 1) for k in (1, 2, 3)]
            for x in ss[1:]:
                x.owner = "B"
            b = faction(p, "B", "Хранители", 20, 0, 30)
            b.supply = 100.0
            p = replace(p, crew_cap={**p.crew_cap, **{f"Пустошь-{k}": 1 for k in (1, 2, 3)}})
            horizon = 3
        else:
            ss = [rudnik] + sites()
            ss[1].owner = "B"
            b = faction(p, "B", "Хранители", 60, 60, 40)
            horizon = {"RB4": 31}.get(sc, 30)
        w = World({"A": a, "B": b}, ss, p)
        if sc != "RB2":
            w.known_at_start = {"A": tuple(x.name for x in ss if x.owner == "B")}
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
    elif sc in SW_SCENARIOS or sc in EV_WORLD:
        # spec 20: мир из 6 фракций и 18 объектов (по 3 на фракцию, 03b), 500 тиков, все переключатели 08a–08e и дисциплина налётов
        names = ("X1", "X2", "X3", "X4", "X5", "X6")
        kinds = {"X1": ("Хранители", 60), "X2": ("Хранители", 40), "X3": ("Хищники", 50), "X4": ("Хищники", 50),
                 "X5": ("Контролёры", 40), "X6": ("Дрейфующие", 30)}
        caps, ss = dict(p.crew_cap), []
        for n in names:
            for k, (bc, y, mc, cp) in enumerate(((40, 90, 4, 40), (15, 35, 2, 15), (20, 60, 3, 20))):
                nm = f"{n}-{k + 1}"
                caps[nm] = cp
                x = Site(nm, bc, y, mc)
                x.owner = n
                ss.append(x)
        p = replace(p, relations_enabled=True, knowledge_enabled=True, wars_enabled=True, crew_cap=caps, evolution_enabled=sc in EV_WORLD)
        dos = {"SW1": 20, "SW2": 40, "EV12": 20, "EV13": 6}[sc]
        fs = {n: faction(p, n, a_, m_, dos, 75) for n, (a_, m_) in kinds.items()}
        w = World(fs, ss, p)
        w.known_at_start = {n: tuple(x.name for x in ss if x.owner != n) for n, (a_, m_) in kinds.items() if a_ in ("Хищники", "Контролёры")}
        horizon = 500
    elif sc in PL_SCENARIOS:
        # spec 21d: рычаги игрока. Правила числового стека вынуты (evo_rule_order = ()), оси не меняют уклад
        p = replace(p, evolution_enabled=True, leader_enabled=True, player_levers_enabled=True, evo_rule_order=())
        if sc in PL_SIMPLE:
            p = replace(p, relations_enabled=True, knowledge_enabled=True, hunger_threshold=0.0, underpay_morale=0.0, raids_enabled=False,
                        object_raids_enabled=False, smuggling_enabled=False, fees_enabled=False, prisoner_sale_enabled=False,
                        decisions_enabled=False, archetype_assault_threshold={})
            names = ("A", "B", "C", "D") if sc == "PL3" else ("A", "B")
            fs = {n: faction(p, n, "Хранители", 30, 40, 40 if n == "B" else 0) for n in names}
            w = World(fs, [Site("Перевал", 40, 90, 4, owner="B")], p)
            for n in names:
                give_named(w, n, profile={"C": "Радикальный", "D": "Осторожный"}.get(n, "Основатель"))
            horizon = 70 if sc == "PL7" else 25
            w.player_funds = {"PL1": 1000.0, "PL2": 3000.0, "PL3": 1000.0, "PL4": 1000.0, "PL5": 100.0, "PL6": 2000.0, "PL7": 1000.0}[sc]
            w.player_script = {
                "PL1": {2: [("bribe", "A", "B", 300.0)]},
                "PL2": {2: [("bribe", "A", "B", 300.0)], 12: [("bribe", "A", "B", 2000.0)]},
                "PL3": {2: [("bribe", n, "B", 300.0) for n in "ACD"]},
                "PL4": {3: [("kill", "A", "A:вожак")], 5: [("bribe", "A", "B", 300.0), ("tip", "A", "Перевал")]},
                "PL5": {2: [("bribe", "A", "B", 300.0)]},
                "PL6": {2: [("bribe", "A", "B", 200.0)], 7: [("bribe", "A", "B", 200.0)], 12: [("bribe", "A", "B", 200.0)]},
                "PL7": {2: [("bribe", "A", "B", 600.0)]},
            }[sc]
        else:
            base = {"PL8": "WR2", "PL8b": "WR2", "PL8c": "WR2"}.get(sc, "WR1")
            w, horizon = build(base, p)
            for n in w.factions:
                give_named(w, n, officers=1 if (sc == "PL11" and n == "B") else 0)
            w.player_funds = 1000.0
            if sc in ("PL8", "PL8b", "PL8c"):
                if sc == "PL8b":
                    w.known_at_start = {}
                w.player_script = {2: [("tip", "A", "Перевал"), ("bribe", "A", "B", 600.0)] if sc == "PL8" else
                                      [("bribe", "A", "B", 600.0)] if sc == "PL8b" else [("tip", "A", "Перевал")]}
                horizon = 40
            else:
                horizon = 40
                shock = lambda w: setattr(w.factions["B"], "shock", 45.0)
                if sc == "PL9":
                    w.scheduled = {22: [shock]}
                    w.player_script = {22: [("persuade", "B", "A")], 24: [("persuade", "B", "A")]}
                elif sc == "PL10":
                    w.factions["C"] = faction(p, "C", "Хранители", 30, 40, 0)   # третья сторона для NO_WAR
                    w.init_tiers(w.factions["C"])
                    w.publish_dos(w.factions["C"], phase=0)
                    w.regions.setdefault(w.factions["C"].home, p.region_start)
                    give_named(w, "C")
                    w.scheduled = {20: [lambda w: w.player_rep.__setitem__("B", 10.0)], 21: [shock],
                                   22: [lambda w: w.player_rep.__setitem__("B", 50.0), lambda w: w.betray("A", "B"), shock],
                                   24: [shock], 25: [shock]}
                    w.player_script = {20: [("persuade", "B", "A")], 21: [("persuade", "B", "A")], 22: [("persuade", "B", "A")],
                                       23: [("kill", "B", "B:вожак")], 24: [("persuade", "B", "A")], 25: [("persuade", "B", "C")]}
                else:   # PL11
                    w.scheduled = {21: [shock]}
                    w.player_script = {20: [("kill", "B", "B:офицер1")], 21: [("persuade", "B", "A")]}
        return w, horizon
    elif sc in ("EV26", "EV26b", "EV26c"):
        # spec 21b: обстановка войны WR7a (сломлены), WR7b (выдохлись), WR7c (цель достигнута); у A и B вожак и преемник
        base = {"EV26": "WR7a", "EV26b": "WR7b", "EV26c": "WR7c"}[sc]
        p = replace(p, evolution_enabled=True, leader_enabled=True, leader_kill_broken=True, evo_rule_order=(3, 5, 8))
        w, horizon = build(base, p)
        for n in ("A", "B"):
            give_named(w, n, ("Радикальный",))
        return w, horizon
    elif sc in CR_PIN:
        # spec 21c: чистая обстановка как EV_PIN, порядок правил полный (если сценарий не переопределил), оси задаёт подвязка
        order = CR_ORDER if p.evo_rule_order == Params().evo_rule_order else p.evo_rule_order
        p = replace(p, evolution_enabled=True, hunger_threshold=0.0, underpay_morale=0.0, raids_enabled=False, object_raids_enabled=False,
                    smuggling_enabled=False, fees_enabled=False, prisoner_sale_enabled=False, decisions_enabled=False,
                    archetype_assault_threshold={}, evo_m_recover=0.0, evo_c_relax=0.0, evo_rule_order=order)
        site = Site("Объект", 10, 0, 4, owner="A", income_disabled=True)
        spec = {   # сценарий: (уклад, объект, доктрина, сегменты подвязки (до тика, dos, шок, мораль, C), горизонт)
            "CR1": ("Хранители", False, 0, [(8, 15, 30, 25, 50)], 8),
            "CR2": ("Культисты", False, 0, [(20, 3, 26, 25, 30), (26, 3, 26, 50, 30)], 26),
            "CR3": ("Хранители", False, 0, [(8, 15, 22, 60, 80)], 8),
            "CR4": ("Regime", False, 0, [(8, 15, 22, 10, 80)], 8),
            "CR7": ("Хищники", True, 1, [(20, 18, 8, 60, 70), (24, 27, 8, 60, 70)], 24),
            "CR7k": ("Хищники", True, 0, [(20, 18, 8, 60, 70), (24, 27, 8, 60, 70)], 24),
            "CR8": ("Хищники", True, 2, [(30, 27, 0, 60, 50)], 30),
            "CR9": ("Хищники", False, 2, [(200, None, None, 0, None)], 200),
        }
        arche, with_site, doc, segs, horizon = spec[sc]
        if sc == "CR9":
            p = replace(p, hunger_threshold=10.0)    # голод и дезертирство работают, дохода нет
        w = World({"A": faction(p, "A", arche, 30, 3 if sc == "CR9" else 20, 10 if with_site else 0)}, [site] if with_site else [], p)
        w.factions["A"].doctrine = doc
        if sc == "CR8":
            p2 = replace(p, leader_enabled=True)
            w.p = p2
            give_named(w, "A", ("Осторожный",))
            w.player_script = {10: [("kill", "A", "A:вожак")]}
        if sc == "CR9":
            w.factions["A"].morale = 0.0        # M = 0 один раз; подвязки нет, иначе она обнуляла бы долг голода
        else:
            w.scheduled = {t: [ev_pins("A", segs)] for t in range(1, horizon + 1)}
        for f in w.factions.values():
            w.publish_dos(f, phase=0)
        return w, horizon
    elif sc in EV_LEADER or sc == "CR5":
        # spec 21b: чистая обстановка, правила 6 и 7 вынуты из стека (оси не вмешиваются), голод и каналы выключены, оси растут и тают как обычно
        p = replace(p, evolution_enabled=True, leader_enabled=True, hunger_threshold=0.0, underpay_morale=0.0, raids_enabled=False,
                    object_raids_enabled=False, smuggling_enabled=False, fees_enabled=False, prisoner_sale_enabled=False,
                    decisions_enabled=False, archetype_assault_threshold={}, evo_rule_order=(3, 5, 8))
        horizon = 20
        PV, NS = lambda n: Site(f"Перевал{n}", 40, 90, 4, owner=n), lambda n: Site(f"Насосная{n}", 15, 35, 2, owner=n)
        if sc in ("EV20", "EV21", "EV22", "EV23", "EV31", "CR5"):
            arche = {"EV22": "Хищники"}.get(sc, "Хранители")
            w = World({"A": faction(p, "A", arche, 30, 40, 10)}, [Site("Объект", 10, 0, 4, owner="A", income_disabled=True)], p)   # объект есть: иначе «зачистка базы» убила бы преемников
            succ = {"EV21": ("Радикальный",), "EV22": ("Осторожный",), "EV23": ("Радикальный", "Осторожный"), "CR5": ("Идеолог",)}.get(sc, ())
            give_named(w, "A", succ, officers=2 if sc == "EV31" else 0)
            if sc == "EV21":
                def prime(w):
                    f = w.factions["A"]
                    f.cooldown, f.pending, f.pending_ticks = 5, "Контролёры", 2
                w.scheduled = {9: [prime]}
                w.player_script = {10: [("kill", "A", "A:вожак")]}
            elif sc == "EV23":
                w.player_script = {10: [("kill", "A", "A:вожак")], 30: [("kill", "A", "A:преемник1")], 50: [("kill", "A", "A:преемник2")]}
                horizon = 60
            elif sc == "EV31":
                w.player_script = {10: [("kill", "A", "A:офицер1")], 12: [("kill", "A", "A:офицер1")]}
            else:
                w.player_script = {10: [("kill", "A", "A:вожак")]}
        elif sc in ("EV24", "EV30"):
            # A (Хищники 90) принудительно штурмует: тик 5 склад B, тик 6 не склад C, тик 7 объект D, склад которого в тайнике
            p = replace(p, leader_kill_seat=(sc == "EV24"))
            ss = [PV("B"), NS("B"), PV("C"), NS("C"), PV("D"), NS("D")]
            fs = {"A": faction(p, "A", "Хищники", 90, 60, 0), "B": faction(p, "B", "Хранители", 30, 40, 55),
                  "C": faction(p, "C", "Хранители", 30, 40, 55), "D": faction(p, "D", "Хранители", 30, 40, 55)}
            w = World(fs, ss, p)
            w.factions["D"].depot = "CACHE"
            for n in "BCD":
                give_named(w, n, ("Радикальный",))
            w.forced_assaults = {5: [("A", "ПеревалB")], 6: [("A", "НасоснаяC")], 7: [("A", "ПеревалD")]}
            if sc == "EV30":
                w.player_script = {20: [("kill", "B", "B:вожак")]}
                horizon = 25
            else:
                horizon = 12
        elif sc == "EV25":
            p = replace(p, leader_kill_seat=True)
            fs = {"A": faction(p, "A", "Хищники", 90, 60, 0), "B": faction(p, "B", "Хранители", 30, 40, 40)}
            w = World(fs, [PV("B")], p)
            give_named(w, "B", ("Радикальный",))
            w.forced_assaults = {5: [("A", "ПеревалB")]}
            horizon = 12
        elif sc == "EV27":
            p = replace(p, leader_kill_seat=True)
            fs = {"A": faction(p, "A", "Хранители", 30, 40, 55), "B": faction(p, "B", "Хищники", 90, 60, 0)}
            w = World(fs, [PV("A"), NS("A")], p)
            give_named(w, "A")
            w.player_script = {10: [("kill", "A", "A:вожак")], 20: [("kill", "A", "A:вожак")]}
            w.forced_assaults = {15: [("B", "ПеревалA")]}
            horizon = 25
        else:
            raise ValueError(sc)
    elif sc == "EV19":
        # spec 21a-4: Хищники без объектов, голод, решения и контрабанда включены, остальное выключено
        p = replace(p, evolution_enabled=True, raids_enabled=False, object_raids_enabled=False, fees_enabled=False,
                    prisoner_sale_enabled=False, archetype_assault_threshold={})
        w = World({"A": faction(p, "A", "Хищники", 30, 3, 0)}, [], p)
        w.factions["A"].morale = 40.0
        horizon = 8
    elif sc in EV_PIN or sc in EV_MECH:
        # spec 21a: чистая обстановка; оси в EV1–EV9 задаёт подвязка, голод, недоплата, рост C и M отключены
        p = replace(p, evolution_enabled=True, hunger_threshold=0.0, underpay_morale=0.0, raids_enabled=False,
                    object_raids_enabled=False, smuggling_enabled=False, fees_enabled=False,
                    prisoner_sale_enabled=False, decisions_enabled=False, archetype_assault_threshold={})
        if sc in EV_PIN:
            p = replace(p, evo_m_recover=0.0, evo_c_relax=0.0)
        site = Site("Объект", 10, 0, 4, owner="A", income_disabled=True)   # укомплектованный объект без дохода: «контроль актива» для правила 6
        if sc in ("EV2", "EV3", "EV5", "EV8"):
            arche = {"EV2": "Хищники", "EV3": "Хищники", "EV5": "Контролёры", "EV8": "Хранители"}[sc]
            w = World({"A": faction(p, "A", arche, 30, 20, 10)}, [site], p)
        elif sc == "EV7":
            site7 = Site("Объект", 10, 0, 4, owner="A", income_disabled=True)
            w = World({"A": faction(p, "A", "Дрейфующие", 30, 20, 10), "B": faction(p, "B", "Дрейфующие", 30, 20, 0),
                       "C": faction(p, "C", "Дрейфующие", 30, 20, 0)}, [site7], p)
        elif sc == "EV18":
            w = World({"A": faction(p, "A", "Хранители", 30, 20, 0), "B": faction(p, "B", "Хранители", 30, 20, 0)}, [], p)
            w.factions["A"].armory = 10.0   # нет оружия для налёта (< 25, docs/13)
        elif sc == "EV14":
            w = World({"A": faction(p, "A", "Хранители", 30, 40, 0)}, [], p)
            w.factions["A"].morale = 40.0
        elif sc == "EV17":
            ss = [Site("Дорогой", 40, 90, 4, owner="A"), Site("Дешёвый", 10, 20, 2)]
            w = World({"A": faction(p, "A", "Хранители", 30, 3, 40)}, ss, p)
        elif sc in ("EV15", "EV16"):
            site = Site("Перевал", 40, 90, 4, owner="B")
            p = replace(p, hunger_threshold=10.0)    # B голодает и теряет дезертиров
            w = World({"A": faction(p, "A", "Хищники", 90, 60, 0), "B": faction(p, "B", "Хранители", 30, 3, 40)}, [site], p)
            w.forced_assaults = {5: [("A", "Перевал")]}
            p = replace(p, evo_rule_order=(3, 5, 6, 8))   # правило 7 вынуто: сытый A иначе стал бы Хранителем и сменил покойное значение C
            w.p = p
        else:
            arche = {"EV1": "Хранители", "EV4": "Хищники", "EV6": "Хранители", "EV9": "Хранители"}[sc]
            w = World({"A": faction(p, "A", arche, 30, 20, 0)}, [], p)
        BAD, GOOD = (3, 60, 60, 40), (27, 8, 60, 50)   # EV9: dos, шок до затухания не используется (см. ev_pins), мораль, C
        pins = {
            "EV1": [(6, 5, 31, 60, 50)],
            "EV2": [(20, 9, 20, 60, 70), (24, 15, 20, 60, 70)],
            "EV3": [(1, 15, 4, 60, 70), (14, 3, 31, 60, 40)],
            "EV4": [(8, 27, 0, 60, 50)],
            "EV5": [(8, 15, 0, 15, 80)],
            "EV6": [(8, 15, 0, 10, 50)],
            "EV8": [(3, 3, 31, 60, 40), (11, 15, 2, 60, 70), (23, 15, 0, 20, 80), (35, 15, 0, 10, 30), (50, 27, 0, 10, 30)],
            "EV9": [(t, *( (3, 31, 60, 40) if (t - 1) // 25 % 2 == 0 else (27, 0, 60, 50) )) for t in range(25, 201, 25)],
        }
        if sc == "EV18":
            horizon = 8
            w.scheduled = {t: [ev_pins("A", [(8, 5, 31, 60, 50)]), ev_pins("B", [(8, 5, 31, 60, 50)])] for t in range(1, 9)}
        elif sc == "EV7":
            w.scheduled = {t: [ev_pins("A", [(12, 27, 0, 10, 20)]), ev_pins("B", [(12, 3, 31, 10, 20)]), ev_pins("C", [(12, 27, 0, 10, 20)])] for t in range(1, 13)}
            horizon = 12
        elif sc in pins:
            horizon = {"EV1": 6, "EV2": 24, "EV3": 14, "EV4": 8, "EV5": 8, "EV6": 8, "EV8": 50, "EV9": 200}[sc]
            w.scheduled = {t: [ev_pins("A", pins[sc])] for t in range(1, horizon + 1)}
        elif sc == "EV14":
            horizon = 20
        else:
            horizon = 20
    else:
        raise ValueError(sc)
    for f in w.factions.values():
        w.publish_dos(f, phase=0)
    if sc in RB_SCENARIOS:
        w.knowledge_step()   # обстановка RB: мотив считается до тика 1 (иначе он появился бы только после тика 1, мотив читается из прошлого тика)
    return w, horizon


def run(sc: str, p: Params | None = None, evo: bool | None = None):
    """evo: None = по умолчанию (прежние сценарии идут с evolution_enabled = False, новые EV — как задаёт build); True/False — явно (spec 21a-2 §1.4)."""
    if p is None:
        p = Params()
        if sc in RB_SCENARIOS or sc in SW_SCENARIOS or sc in EV_WORLD:
            p = replace(p, raid_discipline_enabled=True)   # spec 20: по умолчанию сценарии RB и SW идут с дисциплиной налётов; обратные проверки передают False явно
        if sc in SW_SCENARIOS or sc in WS_SCENARIOS or sc in EV_WORLD:
            p = replace(p, war_steers_attacks=True)   # spec 08d: по умолчанию сценарии WS идут с управлением; обратные проверки передают False явно
    if evo is None and not sc.startswith("EV"):
        evo = False   # прежние 70 сценариев проверяют механику при неизменном укладе; критерии не менять (spec 21a-2 §1.4)
    if evo is not None:
        p = replace(p, evolution_enabled=evo)
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
    elif sc in RB_SCENARIOS:
        obj = [e for e in w.events if e["kind"] == "raid_object"]
        sk = [e for e in w.events if e["kind"] == "raid_skipped"]
        reasons = {e["reason"] for e in sk}
        if sc == "RB1":
            res.append(("сытый не бьёт: налётов на объект нет", not obj, f"налётов {len(obj)}"))
            res.append(("в events есть raid_skipped NO_MOTIVE", "NO_MOTIVE" in reasons, f"причины: {sorted(reasons)}"))
        elif sc == "RB2":
            res.append(("сценарий валиден: A нуждается", w.factions["A"].days_supply < p.hunger_threshold, f"запас A {w.factions['A'].days_supply:.1f} суток"))
            res.append(("без знания налётов на объект нет", not obj, f"налётов {len(obj)}"))
            res.append(("в events есть raid_skipped NO_MOTIVE", "NO_MOTIVE" in reasons, f"причины: {sorted(reasons)}"))
        elif sc == "RB3":
            res.append(("нуждающийся со знанием: первый налёт на тике 1", bool(obj) and obj[0]["tick"] == 1 and obj[0]["site"] == "Перевал", f"налёты: {[(e['tick'], e['site']) for e in obj]}"))
        elif sc == "RB4":
            on = [e["tick"] for e in obj if e["site"] == "Перевал"]
            res.append(("налёты на тот же объект на тиках 1, 16, 31", on == [1, 16, 31], f"тики налётов: {on}"))
            res.append(("между ними raid_skipped причины PAUSE", "PAUSE" in reasons, f"причины: {sorted(reasons)}"))
        else:
            res.append(("доля пула каждого объекта B ниже порога: налётов нет", not obj, f"налётов {len(obj)}"))
            res.append(("в events есть raid_skipped PLUNDERED", "PLUNDERED" in reasons, f"причины: {sorted(reasons)}"))
    elif sc in SW_SCENARIOS:
        alive = {n: f.manpower for n, f in w.factions.items()}
        obj = [e for e in w.events if e["kind"] == "raid_object"]
        sk = {}
        for e in w.events:
            if e["kind"] == "raid_skipped":
                sk[e["reason"]] = sk.get(e["reason"], 0) + 1
        res.append(("на тике 500 у каждой из 6 фракций людей больше нуля", all(v > 0 for v in alive.values()),
                    f"людей: {alive}; налётов на объекты {len(obj)}, штурмов {len([e for e in w.events if e['kind'] == 'assault'])}, войн {len([e for e in w.events if e['kind'] == 'war_declared'])}, пропусков {sk}"))
    elif sc in CR_SCENARIOS:
        ch = [(e["tick"], e["frm"], e["to"], e["rule"]) for e in w.events if e["kind"] == "archetype_change"]
        A = w.factions["A"]
        def ok_(name, cond, det):
            res.append((name, bool(cond), det))
        if sc == "CR1":
            ok_("Культисты ровно на тике 5 по правилу 4", ch == [(5, "Хранители", "Культисты", 4)], f"смены: {ch}")
        elif sc == "CR2":
            ok_("20 тиков Культисты, затем при M = 50 Хищники через 3 тика (тик 23, правило 5)", ch == [(23, "Культисты", "Хищники", 5)], f"смены: {ch}")
        elif sc == "CR3":
            ok_("Regime ровно на тике 5 по правилу 9", ch == [(5, "Хранители", "Regime", 9)], f"смены: {ch}")
        elif sc == "CR4":
            ok_("правило 9 молчит (M < 25), правило 3: Хранители на тике 5", ch == [(5, "Regime", "Хранители", 3)], f"смены: {ch}")
        elif sc == "CR5":
            ok_("Идеолог: Культисты на тике 11 по правилу 2, вожак — преемник", ch == [(11, "Хранители", "Культисты", 2)] and A.leader == "A:преемник1", f"смены: {ch}; вожак: {A.leader}")
        elif sc == "CR7k":
            ok_("доктрина 0 (контроль): на тике 1 Контролёры по правилу 6", ch[:1] == [(1, "Хищники", "Контролёры", 6)], f"смены: {ch}")
        elif sc == "CR7":
            ok_("доктрина 1: до тика 20 смены нет (выход закрыт: R <= 65 и P >= 10)", not [x for x in ch if x[0] <= 20], f"смены: {ch}")
            ok_("после R = 90 (тик 21) смена на Контролёров", ch[:1] == [(21, "Хищники", "Контролёры", 6)], f"смены: {ch}")
        elif sc == "CR8":
            ok_("доктрина 2: до тика 10 уклад Хищники, хотя правило 7 хочет Хранителей", not [x for x in ch if x[0] <= 10] and A.doctrine == 2, f"смены: {ch}")
            ok_("убийство вожака пробивает доктрину: Хранители на тике 11, RULE_2", ch == [(11, "Хищники", "Хранители", 2)], f"смены: {ch}")
        elif sc == "CR9":
            ok_("доктрина 2 при M = 0: уклад не менялся", not ch and A.archetype == "Хищники", f"смены: {ch}")
            ok_("людей к тику 200 нет: доктрина не делает фракцию вечной", A.manpower == 0, f"людей: {A.manpower}, дезертировало {A.deserted}")
    elif sc in PL_SCENARIOS:
        pf = [(e["tick"], e["action"], e["code"]) for e in w.events if e["kind"] == "player_failed"]
        wd = [(e["tick"], e["initiator"], e["victim"]) for e in w.events if e["kind"] == "war_declared"]
        we = [(e["tick"], e["reason"]) for e in w.events if e["kind"] == "war_end"]
        def rows(target, reason=None):
            return [r for r in w.log if r[3] == target and (reason is None or r[6] == reason)]
        def ok_(name, cond, det):
            res.append((name, bool(cond), det))
        if sc == "PL1":
            br = rows("rel.A>B.i", "PLAYER_BRIBE")
            ok_("i(A→B) = 3.0 строкой PLAYER_BRIBE", [(r[0], r[5]) for r in br] == [(2, 3.0)], f"строки: {br}")
            hr = rows("rel.A>B.H")
            ok_("H(A→B) на тике подкупа = база + 3.0", bool(hr) and hr[0][0] == 2 and hr[0][5] == w.base_h("A", "B") + 3.0, f"H: {[(r[0], r[5]) for r in hr]}, база {w.base_h('A', 'B')}")
            ok_("деньги 1000 → 700 (PLAYER_BRIBE)", [(r[0], r[4], r[5]) for r in rows("player.funds", "PLAYER_BRIBE")] == [(2, 1000.0, 700.0)], f"деньги: {rows('player.funds')}")
        elif sc == "PL2":
            br = rows("rel.A>B.i", "PLAYER_BRIBE")
            ok_("после второго подкупа i = 6.0 (потолок)", [r[5] for r in br] == [3.0, 6.0], f"строки: {br}")
            ok_("за второй подкуп списано только за прирост до потолка (400), остальное у игрока", [(r[0], r[4] - r[5]) for r in rows("player.funds", "PLAYER_BRIBE")] == [(2, 300.0), (12, 400.0)] and w.player_funds == 2300.0,
                f"деньги: {rows('player.funds')}, итого {w.player_funds}")
        elif sc == "PL3":
            iv = {n: [r[5] for r in rows(f"rel.{n}>B.i", "PLAYER_BRIBE")] for n in "ACD"}
            ok_("на 300: Основатель +3.0, Радикальный +6.0, Осторожный +1.5", iv == {"A": [3.0], "C": [6.0], "D": [1.5]}, f"добавки: {iv}")
        elif sc == "PL4":
            ok_("подкуп и подсказка отказаны NO_LEADER, деньги целы", pf == [(5, "bribe", "NO_LEADER"), (5, "tip", "NO_LEADER")] and w.player_funds == 1000.0, f"отказы: {pf}, деньги {w.player_funds}")
        elif sc == "PL5":
            ok_("NO_FUNDS, ничего не изменилось", pf == [(2, "bribe", "NO_FUNDS")] and w.player_funds == 100.0 and not w.rel, f"отказы: {pf}")
        elif sc == "PL6":
            br = rows("rel.A>B.i", "PLAYER_BRIBE")
            ok_("на тике 7 COOLDOWN, на тике 12 подкуп проходит", pf == [(7, "bribe", "COOLDOWN")] and [r[0] for r in br] == [2, 12], f"отказы: {pf}, подкупы: {[r[0] for r in br]}")
        elif sc == "PL7":
            dec = rows("rel.A>B.i", "INCITE_DECAY")
            ok_("i = 6.0 затухает до 0 за 60 тиков по 1.0 каждые 10", [(r[0], r[5]) for r in dec] == [(10, 5.0), (20, 4.0), (30, 3.0), (40, 2.0), (50, 1.0), (60, 0.0)] and w.rel[("A", "B")].i == 0.0, f"затухание: {[(r[0], r[5]) for r in dec]}")
        elif sc == "PL8":
            ok_("после подсказки и подкупа война A>B объявлена", any(x[1:] == ("A", "B") for x in wd), f"войны: {wd}")
        elif sc == "PL8b":
            ok_("подкуп без подсказки и без знания: войны нет", not wd, f"войны: {wd}")
        elif sc == "PL8c":
            ok_("подсказка без подкупа: войны нет", not wd, f"войны: {wd}")
        elif sc == "PL9":
            ok_("убеждение на тике 22: война закрыта WAR_END_PLAYER, победителя и репараций нет", we and we[0] == (22, "WAR_END_PLAYER") and not [e for e in w.events if e["kind"] == "war_end" and (e["winner"] or e["reparations"])], f"концы: {we}")
            tr = [r for r in w.log if r[3].startswith("truce.") and r[6] == "TRUCE"]
            ok_("перемирие war_truce стартовало на тике 22", any(r[0] == 22 and r[5] == 22 + w.p.war_truce for r in tr), f"перемирия: {tr}")
            ok_("новой войны пары до конца перемирия нет; повтор на тике 24 — COOLDOWN", not [x for x in wd if 22 < x[0] < 22 + w.p.war_truce] and pf == [(24, "persuade", "COOLDOWN")], f"войны: {wd}; отказы: {pf}")
        elif sc == "PL10":
            ok_("отказы по порядку: NO_SHOCK, LOW_REP, ARCHNEMESIS, NO_LEADER, NO_WAR", [x[2] for x in pf] == ["NO_SHOCK", "LOW_REP", "ARCHNEMESIS", "NO_LEADER", "NO_WAR"], f"отказы: {pf}")
            ok_("во всех случаях война идёт (до тика 26 не закрыта)", not [x for x in we if x[0] <= 26] and wd, f"войны: {wd}, концы: {we}")
        elif sc == "PL11":
            rp = rows("player.rep.B", "PLAYER_KILL")
            ok_("убийство офицера: репутация B 50 → 20", [(r[4], r[5]) for r in rp] == [(50.0, 20.0)], f"репутация: {rp}")
            ok_("persuade(B, A) → LOW_REP, хотя шок и война есть; война идёт", pf == [(21, "persuade", "LOW_REP")] and not [x for x in we if x[0] <= 21], f"отказы: {pf}, концы: {we}")
    elif sc in EV_LEADER:
        ch = [(e["tick"], e["faction"], e["frm"], e["to"], e["rule"]) for e in w.events if e["kind"] == "archetype_change"]
        lk = [(e["tick"], e["faction"], e["reason"]) for e in w.events if e["kind"] == "leader_killed"]
        sk = [e for e in w.events if e["kind"] == "player_skipped"]
        def rows(target, reason=None):
            return [r for r in w.log if r[3] == target and (reason is None or r[6] == reason)]
        def ok_(name, cond, det):
            res.append((name, bool(cond), det))
        A = w.factions["A"]
        if sc == "EV20":
            ok_("на тике 11 Дрейфующие по правилу 1, других смен нет", ch == [(11, "A", "Хранители", "Дрейфующие", 1)], f"смены: {ch}")
            ok_("вожака нет", A.leader is None, f"вожак: {A.leader}")
            ok_("в журнале C -30 и M -10 на тике 11 (LEADER_LOST)", [(r[0], r[4], r[5]) for r in rows("A.ctl", "LEADER_LOST")] == [(11, 50.0, 20.0)] and [(r[0], r[4], r[5]) for r in rows("A.morale", "LEADER_LOST")] == [(11, 70.0, 60.0)],
                f"C: {rows('A.ctl', 'LEADER_LOST')}; M: {rows('A.morale', 'LEADER_LOST')}")
            ok_("людей столько же (30), Manpower гибелью вожака не менялся", A.manpower == 30, f"людей: {A.manpower}")
        elif sc == "EV21":
            cd = [r for r in rows("A.cooldown") if r[0] in (10, 11)]
            ok_("к тику 10 пауза идёт (cooldown > 0)", any(r[0] == 10 and r[5] > 0 for r in cd), f"cooldown: {cd}")
            ok_("правило 2: на тике 11 Хищники, пауза пробита", ch == [(11, "A", "Хранители", "Хищники", 2)], f"смены: {ch}")
            ok_("pending сброшен на тике 11", [(r[0], r[4], r[5]) for r in rows("A.pending") if r[0] == 11] == [(11, "Контролёры", None)] and A.pending is None and A.pending_ticks == 0,
                f"pending: {rows('A.pending')}; ticks: {rows('A.pending_ticks')}")
            ok_("новая пауза 7 (RULE_2)", [(r[0], r[5]) for r in rows("A.cooldown", "RULE_2")] == [(11, 7)], f"cooldown: {rows('A.cooldown', 'RULE_2')}")
        elif sc == "EV22":
            ok_("Хищники → Хранители по правилу 2 на тике 11", ch == [(11, "A", "Хищники", "Хранители", 2)], f"смены: {ch}")
            ok_("вожак — Осторожный преемник", A.leader == "A:преемник1", f"вожак: {A.leader}")
        elif sc == "EV23":
            ok_("Хищники, Хранители, затем Дрейфующие (тики 11, 31, 51)", ch == [(11, "A", "Хранители", "Хищники", 2), (31, "A", "Хищники", "Хранители", 2), (51, "A", "Хранители", "Дрейфующие", 1)], f"смены: {ch}")
            ok_("вожаки по порядку: преемник1, преемник2, затем никого", [r[5] for r in rows("A.leader") if r[5] is not None] == ["A:преемник1", "A:преемник2"] and A.leader is None,
                f"вожаки: {[r[5] for r in rows('A.leader')]}")
        elif sc == "EV24":
            ok_("убит только вожак B (склад), смена B на тике 6 по правилу 2", lk == [(5, "B", "LEADER_SEAT")] and ch == [(6, "B", "Хранители", "Хищники", 2)], f"гибели: {lk}; смены: {ch}")
            ok_("штурм не склада (C) и склад в тайнике (D): вожаки живы, смен нет", w.factions["C"].leader == "C:вожак" and w.factions["D"].leader == "D:вожак",
                f"C: {w.factions['C'].leader}, D: {w.factions['D'].leader}")
            asl = [(e["tick"], e["defender"], e["attacker_wins"]) for e in w.events if e["kind"] == "assault"]
            ok_("все три штурма состоялись и атакующий победил", asl == [(5, "B", True), (6, "C", True), (7, "D", True)], f"штурмы: {asl}")
        elif sc == "EV25":
            B = w.factions["B"]
            ok_("зачистка базы: правило 1, а не 2", ch == [(6, "B", "Хранители", "Дрейфующие", 1)] and w.rule_hits == {1: 1}, f"смены: {ch}; правила: {w.rule_hits}")
            ok_("преемник погиб вместе с вожаком", not any(n["alive"] for n in B.named), f"именные: {[(n['name'], n['alive']) for n in B.named]}")
        elif sc in ("EV26", "EV26b", "EV26c"):
            we = [(e["tick"], e["reason"]) for e in w.events if e["kind"] == "war_end"]
            if sc == "EV26":
                ok_("война закончилась «сломлены»", [x[1] for x in we] == ["WAR_END_BROKEN"], f"концы войн: {we}")
                ok_("вожак проигравшего (B) убит, смена по правилу 2", len(lk) == 1 and lk[0][1:] == ("B", "LEADER_BROKEN") and (lk[0][0] + 1, "B") == (ch[0][0], ch[0][1]) and ch[0][4] == 2, f"гибели: {lk}; смены: {ch}")
            else:
                want = {"EV26b": "WAR_END_EXHAUSTED", "EV26c": "WAR_END_GOAL"}[sc]
                ok_(f"война закончилась по причине {want}", [x[1] for x in we] == [want], f"концы войн: {we}")
                ok_("вожаки обеих сторон живы", not lk and w.factions["A"].leader and w.factions["B"].leader, f"гибели: {lk}")
        elif sc == "EV27":
            ok_("правило 1 сработало ровно один раз", w.rule_hits.get(1) == 1 and len(lk) == 1, f"правила: {w.rule_hits}; гибели: {lk}")
            ok_("второе убийство мёртвого вожака пропущено", len(sk) == 1, f"пропусков: {len(sk)}")
            asl = [(e["tick"], e["defender"], e["attacker_wins"]) for e in w.events if e["kind"] == "assault"]
            ok_("потеря склада Дрейфующими (штурм на тике 15) новых гибелей не создала", asl == [(15, "A", True)] and len(lk) == 1, f"штурмы: {asl}; гибели: {lk}")
        elif sc == "EV30":
            asl = [(e["tick"], e["defender"], e["attacker_wins"]) for e in w.events if e["kind"] == "assault"]
            ok_("штурм склада B на тике 5 состоялся, вожак не убит (по умолчанию «заперт»)", (5, "B", True) in asl and not [x for x in lk if x[0] < 20], f"штурмы: {asl}; гибели: {lk}")
            ok_("убил вожака только игрок (тик 20), смена B на тике 21", lk == [(20, "B", "LEADER_PLAYER")] and ch == [(21, "B", "Хранители", "Хищники", 2)], f"гибели: {lk}; смены: {ch}")
        elif sc == "EV31":
            off = [e for e in w.events if e["kind"] == "officer_killed"]
            ok_("офицер убит: ярус офицеров 3 → 2", len(off) == 1 and A.off == 2, f"офицеров: {A.off}; события: {len(off)}")
            ok_("вожак жив, уклад не менялся", A.leader == "A:вожак" and not ch, f"вожак: {A.leader}; смены: {ch}")
            ok_("повторное убийство того же пропущено", len(sk) == 1, f"пропусков: {len(sk)}")
    elif sc in EV_SCENARIOS:
        ch = [e for e in w.events if e["kind"] == "archetype_change"]
        mine = lambda n: [(e["tick"], e["frm"], e["to"], e["rule"]) for e in ch if e["faction"] == n]
        def rows(target, reason=None):
            return [r for r in w.log if r[3] == target and (reason is None or r[6] == reason)]
        def ok_(name, cond, det):
            res.append((name, bool(cond), det))
        if sc == "EV1":
            a = mine("A")
            ok_("смена на Хищников ровно на тике 3 по правилу 5, до этого уклад не менялся", a == [(3, "Хранители", "Хищники", 5)], f"смены: {a}")
            ok_("pending = Хищники на тиках 1 и 2", [(r[0], r[5]) for r in rows("A.pending") if r[0] <= 2] == [(1, "Хищники")], f"pending: {[(r[0], r[5]) for r in rows('A.pending')]}")
        elif sc == "EV19":
            ex = [e for e in w.events if e["kind"] == "expel"]
            sm = [r for r in w.log if r[6] == "SMUGGLING" and r[3] == "A.supply"]
            ok_("за 8 тиков изгнаний нет", not ex, f"изгнаний: {len(ex)}")
            ok_("контрабанда идёт (строки SMUGGLING есть)", bool(sm), f"строк SMUGGLING: {len(sm)}")
        elif sc == "EV18":
            ok_("с оружием 50 и 30 людьми B уходит в Хищники на тике 3", mine("B") == [(3, "Хранители", "Хищники", 5)], f"B: {mine('B')}")
            ok_("с оружием 10 A при тех же осях остаётся Хранителем: хищничать нечем", mine("A") == [], f"A: {mine('A')}")
        elif sc == "EV2":
            a = mine("A")
            ok_("тиков 1–20 уклад Хищники, смены нет: гистерезис держит", not [x for x in a if x[0] <= 20], f"смены: {a}")
            ok_("pending пуст до тика 20 (кандидат есть, выход закрыт)", not [r for r in rows("A.pending") if r[0] <= 20], f"pending: {[(r[0], r[5]) for r in rows('A.pending') if r[0] <= 20]}")
            ok_("на тике 21 смена на Контролёров (выход открыт, выдержка 1, правило 6)", a == [(21, "Хищники", "Контролёры", 6)], f"смены: {a}")
        elif sc == "EV3":
            a = mine("A")
            gap = a[1][0] - a[0][0] if len(a) >= 2 else None
            ok_("две смены: тик 1 (правило 6) и тик 11 (правило 5)", [(x[0], x[3]) for x in a] == [(1, 6), (11, 5)], f"смены: {a}")
            ok_("зазор между сменами не меньше 8 тиков (7 суток паузы и тик проверки; здесь ещё выдержка 3)", gap is not None and gap >= 8, f"зазор: {gap}")
        elif sc == "EV4":
            a = mine("A")
            ok_("смена на Хранителей ровно через 5 тиков по правилу 7", a == [(5, "Хищники", "Хранители", 7)], f"смены: {a}")
            sh = rows("A.morale", "SHARE_SHOCK")
            ok_("цена перемены: доля 0.35 → 0, ΔM = −(0.35 − 0) × 60 = −21 (формула 06 буквально), мораль 60 → 39", len(sh) == 1 and abs(sh[0][5] - 39.0) < 1e-6 and sh[0][4] == 60.0, f"строки: {[(r[0], r[4], r[5]) for r in sh]}")
        elif sc == "EV5":
            a = mine("A")
            ok_("бунт: Контролёры → Хранители ровно через 5 тиков по правилу 3", a == [(5, "Контролёры", "Хранители", 3)], f"смены: {a}")
            sh = rows("A.morale", "SHARE_SHOCK")
            ok_("мораль после смены на 6 ниже (0.10 × 60): 15 → 9", len(sh) == 1 and abs(sh[0][4] - sh[0][5] - 6.0) < 1e-6, f"строки: {[(r[0], r[4], r[5]) for r in sh]}")
        elif sc == "EV6":
            a = mine("A")
            ok_("catch-all: Хранители → Дрейфующие через 5 тиков по правилу 8", a == [(5, "Хранители", "Дрейфующие", 8)], f"смены: {a}")
            ok_("доли обе 0: цены перемены нет", not rows("A.morale", "SHARE_SHOCK"), f"строки: {rows('A.morale', 'SHARE_SHOCK')}")
        elif sc == "EV7":
            ok_("Дрейфующие с объектом при R = 90, P = 0 уходят в Хранители через 5 тиков (правило 7 выше правила 8)", mine("A") == [(5, "Дрейфующие", "Хранители", 7)], f"A: {mine('A')}")
            ok_("Дрейфующие при R = 10, P = 78 уходят в Хищники через 3 тика (правило 5, объект не нужен)", mine("B") == [(3, "Дрейфующие", "Хищники", 5)], f"B: {mine('B')}")
            ok_("Дрейфующие без объекта при R = 90 остаются Дрейфующими 12 тиков (ловушка закрыта)", mine("C") == [], f"C: {mine('C')}")
        elif sc == "EV8":
            a = mine("A")
            want = [("Хранители", "Хищники", 5), ("Хищники", "Контролёры", 6), ("Контролёры", "Хранители", 3), ("Хранители", "Дрейфующие", 8), ("Дрейфующие", "Хранители", 7)]
            ok_("цикл: 5 смен с причинами RULE_5, RULE_6, RULE_3, RULE_8, RULE_7 и возврат в Хранители", [(x[1], x[2], x[3]) for x in a] == want, f"смены: {a}")
            gaps = [a[i + 1][0] - a[i][0] for i in range(len(a) - 1)]
            ok_("зазор между сменами нигде не меньше 8 тиков", bool(gaps) and min(gaps) >= 8, f"зазоры: {gaps}")
        elif sc == "EV9":
            a = mine("A")
            gaps = [a[i + 1][0] - a[i][0] for i in range(len(a) - 1)]
            back = sum(1 for x in a if x[2] == "Хранители")
            ok_("туда и обратно не меньше двух раз (смен на Хищников и обратно)", sum(1 for x in a if x[2] == "Хищники") >= 2 and back >= 2, f"смены: {[(x[0], x[2]) for x in a]}")
            ok_("смены реже раза в 10 тиков", bool(gaps) and min(gaps) >= 10, f"зазоры: {gaps}")
            ok_("уклад не залип: смена происходит и после тика 150", any(x[0] > 150 for x in a), f"последняя смена: {a[-1][0] if a else None}")
        elif sc in EV_WORLD:
            gaps_all = {}
            for n in w.factions:
                a = mine(n)
                gaps_all[n] = min([a[i + 1][0] - a[i][0] for i in range(len(a) - 1)] or [999])
            ok_("ни у одной фракции смены чаще, чем через 8 тиков", min(gaps_all.values()) >= 8, f"минимальные зазоры: {gaps_all}")
            def mirror(f):
                last = [r for r in w.log if r[3] == f"{f.name}.pending"]
                return last[-1][5] if last else None
            ok_("pending в конце равен восстановленному из журнала", all(f.pending == mirror(f) for f in w.factions.values()), "зеркало совпало" if all(f.pending == mirror(f) for f in w.factions.values()) else "расхождение")
            summary = {n: (f.archetype, f.changes, f.manpower) for n, f in w.factions.items()}
            if sc == "EV13":
                dead_early = [n for n, f in w.factions.items() if f.manpower == 0 and f.changes < 2]
                ok_("нет вымирания раньше двух смен (docs/07 S3)", not dead_early, f"вымерли с менее чем двумя сменами: {dead_early}; итог (уклад, смен, людей): {summary}")
                ok_("Дрейфующие X6 к тику 500 живы (spec 21a-2)", w.factions["X6"].manpower > 0, f"X6: уклад {w.factions['X6'].archetype}, людей {w.factions['X6'].manpower}, смен {w.factions['X6'].changes}, объектов {len(w.owned(w.factions['X6']))}")
            else:
                ok_("итог мира измерен (уклад, смен, людей)", True, f"{summary}")
        elif sc == "EV14":
            mo = {r[0]: r[5] for r in rows("A.morale")}
            ok_("сытая фракция: мораль 40 → 60 к тику 20 (по +1 в сутки)", abs(w.factions["A"].morale - 60.0) < 1e-6, f"мораль в конце {w.factions['A'].morale}")
            ok_("уклад не менялся (R высокая, P = 0, правило 7 даёт тот же уклад)", not ch, f"смены: {mine('A')}")
        elif sc == "EV15":
            cw = [(r[0], r[4], r[5]) for r in rows("A.ctl", "C_WIN")]
            ok_("победа в штурме на тике 5: C победителя +10 на тике 6", len(cw) == 1 and cw[0][0] == 6 and abs(cw[0][2] - cw[0][1] - 10.0) < 1e-6, f"строки C_WIN: {cw}")
            mw = [(r[0], r[4], r[5]) for r in rows("A.morale", "M_WIN")]
            ok_("победа поднимает мораль победителя на 5", len(mw) == 1 and abs(mw[0][2] - mw[0][1] - 5.0) < 1e-6, f"строки M_WIN: {mw}")
            rl = [(r[0], r[4], r[5]) for r in rows("A.ctl", "C_RELAX")]
            ok_("после победы C тянется к покойному 40 на 1 в сутки", bool(rl) and all(abs(x[1] - x[2] - 1.0) < 1e-6 for x in rl), f"строки C_RELAX: {rl[:4]}…")
            cd = [(r[0], r[4], r[5]) for r in rows("B.ctl", "C_DESERTION")]
            ok_("дезертир опускает C на 1", bool(cd) and all(abs(x[1] - x[2] - 1.0) < 1e-6 for x in cd), f"строки C_DESERTION: {cd}")
        elif sc == "EV16":
            tb = [(r[0], r[4], r[5]) for r in rows("B.tshock")]
            ok_("B потеряла объект на тике 5: tshock 0 → 25 на тике 6, затем 17, 9, 1, 0", [(x[0], x[2]) for x in tb] == [(6, 25.0), (7, 17.0), (8, 9.0), (9, 1.0), (10, 0.0)], f"строки B.tshock: {tb}")
            ok_("у победителя A территориального шока нет", not rows("A.tshock"), f"строки A.tshock: {rows('A.tshock')}")
            pb = [(r[0], r[5]) for r in rows("B.ax_p") if r[0] == 6]
            ok_("P у B на тике 6 не ниже 62.5 (2.5 × 25 одного территориального шока)", bool(pb) and pb[-1][1] >= 62.5 - 1e-6, f"B.ax_p на тике 6: {pb}")
        elif sc == "EV17":
            ta = [(r[0], r[4], r[5]) for r in rows("A.tshock")]
            ok_("сдача актива на тике 1: tshock 0 → 25 на тике 2, затем падает на 8", ta[:2] == [(2, 0.0, 25.0), (3, 25.0, 17.0)], f"строки A.tshock: {ta[:4]}")
    return res, m


def evaluate(sc: str, p: Params | None = None):
    w, series = run(sc, p)
    res, m = check(sc, w, series)
    return all(ok for _, ok, _ in res), res, m, w, series


def cr6(p=None):
    """CR6: обход стека с правилами 4 и 9. Возвращает (ok, деталь)."""
    from . import evolution as evo
    p = replace(p or Params(), evo_rule_order=CR_ORDER)
    bad = evo.shadowed(p) + evo.dead(p)
    q = replace(Params(), evo_rule_order=(8, 3, 4, 5, 6, 7, 9))
    sh = evo.shadowed(q)
    w = evo.walk(p)
    return (not bad and bool(sh)), (f"полный порядок: мёртвых и затенённых нет ({'да' if not bad else bad}); полосы по M первым срабатыванием: "
                                  f"{ {x: d['band_first'] for x, d in w.items()} }; при порядке (8, 3, 4, 5, 6, 7, 9) затенены {sh}")


def ev10(p=None):
    """EV10: обход стека. Возвращает (ok, деталь)."""
    from . import evolution as evo
    p = p or Params()
    w = evo.walk(p)
    bad = evo.shadowed(p) + evo.dead(p)
    q = replace(Params(), evo_rule_order=(8, 3, 5, 6, 7))
    sh = evo.shadowed(q)
    wq = evo.walk(q)
    ok = not bad and sh == [3, 5, 6, 7]
    return ok, (f"по умолчанию: мёртвых и затенённых нет ({'да' if not bad else bad}); полосы по M первым срабатыванием: "
                f"{ {x: d['band_first'] for x, d in w.items()} }; при порядке (8, 3, 5, 6, 7) затенены {sh}, бунт срабатывает первым только в M {wq[3]['band_first']} вместо {wq[3]['band_any']}")


def ev11(scenarios):
    """EV11: достижимость правил в динамике по прежним сценариям. Возвращает (ok, деталь, счётчики по K)."""
    out = {}
    for k in (0.3, 0.0):
        hits = {}
        for sc in scenarios:
            w, _ = run(sc, replace(Params(), morale_hunger_k=k), evo=True)
            for r, n in w.rule_hits.items():
                hits[r] = hits.get(r, 0) + n
        out[k] = hits
    ok = all(out[k].get(5, 0) > 0 for k in out)
    return ok, f"правило 5 сработало первым: при K=0.3 {out[0.3].get(5, 0)} раз, при K=0 {out[0.0].get(5, 0)}; все правила: K=0.3 {dict(sorted(out[0.3].items()))}, K=0 {dict(sorted(out[0.0].items()))}", out


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
    "R35": (replace(Params(), raid_discipline_enabled=False), ("RB1",), "налёты без дисциплины (сытый бьёт)"),
    "R36": (replace(Params(), raid_discipline_enabled=False), ("SW1",), "мир без дисциплины налётов (Дрейфующие вымирают)"),
    "R37": (replace(Params(), raid_pause=0), ("RB4",), "пауза после налёта на ту же цель выключена"),
    "R38": (replace(Params(), raid_min_loot_share=0.0), ("RB5",), "разграбленный объект тоже бьют"),
    "R39": (replace(Params(), evo_hysteresis=False), ("EV2",), "условия выхода не проверяются (гистерезиса нет)"),
    "R40": (replace(Params(), evo_cooldown=0), ("EV3",), "паузы после смены нет"),
    "R41": (replace(Params(), evo_dwell_scale=0.0), ("EV1",), "выдержки нет (смена на первом тике условия)"),
    "R42": (replace(Params(), evo_share_shock_k=0.0), ("EV5",), "смена уклада не бьёт по морали"),
    "R43": (replace(Params(), evo_rule_order=(8, 3, 5, 6, 7)), ("EV5",), "catch-all (правило 8) стоит первым"),
    "R44": (replace(Params(), evo_m_recover=0.0), ("EV14",), "мораль не растёт"),
    "R46": (replace(Params(), evo_drifter_needs_site=False), ("EV7",), "Дрейфующие без объекта тоже уходят по правилу 7 (ловушка открыта)"),
    "R49": (replace(Params(), predators_keep_without_site=False), ("EV19",), "Хищники без объектов изгоняют людей как раньше"),
    "R48": (replace(Params(), evo_rule5_needs_force=False), ("EV18",), "вход в Хищники не требует сил для налёта"),
    "R47": (replace(Params(), evo_t_site=0.0), ("EV16",), "потеря объекта не даёт территориального шока"),
    "R45": (replace(Params(), evo_c_win=0.0), ("EV15",), "победа не поднимает C"),
    "R63": (replace(Params(), doctrine_gap_mult=1.0), ("CR7",), "доктрина 1 не удваивает зазор выхода"),
    "R64": (replace(Params(), doctrine2_freezes=False), ("CR8",), "доктрина 2 не замораживает выход"),
    "R65": (replace(Params(), evo_hysteresis=False), ("CR2",), "условия выхода не проверяются"),
    "R66": (replace(Params(), evo_dwell_scale=0.0), ("CR1",), "выдержки нет"),
    "R67": (replace(Params(), evo_rule_order=(9, 3, 4, 5, 6, 7, 8), evo_rule9_m=0.0), ("CR4",), "правило 9 выше бунта и без M >= 25"),
    "R68": (replace(Params(), succession_arch={"Осторожный": "Хранители", "Радикальный": "Хищники", "Идеолог": "Хищники"}), ("CR5",), "Идеолог даёт Хищников, не Культистов"),
    "R55": (replace(Params(), incite_cap=1e9), ("PL2",), "потолок добавки снят"),
    "R56": (replace(Params(), bribe_cooldown=0), ("PL6",), "остывания подкупа нет"),
    "R57": (replace(Params(), persuade_min_shock=0.0), ("PL10",), "порог шока для убеждения 0"),
    "R58": (replace(Params(), persuade_min_rep=0.0), ("PL11",), "порог репутации для убеждения 0"),
    "R59": (replace(Params(), incite_decay_every=10**9), ("PL7",), "добавка не затухает"),
    "R60": (replace(Params(), bribe_profile_mult={}), ("PL3",), "профиль вожака не влияет на цену"),
    "R61": (replace(Params(), persuade_block_archnemesis=False), ("PL10",), "труа доступна при Archnemesis"),
    "R62": (replace(Params(), bribe_gives_knowledge=True), ("PL8b",), "подкуп сам даёт знание (подсказка не нужна)"),
    "R50": (replace(Params(), succession_ignores_cooldown=False), ("EV21",), "ApplySuccession не пробивает паузу"),
    "R51": (replace(Params(), succession_resets_pending=False), ("EV21",), "ApplySuccession не сбрасывает pending"),
    "R52": (replace(Params(), leader_wipe_kills_successors=False), ("EV25",), "при зачистке базы преемник жив"),
    "R53": (replace(Params(), leader_kill_any_war_end=True), ("EV26b", "EV26c"), "вожак гибнет при любом конце войны"),
    "R54": (replace(Params(), leader_kill_any_site=True), ("EV24",), "штурм любого объекта убивает вожака"),
}
