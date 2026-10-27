"""Задача 14: хозяин планеты (spec 14). Сценарии PH1–PH10, обратные R79–R83."""
import copy
from dataclasses import replace

from .extra import clean, rows
from .model import Site, World
from .params import Params
from . import scenarios as S

PH = ("PH1", "PH1b", "PH2", "PH3", "PH4", "PH5", "PH6", "PH6b", "PH7", "PH8", "PH9", "PH10")


def _w(p, owners, a=60, b=60, strong_a=True):
    ss = [Site(f"Х{i}", 20, 60, 2, owner=o, region="Перевал", kind=1 if i == len(owners) - 1 else 0) for i, o in enumerate(owners)]
    fs = {"A": S.faction(p, "A", "Хранители", a, 30, 0), "B": S.faction(p, "B", "Хранители", b, 30, 0)}
    return World(fs, ss, p)


def _plan(sc):
    """(владельцы, штурмы {тик: [(кто, объект)]}, горизонт, параметры, a, b)"""
    A3B1 = ["A", "A", "A", "B"]
    return {
        "PH1": (A3B1, {}, 3, {}),
        "PH1b": (["A", "A", "A", "B", None, None, None], {}, 3, {}),
        "PH2": (["A", "A", "B", "B"], {}, 3, {}),
        "PH3": (A3B1, {3: [("B", "Х0")]}, 12, {}),
        "PH4": (A3B1, {10: [("B", "Х0")], 11: [("A", "Х0")], 12: [("B", "Х1")], 13: [("A", "Х1")]}, 30, {}),
        "PH5": (["A", "A", "B", "B"], {3: [("A", "Х2")]}, 12, {}),
        "PH6": (A3B1, {4: [("B", "Х0")]}, 12, {}),
        "PH6b": (A3B1, {4: [("B", "Х0")], 6: [("A", "Х0")]}, 12, {}),
        "PH7": (A3B1, {3: [("B", "Х0")], 12: [("A", "Х0")], 20: [("B", "Х1")]}, 30, {}),
        "PH8": (A3B1, {}, 3, dict(hegemon_margin=2)),
        "PH9": (["A", "A", "B", "B"], {3: [("A", "Х2")]}, 14, {}),
        "PH10": (A3B1, {3: [("B", "Х0")]}, 12, {}),
    }[sc]


def build(sc):
    def f(p):
        owners, ass, hor, kw = _plan(sc)
        p = replace(clean(p), planet_hegemon_enabled=sc != "PH10", **kw)
        # сильный нападающий выбирается так, чтобы штурм побеждал: в каждый тик нападает тот, у кого людей больше
        w = _w(p, owners)
        w.flips = 0
        for t, lst in ass.items():   # смена владельца объекта входом сценария (захват); модуль 14 читает только реестр
            def flip(w, lst=lst):
                for who, site in lst:
                    w.site(site).owner = who
                    w.flips += 1
            w.scheduled.setdefault(t, []).append(flip)
        return w, hor
    return f


def _hg(w):
    return [(r[0], r[5]) for r in w.log if r[3] == "planet.hegemon"]


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        h = _hg(w)
        won = getattr(w, "flips", 0)
        if sc in ("PH1", "PH1b"):
            ok("на тике 1 hegemon = A", h == [(1, "A")] and w.hegemon == "A", f"статус: {h}")
        elif sc == "PH2":
            ok("ничья 2 : 2 → Contested на тике 1", h == [(1, "Contested")], f"статус: {h}")
        elif sc == "PH3":
            ok("статус A держится до тика 7 включительно, на тике 8 → Contested", h == [(1, "A"), (8, "Contested")] and won == 1, f"статус: {h}, захватов {won}")
        elif sc == "PH4":
            ticks = [t for t, _ in h]
            gaps = [b - a for a, b in zip(ticks, ticks[1:])]
            ok("смен не больше 1 + 30 ÷ 7, интервалы не меньше 7", len(h) <= 1 + 30 // 7 and all(g >= 7 for g in gaps) and won >= 3, f"смены: {h}, захватов {won}")
        elif sc == "PH5":
            ok("Contested с тика 1, hegemon = A на первом тике после cooldown (8)", h == [(1, "Contested"), (8, "A")], f"статус: {h}")
        elif sc == "PH6":
            ok("запрос на смену на тике 4 не потерян: смена на тике 8", h == [(1, "A"), (8, "Contested")], f"статус: {h}")
        elif sc == "PH6b":
            ok("кандидат вернулся к статусу до конца cooldown: смены нет", h == [(1, "A")] and won == 2, f"статус: {h}, захватов {won}")
        elif sc == "PH7":
            ev = [e for e in w.events if e["kind"] == "hegemon_change"]
            ok("каждая смена — ровно одно событие и ровно одна строка", len(ev) == len(h) and [(e["tick"], e["new"]) for e in ev] == h and len(h) >= 3, f"строки: {h}, событий {len(ev)}")
        elif sc == "PH8":
            q = _w(w.p, ["A", "A", "B"])
            q.step()
            ok("margin 2: 3 : 1 → хозяин A, 2 : 1 → Contested", h == [(1, "A")] and _hg(q) == [(1, "Contested")], f"3:1 {h}, 2:1 {_hg(q)}")
        elif sc == "PH9":
            a, _ = S.build("PH9", replace(w.p))
            for _ in range(5):
                a.step()
            b = copy.deepcopy(a)
            for _ in range(9):
                a.step(); b.step()
            ok("копия мира посреди прогона даёт тот же статус и те же тики", a.log == b.log == w.log and a.hegemon_tick == b.hegemon_tick, f"статус {a.hegemon}/{b.hegemon}, тик смены {a.hegemon_tick}/{b.hegemon_tick}, строки {_hg(a)}")
        elif sc == "PH10":
            ok("флаг выключен: нет строк planet.hegemon", not h and w.hegemon is None, f"строки: {h}")
        return res
    return f


for _sc in PH:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R79": (replace(Params(), hegemon_cooldown=0), ("PH3", "PH4"), "cooldown 0"),
    "R80": (replace(Params(), hegemon_margin=0), ("PH2",), "запас 0: ничья отдаёт хозяйство первому"),
    "R81": (replace(Params(), hegemon_drop_deferred=True), ("PH6",), "запрос смены в cooldown теряется"),
    "R82": (replace(Params(), hegemon_stateless=True), ("PH3",), "статус без памяти"),
    "R83": (replace(Params(), hegemon_count_unowned=True), ("PH1b",), "бесхозные считаются как фракция"),
})
