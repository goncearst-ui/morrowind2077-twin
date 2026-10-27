"""Задача 16c: наследование цели и вендетта (spec 16c). Сценарии IV1–IV10 (IV8b — накопитель), обратные R125–R129."""
from dataclasses import replace

from .extra import clean, rows
from .model import Site, World
from .params import Params
from . import scenarios as S

IV = ("IV1", "IV2", "IV3", "IV4", "IV5", "IV6", "IV7", "IV8", "IV8b", "IV9", "IV10")
AL = "Agreeableness_Low"
KILL = 16        # убийство на тике 16, преемственность на тике 17 (T)
T = KILL + 1


def _p(p, **kw):
    base = dict(evolution_enabled=True, leader_enabled=True, npc_state_enabled=True, obj_enabled=True, strategy_enabled=True,
                player_levers_enabled=True, reputation_enabled=True, inheritance_enabled=True, evo_rule_order=())
    return replace(clean(p), **{**base, **kw})


def _world(p, succ="Радикальный", traits=(AL,), obj=1, masked=False, doctrine=0, third=False, kill=KILL):
    ss = [Site("База", 10, 0, 4, owner="A", income_disabled=True), Site("Узел", 20, 60, 2, owner="A", region="common")]
    fs = {"A": S.faction(p, "A", "Хранители", 40, 30, 10), "B": S.faction(p, "B", "Хранители", 40, 30, 10)}
    if third:
        fs["C"] = S.faction(p, "C", "Хранители", 30, 30, 0)
    w = World(fs, ss, p)
    S.give_named(w, "A", (succ,))
    w.factions["A"].named[1]["traits"] = tuple(traits)
    w.factions["A"].doctrine = doctrine
    for t in range(1, 61):
        w.scheduled.setdefault(t, []).append(S.ev_pins("A", [(10**6, None, None, None, 80.0)]))
    sets = []
    if third:
        sets += [lambda w: w.set_objective("B", 1, "Узел", "A"), lambda w: w.set_objective("C", 3, None, "A")]
    if obj is not None:
        sets.append(lambda w, o=obj: w.set_objective("A", o, "Узел", "B"))
    w.scheduled.setdefault(1, [])[0:0] = sets
    w.player_script = {kill: [("kill", "A", "A:вожак", {"masked": masked, "witnesses": 1})]}
    for fx in w.factions.values():
        w.publish_dos(fx, phase=0)
    return w


def _go(w, n):
    for _ in range(n):
        w.step()
    return w


def _obj(w):
    return [(r[0], r[4], r[5], r[6]) for r in rows(w, "A.objective")]


def build(sc):
    def f(p):
        q = _p(p)
        if sc == "IV1":
            return _world(q), 45
        if sc == "IV2":
            return _world(q, masked=True), 20
        if sc == "IV3":
            return _world(q, "Осторожный", ()), 20
        if sc == "IV4":
            return _world(q, "Идеолог", (), obj=2), 20
        if sc == "IV5":
            return _world(q, obj=None), 20
        if sc == "IV6":
            return _world(q, obj=2, doctrine=2, third=True), 20
        if sc == "IV7":
            return _world(q), 45
        if sc == "IV8":
            w, _ = S.build("PL9", replace(p, obj_enabled=True, strategy_enabled=True, npc_state_enabled=True, inheritance_enabled=True))
            S.give_named(w, "B", ("Радикальный",))
            w.factions["B"].named[1]["traits"] = (AL,)
            shock = lambda w: setattr(w.factions["B"], "shock", 45.0)
            rep = lambda w: w.player_rep.__setitem__("B", 50.0)
            w.scheduled = {21: [shock, rep], 37: [shock, rep]}
            w.player_script = {KILL: [("kill", "B", "B:вожак")], 21: [("persuade", "B", "A")], 37: [("persuade", "B", "A")]}
            return w, 40
        if sc == "IV8b":
            w, _ = S.build("WR1", replace(p, evolution_enabled=True, leader_enabled=True, evo_rule_order=(), npc_state_enabled=True, obj_enabled=True, strategy_enabled=True, inheritance_enabled=True))
            S.give_named(w, "A")
            def inject(w):
                w.factions["A"].vendetta, w.factions["A"].vendetta_culprit = 20, "B"
            w.scheduled.setdefault(1, []).insert(0, inject)
            return w, 3
        if sc == "IV9":
            return _world(q, obj=3), 20
        if sc == "IV10":
            return _world(_p(p, inheritance_enabled=False)), 20
    return f


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        ev = lambda k: [e for e in w.events if e["kind"] == k]
        vend = [(r[0], r[4], r[5], r[6]) for r in rows(w, "A.vendetta")]
        if sc == "IV1":
            ctr = [(r[0], r[4], r[5], r[6]) for r in rows(w, "A.obj_ctr.2") if r[6] == "OBJ_CONTINUE"]
            ok("Радикальный + Agreeableness_Low, виновник известен: цель остаётся 1, счётчик сброшен, событие objective_continued, vendetta = 20",
               w.factions["A"].objective == 1 and _obj(w) == [(1, 0, 1, "OBJ_SET")] and len(ctr) == 1 and ctr[0][0] == T and ctr[0][2] == 0 and ctr[0][1] >= 10
               and len(ev("objective_continued")) == 1 and ev("leader_killed")[0]["culprit"] == "player" and vend[:1] == [(T, 0, 20, "VENDETTA_SET")],
               f"цель: {_obj(w)}, счётчик: {ctr}, события: {len(ev('objective_continued'))}, вендетта: {vend[:2]}")
            q = _world(replace(w.p, leader_kill_seat=True), obj=1)
            q.player_script = {}
            q.factions["B"].steady = q.factions["B"].ordinary = 0
            q.factions["B"].skittish = 0
            q.factions["B"] = S.faction(q.p, "B", "Хранители", 80, 30, 10)
            q.init_tiers(q.factions["B"])
            q.publish_dos(q.factions["B"], phase=0)
            q.factions["A"].depot = "База"
            q.forced_assaults = {5: [("B", "База")]}
            _go(q, 8)
            lk = [e for e in q.events if e["kind"] == "leader_killed"]
            ok("виновник — фракция: убийство вожака при штурме склада пишет culprit = нападавший, вендетта A направлена на него",
               len(lk) == 1 and lk[0]["culprit"] == "B" and q.factions["A"].vendetta_culprit == "B" and q.factions["A"].vendetta > 0, f"события: {[(e['reason'], e['culprit']) for e in lk]}, вендетта A: {q.factions['A'].vendetta} против {q.factions['A'].vendetta_culprit}")
        elif sc == "IV2":
            ok("убийство в маске: цель → ГЕГЕМОНИЯ (3), этап 0, вендетты нет", _obj(w) == [(1, 0, 1, "OBJ_SET"), (T, 1, 3, "OBJ_CHANGE")] and w.factions["A"].obj_stage in (0, 1) and not vend and ev("leader_killed")[0]["culprit"] is None,
               f"цель: {_obj(w)}, вендетта: {vend}, виновник: {ev('leader_killed')[0]['culprit']}")
        elif sc == "IV3":
            u = _go(_world(w.p, "Осторожный", (), masked=True), 20)
            ok("Осторожный: при известном и неизвестном виновнике цель 0, этап 0", _obj(w)[-1] == (T, 1, 0, "OBJ_CHANGE") and _obj(u)[-1] == (T, 1, 0, "OBJ_CHANGE") and w.factions["A"].objective == 0 == u.factions["A"].objective and w.factions["A"].obj_stage == 0,
               f"известный: {_obj(w)}, неизвестный: {_obj(u)}")
        elif sc == "IV4":
            m = _go(_world(w.p, "Идеолог", (), obj=1), 20)
            u = _go(_world(w.p, "Идеолог", (), obj=2, masked=True), 20)
            ok("Идеолог: известный, АВТАРКИЯ → остаётся; известный, МОНОПОЛИЯ → АВТАРКИЯ; неизвестный, АВТАРКИЯ → остаётся",
               w.factions["A"].objective == 2 and len(ev("objective_continued")) == 1 and _obj(m)[-1] == (T, 1, 2, "OBJ_CHANGE") and u.factions["A"].objective == 2,
               f"АВТАРКИЯ: {_obj(w)}, МОНОПОЛИЯ: {_obj(m)}, неизвестный: {_obj(u)}")
        elif sc == "IV5":
            ok("Радикальный, виновник известен, цель 0 (пассивная) → ГЕГЕМОНИЯ", _obj(w) == [(T, 0, 3, "OBJ_CHANGE")], f"цель: {_obj(w)}")
        elif sc == "IV6":
            ok("две активные цели у B и C; исход «ГЕГЕМОНИЯ» для A (была пассивная АВТАРКИЯ при доктрине 2) даёт ВЫЖИВАНИЕ, CAP_ACTIVE_OBJ",
               _obj(w) == [(1, 0, 2, "OBJ_SET"), (T, 2, 0, "CAP_ACTIVE_OBJ")] and w.factions["B"].objective == 1 and w.factions["C"].objective == 3, f"цель A: {_obj(w)}")
        elif sc == "IV7":
            tick = [(t, a, b) for t, a, b, rs in vend if rs == "VENDETTA_TICK"]
            ok("вендетта 20 на тике T, 0 на T + 20 и остаётся 0; VENDETTA_TICK на каждом шаге; не продлевается",
               vend[0] == (T, 0, 20, "VENDETTA_SET") and tick == [(T + i, 20 - i + 1, 20 - i) for i in range(1, 21)] and len(vend) == 21 and w.factions["A"].vendetta == 0,
               f"строк {len(vend)}, первые: {vend[:3]}, последние: {vend[-2:]}")
        elif sc == "IV8":
            pf = [(e["tick"], e["code"]) for e in w.events if e["kind"] == "player_failed" and e["action"] == "persuade"]
            we = [(e["tick"], e["reason"]) for e in w.events if e["kind"] == "war_end"]
            b = [(r[0], r[4], r[5], r[6]) for r in rows(w, "B.vendetta")]
            ok("виновник — игрок: persuade на T + 5 (21) отказан VENDETTA, на T + 21 (37) проходит (WAR_END_PLAYER)",
               pf == [(21, "VENDETTA")] and (37, "WAR_END_PLAYER") in we and b[:1] == [(T, 0, 20, "VENDETTA_SET")], f"отказы: {pf}, концы войн: {we}, вендетта B: {b[:2]}")
        elif sc == "IV8b":
            base, _ = S.build("WR1", replace(w.p, inheritance_enabled=False))
            S.give_named(base, "A")
            _go(base, 3)
            a = [r[5] for r in rows(w, "war.A>B.acc")]
            b = [r[5] for r in rows(base, "war.A>B.acc")]
            ok("виновник — фракция B: накопитель войны клана A против B растёт в 1.5 раза быстрее, чем без вендетты (вендетта задана входом сценария)",
               len(a) == 3 and len(b) == 3 and all(abs(x / y - 1.5) < 1e-3 for x, y in zip(a, b)), f"с вендеттой: {a}, без: {b}")
        elif sc == "IV9":
            m = _go(_world(w.p, obj=3, masked=True), 20)
            vm = [(r[0], r[4], r[5], r[6]) for r in rows(m, "A.vendetta")]
            ok("цель ГЕГЕМОНИЯ, Радикальный: без маски — цель 3 и вендетта 20; в маске — цель 3 и вендетты нет",
               w.factions["A"].objective == 3 and vend[:1] == [(T, 0, 20, "VENDETTA_SET")] and m.factions["A"].objective == 3 and not vm and _obj(w) == [(1, 0, 3, "OBJ_SET")] == _obj(m),
               f"без маски: {_obj(w)} / {vend[:1]}, в маске: {_obj(m)} / {vm}")
        elif sc == "IV10":
            ok("inheritance_enabled = False: цель 0 по 16a (OBJ_SUCCESSOR), вендетты нет", _obj(w) == [(1, 0, 1, "OBJ_SET"), (T, 1, 0, "OBJ_SUCCESSOR")] and not vend and not ev("objective_continued"), f"цель: {_obj(w)}, вендетта: {vend}")
        return res
    return f


for _sc in IV:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R125": (replace(Params(), inh_bug_ignore_cause=True), ("IV2",), "причина смерти игнорируется"),
    "R126": (replace(Params(), inh_bug_no_cap=True), ("IV6",), "потолок активных целей снят при наследовании"),
    "R127": (replace(Params(), inh_bug_vendetta_extend=True), ("IV7",), "вендетта продлевается"),
    "R128": (replace(Params(), inh_bug_persuade_ignores=True), ("IV8",), "убеждение не читает вендетту"),
    "R129": (replace(Params(), inh_bug_swap_profiles=True), ("IV4",), "Идеолог ведёт себя как Радикальный"),
})
