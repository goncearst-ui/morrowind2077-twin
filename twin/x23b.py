"""Задача 23b: именные до сотен (spec 23). Сценарии NN1–NN5, обратные R153–R154. Двойник; Creation Kit не описывает."""
import time
from dataclasses import replace

from . import integration as I
from . import scenarios as S
from .extra import clean
from .model import Site, World
from .named import named_roster
from .params import Params

NN = ("NN1", "NN2", "NN3", "NN4", "NN5")
PER = 25   # именных на фракцию в эталонном мире 23b: 4 × 25 = 100 [решение Стана: «сотни»]


def _world100(p):
    w, h, _ = I.everything(p, named=PER)
    I.instrument(w)
    if p.nn_bug_promote:   # R153: «продвижение из ведра» — новый именной появляется в ходе игры
        w.scheduled.setdefault(100, []).append(lambda w: w.factions[next(iter(w.factions))].named.append(dict(name="продвинутый", role="офицер", profile="—", alive=True)))
    return w, h


def _bench(p):
    """NN3: глубокая скамейка (25 именных, 4 преемника) и тонкая (только вожак): убиваем вожаков по очереди."""
    q = replace(clean(p), evolution_enabled=True, leader_enabled=True, evo_rule_order=(3, 5, 8), named_max=PER)
    ss = [Site("ОбъектA", 10, 0, 4, owner="A", income_disabled=True), Site("ОбъектB", 10, 0, 4, owner="B", income_disabled=True)]
    w = World({"A": S.faction(q, "A", "Хранители", 30, 40, 10), "B": S.faction(q, "B", "Хранители", 30, 40, 10)}, ss, q)
    for n, k in (("A", PER), ("B", 1)):
        w.factions[n].named = named_roster(n, k, q)
        w.factions[n].leader = f"{n}:вожак"
    w.player_script = {10: [("kill", "A", "A:вожак"), ("kill", "B", "B:вожак")], 30: [("kill", "A", "A:преемник1")], 50: [("kill", "A", "A:преемник2")],
                       70: [("kill", "A", "A:преемник3")], 90: [("kill", "A", "A:преемник4")]}
    return w, 120


def build(sc):
    def f(p):
        if sc == "NN1":
            return S.build("DS1", p)
        if sc == "NN3":
            return _bench(p)
        if sc in ("NN2", "NN5"):
            return _world100(p)
        w, h, _ = I.everything(p, named=PER)   # NN4: часы считает сама проверка
        return w, 0
    return f


def _timed(p, named):
    t = time.perf_counter()
    w, h, _ = I.everything(p, named=named)
    for _ in range(h):
        w.step()
    return time.perf_counter() - t, w


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        p = w.p
        if sc == "NN1":
            old = S.roster("X", ("Осторожный", "Радикальный", "Осторожный", "Радикальный"), 20)
            new = named_roster("X", PER)
            key = lambda xs: [(x["name"], x["role"], x["profile"] if x["role"] != "вожак" else "-", x["alive"]) for x in xs]
            try:
                named_roster("X", 11, Params())
                over = False
            except ValueError:
                over = True
            q = I.everything(Params(), named=None)[0]
            q.factions[next(iter(q.factions))].named = named_roster("X", 11)
            try:
                q.step()
                over_step = False
            except ValueError:
                over_step = True
            ok("список из таблицы на 25 мест (вожак, 4 преемника, 20 офицеров) совпадает с прежним roster(); выше named_max — ошибка и в генераторе, и на первом тике мира",
               key(old) == key(new) and over and over_step, f"прежний {key(old)[:2]}…, из таблицы {key(new)[:2]}…, ошибка генератора {over}, ошибка мира {over_step}")
        elif sc == "NN2":
            names = {x["name"] for f_ in w.factions.values() for x in f_.named}
            logged = {r[3].split(".named.", 1)[1].rsplit(".", 1)[0] for r in w.log if ".named." in r[3]}
            sizes = [len(f_.named) for f_ in w.factions.values()]
            ok("мир 4 × 25 именных, 1000 тиков: люди сохраняются, инварианты (а)–(д) задачи 22 зелёные, число именных остаётся 100, имён вне списка нет",
               w.tick == 1000 and not w.ig_bad and sizes == [PER] * 4 and logged <= names,
               f"тик {w.tick}, нарушений {len(w.ig_bad)}: {w.ig_bad[:2]}, именных по фракциям {sizes}, имён в журнале {len(logged)}")
        elif sc == "NN3":
            A, B = w.factions["A"], w.factions["B"]
            lead = [r[5] for r in S.EXTRA_rows(w, "A.leader") if r[5] is not None]
            off_alive = sum(1 for x in A.named if x["role"] == "офицер" and x["alive"])
            ok("глубокая скамейка: вожаки по порядку преемник1…преемник4, затем никого и уклад Дрейфующие; 20 офицеров живы; тонкий список (только вожак) не роняет прогон: вожака нет, уклад Дрейфующие",
               lead == [f"A:преемник{i}" for i in range(1, 5)] and A.leader is None and A.archetype == "Дрейфующие" and off_alive == 20
               and B.leader is None and B.archetype == "Дрейфующие",
               f"вожаки A: {lead}, итог A: {A.leader}/{A.archetype}, офицеров живых {off_alive}, B: {B.leader}/{B.archetype}")
        elif sc == "NN4":
            t10, _ = _timed(p, None)
            t100, w100 = _timed(p, PER)
            ratio = t100 / max(t10, 0.3)
            ok("время прогона 1000 тиков при 100 именных не больше 15 × времени при прежних 17 именных [предл]", ratio <= 15.0,
               f"17 именных {t10:.2f} с, 100 именных {t100:.2f} с, отношение {ratio:.2f} (знаменатель не меньше 0.3 с)")
        elif sc == "NN5":
            q, h = _world100(p)
            for _ in range(h):
                q.step()
            ok("два прогона мира со 100 именными дают идентичные журналы", q.log == w.log and len(w.log) > 1000, f"строк {len(w.log)} и {len(q.log)}")
        return res
    return f


def _rows(w, target):
    return [r for r in w.log if r[3] == target]


S.EXTRA_rows = _rows
for _sc in NN:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R153": (replace(Params(), nn_bug_promote=True), ("NN2",), "именной «продвигается из ведра» в ходе игры"),
    "R154": (replace(Params(), nn_bug_roster_cap=True), ("NN2",), "генератор списка игнорирует численность выше 10"),
})
