"""Задача 02: репутация и узнаваемость (spec 02). Сценарии RY1–RY9, обратные R91–R96."""
from dataclasses import replace

from .extra import clean, rows
from .model import Site, World
from .params import Params
from . import scenarios as S

RY = ("RY1", "RY2", "RY3", "RY4", "RY5", "RY6", "RY7", "RY7b", "RY8", "RY9", "RY9b")
KILL = lambda **o: ("kill", "B", "B:офицер1", o)


def _p(p, **kw):
    return replace(clean(p), evolution_enabled=True, leader_enabled=True, evo_rule_order=(), relations_enabled=True,
                   knowledge_enabled=True, player_levers_enabled=True, **kw)


def _world(p):
    fs = {"A": S.faction(p, "A", "Хранители", 30, 40, 0), "B": S.faction(p, "B", "Хранители", 30, 40, 40)}
    w = World(fs, [Site("Перевал", 40, 90, 4, owner="B")], p)
    S.give_named(w, "A", successors=("Осторожный",))
    S.give_named(w, "B", successors=("Осторожный",), officers=1)
    return w


def build(sc):
    def f(p):
        if sc in ("RY1", "RY2", "RY3", "RY4", "RY5", "RY6"):
            w = _world(_p(p, reputation_enabled=True))
            o = {"RY1": dict(masked=False, witnesses=1), "RY2": dict(masked=True, witnesses=1), "RY3": dict(masked=False, witnesses=0),
                 "RY4": dict(masked=False, witnesses=1), "RY5": dict(masked=False, witnesses=2), "RY6": dict(masked=False, witnesses=1)}[sc]
            w.player_script = {5: [KILL(**o)]}
            if sc == "RY4":
                w.player_script[6] = [("silence", "B")]
            if sc == "RY5":
                w.player_script[6] = [("silence", "B")]
            return w, 21 if sc == "RY6" else 10
        if sc in ("RY7", "RY7b"):
            w = _world(_p(p, reputation_enabled=True))
            w.player_funds = 1000.0
            w.scheduled = {1: [lambda w, sc=sc: w.region_rep.__setitem__("common", 30.0 if sc == "RY7" else 50.0)]}
            w.player_script = {2: [("bribe", "A", "B", 300.0)]}
            return w, 4
        if sc == "RY8":
            w = _world(_p(p, reputation_enabled=False))
            w.player_script = {5: [("kill", "B", "B:офицер1")]}
            return w, 8
        w, h = S.build("PL11", replace(p, reputation_enabled=True))
        o = dict(masked=False, witnesses=1)
        if sc == "RY9":
            w.player_script = {20: [KILL(**o)], 21: [("persuade", "B", "A")]}
            h = 24
        else:
            shock = lambda w: setattr(w.factions["B"], "shock", 45.0)
            w.scheduled = {23: [shock]}
            w.player_script = {20: [KILL(**o)], 23: [("persuade", "B", "A")]}
            h = 24
        return w, h
    return f


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        pr = [(r[0], r[4], r[5]) for r in rows(w, "player.rep.B")]
        rg = [(r[0], r[4], r[5]) for r in rows(w, "rep.region.common")]
        ev = [(e["tick"], e["kind"]) for e in w.events if e["kind"].startswith("rep_")]
        if sc == "RY1":
            ok("тик 5 без изменений; тик 7: репутация 50 → 20, регион 50 → 30, rep_identified", pr == [(7, 50.0, 20.0)] and [r for r in rg if r[0] <= 9] == [(7, 50.0, 30.0)] and ev == [(7, "rep_identified")], f"репутация {pr}, регион {rg}, события {ev}")
        elif sc == "RY2":
            ok("в маске: на тике 7 слух без имени, репутации 50", not pr and not rg and ev == [(7, "rep_unidentified")] and w.player_rep.get("B", 50.0) == 50.0, f"репутация {pr}, регион {rg}, события {ev}")
        elif sc == "RY3":
            ok("свидетелей нет: слуха нет, репутации целы, офицер убит (ярус −1)", not pr and not rg and not ev and not w.rep_rumors and not w.factions["B"].named[-1]["alive"] and not rows(w, "rep.rumor.B.5"), f"репутация {pr}, события {ev}")
        elif sc == "RY4":
            rc = rows(w, "rep.rumor.B.5", "RUMOR_CANCELLED")
            ok("слух отменён на тике 6, репутации на 7–10 не меняются", len(rc) == 1 and rc[0][0] == 6 and not pr and not rg, f"отмена {rc}, репутация {pr}")
        elif sc == "RY5":
            ok("два свидетеля, одно silence: доставлен как опознанный", pr == [(7, 50.0, 20.0)] and ev == [(7, "rep_identified")], f"репутация {pr}, события {ev}")
        elif sc == "RY6":
            ok("регион: 30 на тике 7, 31 на 10, 32 на 20, не выше 50", rg == [(7, 50.0, 30.0), (10, 30.0, 31.0), (20, 31.0, 32.0)] and w.region_rep["common"] <= 50, f"регион {rg}")
        elif sc == "RY7":
            i = rows(w, "rel.A>B.i", "PLAYER_BRIBE")
            o, _ = S.run("RY7b", w.p)
            io = rows(o, "rel.A>B.i", "PLAYER_BRIBE")
            ok("region_rep 30: +2.5 (цена 120); region_rep 50: +3.0", [r[5] for r in i] == [2.5] and [r[5] for r in io] == [3.0], f"30: {[r[5] for r in i]}, 50: {[r[5] for r in io]}")
        elif sc == "RY8":
            ok("выключено: штраф сразу на тике 5 (как в PL11), слухов нет", pr == [(5, 50.0, 20.0)] and not [r for r in w.log if r[2] == "02"], f"репутация {pr}")
        elif sc == "RY9":
            we = [(e["tick"], e["reason"]) for e in w.events if e["kind"] == "war_end"]
            pf = [(e["tick"], e["code"]) for e in w.events if e["kind"] == "player_failed"]
            o, _ = S.run("RY9b", w.p)
            pf2 = [(e["tick"], e["code"]) for e in o.events if e["kind"] == "player_failed"]
            ok("убеждение на тике 21 (слух в пути) проходит; то же на тике 23 отказано LOW_REP", (21, "WAR_END_PLAYER") in we and not pf and pf2 == [(23, "LOW_REP")], f"тик 21: концы {we}, отказы {pf}; тик 23: {pf2}")
        return res
    return f


for _sc in RY:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R91": (replace(Params(), rep_rumor_delay=0), ("RY1", "RY9"), "задержка слуха 0"),
    "R92": (replace(Params(), rep_masked_identifies=True), ("RY2",), "маска не меняет опознание"),
    "R93": (replace(Params(), rep_silence_cancels=False), ("RY4",), "silence не отменяет слух"),
    "R94": (replace(Params(), rep_ignore_witnesses=True), ("RY5",), "число свидетелей игнорируется"),
    "R95": (replace(Params(), rep_recover_off=True), ("RY6",), "восстановление выключено"),
    "R96": (replace(Params(), bribe_rep_price_k=0.0), ("RY7",), "цена подкупа не зависит от репутации региона"),
})
