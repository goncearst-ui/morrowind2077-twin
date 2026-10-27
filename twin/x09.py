"""Задача 09: хроника двойника (spec 09). Сценарии HC1–HC9, обратные R109–R113. Миров новых нет: проверяются чистая функция render() и существующие сценарии."""
import copy
import re
from dataclasses import replace

from .chronicle import CANDIDATES, TRACE, render, strength
from .extra import clean
from .model import Site, World
from .params import Params
from . import scenarios as S

HC = ("HC1", "HC2", "HC3", "HC4", "HC5", "HC6", "HC7", "HC8", "HC9")
BUGS = ("chronicle_bug_no_trace", "chronicle_bug_mutate", "chronicle_bug_numbers", "chronicle_bug_dup", "chronicle_bug_unnorm",
        "chronicle_candidates")
SUBSET = ("DS1", "DS2", "DS4", "OB1", "HD1", "RT1", "RL2", "MK1", "WR1", "WS1", "WE1", "EV1", "EV3", "EV8", "EV13", "EV20", "EV24", "EV26c", "PL4", "PL10", "CR1", "CR8", "PH3", "PH7")


def _quiet(p, owners=("A", "B")):
    ss = [Site(f"Х{i}", 20, 60, 2, owner=o, region="Перевал") for i, o in enumerate(owners)]
    fs = {"A": S.faction(p, "A", "Хранители", 40, 30, 0), "B": S.faction(p, "B", "Хранители", 40, 30, 0)}
    return World(fs, ss, p)


def _build(sc):
    def f(p):
        return _quiet(replace(clean(p), planet_hegemon_enabled=True)), 3
    return f


def _sub(sc, w):
    """Прогон существующего сценария; флаги хроники берутся из p проверяемого мира (обратные проверки)."""
    if sc.startswith("PH"):
        q, _ = S.run(sc)
    else:
        q, _ = S.run(sc)
    q.p = replace(q.p, **{k: getattr(w.p, k) for k in BUGS})
    return q


def _names(q):
    return set(q.factions) | {s.name for s in q.sites}


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        if sc == "HC1":
            q = _quiet(replace(w.p, chronicle_candidates=False, hunger_threshold=10.0))
            q.tick = 12
            q.events += [dict(kind="assault", tick=4, forced=False, attacker="A", defender="B", site="Х1", attacker_wins=True, ratio=1.5, losses={"A": 2, "B": 5}),
                         dict(kind="archetype_change", tick=6, faction="A", frm="Хранители", to="Хищники", rule=1),
                         dict(kind="absorb", tick=7, faction="B", n=3),
                         dict(kind="hegemon_change", tick=8, old=None, new="A"),
                         dict(kind="hegemon_change", tick=9, old="A", new="Contested")]
            q.log += [(3, 4, "00", "A.days_supply", 12.0, 8.0, "PUBLISH"), (5, 7, "06", "site.Х0.owner", "A", None, "SURRENDER")]
            q.log += [(10, 7, "06", "B.steady", 28, 12, "X")]
            q.factions["B"].steady = 12
            rows = render(q)
            by = {}
            for r in rows:
                by.setdefault(r["type"], []).append(r)
            pat = {"T1": r"Тик 4: A взяла «Х1» у B; погибло 7\.", "T2": r"У B стало меньше людей: было \d+, стало \d+\.",
                   "T3": r"У A кончается снабжение: хватит на 8 суток\.", "T4": r"«Х0» остался без хозяина", "T5": r"A больше не Хранители: теперь Хищники\.",
                   "T6": r"B приняла 3 чужих\.", "T7": r"Под A теперь большая часть планеты\.|Планета спорная\."}
            miss = [t for t, rx in pat.items() if not any(re.search(rx, r["text"]) for r in by.get(t, []))]
            ok("для T1–T7 есть шаблон, след в TRACE и строка нужного вида (T6 — на искусственном событии)",
               all(t in TRACE and TRACE[t] for t in pat) and not miss and any("спорная" in r["text"] for r in by.get("T7", [])), f"нет строк: {miss}; типы: {sorted(by)}")
        elif sc == "HC2":
            seen, bad, nrows = set(), [], 0
            allowed = set(TRACE.values())
            for name in SUBSET:
                q = _sub(name, w)
                for r in render(q):
                    nrows += 1
                    seen.add(r["type"])
                    if not r["trace"] or r["trace"] not in allowed or r["trace"] != TRACE[r["type"]]:
                        bad.append((name, r["tick"], r["type"]))
            q.events.append(dict(kind="mystery", tick=1))
            same = len(render(q)) == len(render(_sub(SUBSET[-1], w)))
            ok("у каждой строки непустой след из TRACE; неизвестное событие строк не создаёт; встретились T1, T2, T3, T4, T5, T7",
               not bad and same and {"T1", "T2", "T3", "T4", "T5", "T7"} <= seen, f"сценариев {len(SUBSET)}, строк {nrows}, типы {sorted(seen)}, без следа {bad[:3]}")
        elif sc == "HC3":
            q = _sub("EV13", w)
            before = (len(q.log), copy.deepcopy(q.events), repr(q.factions), repr(q.sites))
            a = render(q)
            b = render(q)
            after = (len(q.log), q.events, repr(q.factions), repr(q.sites))
            ok("render() не меняет журнал, события, фракции и объекты; два вызова равны", before == after and a == b and bool(a),
               f"журнал {before[0]}→{after[0]}, строк {len(a)}")
        elif sc == "HC4":
            bad, n = [], 0
            for name in ("DS1", "DS2", "EV13", "EV24", "WS1"):
                q = _sub(name, w)
                names = _names(q)
                for r in render(q):
                    n += 1
                    if not any(x in r["text"] for x in names) or re.fullmatch(r"[\d\s.:,Тик]*", r["text"]):
                        bad.append((name, r["text"]))
            ok("в каждой строке есть имя фракции или объекта; нет строк из одних чисел", n > 0 and not bad, f"строк {n}, плохих {bad[:2]}")
        elif sc == "HC5":
            q = _sub("DS1", w)
            t1 = [r for r in render(q) if r["type"] == "T1"]
            ev = [e for e in q.events if e["kind"] == "assault"]
            good = len(ev) > 0 and all(any(f"Тик {e['tick']}:" in r["text"] and e["attacker"] in r["text"] and e["defender"] in r["text"] and f"«{e['site']}»" in r["text"] for r in t1) for e in ev)
            q5 = _sub("EV13", w)
            ch = [e for e in q5.events if e["kind"] == "archetype_change"]
            t5 = [r for r in render(q5) if r["type"] == "T5"]
            good5 = bool(ch) and all(any(r["tick"] == e["tick"] and f"{e['faction']} больше не {e['frm']}: теперь {e['to']}." == r["text"] for r in t5) for e in ch)
            ok("DS1: T1 с верными атакующим, защитником, объектом, тиком; EV13: T5 со старым и новым укладом и тиком", good and good5, f"DS1 штурмов {len(ev)}, строк T1 {len(t1)}; EV13 смен {len(ch)}, T5 {len(t5)}")
        elif sc == "HC6":
            q = _sub("DS1", w)
            ev = [e for e in q.events if e["kind"] == "assault"]
            one = len([r for r in render(q) if r["type"] == "T1"]) == len(ev)
            q2 = _sub("WS1", w)
            won = [e for e in q2.events if e["kind"] == "assault" and e["attacker_wins"]]
            rows = render(q2)
            dup = [e for e in won if sum(1 for r in rows if r["tick"] == e["tick"] and f"«{e['site']}»" in r["text"]) != 1]
            ok("один штурм — одна строка T1; захват не рассказан дважды (T4 не повторяет T1)", one and bool(won) and not dup, f"DS1 штурмов {len(ev)}, WS1 захватов {len(won)}, дублей {len(dup)}")
        elif sc == "HC7":
            def mk(own, steady, arm, dos):
                q = _quiet(replace(w.p), owners=own)
                q.factions["A"].steady, q.factions["A"].ordinary, q.factions["A"].skittish = steady, 0, 0
                q.factions["A"].armory, q.factions["A"].days_supply = arm, dos
                return strength(q, "A")
            empty = mk(("B", "B"), 0, 0.0, 0.0)
            full = mk(("A", "A"), 40, 100.0, 40.0)
            seq = [[mk(own, 40, 50.0, 15.0) for own in (("B", "B"), ("A", "B"), ("A", "A"))],
                   [mk(("A", "B"), 40, a, 15.0) for a in (0.0, 50.0, 100.0)],
                   [mk(("A", "B"), 40, 50.0, d) for d in (0.0, 15.0, 30.0, 60.0)]]
            mono = all(all(x <= y for x, y in zip(s, s[1:])) for s in seq)
            inr = all(0.0 <= v <= 100.0 for s in seq for v in s + [empty, full])
            q = _sub("DS1", w)
            a = q.factions["A"]
            exp = 100 * (0.3 * (sum(1 for s in q.sites if s.owner == "A") / len(q.sites)) + 0.3 * min(1.0, a.manpower / 40) + 0.2 * a.armory / 100 + 0.2 * min(1.0, a.days_supply / 30))
            ok("пустая → 0; полная → 100; слагаемые монотонны; в пределах 0..100; DS1 совпадает с формулой docs", abs(empty) < 1e-9 and abs(full - 100) < 1e-9 and mono and inr and abs(strength(q, "A") - exp) < 1e-9,
               f"пустая {empty}, полная {full}, ряды {[[round(x, 1) for x in s] for s in seq]}, DS1 {strength(q, 'A'):.2f} ожид. {exp:.2f}")
        elif sc == "HC8":
            a, _ = S.build("DS1", replace(Params(), evolution_enabled=False))
            b, _ = S.build("DS1", replace(Params(), evolution_enabled=False))
            a.p = replace(a.p, **{k: getattr(w.p, k) for k in BUGS})
            for _ in range(15):
                a.step(); b.step()
                render(a)
            ok("журнал мира с вызовом render() после каждого тика равен журналу без вызова", a.log == b.log and a.events == b.events, f"строк {len(a.log)} / {len(b.log)}")
        elif sc == "HC9":
            def mk(flag):
                q = _quiet(replace(w.p, chronicle_candidates=flag))
                q.events += [dict(kind="depot_move", tick=3, faction="A", frm="Х0", to="CACHE", wh=1),
                             dict(kind="leader_killed", tick=5, faction="B", name="Вожак Б", reason="X"),
                             dict(kind="war_declared", tick=6, initiator="A", victim="B", goal="G"),
                             dict(kind="war_end", tick=9, initiator="A", victim="B", reason="WAR_END_TRUCE", goal="G")]
                q.log.append((6, 6, "05", "B.leader", None, "Преемник Б", "RULE_2"))
                return render(q)
            off, on = mk(False), mk(True)
            kinds = {r["type"] for r in on}
            ok("флаг выключен: кандидатных строк нет; включён: C1, C2, C3 со следами", not [r for r in off if r["type"] in CANDIDATES] and kinds >= set(CANDIDATES)
               and all(r["trace"] == TRACE[r["type"]] and r["trace"] for r in on if r["type"] in CANDIDATES) and any("преемник Преемник Б" in r["text"] for r in on), f"выкл {len(off)} строк, вкл типы {sorted(kinds)}")
        return res
    return f


for _sc in HC:
    S.EXTRA[_sc] = (_build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R109": (replace(Params(), chronicle_bug_no_trace=True), ("HC2",), "шаблон T3 без следа"),
    "R110": (replace(Params(), chronicle_bug_mutate=True), ("HC3", "HC8"), "render() дописывает в журнал"),
    "R111": (replace(Params(), chronicle_bug_numbers=True), ("HC4",), "шаблон T1 печатает только числа"),
    "R112": (replace(Params(), chronicle_bug_dup=True), ("HC6",), "T1 по строке на каждую запись журнала"),
    "R113": (replace(Params(), chronicle_bug_unnorm=True), ("HC7",), "слагаемые крепости не нормированы"),
})
