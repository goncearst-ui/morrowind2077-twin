"""Задача 19: допрос пленного (spec 19). Сценарии ID1–ID11, обратные R130–R135. Двойник; Creation Kit не описывает."""
from dataclasses import replace

from .extra import clean, rows
from .interrogation import fear_of, outcome_of
from .model import BUCKETS_OUT, Site, World
from .params import Params
from . import scenarios as S

ID = ("ID1", "ID2", "ID3", "ID4", "ID5", "ID6", "ID7", "ID8", "ID9", "ID10", "ID11")


def _p(p, **kw):
    base = dict(evolution_enabled=True, leader_enabled=True, npc_state_enabled=True, interrogation_enabled=True, evo_rule_order=(), evo_m_recover=0.0)   # мораль стоит: страх допроса читает её
    return replace(clean(p), **{**base, **kw})


def _world(p, morale=60.0, script=None, n_f=1):
    """Игрок G и n_f фракций-противников F, F2, …: у каждой объект «Склад»/«Склад2» и склад на нём."""
    ss = [Site("База", 10, 0, 4, owner="G", income_disabled=True)]
    fs = {"G": S.faction(p, "G", "Хранители", 30, 30, 10)}
    for i in range(1, n_f + 1):
        nm = "F" if i == 1 else f"F{i}"
        sn = "Склад" if i == 1 else f"Склад{i}"
        ss.append(Site(sn, 10, 0, 2, owner=nm, income_disabled=True))
        fs[nm] = S.faction(p, nm, "Хранители", 40, 30, 10)
        fs[nm].morale = morale
        fs[nm].depot = sn
    w = World(fs, ss, p)
    w.player_script = script or {}
    for fx in w.factions.values():
        w.publish_dos(fx, phase=0)
    return w


def _go(w, n):
    for _ in range(n):
        w.step()
    return w


def cap(b, label=None, target="F"):
    d = {"do": "capture", "target": target, "bucket": b, "by": "G"}
    if label:
        d["label"] = label
    return d


def itg(i, k):
    return {"do": "interrogate", "id": i, "pressure": k}


def fin(do, i, **kw):
    return {"do": do, "id": i, **kw}


def _plan(sc, p):
    """(мир, горизонт)"""
    if sc == "ID2":
        return _world(p, script={2: [cap("skittish")], 3: [itg(1, 1)]}), 5
    if sc == "ID3":
        return _world(p, 60.0, {2: [cap("steady")], 3: [itg(1, 6)]}), 5
    if sc == "ID4":
        return _world(p, 50.0, {2: [cap("ordinary", "Вспыльчивый")], 3: [itg(1, 3)]}), 5
    if sc == "ID5":
        w = _world(p, 50.0, n_f=4)
        sc_ = {2: [cap("ordinary", "Хладнокровный", t) for t in ("F", "F2", "F3", "F4")],
               3: [itg(1, 6), itg(2, 6), itg(3, 6)]}
        w.player_script = sc_
        w.forced_assaults = {8: [("G", "Склад")]}
        return w, 10
    if sc == "ID6":
        return _world(p, script={2: [cap("skittish")], 3: [itg(1, 1)]}), 5
    if sc == "ID7":
        return _world(p, script=_conserve_script()), 9
    if sc == "ID8":
        return _world(p, script={2: [cap("skittish"), cap("steady")], 3: [itg(1, 1)], 4: [fin("release", 1), fin("release", 2)]}), 6
    if sc == "ID9":
        q = replace(p, reputation_enabled=True, player_levers_enabled=True)
        return _world(q, script={2: [cap("ordinary")], 3: [fin("execute", 1, witnesses=1)]}), 8
    if sc == "ID10":
        return _world(p, script=_conserve_script()), 9
    if sc == "ID11":
        return _world(replace(p, interrogation_enabled=False), script={2: [cap("skittish")], 3: [itg(1, 1)]}), 5
    raise KeyError(sc)


def _conserve_script():
    return {2: [cap("skittish"), cap("ordinary"), cap("steady")], 3: [itg(1, 1)], 4: [fin("release", 2)], 5: [fin("hand_over", 3)], 6: [fin("execute", 1)]}


def build(sc):
    def f(p):
        if sc == "ID1":
            return _world(_p(p)), 1
        return _plan(sc, _p(p))
    return f


def _know(w):
    return [(r[0], r[4], r[5], r[6]) for r in rows(w, "know.G>Склад")]


def _outcome(w, i=1):
    return [(r[0], r[5]) for r in rows(w, f"prisoner.{i}.outcome")]


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        p = w.p
        if sc == "ID1":
            lab = ("Пугливый", "", "Бродяга", "Вспыльчивый", "Хладнокровный", "Упёртый")
            want = {"Пугливый": ("truth",) * 3, "": ("silent", "truth", "truth"), "Вспыльчивый": ("silent", "lie", "truth"),
                    "Хладнокровный": ("silent", "silent", "trap"), "Упёртый": ("silent",) * 3}
            got = {l: tuple(outcome_of(p, l, fear_of(p, l, k, 50.0), 50.0) for k in (0, 3, 6)) for l in want}
            bro = tuple(outcome_of(p, "Бродяга", fear_of(p, "Бродяга", k, 50.0), 50.0, paid=True) for k in (0, 3, 6))
            bro0 = tuple(outcome_of(p, "Бродяга", fear_of(p, "Бродяга", k, 50.0), 50.0) for k in (0, 3, 6))
            ok("каждый ярлык при давлении 0, 3, 6 и морали 50 даёт ожидаемый исход (Бродяга — только при оплате)", got == want and bro == ("silent", "truth", "truth") and bro0 == ("silent",) * 3, f"исходы: {got}, Бродяга с оплатой {bro}, без {bro0}")
        elif sc in ("ID2", "ID6"):
            if sc == "ID2":
                ok("пугливый, давление 1: страх 68, правда; знание G о складе F стоит, INTERROGATE_TRUE",
                   _outcome(w) == [(3, "truth")] and _know(w) == [(3, None, "F", "INTERROGATE_TRUE")], f"исход: {_outcome(w)}, знание: {_know(w)}")
            else:
                try:
                    w.player_action(itg(1, 1))
                    err = None
                except ValueError as e:
                    err = str(e)
                ok("второй допрос того же пленного — ValueError", err is not None and "один секрет" in err, f"ошибка: {err}")
        elif sc == "ID3":
            hi = _world(replace(w.p), 15.0, {2: [cap("steady")], 3: [itg(1, 6)]})
            _go(hi, 5)
            ok("упёртый, давление 6, мораль 60: молчит, строк знания нет; при морали 15 — правда", _outcome(w) == [(3, "silent")] and not _know(w) and _outcome(hi) == [(3, "truth")] and _know(hi) == [(3, None, "F", "INTERROGATE_TRUE")],
               f"мораль 60: {_outcome(w)}, знание {_know(w)}; мораль 15: {_outcome(hi)}, знание {_know(hi)}")
        elif sc == "ID4":
            lie = [e for e in w.events if e["kind"] == "interrogation_lie"]
            ok("вспыльчивый, страх 60: ложь, событие interrogation_lie, знание не меняется", _outcome(w) == [(3, "lie")] and len(lie) == 1 and not _know(w) and not w.know, f"исход: {_outcome(w)}, знание: {_know(w)}")
        elif sc == "ID5":
            loss = [r for r in w.log if r[6] == "INTERROGATE_TRAP" and r[3].startswith("G.") and r[3] != "G.trap"]
            lost = sum(r[4] - r[5] for r in loss if r[3] in ("G.steady", "G.ordinary", "G.skittish"))
            traps = [r for r in w.log if r[3].startswith("trap.")]
            q = _plan("ID5", w.p)[0]
            _go(q, 4)
            try:
                q.player_action(itg(4, 6))
                err = None
            except ValueError as e:
                err = str(e)
            ok("хладнокровный: ловушка на «Складе»; штурм G стоит 3 бойцов (INTERROGATE_TRAP); четвёртая ловушка — ValueError",
               len(w.traps) == 2 and "Склад" not in w.traps and len(q.traps) == 3 and lost == p.trap_losses and err is not None and "ловушек" in err, f"ловушки в конце: {w.traps}, потери: {lost}, строки: {traps}, ошибка: {err}")
        elif sc == "ID7":
            q = _plan("ID7", w.p)[0]
            start = {n: x.manpower + x.wounded + sum(getattr(x, b) for b in BUCKETS_OUT) - x.absorbed for n, x in q.factions.items()}
            bad = []
            for _ in range(9):
                q.step()
                for n, x in q.factions.items():
                    if x.manpower + x.wounded + sum(getattr(x, b) for b in BUCKETS_OUT) != start[n] + x.absorbed:
                        bad.append((q.tick, n))
            ok("на всех тиках (захват → допрос → выпустить / сдать / казнить) люди мира сходятся с учётом held, captured, deserted, dead", not bad and q.factions["F"].held == 0, f"расхождения: {bad[:3]}; F: dead {q.factions['F'].dead}, captured {q.factions['F'].captured}, deserted {q.factions['F'].deserted}")
        elif sc == "ID8":
            des = rows(w, "F.deserted", "RELEASED_DESERTED")
            back = rows(w, "F.steady", "RELEASED_SUSPECT")
            sh = rows(w, "F.shock", "RELEASED_SUSPECT")
            ok("напуганный (страх 68) выбывает, RELEASED_DESERTED; ненапуганный возвращается в ведро, шок RELEASED_SUSPECT +1",
               len(des) == 1 and des[0][5] == 1 and len(back) == 1 and len(sh) == 1 and round(sh[0][5] - sh[0][4], 4) == p.purge_shock, f"deserted: {des}, возврат: {back}, шок: {sh}")
        elif sc == "ID9":
            sh = rows(w, "F.shock", "EXECUTE")
            rum = [r for r in w.log if r[3].startswith("rep.rumor.F") and r[6] == "RUMOR_NEW"]
            ident = [e for e in w.events if e["kind"] == "rep_identified"]
            q = _plan("ID9", w.p)[0]
            q.player_script[3] = [fin("execute", 1, witnesses=0)]
            _go(q, 8)
            ok("казнь: шок на фракции пленного, EXECUTE; со свидетелем — слух и событие репутации, без свидетелей — нет", len(sh) == 1 and sh[0][5] > sh[0][4] and len(rum) == 1 and len(ident) == 1 and not [r for r in q.log if r[3].startswith("rep.rumor")],
               f"шок: {sh}, слухи: {rum}, события: {len(ident)}")
        elif sc == "ID10":
            a = _plan("ID10", w.p)[0]
            _go(a, 9)
            ok("два прогона сценария идентичны", a.log == w.log and a.events == w.events and len(w.log) > 0, f"строк {len(w.log)}")
        elif sc == "ID11":
            fl = [(e["tick"], e["action"], e["code"]) for e in w.events if e["kind"] == "player_failed"]
            ok("interrogation_enabled = False: capture и interrogate — отказ DISABLED; ни одной строки prisoner / held", fl == [(2, "capture", "DISABLED"), (3, "interrogate", "DISABLED")] and not [r for r in w.log if r[3].startswith(("prisoner", "trap")) or r[3].endswith(".held")], f"отказы: {fl}")
        return res
    return f


for _sc in ID:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R130": (replace(Params(), int_bug_no_trap_cost=True), ("ID5",), "ловушка не стоит бойцов"),
    "R131": (replace(Params(), int_bug_lie_knowledge=True), ("ID4",), "ложь ставит знание"),
    "R132": (replace(Params(), int_bug_stubborn_talks=True), ("ID3",), "Упёртый говорит при высокой морали"),
    "R133": (replace(Params(), int_bug_uncounted=True), ("ID7",), "пленный не учитывается в сумме людей"),
    "R134": (replace(Params(), int_bug_repeat=True), ("ID6",), "повторный допрос проходит"),
    "R135": (replace(Params(), int_bug_scared_returns=True), ("ID8",), "напуганный отпущенный возвращается"),
})
