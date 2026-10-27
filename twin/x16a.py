"""Задача 16a: цель лидера, KR, этап, жизненный цикл (spec 16a). Сценарии IN1–IN10, обратные R114–R119."""
from dataclasses import replace

from .extra import clean, rows
from .model import Site, World
from .params import Params
from . import scenarios as S

IN = ("IN1", "IN2", "IN3", "IN4", "IN5", "IN6", "IN7", "IN8", "IN9", "IN10")
HOR = {"IN1": 5, "IN2": 12, "IN3": 30, "IN4": 2, "IN5": 21, "IN6": 14, "IN7": 205, "IN8": 205, "IN9": 3, "IN10": 5}


def _p(p, on=True, **kw):
    return replace(clean(p), evolution_enabled=True, leader_enabled=True, evo_rule_order=(), obj_enabled=on, **kw)


def _set_mp(f, n):
    """Вход сценария: численность фракции с согласованными ярусами (сумма ярусов = Manpower)."""
    f.steady = f.ordinary = 0
    f.skittish = n
    f.rank, f.vet, f.off = n, 0, 0


def _pin(w, hor, segs):
    """C фракции A подвязан на каждый тик (вход сценария: иначе C уходит к покойному значению)."""
    for t in range(1, hor + 1):
        w.scheduled.setdefault(t, []).append(S.ev_pins("A", segs))


def _world(p, owner="B", a=40, b=40, c=False):
    ss = [Site("База", 10, 0, 4, owner="A", income_disabled=True), Site("Узел", 20, 60, 2, owner=owner, region="common")]
    fs = {"A": S.faction(p, "A", "Хранители", a, 30, 10), "B": S.faction(p, "B", "Хранители", b, 30, 10)}
    if c:
        fs["C"] = S.faction(p, "C", "Хранители", 30, 30, 0)
    return World(fs, ss, p)


def _setter(fname, obj, target=None, rival=None):
    return lambda w: w.set_objective(fname, obj, target, rival)


def build(sc):
    def f(p):
        hor = HOR[sc]
        q = _p(p, on=sc != "IN10")
        low = [(10**6, None, None, None, 40.0)]
        if sc in ("IN1", "IN2", "IN10"):
            w = _world(q, a=80 if sc == "IN2" else 40)
            _pin(w, hor, low)
            if sc != "IN10":
                w.scheduled.setdefault(1, []).insert(0, _setter("A", 1, "Узел", "B"))
            if sc == "IN2":
                w.forced_assaults = {10: [("A", "Узел")]}
        elif sc == "IN3":
            w = _world(q)
            _pin(w, hor, [(24, None, None, None, 80.0), (10**6, None, None, None, 40.0)])
            w.scheduled.setdefault(1, []).insert(0, _setter("A", 1, "Узел", "B"))
        elif sc == "IN4":
            q = replace(q, obj_kr={**q.obj_kr, 1: (("hold", "ctl", ">", 60.0, 20), ("hold", "days_supply", ">", 5.0, 10), ("rival_supply_low", 15.0, 20))})
            w = _world(q)
        elif sc == "IN5":
            w = _world(q, owner="A")
            _pin(w, hor, [(10**6, None, None, None, 80.0)])
            w.scheduled.setdefault(1, []).insert(0, _setter("A", 1, "Узел", "B"))
            w.scheduled.setdefault(10, []).append(lambda w: _set_mp(w.factions["B"], 5))
        elif sc == "IN6":
            w = _world(q)
            S.give_named(w, "A")
            _pin(w, hor, low)
            w.scheduled.setdefault(1, []).insert(0, _setter("A", 1, "Узел", "B"))
            w.player_script = {10: [("kill", "A", "A:вожак")]}
        elif sc in ("IN7", "IN8"):
            w = _world(q)
            _pin(w, hor, low)
            w.scheduled.setdefault(1, []).insert(0, _setter("A", 1, "Узел", "B"))
            if sc == "IN8":
                w.scheduled.setdefault(50, []).append(lambda w: setattr(w.factions["B"], "depot", "CACHE"))
        elif sc == "IN9":
            w = _world(q, c=True)
            w.factions["C"].doctrine = 2
            w.scheduled.setdefault(1, []).insert(0, _setter("A", 1, "Узел", "B"))
            w.scheduled.setdefault(1, []).insert(1, _setter("B", 3, None, "A"))
        return w, hor
    return f


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        obj = lambda t=None: [r for r in w.log if (r[3].startswith("A.obj") and r[3] != "A.objective_" ) and (t is None or r[0] == t)]
        allobj = [r for r in w.log if ".obj" in r[3]]
        if sc == "IN1":
            ok("строка A.objective 0 → 1 на тике 1, OBJ_SET; этап 0; других строк цели нет", allobj == [(1, 7, "16", "A.objective", 0, 1, "OBJ_SET")] and w.factions["A"].obj_stage == 0, f"строки цели: {allobj}")
        elif sc == "IN2":
            st = rows(w, "A.obj_stage")
            ok("A.obj_stage 0 → 1 на тике 10, KR_1; до тика 10 строк этапа нет", [(r[0], r[4], r[5], r[6]) for r in st] == [(10, 0, 1, "KR_1")] and w.site("Узел").owner == "A", f"этап: {st}, хозяин: {w.site('Узел').owner}")
        elif sc == "IN3":
            ctr = rows(w, "A.obj_ctr.2")
            st = rows(w, "A.obj_stage")
            up = [(r[0], r[5]) for r in ctr if r[5] > r[4]]
            ok("счётчик растёт на 1 в тик с тика 1 (до 24, пока C выше 60); этап 0 → 1 на тике 20", up == [(t, t) for t in range(1, 25)] and (20, 0, 1, "KR_2") in [(r[0], r[4], r[5], r[6]) for r in st], f"счётчик до: {up[-3:]}, этап: {st}")
            ok("просадка C на тике 25: счётчик 20 → 0 и этап 1 → 0; строки OBJ_CTR на каждом изменении", (25, 24, 0, "OBJ_CTR") in [(r[0], r[4], r[5], r[6]) for r in ctr] and (25, 1, 0, "KR_2") in [(r[0], r[4], r[5], r[6]) for r in st] and len(ctr) == 25 and all(r[6] == "OBJ_CTR" for r in ctr),
               f"строк счётчика {len(ctr)}, тик 25: {[r for r in ctr if r[0] == 25]}, этап: {st}")
        elif sc == "IN4":
            try:
                w.set_objective("A", 1, "Узел", "B")
                err = None
            except ValueError as e:
                err = str(e)
            ok("три KR с длительностью у одной фракции → ValueError при установке", err is not None and "длительн" in err and not allobj, f"ошибка: {err}")
        elif sc == "IN5":
            ev = [e for e in w.events if e["kind"] == "objective_done"]
            ob = rows(w, "A.objective")
            f_ = w.factions["A"]
            ok("все KR МОНОПОЛИИ выполнены: на тике 20 цель 1 → 3, OBJ_DONE, событие; этап 0, счётчики 0",
               [(r[0], r[4], r[5], r[6]) for r in ob] == [(1, 0, 1, "OBJ_SET"), (20, 1, 3, "OBJ_DONE")] and len(ev) == 1 and ev[0]["tick"] == 20 and f_.obj_stage in (0, 1) and (20, 3, 0, "OBJ_DONE") in [(r[0], r[4], r[5], r[6]) for r in rows(w, "A.obj_stage")]
               and (20, 20, 0, "OBJ_DONE") in [(r[0], r[4], r[5], r[6]) for r in rows(w, "A.obj_ctr.2")], f"цель: {ob}, событий {len(ev)}, этап: {rows(w, 'A.obj_stage')}")
        elif sc == "IN6":
            ob = rows(w, "A.objective")
            mo = rows(w, "A.morale", "OBJ_COLLAPSE")
            ok("вожак убит, преемника нет: на тике 11 A — Дрейфующие, цель 0, OBJ_COLLAPSE, мораль −15",
               [(r[0], r[4], r[5], r[6]) for r in ob] == [(1, 0, 1, "OBJ_SET"), (11, 1, 0, "OBJ_COLLAPSE")] and w.factions["A"].archetype == "Дрейфующие" and [(r[0], round(r[4] - r[5], 4)) for r in mo] == [(11, 15.0)],
               f"цель: {ob}, мораль: {mo}, уклад: {w.factions['A'].archetype}")
        elif sc == "IN7":
            ob = rows(w, "A.objective")
            ok("недостижимые KR: на тике 200 цель 1 → 0, OBJ_STALE; дольше 200 тиков без роста не стоит", [(r[0], r[4], r[5], r[6]) for r in ob] == [(1, 0, 1, "OBJ_SET"), (200, 1, 0, "OBJ_STALE")], f"цель: {ob}")
        elif sc == "IN8":
            ob = rows(w, "A.objective")
            ok("депо соперника переехало на тике 50: на тике 200 причина OBJ_TARGET_LEFT, не OBJ_STALE", [(r[0], r[4], r[5], r[6]) for r in ob] == [(1, 0, 1, "OBJ_SET"), (200, 1, 0, "OBJ_TARGET_LEFT")], f"цель: {ob}")
        elif sc == "IN9":
            try:
                w.set_objective("C", 4, "Узел", "B")
                err = None
            except ValueError as e:
                err = str(e)
            try:
                w.set_objective("C", 2)
                passive = True
            except ValueError:
                passive = False
            ok("две активные цели у двух фракций; третья активная — ValueError; пассивная АВТАРКИЯ при доктрине 2 не считается", err is not None and "активных" in err and passive and w.factions["C"].objective == 2, f"ошибка: {err}; пассивная принята: {passive}")
        elif sc == "IN10":
            try:
                w.set_objective("A", 1, "Узел", "B")
                err = True
            except ValueError:
                err = False
            ok("obj_enabled = False: ни одной строки objective / obj_*; установка — ValueError", not allobj and not err, f"строки: {allobj[:3]}")
        return res
    return f


for _sc in IN:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R114": (replace(Params(), obj_bug_ctr_keep=True), ("IN3",), "счётчик не сбрасывается при просадке"),
    "R115": (replace(Params(), obj_bug_stage_every_tick=True), ("IN1", "IN2"), "этап пишется каждый тик"),
    "R116": (replace(Params(), obj_bug_no_stale=True), ("IN7",), "протухание выключено"),
    "R117": (replace(Params(), obj_bug_no_cap=True), ("IN9",), "потолок активных целей снят"),
    "R118": (replace(Params(), obj_bug_no_collapse_morale=True), ("IN6",), "мораль коллапса 0"),
    "R119": (replace(Params(), obj_bug_no_target_left=True), ("IN8",), "причина TARGET_LEFT не различается"),
})
