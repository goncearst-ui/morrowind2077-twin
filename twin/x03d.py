"""Задача 03d: общий регион и представители фракций (spec 03d). Сценарии ED1–ED8, обратные R97–R102."""
from dataclasses import replace

from .extra import clean, rows
from .model import Site, World
from .params import Params
from . import scenarios as S

ED = ("ED1", "ED2", "ED3", "ED4", "ED5", "ED5b", "ED6", "ED7", "ED8", "ED9")


def _p(p, **kw):
    return replace(clean(p), evolution_enabled=True, leader_enabled=True, evo_rule_order=(), relations_enabled=True,
                   knowledge_enabled=True, player_levers_enabled=True, reputation_enabled=True, **kw)


def _world(p):
    fs = {n: S.faction(p, n, "Хранители", 30, 40, 40 if n == "B" else 0) for n in "ABC"}
    w = World(fs, [Site("Перевал", 40, 90, 4, owner="B")], p)
    for n in "ABC":
        S.give_named(w, n, successors=("Осторожный",))
    return w


def build(sc):
    def f(p):
        if sc == "ED8":
            w, h = S.build("PL9", replace(p, reputation_enabled=True, envoys_enabled=True))
            return w, 100
        w = _world(_p(p, envoys_enabled=sc != "ED9"))
        w.player_funds = 1000.0
        w.player_script = {
            "ED1": {}, "ED2": {5: [("kill", "A", "A:вожак")]},
            "ED3": {3: [("kill", "A", "A:представитель")], 5: [("kill", "A", "A:вожак")], 6: [("kill", "B", "B:вожак")]},
            "ED4": {5: [("kill", "B", "B:представитель", dict(masked=False, witnesses=1))]},
            "ED5": {5: [("frame", "B", "C", dict(masked=True, witnesses=1))]},
            "ED5b": {2: [("bribe", "B", "C", 300.0)], 5: [("frame", "B", "C", dict(masked=True, witnesses=1))]},
            "ED6": {5: [("frame", "B", "C", dict(masked=False, witnesses=1))]},
            "ED7": {5: [("frame", "B", "C", dict(masked=True, witnesses=1))], 6: [("frame", "B", "A", dict(masked=True, witnesses=1))]},
            "ED9": {5: [("kill", "A", "A:вожак")]},
        }[sc]
        return w, {"ED1": 3, "ED5": 16}.get(sc, 12)
    return f


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        board = w.hub_board
        pf = [(e["tick"], e["code"]) for e in w.events if e["kind"] == "player_failed"]
        ev = [(e["tick"], e["kind"]) for e in w.events if e["kind"] in ("envoy_killed", "frame", "frame_exposed", "rep_identified", "rep_unidentified")]
        if sc == "ED1":
            ok("у каждой фракции один живой представитель; Manpower как без выключателя", sorted(w.envoys) == ["A", "B", "C"] and all(e["alive"] and e["region"] == "hub" for e in w.envoys.values())
               and all(f.manpower == 30 for f in w.factions.values()), f"представители {list(w.envoys)}, Manpower {[f.manpower for f in w.factions.values()]}")
        elif sc == "ED2":
            ok("запись о вожаке A на доске на тике 8, не раньше", board.get("A.leader_killed.5") == 8, f"доска: {board}")
        elif sc == "ED3":
            late = [k for k in board if k.startswith("A.") and int(k.split(".")[-1]) > 3]
            ok("события A после тика 3 не на доске; события B — на доске", not late and board.get("B.leader_killed.6") == 9, f"доска: {board}")
        elif sc == "ED4":
            pr = [(r[0], r[4], r[5]) for r in rows(w, "player.rep.B")]
            rg = [(r[0], r[4], r[5]) for r in rows(w, "rep.region.common") if r[0] <= 9]
            ok("репутации падают на тике 7 по 02, событие envoy_killed на тике 5", pr == [(7, 50.0, 20.0)] and rg == [(7, 50.0, 30.0)] and (5, "envoy_killed") in ev, f"репутация {pr}, регион {rg}, события {ev}")
        elif sc == "ED5":
            i = [(r[0], r[5]) for r in rows(w, "rel.B>C.i")]
            h5 = [r for r in rows(w, "rel.B>C.H") if r[0] == 5]
            ok("представитель B убит, i(B→C) = 5.0 на тике 5, H вырос на 5.0, на тике 15 i = 4.0", not w.envoys["B"]["alive"] and i[0] == (5, 5.0) and (10, 4.0) in i and w.rel[("B", "C")].i == 4.0
               and bool(h5) and abs(h5[0][5] - (w.base_h("B", "C") + 5.0)) < 1e-6, f"i: {i}, H на тике 5: {h5}")
        elif sc == "ED5b":
            i = [(r[0], r[5]) for r in rows(w, "rel.B>C.i")]
            ok("с подкупом общий потолок 6.0: 3.0 → 6.0", i[:2] == [(2, 3.0), (5, 6.0)], f"i: {i}")
        elif sc == "ED6":
            ok("подстава без маски: H не меняется, frame_exposed, репутация падает по 02", not rows(w, "rel.B>C.i") and (5, "frame_exposed") in ev and (7, "rep_identified") in ev and w.player_rep.get("B") == 20.0, f"события {ev}")
        elif sc == "ED7":
            ok("повторная подстава против B: NO_ENVOY", pf == [(6, "NO_ENVOY")], f"отказы {pf}")
        elif sc == "ED8":
            ok("100 тиков: все представители живы, автономных убийств нет", all(e["alive"] for e in w.envoys.values()) and not [r for r in w.log if r[6] == "ENVOY_KILLED"], f"представители {[(n, e['alive']) for n, e in w.envoys.items()]}")
            ok("мир не пуст: война, штурмы или налёты были", any(e["kind"] in ("war_declared", "assault", "raid_object") for e in w.events), f"событий {len(w.events)}")
        elif sc == "ED9":
            ok("envoys_enabled = False: представителей и доски нет", not w.envoys and not w.hub_board and not [r for r in w.log if r[2] == "03d"], f"строк 03d: {len([r for r in w.log if r[2] == '03d'])}")
        return res
    return f


for _sc in ED:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R97": (replace(Params(), hub_rumor_delay=0), ("ED2",), "задержка доски 0"),
    "R98": (replace(Params(), hub_board_when_dead=True), ("ED3",), "доска пишет и при мёртвом представителе"),
    "R99": (replace(Params(), envoy_counts_manpower=True), ("ED1",), "представитель входит в Manpower"),
    "R100": (replace(Params(), frame_ignores_mask=True), ("ED6",), "подстава не требует маски"),
    "R101": (replace(Params(), frame_cap_separate=True), ("ED5b",), "потолок H подставы отдельный от подкупа"),
    "R102": (replace(Params(), envoy_autokill_tick=30), ("ED8",), "автономное убийство представителя"),
})
