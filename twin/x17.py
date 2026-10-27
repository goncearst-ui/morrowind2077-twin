"""Задача 17: триада профилей (spec 17). Сценарии TR1–TR9, обратные R141–R144. Новой механики нет."""
from dataclasses import replace

from .extra import rows
from .params import Params
from .triad import F, K, M, triad
from . import scenarios as S

TR = ("TR1", "TR2", "TR3", "TR4", "TR5", "TR6", "TR7", "TR8", "TR9")
HOR = {"TR1": 1, "TR6": 240}


def _go(w, n):
    for _ in range(n):
        w.step()
    return w


def _run(p, n=200, **kw):
    w, _ = triad(p, **kw)
    return _go(w, n)


def _first_diff(a, b):
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None if len(a) == len(b) else min(len(a), len(b)))


def _stage_up(w, fid):
    return [r for r in rows(w, f"{fid}.obj_stage") if r[5] > r[4]]


def _assaults(w):
    return [(e["tick"], e["attacker"], e["site"]) for e in w.events if e["kind"] == "assault"]


def build(sc):
    def f(p):
        if sc == "TR6":
            w, _ = triad(p, leaders=("negotiator", "radical"))
            w.factions[M].depot = "Метро-1"
            w.scheduled.setdefault(50, []).append(lambda w: setattr(w.factions[M], "depot", "CACHE"))   # переезд депо Метрополии (вход сценария)
            return w, 240
        w, _ = triad(p)
        return w, HOR.get(sc, 200)
    return f


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        if sc == "TR1":
            _, pr = triad(w.p)
            got = {n: (x.archetype, x.doctrine, x.objective) for n, x in w.factions.items()}
            want = {n: (v["archetype"], v["doctrine"], v["objective"]) for n, v in pr.items()}
            from . import objective as O
            act = sum(1 for x in w.factions.values() if O.is_active(x, x.objective))
            tr = {n: tuple(next(x for x in w.factions[n].named if x["name"] == w.factions[n].leader)["traits"]) for n in w.factions}
            ok("три фракции с архетипом, доктриной, целью и лидером из п. 1; активных целей ровно две (потолок 16a)",
               got == want == {M: ("Контролёры", 0, 3), K: ("Хранители", 2, 2), F: ("Контролёры", 0, 5)} and act == 2 and tr[K] == ("Conscientiousness_High",) and "Agreeableness_Low" in tr[M] and "Agreeableness_Low" in tr[F],
               f"{got}; активных {act}; трейты {tr}")
        elif sc == "TR2":
            bad = [r for r in w.log if ("Колония" in r[3]) and not r[3].startswith(("Колония", "region.", "know.Колония>", "rumor."))]
            ev = [e for e in w.events if any(isinstance(v, str) and "Колония" in v for k, v in e.items() if k not in ("faction", "kind", "tick"))]
            ok("за 200 тиков ни одно событие и ни одна строка Метрополии и Тропы не имеет Колонию как цель или объект", not bad and not ev, f"строк {len(bad)} {bad[:2]}, событий {len(ev)} {ev[:1]}")
        elif sc == "TR3":
            n = _run(w.p, leaders=("negotiator", "radical"))
            d = _first_diff(w.log, n.log)
            ok("Метрополия: Ястреб против Переговорщика — журналы различны, этап цели растёт в обоих прогонах", d is not None and _stage_up(w, M) and _stage_up(n, M),
               f"расхождение со строки {d}: {w.log[d] if d is not None and d < len(w.log) else None} / {n.log[d] if d is not None and d < len(n.log) else None}; штурмы: {_assaults(w)} / {_assaults(n)}")
        elif sc == "TR4":
            n = _run(w.p, leaders=("hawk", "negotiator"))
            d = _first_diff(w.log, n.log)
            ok("Тропа: Радикал против Переговорщика — журналы различны, этап цели растёт в обоих прогонах", d is not None and _stage_up(w, F) and _stage_up(n, F),
               f"расхождение со строки {d}: {w.log[d] if d is not None and d < len(w.log) else None}; штурмы: {_assaults(w)} / {_assaults(n)}")
        elif sc == "TR5":
            z = _run(w.p, goal_m=0)
            strip = lambda l: [r for r in l if ".obj" not in r[3] and ".strategy" not in r[3]]
            ok("ГЕГЕМОНИЯ против цели 0 (всё прочее равно): журналы различны не только строками цели, этапа, стратегии (есть разница в штурмах)",
               strip(w.log) != strip(z.log) and _assaults(w) != _assaults(z), f"штурмы с целью 3: {_assaults(w)}, с целью 0: {_assaults(z)}")
        elif sc == "TR6":
            up = _stage_up(w, F)
            ob = [(r[0], r[4], r[5], r[6]) for r in rows(w, f"{F}.objective")]
            ok("этап Тропы растёт по KR2 (Метрополия ниже 15 суток 20 тиков); после переезда депо Метрополии причина OBJ_TARGET_LEFT, не OBJ_STALE",
               up and up[0][6] == "KR_2" and ob[-1][1:] == (5, 0, "OBJ_TARGET_LEFT") and not any(o[3] == "OBJ_STALE" for o in ob if o[0] > 1), f"рост этапа: {[(r[0], r[6]) for r in up]}, цель Тропы: {ob}")
        elif sc == "TR7":
            a = _run(w.p, vassal=True)
            b = _run(w.p, vassal=False)
            rel = lambda x: [r for r in x.log if r[3].startswith("rel.")]
            m = lambda x: [(r[0], r[3], r[4], r[5]) for r in x.log if r[3].startswith(f"{M}.obj_stage")]
            ok("флаг вассальной труа не меняет H и уровень пары; меняет только KR2 Метрополии (этап)", rel(a) == rel(b) and bool(rel(a)) and m(a) != m(b), f"строк rel {len(rel(a))}/{len(rel(b))}; этап M с флагом {m(a)[:2]}, без {m(b)[:2]}")
        elif sc == "TR8":
            a, b = _run(w.p), _run(w.p)
            ok("два прогона одной фабрики дают идентичные журналы", a.log == b.log and a.events == b.events and len(a.log) > 0, f"строк {len(a.log)}")
        elif sc == "TR9":
            import inspect
            src = inspect.getsource(S)
            ok("прежние сценарии не используют triad (в twin/scenarios.py нет обращений к фабрике)", "triad(" not in src and "import triad" not in src, "")
        return res
    return f


for _sc in TR:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R141": (replace(Params(), tri_bug_colony_lever=True), ("TR2",), "Колония втянута в рычаг (Тропа штурмует Колонию)"),
    "R142": (replace(Params(), tri_bug_ignore_goal=True), ("TR5",), "цель Метрополии игнорируется"),
    "R143": (replace(Params(), tri_bug_vassal_h=True), ("TR7",), "флаг вассальной труа меняет уровни отношений"),
    "R144": (replace(Params(), tri_bug_same_leaders=True), ("TR3",), "лидеры совпадают по трейтам"),
})
