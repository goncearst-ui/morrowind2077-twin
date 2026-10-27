"""Задача 16b: стратегия — таблица (цель × трейт вожака) → множители порогов (spec 16b). Сценарии IS1–IS9, обратные R120–R124."""
from dataclasses import replace

from .extra import clean, rows
from .model import Site, World
from .objective import NEUTRAL, strategy_vector
from .params import Params
from . import scenarios as S

IS = ("IS1", "IS2", "IS3", "IS4", "IS5", "IS6", "IS7", "IS8", "IS9")
HOR = {"IS1": 1, "IS2": 1, "IS3": 3, "IS4": 1, "IS5": 14, "IS6": 200, "IS7": 200, "IS8": 5, "IS9": 5}
NH, CH, OH, AL, AH = "Neuroticism_High", "Conscientiousness_High", "Openness_High", "Agreeableness_Low", "Agreeableness_High"


def _p(p, **kw):
    base = dict(evolution_enabled=True, leader_enabled=True, npc_state_enabled=True, obj_enabled=True, strategy_enabled=True, evo_rule_order=())
    q = replace(clean(p), **{**base, **kw})
    return replace(q, archetype_assault_threshold={"Хищники": 1.1, "Контролёры": 1.6})


def _world(p, arche="Контролёры", traits=(), obj=1, fa=66, fb=35, doctrine=0, succ=()):
    """A (с вожаком, его трейты заданы) и B с объектом «Узел»; ресурсы и C подвязаны на каждый тик: мир стоит, пока его не двинет решение."""
    ss = [Site("База", 10, 0, 4, owner="A", income_disabled=True), Site("Узел", 20, 60, 2, owner="B", region="common")]
    w = World({"A": S.faction(p, "A", arche, fa, 30, 10), "B": S.faction(p, "B", "Хранители", fb, 30, 10)}, ss, p)
    S.give_named(w, "A", succ)
    w.factions["A"].named[0]["traits"] = tuple(traits)
    w.factions["A"].doctrine = doctrine
    hor = 200
    for t in range(1, hor + 1):
        w.scheduled.setdefault(t, []).extend([S.ev_pins("A", [(10**6, 9.5, None, None, 80.0)]), S.ev_pins("B", [(10**6, 30, None, None, None)])])
    for fx in w.factions.values():   # как делает build() для EXTRA: братские миры из проверок получают тот же тик 0
        w.publish_dos(fx, phase=0)
    if obj is not None:
        w.scheduled.setdefault(1, []).insert(0, lambda w: w.set_objective("A", obj, "Узел", "B"))
    return w


def _go(w, n):
    for _ in range(n):
        w.step()
    return w


def _assaults(w):
    return [(e["tick"], e["attacker"], e["site"]) for e in w.events if e["kind"] == "assault"]


def build(sc):
    def f(p):
        if sc == "IS1":
            return _world(_p(p)), 1
        if sc in ("IS2", "IS9"):
            return _world(_p(p, strategy_enabled=sc != "IS9"), traits=(NH,)), HOR[sc]
        if sc == "IS3":
            q = replace(p, evolution_enabled=True, leader_enabled=True, evo_rule_order=(), npc_state_enabled=True, obj_enabled=True, strategy_enabled=True)
            w, _ = S.build("WR1", q)
            S.give_named(w, "A")
            w.factions["A"].named[0]["traits"] = (AL,)
            w.scheduled.setdefault(1, []).insert(0, lambda w: w.set_objective("A", 3, None, "B"))
            return w, 3
        if sc == "IS4":
            return _world(_p(p), "Хищники", (), 4, fa=78, fb=40), 1
        if sc == "IS5":
            w = _world(_p(p), "Контролёры", (NH,), 1, fa=40, fb=40, succ=("Осторожный",))
            w.factions["A"].named[1]["traits"] = (CH,)
            w.scheduled.setdefault(5, []).append(lambda w: w.factions["A"].named[0].update(traits=(OH,)))
            w.player_script = {10: [("kill", "A", "A:вожак")]}
            return w, 14
        if sc == "IS6":
            return _world(_p(p), "Контролёры", (NH,), 1), 200
        if sc == "IS7":
            return _world(_p(p), "Хищники", (NH,), 1, fa=55, fb=35), 200
        if sc == "IS8":
            return _world(_p(p), "Хищники", (), 2, fa=55, fb=35, doctrine=2), 5
    return f


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        tbl = w.p.strategy_table
        if sc == "IS1":
            neg = lambda o, t, d=0: strategy_vector(tbl, o, t, d, w.p.strategy_bug_ignore_traits)
            want = {(1, NH): (0.85, 0.0, 1.0), (1, OH): (1.2, 0.0, 0.5), (1, CH): (1.0, 1.5, 1.0), (3, AL): (0.85, 0.0, 1.5), (3, OH): (1.2, 0.0, 0.5),
                    (4, "Любой"): (2.0, 0.0, 1.0), (5, AH): (1.0, 0.0, 0.5), (5, AL): (0.85, 0.0, 1.5)}
            bad = {k: (neg(*k), v) for k, v in want.items() if neg(*k) != v}
            neutral = [neg(0, (NH,)), neg(2, (NH,), 2), neg(2, (), 0), neg(1, (AL,)), neg(5, (OH,)), neg(3, (CH,))]
            first = neg(1, (CH, NH, OH))
            ok("каждая строка таблицы даёт свой вектор; пассивные и неописанные — (1.0, 0.0, 1.0); первая подходящая строка побеждает",
               not bad and all(x == NEUTRAL for x in neutral) and first == (0.85, 0.0, 1.0), f"расхождения: {bad}; нейтральные: {neutral}; приоритет: {first}")
        elif sc == "IS2":
            def run1(traits, obj, arche="Контролёры"):
                q = _world(w.p, arche, traits, obj)
                return _assaults(_go(q, 1))
            nh, ch, zero = _assaults(w), run1((CH,), 1), run1((NH,), None)
            ok("отношение 1.45, порог 1.6: Neuroticism_High (порог 1.36) → штурм на тике 1; Conscientiousness_High (порог 1.6) и цель 0 → штурма нет",
               nh == [(1, "A", "Узел")] and ch == [] and zero == [], f"NH: {nh}, CH: {ch}, цель 0: {zero}")
            hp, hp0 = run1((CH,), 1, "Хищники"), run1((), None, "Хищники")
            ok("добавлено к spec (чтобы thr_min был различим): Хищники, порог 1.1, отношение 1.45: Conscientiousness_High поднимает порог до 1.5 → штурма нет; при цели 0 штурм есть",
               hp == [] and hp0 == [(1, "A", "Узел")], f"CH: {hp}, цель 0: {hp0}")
        elif sc == "IS3":
            base, _ = S.build("WR1", replace(w.p))
            S.give_named(base, "A")
            base.factions["A"].named[0]["traits"] = (AL,)
            _go(base, 3)
            a = [r[5] for r in rows(w, "war.A>B.acc")]
            b = [r[5] for r in rows(base, "war.A>B.acc")]
            ok("ГЕГЕМОНИЯ + Agreeableness_Low: накопитель войны растёт в 1.5 раза быстрее, чем при цели 0",
               len(a) == 3 and len(b) == 3 and all(abs(x / y - 1.5) < 1e-3 for x, y in zip(a, b)), f"цель 3: {a}, цель 0: {b}")
        elif sc == "IS4":
            zero = _assaults(_go(_world(w.p, "Хищники", (), None, fa=78, fb=40), 1))
            ok("Хищники, отношение 1.5: при ИСХОДЕ (порог 2.2) штурма нет, при цели 0 (порог 1.1) штурм есть", _assaults(w) == [] and zero == [(1, "A", "Узел")], f"ИСХОД: {_assaults(w)}, цель 0: {zero}")
        elif sc == "IS5":
            st = [(r[0], r[4], r[5], r[6]) for r in rows(w, "A.strategy")]
            ok("строка strategy на тике установки цели, на тике смены трейтов (5) и на тике смены вожака (11); между ними и после — нет",
               st == [(1, "1/0/1", "0.85/0/1", "STRATEGY"), (5, "0.85/0/1", "1.2/0/0.5", "STRATEGY"), (11, "1.2/0/0.5", "1/0/1", "STRATEGY")] and w.factions["A"].leader == "A:преемник1", f"строки: {st}")
        elif sc == "IS6":
            c = _go(_world(w.p, "Контролёры", (CH,), 1), 200)
            diff = next((i for i, (x, y) in enumerate(zip(w.log, c.log)) if x != y), None)
            ok("одна цель, два характера: журналы расходятся, в прогоне NH есть штурм, в CH нет, этап цели ≥ 1 к тику 200 в обоих",
               diff is not None and len(_assaults(w)) >= 1 and _assaults(c) == [] and w.factions["A"].obj_stage >= 1 and c.factions["A"].obj_stage >= 1 and w.factions["A"].objective == 1 and c.factions["A"].objective == 1,
               f"первое расхождение: строка {diff}; штурмы NH {_assaults(w)[:2]}, CH {_assaults(c)[:2]}; этап NH {w.factions['A'].obj_stage}, CH {c.factions['A'].obj_stage}")
        elif sc == "IS7":
            k = _go(_world(w.p, "Контролёры", (NH,), 1, fa=55, fb=35), 200)
            ok("цель МОНОПОЛИЯ и один вожак у Хищников и Контролёров: журналы за 200 тиков различны (Хищники бьют, Контролёры нет)",
               w.log != k.log and len(_assaults(w)) >= 1 and _assaults(k) == [], f"Хищники {_assaults(w)[:2]}, Контролёры {_assaults(k)[:2]}")
        elif sc == "IS8":
            z = _go(_world(w.p, "Хищники", (), None, fa=55, fb=35, doctrine=2), 5)
            strip = lambda l: [r for r in l if ".obj" not in r[3]]
            ok("АВТАРКИЯ при доктрине 2: вектор нейтральный, поведение совпадает с целью 0",
               not rows(w, "A.strategy") and _assaults(w) == _assaults(z) != [] and strip(w.log) == strip(z.log), f"штурмы: {_assaults(w)} против {_assaults(z)}; строк strategy {len(rows(w, 'A.strategy'))}")
        elif sc == "IS9":
            ok("strategy_enabled = False: порог штурма не меняется (1.45 < 1.6 → штурма нет), строк strategy нет",
               _assaults(w) == [] and not rows(w, "A.strategy"), f"штурмы: {_assaults(w)}")
        return res
    return f


for _sc in IS:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R120": (replace(Params(), strategy_bug_no_mult=True), ("IS2",), "thr_mult не применяется"),
    "R121": (replace(Params(), strategy_bug_no_min=True), ("IS2",), "thr_min не применяется"),
    "R122": (replace(Params(), strategy_bug_no_acc=True), ("IS3",), "war_acc_mult не применяется"),
    "R123": (replace(Params(), strategy_bug_ignore_traits=True), ("IS6",), "таблица игнорирует трейты вожака"),
    "R124": (replace(Params(), strategy_bug_no_log=True), ("IS5",), "вектор не пишется в журнал"),
})
