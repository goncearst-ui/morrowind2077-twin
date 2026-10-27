"""Задача 15: реестр активов (spec 15). Сценарии RE1–RE5, обратные R75–R78."""
from dataclasses import replace

from .model import Site, World
from .params import Params
from . import scenarios as S
from .extra import clean

RE = ("RE1", "RE2", "RE3", "RE3b", "RE4", "RE5")


def _w(p, extra=(), kinds=(0, 0, 0, 1), region="orbit"):
    ss = [Site(f"Х{i}", 20, 60, 2, owner="A" if i != 1 else "B", region=region, kind=k) for i, k in enumerate(kinds)]
    ss += list(extra)
    return World({"A": S.faction(p, "A", "Хранители", 10, 30, 0), "B": S.faction(p, "B", "Хранители", 60, 30, 0)}, ss, p)


def build(sc):
    def f(p):
        p = clean(p)
        if sc == "RE2":
            p = replace(p, asset_cap=4)
        if sc in ("RE3", "RE3b"):
            w = _w(p, kinds=(0, 0, 0, 1 if sc == "RE3" else 0))
            w.forced_assaults = {5: [("B", "Х3")]}
            return w, 12
        if sc == "RE5":
            return World({"A": S.faction(p, "A", "Хранители", 10, 30, 0)}, [Site("Ст", 20, 60, 2, owner="A", kind=1)], p), 2
        return _w(p), 3
    return f


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        if sc == "RE1":
            ok("4 записи по порядку, типы 0, 0, 0, 1", [(r[0], r[2]) for r in w.registry()] == [(0, 0), (1, 0), (2, 0), (3, 1)], f"реестр: {w.registry()}")
        elif sc == "RE2":
            err = 0
            try:
                _w(w.p, extra=[Site("Х9", 20, 60, 2)])
            except ValueError:
                err = 1
            big = World({"A": S.faction(replace(w.p, asset_cap=None), "A", "Хранители", 10, 30, 0)}, [Site(f"К{i}", 1, 1, 1) for i in range(18)], replace(w.p, asset_cap=None))
            ok("4 создаётся, 5 — ValueError, None допускает 18", err == 1 and len(w.sites) == 4 and len(big.sites) == 18, f"ошибка на 5: {err}, активов {len(w.sites)}, без потолка {len(big.sites)}")
        elif sc == "RE3":
            from .scenarios import run
            o, _ = run("RE3b", replace(w.p))
            ok("штурм и доход станции — теми же строками журнала, что у обычного объекта при тех же числах", w.log == o.log, f"журналы совпадают: {w.log == o.log}, строк {len(w.log)}")
            ok("штурм станции состоялся", any(e["kind"] == "assault" and e["site"] == "Х3" for e in w.events), f"штурмов: {sum(1 for e in w.events if e['kind'] == 'assault')}")
        elif sc == "RE3b":
            pass
        elif sc == "RE4":
            a = [r[:2] for r in w.registry()][:2]
            w.sites.append(Site("А2", 20, 60, 2)); w.sites.append(Site("А1", 20, 60, 2, kind=1))
            b = [r[:2] for r in w.registry()][:2]
            ok("индексы 0 и 1 не меняются при добавлении активов в конец", a == b, f"до: {a}, после: {b}")
        elif sc == "RE5":
            ok("станция без региона лежит в «orbit», регион в world.regions", w.sites[0].region == "orbit" and "orbit" in w.regions, f"регион: {w.sites[0].region}, регионы: {list(w.regions)}")
        return res
    return f


for _sc in RE:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R75": (replace(Params(), station_income_mult=0.5), ("RE3",), "станция со своей логикой дохода"),
    "R76": (replace(Params(), registry_sort=True), ("RE4",), "индекс по сортировке имён"),
    "R77": (replace(Params(), asset_cap_ignored=True), ("RE2",), "потолок не проверяется"),
    "R78": (replace(Params(), station_region="common"), ("RE5",), "станция без региона падает в common"),
})
