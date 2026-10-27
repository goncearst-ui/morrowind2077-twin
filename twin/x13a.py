"""Задача 13a: доля фракции в регионе (spec 13a). Сценарии OS1–OS7, обратные R70–R74."""
from dataclasses import replace

from .extra import clean, rows
from .model import Site, World
from .params import Params
from . import scenarios as S

OS = ("OS1", "OS1b", "OS2", "OS3", "OS4", "OS5", "OS6", "OS7")


def _sites(owners):
    return [Site(f"О{i + 1}", 20, 60, 2, owner=o, region="Перевал") for i, o in enumerate(owners)]


def _world(p, owners, a=30, b=30):
    fs = {"A": S.faction(p, "A", "Хранители", a, 30, 0), "B": S.faction(p, "B", "Хранители", b, 30, 0)}
    return World(fs, _sites(owners), p)


def build(sc):
    def f(p):
        p = replace(clean(p), region_share_enabled=sc != "OS7")
        if sc == "OS1":
            return _world(p, ["A", "A", "B"]), 3
        if sc == "OS7":
            return _world(p, ["A", "A", "B"]), 3
        if sc == "OS1b":
            return _world(p, ["A", "A", None]), 3
        if sc == "OS2":
            w = _world(p, ["A", "A", "B"], a=10, b=60)
            w.forced_assaults = {10: [("B", "О1")], 20: [("A", "О3")], 30: [("B", "О2")]}
            w.chk = []
            def hook(w):
                pub = {(r, fn): v for (r, fn), v in w.share_pub.items()}
                for r in {s.region for s in w.sites}:
                    ss = [s for s in w.sites if s.region == r]
                    tot = sum(pub.get((r, fn), 0.0) for fn in w.factions) + sum(1 for s in ss if s.owner is None) / len(ss)
                    w.chk.append(abs(tot - 1.0) < 1e-9)
            w.scheduled = {t: [hook] for t in range(2, 41)}
            return w, 40
        if sc == "OS3":
            w = _world(p, ["A", "A", "B"], a=10, b=60)
            w.forced_assaults = {10: [("B", "О1")]}
            return w, 14
        if sc == "OS4":
            return _world(p, ["A", "A", "B"]), 1
        if sc == "OS5":
            return _world(replace(p, share_income_k=0.3), ["A", "A", "B"]), 1
        if sc == "OS6":
            w = _world(p, ["A", "A", "B"])
            def flip(w):
                for s, o in zip(w.sites, ["B", None, "A"]):
                    s.owner = o
            w.scheduled = {3: [flip]}
            return w, 5
    return f


def _chk(sc):
    def f(w, series):
        res = []
        def ok(n, c, d):
            res.append((n, bool(c), d))
        sh = lambda r, fn: w.share_pub.get((r, fn), 0.0)
        if sc == "OS1":
            r = {x[3]: (x[0], x[5]) for x in w.log if x[6] == "SHARE"}
            ok("доли A = 2/3 и B = 1/3 на тике 1", abs(sh("Перевал", "A") - 2 / 3) < 1e-9 and abs(sh("Перевал", "B") - 1 / 3) < 1e-9
               and r["region.Перевал.share.A"][0] == 1 and abs(r["region.Перевал.share.A"][1] - 0.6667) < 1e-4, f"строки: {r}")
        elif sc == "OS1b":
            ok("бесхозный объект в знаменателе: A = 2/3, не 1.0", abs(sh("Перевал", "A") - 2 / 3) < 1e-9, f"A = {sh('Перевал', 'A')}")
        elif sc == "OS2":
            ok("сумма долей и бесхозной доли = 1 на каждом тике", bool(w.chk) and all(w.chk), f"проверено тиков: {len(w.chk)}")
            ok("владельцы менялись (сценарий валиден)", len([e for e in w.events if e["kind"] == "assault"]) >= 3, "штурмов: %d" % len([e for e in w.events if e["kind"] == "assault"]))
        elif sc == "OS3":
            ticks = sorted({x[0] for x in w.log if x[6] == "SHARE" and x[0] > 1})
            won = [e for e in w.events if e["kind"] == "assault" and e["attacker_wins"]]
            ok("доли изменились ровно на тике штурма (10), не на 11", ticks == [10] and bool(won), f"тики изменения долей после старта: {ticks}, победных штурмов: {len(won)}")
        elif sc == "OS4":
            def dom(owners):
                q = _world(w.p, owners)
                return q.dominant("Перевал")
            res_ = (dom(["A", "A", "B"]), dom(["A", "B"]), dom(["A", "A", "A", "B", "B", "B"]))
            ok("2/3 → A; 1/2 на 1/2 → нет; 3 из 6 → нет (строго больше 0.5)", res_ == ("A", None, None), f"хозяева: {res_}")
        elif sc == "OS5":
            def exp(k):
                q = _world(replace(w.p, share_income_k=k), ["A", "A", "B"])
                return q.expected_income(q.factions["A"])
            e0, e3 = exp(0.0), exp(0.3)
            ok("k = 0.3, доля 2/3: доход × 0.9; k = 0: без изменений", abs(e3 - 0.9 * e0) < 1e-9 and e0 > 0, f"k=0: {e0}, k=0.3: {e3}")
        elif sc == "OS6":
            a = w.shares()
            ok("доли по текущему владению, без памяти между тиками", a == {"Перевал": {"B": 1 / 3, "A": 1 / 3}} and abs(sh("Перевал", "A") - 1 / 3) < 1e-9 and abs(sh("Перевал", "B") - 1 / 3) < 1e-9, f"вычисление: {a}, опубликовано: {w.share_pub}")
        elif sc == "OS7":
            ok("region_share_enabled = False: ни одной строки region.*.share.*", not [x for x in w.log if ".share." in x[3]], f"строк: {len([x for x in w.log if '.share.' in x[3]])}")
        return res
    return f


for _sc in OS:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R70": (replace(Params(), share_denominator_owned_only=True), ("OS1b",), "бесхозные не считаются в знаменателе"),
    "R71": (replace(Params(), share_lag=True), ("OS3",), "доли пересчитываются на следующем тике"),
    "R72": (replace(Params(), share_income_ignored=True), ("OS5",), "k не применяется к доходу"),
    "R73": (replace(Params(), dominant_ge=True), ("OS4",), "хозяин при доле ≥ 0.5"),
    "R74": (replace(Params(), share_inertia=0.15), ("OS6", "OS1"), "доля хранится и ползёт к цели"),
})
