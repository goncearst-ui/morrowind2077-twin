"""Задача 22: мир «всё включено», инварианты и таблица флагов (spec 22). Двойник; Creation Kit не описывает."""
import dataclasses
import random
from dataclasses import replace

from . import objective as O
from . import scenarios as S
from .extra import clean
from .model import BUCKETS_OUT, Faction, Site, World
from .params import Params

M, R, K, D = "Метрополия", "Налётчики", "Колония", "Дрейф"   # Контролёры, Хищники, Хранители (Колония-проект из 17), Дрейфующие
# что требует что: флаг -> то, без чего он не работает (ValueError в step/set_objective); нужно для «выключения по одному» (замыкание вверх)
REQ = {"leader_enabled": ("evolution_enabled",), "npc_state_enabled": ("leader_enabled",), "obj_enabled": ("leader_enabled", "evolution_enabled"),
       "strategy_enabled": ("obj_enabled", "npc_state_enabled"), "inheritance_enabled": ("obj_enabled", "strategy_enabled"),
       "interrogation_enabled": ("npc_state_enabled",), "player_levers_enabled": ("leader_enabled",), "reputation_enabled": ("player_levers_enabled",),
       "envoys_enabled": ("reputation_enabled", "player_levers_enabled", "leader_enabled"), "raid_discipline_enabled": ("knowledge_enabled",), "wars_enabled": ("relations_enabled", "knowledge_enabled"),
       "war_steers_attacks": ("wars_enabled",)}
SCALAR = (int, float, str, type(None))


NOT_IN_WORLD22 = ("log_two_level_enabled", "multi_planet_enabled")   # spec 23: меняют формат журнала и устройство мира, а не поведение 4-фракционного мира задачи 22; проверяются своими сценариями LG и MP


def flags():
    """Все булевы поля Params с именем *_enabled (по шаблону spec 22 п. 1) в порядке объявления, кроме флагов масштаба (NOT_IN_WORLD22)."""
    return [f.name for f in dataclasses.fields(Params) if f.name.endswith("_enabled") and isinstance(f.default, bool) and f.name not in NOT_IN_WORLD22]


def all_on(p, off=(), **kw):
    """Все флаги *_enabled включены (кроме off и их зависимых); возвращает (params, фактически выключенные)."""
    cut = set(off)
    grew = True
    while grew:
        grew = False
        for fl, need in REQ.items():
            if fl not in cut and any(n in cut for n in need):
                cut.add(fl)
                grew = True
    q = replace(clean(p), **{f: (f not in cut) for f in flags()}, war_steers_attacks="war_steers_attacks" not in cut, evo_rule_order=Params().evo_rule_order, hunger_threshold=Params().hunger_threshold, **kw)
    q = replace(q, archetype_assault_threshold={"Хищники": 1.1, "Контролёры": 1.6, "Дрейфующие": 1.3, "Хранители": 2.0}, **{k: v for k, v in S.OLD_WAR.items() if False})
    return q, sorted(cut)


def _act(w, needs, act):
    """Действие игрока из распорядка: пропускается, если нужный выключатель выключен."""
    if all(getattr(w.p, n) for n in needs):
        w.player_action(act)
        return True
    w.events.append(dict(kind="player_script_skipped", tick=w.tick, action=act[0] if isinstance(act, tuple) else act.get("do"), needs=needs))
    return False


def _capture(w):
    """Игрок берёт пленного у Налётчиков: из первого непустого ведра (состав к тику 80 зависит от прогона)."""
    b = next((x for x in ("ordinary", "steady", "skittish") if getattr(w.factions[R], x) >= 1), None)
    if b is not None:
        _act(w, ("interrogation_enabled",), {"do": "capture", "target": R, "bucket": b, "by": K})


def everything(p, variant=0, off=(), named=None):
    """Четыре фракции, все флаги включены (кроме off), распорядок игрока. Без случайности. Возвращает (мир, горизонт, выключенные).
    named: число именных на фракцию из фиксированного списка twin/data/named_roster.json (spec 23b); None = прежние ростеры."""
    q, cut = all_on(p, off)
    if named:
        q = replace(q, named_max=max(q.named_max, named))
    if q.ig_bug_nocap:   # R149: потолок активных целей снят
        q = replace(q, obj_bug_no_cap=True)
    ss = [Site("Метро-1", 40, 135, 4, owner=M, region="Центр"), Site("Узел", 20, 100, 2, owner=M, region="Центр"),
          Site("Форпост", 25, 70, 3, owner=R, region="Центр"), Site("Колония-1", 20, 130, 2, owner=K, region="Колония"),
          Site("Дрейф-1", 20, 70, 2, owner=D, region="Центр"), Site("Станция", 30, 70, 2, owner=D, region="Центр", kind=1)]
    fs = {M: S.faction(q, M, "Контролёры", 66, 12.0, 60), R: S.faction(q, R, "Хищники", 60, 7.0, 25), K: S.faction(q, K, "Хранители", 40, 30.0, 20),
          D: S.faction(q, D, "Дрейфующие", 45, 8.0, 50)}
    fs[K].home = "Колония"
    for n in (M, R, D):
        fs[n].home = "Центр"
    fs[K].doctrine = 2
    w = World(fs, ss, q)
    for n, succ, off_n in ((M, ("Осторожный", "Радикальный"), 2), (R, ("Радикальный",), 2), (K, ("Осторожный",), 1), (D, ("Идеолог", "Осторожный"), 2)):
        S.give_named(w, n, successors=succ, officers=off_n)
        if named:
            from .named import named_roster
            w.factions[n].named = named_roster(n, named, q)
    tr = {M: ("Openness_High",), R: ("Conscientiousness_High", "Agreeableness_Low"), K: ("Conscientiousness_High",), D: ("Agreeableness_Low", "Neuroticism_High")}
    for n, t in tr.items():
        w.factions[n].named[0]["traits"] = t
    w.known_at_start = {M: ("Форпост",), R: ("Узел", "Метро-1"), D: ("Узел", "Форпост", "Колония-1")}
    if q.obj_enabled:
        sets = [lambda w: w.set_objective(M, 3, "Форпост", R), lambda w: w.set_objective(K, 2, None, None),
                lambda w: w.set_objective(R, 4 if variant else 1, "Узел", M)]
        if q.obj_bug_no_cap:   # R149: потолок снят — третья активная цель
            sets.append(lambda w: w.set_objective(D, 5, "Узел", M))
        w.scheduled.setdefault(1, [])[0:0] = sets
    w.player_funds = 3000.0
    if q.ig_bug_people:   # R145: тайный прирост людей (строка журнала есть, баланс людей нарушен)
        w.scheduled.setdefault(50, []).append(lambda w: [w.setf(w.factions[M], x, getattr(w.factions[M], x) + 3, 0, "22", "BUG") for x in ("steady", "rank")])
    if q.ig_bug_nolog:    # R146: поле меняется без строки журнала
        w.scheduled.setdefault(40, []).append(lambda w: setattr(w.factions[K], "morale", w.factions[K].morale - 5.0))
    if q.ig_bug_random:   # R148: вызов случайности
        w.scheduled.setdefault(10, []).append(lambda w: random.random())
    w.forced_assaults = {t: [(R, "Дрейф-1")] for t in (3, 9)} | { 100: [(R, "Узел")], 106: [(R, "Узел")], 112: [(R, "Узел")]}   # слабые налёты Колонии на голодный Дрейф: обида Дрейфа → война (08a–08b)
    for t in range(5, 41):   # Колония держит контроль: цель АВТАРКИЯ достигается (16a); свой вход сценария, строки журнала пишет setf
        w.scheduled.setdefault(t, []).append(lambda w: w.setf(w.factions[K], "ctl", 70.0, 0, "22", "SCENARIO") if w.factions[K].ctl != 70.0 else None)
    sc = w.scheduled
    kill_opts = {"witnesses": 1, "masked": False}
    steps = [(20, (), ("kill", R, f"{R}:офицер1")), (30, ("player_levers_enabled", "relations_enabled", "leader_enabled"), ("bribe", D, M, 200.0)),
             (150, (), ("kill", M, f"{M}:вожак")), (35, ("knowledge_enabled", "player_levers_enabled", "leader_enabled"), ("tip", D, "Метро-1")), (125, ("wars_enabled", "player_levers_enabled", "leader_enabled"), ("persuade", M, R))]
    for t, needs, act in steps:
        if q.reputation_enabled and act[0] == "kill" if isinstance(act, tuple) else False:
            act = act + (kill_opts,)
        sc.setdefault(t, []).append(lambda w, n=needs, a=act: _act(w, n, a))
    sc.setdefault(80, []).append(_capture)
    sc.setdefault(82, []).append(lambda w: _act(w, ("interrogation_enabled",), {"do": "interrogate", "id": 1, "pressure": 3}) if 1 in w.prisoners else None)
    sc.setdefault(90, []).append(lambda w: _act(w, ("interrogation_enabled",), {"do": "release", "id": 1}) if 1 in w.prisoners and w.prisoners[1]["state"] == "held" else None)
    for f in w.factions.values():
        w.publish_dos(f, phase=0)
    return w, 1000, cut


# служебные поля: часы и кэши, чьё изменение несёт другая строка журнала того же тика (событие, OBJ_SET, смена уклада); для них проверяем
# слабее — у фракции в этот тик есть хотя бы одна строка. Это находка для отчёта: строк «имя.поле» у них нет. ctl: ленивое None → число на первом тике.
SERVICE = ("last_raid", "last_assault", "obj_stage_tick", "obj_target", "obj_rival", "obj_rival_start", "obj_rival_depot", "obj_start", "strategy_txt", "changes")
FIELDS = [f.name for f in dataclasses.fields(Faction) if f.name not in ("name",)]


def _snap(w):
    out = {}
    for n, f in w.factions.items():
        out[n] = {a: getattr(f, a) for a in FIELDS if isinstance(getattr(f, a), SCALAR)}
    return out


def _rnd(x):
    return round(x, 4) if isinstance(x, float) else x


class NoRandom:
    """Во время прогона любой вызов random / secrets / os.urandom — нарушение (д)."""
    NAMES = ("random", "randint", "choice", "choices", "shuffle", "sample", "uniform", "randrange", "getrandbits", "gauss", "seed")

    def __init__(self):
        self.hits = []

    def __enter__(self):
        import os
        import secrets
        self.saved = []
        for mod, names in ((random, self.NAMES), (secrets, ("randbelow", "token_bytes", "choice")), (os, ("urandom",))):
            for nm in names:
                if hasattr(mod, nm):
                    self.saved.append((mod, nm, getattr(mod, nm)))
                    setattr(mod, nm, self._trap(f"{mod.__name__}.{nm}"))
        return self

    def _trap(self, nm):
        def f(*a, **k):
            self.hits.append(nm)
            raise RuntimeError(f"случайность запрещена: {nm}")
        return f

    def __exit__(self, *a):
        for mod, nm, orig in self.saved:
            setattr(mod, nm, orig)
        return False


def instrument(w):
    """Оборачивает w.step: после каждого тика проверяются инварианты (а)–(д); нарушения копятся в w.ig_bad = [(тик, буква, подробность)]."""
    orig = w.step
    w.ig_bad = []
    start = {n: f.manpower for n, f in w.factions.items()}

    def step():
        before = _snap(w)
        i0 = len(w.log)
        e0 = len(w.events)
        with NoRandom() as nr:
            try:
                orig()
            except RuntimeError as e:
                if not nr.hits:
                    raise
                w.ig_bad.append((w.tick, "д", str(e)))
                return
        t = w.tick
        for n, f in w.factions.items():                                              # (а) люди не берутся из воздуха
            tot = f.manpower + f.wounded + sum(getattr(f, b) for b in BUCKETS_OUT)
            if tot != start[n] + f.absorbed:
                w.ig_bad.append((t, "а", f"{n}: учтено {tot}, должно быть {start[n] + f.absorbed}"))
        if sum(1 for f in w.factions.values() if O.is_active(f, f.objective)) > w.p.obj_max_active:   # (г) потолок активных целей 16a
            w.ig_bad.append((t, "г", "активных целей больше потолка 16a"))
        rows = w.log[i0:]
        for r in rows:                                                               # (б) семь полей: tick, phase, module, target, old, new, reason
            if len(r) != 7 or r[0] != t or not isinstance(r[1], int) or not r[6]:
                w.ig_bad.append((t, "б", f"строка {r}"))
        after = _snap(w)
        ticked = any(e.get("tick") == t for e in w.events[e0:])
        for n in after:                                                              # (в) каждое изменение поля — строка с теми же old/new
            for a, v in after[n].items():
                if before[n].get(a) == v:
                    continue
                if a in SERVICE or (a == "ctl" and before[n].get(a) is None):
                    if not any(n in r[3] for r in rows) and not ticked:
                        w.ig_bad.append((t, "в", f"{n}.{a}: служебное поле изменилось без единой строки фракции в этот тик"))
                    continue
                mine = [r for r in rows if r[3] == f"{n}.{a}"]
                if not mine or _rnd(mine[0][4]) != _rnd(before[n][a]) or _rnd(mine[-1][5]) != _rnd(v):
                    w.ig_bad.append((t, "в", f"{n}.{a}: {before[n].get(a)} → {v}, строк {len(mine)}"))

    w.step = step
    return w


def simulate(p, off=(), variant=0):
    """Мир «всё включено» (без off) с инвариантами. Возвращает (мир, нарушения, выключенные)."""
    w, h, cut = everything(p, variant, off)
    instrument(w)
    for _ in range(h):
        w.step()
    return w, w.ig_bad, cut


# ---------- таблица флагов (spec 22 п. 3–4) ----------
_CACHE = {}
TABLE_PATH = "reports/22-flag-table.md"


def _key(p):
    return tuple(getattr(p, k) for k in ("ig_bug_people", "ig_bug_nolog", "ig_bug_table_skip", "ig_bug_random", "ig_bug_nocap"))


def _final(w):
    out = {f"{n}.{k}": getattr(f, k) for n, f in w.factions.items() for k in ("archetype", "objective", "leader")}
    out |= {f"{n}.manpower": f.manpower for n, f in w.factions.items()}
    out |= {f"site.{s.name}": s.owner for s in w.sites}
    return out


def kinds(w):
    from collections import Counter
    return Counter(e["kind"] for e in w.events)


def table(p):
    """Прогон «всё включено» и n прогонов с одним выключенным флагом. Кэш по тестовым параметрам. Возвращает dict(base=(мир, нарушения), baseless=…, rows=[…])."""
    k = _key(p)
    if k in _CACHE:
        return _CACHE[k]
    base, bad, _ = simulate(p)
    none, _, _ = simulate(p, off=[f for f in flags() if not getattr(Params(), f)])   # «без флагов»: выключено всё, что выключено по умолчанию
    rows = []
    on_set, on_fin = set(base.log), _final(base)
    for fl in flags():
        if p.ig_bug_table_skip and fl == flags()[-1]:
            continue
        w, b, cut = simulate(p, off=[fl])
        off_set, off_fin = set(w.log), _final(w)
        rows.append(dict(flag=fl, default=bool(getattr(Params(), fl)), also_off=[c for c in cut if c != fl], rows_on=len(base.log), rows_off=len(w.log),
                         delta=len(base.log) - len(w.log), diverge=len(on_set ^ off_set), final_diff=sum(1 for x in on_fin if on_fin[x] != off_fin.get(x)),
                         red=len(b), first_red=b[0] if b else None, kinds_off=kinds(w)))
    _CACHE[k] = dict(base=base, bad=bad, none=none, rows=rows)
    return _CACHE[k]


def recommend(r):
    """Предложение по флагу с числовым обоснованием. Не решение: значения по умолчанию меняет только Стан."""
    share = 100.0 * r["delta"] / r["rows_on"] if r["rows_on"] else 0.0
    nums = f"строк журнала с флагом на {r['delta']:+d} ({share:+.1f}% от {r['rows_on']}), расхождений журнала {r['diverge']}, различий итога {r['final_diff']}"
    if r["red"]:
        t, letter, det = r["first_red"]
        return f"оставить опцией: при выключении {r['red']} нарушений инвариантов (первое — тик {t}, п. {letter}); {nums}"
    if r["default"]:
        return f"уже включён по умолчанию; {nums}"
    if r["diverge"] == 0:
        return f"можно включить по умолчанию: в этом мире ничего не меняет (0 расхождений); {nums}"
    if share <= 10.0:
        return f"кандидат на включение по умолчанию: инварианты зелёные, вклад в журнал не больше 10%; {nums}"
    return f"оставить опцией: вклад в журнал больше 10%; {nums}"


def render(p):
    t = table(p)
    base, none = t["base"], t["none"]
    ratio = len(base.log) / max(1, len(none.log))
    out = ["# Таблица флагов (задача 22)", "",
           "Это предложение для Стана; значения по умолчанию эта задача не меняет. Мир «всё включено»: 4 фракции, 1000 тиков, распорядок игрока из twin/integration.py.", "",
           f"Строк журнала: всё включено {len(base.log)}, без флагов {len(none.log)} (рост ×{ratio:.2f}). Нарушений инвариантов в мире «всё включено»: {len(t['bad'])}.", "",
           "| Флаг | По умолчанию | Выключается вместе с ним | Строк журнала (с флагом − без) | Расхождений журнала | Различий итога | Красных инвариантов | Предложение |",
           "|---|---|---|---|---|---|---|---|"]
    for r in t["rows"]:
        out.append(f"| {r['flag']} | {'включён' if r['default'] else 'выключен'} | {', '.join(r['also_off']) or '—'} | {r['delta']} | {r['diverge']} | {r['final_diff']} | {r['red']} | {recommend(r)} |")
    out += ["", "Пороги предложения (вклад в журнал не больше 10%, 0 расхождений) — мои, [предл]. Таблица описывает один мир (4 фракции, один распорядок игрока); на другой геометрии числа будут другими.", "",
           "Расхождений журнала — число строк, которые есть только в одном из двух журналов (мир «всё включено» и мир с выключенным флагом). Различий итога — число пунктов (уклад, цель, вожак, людей, владелец объекта) на тик 1000, где миры различаются."]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    import sys
    text = render(Params())
    if "--write" in sys.argv:
        open(TABLE_PATH, "w", encoding="utf-8").write(text)
    print(text)
