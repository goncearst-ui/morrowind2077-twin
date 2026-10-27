"""Задача 08f: стенд «мир из нескольких фракций» для замера войн (spec 08f). Модель не меняется."""
from dataclasses import replace

from .model import BUCKETS_OUT, Site, World
from .params import Params

NAMES = ("X1", "X2", "X3", "X4", "X5", "X6")
KINDS = ("Хранители", "Хранители", "Хищники", "Хищники", "Контролёры", "Дрейфующие")
SITE_SPEC = ((40, 90, 4, 40), (15, 35, 2, 15), (20, 60, 3, 20))   # как в SW (03b): три объекта на фракцию

# Пять раскладов, таблицей, без случайности [решение Стана: вопрос 3; числа предл].
# men — численность 30–60; dos — запас в сутках 20–60; swap — (объект, новый владелец) поверх «каждый держит свои три»;
# know — у кого что известно на старте: "all" = все чужие объекты, "near" = только объекты двух соседей по кругу, "none" = ничего.
LAYOUTS = {
    1: dict(men=(60, 40, 50, 50, 40, 30), dos=(20,) * 6, swap=(), know="all"),
    2: dict(men=(60, 40, 50, 50, 40, 30), dos=(40,) * 6, swap=(), know="all"),
    3: dict(men=(45, 55, 60, 35, 50, 30), dos=(60, 30, 20, 25, 40, 50), swap=(("X1-1", "X3"), ("X2-1", "X4")), know="all"),
    4: dict(men=(50, 50, 45, 45, 60, 35), dos=(30, 45, 25, 25, 55, 20), swap=(("X5-3", "X3"),), know="near"),
    5: dict(men=(40, 60, 55, 40, 30, 45), dos=(50, 20, 20, 20, 35, 60), swap=(("X6-1", "X4"), ("X1-2", "X5"), ("X2-3", "X3")), know="none"),
}


def build_bench(layout: int, wars_on: bool, p: Params | None = None):
    from .scenarios import faction
    p = p or Params()
    lay = LAYOUTS[layout]
    caps, ss = dict(p.crew_cap), []
    for n in NAMES:
        for k, (bc, y, mc, cp) in enumerate(SITE_SPEC):
            nm = f"{n}-{k + 1}"
            caps[nm] = cp
            ss.append(Site(nm, bc, y, mc, owner=n))
    for site, owner in lay["swap"]:
        next(s for s in ss if s.name == site).owner = owner
    p = replace(p, relations_enabled=True, knowledge_enabled=True, wars_enabled=wars_on, war_steers_attacks=wars_on,
                raid_discipline_enabled=True, crew_cap=caps, evolution_enabled=False)
    fs = {n: faction(p, n, KINDS[i], lay["men"][i], lay["dos"][i], 75) for i, n in enumerate(NAMES)}
    w = World(fs, ss, p)
    known = {}
    for i, n in enumerate(NAMES):
        if KINDS[i] not in ("Хищники", "Контролёры"):
            continue
        if lay["know"] == "all":
            known[n] = tuple(s.name for s in ss if s.owner != n)
        elif lay["know"] == "near":
            near = {NAMES[(i + 1) % 6], NAMES[(i - 1) % 6]}
            known[n] = tuple(s.name for s in ss if s.owner in near)
    w.known_at_start = known
    return w, 500


def summary(w: World) -> dict:
    ev = w.events
    declared = [e for e in ev if e["kind"] == "war_declared"]
    ends = [e for e in ev if e["kind"] == "war_end"]
    reasons = {}
    for e in ends:
        reasons[e["reason"]] = reasons.get(e["reason"], 0) + 1
    rep = sum(1 for r in w.log if r[6] == "WAR_REPARATION" and r[3].endswith(".supply") and r[5] > r[4])
    assaults = [e for e in ev if e["kind"] == "assault"]
    raids = [e for e in ev if e["kind"] == "raid_object"]
    dead_by = {}
    for r in w.log:
        if r[3].endswith(".dead") and r[5] > r[4]:
            dead_by[r[6]] = dead_by.get(r[6], 0) + (r[5] - r[4])
    min_dos = {}
    for r in w.log:
        if r[3].endswith(".days_supply"):
            n = r[3].split(".")[0]
            min_dos[n] = min(min_dos.get(n, 1e9), r[5])
    extinct = [n for n, f in w.factions.items() if f.manpower + f.wounded == 0]
    return dict(wars=len(declared), war_ticks=[e["tick"] for e in declared], ends=reasons, reparations=rep,
                assaults=len(assaults), raids=len(raids), losses=dead_by, min_dos={k: round(v, 1) for k, v in sorted(min_dos.items())},
                extinct=extinct)


def people_conserved(w: World, start: dict) -> bool:
    return all(f.manpower + f.wounded + sum(getattr(f, b) for b in BUCKETS_OUT) == start[n] + f.absorbed for n, f in w.factions.items())


def bn4(layout: int):
    """BN4: журнал режима «войны выкл» (без строк 08b) = журнал режима «войны вкл» при war_cost = 0, war_reparation_share = 0 и без управления."""
    off, h = build_bench(layout, False)
    on, _ = build_bench(layout, True, replace(Params(), war_cost=0.0, war_reparation_share=0.0))
    on.p = replace(on.p, war_steers_attacks=False)
    for w in (off, on):
        for f in w.factions.values():
            w.publish_dos(f, phase=0)
        for _ in range(h):
            w.step()
    return [r for r in on.log if r[2] != "08b"] == off.log
