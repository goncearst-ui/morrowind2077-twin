"""Задача 01: личное состояние именных (spec 01). Сценарии NP1–NP9, обратные R84–R90."""
from dataclasses import replace
from itertools import combinations

from .extra import clean, rows
from .model import Site, World
from .npc import TRAITS, bucket_of, package_for, temperament
from .params import Params
from . import scenarios as S

NP = ("NP1", "NP2", "NP3", "NP4", "NP5", "NP6", "NP6b", "NP7", "NP7b", "NP8", "NP9")


def _p(p, **kw):
    return replace(clean(p), evolution_enabled=True, leader_enabled=True, evo_rule_order=(), relations_enabled=True,
                   knowledge_enabled=True, player_levers_enabled=True, **kw)


def _world(p, arch="Хранители", traits=("Neuroticism_Low",)):
    fs = {"A": S.faction(p, "A", arch, 30, 40, 0), "B": S.faction(p, "B", "Хранители", 30, 40, 40)}
    w = World(fs, [Site("Перевал", 40, 90, 4, owner="B")], p)
    for n in "AB":
        S.give_named(w, n, successors=("Осторожный",), officers=1)
    w.factions["A"].named[0]["traits"] = tuple(traits)
    return w


def build(sc):
    def f(p):
        if sc in ("NP1", "NP2", "NP3", "NP8"):
            return _world(_p(p, npc_state_enabled=True)), 2
        if sc == "NP4":
            w = _world(_p(p, npc_state_enabled=True))
            w.player_script = {1: [("threaten", "A", "A:вожак")] * 3}
            return w, 14
        if sc == "NP5":
            w = _world(_p(p, npc_state_enabled=True), arch="Хищники")
            w.scheduled = {5: [lambda w: w._switch(w.factions["A"], "Контролёры", 3)]}
            return w, 7
        if sc in ("NP6", "NP6b"):
            w = _world(_p(p, npc_state_enabled=True), arch="Хищники")
            if sc == "NP6":
                w.scheduled = {2: [lambda w: w._switch(w.factions["A"], "Контролёры", 3)]}
            w.player_funds = 1000.0
            w.player_script = {4: [("bribe", "A", "B", 300.0)]}
            return w, 6
        if sc in ("NP7", "NP7b"):
            w, h = S.build("PL9", replace(p, npc_state_enabled=True))
            def prep(w, sc=sc):
                w.player_rep["B"] = 20.0
                ln = next(x for x in w.factions["B"].named if x["name"] == "B:вожак")
                ln["debt"] = 300.0 if sc == "NP7" else 0.0
            w.scheduled.setdefault(20, []).append(prep)
            return w, h
        if sc == "NP9":
            return _world(replace(_p(p), npc_state_enabled=False)), 8
    return f


SETS = [c for k in range(0, 5) for c in combinations(TRAITS, k) if not ({"Neuroticism_High", "Neuroticism_Low"} <= set(c)) and not ({"Agreeableness_High", "Agreeableness_Low"} <= set(c))]


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        p = w.p
        T = lambda *t: temperament(t, p.npc_swap34)
        if sc == "NP1":
            cases = [(("Neuroticism_High", "Agreeableness_Low"), "Вспыльчивый"), (("Neuroticism_High",), "Пугливый"),
                     (("Neuroticism_High", "Agreeableness_Low", "Conscientiousness_High"), "Вспыльчивый"),
                     (("Neuroticism_Low", "Agreeableness_Low"), "Хладнокровный"), (("Neuroticism_Low", "Conscientiousness_High"), "Упёртый"),
                     (("Neuroticism_Low", "Agreeableness_Low", "Conscientiousness_High"), "Хладнокровный"),
                     (("Openness_High",), "Бродяга"), (("Openness_High", "Neuroticism_High"), "Пугливый"),
                     (("Neuroticism_Low",), None), ((), None)]
            bad = [(c, T(*c), e) for c, e in cases if T(*c) != e]
            ok("таблица ярлыков", not bad, f"расхождения: {bad}")
        elif sc == "NP2":
            bad = []
            for c in SETS:
                t, b = temperament(c), bucket_of(c, p.npc_steady_for_skittish)
                if (t == "Упёртый" and b != "steady") or (t in ("Пугливый", "Вспыльчивый") and b != "skittish") \
                        or (t == "Хладнокровный" and b not in ("steady", "ordinary")) or (t == "Бродяга" and b == "skittish"):
                    bad.append((c, t, b))
            ok("ярлыки согласованы с вёдрами по всем наборам трейтов", not bad and len(SETS) > 20, f"наборов {len(SETS)}, расхождения: {bad[:3]}")
        elif sc == "NP3":
            P = package_for
            cases = [(P("Хищники", "Role_Soldier", ("Neuroticism_Low",)), "Raid_Package"), (P("Хищники", "Role_Soldier", ("Neuroticism_High",)), "Loot_Avoid_Pkg"),
                     (P("Контролёры", "Role_Soldier", ()), "Toll_Package"), (P("Хранители", "Role_Leader", ()), "Work_Sandbox"),
                     (P("Хищники", "Role_Soldier", ("Neuroticism_Low",), night=True), "Raid_Package"), (P("Хранители", "Role_Leader", (), night=True), "Home_Sandbox"),
                     (P("Хранители", "Role_Soldier", (), fear=None, loyalty=None, share_dropped=True), "Work_Sandbox"),
                     (P("Хранители", "Role_Soldier", (), fear=80.0, loyalty=10.0, share_dropped=True), "Avoid_Package"),
                     (P("Хранители", "Role_Soldier", (), fear=0.0, loyalty=10.0, share_dropped=True), "Disaffected_Pkg")]
            ok("стек пакетов", all(a == b for a, b in cases), f"{[(a, b) for a, b in cases if a != b]}")
        elif sc == "NP4":
            fr = {r[0]: r[5] for r in rows(w, "A.named.A:вожак.fear")}
            pk = rows(w, "A.named.A:вожак.package")
            ok("fear на тике t = 90 − 2·(t − 1)", all(abs(fr.get(t, 0) - (90 - 2 * (t - 1))) < 1e-9 for t in range(2, 12)) and fr.get(12) == 68.0, f"fear: {fr}")
            ok("Avoid_Package с тика 1, возврат к Work_Sandbox на тике 12, не раньше", [(r[0], r[5]) for r in pk] == [(1, "Avoid_Package"), (12, "Work_Sandbox")], f"пакеты: {[(r[0], r[5]) for r in pk]}")
        elif sc == "NP5":
            n = w.factions["A"].named[0]
            pk = [(r[0], r[5]) for r in rows(w, "A.named.A:вожак.package")]
            ok("share 35 → 10, loyalty 60 → 10, флаг, Disaffected_Pkg на тике 5", n["share"] == 10.0 and n["loyalty"] == 10.0 and n["share_dropped"] and pk[-1] == (5, "Disaffected_Pkg"),
               f"share {n['share']}, loyalty {n['loyalty']}, пакеты {pk}")
            ok("строки в журнале на тике 5", {r[3] for r in w.log if r[0] == 5 and r[2] == "01"} >= {"A.named.A:вожак.share", "A.named.A:вожак.loyalty", "A.named.A:вожак.package"}, "ок")
        elif sc == "NP6":
            i = rows(w, "rel.A>B.i", "PLAYER_BRIBE")
            ok("недовольный: цена 50, прирост 6.0, списано 300, debt 300", [r[5] for r in i] == [6.0] and w.player_funds == 700.0 and w.factions["A"].named[0]["debt"] == 300.0, f"i {i}, деньги {w.player_funds}, debt {w.factions['A'].named[0]['debt']}")
            o, _ = S.run("NP6b", w.p)
            io = rows(o, "rel.A>B.i", "PLAYER_BRIBE")
            ok("не недовольный: то же +3.0", [r[5] for r in io] == [3.0], f"i {io}")
        elif sc == "NP7":
            we = [(e["tick"], e["reason"]) for e in w.events if e["kind"] == "war_end"]
            o, _ = S.run("NP7b", w.p)
            pf = [(e["tick"], e["code"]) for e in o.events if e["kind"] == "player_failed"]
            ok("долг 300 при репутации 20: убеждение принято (WAR_END_PLAYER); при долге 0 — LOW_REP", (22, "WAR_END_PLAYER") in we and (22, "LOW_REP") in pf, f"с долгом: {we}; без долга: {pf}")
        elif sc == "NP8":
            before = (len(w.log), {n: (f.manpower, f.supply) for n, f in w.factions.items()})
            outs = {package_for("Хищники", "Role_Soldier", ("Neuroticism_Low",)) for _ in range(1000)}
            outs2 = {package_for("Контролёры", "Role_Soldier", ()) for _ in range(1000)}
            after = (len(w.log), {n: (f.manpower, f.supply) for n, f in w.factions.items()})
            ok("рядовые: 1000 вызовов дают один результат, мир не меняется", outs == {"Raid_Package"} and outs2 == {"Toll_Package"} and before == after, f"{outs}, {outs2}")
        elif sc == "NP9":
            ok("npc_state_enabled = False: ни одной строки пакета и личных чисел", not [r for r in w.log if r[2] == "01"], f"строк модуля 01: {len([r for r in w.log if r[2] == '01'])}")
        elif sc == "NP6b":
            pass
        elif sc == "NP7b":
            pass
        return res
    return f


for _sc in NP:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R84": (replace(Params(), npc_swap34=True), ("NP1",), "строки 3 и 4 таблицы ярлыков поменяны"),
    "R85": (replace(Params(), npc_steady_for_skittish=True), ("NP2",), "Neuroticism_High не даёт Skittish"),
    "R86": (replace(Params(), npc_fear_decay=0.0), ("NP4",), "страх не затухает"),
    "R87": (replace(Params(), npc_loyalty_share_k=0.0), ("NP5",), "падение доли не бьёт по верности"),
    "R88": (replace(Params(), npc_bribe_disaffected_mult=1.0), ("NP6",), "скидки недовольному нет"),
    "R89": (replace(Params(), npc_persuade_debt_waive=1e9), ("NP7",), "долг не снимает проверку LOW_REP"),
    "R90": (replace(Params(), npc_avoid_fear=100.0), ("NP4",), "порог избегания 100"),
})
